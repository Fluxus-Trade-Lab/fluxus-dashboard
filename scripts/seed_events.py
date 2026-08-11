#!/usr/bin/env python3
"""Seed the macro-event calendar with 2026's CPI and FOMC dates.

Idempotent: the store dedupes on (date, event), so re-running adds nothing. Run
it again when a date is rescheduled — the new row wins and the old one stays
visible in the file, which is the point of an append-only store.

Provenance note, kept deliberately blunt. bls.gov returns 403 to this fetcher,
so the CPI series below is transcribed from a secondary schedule. The one date
that mattered today — 2026-08-12 for July's CPI, 08:30 ET — was confirmed
against BLS's own release page independently. The rest are secondary and should
be re-checked against bls.gov before anything is traded off them. FOMC dates
come straight from federalreserve.gov.

Usage:
    .venv/bin/python scripts/seed_events.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.marketcal import market_now
from pipeline.reference import events as EV

CPI_SRC = ("https://www.usinflationcalculator.com/inflation/"
           "consumer-price-index-release-schedule/ (secondary; 2026-08-12 "
           "cross-checked against bls.gov)")
FOMC_SRC = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

# (release date, reference month). The reference month is carried because "the
# August CPI" is ambiguous between the print released in August and the one
# measuring August, and that ambiguity is exactly how a date gets misremembered.
CPI_2026 = [
    ("2026-01-13", "December 2025"), ("2026-02-13", "January 2026"),
    ("2026-03-11", "February 2026"), ("2026-04-10", "March 2026"),
    ("2026-05-12", "April 2026"),    ("2026-06-10", "May 2026"),
    ("2026-07-14", "June 2026"),     ("2026-08-12", "July 2026"),
    ("2026-09-11", "August 2026"),   ("2026-10-14", "September 2026"),
    ("2026-11-10", "October 2026"),  ("2026-12-10", "November 2026"),
]

# Statement day only — the second day of each two-day meeting. The first day
# is not a scheduled release and nothing prints on it.
FOMC_2026 = [
    ("2026-01-28", False), ("2026-03-18", True), ("2026-04-29", False),
    ("2026-06-17", True),  ("2026-07-29", False), ("2026-09-16", True),
    ("2026-10-28", False), ("2026-12-09", True),
]


def main():
    now = market_now().isoformat(timespec="seconds")
    rows = []
    for date, ref in CPI_2026:
        rows.append(EV.entry(date=date, time="08:30", event="CPI",
                             name=f"CPI, {ref} data", source=CPI_SRC,
                             recorded_at=now))
    for date, sep in FOMC_2026:
        rows.append(EV.entry(date=date, time="14:00", event="FOMC",
                             name="FOMC statement" + (" + SEP" if sep else ""),
                             source=FOMC_SRC, recorded_at=now))

    have = {(r["date"], r["event"]) for r in EV.load()}
    new = [r for r in rows if (r["date"], r["event"]) not in have]
    for r in new:
        EV.append(r)

    print(f"seeded {len(new)} new row(s); {len(rows) - len(new)} already held")
    for ev, c in sorted(EV.coverage().items()):
        print(f"  {ev:<5} {c['n']:>2} dates   {c['first']} .. {c['last']}")
    print("\nNot tracked yet (a question about these comes back `unknown`, "
          "never `no`):")
    print("  " + ", ".join(k for k in sorted(EV.ALIASES) if k not in EV.coverage()))


if __name__ == "__main__":
    main()
