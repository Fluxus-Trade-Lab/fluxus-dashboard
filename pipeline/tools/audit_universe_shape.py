"""Universe shape -- did the archive keep covering the same market?

Every archive guard we own measures a QUANTITY: row counts, null rates, date
continuity, one run against another. `audit_archives` I4 is the closest thing
to a coverage check we have, and it asks whether a session's row count sits
inside the trailing-20 median's [floor, 3x] band.

On 2026-06-26 `ticker_events.csv` stopped containing any ticker whose symbol
sorts after "L". It stayed that way for 21 sessions, across all 15 screeners,
19,850 rows -- 17.9% of the whole archive. I4 saw nothing, and it was right
not to: 06-26 has 1,613 rows against the previous day's 965. **The row count
went UP.** What was lost was not rows, it was half the universe; the surviving
half happened to be busier.

    A source that is cut in half along a CONTENT dimension is flawless under
    every COUNT dimension check.

So this file measures a shape instead: the share of symbols starting after "L",
per session, against its own trailing median. The specific statistic barely
matters -- first letter, sector mix, market-cap quantile mix would all work.
What matters is the property: **it must be a quantity that moves even when the
row count does not.** First letter is the cheapest such quantity we have; it
needs no join, no enrichment, and no vendor.

  U1  the share moves off the trailing median by more than --tolerance
  U2  the share is degenerate (exactly 0.0 or exactly 1.0) on a session with
      enough rows to make that essentially impossible -- this is the 2026-06-26
      shape, and it is reported separately because a hard 0 is a truncation
      while a drift is a mix change
  U3  not enough trailing sessions to judge; reported, never fatal

⚠️ After a long outage the BASELINE itself is poisoned, so recovery alarms too:
run this over `ticker_events.csv` and 2026-08-11 fires U1 for moving +51pp --
back to normal, away from a trailing median made of 21 truncated sessions. That
is not a false positive, it is the guard correctly reporting the second shape
change; it just needs a human to say which direction was the healthy one. Not
suppressed, because a rule that hides "it came back" would also hide "it broke
again".

Verified on real history: run over `ticker_events.csv`, it fires on
**2026-06-26, the first affected session**, and is silent across all 74
sessions from 2026-03-09 to 2026-06-25.

`check()` is pure. Reading the CSV lives in `main()`.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

SPLIT = "L"          # symbols sorting after this letter
TOLERANCE = 0.15     # share may drift this far from the trailing median
WINDOW = 20
MIN_ROWS = 50        # below this, a 0.0 share is ordinary small-sample noise


def share_after(tickers: list[str], split: str = SPLIT) -> float | None:
    ts = [t.strip() for t in tickers if t and t.strip()]
    if not ts:
        return None
    return sum(1 for t in ts if t[0].upper() > split.upper()) / len(ts)


def check(by_session: dict[str, list[str]], split: str = SPLIT,
          tolerance: float = TOLERANCE, window: int = WINDOW,
          min_rows: int = MIN_ROWS) -> dict:
    """by_session: {"YYYY-MM-DD": [ticker, ...]} exactly as archived."""
    sessions = sorted(by_session)
    rows_out, violations, warnings = [], [], []
    for i, d in enumerate(sessions):
        tickers = by_session[d]
        sh = share_after(tickers, split)
        n = len(tickers)
        prior = [share_after(by_session[p], split) for p in sessions[max(0, i - window):i]]
        prior = [p for p in prior if p is not None]
        base = statistics.median(prior) if prior else None
        rec = {"session": d, "rows": n, "share": None if sh is None else round(sh, 4),
               "baseline": None if base is None else round(base, 4), "kind": None}

        if sh is not None and n >= min_rows and sh in (0.0, 1.0):
            rec["kind"] = "U2"
            violations.append(
                f"U2 {d}: share of symbols after '{split}' is exactly "
                f"{sh:.1f} over {n} rows -- that is a truncation, not a mix "
                f"change" + (f" (trailing median {base:.2f})" if base is not None else ""))
        elif base is None or len(prior) < 3:
            rec["kind"] = "U3"
            warnings.append(f"U3 {d}: only {len(prior)} trailing sessions, not judged")
        elif sh is not None and abs(sh - base) > tolerance:
            rec["kind"] = "U1"
            violations.append(
                f"U1 {d}: share after '{split}' is {sh:.2f} vs trailing median "
                f"{base:.2f} (moved {abs(sh-base)*100:.0f}pp, tolerance "
                f"{tolerance*100:.0f}pp) over {n} rows")
        rows_out.append(rec)

    return {"split": split, "tolerance": tolerance, "sessions": len(sessions),
            "rows": rows_out, "violations": violations, "warnings": warnings,
            "ok": not violations}


def load(path: Path, date_col: str | None = None,
         ticker_col: str = "ticker") -> dict[str, list[str]]:
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return {}
    dc = date_col or next((c for c in ("date", "as_of", "session", "Date")
                           if c in rows[0]), None)
    if dc is None:
        raise SystemExit(f"no date column in {path}; pass --date-col")
    out: dict[str, list[str]] = {}
    for r in rows:
        d = (r.get(dc) or "")[:10]
        t = r.get(ticker_col) or ""
        if d and t:
            out.setdefault(d, []).append(t)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive", help="CSV with a date column and a ticker column")
    ap.add_argument("--date-col")
    ap.add_argument("--ticker-col", default="ticker")
    ap.add_argument("--split", default=SPLIT)
    ap.add_argument("--tolerance", type=float, default=TOLERANCE)
    ap.add_argument("--window", type=int, default=WINDOW)
    ap.add_argument("--json")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="only print the sessions that failed")
    a = ap.parse_args(argv)

    by = load(Path(a.archive), a.date_col, a.ticker_col)
    if not by:
        print("BAD  archive is empty -- nothing checked, which is not a pass")
        return 1
    out = check(by, a.split, a.tolerance, a.window)
    if not a.quiet:
        print(f"{a.archive}: {out['sessions']} sessions, split '{a.split}', "
              f"tolerance {a.tolerance*100:.0f}pp")
    for v in out["violations"]:
        print(f"BAD  {v}")
    if not a.quiet:
        for w in out["warnings"]:
            print(f"WARN {w}")
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: {len(out['violations'])} "
          f"violations, {len(out['warnings'])} warnings")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
