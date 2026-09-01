"""Calendar gaps -- does the price feed still contain the sessions it gave us?

Every archive guard we own reads the feed's own output and asks whether that
output is internally consistent. `audit_archives` I1-I7 check the archive
against itself; `audit_ledger` L1-L6 check a run against its own evidence;
`audit_regression_gate` compares a run to the one it replaced. All of them take
the *session grid* from whatever rows the feed returned.

Nothing checks the grid itself. So when a session disappears from the vendor,
every one of those guards stays green -- the remaining rows are perfectly
well-formed, in order, non-duplicated, and one day short.

    2026-08-28 is a trading day by `pipeline.marketcal`. Our own
    `delayed_ep_log.csv` holds 28 rows stamped with it, and the closes stored
    that night differ from both the 08-27 and the 08-31 close, so the bar
    existed and we consumed it. By 2026-09-01 Yahoo returned it for **1 of 90**
    tickers we asked about, across four different query spellings. Nothing in
    the repo made a sound.

Why that is dangerous rather than merely annoying: code that means "N sessions
ago" almost always spells it `series.iloc[-N]`. Delete a row and that phrase
silently points at a different day -- lookbacks slide, 52-week windows shift by
one, and a forward-return study measures a horizon it did not intend. The data
is not corrupt; the *index* is, and no value-level check can see it.

  C0  the sample is empty -- nothing could be checked. Reported as a
      violation, never as a pass: a guard that answers "clean" to a question
      it could not ask is worse than no guard.
  C1  a session marketcal says is COMPLETE is absent from the feed
  C2  the feed carries a bar for a session that has not closed yet -- during
      an open session yfinance returns a live partial bar stamped today, which
      downstream code reads as a close
  C3  the feed carries a date marketcal says is not a trading day at all
      (we and the vendor disagree about when the market was open)
  C5  a session the feed DOES return, carrying a bar that is not a real
      session: a null close beside a non-zero volume (the 2026-08-28 shape --
      a truncated window hands back the live day's numbers under the missing
      day's date), or a zero-volume O=H=L=C stale placeholder (the FBRX shape
      -- halted since 2026-07-20, still quoted). Presence in the index is not
      evidence of a session; this is the check that says so.
  C4  for C1, how MANY of the sampled tickers lost the same day. This is the
      discriminator, and it is the whole reason to sample more than one name:
        ~all tickers  -> the feed dropped a session; nothing downstream is safe
        a few tickers -> those names did not trade (halt, IPO, delisting)
      Reported as a share, and only a share above --universal-frac is fatal.

C1 alone is not enough, and 2025-01-09 is why. `marketcal` calls it a trading
day. No ticker has a bar for it, and `breadth_archive.csv` has no row -- it
jumps 01-08 -> 01-10. Five tickers agree the market was shut (it was: an
ad-hoc NYSE closure, which `marketcal` does not model -- it knows the recurring
holidays and nothing else). Run C1 alone against that date and it reports
"THE FEED LOST A SESSION", loudly and wrongly.

What separates it from 2026-08-28 is not the calendar and not the feed. Both
days look identical on those two axes. It is **our own archive**:

    calendar   feed        archive   verdict
    ---------------------------------------------------------------------
    trading    has bar     has row   fine
    trading    has bar     NO ROW    D1 ARCHIVE HOLE -- our writer missed a
                                        session the market really had
    trading    NO BAR      NO ROW    D2 CALENDAR WRONG -- the market was shut
                                        and marketcal does not know it
    trading    NO BAR      HAS ROW   D3 FEED REGRESSION -- the vendor deleted
                                        a session we already consumed

Three sources, and the *pattern of the disagreement* names which one is lying.
Every row of that table has a real instance found on 2026-09-01:
D1 = `ticker_events.csv` is missing 2026-04-07 / 06-08 / 07-14 / 07-15 (SPY has
bars for all four); D2 = 2025-01-09; D3 = 2026-08-28.

`check()` and `reconcile()` are pure -- they take the dates already present and
answer. The network and the file reads live in `main()`, so tests never touch
either.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from pipeline.marketcal import is_trading_day, last_completed_session

DEFAULT_TICKERS = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "JPM", "XOM", "JNJ"]
UNIVERSAL_FRAC = 0.80


def trading_grid(start: dt.date, end: dt.date) -> list[str]:
    """Sessions marketcal says the market was open, inclusive."""
    out, d = [], start
    while d <= end:
        if is_trading_day(d):
            out.append(str(d))
        d += dt.timedelta(days=1)
    return out


def check(present: dict[str, set[str]], start: dt.date, end: dt.date,
          last_complete: dt.date, universal_frac: float = UNIVERSAL_FRAC,
          degenerate: dict[str, set[str]] | None = None) -> dict:
    """Compare what the feed returned against what the calendar says exists.

    present         {ticker: {"YYYY-MM-DD", ...}} as the feed returned them
    start, end      window to audit, inclusive
    last_complete   the last session that has actually closed; anything the
                    feed reports after this is a live partial bar, not a close
    degenerate      {ticker: {dates whose bar is present but not a real
                    session}} -- null close with volume, or zero-volume
                    O=H=L=C. Optional; when omitted C5 does not run.
    """
    grid = trading_grid(start, end)
    complete = [d for d in grid if d <= str(last_complete)]
    tickers = sorted(present)
    n = len(tickers)
    violations: list[str] = []
    warnings: list[str] = []

    # An empty sample is not a clean bill of health. Without this the auditor
    # answers "no gaps found" to a question it was never able to ask, which is
    # the most expensive kind of green there is.
    if not tickers:
        violations.append("C0 the feed returned no tickers at all -- nothing "
                          "was checked; this is not a passing result")

    # C1 / C4 -- sessions the calendar has and the feed does not
    gaps = []
    for d in complete:
        missing = [t for t in tickers if d not in present[t]]
        if not missing:
            continue
        frac = len(missing) / n if n else 0.0
        universal = frac >= universal_frac
        gaps.append({"session": d, "missing": len(missing), "of": n,
                     "frac": round(frac, 4), "universal": universal,
                     "still_present": sorted(set(tickers) - set(missing))[:5]})
        msg = (f"C1 {d}: absent for {len(missing)}/{n} tickers "
               f"({frac*100:.0f}%)")
        if universal:
            violations.append(msg + " -- FEED LOST A SESSION, index-based "
                                    "lookbacks downstream are off by one")
        else:
            warnings.append(msg + " -- sporadic, reads as halted/not-yet-listed")

    # C2 -- bars stamped later than the last session that has closed
    early = sorted({d for t in tickers for d in present[t] if d > str(last_complete)})
    for d in early:
        who = sum(1 for t in tickers if d in present[t])
        violations.append(
            f"C2 {d}: {who}/{n} tickers carry a bar past the last completed "
            f"session ({last_complete}) -- that is a live intraday quote, "
            f"not a close")

    # C3 -- bars on days the calendar says the market was shut
    shut = sorted({d for t in tickers for d in present[t]
                   if str(start) <= d <= str(end)
                   and not is_trading_day(dt.date.fromisoformat(d))})
    for d in shut:
        who = sum(1 for t in tickers if d in present[t])
        violations.append(
            f"C3 {d}: {who}/{n} tickers carry a bar on a day marketcal calls "
            f"non-trading -- our calendar and the vendor disagree")

    # C5 -- a date is in the index, but what is under it is not a session.
    # This is the check that FBRX defeated on 2026-09-01: it was the only name
    # still carrying anything at 08-28, which read as "the one survivor" and
    # was actually a zero-volume stale quote. Having a row is not having a bar.
    if degenerate:
        bad: dict[str, int] = {}
        for t, ds in degenerate.items():
            for d in ds:
                if str(start) <= d <= str(end):
                    bad[d] = bad.get(d, 0) + 1
        for d in sorted(bad):
            violations.append(
                f"C5 {d}: {bad[d]}/{n} tickers carry a bar that is not a real "
                f"session (null close beside volume, or a zero-volume "
                f"placeholder) -- present in the index, absent in fact")

    return {
        "window": [str(start), str(end)],
        "last_complete": str(last_complete),
        "sessions_expected": len(complete),
        "tickers": n,
        "gaps": gaps,
        "violations": violations,
        "warnings": warnings,
        "ok": not violations,
    }


def reconcile(feed: dict[str, set[str]], archive: set[str], start: dt.date,
              end: dt.date, last_complete: dt.date,
              universal_frac: float = UNIVERSAL_FRAC,
              grace_sessions: int = 1) -> dict:
    """Three-way: calendar vs feed vs one of our own archives.

    `check()` can tell that the calendar and the feed disagree. It cannot tell
    WHO is wrong, and on that question it defaults to blaming the feed -- which
    is right for 2026-08-28 and wrong for 2025-01-09. The archive breaks the
    tie, because it records what we actually had in hand at the time.

    archive          the set of session dates our archive holds, e.g. every
                     distinct `date` in breadth_archive.csv
    grace_sessions   how many of the newest sessions to exempt from D1. The
                     nightly writer runs after the close, so between 16:00 ET
                     and the cron there is a window where the newest session
                     is legitimately not in the archive yet. Without this the
                     gate cries wolf every single evening -- which is how a
                     gate stops being read. D3 is NOT exempted: a session the
                     archive already holds cannot un-happen.
    """
    grid = [d for d in trading_grid(start, end) if d <= str(last_complete)]
    fresh = set(grid[-grace_sessions:]) if grace_sessions > 0 else set()
    tickers = sorted(feed)
    n = len(tickers)
    findings: list[dict] = []
    if not tickers:
        return {"window": [str(start), str(end)], "tickers": 0, "findings": [],
                "violations": ["C0 the feed returned no tickers at all -- "
                               "nothing was checked"], "warnings": [], "ok": False}

    violations: list[str] = []
    warnings: list[str] = []
    for d in grid:
        have_feed = sum(1 for t in tickers if d in feed[t]) / n
        feed_has = have_feed >= (1.0 - universal_frac)
        arch_has = d in archive
        if feed_has and arch_has:
            continue
        if feed_has and not arch_has:
            if d in fresh:
                continue          # the nightly writer has not run yet
            kind, msg = "D1", (f"D1 {d}: the market traded ({have_feed*100:.0f}% "
                               f"of tickers have a bar) and our archive has no "
                               f"row -- ARCHIVE HOLE, a writer missed a session")
            violations.append(msg)
        elif not feed_has and not arch_has:
            kind, msg = "D2", (f"D2 {d}: no bars anywhere and no archive row, yet "
                               f"marketcal calls it a trading day -- CALENDAR "
                               f"WRONG, likely an ad-hoc closure it does not model")
            warnings.append(msg)
        else:
            kind, msg = "D3", (f"D3 {d}: our archive has a row and the feed no "
                               f"longer returns the bar ({have_feed*100:.0f}% of "
                               f"tickers) -- FEED REGRESSION, the vendor deleted a "
                               f"session we already consumed")
            violations.append(msg)
        findings.append({"session": d, "kind": kind,
                         "feed_frac": round(have_feed, 4), "in_archive": arch_has})

    return {"window": [str(start), str(end)], "last_complete": str(last_complete),
            "sessions_expected": len(grid), "tickers": n, "findings": findings,
            "violations": violations, "warnings": warnings, "ok": not violations}


def classify_bar(row) -> str:
    """One row of daily OHLCV -> "good" (a real session), "bad" (a row that
    pretends a session happened), or "padding" (an empty row, uninteresting).

    Lifted out of fetch() on 2026-09-02, unchanged. It had lived inside a
    function whose first statement is `import yfinance`, so no test could reach
    it without the network -- and the mutation sweep said so plainly: 17 of the
    52 survivors in this module sat on these four lines, every boolean in the
    check unpinned. This is the check that tells a halted-but-still-quoted name
    from a live one; getting it backwards is how 2026-09-01 read FBRX's
    O=H=L=C, Volume=0 placeholder as "the one ticker that still had data".

    `row` only needs `.get`, so tests pass plain dicts.
    """
    close = row.get("Close")
    vol = row.get("Volume")
    null_close = close is None or (isinstance(close, float) and close != close)
    if null_close:
        # A null close is only interesting if something else pretends a
        # session happened; an entirely empty row is just padding.
        if vol is not None and vol == vol and float(vol) > 0:
            return "bad"
        return "padding"
    o, h, lo = row.get("Open"), row.get("High"), row.get("Low")
    flat = (o == h == lo == close)
    if flat and vol is not None and vol == vol and float(vol) == 0:
        return "bad"              # halted name, still quoted (the FBRX shape)
    return "good"


def fetch(tickers: list[str], start: dt.date,
          end: dt.date) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(dates with a usable bar, dates with a bar that is not a session).

    Deliberately does NOT `dropna()` before looking. Dropping first is exactly
    how the 2026-08-28 slot became invisible: the row was there, its OHLC were
    null, and every consumer that filtered nulls saw a shorter clean series
    instead of a broken one.
    """
    import yfinance as yf
    raw = yf.download(tickers, start=str(start),
                      end=str(end + dt.timedelta(days=1)), interval="1d",
                      group_by="ticker", auto_adjust=False, progress=False,
                      threads=True)
    good: dict[str, set[str]] = {}
    bad: dict[str, set[str]] = {}
    for t in tickers:
        try:
            df = raw[t] if len(tickers) > 1 else raw
        except KeyError:
            continue
        g, b = set(), set()
        for i, row in df.iterrows():
            d = str(i.date())
            verdict = classify_bar(row)
            if verdict == "good":
                g.add(d)
            elif verdict == "bad":
                b.add(d)
        good[t], bad[t] = g, b
    return good, bad


def read_archive_dates(path: Path, column: str | None = None) -> set[str]:
    """Distinct session dates in one of our CSV archives."""
    import csv as _csv
    with path.open(newline="") as fh:
        rows = list(_csv.DictReader(fh))
    if not rows:
        return set()
    col = column or next((c for c in ("as_of", "date", "session", "Date")
                          if c in rows[0]), None)
    if col is None:
        raise SystemExit(f"cannot find a date column in {path}; pass --date-col")
    return {r[col][:10] for r in rows if r.get(col)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=30,
                    help="how far back to audit (calendar days)")
    ap.add_argument("--tickers", default=",".join(DEFAULT_TICKERS),
                    help="sample to ask about; more than one is the point (C4)")
    ap.add_argument("--universal-frac", type=float, default=UNIVERSAL_FRAC,
                    help="share of tickers missing a session for it to count "
                         "as the feed losing the session rather than those "
                         "names not trading")
    ap.add_argument("--archive", help="one of our CSV archives; switches to "
                                      "the three-way calendar/feed/archive "
                                      "reconcile (D1-D3)")
    ap.add_argument("--date-col", help="date column in --archive, if not "
                                       "as_of/date/session/Date")
    ap.add_argument("--grace-sessions", type=int, default=1,
                    help="newest sessions exempt from D1; the nightly writer "
                         "runs after the close, so today's absence is normal")
    ap.add_argument("--json", help="write the report here")
    args = ap.parse_args(argv)

    last_complete = last_completed_session()
    end = last_complete
    start = end - dt.timedelta(days=args.days)
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    present, degenerate = fetch(tickers, start, end + dt.timedelta(days=3))
    if not present:
        print("BAD  feed returned nothing at all")
        return 1

    if args.archive:
        archive = read_archive_dates(Path(args.archive), args.date_col)
        out = reconcile(present, archive, start, end, last_complete,
                        args.universal_frac, args.grace_sessions)
        print(f"window {out['window'][0]}..{out['window'][1]}  "
              f"{out['sessions_expected']} sessions expected  "
              f"{out['tickers']} tickers  vs {args.archive}")
    else:
        out = check(present, start, end, last_complete, args.universal_frac,
                    degenerate=degenerate)
        print(f"window {out['window'][0]}..{out['window'][1]}  "
              f"{out['sessions_expected']} sessions expected  "
              f"{out['tickers']} tickers  (last completed {out['last_complete']})")
    for v in out["violations"]:
        print(f"BAD  {v}")
    for w in out["warnings"]:
        print(f"WARN {w}")
    for g in out.get("gaps", []):
        if g["universal"] and g["still_present"]:
            print(f"     {g['session']} still has a bar for: "
                  f"{', '.join(g['still_present'])}"
                  f"  -- check C5 before calling these survivors")
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: "
          f"{len(out['violations'])} violations, {len(out['warnings'])} warnings")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
