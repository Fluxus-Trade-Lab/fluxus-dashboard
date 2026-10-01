#!/usr/bin/env python3
"""复算 TMC Research 那篇文章印出来的两个数，证明口径 B 是他们的，不是我们的近似。

TMC Research, "History's Message on Yield Shocks"（James Picerno, 2026-05-05）印了两个可核的数：
  · 「In the 3-month, +50-bps example, the sample size is 62.」
  · 「The horizontal blue line marks the median return (2.5% in this case).」

他们公开的规则：月频数据 · 1970 年起 · S&P 500 · 收益率相对**前六个月最低点**的抬升
· 分档 50/100/200/300bp · 「a 6-month exclusion window to prevent a single, ongoing yield
surge from generating multiple signals in quick succession」。

本脚本按这套规则跑一遍。断言 n == 62 且中位数四舍五入到 0.1% == 2.5%。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
START = "1970-01-01"
LOOKBACK_M = 6          # 「prior six months」
EXCL_M = 6              # 「a 6-month exclusion window」
BUCKETS_BP = [50, 100, 200, 300]
HORIZONS_M = [3, 6, 12, 24]


def monthly() -> tuple[pd.Series, pd.Series]:
    raw = pd.read_csv(HERE / "dgs10.csv.gz")
    y = pd.Series(pd.to_numeric(raw["DGS10"], errors="coerce").values,
                  index=pd.to_datetime(raw[raw.columns[0]])).dropna().sort_index()
    px = pd.read_csv(HERE / "prices.csv.gz", index_col=0, parse_dates=True)["^GSPC"].dropna()
    ym = y.resample("ME").last().dropna()
    ym = ym[ym.index >= START]
    pm = px.resample("ME").last().dropna()
    pm = pm.reindex(pm.index.union(ym.index)).ffill().reindex(ym.index)
    return ym, pm


def events(ym: pd.Series, bp: int) -> list[pd.Timestamp]:
    runup = ym - ym.rolling(LOOKBACK_M + 1, min_periods=LOOKBACK_M + 1).min()
    kept: list[pd.Timestamp] = []
    last = None
    for d in runup[runup >= bp / 100.0].index:
        if last is None or (d.to_period("M") - last.to_period("M")).n >= EXCL_M:
            kept.append(d)
            last = d
    return kept


def main() -> int:
    ym, pm = monthly()
    table = {}
    for bp in BUCKETS_BP:
        ev = events(ym, bp)
        pos = [ym.index.get_loc(d) for d in ev]
        table[bp] = {}
        for h in HORIZONS_M:
            r = np.array([pm.iloc[i + h] / pm.iloc[i] - 1 for i in pos if i + h < len(pm)])
            if r.size == 0:
                continue
            table[bp][h] = (int(r.size), float(np.median(r)))
            print(f"  +{bp:3d}bp {h:2d}m: n={r.size:3d} 中位={np.median(r) * 100:+6.2f}%")

    n, med = table[50][3]
    print(f"\n断言：TMC 印的是 n=62、中位 2.5%；我们算出 n={n}、中位 {med * 100:.2f}%")
    assert n == 62, f"样本数不符：{n} ≠ 62，口径没复现，别信下面的结论"
    assert round(med * 100, 1) == 2.5, f"中位数不符：{med * 100:.2f}% ≠ 2.5%"
    print("✅ 两个数都逐字复现，口径 B 已确认是 TMC 的那套规则")
    # 顺手印出他们的高档样本有多薄——他们自己也说了 n 会掉
    print(f"⚠️ 他们的 +300bp 档在这套规则下只有 n={table[300][3][0]}（3 个月那一格）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
