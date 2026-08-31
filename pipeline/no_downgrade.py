"""Do not overwrite a healthy copy of a session with a worse one.

**The structural hole this closes.** Every guard we own is a *self-consistency*
guard: `quality.check` grades null rates against the field's own history,
`audit_archives` I1-I7 check the archive against itself, `audit_ledger` L1-L6
check a run against its own evidence. They all ask the same question --

    is this data internally right?

Not one of them asks the other question:

    is it better than the copy it is about to replace?

On **2026-08-27** that hole cost us a day of data. The main schedule fired
**485 minutes late** onto a session that had already landed twice and healthy,
ran anyway, and won because it wrote last. `universe_quality` went `ok` ->
`degraded`; `bars_missing` 64 -> **266** (x4.2); `unmeasurable` 75 -> **277**
(x3.7); `tradeable` 2562 -> 2465; 15 of 19 panels shrank ~5%. All three runs
reported `success` and not one gate made a sound -- `bars_missing` 266 sits
under the ">300 = the 429 night" alarm line, and every other check was busy
asking whether the new file was self-consistent, which it was.

Full autopsy: `data/reference/incidents/2026-08-29_late_run_overwrote_healthy_data.md`.
Andy's ruling, 2026-08-31: **compare the data** -- option (a), "degrade, do not
overwrite".

**What this module is not.** It is not a freshness gate. A late run is still
allowed to run and still allowed to win; it is only stopped from winning *with
a worse hand*. It is not a halt either: blocking the write leaves the healthy
copy on disk and the run keeps going, because every downstream stage
(`build_groups`, `watchlist`, `shortlist`) re-reads `universe.json` off disk
rather than from memory -- so preserving the file preserves the panels too.
Andy asked for "do not overwrite", not "stop the night".

**Worse, not different.** The trap in a gate like this is writing "worse" as
"not equal". Data moves every night; a gate that fires on movement fires every
night and gets ignored. So all three rules here are strictly *directional* and
none of them can fire on an improvement or on equality:

  D1  **status downgrade** -- the pipeline's own summary word moved down the
      ladder (ok < degraded < stale < severe). Categorical, nothing to tune,
      and this alone is what catches 2026-08-27. A repair run (degraded -> ok,
      like the genuine 08-19 one) cannot trip it.

  D2  **missingness blowout** -- a directional count moved the wrong way past
      BOTH a relative and an absolute floor. Both, because either one alone is
      wrong: relative-only calls 64 -> 68 a 6% regression (it is four names),
      and absolute-only calls a 25-row move on a 2500-row counter a crisis.

  D3  **degraded-set growth** -- three or more columns that were healthy in the
      stored copy are degraded in the new one.

**Same session only.** Comparing today's numbers against yesterday's would be
measuring the market, not the pipeline, so the gate stays silent unless the
stored copy claims the same session as the candidate. A different session, a
missing file, an unparsable file: all `no-baseline`, all allowed through.
Reported as `no-baseline`, never as clean -- the same distinction
`audit_regression_gate` insists on.

Calibration, and what it costs (all numbers from the 08-27 incident table):

    bars_missing   64 -> 266   +316%, +202 rows   BLOCKS (rel 50%, floor 25)
    unmeasurable   75 -> 277   +269%, +202 rows   BLOCKS
    tradeable    2562 -> 2465    -3.8%,  -97 rows  passes D2 (under 5%)
    status         ok -> degraded                  BLOCKS on D1

`tradeable` is stated rather than tuned around: -3.8% is genuinely inside the
range a thin day produces, so D2 does not catch it and D1 does. Lowering the
`tradeable` tolerance until that one number went red would be fitting the gate
to the single sample we have.
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# One ladder, one home. `audit_regression_gate` already owns the status ranking
# for the after-the-fact version of this comparison; a second copy here is how
# the two silently drift apart (see [[pitfall_same_quantity_three_names]]).
from pipeline.tools.audit_regression_gate import STATUS_RANK

log = logging.getLogger(__name__)

# Set to 1 to let a worse copy through anyway. For the case the incident called
# out: a human who has looked and knows the stored copy is the bad one.
FORCE_ENV = "FLUXUS_ALLOW_DOWNGRADE"

# (reading, direction, relative tolerance, absolute floor in rows)
#   "down" -> smaller is better; a rise past BOTH tolerances is the regression
#   "up"   -> larger is better; a fall past BOTH tolerances is the regression
GATES: Tuple[Tuple[str, str, float, int], ...] = (
    # Missingness counters. A doubling is not weather: these sat at 64 / 75 on
    # a healthy 08-27 run and at 266 / 277 on the one that overwrote it. 50%
    # leaves the whole healthy range untouched while catching a 4x blowout.
    ("bars_missing", "down", 0.50, 25),
    ("bars_stale",   "down", 0.50, 25),
    ("unmeasurable", "down", 0.50, 25),
    # Population counters. 5% is not invented here either: it is the size of
    # the 08-27 panel shrinkage, i.e. the smallest damage we have actually
    # seen and want reported -- the same number `audit_regression_gate` uses.
    ("rows",         "up",   0.05, 50),
    ("tradeable",    "up",   0.05, 50),
)

# How many previously-healthy columns have to go degraded before D3 fires. The
# 08-27 overwrite added four (bar_date, bar_scale_mismatch, bars_stale,
# vol_5d_50d) on top of the one already there. Three is that number with one
# of margin, and it is the least-supported threshold in this file: n=1, and D3
# has never been the rule that fired -- D1 always got there first.
DEGRADED_GROWTH = 3

# Field statuses that do not count as "degraded" for D3. `unpopulated` is the
# verdict for a column that has never carried data; counting it would make the
# gate fire on the day a new empty column appears.
HEALTHY_FIELD_STATUSES = frozenset({"ok", "unpopulated"})


def session_of(payload: Mapping[str, Any]) -> Optional[str]:
    """The session a universe.json claims, read from the rows themselves.

    Taken as the modal `bar_date` rather than from `quality.json` or the file's
    `timestamp`: `timestamp` is when the run wrote, not what it measured (the
    08-27 overwrite carried a 08-28 timestamp), and `quality.json` is a
    different file written at the very end of the run, so a run that died in
    between leaves the two disagreeing. The modal bar_date is carried by the
    file being compared, which is the only copy that cannot go out of sync
    with itself.
    """
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return None
    dates = Counter(r.get("bar_date") for r in rows
                    if isinstance(r, Mapping) and r.get("bar_date"))
    if not dates:
        return None
    return str(dates.most_common(1)[0][0])


def readings(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """The comparable vector for one universe.json-shaped payload.

    Deliberately one function used on BOTH sides. The stored copy and the
    candidate are the same shape, and computing them through two code paths is
    how a comparison ends up measuring two different things.
    """
    quality = payload.get("quality")
    quality = quality if isinstance(quality, Mapping) else {}
    rows: Sequence[Any] = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    tradeable = quality.get("tradeable")
    tradeable = tradeable if isinstance(tradeable, Mapping) else {}
    fields = quality.get("fields")
    fields = fields if isinstance(fields, Mapping) else {}

    degraded = sorted(
        name for name, f in fields.items()
        if isinstance(f, Mapping) and f.get("status") not in HEALTHY_FIELD_STATUSES
    )
    return {
        "status": quality.get("status"),
        "rows": len(rows),
        "tradeable": tradeable.get("tradeable"),
        "unmeasurable": tradeable.get("unmeasurable"),
        # Counted here rather than taken from the ledger: the ledger line is
        # written by the run that is asking, so the stored copy has no ledger
        # of its own to read. The rows do carry it, on both sides.
        "bars_missing": sum(1 for r in rows
                            if isinstance(r, Mapping) and r.get("bar_date") is None),
        "bars_stale": sum(1 for r in rows
                          if isinstance(r, Mapping) and r.get("bars_stale") is True),
        "degraded_fields": degraded,
    }


def _rank(status: Any) -> Optional[int]:
    if not isinstance(status, str):
        return None
    return STATUS_RANK.get(status.lower())


def compare(stored: Mapping[str, Any], candidate: Mapping[str, Any]) -> Dict[str, Any]:
    """Is `candidate` materially worse than `stored`? Two reading vectors in."""
    reasons: List[str] = []
    findings: List[Dict[str, Any]] = []

    # D1 -- status downgrade.
    s_rank, c_rank = _rank(stored.get("status")), _rank(candidate.get("status"))
    if s_rank is not None and c_rank is not None and c_rank > s_rank:
        reasons.append(f"D1 universe_quality.status: {stored['status']} -> {candidate['status']}")
        findings.append({"rule": "D1", "metric": "status",
                         "stored": stored.get("status"), "candidate": candidate.get("status")})

    # D2 -- directional count regression, relative AND absolute.
    for name, direction, rel_tol, abs_floor in GATES:
        a, b = stored.get(name), candidate.get(name)
        if not _is_number(a) or not _is_number(b) or a == 0:
            continue
        delta = b - a
        rel = delta / abs(a)
        worse = (delta > 0 and direction == "down") or (delta < 0 and direction == "up")
        if not worse or abs(rel) <= rel_tol or abs(delta) < abs_floor:
            continue
        reasons.append(
            f"D2 {name}: {a} -> {b} ({rel:+.0%}, {delta:+d} rows; "
            f"trips at {rel_tol:.0%} AND {abs_floor} rows, {direction}-is-better)")
        findings.append({"rule": "D2", "metric": name, "stored": a, "candidate": b,
                         "rel": rel, "delta": delta})

    # D3 -- previously-healthy columns that went degraded.
    s_deg = stored.get("degraded_fields")
    c_deg = candidate.get("degraded_fields")
    if isinstance(s_deg, list) and isinstance(c_deg, list):
        new = [f for f in c_deg if f not in set(s_deg)]
        if len(new) >= DEGRADED_GROWTH:
            reasons.append(f"D3 {len(new)} columns newly degraded "
                           f"(threshold {DEGRADED_GROWTH}): {', '.join(new[:8])}")
            findings.append({"rule": "D3", "metric": "degraded_fields",
                             "stored": s_deg, "candidate": c_deg, "new_fields": new})

    return {"worse": bool(reasons), "reasons": reasons, "findings": findings,
            "stored": dict(stored), "candidate": dict(candidate)}


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def load_stored(path: Path) -> Optional[Dict[str, Any]]:
    """The universe.json already on disk, or None if there is nothing usable."""
    try:
        if not path.exists():
            return None
        doc = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def check_overwrite(path: Path, candidate_payload: Mapping[str, Any],
                    candidate_session: Optional[str] = None) -> Dict[str, Any]:
    """Decide whether `candidate_payload` may overwrite the file at `path`.

    Returns a dict with `blocked` (bool), `status` (a ledger word), `reason`
    (one line for the log) and `detail` (numbers for the ledger). Never
    raises: a gate that can crash the run is worse than the leak it plugs, so
    anything unexpected resolves to "allow" and says why.
    """
    out: Dict[str, Any] = {"blocked": False, "status": "ok", "reason": "",
                           "detail": {}}
    try:
        stored_doc = load_stored(path)
        if stored_doc is None:
            out.update(status="no-baseline",
                       reason=f"no readable {path.name} on disk -- nothing to compare against")
            return out

        stored_session = session_of(stored_doc)
        cand_session = candidate_session or session_of(candidate_payload)
        if stored_session is None or cand_session is None:
            out.update(status="no-baseline",
                       reason="session undetermined on one side -- comparison would be "
                              "between unknown days")
            return out
        if stored_session != cand_session:
            out.update(status="no-baseline",
                       reason=f"stored copy is session {stored_session}, candidate is "
                              f"{cand_session} -- a different day is the market moving, "
                              f"not the pipeline")
            out["detail"] = {"stored_session": stored_session, "candidate_session": cand_session}
            return out

        rep = compare(readings(stored_doc), readings(candidate_payload))
        out["detail"] = {"session": cand_session, "stored": rep["stored"],
                         "candidate": rep["candidate"], "findings": rep["findings"]}
        if not rep["worse"]:
            out.update(status="ok",
                       reason=f"candidate is not worse than the stored copy of {cand_session}")
            return out

        joined = "; ".join(rep["reasons"])
        if os.environ.get(FORCE_ENV):
            out.update(status="forced", reason=f"WORSE but {FORCE_ENV} is set -- writing anyway: {joined}")
            return out
        out.update(blocked=True, status="blocked",
                   reason=f"refusing to overwrite the stored copy of {cand_session} with a "
                          f"worse one: {joined}")
        return out
    except Exception as exc:  # noqa: BLE001 -- see docstring
        out.update(status="error", reason=f"gate itself failed ({exc!r}) -- allowing the write")
        return out
