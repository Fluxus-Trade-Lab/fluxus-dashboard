#!/usr/bin/env python3
"""Pilot: how often does the Structure Pivot setup FAIL, and what does a naive
backfill of that event cost?

Answers the ammunition gap logged as x_watch 取件账 09-25n·3 — Linda Raschke on
2026-09-25 on corn: "failed test, and once it takes out the last pivot there is
usually more to come". How much more, and for how long, we had never measured.

What this probe settles (it is a sizing probe, not the study):
  * the EVENT already exists in code. `pipeline/screeners/structure_pivot.py`
    computes `failed_today` every night for the whole universe
    (`pipeline/adapters/yfinance_adapter.py:1259`) and then DROPS it --
    `Result.to_row()` never emits it and `SP_FIELDS` never lists it
    (yfinance_adapter.py:623). Nothing is archived, so nothing can be measured.
  * the event rate, which decides whether an archive is worth the row count.
  * the cost of backfilling it the naive way (call `SP.run` once per bar), which
    is the obvious implementation and the wrong one -- `run()` is ALREADY a
    bar-by-bar simulation, so replaying it per bar is quadratic.

Run:  .venv/bin/python data/research/ammo_gaps_2026-09-27/probe_pivot_fail_rate.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pipeline.screeners import structure_pivot as SP  # noqa: E402

OUT = Path(__file__).resolve().parent / "pivot_fail_pilot.json"
WARMUP = 250        # bars handed to the first call; SP needs history to have pivots at all
UNIVERSE_SIZE = 5600   # Finviz pool, order of magnitude only


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickers", nargs="+", default=["AMD", "NVDA", "SPY"])
    a = ap.parse_args()

    import yfinance as yf
    data = yf.download(a.tickers, period="2y", interval="1d",
                       auto_adjust=False, progress=False, group_by="ticker")

    per_ticker, evals = [], 0
    t0 = time.time()
    for t in a.tickers:
        df = data[t].rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
        if len(df) <= WARMUP:
            continue
        hits = [str(df.index[i].date()) for i in range(WARMUP, len(df))
                if getattr(SP.run(df.iloc[:i + 1]), "failed_today", False)]
        bars = len(df) - WARMUP
        evals += bars
        per_ticker.append({"ticker": t, "sessions": bars, "fail_events": len(hits),
                           "per_year": round(252 * len(hits) / bars, 1),
                           "dates": hits})
    elapsed = time.time() - t0

    res = {"warmup_bars": WARMUP, "per_ticker": per_ticker,
           "naive_replay": {
               "evaluations": evals,
               "seconds": round(elapsed, 1),
               "ms_per_evaluation": round(1000 * elapsed / evals, 1),
               "projected_hours_full_universe_1y":
                   round(elapsed / evals * UNIVERSE_SIZE * 252 / 3600, 1),
               "note": "naive == calling SP.run once per bar. Do not build the "
                       "backfill this way; emit per-bar state from one pass."}}
    OUT.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "per_ticker"}, indent=2))
    for r in per_ticker:
        print(f"{r['ticker']}: {r['fail_events']} fail events in {r['sessions']} "
              f"sessions ({r['per_year']}/yr)")


if __name__ == "__main__":
    main()
