"""Run-ledger invariants -- someone finally reads the evidence.

`pipeline/run_ledger.py` has written one JSON line per run since 08-19: every
guard's verdict plus the numbers behind it. The 08-19 breadth blackout
(`data/reference/incidents/2026-08-19_breadth_blackout.md`) ended with the
line that motivates this file -- the ledger recorded `breadth: ok,
regime_score: None` that night and the incident note says of it: **evidence
on file, nobody reads it**. A status word costs nothing to emit; what makes a
guard load-bearing is something re-reading the number it filed.

So this is `audit_archives` for the ledger. The archives auditor asks "is
what we stored well-formed"; this asks "did the run that stored it actually
do its job, and did each guard's own evidence back up the word it used":

  L1  the last completed session has a line at all (no line = the nightly
      run did not happen, or died before Ledger.write(); no archive check
      can see this, because a run that never ran writes nothing anywhere)
  L2  no guard reports a non-ok status (fail/error = violation,
      degraded/skipped = warning)
  L3  a guard that says "ok" carries the evidence that makes ok mean
      something (EVIDENCE below) -- this is exactly the 08-19 shape:
      status ok, regime_score null, the four enriched blocks missing
  L4  the run's own errors[] is empty
  L5  no guard that ran in the previous session is missing from this one
      (a stage silently dropped out of the orchestrator) -- warning, since
      guards do legitimately get added and retired
  L6  same-session duplicates and numeric drift vs the trailing window
      (fundamentals failure rate, universe rows) -- reported, never fatal;
      duplicates are by design (a re-run is a second line, both happened)

Exit code 1 on any L1/L2(fail)/L3/L4 violation, 0 otherwise. Read-only: it
never writes into data/history, only to an explicit --json path.

    python -m pipeline.tools.audit_ledger              # last session
    python -m pipeline.tools.audit_ledger --window 30  # the monthly report
    python -m pipeline.tools.audit_ledger --json out.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.marketcal import last_completed_session

LEDGER = Path("data/history/run_ledger.jsonl")

# guard -> what "ok" has to be able to show. Each entry is a list of
# (field path, predicate name); the predicate is applied to row["guards"][g].
#   "num+"   number present and > 0
#   "num0+"  number present and >= 0 (0 is a real answer, None is not)
#   "list4"  the four enriched breadth blocks, all of them
#   "dict+"  non-empty mapping
#   "allok"  mapping whose every value is the string "ok"
EVIDENCE: Dict[str, List[tuple]] = {
    "breadth":          [("regime_score", "num+"), ("enriched", "list4")],
    "ticker_events":    [("rows_today", "num+")],
    "universe_quality": [("rows", "num+")],
    "watchlist":        [("panels", "dict+")],
    "screeners":        [("counts", "dict+")],
    "site_quality":     [("sources", "allok")],
    "shortlist":        [("cards", "num+")],
    "asset_signals":    [("count", "num+")],
    "fundamentals":     [("store", "num+"), ("ok", "num0+")],
}
BREADTH_BLOCKS = {"conditions", "regime", "state_board", "verdict"}
OK_WORDS = {"ok", "OK", True}
WARN_WORDS = {"degraded", "skipped", "stale", "partial"}
FUND_FAIL_WARN = 0.20      # >20% of the night's fundamentals fetches failing
DRIFT_WARN = 0.10          # universe rows moving >10% vs the window median


def _load(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"session": None, "_unparsable": line[:120]})
    return rows


def _holds(guard: Dict[str, Any], field: str, pred: str) -> bool:
    v = guard.get(field)
    if pred == "num+":
        return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
    if pred == "num0+":
        return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0
    if pred == "list4":
        return isinstance(v, (list, tuple)) and BREADTH_BLOCKS.issubset(set(v))
    if pred == "dict+":
        return isinstance(v, dict) and len(v) > 0
    if pred == "allok":
        return isinstance(v, dict) and len(v) > 0 and all(x in OK_WORDS for x in v.values())
    raise ValueError(f"unknown predicate {pred}")


def audit_run(row: Dict[str, Any], prev_guards: Optional[set] = None) -> Dict[str, Any]:
    """L2-L5 for one ledger line."""
    rep: Dict[str, Any] = {"session": row.get("session"), "code_sha": row.get("code_sha"),
                           "trigger": row.get("trigger"), "violations": [], "warnings": []}
    guards = row.get("guards") or {}
    if "_unparsable" in row:
        rep["violations"].append("L0 unparsable ledger line")
        return rep
    if not guards:
        rep["violations"].append("L2 no guards recorded at all")

    for name, g in guards.items():
        status = g.get("status") if isinstance(g, dict) else g
        if status in OK_WORDS:
            for field, pred in EVIDENCE.get(name, []):
                if not _holds(g, field, pred):
                    rep["violations"].append(
                        f"L3 {name} says ok but {field}={json.dumps(g.get(field), default=str)[:60]}")
        elif status in WARN_WORDS:
            rep["warnings"].append(f"L2 {name} {status}" + (f" ({g.get('reason')})" if isinstance(g, dict) and g.get("reason") else ""))
        else:
            rep["violations"].append(f"L2 {name} status={status!r}")

    for e in row.get("errors") or []:
        where = e.get("where") if isinstance(e, dict) else "?"
        msg = e.get("msg") if isinstance(e, dict) else str(e)
        rep["violations"].append(f"L4 error in {where}: {str(msg)[:80]}")

    if prev_guards:
        gone = sorted(prev_guards - set(guards))
        if gone:
            rep["warnings"].append(f"L5 guard(s) present last session, missing now: {', '.join(gone)}")

    # L6 numeric drift, reported only
    f = guards.get("fundamentals") or {}
    due, failed = f.get("due"), f.get("failed")
    if isinstance(due, (int, float)) and due and isinstance(failed, (int, float)):
        rate = failed / due
        rep["fund_fail_rate"] = round(rate, 3)
        if rate > FUND_FAIL_WARN:
            rep["warnings"].append(f"L6 fundamentals failed {failed}/{int(due)} ({rate:.0%})")
    uq = guards.get("universe_quality") or {}
    if isinstance(uq.get("rows"), (int, float)):
        rep["universe_rows"] = uq["rows"]
    return rep


def run(path: Path = LEDGER, window: int = 1, last_done: Optional[dt.date] = None) -> Dict[str, Any]:
    """Audit the newest `window` sessions in the ledger."""
    last_done = last_done or last_completed_session()
    rows = _load(path)
    out: Dict[str, Any] = {"as_of_session": str(last_done), "ledger": str(path),
                           "lines": len(rows), "runs": [], "violations": 0, "warnings": 0,
                           "top": []}

    if not rows:
        out["top"].append(f"L1 ledger has no lines at all ({path})")
        out["violations"] = 1
        out["ok"] = False
        return out

    sessions = sorted({r.get("session") for r in rows if r.get("session")})
    if str(last_done) not in sessions:
        out["top"].append(f"L1 no run recorded for the last completed session {last_done} "
                          f"(newest in ledger: {sessions[-1] if sessions else 'none'})")
        out["violations"] += 1

    wanted = sessions[-window:] if window > 0 else sessions
    for i, s in enumerate(wanted):
        same = [r for r in rows if r.get("session") == s]
        # L5 compares against the session before this one, whatever it is
        idx = sessions.index(s)
        prev = ({g for r in rows if r.get("session") == sessions[idx - 1] for g in (r.get("guards") or {})}
                if idx > 0 else None)
        if len(same) > 1:
            out["top"].append(f"L6 {s}: {len(same)} lines (re-run; both happened, not a violation)")
        for r in same:
            rep = audit_run(r, prev_guards=prev)
            out["runs"].append(rep)
            out["violations"] += len(rep["violations"])
            out["warnings"] += len(rep["warnings"])

    # L6 universe drift across the audited window
    sizes = [r["universe_rows"] for r in out["runs"] if r.get("universe_rows")]
    if len(sizes) >= 3:
        med = statistics.median(sizes)
        for rep in out["runs"]:
            n = rep.get("universe_rows")
            if n and med and abs(n - med) / med > DRIFT_WARN:
                rep["warnings"].append(f"L6 universe {n} vs window median {med:.0f}")
                out["warnings"] += 1

    out["ok"] = out["violations"] == 0
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--window", type=int, default=1, help="how many recent sessions to audit (0 = all)")
    ap.add_argument("--ledger", default=str(LEDGER))
    ap.add_argument("--json", help="write the report here")
    args = ap.parse_args(argv)
    out = run(Path(args.ledger), window=args.window)

    for line in out["top"]:
        print(f"BAD {line}" if line.startswith("L1") else f"    {line}")
    for rep in out["runs"]:
        flag = "OK " if not rep["violations"] else "BAD"
        head = f"{flag} {rep['session']}  {rep['trigger'] or '?':16s} {rep['code_sha'] or '-':8s}"
        detail = "; ".join(rep["violations"] + rep["warnings"])
        print(f"{head} {detail}" if detail else head)
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: {out['violations']} violations, "
          f"{out['warnings']} warnings over {len(out['runs'])} run(s) (session {out['as_of_session']})")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
