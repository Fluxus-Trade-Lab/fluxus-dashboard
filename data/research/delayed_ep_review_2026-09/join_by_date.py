"""Break the ledger's join check apart BY SESSION, and ask one specific
question of the day that is under suspicion.

Context. The 2026-09-01 run of `review_benchmarked.py` reported the ledger's
stored closes were clean: 617/617 rows within 0.5% of the bar pulled back
today. That ledger ended 2026-08-28. It now runs to 09-04, and the same check
now reports 96.3% within 0.5% and a worst row off by 19.9%.

Two later findings say where to look. DATA_RELIABILITY sixth section item 7
(2026-09-06) found 2026-09-02's `delayed_ep_log` closes equal to the 09-01
`leaders_log` closes; `audit_progress` (2026-09-08) found all 36 of that
session's rows fail the calendar. Both witnesses are OURS -- one compares two
of our archives, the other compares an archive to the trading calendar.

This check is a THIRD witness and it is independent of both: it compares the
archive to the VENDOR. If 09-02 is a replay of 09-01, then the ledger's 09-02
close should match the vendor's 09-01 bar and not the vendor's 09-02 bar. That
is a directional prediction, not a similarity score, and the other sessions in
the ledger are the negative controls -- they must NOT show it.

  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/join_by_date.py
"""
from __future__ import annotations
import csv
import datetime as dt
from pathlib import Path

import numpy as np

from pipeline.marketcal import is_trading_day

HERE = Path(__file__).parent
LOG = Path("data/history/delayed_ep_log.csv")
SUSPECT = "2026-09-02"


def load_bars() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for r in csv.DictReader((HERE / "bars.csv").open(newline="")):
        out.setdefault(r["ticker"], {})[r["date"]] = float(r["close"])
    return out


def prev_session(d: str) -> str:
    x = dt.date.fromisoformat(d) - dt.timedelta(days=1)
    while not is_trading_day(x):
        x -= dt.timedelta(days=1)
    return str(x)


def main() -> int:
    log = list(csv.DictReader(LOG.open(newline="")))
    bars = load_bars()
    dates = sorted({r["as_of"] for r in log})

    print("=== join check, per session: ledger close vs the vendor bar for THAT day ===")
    print(f"  {'as_of':<12}{'rows':>5}{'resolv':>7}{'med|d|':>9}{'>0.5%':>7}{'>2%':>6}{'max|d|':>9}")
    per_date_bad: dict[str, int] = {}
    for d in dates:
        rows = [r for r in log if r["as_of"] == d]
        rel = [abs(bars[r["ticker"]][d] - float(r["close"])) / float(r["close"])
               for r in rows if r["ticker"] in bars and d in bars[r["ticker"]]]
        if not rel:
            print(f"  {d:<12}{len(rows):>5}{0:>7}       (nothing resolvable)")
            continue
        a = np.array(rel)
        per_date_bad[d] = int((a > 0.005).sum())
        print(f"  {d:<12}{len(rows):>5}{len(rel):>7}{a.mean()*0+np.median(a)*100:>8.2f}%"
              f"{int((a>0.005).sum()):>7}{int((a>0.02).sum()):>6}{a.max()*100:>8.1f}%")

    total_bad = sum(per_date_bad.values())
    on_suspect = per_date_bad.get(SUSPECT, 0)
    print(f"\n  rows off by >0.5%: {total_bad} total, {on_suspect} of them on {SUSPECT} "
          f"({on_suspect/total_bad*100:.0f}%)" if total_bad else "\n  no rows off by >0.5%")

    # ---------------------------------------------------------------- the directional test
    prev = prev_session(SUSPECT)
    print(f"\n=== the specific prediction: is {SUSPECT} the vendor's {prev} bar? ===")
    print("  for every session in the ledger, how many rows match the vendor bar of")
    print("  (a) that same day, vs (b) the PREVIOUS session -- within 0.1%")
    print(f"  {'as_of':<12}{'n':>5}{'same-day':>10}{'prev-day':>10}   verdict")
    for d in dates:
        p = prev_session(d)
        rows = [r for r in log if r["as_of"] == d
                and r["ticker"] in bars and d in bars[r["ticker"]] and p in bars[r["ticker"]]]
        if not rows:
            continue
        same = sum(1 for r in rows
                   if abs(bars[r["ticker"]][d] - float(r["close"])) / float(r["close"]) <= 0.001)
        prv = sum(1 for r in rows
                  if abs(bars[r["ticker"]][p] - float(r["close"])) / float(r["close"]) <= 0.001)
        verdict = ""
        if prv > same:
            verdict = f"  <-- REPLAY of {p}"
        print(f"  {d:<12}{len(rows):>5}{same:>10}{prv:>10}{verdict}")

    print("\n  (a session whose rows match the previous day better than their own day is")
    print("   a replay; every other session is a negative control for this test)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
