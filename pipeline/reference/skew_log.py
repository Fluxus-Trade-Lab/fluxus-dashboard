"""Append-only daily record of the volatility smile's shape.

Built 2026-08-05 after a published claim — "SPY/QQQ/DIA all with +98th %'ile call
skews" — turned out to be unanswerable with what we keep. We store levels and no
history of any series, so every percentile claim, ours included, was a claim we
could neither make nor check. One row a day fixes that for skew.

The distinction this file exists to preserve: **a level is not a percentile.**
A 25-delta call skew of -0.3 vol points sounds bearish and can simultaneously be
the 98th percentile of its own history if the usual level is -1.5. Both numbers
are stored so neither can stand in for the other.

`source` is kept per row because the two measurement paths do not always agree
to the last decimal, and a percentile computed across mixed sources without
saying so is a silent apples-to-oranges comparison.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOG = Path("data/reference/skew_log.jsonl")

# How the row was measured. Solved-from-mid is the fallback when the feed's own
# greeks are starved, which happens on the busiest underlyings.
SOURCES = ("feed_greeks", "solved_mid")


def entry(*, date: str, symbol: str, expiry: str, dte: int, spot: float,
          forward: float, atm_iv: float, source: str,
          call_25d: dict | None = None, put_25d: dict | None = None,
          n_solved: int | None = None) -> dict:
    """One day's smile for one underlying at one tenor.

    `call_25d`/`put_25d` are {strike, delta, iv} or None when that wing could not
    be measured. None is preserved rather than defaulted, because a missing wing
    and a flat wing are different facts and only one of them is data.
    """
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}")
    if not (0.0 < atm_iv < 5.0):
        raise ValueError(f"implausible ATM IV {atm_iv!r} — expected a decimal fraction")
    row = {"date": date, "symbol": symbol, "expiry": expiry, "dte": dte,
           "spot": spot, "forward": forward, "atm_iv": atm_iv,
           "source": source, "n_solved": n_solved,
           "call_25d": call_25d, "put_25d": put_25d}
    row["call_skew"] = (call_25d["iv"] - atm_iv) if call_25d else None
    row["put_skew"] = (put_25d["iv"] - atm_iv) if put_25d else None
    row["risk_reversal"] = ((call_25d["iv"] - put_25d["iv"])
                            if (call_25d and put_25d) else None)
    return row


def append(row: dict, path: Path | str = DEFAULT_LOG) -> bool:
    """Append unless (date, symbol, expiry) is already recorded.

    Returns True if written. Re-running the collector must not inflate the
    sample — a duplicated day would quietly bias every percentile drawn from it.
    """
    p = Path(path)
    key = (row.get("date"), row.get("symbol"), row.get("expiry"))
    if any((r.get("date"), r.get("symbol"), r.get("expiry")) == key for r in read(p)):
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return True


def read(path: Path | str = DEFAULT_LOG) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def series(rows: list[dict], symbol: str, field: str = "call_skew") -> list[float]:
    """The one series a percentile can be taken of, oldest first.

    Rows where the field is None are dropped rather than zero-filled: an
    unmeasured wing is not a wing that measured zero.
    """
    vals = [(r["date"], r[field]) for r in rows
            if r.get("symbol") == symbol and r.get(field) is not None]
    return [v for _, v in sorted(vals)]
