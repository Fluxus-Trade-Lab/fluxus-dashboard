"""Delayed-EP ledger: the read `delayed_ep_scan --review` does, plus the four
things it is missing.

Nighty Zac, 2026-09-01. `--review` had never been run since the ledger was
built (2026-08-13). Its first run printed six numbers and no way to judge any
of them:

  1. NO BENCHMARK. "basing +5d: median -1.4%" is unreadable without the
     market's own move over the identical windows.
  2. NO CONTROL. Nothing answers "does the stage label separate anything at
     all?" -- for that you need the pooled read across every row.
  3. n IS NOT INDEPENDENCE. It printed "n=31" for basing +10d. Those 31 rows
     come from TWO as-of dates. One market move is inside all of them. The
     honest unit is the session, not the row, so every cell here reports
     dates= alongside n= and the CI resamples whole dates.
  4. THE SESSION GRID CAME FROM THE FEED. `--review` counts forward sessions by
     indexing whatever rows yfinance returned. If the feed drops a session, the
     count silently slides onto the wrong day. It did: see below.

FEED GAP (measured 2026-09-01 04:5x JST): 2026-08-28 is a trading day by
pipeline.marketcal, our ledger holds 28 rows stamped with it, and the closes
stored that night differ from both the 08-27 and 08-31 closes -- so the bar
existed. Yahoo no longer returns it, for 46/46 tickers tried, across four
different query spellings. This script therefore takes its session grid from
marketcal and requires the exact target date to be present in the feed; an
observation whose endpoint is missing is DROPPED and counted, never slid onto
the next available bar.

It also refuses any endpoint later than last_completed_session(), because
during an open session yfinance returns a live partial bar dated today.

Read-only. Prints; writes nothing into data/.

Run from the repo root:  PYTHONPATH=. python3 \
    data/research/delayed_ep_review_2026-09/review_benchmarked.py
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from pipeline.marketcal import is_trading_day, last_completed_session

LOG = Path("data/history/delayed_ep_log.csv")
BENCH = "SPY"
HORIZONS = (3, 5, 10)
STAGES = ("breaking", "basing", "drifting", "failed")


def trading_grid(start: dt.date, end: dt.date) -> list[str]:
    out, d = [], start
    while d <= end:
        if is_trading_day(d):
            out.append(str(d))
        d += dt.timedelta(days=1)
    return out


def load_log(path: Path = LOG) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def fetch(tickers: list[str]) -> dict[str, dict[str, float]]:
    """Unadjusted daily closes as {ticker: {YYYY-MM-DD: close}}. Same
    auto_adjust=False the scanner uses, so the stored close is comparable."""
    raw = yf.download(tickers, period="120d", interval="1d", group_by="ticker",
                      auto_adjust=False, progress=False, threads=True)
    out: dict[str, dict[str, float]] = {}
    for t in tickers:
        try:
            s = raw[t]["Close"].dropna() if len(tickers) > 1 else raw["Close"].dropna()
        except KeyError:
            continue
        if len(s):
            out[t] = {str(i.date()): float(v) for i, v in s.items()}
    return out


def block_bootstrap_median(vals, blocks, n_boot=4000, seed=7):
    """CI on the median, resampling whole AS-OF DATES rather than rows.

    Rows are not independent: on one session the same market move sits inside
    every name's forward window. Resampling rows reports a CI several times too
    tight. With very few distinct dates this bootstrap has a RESOLUTION FLOOR --
    k dates can only produce so many distinct resamples -- so the caller prints
    dates= next to every interval and the reader is expected to discount it."""
    if not vals:
        return (None, None)
    rng = np.random.default_rng(seed)
    by_block: dict[str, list[float]] = {}
    for v, b in zip(vals, blocks):
        by_block.setdefault(b, []).append(v)
    keys = list(by_block)
    meds = []
    for _ in range(n_boot):
        pick = rng.choice(len(keys), size=len(keys), replace=True)
        pool = [v for i in pick for v in by_block[keys[i]]]
        if pool:
            meds.append(float(np.median(pool)))
    if not meds:
        return (None, None)
    return (float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5)))


def describe(name: str, rows: list[tuple[float, str]]) -> str:
    if not rows:
        return f"  {name:>24}  (n=0)"
    vals = [r[0] for r in rows]
    blocks = [r[1] for r in rows]
    lo, hi = block_bootstrap_median(vals, blocks)
    med = float(np.median(vals))
    pos = sum(1 for v in vals if v > 0) / len(vals) * 100
    nd = len(set(blocks))
    ci = f"[{lo*100:+.1f},{hi*100:+.1f}]" if lo is not None else "[--]"
    flag = "  <-- dates<4, no resolution" if nd < 4 else ""
    return (f"  {name:>24}  med {med*100:+5.1f}%  CI {ci:>15}  "
            f"n={len(vals):<4} dates={nd:<3} >0:{pos:3.0f}%{flag}")


def main() -> int:
    log = load_log()
    tickers = sorted({r["ticker"] for r in log})
    log_dates = sorted({r["as_of"] for r in log})
    last_ok = str(last_completed_session())
    grid = trading_grid(dt.date.fromisoformat(log_dates[0]), dt.date.fromisoformat(last_ok))
    pos = {d: i for i, d in enumerate(grid)}
    print(f"log: {len(log)} rows | {len(log_dates)} sessions "
          f"{log_dates[0]}..{log_dates[-1]} | {len(tickers)} tickers")
    print(f"marketcal grid {grid[0]}..{grid[-1]} = {len(grid)} sessions | "
          f"last completed session = {last_ok}")

    bars = fetch(tickers + [BENCH])
    if BENCH not in bars:
        print(f"FATAL: no {BENCH} bars"); return 1
    spy = bars[BENCH]

    # ------------------------------------------------- feed vs calendar
    print("\n=== FEED GAPS: sessions marketcal says exist that the feed omits ===")
    missing_days = [d for d in grid if d not in spy]
    print(f"  benchmark {BENCH} is missing: {missing_days or 'none'}")
    for d in missing_days:
        n_t = sum(1 for t in tickers if t in bars and d not in bars[t])
        n_log = sum(1 for r in log if r["as_of"] == d)
        print(f"    {d}: absent for {n_t}/{len(tickers)} logged tickers; "
              f"ledger holds {n_log} rows stamped that day")

    # ------------------------------------------------- join check
    print("\n=== JOIN CHECK: ledger's stored close vs the bar we pull today ===")
    rel, unresolvable = [], 0
    for r in log:
        t, d = r["ticker"], r["as_of"]
        if t not in bars or d not in bars[t]:
            unresolvable += 1
            continue
        rel.append(abs(bars[t][d] - float(r["close"])) / float(r["close"]))
    if rel:
        a = np.array(rel)
        print(f"  resolvable {len(rel)} rows | UNRESOLVABLE {unresolvable} "
              f"(ticker delisted, or its as-of session vanished from the feed)")
        print(f"  within 0.5%: {(a<=0.005).mean()*100:.1f}%   "
              f"within 2%: {(a<=0.02).mean()*100:.1f}%   max gap {a.max()*100:.1f}%")

    # ------------------------------------------------- forward returns
    def fwd(t: str, d: str, h: int):
        """Return over h sessions on the CALENDAR grid. None if either endpoint
        is missing from the feed or the endpoint is not a completed session."""
        i = pos.get(d)
        if i is None or i + h >= len(grid):
            return None
        tgt = grid[i + h]
        s = bars.get(t)
        if not s or d not in s or tgt not in s:
            return None
        return s[tgt] / s[d] - 1.0

    first_day: dict[tuple[str, str], dict] = {}
    for r in sorted(log, key=lambda r: (r["ticker"], r["as_of"])):
        first_day.setdefault((r["ticker"], r["stage"]), r)

    for label, rowset in (("ALL ROWS", log),
                          ("FIRST DAY IN STAGE (what --review prints)",
                           list(first_day.values()))):
        print(f"\n=== {label} ===")
        for h in HORIZONS:
            pooled: list[tuple[float, str]] = []
            per: dict[str, list[tuple[float, float, str]]] = {s: [] for s in STAGES}
            dropped = 0
            for r in rowset:
                t, d, st = r["ticker"], r["as_of"], r["stage"]
                rt, rb = fwd(t, d, h), fwd(BENCH, d, h)
                if rt is None or rb is None:
                    dropped += 1
                    continue
                pooled.append((rt - rb, d))
                if st in per:
                    per[st].append((rt, rt - rb, d))
            print(f"\n  --- +{h} sessions   ({dropped} observations dropped: "
                  f"endpoint missing or beyond {last_ok}) ---")
            print(describe("POOLED excess", pooled))
            for st in STAGES:
                print(describe(f"{st} excess", [(b, c) for _, b, c in per[st]]))

    # ------------------------------------------------- coverage
    print("\n=== WHEN CAN THIS LEDGER ANSWER ITS OWN QUESTION? ===")
    n_rows = sum(1 for r in log if r["stage"] == "breaking")
    n_first = sum(1 for k in first_day if k[1] == "breaking")
    rate = n_first / len(log_dates)
    print(f"  'breaking' -- the second entry, the whole premise of the scan --")
    print(f"    rows in ledger: {n_rows} over {len(log_dates)} sessions")
    print(f"    distinct names first seen breaking: {n_first} ({rate:.1f}/session)")
    for target in (30, 50):
        if rate > 0:
            print(f"    to reach {target} distinct names: "
                  f"~{max(0,target-n_first)/rate:.0f} more sessions")
    print("  NOTE: distinct names is the easy bar. The binding constraint is")
    print("  distinct AS-OF DATES -- see dates= above; +10d currently has 1-2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
