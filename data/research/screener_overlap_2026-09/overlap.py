#!/usr/bin/env python3
"""筛子集合冗余度 —— 逐日 Jaccard / 有向包含度 / 随机基线。

口径不是自造的（宪法「先找口径，别自己造」）：
  * Jaccard index J(A,B) = |A∩B| / |A∪B|     —— 集合相似度的标准量
  * overlap coefficient  = |A∩B| / min(|A|,|B|) —— 标准写法用 min
  * 本文另报 **有向包含度** C(A→B) = |A∩B| / |A|，
    因为「A 是不是 B 的影子」是个有方向的问题，min 版本会把方向抹掉。
    有向这一步是自造的，明写在此。
  * 显著性的标准做法是 hypergeometric / 单尾 Fisher。**本文不报 p 值**，
    理由写在 results.md §0：114 天 × 上万行下它对每一对都会显著，
    是分辨率问题不是发现。这里回答的是幅度。

数据：data/history/ticker_events.csv（只读），universe_size 来自 breadth_archive.csv。
"""
import csv, collections, statistics, json, random, sys

EVENTS = "data/history/ticker_events.csv"
BREADTH = "data/history/breadth_archive.csv"


def load():
    byds = collections.defaultdict(set)
    for r in csv.DictReader(open(EVENTS)):
        byds[(r["date"], r["screener"])].add(r["ticker"])
    dates = sorted({d for d, _ in byds})
    screeners = sorted({s for _, s in byds})
    pool = collections.defaultdict(set)
    for (d, s), v in byds.items():
        pool[d] |= v
    univ = {}
    for r in csv.DictReader(open(BREADTH)):
        try:
            univ[r["date"]] = int(float(r["universe_size"]))
        except (KeyError, ValueError, TypeError):
            pass
    return byds, dates, screeners, pool, univ


def pair_stats(byds, dates, screeners, pool, univ, min_days=30):
    out = []
    for a in screeners:
        for b in screeners:
            if a == b:
                continue
            js, cs, lifts_pool, lifts_univ = [], [], [], []
            for d in dates:
                A, B = byds.get((d, a)), byds.get((d, b))
                if not A or not B:
                    continue
                inter = len(A & B)
                js.append(inter / len(A | B))
                c = inter / len(A)
                cs.append(c)
                # 随机基线：同样大小的 B 从池子里随机抽，E[C] = |B| / pool
                lifts_pool.append(c / (len(B) / len(pool[d])) if pool[d] else float("nan"))
                if d in univ and univ[d]:
                    lifts_univ.append(c / (len(B) / univ[d]))
            if len(cs) < min_days:
                continue
            out.append({
                "a": a, "b": b, "days": len(cs),
                "median_jaccard": statistics.median(js),
                "median_containment": statistics.median(cs),
                "median_lift_vs_pool": statistics.median(lifts_pool),
                "median_lift_vs_universe": statistics.median(lifts_univ) if lifts_univ else None,
                "median_size_a": statistics.median(
                    [len(byds[(d, a)]) for d in dates if (d, a) in byds and (d, b) in byds]),
                "median_size_b": statistics.median(
                    [len(byds[(d, b)]) for d in dates if (d, a) in byds and (d, b) in byds]),
            })
    return out


def null_calibration(byds, dates, screeners, pool, seed=20260906, reps=200):
    """阴性对照的**校准**版（不是「随便打散一次看有没有信号」）：
    每天把每个筛子换成同样大小的随机抽样，重算有向包含度，
    报它与解析期望 |B|/pool 的比值分布 —— 应当以 1 为中心。
    这条是用来证明「lift」这把尺子本身没歪，不是用来证明谁没信号。"""
    rng = random.Random(seed)
    ratios = []
    ds = dates[-reps:] if len(dates) > reps else dates
    for d in ds:
        p = sorted(pool[d])
        present = [s for s in screeners if (d, s) in byds]
        fake = {s: set(rng.sample(p, len(byds[(d, s)]))) for s in present}
        for a in present:
            for b in present:
                if a == b:
                    continue
                c = len(fake[a] & fake[b]) / len(fake[a])
                exp = len(fake[b]) / len(p)
                ratios.append(c / exp)
    ratios.sort()
    q = lambda f: ratios[int(f * (len(ratios) - 1))]
    return {"n": len(ratios), "mean": sum(ratios) / len(ratios),
            "p05": q(.05), "median": q(.5), "p95": q(.95)}


if __name__ == "__main__":
    byds, dates, screeners, pool, univ = load()
    res = pair_stats(byds, dates, screeners, pool, univ)
    res.sort(key=lambda r: -r["median_containment"])
    json.dump({"pairs": res, "null": null_calibration(byds, dates, screeners, pool),
               "dates": [dates[0], dates[-1]], "n_dates": len(dates)},
              open("data/research/screener_overlap_2026-09/overlap.json", "w"),
              indent=1, ensure_ascii=False)
    print(f"{'A (被查的)':30s} {'B (参照)':30s} {'天':>4s} {'|A|':>5s} {'|B|':>5s} {'C(A→B)':>8s} {'J':>6s} {'lift/pool':>10s}")
    for r in res[:30]:
        print(f"{r['a']:30s} {r['b']:30s} {r['days']:4d} {r['median_size_a']:5.0f} "
              f"{r['median_size_b']:5.0f} {r['median_containment']:8.3f} "
              f"{r['median_jaccard']:6.3f} {r['median_lift_vs_pool']:10.2f}")
    print()
    print("阴性对照（随机集合的 lift 分布，应以 1 为中心）:", json.dumps(null_calibration(byds, dates, screeners, pool)))
