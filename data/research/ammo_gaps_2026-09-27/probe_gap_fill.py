#!/usr/bin/env python3
"""Pilot: how much of a TRUE gap comes back in the first hour (SPY, 3 years).

Answers the ammunition gap logged as x_watch 取件账 09-24n·6 — Linda Raschke's
pre-open plan on 2026-09-24 was "SP opens under yesterday's low, it's a true
gap, first thing I watch is how much of it the first hour gives back", and we
had no distribution to answer with.

口径 (registered in data/reference/METRIC_SOURCES.md, section 2026-09-27):
  * TRUE GAP = StockCharts ChartSchool "Full Gap": open ABOVE the prior
    session's HIGH (up) or BELOW the prior session's LOW (down). A gap that
    only clears the prior CLOSE is a Partial Gap and is counted separately.
    https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/gap-trading-strategies
  * FILL TARGET = the prior session's CLOSE. "Filling the gap" in the standard
    sense means trading back to the last price before the gap.
    https://chartschool.stockcharts.com/table-of-contents/chart-analysis/gaps-and-gap-analysis
  * fill fraction = retrace_toward_prior_close / (open - prior_close), signed
    so that 1.0 == the gap fully closed. THIS RATIO IS OURS, not a standard
    reading: the standard defines the binary "filled / not filled", not a
    fraction. See the memo for why the denominator choice moves the headline
    (median 0.43 against the prior close vs 0.86 against the prior extreme).
  * FIRST HOUR = the 09:30 ET hourly bar. yfinance's 1h bars for US equities
    start at 09:30, so bar[0] IS the first hour; no resampling.
  * size floors in ATR(14) are ours, and are reported as a sweep rather than
    picked, because a gap of one cent over the prior high has a denominator
    near zero and would otherwise dominate the ratio.

Run:  .venv/bin/python data/research/ammo_gaps_2026-09-27/probe_gap_fill.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "gap_fill_pilot.json"


def load(symbol: str) -> pd.DataFrame:
    """Daily OHLC joined to the 09:30 ET hourly bar, one row per session."""
    import yfinance as yf

    d = yf.download(symbol, period="3y", interval="1d",
                    auto_adjust=False, progress=False)
    h = yf.download(symbol, period="730d", interval="1h",
                    auto_adjust=False, progress=False)
    for f in (d, h):
        if isinstance(f.columns, pd.MultiIndex):
            f.columns = [c[0] for c in f.columns]
    d = d.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    h = h.rename(columns=str.lower)
    h.index = h.index.tz_convert("America/New_York")
    first = h[(h.index.hour == 9) & (h.index.minute == 30)]
    first.index = pd.DatetimeIndex([t.date() for t in first.index])
    d.index = pd.DatetimeIndex([t.date() for t in d.index])

    j = d.join(first[["high", "low", "close"]].add_prefix("h1_"), how="inner")
    j["prev_close"] = j["close"].shift(1)
    j["prev_high"] = j["high"].shift(1)
    j["prev_low"] = j["low"].shift(1)
    tr = pd.concat([d["high"] - d["low"],
                    (d["high"] - d["close"].shift()).abs(),
                    (d["low"] - d["close"].shift()).abs()], axis=1).max(axis=1)
    j["atr14"] = tr.rolling(14).mean().shift(1)   # shifted: today's ATR is not an input to today
    return j.dropna()


def measure(j: pd.DataFrame) -> dict:
    up = j["open"] > j["prev_high"]
    dn = j["open"] < j["prev_low"]
    part_up = (j["open"] > j["prev_close"]) & ~up
    part_dn = (j["open"] < j["prev_close"]) & ~dn

    tg = j[up | dn].copy()
    tg["dir"] = np.where(up[up | dn], 1, -1)
    tg["gap"] = (tg["open"] - tg["prev_close"]) * tg["dir"]
    tg["gap_atr"] = tg["gap"] / tg["atr14"]
    tg["retrace"] = np.where(tg["dir"] > 0, tg["open"] - tg["h1_low"],
                             tg["h1_high"] - tg["open"])
    tg["fill"] = tg["retrace"] / tg["gap"]
    tg["closed_h1"] = np.where(tg["dir"] > 0, tg["h1_low"] <= tg["prev_close"],
                               tg["h1_high"] >= tg["prev_close"])

    def cut(sub, label):
        q = sub["fill"].quantile([0.25, 0.5, 0.75])
        return {"label": label, "n": int(len(sub)),
                "fill_p25": round(float(q[0.25]), 3),
                "fill_median": round(float(q[0.5]), 3),
                "fill_p75": round(float(q[0.75]), 3),
                "closed_in_hour1": round(float(sub["closed_h1"].mean()), 3)}

    # The alternate denominator, measured rather than asserted: the memo claims
    # the headline moves when you divide by the gap against the prior EXTREME
    # instead of the prior CLOSE. That claim needs its own numbers, and the p90
    # is the point -- a gap one cent past the prior high has a denominator near
    # zero, so the ratio has no upper bound and the tail is the whole story.
    alt_gap = (tg["open"] - np.where(tg["dir"] > 0, tg["prev_high"], tg["prev_low"])) * tg["dir"]
    alt_fill = tg["retrace"] / alt_gap
    alt = {"median": round(float(alt_fill.median()), 3),
           "p90_all": round(float(alt_fill.quantile(0.9)), 1),
           "p90_under_025atr": round(float(alt_fill[tg.gap_atr < 0.25].quantile(0.9)), 1),
           "p90_over_025atr": round(float(alt_fill[tg.gap_atr >= 0.25].quantile(0.9)), 1)}

    return {
        "sessions": int(len(j)),
        "first_session": str(j.index[0].date()),
        "last_session": str(j.index[-1].date()),
        "full_gap_up": int(up.sum()), "full_gap_down": int(dn.sum()),
        "partial_gap_up": int(part_up.sum()), "partial_gap_down": int(part_dn.sum()),
        "sweep": [cut(tg, "all true gaps"),
                  cut(tg[tg.gap_atr >= 0.25], "gap >= 0.25 ATR"),
                  cut(tg[tg.gap_atr >= 0.50], "gap >= 0.50 ATR")],
        "alt_denominator_prior_extreme": alt,
        "by_direction_025atr": {
            "up": cut(tg[(tg.gap_atr >= 0.25) & (tg.dir > 0)], "up"),
            "down": cut(tg[(tg.gap_atr >= 0.25) & (tg.dir < 0)], "down")},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", default="SPY")
    a = ap.parse_args()
    j = load(a.symbol)
    if len(j) < 100:
        sys.exit(f"only {len(j)} joined sessions -- the hourly feed came back short, "
                 "not a result")
    res = {"symbol": a.symbol, **measure(j)}
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
