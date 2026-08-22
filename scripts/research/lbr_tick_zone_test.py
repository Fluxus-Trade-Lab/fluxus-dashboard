"""Zone-effectiveness test for the LBR TICK cycle replications.

Question (per Linda's semantics): do GREEN zones mark buying opportunities
(strong forward returns) and RED zones mark selling zones (weak forward
returns / elevated drawdown odds)?

Variants (all zones evaluated on SPX forward returns from ZONE-ENTRY days --
the first day of each zone episode; overlapping days would fake precision):

  A1 ours-level   USI:TICK hourly-rebuilt daily H/L, SMA15, level ±650
                  (window limited by our rebuild: ~2023-10 ->)
  A2 ours-spread  same series, spread = MA(hi)-MA(lo), rolling-252 rank,
                  buy >= 0.9 / sell <= 0.1
  B1 lector       TICK.NY daily, EMA5, spread percentrank(126) >= 85 buy /
                  <= 15 sell (his published defaults)
  C  long         TICK.NY daily, SMA15, spread rank 252, >= 0.9 / <= 0.1
                  (our construction on the longest feed: 2009-08 ->)

Baselines: all days in each variant's own evaluation window. "Linda's own"
cannot be run (TradeStation feed); A* is our best-fit replication of hers.

Usage:  python3 scripts/research/lbr_tick_zone_test.py
Output: printed table + data/research/lbr_tick_zone_results.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TVDIR = ROOT / "data/reference/breadth_tv"
OUT = ROOT / "data/research/lbr_tick_zone_results.json"


def zones_from(daily: pd.DataFrame, n: int, kind: str, mode: str,
               up=650.0, dn=-650.0, pr_len=252, pr_buy=0.9, pr_sell=0.1):
    f = (lambda s: s.rolling(n).mean()) if kind == "sma" else (lambda s: s.ewm(span=n).mean())
    m_hi, m_lo = f(daily["high"]), f(daily["low"])
    if mode == "level":
        return (m_lo <= dn), (m_hi >= up)
    spread = m_hi - m_lo
    rank = spread.rolling(pr_len).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)
    return (rank >= pr_buy), (rank <= pr_sell)


def entries(mask: pd.Series) -> pd.DatetimeIndex:
    m = mask.fillna(False)
    return m.index[m & ~m.shift(1, fill_value=False)]


def stats(days, px, fwd21, fwd63, dd21):
    days = [d for d in days if d in px.index]
    if not days:
        return {"n": 0}
    r21 = fwd21.reindex(days).dropna()
    r63 = fwd63.reindex(days).dropna()
    dd = dd21.reindex(days).dropna()
    return {"n": len(days),
            "med_fwd21": round(float(r21.median()), 4) if len(r21) else None,
            "med_fwd63": round(float(r63.median()), 4) if len(r63) else None,
            "P_dd5_21d": round(float((dd <= -0.05).mean()), 3) if len(dd) else None}


def main() -> None:
    px = pd.read_pickle(ROOT / ".cache/risk/e1_inputs.pkl")["^GSPC"].dropna()
    fwd21 = px.shift(-21) / px - 1.0
    fwd63 = px.shift(-63) / px - 1.0
    fmin = pd.concat([px.shift(-k) for k in range(1, 22)], axis=1).min(axis=1) / px - 1.0

    ours = pd.read_csv(TVDIR / "USI_TICK_hlc.csv", parse_dates=["date"]).set_index("date")
    ny = pd.read_csv(TVDIR / "USI_TICK_NY_dhlc.csv", parse_dates=["date"]).set_index("date")
    ny = ny[ny.index >= "2009-08-01"]  # single 1971 stub row before this

    variants = {
        "A1_ours_level":  zones_from(ours, 15, "sma", "level"),
        "A2_ours_spread": zones_from(ours, 15, "sma", "spread"),
        "B1_lector":      zones_from(ny, 5, "ema", "spread", pr_len=126, pr_buy=0.85, pr_sell=0.15),
        "C_long":         zones_from(ny, 15, "sma", "spread"),
    }

    results = {}
    for name, (buy, sell) in variants.items():
        window = buy.dropna().index
        base_days = [d for d in window if d in px.index]
        base = stats(base_days, px, fwd21, fwd63, fmin)
        res = {"window": [str(window[0].date()), str(window[-1].date())],
               "baseline_all_days": base,
               "buy_entries": stats(entries(buy), px, fwd21, fwd63, fmin),
               "sell_entries": stats(entries(sell), px, fwd21, fwd63, fmin)}
        results[name] = res
        b, s, ba = res["buy_entries"], res["sell_entries"], base
        print(f"\n=== {name}  window {res['window'][0]} -> {res['window'][1]}")
        print(f"    baseline (n={ba['n']}): fwd21 {ba['med_fwd21']:+.2%}  fwd63 {ba['med_fwd63']:+.2%}  P(dd5) {ba['P_dd5_21d']:.1%}")
        for tag, r in (("BUY ", b), ("SELL", s)):
            if r["n"] == 0:
                print(f"    {tag} entries: none"); continue
            print(f"    {tag} entries n={r['n']:3d}: fwd21 {r['med_fwd21']:+.2%}  fwd63 {r['med_fwd63']:+.2%}  P(dd5) {r['P_dd5_21d']:.1%}")
    OUT.write_text(json.dumps(results, indent=1))
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
