#!/usr/bin/env python3
"""Report what is missing, and lead with what can still be recovered today.

Runs at the END of the daily chain, on purpose. Every other step is trying to
produce something; this one is the only step whose job is to notice what did
NOT get produced, and it has to run after them to be able to tell.

Exit code carries the urgency so the chain can act on it without parsing text:

    0   nothing missing, or nothing that can still be acted on
    1   at least one gap is EXPIRING — its source is alive today and will not
        be tomorrow

`lost` gaps deliberately do NOT set the exit code. An alarm that fires every day
for something nobody can fix is how alarms get ignored, and the eight
unrecoverable flow reads in this repo would have done exactly that.

Usage:
    .venv/bin/python scripts/check_gaps.py
    .venv/bin/python scripts/check_gaps.py --days 10 --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.reference import gaps as G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=6,
                    help="Trading sessions to look back over.")
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r = G.scan(days=args.days, symbol=args.symbol)
    print(json.dumps(r, indent=2) if args.json else G.report(r))

    u = G.urgent(r)
    if u:
        print("\n  to recover them, now:")
        for x in u:
            ymd = x["session"].replace("-", "")
            if x["artifact"].startswith("flow_"):
                t = x["artifact"].split("_")[1][0]
                print(f"    .venv/bin/python scripts/flow_session.py "
                      f"--symbol {args.symbol} --date {ymd} --tenor {t}")
            elif x["artifact"] == "profile":
                print(f"    .venv/bin/python scripts/build_profile.py --date {ymd}")
            else:
                print(f"    {x['artifact']} for {x['session']} — no re-run "
                      f"exists; its source was {x['source']}")
    sys.exit(1 if u else 0)


if __name__ == "__main__":
    main()
