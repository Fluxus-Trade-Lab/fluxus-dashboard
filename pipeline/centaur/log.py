"""d_human and d_machine — the two records a centaur needs.

Both sides state a view in the same shape so they can be compared, scored, and
merged. Neither is privileged in the schema; whose judgement gets weight is
decided later, by measurement, in `skill.py`.

The cost of entry matters more than the richness of the schema. A log the human
will not fill in is worth nothing, so a human view needs only a direction and a
conviction — everything else is optional. The one field that is NOT optional is
`asof`, because a view recorded after the fact is not a view, it is a memory.

**A `human` row may only ever be written by the human.** This log is the sole
evidence of Andy's judgement, and its value is exactly its authenticity — a
fabricated row does not merely add noise, it corrupts the measurement the merge
weights him by. The first thing written to this file was a demo row invented by
the assistant and filed as `human`; it was deleted, and the session guard below
exists because that row was also filed against a Saturday.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOG = Path("data/centaur/views.jsonl")

SOURCES = ("machine", "human")
DIRECTIONS = ("up", "down", "range", "stand_aside")
HORIZONS = ("intraday", "swing")
MAX_CONVICTION = 3


def is_trading_session(session: str) -> bool:
    """Weekday check on the ET session date. Not a holiday calendar — it exists
    to stop a view being filed against a day that never traded."""
    import datetime as dt
    try:
        return dt.date.fromisoformat(session).weekday() < 5
    except ValueError:
        return False


def view(*, asof: str, session: str, source: str, direction: str,
         conviction: int, horizon: str = "intraday",
         rationale: str | None = None, level: float | None = None,
         state_ref: str | None = None) -> dict:
    """One view from one party about one session.

    `conviction` is 1-3 and deliberately coarse. A finer scale invites the
    illusion that the difference between 6 and 7 out of 10 means something; at
    three levels every step has to be defensible.

    `stand_aside` is a first-class direction, not a missing value. "I have no
    view" is information about the human's own calibration and must be
    distinguishable from "was not asked".
    """
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}")
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}")
    if horizon not in HORIZONS:
        raise ValueError(f"horizon must be one of {HORIZONS}")
    if not isinstance(conviction, int) or not 1 <= conviction <= MAX_CONVICTION:
        raise ValueError(f"conviction must be an int in 1..{MAX_CONVICTION}")
    if not asof:
        raise ValueError("asof is required — a view recorded after the fact is a memory")
    if not is_trading_session(session):
        raise ValueError(
            f"{session} is not a trading session — a view filed against a day that "
            f"never traded can never be scored, and would sit in the record as a "
            f"call nobody made")
    return {"asof": asof, "session": session, "source": source,
            "direction": direction, "conviction": conviction, "horizon": horizon,
            "rationale": rationale, "level": level, "state_ref": state_ref}


def append(v: dict, path: Path | str = DEFAULT_LOG) -> bool:
    """Append unless this (session, source, horizon) is already recorded.

    One view per party per session per horizon. Allowing a second would let a
    view be revised after the tape moved, which is the failure the `asof`
    requirement exists to prevent.
    """
    p = Path(path)
    key = (v.get("session"), v.get("source"), v.get("horizon"))
    if any((r.get("session"), r.get("source"), r.get("horizon")) == key
           for r in read(p)):
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as fh:
        fh.write(json.dumps(v, sort_keys=True) + "\n")
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


def paired(rows: list[dict], horizon: str = "intraday") -> list[dict]:
    """Sessions where BOTH parties recorded a view — the only rows a merge can
    learn from, and the only ones where disagreement is observable."""
    by: dict[str, dict] = {}
    for r in rows:
        if r.get("horizon") != horizon:
            continue
        by.setdefault(r["session"], {})[r["source"]] = r
    return [{"session": s, "machine": v["machine"], "human": v["human"]}
            for s, v in sorted(by.items())
            if "machine" in v and "human" in v]


def disagreements(rows: list[dict], horizon: str = "intraday") -> list[dict]:
    """Paired sessions where the two called different directions.

    The highest-information rows in the log: agreement teaches the merge almost
    nothing, and every question about how much to trust whom is answered here.
    """
    return [p for p in paired(rows, horizon)
            if p["machine"]["direction"] != p["human"]["direction"]]
