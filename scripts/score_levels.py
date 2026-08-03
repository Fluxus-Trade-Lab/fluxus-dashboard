#!/usr/bin/env python3
"""Score published levels against the session that followed them.

Reads the append-only levels log, pairs each day's final published state with
the NEXT session's OHLC from IBKR, and prints a cumulative table. Levels are
scored forward only — scoring against the same session they were published in
would be hindsight.

Publish the output whether or not it flatters us; a scorecard that only appears
after good weeks is marketing, not a record.

Usage:
    .venv/bin/python scripts/score_levels.py --symbol SPX
    .venv/bin/python scripts/score_levels.py --md            # markdown for pasting
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.reference import levels_log as LL
from pipeline.reference.scorecard import score_session, summarise

OUT = Path("data/reference")


def _fetch_bars(symbol: str, days: int = 60) -> dict[str, dict]:
    """{YYYY-MM-DD: {open,high,low,close}} of RTH daily bars."""
    from ib_async import IB, Index, Stock
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=115, timeout=10)
            break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")
    try:
        c = Index(symbol, "CBOE") if symbol in ("SPX", "VIX") else Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr=f"{days} D",
                                    barSizeSetting="1 day", whatToShow="TRADES",
                                    useRTH=True, formatDate=1)
        return {str(b.date): {"date": str(b.date), "open": b.open, "high": b.high,
                              "low": b.low, "close": b.close} for b in bars}
    finally:
        ib.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--log", default=str(LL.DEFAULT_LOG))
    ap.add_argument("--md", action="store_true", help="emit markdown")
    args = ap.parse_args()

    rows = LL.read(args.log)
    if not rows:
        sys.exit(f"levels log empty at {args.log} — run build_snapshot first")
    per_day = LL.last_entry_per_day(rows, args.symbol)
    bars = _fetch_bars(args.symbol)
    sessions = sorted(bars)

    results = []
    for day, entry in sorted(per_day.items()):
        # the first session STRICTLY AFTER the publication day
        nxt = next((s for s in sessions if s > day), None)
        if not nxt:
            continue
        results.extend(score_session(entry, bars[nxt]))

    if not results:
        sys.exit("nothing scoreable yet — need at least one published day with a "
                 "following session")
    s = summarise(results)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"scorecard_{args.symbol}.json").write_text(
        json.dumps({"results": results, "summary": s}, indent=2))

    if args.md:
        print(f"# {args.symbol} levels scorecard\n")
        print("| Level | Held | Broke | Untested | Held % (of tested) |")
        print("|---|---|---|---|---|")
        for name, b in s["by_level"].items():
            pct = f"{b['held_pct']:.0f}%" if b["held_pct"] is not None else "—"
            print(f"| {name} | {b['held']} | {b['broke']} | {b['untested']} | {pct} |")
        t = s["total"]
        pct = f"{t['held_pct']:.0f}%" if t["held_pct"] is not None else "—"
        print(f"| **total** | {t['held']} | {t['broke']} | {t['untested']} | **{pct}** |")
        print(f"\n*{len(per_day)} published sessions. Levels scored against the "
              f"following session only. 'Untested' is counted separately and is not "
              f"folded into the rate.*")
    else:
        print(f"scored {len(results)} levels across {len(per_day)} published sessions")
        print(f"{'level':<20}{'held':>6}{'broke':>7}{'untest':>8}{'held% (tested)':>16}")
        for name, b in s["by_level"].items():
            pct = f"{b['held_pct']:.1f}%" if b["held_pct"] is not None else "n/a"
            print(f"{name:<20}{b['held']:>6}{b['broke']:>7}{b['untested']:>8}{pct:>16}")
        t = s["total"]
        pct = f"{t['held_pct']:.1f}%" if t["held_pct"] is not None else "n/a"
        print(f"{'TOTAL':<20}{t['held']:>6}{t['broke']:>7}{t['untested']:>8}{pct:>16}")
        print(f"\nwrote {OUT / f'scorecard_{args.symbol}.json'}")


if __name__ == "__main__":
    main()
