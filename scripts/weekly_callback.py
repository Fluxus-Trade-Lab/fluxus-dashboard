#!/usr/bin/env python3
"""每周信「技术段」的素材生成器 —— callback 引擎。

流程照搬 TSF 的周报，但用一个他没有的东西：**完整的筛选器历史归档**。
TSF 只能写「两周前它出现在我们的 leaderboard 上」——不可核对。
你能写「7 月 31 日第一次出现，从 3 月 9 日开始的归档里查得到」——可核对。

    python scripts/weekly_callback.py              # 最近 5 个交易日 vs 前 5 个
    python scripts/weekly_callback.py --window 10  # 改成 10 日窗口
    python scripts/weekly_callback.py --ticker PLTR META   # 点名核对

输出四块，正好对应信里技术段的四个小节：
    ① 主题层  哪个板块在扩张（写小节标题用）
    ② 新面孔  最近窗口第一次上榜的（今天的清单）
    ③ 持续性  跨筛选器密集上榜的（真正在跑的）
    ④ callback 某个名字的完整上榜史（"它什么时候第一次告诉我的"）
"""
import argparse
import collections
import csv
from pathlib import Path

ARCHIVE = Path("data/history/ticker_events.csv")


def load():
    if not ARCHIVE.exists():
        raise SystemExit(f"归档不存在: {ARCHIVE}")
    rows = list(csv.DictReader(open(ARCHIVE)))
    dates = sorted({r["date"] for r in rows})
    return rows, dates


def block_themes(rows, cur, prev):
    """板块层：本期 vs 前期。按相对变化排序 —— 绝对值会被大板块盖住。"""
    def agg(sel):
        c = collections.Counter()
        for r in rows:
            if r["date"] in sel and r.get("sector"):
                c[r["sector"]] += 1
        return c
    a, b = agg(cur), agg(prev)
    out = []
    for k in set(a) | set(b):
        base = b[k] or 1
        out.append((k, a[k], b[k], a[k] - b[k], (a[k] - b[k]) / base * 100))
    out.sort(key=lambda x: -x[4])
    return out


def block_new(rows, cur):
    """最近窗口第一次上榜的名字 = 今天该看的清单。"""
    first, hits, scr = {}, collections.Counter(), collections.defaultdict(set)
    for r in rows:
        t = r["ticker"]
        if t not in first or r["date"] < first[t]:
            first[t] = r["date"]
        if r["date"] in cur:
            hits[t] += 1
            scr[t].add(r["screener"])
    return [(t, n, first[t], sorted(scr[t])) for t, n in hits.most_common()
            if first[t] in cur]


def block_persistent(rows, cur, min_screeners=3):
    """跨筛选器上榜 = 不是单一指标的噪音，是真的在跑。"""
    hits, scr, first = collections.Counter(), collections.defaultdict(set), {}
    for r in rows:
        t = r["ticker"]
        if t not in first or r["date"] < first[t]:
            first[t] = r["date"]
        if r["date"] in cur:
            hits[t] += 1
            scr[t].add(r["screener"])
    return [(t, n, first[t], sorted(scr[t])) for t, n in hits.most_common()
            if len(scr[t]) >= min_screeners]


def block_callback(rows, ticker):
    h = [r for r in rows if r["ticker"] == ticker.upper()]
    if not h:
        return None
    days = sorted({r["date"] for r in h})
    return {"first": days[0], "last": days[-1], "n_days": len(days),
            "screeners": sorted({r["screener"] for r in h}), "days": days}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=5, help="交易日窗口，默认 5")
    ap.add_argument("--ticker", nargs="*", default=[], help="点名核对")
    args = ap.parse_args()

    rows, dates = load()
    w = args.window
    cur, prev = set(dates[-w:]), set(dates[-2 * w:-w])

    print(f"归档 {dates[0]} → {dates[-1]}（{len(rows):,} 行）")
    print(f"本期 {min(cur)} → {max(cur)}   对照期 {min(prev)} → {max(prev)}\n")

    print("═══ ① 主题层：哪个板块在扩张（按相对变化排）═══")
    print(f"  {'板块':<24} {'本期':>6} {'前期':>6} {'变化':>7} {'相对':>8}")
    themes = block_themes(rows, cur, prev)
    for k, a, b, d, pct in themes[:5]:
        print(f"  ↑ {k:<22} {a:>6} {b:>6} {d:>+7} {pct:>+7.0f}%")
    for k, a, b, d, pct in themes[-3:]:
        print(f"  ↓ {k:<22} {a:>6} {b:>6} {d:>+7} {pct:>+7.0f}%")

    new = block_new(rows, cur)
    print(f"\n═══ ② 新面孔：本期第一次上榜（共 {len(new)} 个）═══")
    for t, n, f, s in new[:10]:
        print(f"  {t:<6} {n:>3} 次 · 首现 {f} · {', '.join(s)}")

    per = block_persistent(rows, cur)
    print(f"\n═══ ③ 持续性：≥3 个筛选器同时命中（共 {len(per)} 个）═══")
    for t, n, f, s in per[:10]:
        print(f"  {t:<6} {n:>3} 次 · {len(s)} 器 · 首现 {f} · {', '.join(s)}")

    if args.ticker:
        print("\n═══ ④ callback：点名核对 ═══")
        for t in args.ticker:
            c = block_callback(rows, t)
            if not c:
                print(f"  {t.upper()}: 归档里从未上榜")
                continue
            print(f"  {t.upper()}: 首次 {c['first']} · 共 {c['n_days']} 天 · "
                  f"最近 {c['last']}")
            print(f"          筛选器 {', '.join(c['screeners'])}")

    print("\n⚠️ 归档最后一天是 " + dates[-1] + "。写之前先确认管线已跑到最新交易日。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
