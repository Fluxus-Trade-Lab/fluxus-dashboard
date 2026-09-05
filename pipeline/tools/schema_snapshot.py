"""Schema snapshot of data/output -- what fields each file carries.

The frontend reads these files by field name; a column that silently
disappears (or appears) is the kind of change DATA_CONTRACTS.md is supposed
to announce and sometimes does not. This keeps a machine snapshot in
`data/reference/schema_snapshot.json` and diffs the live outputs against it.

    python -m pipeline.tools.schema_snapshot --check    # print added/removed, exit 0 always
    python -m pipeline.tools.schema_snapshot --update   # accept the live shape

Per file: top-level keys; for every top-level list-of-dicts (or dict whose
values are lists of dicts, e.g. themes/industries, or the `rows` list) the
union of keys over the first 200 entries. Types are not tracked -- null vs
number on a field is a quality question (quality.py), not a schema one.

An EMPTY collection is recorded as such rather than skipped: "no rows fired
today" and "the rows lost their fields" are different facts, and conflating
them made a quiet EP day look like a schema break (2026-08-24).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

OUTPUT = Path("data/output")
SNAPSHOT = Path("data/reference/schema_snapshot.json")
# Bounds the key-union scan, not a real limit at this repo's sizes (largest
# collection is universe.json's ~5,631 rows) -- see the 2026-09-04 incident
# note on the dict-of-lists branch below for why a small sample is unsafe.
SAMPLE = 20000

# A collection that was measured and held nothing. Distinct from a path that
# is ABSENT (the parent key vanished) -- that one is a real removal. Without
# this distinction an empty list reads as "every field was removed", which is
# what failed the 2026-08-24 nightly run and blocked the whole commit.
EMPTY = None


def _walk(node: Any, path: str, out: Dict[str, Any], depth: int) -> None:
    """Record the key-set at every list-of-dicts / dict-of-dicts down to `depth`."""
    if depth > 6:
        return
    if isinstance(node, dict):
        vals = list(node.values())
        if path and vals and all(isinstance(x, dict) for x in vals[:5]) and len(vals) > 3 \
                and not any(isinstance(k, str) and k in ("summary",) for k in node):
            # a dict keyed by ticker/group name -> treat its values as rows
            ks: set = set()
            for x in vals[:SAMPLE]:
                ks.update(x.keys())
            out[path + "{}"] = sorted(ks)
            _walk(vals[0], path + "{}", out, depth + 1)
            return
        if path and vals and len(vals) > 3 and all(isinstance(x, list) for x in vals[:5]):
            # a dict keyed by ticker/date whose values are row lists (e.g.
            # ticker_events.json's events{}, keyed by ~5,000 tickers).
            #
            # This used to sample only the first 50 keys' first 20 items —
            # cheap, but the sample window sits at the alphabetic front of a
            # ~5,000-ticker dict. A field a low-hit-rate screener contributes
            # (VCP: ~35/5,631 tickers) can have every one of its rows fall
            # outside that window on a given night, and the live shape then
            # reads as the field having been REMOVED though the code never
            # stopped emitting it. 2026-09-04: exactly this blocked a good
            # run's commit over num_contractions/pct_to_pivot, sampled away
            # because no VCP ticker landed in the first 50 keys that night.
            # Same false-positive family as the 08-24/08-25 empty-collection
            # bugs (`EMPTY` above) -- there the collection was silent, here
            # it was just sparse and unluckily ordered out of a small sample.
            # Fix: union over every entry, capped only at SAMPLE for cost
            # (harmless at this repo's sizes; see SAMPLE's comment).
            saw_any = False
            ks: set = set()
            for x in vals:
                for e in x:
                    if isinstance(e, dict):
                        saw_any = True
                        ks.update(e.keys())
                        if len(ks) >= SAMPLE:
                            break
            out[path + "{}[]"] = sorted(ks) if saw_any else EMPTY
            return
        for k, v in node.items():
            _walk(v, f"{path}.{k}" if path else k, out, depth + 1)
    elif isinstance(node, list):
        if not node:
            # Measured, and it held nothing. Recording EMPTY (rather than
            # nothing) is what lets `diff` tell "no rows fired today" apart
            # from "the rows lost their fields" -- see EMPTY's comment.
            if path:
                out[path + "[]"] = EMPTY
            return
        if isinstance(node[0], dict):
            ks: set = set()
            for x in node[:SAMPLE]:
                if isinstance(x, dict):
                    ks.update(x.keys())
            out[path + "[]"] = sorted(ks)
            _walk(node[0], path + "[]", out, depth + 1)


def shape(payload: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {"top": sorted(payload.keys()) if isinstance(payload, dict) else ["<list>"]}
    _walk(payload, "", out, 0)
    return out


def live(output: Path = OUTPUT) -> Dict[str, Dict[str, Any]]:
    snap: Dict[str, Dict[str, Any]] = {}
    for p in sorted(output.glob("*.json")):
        try:
            snap[p.name] = shape(json.loads(p.read_text()))
        except Exception as e:  # noqa: BLE001
            snap[p.name] = {"top": [f"<unreadable: {type(e).__name__}>"]}
    return snap


_ABSENT = object()


def diff(old: Dict[str, Dict[str, Any]], new: Dict[str, Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for f in sorted(set(old) | set(new)):
        if f not in new:
            lines.append(f"{f}: FILE MISSING"); continue
        if f not in old:
            lines.append(f"{f}: new file ({len(new[f].get('top', []))} top-level keys)"); continue
        for sect in sorted(set(old[f]) | set(new[f])):
            ov = old[f].get(sect, _ABSENT)
            nv = new[f].get(sect, _ABSENT)
            # An empty collection is "nothing fired today", not "the fields
            # are gone" -- the 2026-08-24 cron failed on exactly this: no EP
            # fired and no card had a panel hit, so episodic_pivot.json's
            # tickers[] and shortlist.json's cards[].panels[] read as
            # `removed [every field]` and the whole night's data never
            # committed. The shape a real removal has is the PATH going
            # missing (breadth.json's blackout), which stays fatal below.
            if nv is EMPTY:
                if ov not in (EMPTY, _ABSENT):
                    lines.append(f"{f} {sect}: empty today "
                                 f"({len(ov)} field(s) not observable -- not a removal)")
                continue
            if ov is EMPTY:
                if nv is not _ABSENT:
                    lines.append(f"{f} {sect}: populated again ({len(nv)} field(s))")
                continue
            a = set(ov) if ov is not _ABSENT else set()
            b = set(nv) if nv is not _ABSENT else set()
            if a - b:
                lines.append(f"{f} {sect}: removed {sorted(a - b)}")
            if b - a:
                lines.append(f"{f} {sect}: added {sorted(b - a)}")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--output", default=str(OUTPUT))
    ap.add_argument("--snapshot", default=str(SNAPSHOT))
    args = ap.parse_args(argv)
    now = live(Path(args.output))
    snap_path = Path(args.snapshot)
    if args.update or not snap_path.exists():
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(json.dumps(now, indent=1, sort_keys=True))
        print(f"snapshot written: {snap_path} ({len(now)} files)")
        return 0
    old = json.loads(snap_path.read_text())
    lines = diff(old, now)
    if lines:
        print("SCHEMA CHANGES vs snapshot:")
        for l in lines:
            print("  " + l)
        print("\n(accept with --update after DATA_CONTRACTS.md says so)")
    else:
        print(f"schema unchanged ({len(now)} files)")
    # Removed fields and missing files are BREAKS, not drift: the 2026-08-19
    # nightly run printed "breadth.json top: removed [conditions, regime,
    # state_board, verdict]" right here and then committed anyway -- the whole
    # Breadth page went dark for a day. Additions stay report-only (new
    # columns land on purpose); a deliberate removal ships its --update in
    # the same commit as the code that removes the field.
    broken = [l for l in lines if ": removed " in l or "FILE MISSING" in l]
    if broken:
        print(f"\n{len(broken)} removal(s): failing the check", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
