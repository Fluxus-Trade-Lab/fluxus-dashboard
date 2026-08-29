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

PANEL MODE (`--outputs`)
------------------------
The ledger does not carry the numbers Andy actually looks at. The 08-27
autopsy had to read `watchlist.gated` and friends out of git history by hand.
`--outputs A B` does that mechanically: it walks every `data/output/*.json` at
two commits and compares every integer and every list length they share.

It needs no per-metric direction table, because it only ever compares two
commits that claim **the same session**. Same input day, same numbers -- so a
move in either direction is worth a look, and the tool refuses outright when
the two commits carry different session dates (that comparison would be the
market moving, not the pipeline).

Two prunings keep the key space readable, both generic rather than curated:
a depth limit, and skipping any dict with more than MAX_FANOUT keys -- that
shape is an entity index (`events.TCBX`, one key per ticker), not structure.
Without them the same pair yields 26,994 keys and 114 movers, nearly all of
them one ticker gaining an event.

**Panel mode is a reporting instrument, not a gate.** It exits 0. Measured on
the only two same-session pairs in git history, at a 2% tolerance over 261
comparable keys:

    3a4d4bc1 -> 7b9d469e   ok -> ok          7 movers (+3 by design)
    7b9d469e -> 03761dc8   ok -> degraded   40 movers

Nearly 6x apart, and the damaged pair's movers are coherent -- the universe
shrank 3.8% and thirty downstream counts shrank with it -- where the healthy
pair's are scattered and small. That is suggestive. It is not a calibrated
boundary: n = 2, one of each. Turning a mover count into a threshold needs a
baseline we do not have, the same reason `audit_mutation_sweep` still
returns 0.

Usage:

    python -m pipeline.tools.audit_regression_gate              # whole ledger
    python -m pipeline.tools.audit_regression_gate --session 2026-08-27
    python -m pipeline.tools.audit_regression_gate --strict     # R2 fatal too
    python -m pipeline.tools.audit_regression_gate --outputs A B
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


# --------------------------------------------------------------------------
# panel mode -- two commits of data/output, same session
# --------------------------------------------------------------------------

OUTPUTS = "data/output"

# Depth past which a JSON path stops being structure and starts being data.
MAX_DEPTH = 3
# A dict wider than this is an entity index (one key per ticker), not a shape.
MAX_FANOUT = 30
# Relative move a shared count has to make before it is worth printing.
PANEL_TOL = 0.02

# Keys that move between two runs of the same session *by design*. They are
# reported in their own section rather than dropped: a benign key that fires
# in the headline list every time is how a report teaches people to skip it,
# but silently deleting one is how real damage hides behind a docstring.
BY_DESIGN = {
    "universe.json": {"quality.runs_in_baseline"},   # counts the runs, so a rerun increments it
    "shortlist.json": {"manual[]", "cards[]"},       # Andy hand-edits these between runs
}


def _git(args: List[str], cwd: Optional[Path] = None) -> Optional[str]:
    import subprocess
    try:
        done = subprocess.run(["git"] + args, capture_output=True, text=True,
                              cwd=str(cwd) if cwd else None)
    except OSError:
        return None
    return done.stdout if done.returncode == 0 else None


def flatten_counts(doc: Any, max_depth: int = MAX_DEPTH,
                   max_fanout: int = MAX_FANOUT) -> Dict[str, int]:
    """Every integer and every list length in a document, by dotted path.

    Floats are left out on purpose: a price or a ratio moving is the market,
    a count moving is the pipeline.
    """
    out: Dict[str, int] = {}

    def walk(node: Any, path: str, depth: int) -> None:
        if depth > max_depth:
            return
        if isinstance(node, dict):
            if len(node) > max_fanout:
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else str(k), depth + 1)
        elif isinstance(node, list):
            out[f"{path}[]"] = len(node)
        elif isinstance(node, bool):
            return
        elif isinstance(node, int):
            out[path] = node

    walk(doc, "", 0)
    return out


def panel_counts(ref: str, repo: Optional[Path] = None) -> Dict[str, Dict[str, int]]:
    """{filename: {path: count}} for every data/output/*.json at `ref`."""
    listing = _git(["ls-tree", "--name-only", ref, f"{OUTPUTS}/"], repo)
    if listing is None:
        return {}
    out: Dict[str, Dict[str, int]] = {}
    for path in listing.split():
        if not path.endswith(".json"):
            continue
        blob = _git(["show", f"{ref}:{path}"], repo)
        if blob is None:
            continue
        try:
            doc = json.loads(blob)
        except json.JSONDecodeError:
            continue
        out[path.rsplit("/", 1)[-1]] = flatten_counts(doc)
    return out


def session_of(ref: str, repo: Optional[Path] = None) -> Optional[str]:
    """The session a commit's outputs claim, read from quality.json."""
    blob = _git(["show", f"{ref}:{OUTPUTS}/quality.json"], repo)
    if blob is None:
        return None
    try:
        return json.loads(blob).get("date")
    except json.JSONDecodeError:
        return None


def compare_panels(baseline: Dict[str, Dict[str, int]],
                   candidate: Dict[str, Dict[str, int]],
                   tol: float = PANEL_TOL) -> Dict[str, Any]:
    movers: List[Dict[str, Any]] = []
    by_design: List[Dict[str, Any]] = []
    comparable = 0
    for filename, base in baseline.items():
        cand = candidate.get(filename)
        if not cand:
            continue
        for key in sorted(set(base) & set(cand)):
            comparable += 1
            a, b = base[key], cand[key]
            if a == b or a == 0:
                continue
            rel = (b - a) / abs(a)
            if abs(rel) <= tol:
                continue
            row = {"file": filename, "key": key, "baseline": a,
                   "candidate": b, "rel": rel}
            (by_design if key in BY_DESIGN.get(filename, set()) else movers).append(row)
    movers.sort(key=lambda r: abs(r["rel"]), reverse=True)
    by_design.sort(key=lambda r: abs(r["rel"]), reverse=True)
    return {"comparable": comparable, "movers": movers, "by_design": by_design,
            "tolerance": tol}


def audit_outputs(baseline_ref: str, candidate_ref: str,
                  repo: Optional[Path] = None,
                  tol: float = PANEL_TOL) -> Dict[str, Any]:
    s_a, s_b = session_of(baseline_ref, repo), session_of(candidate_ref, repo)
    if s_a is None or s_b is None:
        return {"error": f"no session date at {baseline_ref if s_a is None else candidate_ref} "
                         f"(data/output/quality.json unreadable there)",
                "baseline_ref": baseline_ref, "candidate_ref": candidate_ref}
    if s_a != s_b:
        return {"error": f"different sessions ({s_a} vs {s_b}) -- that comparison is "
                         f"the market moving, not the pipeline",
                "baseline_ref": baseline_ref, "candidate_ref": candidate_ref,
                "baseline_session": s_a, "candidate_session": s_b}
    out = compare_panels(panel_counts(baseline_ref, repo),
                         panel_counts(candidate_ref, repo), tol=tol)
    out.update({"baseline_ref": baseline_ref, "candidate_ref": candidate_ref,
                "session": s_a})
    return out


def render_outputs(out: Dict[str, Any]) -> str:
    if "error" in out:
        return f"panel mode refused: {out['error']}"
    L = [f"{out['session']}  {out['baseline_ref']} -> {out['candidate_ref']}  "
         f"({out['comparable']} comparable counts, tolerance {out['tolerance']:.0%})"]
    for r in out["movers"]:
        L.append(f"    {r['file']:22s} {r['key'][:40]:40s} "
                 f"{r['baseline']:>7} -> {r['candidate']:>7}  {r['rel']:+.1%}")
    if out["by_design"]:
        L.append("  moves between runs by design (not damage):")
        for r in out["by_design"]:
            L.append(f"    {r['file']:22s} {r['key'][:40]:40s} "
                     f"{r['baseline']:>7} -> {r['candidate']:>7}  {r['rel']:+.1%}")
    L.append(f"{len(out['movers'])} mover(s). The only two same-session pairs in "
             f"git history scored 7 (both runs healthy) and 40 (the 08-27 "
             f"overwrite). Reference points, not a threshold -- n=2.")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--session", help="only this session (YYYY-MM-DD)")
    ap.add_argument("--strict", action="store_true",
                    help="R2/R3 count regressions become violations too")
    ap.add_argument("--outputs", nargs=2, metavar=("BASELINE_REF", "CANDIDATE_REF"),
                    help="compare data/output panel counts at two commits of the "
                         "same session (reporting only, always exits 0)")
    ap.add_argument("--repo", type=Path, help="repository to read refs from")
    ap.add_argument("--panel-tol", type=float, default=PANEL_TOL)
    ap.add_argument("--json", type=Path, help="write the full report here")
    args = ap.parse_args(argv)

    if args.outputs:
        out = audit_outputs(args.outputs[0], args.outputs[1], repo=args.repo,
                            tol=args.panel_tol)
        print(render_outputs(out))
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(out, indent=2))
        return 2 if "error" in out else 0

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
