"""Append-only log of every published levels snapshot.

Two things need this and neither works without it:

  * **Sequence.** A dated JSON gets overwritten on every pull, so the file only
    ever shows the last state of the day. The order in which the walls moved —
    which is the thing that actually happened — is destroyed by the overwrite.
  * **Scorekeeping.** You cannot score a level you did not record at the time
    you published it. Reconstructing it later from an end-of-day file is
    hindsight, not a record.

Append-only and never rewritten: an entry is what we believed at that moment,
including when that turns out to be wrong.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LOG = Path("data/gex/levels_log.jsonl")

FIELDS = ("call_wall", "zero_gamma_flip", "put_wall", "pin_strike",
          "charm_peak_strike", "total_gex", "total_charm", "spot", "regime")


def entry_from(doc: dict, symbol: str = "SPX", confluence: list | None = None) -> dict:
    """Flatten a GEX document into one log row."""
    row = {"symbol": symbol, "generated_at": doc.get("generated_at")}
    row.update({f: doc.get(f) for f in FIELDS})
    if confluence is not None:
        row["confluence"] = sorted(confluence)
    return row


def append(entry: dict, path: Path | str = DEFAULT_LOG) -> bool:
    """Append one row unless that exact observation is already recorded.

    Re-running the builder over the same GEX file is not a new observation, so
    (symbol, generated_at) is treated as the identity of a pull. This is a skip,
    never a rewrite — nothing already on disk is altered.
    Returns True if written.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    key = (entry.get("symbol"), entry.get("generated_at"))
    if key[1] and any((r.get("symbol"), r.get("generated_at")) == key for r in read(p)):
        return False
    with p.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return True


def read(path: Path | str = DEFAULT_LOG) -> list[dict]:
    """All rows, in write order. Malformed lines are skipped, not fatal."""
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _day(ts: str | None) -> str:
    return (ts or "")[:10]


def intraday_sequence(rows: list[dict], day: str, symbol: str = "SPX") -> list[dict]:
    """Every entry recorded on `day`, with the change since the previous one.

    This is the sequence view: not "where are the walls" but "how did they move,
    in what order". A single-entry day yields one row with no deltas — correct,
    and visibly different from a day we simply failed to record.
    """
    same = [r for r in rows if r.get("symbol") == symbol and _day(r.get("generated_at")) == day]
    same.sort(key=lambda r: r.get("generated_at") or "")
    out = []
    for i, r in enumerate(same):
        step = {"generated_at": r.get("generated_at"), "spot": r.get("spot"),
                "call_wall": r.get("call_wall"), "put_wall": r.get("put_wall"),
                "flip": r.get("zero_gamma_flip"), "total_gex": r.get("total_gex")}
        if i:
            prev = same[i - 1]
            step["moved"] = {
                k: round(r[j] - prev[j], 1)
                for k, j in (("call_wall", "call_wall"), ("put_wall", "put_wall"),
                             ("flip", "zero_gamma_flip"), ("spot", "spot"))
                if isinstance(r.get(j), (int, float)) and isinstance(prev.get(j), (int, float))
                and r[j] != prev[j]
            } or None
        out.append(step)
    return out


def last_entry_per_day(rows: list[dict], symbol: str = "SPX") -> dict[str, dict]:
    """The final recorded state for each day — the basis for scoring."""
    by_day: dict[str, dict] = {}
    for r in sorted(rows, key=lambda x: x.get("generated_at") or ""):
        if r.get("symbol") != symbol:
            continue
        d = _day(r.get("generated_at"))
        if d:
            by_day[d] = r
    return by_day
