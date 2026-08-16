"""Daily group snapshot -- the archive the state ribbon needs and cannot fake.

The rotation ribbon works today for style baskets because a basket is one ETF
and an ETF has two years of bars on disk. It cannot work for our 128 industries
and 80 themes, because those are cross-sectional aggregates of Finviz columns
that carry no history: `universe.json` is overwritten every session, so
yesterday's industry median is simply gone.

Two ways out. Fetch daily bars for all 3,071 constituent tickers and rebuild
every aggregate from scratch, or store one row per group per session from here
on. This is the second. It costs a few hundred kilobytes a day and needs ten
weeks before the ribbon has anything to draw -- which is why it should start
running before the UI wants it, not after.

**Store what was computed, not what can be recomputed.** Each row carries the
level, the acceleration and the state exactly as they were published that day.
Recomputing a past state from stored perf columns would silently apply today's
window constants to yesterday's data, so a change to `_LEVEL_COL` would rewrite
history. The stored state is the record of what we actually said.

Append-only and idempotent: re-running a date replaces that date's rows rather
than doubling them, so a re-run after a fix does not corrupt the series.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

log = logging.getLogger(__name__)

ARCHIVE = Path("data/history/groups_archive.csv")

# Deliberately narrow. Constituent lists change daily and belong in
# groups.json, not in a file that grows by one row per group per session.
FIELDS: List[str] = [
    "date", "kind", "group", "members",
    "excess_3m", "rs_accel", "state",
    "persistence", "persistence_of",
    "perf_1w", "perf_1m", "perf_3m", "perf_6m",
    # Appended 2026-08-16 (rows before that date read blank here): the
    # length-matched slope that words like "decelerating" must come from.
    # `rs_accel` above stays the state gate. See rs_engine module docstring.
    "rs_accel_rate",
    # Appended 2026-08-16 too: the session's change (median of members).
    "perf_1d",
    # Appended 2026-08-17 (rows before that date read blank here): the
    # one-month excess, so the archive carries the same three windows the
    # page offers. Without it a window study has to re-derive 1M from
    # perf_1m and a benchmark row the archive does not store.
    "excess_1m",
]


def rows_from(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Flatten one `groups.json` into archive rows."""
    date = payload.get("date")
    if not date:
        return []
    out: List[Dict[str, Any]] = []
    # Explicit, because one row is one group and `kind` should read as a label
    # on that row rather than as the section it came from. Stripping a trailing
    # "s" gets "industrie" -- a stored value is forever, so the mapping is
    # spelled out rather than derived.
    for section, kind in (("industries", "industry"), ("themes", "theme")):
        for g in payload.get(section) or []:
            row = {f: g.get(f) for f in FIELDS}
            row["date"] = date
            row["kind"] = kind
            out.append(row)
    return out


def read(path: Path = ARCHIVE) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def append(new_rows: Sequence[Mapping[str, Any]], path: Path = ARCHIVE
           ) -> Dict[str, int]:
    """Write `new_rows`, replacing any existing rows for the same dates.

    Replacement is by date, not by (date, group): a group that disappears from
    the taxonomy must disappear from that day's snapshot too, and a per-key
    merge would leave its last row behind forever.
    """
    if not new_rows:
        return {"written": 0, "replaced": 0, "total": len(read(path))}

    dates = {r["date"] for r in new_rows}
    kept = [r for r in read(path) if r["date"] not in dates]
    replaced = len(read(path)) - len(kept)

    merged: Iterable[Mapping[str, Any]] = sorted(
        [*kept, *new_rows], key=lambda r: (str(r["date"]), str(r["kind"]), str(r["group"])))

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(merged)

    total = sum(1 for _ in merged) if isinstance(merged, list) else len(kept) + len(new_rows)
    log.info("group archive: +%d rows for %s (replaced %d), %d total",
             len(new_rows), ", ".join(sorted(dates)), replaced, total)
    return {"written": len(new_rows), "replaced": replaced, "total": total}


def record(payload: Mapping[str, Any], path: Path = ARCHIVE) -> Dict[str, int]:
    """Snapshot one `groups.json` payload into the archive."""
    return append(rows_from(payload), path)
