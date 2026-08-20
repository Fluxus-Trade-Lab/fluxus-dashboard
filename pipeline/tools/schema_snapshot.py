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
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

OUTPUT = Path("data/output")
SNAPSHOT = Path("data/reference/schema_snapshot.json")
SAMPLE = 200


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
            # a dict keyed by ticker/date whose values are row lists
            inner = [e for x in vals[:50] for e in x[:20] if isinstance(e, dict)]
            if inner:
                ks = set()
                for e in inner[:SAMPLE]:
                    ks.update(e.keys())
                out[path + "{}[]"] = sorted(ks)
            return
        for k, v in node.items():
            _walk(v, f"{path}.{k}" if path else k, out, depth + 1)
    elif isinstance(node, list) and node and isinstance(node[0], dict):
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


def diff(old: Dict[str, Dict[str, Any]], new: Dict[str, Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for f in sorted(set(old) | set(new)):
        if f not in new:
            lines.append(f"{f}: FILE MISSING"); continue
        if f not in old:
            lines.append(f"{f}: new file ({len(new[f].get('top', []))} top-level keys)"); continue
        for sect in sorted(set(old[f]) | set(new[f])):
            a, b = set(old[f].get(sect, [])), set(new[f].get(sect, []))
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
