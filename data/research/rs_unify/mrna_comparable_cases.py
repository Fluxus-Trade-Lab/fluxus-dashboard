"""T-1002-03 追加要求: "排名适合筛选、不适合提示变化" -- find stocks shaped like the
MRNA case (already strong by rs_rating standard, RS line newly spiking from a
mid reading to a short-window high) and show what happened next, including the
ones that did NOT go on to rally. A single hand-picked example (MRNA) proves
nothing; this script scans the whole panel built by rs_compare.py so the
comparison set is not cherry-picked after the fact.

Shape definition (operationalized, not from any external standard -- flagged
as self-built per METRIC_SOURCES.md convention):
  - rs_line_21 (RS line self-percentile, 21d window) was <= 60 at t-10 trading
    days and reaches >= 95 at date t (a *new* short-window RS-line high, not a
    stock that had already been at the top for weeks)
  - rs_rating stays in [80, 96] for the entire [t-10, t] window (the stock is
    *already* a recognized leader by the ranking metric -- ranking is not
    moving, only the line is) -- this is the MRNA shape: rs_rating ~89-93
    while RS line goes 10 -> 100
  - events for the same ticker are de-duplicated with a 60-session gap

Run: python3 data/research/rs_unify/mrna_comparable_cases.py
Requires the cached panel built by `rs_compare.py --fetch` (same cache file).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rs_compare import CACHE, BENCH, build_features  # noqa: E402

OUT = Path("data/research/rs_unify/mrna_comparable_cases.json")
LOOKBACK = 10
GAP = 60
RS_LINE_LOW = 60
RS_LINE_HIGH = 95
RATING_BAND = (80, 96)
HORIZONS = (20, 63)


def find_events(f: dict) -> list[dict]:
    rs_line = f["rs_line_21"]
    rs_rating = f["rs_rating"]
    dates = rs_line.index
    events = []
    for ticker in rs_line.columns:
        if ticker == BENCH:
            continue
        line = rs_line[ticker]
        rating = rs_rating[ticker]
        last_event_i = -GAP
        for i in range(LOOKBACK, len(dates)):
            if i - last_event_i < GAP:
                continue
            today, before = line.iloc[i], line.iloc[i - LOOKBACK]
            if pd.isna(today) or pd.isna(before):
                continue
            if not (before <= RS_LINE_LOW and today >= RS_LINE_HIGH):
                continue
            window_rating = rating.iloc[i - LOOKBACK:i + 1]
            if window_rating.isna().any():
                continue
            if not ((window_rating >= RATING_BAND[0]) & (window_rating <= RATING_BAND[1])).all():
                continue
            events.append({"ticker": ticker, "date_idx": i, "date": str(dates[i].date())})
            last_event_i = i
    return events


def main() -> None:
    if not CACHE.exists():
        raise SystemExit("run `python3 data/research/rs_unify/rs_compare.py --fetch` first")
    close = pd.read_pickle(CACHE)
    f = build_features(close)
    events = find_events(f)
    print(f"{len(events)} MRNA-shaped events found across panel "
          f"({close.shape[1]-1} tickers, {close.shape[0]} sessions)")

    fwd20, fwd63 = f["fwd"][20], f["fwd"][63]
    rows = []
    for e in events:
        i, t = e["date_idx"], e["ticker"]
        dt = f["rs_line_21"].index[i]
        row = {
            "ticker": t, "date": e["date"],
            "rs_line_21_before": round(float(f["rs_line_21"][t].iloc[i - LOOKBACK]), 1),
            "rs_line_21_at": round(float(f["rs_line_21"][t].iloc[i]), 1),
            "rs_rating_at": round(float(f["rs_rating"][t].iloc[i]), 1),
            "fwd20_excess_pct": round(float(fwd20[t].loc[dt]) * 100, 2) if dt in fwd20.index and not pd.isna(fwd20[t].loc[dt]) else None,
            "fwd63_excess_pct": round(float(fwd63[t].loc[dt]) * 100, 2) if dt in fwd63.index and not pd.isna(fwd63[t].loc[dt]) else None,
        }
        rows.append(row)

    complete = [r for r in rows if r["fwd20_excess_pct"] is not None]
    complete.sort(key=lambda r: r["fwd20_excess_pct"])
    mrna_rows = [r for r in rows if r["ticker"] == "MRNA"]

    n = len(complete)
    sample = []
    if n:
        # deliberately span the outcome distribution: worst 3, middle 2, best 3
        idxs = sorted(set([0, 1, 2, n // 2 - 1, n // 2, n - 3, n - 2, n - 1]) & set(range(n)))
        sample = [complete[i] for i in idxs]
    # make sure MRNA's own event (if it independently qualified) is included
    for mr in mrna_rows:
        if mr not in sample:
            sample.append(mr)

    hit_rate_20 = float(np.mean([r["fwd20_excess_pct"] > 0 for r in complete])) if complete else None
    hit_rate_63 = float(np.mean([r["fwd63_excess_pct"] > 0 for r in complete if r["fwd63_excess_pct"] is not None])) if complete else None

    out = {
        "definition": "rs_line_21 <=60 at t-10 sessions then >=95 at t, "
                       "while rs_rating stays in [80,96] across the whole "
                       "[t-10,t] window -- self-built shape filter, not a "
                       "published standard (see METRIC_SOURCES.md)",
        "n_events_total": len(events),
        "n_events_with_fwd20": n,
        "hit_rate_fwd20_positive": round(hit_rate_20, 3) if hit_rate_20 is not None else None,
        "hit_rate_fwd63_positive": round(hit_rate_63, 3) if hit_rate_63 is not None else None,
        "mean_fwd20_excess_pct": round(float(np.mean([r["fwd20_excess_pct"] for r in complete])), 2) if complete else None,
        "median_fwd20_excess_pct": round(float(np.median([r["fwd20_excess_pct"] for r in complete])), 2) if complete else None,
        "mrna_events": mrna_rows,
        "sample_spanning_outcomes": sample,
        "note": "all_events (3,428 rows) omitted from this file to avoid "
                "repo bloat -- rerun this script (needs the panel cache from "
                "`rs_compare.py --fetch`) to regenerate the full event list; "
                "this file keeps only the summary stats, MRNA's own events, "
                "and the outcome-spanning sample used in the proposal.",
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"hit_rate(fwd20>0)={hit_rate_20} mean_fwd20={out['mean_fwd20_excess_pct']}% "
          f"median_fwd20={out['median_fwd20_excess_pct']}%  n={n}")
    for r in sample:
        print(r)


if __name__ == "__main__":
    main()
