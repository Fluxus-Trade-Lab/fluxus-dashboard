"""Claim registry -- the ledger that makes RESEARCH_PROTOCOL.md enforceable.

2026-08-23 (Andy, after the atr_pctl winner's-curse incident: "是建立机制,
熟悉什么是完整的合理的测试环境,什么是专业的测试机制"). The protocol document
says what "tested" means; this tool is its teeth: every quantitative claim
lives as one line in data/research/claims/claims.jsonl, and CI fails when a
claim's status and its evidence (or its use in code) disagree.

Schema, one JSON object per line:

    id            kebab-case, unique, stable
    claim         one sentence, falsifiable, Chinese ok
    direction     "positive" | "null" | "negative"
    status        preregistered | candidate | validated | live | null | retracted
    spec_search_n int -- how many comparisons the headline number was picked
                  from (REQUIRED for positive claims; 1 = a single
                  preregistered test)
    evidence      {in_sample: {...}, holdout: {...}, forward: {...}} -- free
                  dicts; holdout REQUIRED (non-empty) for validated/live
    gates         [str] -- places where this claim CHANGES BEHAVIOUR (a
                  threshold, a seat rule, a panel condition). Non-empty gates
                  require status validated/live/null -- OR a `waiver`
                  {until, reason}: an acknowledged debt that turns CI red by
                  itself the day `until` passes without adjudication. A field merely being
                  COMPUTED is not a gate; list those under code_refs.
    code_refs     [str] -- where it is computed/displayed (no status demand)
    study         path or URL of the write-up
    registered / updated   ISO dates
    notes         optional free text (e.g. retraction reason)

Checks (--check, exit 1 on any violation):
  R1  file parses, ids unique, required keys present, enums valid
  R2  positive claims carry spec_search_n >= 1
  R3  validated/live claims carry non-empty evidence.holdout
  R4  gates non-empty -> status in {validated, live, null}
  R5  retracted claims carry notes (why)
  R6  study paths that look local must exist in the repo

Deliberately NOT checked: whether the numbers are true. The registry makes
claims auditable, not correct -- an auditor (human or session) goes from here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REGISTRY = Path("data/research/claims/claims.jsonl")

STATUSES = {"preregistered", "candidate", "validated", "live", "null", "retracted"}
DIRECTIONS = {"positive", "null", "negative"}
REQUIRED = ("id", "claim", "direction", "status", "registered", "updated", "study")
# gate-bearing claims must have survived a holdout (or be a null guard)
GATE_OK = {"validated", "live", "null"}


def load(path: Path = REGISTRY) -> list[dict]:
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"line {i}: bad JSON ({e})") from e
    return rows


def check(rows: list[dict], repo: Path = Path(".")) -> list[str]:
    errs: list[str] = []
    seen: set[str] = set()
    for r in rows:
        rid = r.get("id", "<no id>")
        for k in REQUIRED:
            if not r.get(k):
                errs.append(f"{rid}: R1 missing `{k}`")
        if rid in seen:
            errs.append(f"{rid}: R1 duplicate id")
        seen.add(rid)
        if r.get("status") not in STATUSES:
            errs.append(f"{rid}: R1 bad status {r.get('status')!r}")
        if r.get("direction") not in DIRECTIONS:
            errs.append(f"{rid}: R1 bad direction {r.get('direction')!r}")
        if r.get("direction") == "positive":
            n = r.get("spec_search_n")
            if not isinstance(n, int) or n < 1:
                errs.append(f"{rid}: R2 positive claim without spec_search_n")
        if r.get("status") in ("validated", "live"):
            ho = (r.get("evidence") or {}).get("holdout")
            if not ho:
                errs.append(f"{rid}: R3 status {r['status']} without evidence.holdout")
        gates = r.get("gates") or []
        if gates and r.get("status") not in GATE_OK:
            # a WAIVER with a deadline turns this into a ticking clock instead
            # of an instant red: existing debts get registered honestly, and
            # CI goes red BY ITSELF the day the deadline passes un-adjudicated.
            w = r.get("waiver") or {}
            until = str(w.get("until") or "")
            from pipeline.marketcal import market_today   # ET, never host JST
            today = market_today().isoformat()
            if until and w.get("reason") and until >= today:
                pass  # acknowledged debt, clock running
            else:
                tail = f" (waiver expired {until})" if until else ""
                errs.append(f"{rid}: R4 gates {gates} but status {r.get('status')!r}"
                            f"{tail} (candidate 不许当规则 -- RESEARCH_PROTOCOL §一 铁律 1)")
        if r.get("status") == "retracted" and not r.get("notes"):
            errs.append(f"{rid}: R5 retracted without notes")
        study = str(r.get("study") or "")
        if study and not study.startswith(("http://", "https://")):
            if not (repo / study).exists():
                errs.append(f"{rid}: R6 study path {study} not found")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--check", action="store_true", help="validate; exit 1 on violations")
    ap.add_argument("--list", action="store_true", help="print one line per claim")
    args = ap.parse_args(argv)
    if not args.registry.exists():
        print(f"no registry at {args.registry}", file=sys.stderr)
        return 1
    try:
        rows = load(args.registry)
    except ValueError as e:
        print(f"VIOLATION {e}", file=sys.stderr)
        return 1
    if args.list or not args.check:
        for r in rows:
            gate = " ⛩" if r.get("gates") else ""
            print(f"{r.get('status', '?'):13s} {r.get('id', '?')}{gate}  {r.get('claim', '')[:70]}")
    if args.check:
        errs = check(rows)
        for e in errs:
            print(f"VIOLATION {e}", file=sys.stderr)
        print(f"{'FAIL' if errs else 'OK'}: {len(rows)} claims, {len(errs)} violations")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
