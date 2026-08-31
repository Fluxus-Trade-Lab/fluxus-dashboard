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
  C4  for C1, how MANY of the sampled tickers lost the same day. This is the
      discriminator, and it is the whole reason to sample more than one name:
        ~all tickers  -> the feed dropped a session; nothing downstream is safe
        a few tickers -> those names did not trade (halt, IPO, delisting)
      Reported as a share, and only a share above --universal-frac is fatal.

`check()` is pure -- it takes the dates already present and answers. The
network lives in `main()`, so the tests never touch it.
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
          last_complete: dt.date, universal_frac: float = UNIVERSAL_FRAC) -> dict:
    """Compare what the feed returned against what the calendar says exists.

    present         {ticker: {"YYYY-MM-DD", ...}} as the feed returned them
    start, end      window to audit, inclusive
    last_complete   the last session that has actually closed; anything the
                    feed reports after this is a live partial bar, not a close
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


def fetch(tickers: list[str], start: dt.date, end: dt.date) -> dict[str, set[str]]:
    import yfinance as yf
    raw = yf.download(tickers, start=str(start),
                      end=str(end + dt.timedelta(days=1)), interval="1d",
                      group_by="ticker", auto_adjust=False, progress=False,
                      threads=True)
    out: dict[str, set[str]] = {}
    for t in tickers:
        try:
            s = raw[t]["Close"].dropna() if len(tickers) > 1 else raw["Close"].dropna()
        except KeyError:
            continue
        out[t] = {str(i.date()) for i in s.index}
    return out


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
    ap.add_argument("--json", help="write the report here")
    args = ap.parse_args(argv)

    last_complete = last_completed_session()
    end = last_complete
    start = end - dt.timedelta(days=args.days)
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    present = fetch(tickers, start, end + dt.timedelta(days=3))
    if not present:
        print("BAD  feed returned nothing at all")
        return 1
    out = check(present, start, end, last_complete, args.universal_frac)

    print(f"window {out['window'][0]}..{out['window'][1]}  "
          f"{out['sessions_expected']} sessions expected  "
          f"{out['tickers']} tickers  (last completed {out['last_complete']})")
    for v in out["violations"]:
        print(f"BAD  {v}")
    for w in out["warnings"]:
        print(f"WARN {w}")
    for g in out["gaps"]:
        if g["universal"] and g["still_present"]:
            print(f"     {g['session']} survived only for: "
                  f"{', '.join(g['still_present'])}")
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: "
          f"{len(out['violations'])} violations, {len(out['warnings'])} warnings")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
