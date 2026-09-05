#!/usr/bin/env python3
"""每一对的阴性对照，量的是**和观测同一个统计量**：逐日包含度的中位数。

上一版的错在这里：我算的是「单日 lift 的分布」（p95=2.60），
却拿它去判断「100 天中位数」这个量大不大 —— 两个不同的量。
单次观测的散度和 100 天中位数的散度差着一个 sqrt(n)。
（协议里的原话：阴性对照不等于校准检查。）

做法：每天把每个筛子替换成同样大小的随机抽样（抽自当天的观测池），
重算 C(A→B)，对日期取中位数 —— 重复 R 次得到「中位包含度」的零分布。
观测值落在这个零分布的哪个分位，才是「它比随机高多少」的答案。
"""
import csv, collections, statistics, random, json, sys

R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
SEED = 20260906

byds = collections.defaultdict(set)
for r in csv.DictReader(open("data/history/ticker_events.csv")):
    byds[(r["date"], r["screener"])].add(r["ticker"])
dates = sorted({d for d, _ in byds})
screeners = sorted({s for _, s in byds})
pool = collections.defaultdict(set)
for (d, s), v in byds.items():
    pool[d] |= v
pool_l = {d: sorted(v) for d, v in pool.items()}

obs = {}
for a in screeners:
    for b in screeners:
        if a == b:
            continue
        cs = [len(byds[(d, a)] & byds[(d, b)]) / len(byds[(d, a)])
              for d in dates if (d, a) in byds and (d, b) in byds]
        if len(cs) >= 30:
            obs[(a, b)] = statistics.median(cs)

rng = random.Random(SEED)
null = collections.defaultdict(list)
for rep in range(R):
    per_date = {}
    for d in dates:
        p = pool_l[d]
        per_date[d] = {s: set(rng.sample(p, len(byds[(d, s)])))
                       for s in screeners if (d, s) in byds}
    for (a, b) in obs:
        cs = [len(per_date[d][a] & per_date[d][b]) / len(per_date[d][a])
              for d in dates if a in per_date[d] and b in per_date[d]]
        null[(a, b)].append(statistics.median(cs))

out = []
for (a, b), o in obs.items():
    n = sorted(null[(a, b)])
    ge = sum(1 for x in n if x >= o)
    out.append({"a": a, "b": b, "obs": o,
                "null_median": n[len(n) // 2], "null_p95": n[int(.95 * (len(n) - 1))],
                "null_max": n[-1], "p_perm": (ge + 1) / (len(n) + 1)})
out.sort(key=lambda r: -r["obs"])
json.dump({"R": R, "seed": SEED, "pairs": out},
          open("data/research/screener_overlap_2026-09/null_median.json", "w"),
          indent=1, ensure_ascii=False)
print(f"R={R}  最小可能置换 p = {1/(R+1):.4f}（{len(out)} 对 → Bonferroni 后地板 {len(out)/(R+1):.2f}）")
print(f"{'A':30s} {'B':30s} {'观测C':>7s} {'零中位':>7s} {'零p95':>7s} {'零最大':>7s} {'p_perm':>7s}")
for r in out[:22]:
    print(f"{r['a']:30s} {r['b']:30s} {r['obs']:7.3f} {r['null_median']:7.3f} "
          f"{r['null_p95']:7.3f} {r['null_max']:7.3f} {r['p_perm']:7.3f}")
