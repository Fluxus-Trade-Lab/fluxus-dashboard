"""规则 2 的区间：按日期分块自助，给 h63 的 gap 一个 90% 区间。

为什么必须做：上面 n=4 万是每天一行的重叠窗口，同一天还有 77 个组横截面相关。
真正独立的单位是**日期块**，4200 个交易日除以 63 ≈ 66 块。自助按块抽日期，
每次重算「RSP 线下中位超额 − 线上中位超额」，看 0 在不在区间里。
"""
import json, pickle, statistics, sys
from collections import defaultdict
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path("data/research/four_rules_2026-09-21").resolve()))
from r2_rsp_50dma import four_state, equal_weight_industry, REPO, BENCH, STOCKS, OUT

rng = np.random.default_rng(20260921)
H, BLOCK, ITERS = 63, 63, 600

bench = pickle.loads(BENCH.read_bytes())
spy, rsp = bench["SPY"].Close, bench["RSP"].Close
stock_panel = pickle.loads(STOCKS.read_bytes())
gj = json.loads((REPO / "data/output/groups.json").read_text())["stocks"]
ind = defaultdict(list)
for t, rec in gj.items():
    if t in stock_panel:
        ind[rec["group"]].append(t)
navs = equal_weight_industry(stock_panel, ind, spy.index)

ratio = rsp / spy.reindex(rsp.index)
sigs = {
    "rsp_vs_own_50dma": (rsp < rsp.rolling(50).mean()).reindex(spy.index),
    "rsp_over_spy_ratio_vs_50dma": (ratio < ratio.rolling(50).mean()).reindex(spy.index),
}

fwd_s = spy.shift(-H) / spy - 1.0
by_date = defaultdict(list)          # date -> [excess, ...] for Leading groups
for g, nav in navs.items():
    nav = nav.dropna()
    st = four_state(nav, spy)["state"]
    exc = (nav.shift(-H) / nav - 1.0) - fwd_s.reindex(nav.index)
    for d, v in exc.items():
        if np.isfinite(v) and st.get(d) == "Leading":
            by_date[d].append(float(v))

dates = sorted(by_date)
blocks = [dates[i:i + BLOCK] for i in range(0, len(dates), BLOCK)]
print(f"Leading 组有远期的交易日 {len(dates)} 天 → {len(blocks)} 个不重叠日期块")

out = {}
for name, sig in sigs.items():
    def gap(ds):
        below, above = [], []
        for d in ds:
            s = sig.get(d)
            if s is None or pd.isna(s):
                continue
            (below if bool(s) else above).extend(by_date[d])
        if len(below) < 30 or len(above) < 30:
            return None
        return 100 * (statistics.median(below) - statistics.median(above))

    point = gap(dates)
    draws = []
    for _ in range(ITERS):
        pick = rng.integers(0, len(blocks), len(blocks))
        ds = [d for k in pick for d in blocks[k]]
        v = gap(ds)
        if v is not None:
            draws.append(v)
    lo, hi = np.percentile(draws, [5, 95])
    out[name] = {"gap_below_minus_above_pp": round(point, 2),
                 "ci90_pp": [round(float(lo), 2), round(float(hi), 2)],
                 "n_blocks": len(blocks), "n_boot": len(draws),
                 "crosses_zero": bool(lo <= 0 <= hi)}
    print(f"{name}: gap={point:+.2f}pp  90% CI [{lo:+.2f}, {hi:+.2f}]  "
          f"{'跨 0 —— 测不出方向' if lo <= 0 <= hi else '不跨 0'}")

res = json.loads(OUT.read_text())
res["block_bootstrap_h63"] = out
OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False))
print("written")
