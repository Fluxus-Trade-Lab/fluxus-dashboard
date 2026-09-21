"""规则 3 的两道关键控制（T-0921-100）

r3 的头条是：难买日守住前一天低点的票，63 日内创 52 周新高的概率 49.5% vs 41.3%（+8.2pp）。
**这个差值有一半可能是同义反复**：一只当天没跌的票，本来就离 52 周高点更近。
所以这里做两件事：

控制 ①（机械性）：按**当天离 52 周高点的距离**分十档，在每一档内部再比「守住 vs 没守住」。
  如果 +8pp 在每一档内部都塌成 0，那它就是「离高点近」换了个说法，不是「守住」的功劳。

控制 ②（有出处那条）：Deepvue 的说法是「**修正期间** RS Day 占比 >60% 的票是潜在龙头」。
  这不是单日信号，是一段期间的占比。按 appJ 的修正识别口径（SPY 日内 52 周新高之间、
  跌幅 ≥10%）切出修正段，算每只票在段内难买日的 RS Day 占比，按 >60% / ≤60% 分两组，
  比低点之后 63/126 日的超额与创新高概率。

输出：r3b_controls.json
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BENCH = REPO / ".cache" / "fr_bench_panel.pkl"
STOCKS = REPO / ".cache" / "fr_stock_panel.pkl"
OUT = HERE / "r3b_controls.json"

LOOKBACK = 252
NH_WINDOW = 63


def load():
    bench = pickle.loads(BENCH.read_bytes())
    panel = pickle.loads(STOCKS.read_bytes())
    spy = bench["SPY"].Close
    idx = spy.index
    tickers = sorted(panel)
    close = pd.DataFrame({t: panel[t].Close for t in tickers}).reindex(idx)
    low = pd.DataFrame({t: panel[t].Low for t in tickers}).reindex(idx)
    return bench, idx, tickers, close, low, spy


def main():
    bench, idx, tickers, close, low, spy = load()
    C, L = close.to_numpy(float), low.to_numpy(float)
    n_days = len(idx)
    spy_a = spy.to_numpy(float)
    ix = bench["^IXIC"].Close.reindex(idx).to_numpy(float)
    ix_ret = np.full(n_days, np.nan)
    ix_ret[1:] = ix[1:] / ix[:-1] - 1.0

    prior_max = close.shift(1).rolling(LOOKBACK, min_periods=LOOKBACK).max().to_numpy(float)
    is_nh = C >= prior_max
    hist_ok = np.isfinite(prior_max)
    dist_hi = C / prior_max - 1.0          # ≤0，越接近 0 离高点越近

    nh_soon = np.full(C.shape, np.nan)
    for i in range(n_days - NH_WINDOW):
        w = is_nh[i + 1:i + 1 + NH_WINDOW] & hist_ok[i + 1:i + 1 + NH_WINDOW]
        nh_soon[i] = w.any(axis=0).astype(float)

    fwd63 = np.full_like(C, np.nan)
    fwd63[:-63] = C[63:] / C[:-63] - 1.0
    s63 = np.full(n_days, np.nan)
    s63[:-63] = spy_a[63:] / spy_a[:-63] - 1.0
    exc63 = fwd63 - s63[:, None]

    held = np.full(C.shape, np.nan)
    held[1:] = (L[1:] >= L[:-1]).astype(float)
    held[1:][~np.isfinite(L[:-1]) | ~np.isfinite(L[1:])] = np.nan

    rows = np.where((ix_ret < 0) & (np.arange(n_days) > LOOKBACK))[0]

    # ── 控制 ①：按离 52 周高点的距离分十档 ────────────────────
    edges = [-1.01, -0.50, -0.35, -0.25, -0.18, -0.13, -0.09, -0.06, -0.035, -0.015, 0.001]
    labels = [f"[{edges[k]*100:.1f}%,{edges[k+1]*100:.1f}%)" for k in range(len(edges) - 1)]
    buckets = {lab: {"h_nh": [], "b_nh": [], "h_ex": [], "b_ex": []} for lab in labels}
    for i in rows:
        ok = np.isfinite(held[i]) & hist_ok[i] & np.isfinite(dist_hi[i])
        if not ok.any():
            continue
        bi = np.digitize(dist_hi[i], edges) - 1
        for k, lab in enumerate(labels):
            m = ok & (bi == k)
            if not m.any():
                continue
            hm, bm = m & (held[i] == 1), m & (held[i] == 0)
            for src, tgt in ((nh_soon[i], "nh"), (exc63[i], "ex")):
                good = np.isfinite(src)
                buckets[lab][f"h_{tgt}"].extend(src[hm & good])
                buckets[lab][f"b_{tgt}"].extend(src[bm & good])

    ctrl1 = {}
    for lab in labels:
        d = buckets[lab]
        if len(d["h_nh"]) < 500 or len(d["b_nh"]) < 500:
            continue
        ctrl1[lab] = {
            "n_held": len(d["h_nh"]), "n_broke": len(d["b_nh"]),
            "nh63_held_pct": round(100 * float(np.mean(d["h_nh"])), 1),
            "nh63_broke_pct": round(100 * float(np.mean(d["b_nh"])), 1),
            "nh63_gap_pp": round(100 * (float(np.mean(d["h_nh"])) - float(np.mean(d["b_nh"]))), 1),
            "exc63_held_median_pct": round(100 * float(np.median(d["h_ex"])), 2) if d["h_ex"] else None,
            "exc63_broke_median_pct": round(100 * float(np.median(d["b_ex"])), 2) if d["b_ex"] else None,
        }

    # ── 控制 ②：Deepvue 的「修正期 RS Day 占比 >60%」 ────────────
    sp = bench["SPY"]
    hi, lo = sp.High.reindex(idx), sp.Low.reindex(idx)
    roll = hi.rolling(LOOKBACK, min_periods=1).max()
    peaks = [k for k, v in enumerate((hi >= roll).to_numpy()) if v]
    corrections = []
    for a, b in zip(peaks, peaks[1:] + [n_days]):
        if b - a < 2:
            continue
        seg = lo.iloc[a:b]
        t = int(np.argmin(seg.to_numpy())) + a
        dd = float(seg.min()) / float(hi.iloc[a]) - 1.0
        if dd <= -0.10:
            corrections.append({"peak_i": a, "trough_i": t,
                                "peak": str(idx[a].date()), "trough": str(idx[t].date()),
                                "dd_pct": round(dd * 100, 2)})

    ctrl2 = {"corrections": corrections, "cells": {}}
    hi_rate, lo_rate = {63: ([], []), 126: ([], [])}, None
    agg = {63: {"hi": [], "lo": []}, 126: {"hi": [], "lo": []}}
    agg_nh = {"hi": [], "lo": []}
    for corr in corrections:
        a, t = corr["peak_i"], corr["trough_i"]
        days = [i for i in range(a, t + 1) if ix_ret[i] < 0]
        if len(days) < 10:
            continue
        hcol = held[days]                       # (ndays, ntickers)
        with np.errstate(invalid="ignore"):
            rate = np.nanmean(hcol, axis=0)
        n_obs = np.isfinite(hcol).sum(axis=0)
        alive = hist_ok[t] & (n_obs >= 10)
        for h in (63, 126):
            j = t + h
            if j >= n_days:
                continue
            f = C[j] / C[t] - 1.0 - (spy_a[j] / spy_a[t] - 1.0)
            good = alive & np.isfinite(f)
            agg[h]["hi"].extend(f[good & (rate > 0.60)])
            agg[h]["lo"].extend(f[good & (rate <= 0.60)])
        good = alive & np.isfinite(nh_soon[t])
        agg_nh["hi"].extend(nh_soon[t][good & (rate > 0.60)])
        agg_nh["lo"].extend(nh_soon[t][good & (rate <= 0.60)])

    for h in (63, 126):
        a_, b_ = agg[h]["hi"], agg[h]["lo"]
        ctrl2["cells"][f"exc{h}_from_trough"] = {
            "rs_day_rate_gt60": {"n": len(a_),
                                 "median_pct": round(100 * float(np.median(a_)), 2) if a_ else None,
                                 "mean_pct": round(100 * float(np.mean(a_)), 2) if a_ else None},
            "rs_day_rate_le60": {"n": len(b_),
                                 "median_pct": round(100 * float(np.median(b_)), 2) if b_ else None,
                                 "mean_pct": round(100 * float(np.mean(b_)), 2) if b_ else None},
            "gap_median_pp": round(100 * (float(np.median(a_)) - float(np.median(b_))), 2)
            if a_ and b_ else None,
        }
    a_, b_ = agg_nh["hi"], agg_nh["lo"]
    ctrl2["cells"]["new_52w_high_within_63d_from_trough"] = {
        "gt60_pct": round(100 * float(np.mean(a_)), 1) if a_ else None,
        "le60_pct": round(100 * float(np.mean(b_)), 1) if b_ else None,
        "gap_pp": round(100 * (float(np.mean(a_)) - float(np.mean(b_))), 1) if a_ and b_ else None,
        "n_gt60": len(a_), "n_le60": len(b_),
    }

    res = {"meta": {
        "generated": "2026-09-21",
        "control_1": "按当天离 52 周高点的距离分十档，档内再比守住/没守住",
        "control_2": "Deepvue「修正期 RS Day 占比 >60%」；修正识别照抄 SwingMasterclass "
                     "_bench/appJ_correction_leaders.py（SPY 日内 52 周新高之间、跌幅 ≥10%）",
        "survivorship": "今天还活着的 1826 只；两组同源",
    }, "control_1_by_distance_to_52w_high": ctrl1, "control_2_deepvue_rs_day_rate": ctrl2}
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False))

    print("== 控制①：档内再比（nh63 = 63 日内创 52 周新高的概率）==")
    print(f"{'离高点距离':>18} {'n_held':>8} {'守住%':>7} {'没守%':>7} {'差 pp':>7} "
          f"{'守住 exc63':>10} {'没守 exc63':>10}")
    for lab, v in ctrl1.items():
        print(f"{lab:>18} {v['n_held']:>8} {v['nh63_held_pct']:>7} {v['nh63_broke_pct']:>7} "
              f"{v['nh63_gap_pp']:>7} {v['exc63_held_median_pct']:>10} "
              f"{v['exc63_broke_median_pct']:>10}")
    print(f"\n== 控制②：{len(corrections)} 次修正 ==")
    for c in corrections:
        print("  ", c)
    print(json.dumps(ctrl2["cells"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
