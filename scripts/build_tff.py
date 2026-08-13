#!/usr/bin/env python3
"""Build Jones' three TFF tables for the S&P and read today against them.

Jones built his on 210 days of T-bond Liquidity Data Bank reports. He notes the
tables are instrument-specific and that he intended to extend them to other
markets; @TailThatWagsDog says the same thing about doing it for the S&P —
"same principle, different instrument". This is that baseline for us.

Two instruments: SPX because our levels are denominated in it, SPY because that
is his model surface. Ticks are chosen to be equivalent (SPX 2.5 ≈ SPY 0.25 at a
10:1 index ratio) so the two readings are comparable in shape, though never in
magnitude — a TPO count is denominated in ticks and does not travel.

Usage:
    .venv/bin/python scripts/build_tff.py --months 6
    .venv/bin/python scripts/build_tff.py --date 20260812
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.marketcal import MARKET_TZ, market_now
from pipeline.profile import tff as T

OUT = Path("data/profile")
INSTRUMENTS = {"SPX": 2.5, "SPY": 0.25}
MIN_BRACKETS = 8


def _sessions(bars) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for b in bars:
        out[str(b.date)[:10]].append({"low": b.low, "high": b.high,
                                      "close": b.close})
    return {d: bs for d, bs in out.items() if len(bs) >= MIN_BRACKETS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6)
    ap.add_argument("--date", help="YYYYMMDD (ET) to read. Default: the last "
                                   "complete session in the pull.")
    args = ap.parse_args()

    from ib_async import IB, Index, Stock
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=179, timeout=10)
            break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")

    doc = {"generated_at": market_now().isoformat(timespec="seconds"),
           "months": args.months, "source": "Jones, S&C 6:9 (1988)",
           "instruments": {}}
    try:
        for name, tick in INSTRUMENTS.items():
            c = Index("SPX", "CBOE") if name == "SPX" else Stock(name, "SMART", "USD")
            ib.qualifyContracts(c)
            bars = ib.reqHistoricalData(
                c, endDateTime="", durationStr=f"{args.months} M",
                barSizeSetting="30 mins", whatToShow="TRADES", useRTH=True,
                formatDate=1, timeout=180)
            S = _sessions(bars)
            day = args.date and f"{args.date[:4]}-{args.date[4:6]}-{args.date[6:]}"
            day = day or sorted(S)[-1]
            today = S.get(day)
            # The day being read must not also sit in the baseline it is ranked
            # against: a session cannot help set the standard it is measured by.
            hist = {d: v for d, v in S.items() if d != day}

            tables = {m: T.build_table(hist, tick, measure=m) for m in T.MEASURES}
            reading = T.read(today, tick, tables) if today else None
            doc["instruments"][name] = {
                "tick": tick, "session_read": day,
                "baseline_sessions": tables["tpo"]["n_sessions"],
                "reading": reading,
                "percentile_line": (T.percentile_line(today, tick, hist)
                                    if today else None),
                "tables": tables,
            }
            print(f"\n{'='*62}\n{name}  tick {tick}  —  baseline "
                  f"{tables['tpo']['n_sessions']} sessions, reading {day}")
            if not reading or not reading.get("measurable"):
                print(f"  unmeasurable: {(reading or {}).get('note', 'no session')}")
                continue
            for m in T.MEASURES:
                r = reading["measures"][m]
                flag = "  AMBIGUOUS" if r.get("ambiguous") else ""
                mono = "" if r.get("column_monotone") else "  (column not monotone)"
                print(f"  {m:<6} value {r['value']:>9,.2f}   TFF {r['tff']:>5.0%}   "
                      f"{r['band']}{flag}{mono}")
            print(f"  -> {reading['note']}")
            print(f"  cardinal rule — non-facilitating? "
                  f"{T.is_non_facilitating(reading)}")

            # Where does it sit against the summer, on his own claim's terms?
            fin = sorted((v[-1], d) for d, v in
                         ((d, T.tpo_line(bs, tick)) for d, bs in S.items())
                         if len(v) == max(len(T.tpo_line(b, tick)) for b in S.values()))
            if today:
                rank = [d for _, d in fin].index(day) + 1 if day in [d for _, d in fin] else None
                if rank:
                    print(f"  raw rank by final TPO count: {rank} of {len(fin)} "
                          f"(1 = quietest).  quietest 5: "
                          + ", ".join(f"{d} ({v})" for v, d in fin[:5]))
    finally:
        ib.disconnect()

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "tff_tables.json"
    p.write_text(json.dumps(doc, indent=2))
    print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
