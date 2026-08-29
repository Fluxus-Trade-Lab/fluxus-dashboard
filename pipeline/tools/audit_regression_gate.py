"""Regression gate -- the one question none of our other gates asks.

Every guard we own asks *"is this data self-consistent?"*. `audit_archives`
I1-I7 check the archive against itself; `audit_ledger` L1-L6 check a run
against its own evidence; `universe_quality` checks null rates against
absolute thresholds. None of them asks the other question:

    **is this one better than the one it replaced?**

That hole has a name and a date. On 2026-08-27 the main schedule fired 485
minutes late, found session 2026-08-27 already landed twice and healthy, ran
anyway, and overwrote `universe_quality: ok` with `degraded` -- `bars_missing`
64 -> 266, `unmeasurable` 75 -> 277, 15 of 19 panels ~5% smaller. Three runs,
all `success`, and not one gate made a sound. Full autopsy:
`data/reference/incidents/2026-08-29_late_run_overwrote_healthy_data.md`.

`audit_ledger` L6 comes closest -- it *notices* the duplicate lines and then
says, in as many words, "re-run; both happened, not a violation". It is right
that a re-run is legal. It just never compares the two.

So this file compares them. It reads one direction-aware vector of key
readings per run and reports where the run that *won* (the later writer) is
worse than the one it replaced.

Direction matters more than magnitude here. `bars_missing` going up is bad;
`tradeable` going up is good; `rows_today` is bad in *both* directions (1674
is a thin day, 5810 meant every row got flagged). A gate that only knows
"changed by X%" cannot tell an improvement from a regression, which is
precisely how the 08-19 re-run (degraded -> ok, a genuine repair) has to stay
green while the 08-27 one goes red.

  R1  status downgrade -- a status word moved down the ladder
      (ok < degraded < stale < severe < fail). Categorical, no threshold to
      tune, and the only tier that exits non-zero by default.
  R2  count regression -- a directional number moved the wrong way by more
      than its tolerance. Warning by default; `--strict` promotes to
      violation.
  R3  degraded-set growth -- fields that were fine in the baseline and are
      degraded in the candidate, listed by name.

What this gate CANNOT see (stated so nobody reads its silence as safety):

  * a single run per session. With no baseline there is nothing to regress
    against; those sessions are reported as `no-baseline`, not as clean.
  * a bad run that is bad in *both* copies -- this measures relative damage
    only. Absolute badness is `universe_quality`'s job.
  * anything not in the ledger. Panel counts (`true_market_leaders`,
    `bullish_4pct`, ...) live in `data/output/`; the 08-27 autopsy had to
    read them out of git history by hand. Extending to those means diffing
    two commits, not two ledger lines -- deliberately out of scope here.

Usage:

    python -m pipeline.tools.audit_regression_gate              # whole ledger
    python -m pipeline.tools.audit_regression_gate --session 2026-08-27
    python -m pipeline.tools.audit_regression_gate --strict     # R2 fatal too
    python -m pipeline.tools.audit_regression_gate --json out.json

Read-only. It never writes into data/history, only to an explicit --json path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LEDGER = Path("data/history/run_ledger.jsonl")

# Status ladder. Higher index = worse. A candidate whose index exceeds the
# baseline's is R1, full stop -- no tolerance, because these words are already
# the pipeline's own summary judgement and it demoted itself.
STATUS_RANK: Dict[str, int] = {
    "ok": 0,
    "skipped": 1,
    "degraded": 2,
    "stale": 2,
    "severe": 3,
    "fail": 4,
    "error": 4,
}

# Which guards carry a status word worth watching.
STATUS_FIELDS: Tuple[str, ...] = (
    "universe_quality",
    "ticker_events",
    "breadth",
    "fundamentals",
    "asset_signals",
)

# (label, guard, dotted path inside the guard, direction, tolerance)
#   direction "up"   -> larger is better, a drop is the regression
#   direction "down" -> smaller is better, a rise is the regression
#   direction "both" -> either way past tolerance is a regression
# Tolerance is a fraction of the baseline value. 0.05 is not a tuned number:
# it is the size of the 08-27 panel shrinkage, i.e. the smallest damage we
# have actually seen and want reported. Section "calibration" in the report
# for what it costs in false positives on the ledger we have.
COUNTS: Tuple[Tuple[str, str, str, str, float], ...] = (
    ("universe rows",        "universe_quality", "rows",                   "up",   0.05),
    ("tradeable",            "universe_quality", "tradeable.tradeable",    "up",   0.05),
    ("bars_missing",         "universe_quality", "bars_missing",           "down", 0.05),
    ("bars_stale",           "universe_quality", "bars_stale",             "down", 0.05),
    ("unmeasurable",         "universe_quality", "tradeable.unmeasurable", "down", 0.05),
    ("ticker_events rows",   "ticker_events",    "rows_today",             "both", 0.25),
    ("fundamentals ok",      "fundamentals",     "ok",                     "up",   0.05),
    ("fundamentals store",   "fundamentals",     "store",                  "up",   0.05),
)

# Deliberately NOT here: breadth.regime_score. It is a reading of the market,
# not of our data quality -- 43.8 -> 34.4 is the tape moving, and a gate that
# calls that a regression is measuring the wrong thing.


def _dig(obj: Any, path: str) -> Any:
    """Follow a dotted path, returning None the moment it stops resolving."""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _rank(status: Any) -> Optional[int]:
    if not isinstance(status, str):
        return None
    return STATUS_RANK.get(status.lower())


def compare(baseline: Dict[str, Any], candidate: Dict[str, Any],
            strict: bool = False) -> Dict[str, Any]:
    """Compare two ledger rows. `candidate` is the later run -- the one that won."""
    violations: List[str] = []
    warnings: List[str] = []
    findings: List[Dict[str, Any]] = []

    base_g = baseline.get("guards") or {}
    cand_g = candidate.get("guards") or {}

    # R1 -- status downgrade
    for guard in STATUS_FIELDS:
        b_rank = _rank(_dig(base_g, f"{guard}.status"))
        c_rank = _rank(_dig(cand_g, f"{guard}.status"))
        if b_rank is None or c_rank is None:
            continue
        if c_rank > b_rank:
            msg = (f"R1 {guard}: {_dig(base_g, f'{guard}.status')} -> "
                   f"{_dig(cand_g, f'{guard}.status')}")
            violations.append(msg)
            findings.append({"rule": "R1", "metric": guard, "tier": "violation",
                             "baseline": _dig(base_g, f"{guard}.status"),
                             "candidate": _dig(cand_g, f"{guard}.status")})

    # R2 -- directional count regression
    for label, guard, path, direction, tol in COUNTS:
        b = _dig(base_g, f"{guard}.{path}")
        c = _dig(cand_g, f"{guard}.{path}")
        if not isinstance(b, (int, float)) or not isinstance(c, (int, float)):
            continue
        if isinstance(b, bool) or isinstance(c, bool):
            continue
        if b == 0:
            # No proportional baseline to measure against. A rise from zero on
            # a "down" metric is still worth saying out loud; a rise from zero
            # on an "up" metric is an improvement.
            if direction in ("down", "both") and c > 0:
                warnings.append(f"R2 {label}: 0 -> {c} (no baseline to scale by)")
                findings.append({"rule": "R2", "metric": label, "tier": "warning",
                                 "baseline": b, "candidate": c, "rel": None})
            continue
        rel = (c - b) / abs(b)
        bad = ((direction == "up" and rel < -tol)
               or (direction == "down" and rel > tol)
               or (direction == "both" and abs(rel) > tol))
        if not bad:
            continue
        msg = f"R2 {label}: {b} -> {c} ({rel:+.0%}, tolerance {tol:.0%} {direction})"
        (violations if strict else warnings).append(msg)
        findings.append({"rule": "R2", "metric": label,
                         "tier": "violation" if strict else "warning",
                         "baseline": b, "candidate": c, "rel": rel})

    # R3 -- degraded-set growth, by name
    b_deg = _dig(base_g, "universe_quality.degraded")
    c_deg = _dig(cand_g, "universe_quality.degraded")
    if isinstance(b_deg, list) and isinstance(c_deg, list):
        new = [f for f in c_deg if f not in set(b_deg)]
        if new:
            shown = ", ".join(new[:8]) + (f", +{len(new) - 8} more" if len(new) > 8 else "")
            msg = f"R3 universe_quality degraded +{len(new)}: {shown}"
            (violations if strict else warnings).append(msg)
            findings.append({"rule": "R3", "metric": "universe_quality.degraded",
                             "tier": "violation" if strict else "warning",
                             "baseline": len(b_deg), "candidate": len(c_deg),
                             "new_fields": new})

    return {
        "baseline_run": baseline.get("run_id"),
        "candidate_run": candidate.get("run_id"),
        "session": candidate.get("session"),
        "violations": violations,
        "warnings": warnings,
        "findings": findings,
        "ok": not violations,
    }


def load_ledger(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _order_key(row: Dict[str, Any]) -> str:
    """Runs are ordered by when they finished -- the last writer wins on disk."""
    return str(row.get("finished_utc") or row.get("started_utc") or "")


def audit(rows: List[Dict[str, Any]], session: Optional[str] = None,
          strict: bool = False) -> Dict[str, Any]:
    """Walk every session that ran more than once and compare the reruns in order."""
    sessions: List[str] = []
    for r in rows:
        s = r.get("session")
        if s and s not in sessions:
            sessions.append(s)
    if session:
        sessions = [s for s in sessions if s == session]

    out: Dict[str, Any] = {"pairs": [], "no_baseline": [],
                           "violations": 0, "warnings": 0, "strict": strict}
    for s in sessions:
        same = sorted([r for r in rows if r.get("session") == s], key=_order_key)
        if len(same) < 2:
            out["no_baseline"].append(s)
            continue
        # Compare each run against the one before it: the damage is done by
        # whichever run wrote last, but an intermediate regression that a
        # later run repaired is still worth seeing.
        for prev, cur in zip(same, same[1:]):
            rep = compare(prev, cur, strict=strict)
            out["pairs"].append(rep)
            out["violations"] += len(rep["violations"])
            out["warnings"] += len(rep["warnings"])

    out["ok"] = out["violations"] == 0
    return out


def render(out: Dict[str, Any]) -> str:
    lines: List[str] = []
    if not out["pairs"]:
        lines.append("no same-session reruns in range -- nothing to compare")
    for rep in out["pairs"]:
        head = (f"{rep['session']}  {rep['baseline_run']} -> {rep['candidate_run']}"
                f"  {'OK' if rep['ok'] and not rep['warnings'] else ('WARN' if rep['ok'] else 'REGRESSION')}")
        lines.append(head)
        for v in rep["violations"]:
            lines.append(f"    ! {v}")
        for w in rep["warnings"]:
            lines.append(f"    - {w}")
    if out["no_baseline"]:
        lines.append(f"no-baseline (single run, cannot be checked): "
                     f"{', '.join(out['no_baseline'])}")
    lines.append(f"{len(out['pairs'])} pair(s) | {out['violations']} violation(s) | "
                 f"{out['warnings']} warning(s)")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--session", help="only this session (YYYY-MM-DD)")
    ap.add_argument("--strict", action="store_true",
                    help="R2/R3 count regressions become violations too")
    ap.add_argument("--json", type=Path, help="write the full report here")
    args = ap.parse_args(argv)

    rows = load_ledger(args.ledger)
    if not rows:
        print(f"no ledger rows at {args.ledger}", file=sys.stderr)
        return 2

    out = audit(rows, session=args.session, strict=args.strict)
    print(render(out))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
