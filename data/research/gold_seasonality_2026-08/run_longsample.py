"""长样本复核：World Bank Pink Sheet 1960–2025（月均价）。

为什么有这一步：本研究 v1 的预注册写「2000-09 → 2026-08 是最长可得」——**那是假的**，
只是 yfinance 上 GC=F 最长。反驳视角的核对员指出后自己重取。

⚠️ 两处必须一起报，否则会拿一个更长但不同口径的序列去推翻自己的主口径：
① Pink Sheet 是**当月均价**，不是月末价 —— 会平滑并把变化后移约半个月；
② 1971 年之前黄金被布雷顿森林钉住（35 美元），根本没有自由价格。
所以长样本的作用是**问「我们的窗口是不是切掉了效应最强的年代」**，
不是用来替换主口径的读数。
"""
import json
import numpy as np
import pandas as pd
from pink_reader import read_monthly, series
from run_study import perm_p, holm, MONTHS

SEED = 20260831
WINDOWS = [("1968_2025", 1968, 2025), ("1975_1999", 1975, 1999),
           ("1975_2025", 1975, 2025), ("2000_2025", 2000, 2025)]


def monthly_ret(s, lo, hi):
    r = (s / s.shift(1) - 1).dropna()
    r = r[(r.index.year >= lo) & (r.index.year <= hi)]
    r.index = r.index.to_timestamp("M")
    return r


def main():
    px = series(read_monthly(), {"Gold", "Silver"})
    out = {"source": "World Bank Pink Sheet CMO-Historical-Data-Monthly.xlsx (月均价)",
           "coverage": {k: [str(v.index[0]), str(v.index[-1]), int(len(v))] for k, v in px.items()},
           "windows": {}}
    rng = np.random.default_rng(SEED)
    for tag, lo, hi in WINDOWS:
        rows = []
        for metal, s in [("gold", px["Gold"]), ("silver", px["Silver"])]:
            r = monthly_ret(s, lo, hi)
            for m in range(1, 13):
                obs, p, n = perm_p(r, m, rng)
                rows.append({"metal": metal, "month": MONTHS[m - 1], "n": n,
                             "mean_diff_pct": round(float(obs) * 100, 4),
                             "p_raw": round(float(p), 5)})
        adj = holm([x["p_raw"] for x in rows])
        for x, a in zip(rows, adj):
            x["p_holm"] = round(float(a), 5)
        grad = {}
        for metal, s in [("gold", px["Gold"]), ("silver", px["Silver"])]:
            r = monthly_ret(s, lo, hi)
            grad[metal] = sorted([(MONTHS[m - 1], round(float(r[r.index.month == m].mean() * 100), 3))
                                  for m in range(1, 13)], key=lambda x: -x[1])
        out["windows"][tag] = {"cells": rows, "gradient": grad}
    json.dump(out, open("results_longsample.json", "w"), indent=2)

    print(f"覆盖：{out['coverage']}\n")
    hdr = f"{'窗口':<12}{'金9 超额':>10}{'p_raw':>9}{'p_Holm':>9}{'金9 名次':>10}"
    hdr += f"{'银10 超额':>11}{'p_raw':>9}{'银10 名次':>11}"
    print(hdr); print("-" * len(hdr))
    for tag, _, _ in WINDOWS:
        w = out["windows"][tag]
        g = [c for c in w["cells"] if c["metal"] == "gold" and c["month"] == "Sep"][0]
        s = [c for c in w["cells"] if c["metal"] == "silver" and c["month"] == "Oct"][0]
        gr = [m for m, _ in w["gradient"]["gold"]].index("Sep") + 1
        sr = [m for m, _ in w["gradient"]["silver"]].index("Oct") + 1
        print(f"{tag:<12}{g['mean_diff_pct']:>+9.2f}pp{g['p_raw']:>9.3f}{g['p_holm']:>9.3f}"
              f"{gr:>8}/12{s['mean_diff_pct']:>+10.2f}pp{s['p_raw']:>9.3f}{sr:>9}/12")


if __name__ == "__main__":
    main()
