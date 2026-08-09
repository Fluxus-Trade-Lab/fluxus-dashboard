#!/usr/bin/env python3
"""Backfill machine views from briefs that already exist.

Legitimate because `machine_direction()` is a PURE function of a brief's own
contents, and the briefs are dated artefacts written at the time. What is
derived now is exactly what would have been derived then, so `asof` is the
brief's own `generated_at`, not today.

The human side is NOT backfillable and this script will not touch it. Andy's
judgement on 2026-08-04 does not exist anywhere; inventing it would corrupt the
one measurement the merge weights him by — which already happened once, by hand.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(Path("data/snapshots").glob(f"snapshot_{args.symbol}_*.json"))
    written = skipped = unreadable = 0
    for f in files:
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            unreadable += 1
            continue
        session = data.get("date")
        asof = data.get("generated_at")
        v = machine_direction(data)
        if not (session and asof and v):
            unreadable += 1
            continue
        if not L.is_trading_session(session):
            skipped += 1
            continue
        row = L.view(asof=asof, session=session, source="machine",
                     direction=v["direction"], conviction=v["conviction"],
                     rationale=v["rationale"], state_ref=str(f))
        if args.dry_run:
            print(f"  {session}  {v['direction']:<12} conv {v['conviction']}  {asof[:16]}")
            written += 1
            continue
        written += bool(L.append(row))
    print(f"{'would write' if args.dry_run else 'wrote'} {written} machine view(s); "
          f"{skipped} non-trading session(s) skipped, {unreadable} brief(s) unreadable")


if __name__ == "__main__":
    main()
