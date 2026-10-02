#!/usr/bin/env python3
"""Semiconductor-pool breadth, 2026-08-01 -> last completed session (T-1002-80).

Same rulers as ``pipeline.screeners.breadth_metrics``; only the pool changes,
from "everything Finviz carries" to the union of three taxonomy theme groups.
Every threshold below is imported in spirit from breadth_metrics.py -- the
values are restated here rather than imported because that module computes a
single snapshot from a Finviz universe row set, while this one needs a daily
series built from bars. Any drift between the two is a defect; the positive
control in ``verify_control()`` is what catches it.

Usage:
    python3 data/research/semi_breadth_2026-10-02/build_series.py [--outdir DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np

REPO = Path(__file__).resolve().parents[3]

# ── Rulers, restated from pipeline/screeners/breadth_metrics.py ───────────
NEW_HIGH_THRESHOLD = -0.001      # breadth_metrics.py:33
NEW_LOW_THRESHOLD = 0.001        # breadth_metrics.py:34
EXCLUDED_INDUSTRIES = frozenset({'Shell Companies'})   # breadth_metrics.py:51
MIN_BARS_52W = 200               # breadth_metrics.py:59
MIN_BARS_4W = 20                 # breadth_metrics.py:60
WIN_52W, WIN_4W = 252, 20

GROUPS = ("Semiconductors Broad", "Semiconductors Large Caps", "Memory & Storage")
WINDOW_START = "2026-08-01"
# 52w lookback + 50d SMA warmup must both be satisfied at WINDOW_START.
DOWNLOAD_START = "2024-09-01"


def load_pool(repo: Path) -> dict:
    """The three theme groups as published in data/output/groups.json."""
    d = json.loads((repo / "data/output/groups.json").read_text())
    per = {t["group"]: sorted(t["tickers"]) for t in d["themes"] if t["group"] in GROUPS}
    missing = set(GROUPS) - set(per)
    if missing:
        raise SystemExit(f"groups.json has no theme named: {sorted(missing)}")
    return {"as_of": d["date"], "groups": per, "pool": sorted(set().union(*per.values()))}


def load_industries(repo: Path, pool: list[str]) -> dict:
    """Finviz industry per pool name, for the common-stock type gate."""
    u = json.loads((repo / "data/output/universe.json").read_text())
    rows = {r["ticker"]: r for r in u["rows"]}
    absent = [t for t in pool if t not in rows]
    if absent:
        print(f"  warn: not in published universe, type gate unknown: {absent}")
    return {t: rows.get(t, {}).get("industry") for t in pool}


def download(pool: list[str], end: str) -> dict[str, pd.DataFrame]:
    import yfinance as yf
    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(pool), 20):
        chunk = pool[i:i + 20]
        df = yf.download(chunk, start=DOWNLOAD_START, end=end, auto_adjust=True,
                         progress=False, group_by="ticker", threads=True, actions=False)
        for t in chunk:
            try:
                sub = df[t].dropna(how="all")
            except KeyError:
                print(f"  warn: no bars for {t}")
                continue
            if len(sub):
                out[t] = sub[["High", "Low", "Close"]].copy()
        time.sleep(1)
    return out


def panels(bars: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out = {}
    for t, h in bars.items():
        c = h["Close"]
        out[t] = pd.DataFrame({
            "close": c,
            "sma50": c.rolling(50).mean(),
            "sma200": c.rolling(200).mean(),
            # min_periods is the bar floor, not the window length: production
            # counts a name at a 52-week extreme once it has 200 bars
            # (MIN_BARS_52W), and Finviz publishes a high_52w for it from the
            # history it has. Leaving min_periods at the pandas default (= the
            # window) would silently impose a 252-bar floor instead and drop
            # names with 200-251 bars out of the gated counts -- one name on
            # 2026-10-01, which is why `semi_n_gate_52w` read 117 before this
            # was fixed. The gate below still re-checks bars_n, so the two
            # floors agree rather than overlapping at different values.
            "max_h_252": h["High"].rolling(WIN_52W, min_periods=MIN_BARS_52W).max(),
            "min_l_252": h["Low"].rolling(WIN_52W, min_periods=MIN_BARS_52W).min(),
            "max_h_20": h["High"].rolling(WIN_4W, min_periods=MIN_BARS_4W).max(),
            "min_l_20": h["Low"].rolling(WIN_4W, min_periods=MIN_BARS_4W).min(),
            "bars_n": np.arange(1, len(c) + 1),
        })
    return out


def verify_control(panel: dict, repo: Path, asof: str) -> None:
    """Positive control: reproduce the published per-name readings on `asof`.

    Finviz's 52-week range is built on INTRADAY highs/lows, not closes. The
    close-based variant is kept here as the negative arm -- if it ever stops
    being visibly worse, the control has stopped discriminating and this
    whole series is unverified.
    """
    u = json.loads((repo / "data/output/universe.json").read_text())
    rows = {r["ticker"]: r for r in u["rows"]}
    D = pd.Timestamp(asof)
    sma_sign_dis = hi_flag_dis = 0
    d_hi_high, d_hi_close, d_sma = [], [], []
    mine_above = pub_above = 0
    for t, p in panel.items():
        if D not in p.index or t not in rows:
            continue
        r, pub = p.loc[D], rows[t]
        if pd.notna(r["sma50"]) and pub.get("sma50_dist") is not None:
            mine = r["close"] / r["sma50"] - 1
            d_sma.append(abs(mine - pub["sma50_dist"]))
            mine_above += mine > 0
            pub_above += pub["sma50_dist"] > 0
            sma_sign_dis += (mine > 0) != (pub["sma50_dist"] > 0)
        if pd.notna(r["max_h_252"]) and pub.get("high_52w") is not None:
            mine_h = r["close"] / r["max_h_252"] - 1
            d_hi_high.append(abs(mine_h - pub["high_52w"]))
            d_hi_close.append(abs(r["close"] / p.loc[:D, "close"].tail(WIN_52W).max() - 1
                                  - pub["high_52w"]))
            hi_flag_dis += (mine_h >= NEW_HIGH_THRESHOLD) != (pub["high_52w"] >= NEW_HIGH_THRESHOLD)

    med_high, med_close = float(np.median(d_hi_high)), float(np.median(d_hi_close))
    print(f"  control on {asof}: n={len(d_sma)}")
    print(f"    sma50 dist   median |diff| {np.median(d_sma):.5f}  max {max(d_sma):.4f}"
          f"  sign disagreements {sma_sign_dis}")
    print(f"    above-50sma count  mine {mine_above} / published {pub_above}")
    print(f"    52w high (HIGH)  median |diff| {med_high:.5f}   <- used")
    print(f"    52w high (CLOSE) median |diff| {med_close:.5f}   <- negative arm")
    print(f"    new-high flag disagreements {hi_flag_dis}")
    assert sma_sign_dis == 0, "50-day ruler disagrees in sign with the published one"
    assert hi_flag_dis == 0, "52-week new-high flag disagrees with the published one"
    assert med_close > med_high * 5, (
        "close-based 52w window is no longer visibly worse than the high-based one -- "
        "the control can no longer tell the two apart, so it proves nothing")


def count_day(panel: dict, tickers: list[str], industry: dict, D: pd.Timestamp) -> dict:
    n50 = a50 = n200 = a200 = 0
    nh52 = nl52 = nh4 = nl4 = g52 = g4 = present = 0
    for t in tickers:
        p = panel.get(t)
        if p is None or D not in p.index:
            continue
        r = p.loc[D]
        present += 1
        if pd.notna(r["sma50"]):
            n50 += 1
            a50 += r["close"] > r["sma50"]
        if pd.notna(r["sma200"]):
            n200 += 1
            a200 += r["close"] > r["sma200"]
        if industry.get(t) in EXCLUDED_INDUSTRIES:
            continue                       # common-stock type gate
        bn = int(r["bars_n"])
        if bn >= MIN_BARS_52W and pd.notna(r["max_h_252"]):
            g52 += 1
            nh52 += r["close"] / r["max_h_252"] - 1 >= NEW_HIGH_THRESHOLD
            nl52 += r["close"] / r["min_l_252"] - 1 <= NEW_LOW_THRESHOLD
        if bn >= MIN_BARS_4W and pd.notna(r["max_h_20"]):
            g4 += 1
            nh4 += r["close"] / r["max_h_20"] - 1 >= NEW_HIGH_THRESHOLD
            nl4 += r["close"] / r["min_l_20"] - 1 <= NEW_LOW_THRESHOLD
    return dict(n50=n50, a50=int(a50), n200=n200, a200=int(a200),
                nh52=int(nh52), nl52=int(nl52), g52=g52,
                nh4=int(nh4), nl4=int(nl4), g4=g4, present=present)


def pct(a: int, n: int):
    return round(a / n * 100, 2) if n else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(Path(__file__).resolve().parent))
    args = ap.parse_args()
    outdir = Path(args.outdir)

    pool = load_pool(REPO)
    print(f"pool as of {pool['as_of']}: "
          + ", ".join(f"{g}={len(pool['groups'][g])}" for g in GROUPS)
          + f", union={len(pool['pool'])}")

    industry = load_industries(REPO, pool["pool"])
    shells = [t for t, i in industry.items() if i in EXCLUDED_INDUSTRIES]
    print(f"  type gate removes {len(shells)} name(s): {shells or 'none'}")

    arch = pd.read_csv(REPO / "data/history/breadth_archive.csv")
    sessions = [d for d in arch["date"] if d >= WINDOW_START]
    if not sessions:
        raise SystemExit("breadth_archive has no sessions in the window")
    last = sessions[-1]
    print(f"  {len(sessions)} sessions, {sessions[0]} -> {last}")

    bars = download(pool["pool"], end=str(pd.Timestamp(last) + pd.Timedelta(days=1))[:10])
    print(f"  bars for {len(bars)}/{len(pool['pool'])} names")
    panel = panels(bars)
    verify_control(panel, REPO, last)

    recs = []
    for ds in sessions:
        D = pd.Timestamp(ds)
        u = count_day(panel, pool["pool"], industry, D)
        rec = {
            "date": ds,
            "semi_pct_above_50sma": pct(u["a50"], u["n50"]),
            "semi_above_50sma_n": u["a50"],
            "semi_n_with_sma50": u["n50"],
            "semi_pct_above_200sma": pct(u["a200"], u["n200"]),
            "semi_n_with_sma200": u["n200"],
            "semi_new_highs_common": u["nh52"],
            "semi_new_lows_common": u["nl52"],
            "semi_n_gate_52w": u["g52"],
            "semi_new_highs_4w_common": u["nh4"],
            "semi_new_lows_4w_common": u["nl4"],
            "semi_n_gate_4w": u["g4"],
            "semi_pool_present": u["present"],
        }
        for g, short in (("Semiconductors Large Caps", "largecap"),
                         ("Memory & Storage", "memory"),
                         ("Semiconductors Broad", "broad")):
            s = count_day(panel, pool["groups"][g], industry, D)
            rec[f"pct_above_50sma_{short}"] = pct(s["a50"], s["n50"])
            rec[f"n_with_sma50_{short}"] = s["n50"]
        recs.append(rec)

    semi = pd.DataFrame(recs)
    mkt = arch[arch.date.isin(sessions)][[
        "date", "pct_above_50sma", "pct_above_200sma", "new_highs_common",
        "new_lows_common", "new_highs_4w_common", "new_lows_4w_common",
        "universe_size", "common_universe"]].rename(columns={
            "pct_above_50sma": "mkt_pct_above_50sma",
            "pct_above_200sma": "mkt_pct_above_200sma",
            "new_highs_common": "mkt_new_highs_common",
            "new_lows_common": "mkt_new_lows_common",
            "new_highs_4w_common": "mkt_new_highs_4w_common",
            "new_lows_4w_common": "mkt_new_lows_4w_common",
            "universe_size": "mkt_universe_size",
            "common_universe": "mkt_common_universe"})
    df = semi.merge(mkt, on="date", how="left")
    df["spread_50sma"] = (df.semi_pct_above_50sma - df.mkt_pct_above_50sma).round(2)
    df["spread_200sma"] = (df.semi_pct_above_200sma - df.mkt_pct_above_200sma).round(2)

    outdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(outdir / "semi_breadth_series.csv", index=False)
    (outdir / "pool_members.json").write_text(json.dumps(pool, indent=1) + "\n")
    print(f"  wrote {outdir/'semi_breadth_series.csv'} ({len(df)} rows)")

    cross = df[df.spread_50sma > 0]
    print("\nsummary")
    print(f"  semi %>50sma  {df.semi_pct_above_50sma.iloc[0]} -> {df.semi_pct_above_50sma.iloc[-1]}"
          f"  (window low {df.semi_pct_above_50sma.min()}, high {df.semi_pct_above_50sma.max()})")
    print(f"  mkt  %>50sma  {df.mkt_pct_above_50sma.iloc[0]} -> {df.mkt_pct_above_50sma.iloc[-1]}")
    print(f"  spread        {df.spread_50sma.iloc[0]:+} -> {df.spread_50sma.iloc[-1]:+}"
          f"  (min {df.spread_50sma.min():+}, max {df.spread_50sma.max():+})")
    print(f"  first session semis lead: {cross.date.iloc[0] if len(cross) else 'never'}")
    print(f"  pool 52w new highs, whole window: {int(df.semi_new_highs_common.sum())}")
    print(f"  pool 52w new lows,  whole window: {int(df.semi_new_lows_common.sum())}")
    print(f"  spread on 200sma  {df.spread_200sma.iloc[0]:+} -> {df.spread_200sma.iloc[-1]:+}"
          f"  (min {df.spread_200sma.min():+}, max {df.spread_200sma.max():+},"
          f" sessions semis trail: {int((df.spread_200sma < 0).sum())})")


if __name__ == "__main__":
    main()
