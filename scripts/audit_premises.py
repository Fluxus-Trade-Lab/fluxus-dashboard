#!/usr/bin/env python3
"""Check every logged view's rationale against the macro calendar.

This reads and reports. It never edits a row. A human view is written by the
human alone, and a premise that turned out to be wrong is evidence about the
reasoning — evidence is only worth having if it stays where it fell.

What it can and cannot say is the whole point:

    confirmed   the named event really was on that date
    mismatch    we hold that event's schedule for that stretch, and the date
                is not one of them
    unknown     we do not hold enough of that event's schedule to say

`unknown` is not a soft `no`. Most events are still untracked, and a rationale
naming one comes back unknown by design.

Usage:
    .venv/bin/python scripts/audit_premises.py
    .venv/bin/python scripts/audit_premises.py --source human
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.reference import events as EV

VIEWS = Path("data/centaur/views.jsonl")
MARK = {"confirmed": "ok", "mismatch": "WRONG", "unknown": "?"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", default=VIEWS)
    ap.add_argument("--source", choices=("human", "machine"),
                    help="restrict to one side of the pair")
    args = ap.parse_args()

    p = Path(args.views)
    if not p.exists():
        sys.exit(f"no views at {p}")
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if args.source:
        rows = [r for r in rows if r.get("source") == args.source]

    cal = EV.load()
    if not cal:
        sys.exit("no calendar held — run scripts/seed_events.py first")

    tally = {"confirmed": 0, "mismatch": 0, "unknown": 0}
    n_checked = 0
    for r in rows:
        results = EV.check_claim(r.get("rationale") or "", r.get("session") or "", cal)
        if not results:
            continue
        n_checked += 1
        who = r.get("source", "?")
        print(f"\n{r.get('session')}  {who:<7} {r.get('direction')}/"
              f"{r.get('conviction')}  {r.get('horizon')}"
              + ("   [amended]" if r.get("amended") else ""))
        print(f"  \"{r.get('rationale')}\"")
        for g in results:
            tally[g["verdict"]] += 1
            print(f"    [{MARK[g['verdict']]:>5}] {g['note']}")

    print(f"\n{len(rows)} view(s); {n_checked} named a calendar event")
    print(f"  confirmed {tally['confirmed']}   mismatch {tally['mismatch']}"
          f"   unknown {tally['unknown']}")
    cov = EV.coverage(cal)
    untracked = [k for k in sorted(EV.ALIASES) if k not in cov]
    print(f"  tracking {', '.join(f'{k} (n={v[chr(110)]})' for k, v in sorted(cov.items()))}"
          + (f"; untracked: {', '.join(untracked)}" if untracked else ""))
    # A wrong premise is not a wrong call. Scoring stays on the outcome, and the
    # two are reported separately so neither can quietly stand in for the other.
    if tally["mismatch"]:
        print("\nA mismatched premise does not make the call wrong — direction is "
              "still scored on the tape. It is recorded because 'right for the "
              "wrong reason' is a category, and it is only visible if kept.")


if __name__ == "__main__":
    main()
