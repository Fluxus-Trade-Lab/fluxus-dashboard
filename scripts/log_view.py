#!/usr/bin/env python3
"""Log a view — one line, because a log that costs effort does not get used.

    .venv/bin/python scripts/log_view.py down 3 "puts hammered at 7700"
    .venv/bin/python scripts/log_view.py range 2
    .venv/bin/python scripts/log_view.py aside 1 "no read"
    .venv/bin/python scripts/log_view.py --machine          # from today's brief
    .venv/bin/python scripts/log_view.py --show             # what is on record

The whole point of this file is that Andy's judgement stops evaporating. Eight
months of decisions left no trace, so the merge had nothing to weigh him by and
capped him at "unproven". That number only moves by logging calls and being
right.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.centaur import log as L
from pipeline.centaur.machine_view import machine_direction
from pipeline.marketcal import market_now, market_today

ALIASES = {"aside": "stand_aside", "flat": "range", "long": "up", "short": "down",
           "up": "up", "down": "down", "range": "range", "stand_aside": "stand_aside"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("direction", nargs="?", help=f"one of {sorted(ALIASES)}")
    ap.add_argument("conviction", nargs="?", type=int, help="1, 2 or 3")
    ap.add_argument("rationale", nargs="?", default=None)
    ap.add_argument("--horizon", default="intraday", choices=("intraday", "swing"))
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--machine", action="store_true",
                    help="derive and log the machine's view from today's brief")
    ap.add_argument("--show", action="store_true", help="print the log and exit")
    ap.add_argument("--amend", action="store_true",
                    help="replace today's view for this horizon. Allowed only "
                         "before 09:30 ET; the superseded view is kept.")
    args = ap.parse_args()

    if args.show:
        rows = L.read()
        if not rows:
            print("no views on record yet")
            return
        print(f"{'session':<12}{'source':<9}{'dir':<13}{'conv':>5}  rationale")
        for r in sorted(rows, key=lambda x: (x["session"], x["source"])):
            print(f"{r['session']:<12}{r['source']:<9}{r['direction']:<13}"
                  f"{r['conviction']:>5}  {(r.get('rationale') or '')[:60]}")
        d = L.disagreements(rows)
        print(f"\n{len(L.paired(rows))} paired session(s), {len(d)} disagreement(s)"
              + (" — the rows the merge actually learns from" if d else ""))
        return

    now = market_now()
    session = str(market_today(now))
    if not L.is_trading_session(session):
        sys.exit(f"{session} is not a trading session — nothing to have a view about")

    if args.machine:
        snap = Path(f"data/snapshots/snapshot_{args.symbol}_{now:%Y%m%d}.json")
        if not snap.exists():
            sys.exit(f"no brief at {snap} — run build_snapshot.py first")
        v = machine_direction(json.loads(snap.read_text()))
        if v is None:
            sys.exit("the brief does not carry enough to state a view — "
                     "logging nothing rather than guessing")
        row = L.view(asof=now.isoformat(timespec="seconds"), session=session,
                     source="machine", direction=v["direction"],
                     conviction=v["conviction"], horizon=args.horizon,
                     rationale=v["rationale"], state_ref=str(snap))
    else:
        if not args.direction or args.conviction is None:
            ap.error("direction and conviction are required (or use --machine/--show)")
        d = ALIASES.get(args.direction.lower())
        if d is None:
            ap.error(f"direction must be one of {sorted(ALIASES)}")
        row = L.view(asof=now.isoformat(timespec="seconds"), session=session,
                     source="human", direction=d, conviction=args.conviction,
                     horizon=args.horizon, rationale=args.rationale)

    who = row["source"]
    if args.amend:
        try:
            ch = L.amend(row, now.strftime("%H:%M"))
        except ValueError as e:
            sys.exit(str(e))
        print(f"amended {who} {args.horizon} view for {session}: "
              f"{ch['was']} @ {ch['was_conviction']} -> {ch['now']} @ {ch['now_conviction']}")
        if row.get("rationale"):
            print(f"  {row['rationale']}")
        print("  the superseded view is kept in the log, marked amended")
        return

    fresh = L.append(row)
    if fresh:
        print(f"logged {who} view for {session} ({args.horizon}): "
              f"{row['direction']} @ conviction {row['conviction']}")
        if row.get("rationale"):
            print(f"  {row['rationale']}")
    else:
        print(f"{who} already has a {args.horizon} view on record for {session} — "
              f"not overwriting (a view revised after the tape moved is not a view)")


if __name__ == "__main__":
    main()
