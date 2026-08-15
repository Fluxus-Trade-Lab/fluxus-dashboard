"""What is missing, and — the part that matters — whether it can still be had.

Built 2026-08-14, after the post-close chain hung on three consecutive days and
the 0DTE flow reads for 2026-08-12 and 2026-08-13 were found to be **permanently
gone**. Not "not yet pulled": an expired SPX option is unreachable at IBKR, the
chain lists live expiries only, and constructing the contract by hand returns
error 200. The ticks exist; the contract that would let you ask for them does
not.

So a gap report that only says "missing" is useless here. The whole question is
**how long you have**, and the artifacts differ:

  * **bars** persist for years. A profile or a TFF table missing from last month
    can be rebuilt today exactly as it would have been.
  * **the option chain** does not. Open interest is a snapshot with no history,
    and a contract disappears a day or two after it expires.

Three verdicts, and only one of them is urgent:

    ``recoverable``  the input still exists; fix it whenever
    ``expiring``     the input is alive TODAY and will not be tomorrow — act now
    ``lost``         the input is gone; record it and stop planning around it

`lost` is a first-class answer. A backlog that keeps listing an unrecoverable
gap is a to-do item that can never be closed, and the honest thing is to say so
once and move the date out of the plan.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from ..marketcal import is_trading_day, market_today

# What a complete session leaves behind, and what its input is made of.
# `perishable` marks the artifacts whose SOURCE expires rather than the file.
ARTIFACTS = {
    "gex": {
        "path": "data/gex/gex_{sym}_{ymd}.json",
        "perishable": True,
        "source": "the option chain's open interest, which is a snapshot with "
                  "no history — once the day passes there is nothing to re-ask",
    },
    "profile": {
        "path": "data/profile/profile_{ymd}.json",
        "perishable": False,
        "source": "30-minute bars, which IBKR keeps for years",
    },
    "flow_0dte": {
        "path": "data/flow/flow_{sym}_{ymd}_0dte.json",
        "perishable": True,
        "source": "the expiry ON that session, which drops off the chain a day "
                  "or two later and then cannot be resolved at all",
    },
    "flow_1dte": {
        "path": "data/flow/flow_{sym}_{ymd}_1dte.json",
        "perishable": True,
        "source": "the first expiry after that session, alive until it expires",
    },
}

# How long a perishable input stays reachable after its session, in calendar
# days. Deliberately conservative: the 2026-08-14 chain still listed that day's
# own expiry on the evening of the 14th but not 08-12's or 08-13's, so the real
# window is between one and two days and the check should not promise the top of
# that range.
PERISHABLE_DAYS = 1


def trading_days_back(n: int, end: dt.date | None = None) -> list[dt.date]:
    """The last `n` trading days ending at `end`, oldest first."""
    d = end or market_today()
    out = []
    while len(out) < n:
        if is_trading_day(d):
            out.append(d)
        d -= dt.timedelta(days=1)
    return sorted(out)


def _verdict(kind: str, day: dt.date, today: dt.date) -> str:
    if not ARTIFACTS[kind]["perishable"]:
        return "recoverable"
    age = (today - day).days
    if age <= 0:
        return "recoverable"
    return "expiring" if age <= PERISHABLE_DAYS else "lost"


def scan(days: int = 5, symbol: str = "SPX", root: str | Path = ".",
         today: dt.date | None = None) -> dict:
    """Which artifacts are missing over the last `days` trading sessions.

    `today` is injectable so the verdict boundaries can be tested without
    waiting for a Tuesday.
    """
    root = Path(root)
    now = today or market_today()
    sessions = trading_days_back(days, now)
    rows = []
    for d in sessions:
        ymd = d.strftime("%Y%m%d")
        for kind, spec in ARTIFACTS.items():
            p = root / spec["path"].format(sym=symbol, ymd=ymd)
            if p.exists():
                continue
            rows.append({"session": d.isoformat(), "artifact": kind,
                         "path": str(p), "verdict": _verdict(kind, d, now),
                         "source": spec["source"]})
    counts = {v: sum(1 for r in rows if r["verdict"] == v)
              for v in ("expiring", "lost", "recoverable")}
    return {"generated_for": now.isoformat(), "sessions_checked": len(sessions),
            "first": sessions[0].isoformat(), "last": sessions[-1].isoformat(),
            "symbol": symbol, "missing": rows, **counts,
            "note": _explain(counts)}


def _explain(c: dict) -> str:
    """A whole sentence per branch."""
    if not any(c.values()):
        return "nothing missing over the window checked"
    if c["expiring"]:
        return (f"{c['expiring']} gap(s) can still be filled TODAY and not "
                f"tomorrow — everything else can wait")
    if c["lost"] and not c["recoverable"]:
        return (f"{c['lost']} gap(s) are unrecoverable; nothing here can be "
                f"acted on, and they should come out of the plan")
    return (f"{c['recoverable']} recoverable gap(s)"
            + (f" and {c['lost']} that are gone for good" if c["lost"] else ""))


def urgent(report: dict) -> list[dict]:
    """Only the gaps a person can still do something about, today."""
    return [r for r in report["missing"] if r["verdict"] == "expiring"]


def report(r: dict) -> str:
    head = (f"gap check {r['first']} .. {r['last']} ({r['sessions_checked']} "
            f"sessions, {r['symbol']})")
    if not r["missing"]:
        return f"{head}\n  complete — nothing missing"
    lines = [head, f"  expiring {r['expiring']}   lost {r['lost']}   "
                   f"recoverable {r['recoverable']}", ""]
    for v in ("expiring", "lost", "recoverable"):
        rows = [x for x in r["missing"] if x["verdict"] == v]
        if not rows:
            continue
        lines.append(f"  [{v}]")
        for x in rows:
            lines.append(f"    {x['session']}  {x['artifact']}")
        if v == "expiring":
            lines.append("      ^ pull these now; the source is alive today "
                         "and will not be tomorrow")
    lines += ["", f"  {r['note']}"]
    return "\n".join(lines)
