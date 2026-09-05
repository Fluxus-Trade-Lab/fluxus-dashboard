"""Wiring -- is this guard on the chain at all, or only correct?

Every other `audit_*` in this directory asks whether some quantity is right.
None of them asks the prior question: **does anything ever run me?**

That question has now cost us three separate outages of the same shape:

  2026-08-31  `no_downgrade` was wired into `run_all.py` at 4f2fe309 and the
              27 lines were deleted the same day by 8e4a64ef, a conflict
              resolved by hand. The module (294 lines) and its tests (269
              lines) were untouched and stayed green for three days, because
              they test the module, not the call site. Nothing stopped a late
              run from overwriting good data until 89ba7d94 on 2026-09-03.
  2026-09-02  1,347 tests, no automatic trigger. Still true as of this file:
              no workflow in `.github/workflows/` runs pytest, and not one of
              the six declares `on: push` or `on: pull_request`.
  2026-09-03  three of seven `audit_*` gates have no automatic trigger at all.

    We keep verifying that a thing is CORRECT. We never verify that it is
    CONNECTED. A guard nobody calls and a guard that does not exist are the
    same guard.

⚠️ Why this file is a RATCHET and not an alarm.

Three gates are unwired *today*, and wiring them means editing workflow files.
If this audit simply went red on the current state it would be red for weeks,
and a permanently red check is a check everybody learns to skip -- which is the
disease, not the cure. So the known-unwired set is declared below with an owner
and the date it was found, and the audit is GREEN on exactly that set. It goes
RED when the situation CHANGES:

  W1  a guard exists that is neither wired, exempt, nor in the known set
      -- a NEW gate that nobody calls, i.e. the 08-31 shape happening again
  W2  a known-unwired guard is now wired, but still listed here
      -- the anti-rot half: fixing it forces you to delete the excuse
  W3  an entry names a module that no longer exists
  W4  an entry carries no owner or no reason

W2/W3/W4 are what stop this table from decaying into a permanent allowlist.

⚠️ What counts as "wired" -- and why this file parses instead of grepping.

`grep audit_archives .github/workflows/` gets four hits and two of them are
COMMENTS describing the guard. Reading a name is not observing a call. So:

  * workflows are parsed, `run:` blocks are extracted, and comment lines inside
    them are stripped before looking for `python -m pipeline.tools.X`
  * a workflow only counts if it has an AUTOMATIC trigger (`schedule`, `push`,
    `pull_request`). `workflow_dispatch` alone is a human pressing a button,
    which is exactly the thing we are trying to stop relying on
  * production Python is parsed with `ast`: a module counts as invoked only if
    a name imported from it is actually CALLED somewhere

That last rule matters more than it looks. `pipeline/no_downgrade.py` line 85
does `from pipeline.tools.audit_regression_gate import STATUS_RANK` -- a real
import of a real symbol, which any grep reports as a caller. It imports a
lookup table and never calls the gate. Under `ast` it correctly reads as
unwired, because the name is only ever subscripted.

Tests are NOT a trigger here. A wiring assertion in `pipeline/tests/` only runs
when a human types pytest, and this repo has no CI that types it. Counting
tests as wiring would let the whole suite vouch for itself.

`check()` is pure. Reading the tree lives in `collect()`.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

GUARD_GLOB = "pipeline/tools/audit_*.py"
AUTOMATIC_TRIGGERS = {"schedule", "push", "pull_request"}

# Guards that are MEANT to be typed by a person. Each needs a reason, because
# "it's fine, it's manual" is the sentence that hid the other three.
EXEMPT: dict[str, str] = {
    "audit_unpushed": (
        "collar check for a session's own commits; the night/morning SKILL.md "
        "run it at 收工. Automating it would need a session, not a workflow."
    ),
    "audit_mutation_sweep": (
        "development instrument -- measures how many mutants the suite kills. "
        "Minutes to hours per run; belongs in a research window, not a cron."
    ),
    "audit_metric_names": (
        "naming-collision check at the moment a new field is PROPOSED, not an "
        "invariant on data the pipeline produces every night -- there is no "
        "cron trigger for 'someone is about to name a field after a standard "
        "it doesn't match'. Meant to be typed before adding a row to "
        "data/reference/METRIC_SOURCES.md's 登记表, the same manual cadence "
        "as audit_unpushed at 收工 (Andy 2026-09-06 「撞名立机制」)."
    ),
}

# Known-unwired baseline. (owner, found_on, why_it_matters)
KNOWN_UNWIRED: dict[str, tuple[str, str, str]] = {
    "audit_calendar_gaps": (
        "DATA ALEX", "2026-09-03",
        "its docstring was written FOR the 2026-08-28 miss and it has never "
        "run automatically; independently measured 2026-09-03: that session's "
        "yfinance daily gave 38 of 283 tickers (13.4%)",
    ),
    "audit_universe_shape": (
        "DATA ALEX", "2026-09-03",
        "the only guard that survives a source cut in half along a CONTENT "
        "dimension -- the 2026-06-26 shape, 21 sessions, 17.9% of the archive",
    ),
    "audit_regression_gate": (
        "DATA ALEX", "2026-09-03",
        "no_downgrade imports STATUS_RANK from it, which is a table, not a "
        "call; the gate itself has never been invoked automatically",
    ),
    # Declared by its own author on the night it was written, which is the
    # shape of `pitfall_i_changed_the_rule_to_fit_what_i_did` and is said out
    # loud here for that reason. What makes it legitimate is that nothing was
    # changed to accommodate it: this is the channel this table exists for,
    # the entry names an owner outside the author's lane, and W2 deletes the
    # excuse the moment somebody wires it. Wiring is three lines next to the
    # `audit_wiring (reported)` step in tests.yml -- a file the night shift
    # cannot merge.
    "audit_ci_test_coverage": (
        "DATA ALEX / whoever owns .github/workflows", "2026-09-05",
        "it is the only reader of what the wired pytest run leaves out: 614 "
        "of the repository's test functions, including a second test root "
        "(tests/, 607) that has been carrying a red test since 2026-08-27",
    ),
}

SKIP_DIRS = {".venv", "venv", ".git", ".claude", "node_modules", "__pycache__",
             "frontend", "data"}


# ---------- workflows ----------

def _run_blocks_regex(text: str) -> list[str]:
    """`run:` bodies, found without a YAML parser. Both step forms.

    A regex gets this wrong in both directions and we have been bitten by
    each, in the same afternoon:

    * UNDER-reads -- `^\\s*run:` cannot see the compact `- run: |` form,
      because a step written without a `name:` puts `- ` in front. A guard
      wired that way was reported UNWIRED.
    * OVER-reads -- a continuation of `(?:\\s+.*\\n)+` swallows blank lines
      and every following step to EOF, since in YAML each of those lines is
      indented. Text that is not a command counted as one.

    And the two were entangled: every `run:` in `daily-data-update.yml` is the
    INLINE form, `run: python -m pipeline.tools.audit_archives ...`, which the
    old head pattern never matched. Those calls were being found only because
    the over-read swallowed them out of a later part of the file. Fixing the
    over-read alone made the real repository's two wired guards vanish. One
    bug was covering for the other.

    So handle both forms deliberately:
      inline        `run: cmd`      -> the rest of that line
      block scalar  `run: |`        -> the lines indented STRICTLY deeper,
                                       blank lines kept only when a deeper
                                       line follows
    """
    out: list[str] = []
    lines = text.splitlines()
    block = re.compile(r"^(\s*)(?:-\s+)?run:\s*[|>][-+]?\s*$")
    inline = re.compile(r"^\s*(?:-\s+)?run:[ \t]+(\S.*)$")
    for i, line in enumerate(lines):
        m = block.match(line)
        if m:
            indent = len(m.group(1))
            body, pending = [], []
            for nxt in lines[i + 1:]:
                if not nxt.strip():             # blank: keep only if more follows
                    pending.append(nxt)
                    continue
                if len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                body.extend(pending); pending = []
                body.append(nxt)
            if body:
                out.append("\n".join(body) + "\n")
            continue
        m = inline.match(line)
        if m:
            out.append(m.group(1) + "\n")
    return out


def _run_blocks(text: str) -> list[str]:
    """Every `run:` body in a workflow, comment lines stripped."""
    try:
        import yaml
        doc = yaml.safe_load(text)
    except Exception:
        doc = None
    blocks: list[str] = []
    if isinstance(doc, dict):
        for job in (doc.get("jobs") or {}).values():
            if not isinstance(job, dict):
                continue
            for step in job.get("steps") or []:
                if isinstance(step, dict) and isinstance(step.get("run"), str):
                    blocks.append(step["run"])
    else:
        # Fallback for environments without PyYAML -- which is the LOCAL one,
        # so this branch is what the tests actually exercise. It missed the
        # compact list-item form `- run: |` until 2026-09-04: the old pattern
        # required `run:` to be preceded by whitespace only, and a step
        # written without a `name:` puts `- ` in front of it. A guard wired
        # that way read as UNWIRED, which is the one direction that hurts --
        # an auditor that under-reports says nothing is wrong.
        blocks = _run_blocks_regex(text)
    out = []
    for b in blocks:
        out.append("\n".join(ln for ln in b.splitlines()
                             if not ln.lstrip().startswith("#")))
    return out


def _triggers(text: str) -> set[str]:
    try:
        import yaml
        doc = yaml.safe_load(text)
    except Exception:
        doc = None
    if isinstance(doc, dict):
        # PyYAML parses the bare key `on:` as the boolean True.
        on = doc.get("on", doc.get(True))
        if isinstance(on, dict):
            return set(on)
        if isinstance(on, list):
            return set(on)
        if isinstance(on, str):
            return {on}
    return set(re.findall(r"^\s{2}(schedule|push|pull_request|workflow_dispatch):",
                          text, re.MULTILINE))


def ci_invocations(workflows: Path) -> dict[str, list[str]]:
    """module -> workflows that actually run it on an automatic trigger."""
    found: dict[str, list[str]] = {}
    if not workflows.is_dir():
        return found
    for wf in sorted(workflows.glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8", errors="replace")
        if not (_triggers(text) & AUTOMATIC_TRIGGERS):
            continue
        body = "\n".join(_run_blocks(text))
        for m in re.finditer(r"pipeline[./]tools[./](audit_\w+)", body):
            found.setdefault(m.group(1), []).append(wf.name)
    return found


# ---------- production python ----------

def _called_names(tree: ast.AST) -> tuple[set[str], set[str]]:
    """(names called directly, root names of attribute calls).

    The split is the whole point. `STATUS_RANK.get(x)` is an attribute call
    whose ROOT is `STATUS_RANK` -- counting that root as "called" would report
    a dict lookup as an invocation of the module it came from, which is the
    exact false positive this file exists to avoid. So a name imported by
    `from X import NAME` only counts when it appears as `NAME(...)`, while a
    module imported by `import X as m` counts on `m.anything(...)`.
    """
    direct: set[str] = set()
    attr_root: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                direct.add(f.id)
            elif isinstance(f, ast.Attribute):
                v = f.value
                while isinstance(v, ast.Attribute):
                    v = v.value
                if isinstance(v, ast.Name):
                    attr_root.add(v.id)
    return direct, attr_root


def _docstrings(tree: ast.AST) -> set[int]:
    """id() of Constant nodes that are docstrings, so we don't read prose."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                out.add(id(body[0].value))
    return out


def prod_invocations(root: Path) -> dict[str, list[str]]:
    """module -> production files that CALL something imported from it."""
    found: dict[str, list[str]] = {}
    for py in sorted(root.rglob("*.py")):
        rel = py.relative_to(root)
        if set(rel.parts) & SKIP_DIRS or "tests" in rel.parts:
            continue
        if rel.parts[:2] == ("pipeline", "tools"):
            continue                          # a tool citing a tool is not a run
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        direct, attr_root = _called_names(tree)
        docs = _docstrings(tree)
        for node in ast.walk(tree):
            mod, hit = None, False
            if isinstance(node, ast.ImportFrom) and node.module \
                    and node.module.startswith("pipeline.tools.audit_"):
                mod = node.module.rsplit(".", 1)[1]
                hit = any((a.asname or a.name) in direct for a in node.names)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("pipeline.tools.audit_"):
                        mod = a.name.rsplit(".", 1)[1]
                        hit = (a.asname or mod) in attr_root
            if mod and hit:
                found.setdefault(mod, []).append(str(rel))
            # subprocess-style: a non-docstring literal naming the module
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and id(node) not in docs:
                for m in re.finditer(r"pipeline[./]tools[./](audit_\w+)",
                                     node.value):
                    found.setdefault(m.group(1), []).append(str(rel))
    return {k: sorted(set(v)) for k, v in found.items()}


def tests_have_ci(workflows: Path) -> bool:
    if not workflows.is_dir():
        return False
    for wf in workflows.glob("*.y*ml"):
        text = wf.read_text(encoding="utf-8", errors="replace")
        if not (_triggers(text) & AUTOMATIC_TRIGGERS):
            continue
        if re.search(r"\bpytest\b", "\n".join(_run_blocks(text))):
            return True
    return False


# ---------- the check ----------

def collect(root: Path) -> dict:
    guards = sorted(p.stem for p in root.glob(GUARD_GLOB))
    wf = root / ".github" / "workflows"
    return {"guards": guards, "ci": ci_invocations(wf),
            "prod": prod_invocations(root), "tests_have_ci": tests_have_ci(wf)}


def check(guards, ci, prod, exempt=None, known=None) -> dict:
    exempt = EXEMPT if exempt is None else exempt
    known = KNOWN_UNWIRED if known is None else known

    status, violations, warnings = {}, [], []
    for g in guards:
        if g in ci:
            status[g] = ("ci", ", ".join(sorted(set(ci[g]))))
        elif g in prod:
            status[g] = ("prod", ", ".join(prod[g]))
        elif g in exempt:
            status[g] = ("exempt", exempt[g])
        elif g in known:
            status[g] = ("known-unwired", known[g][0])
        else:
            status[g] = ("UNWIRED", "")
            violations.append(
                f"W1 {g}: a guard with no automatic trigger, no exemption and "
                f"no entry in KNOWN_UNWIRED. Either wire it, or declare it "
                f"with an owner and a reason.")

    for g, meta in known.items():
        if g not in guards:
            violations.append(f"W3 {g}: listed in KNOWN_UNWIRED but no such module")
        elif g in ci or g in prod:
            violations.append(
                f"W2 {g}: now wired ({status[g][0]}: {status[g][1]}) but still "
                f"listed in KNOWN_UNWIRED -- delete the entry.")
        if len(meta) != 3 or not meta[0] or not meta[2]:
            violations.append(f"W4 {g}: KNOWN_UNWIRED entry needs owner and reason")

    for g, why in exempt.items():
        if g not in guards:
            violations.append(f"W3 {g}: listed in EXEMPT but no such module")
        elif not why.strip():
            violations.append(f"W4 {g}: EXEMPT entry needs a reason")

    for g, meta in known.items():
        if g in guards and g not in ci and g not in prod:
            warnings.append(f"{g} -- unwired since {meta[1]}, owner {meta[0]}: {meta[2]}")

    return {"ok": not violations, "status": status,
            "violations": violations, "warnings": warnings,
            "guards": len(guards),
            "wired": sum(1 for v in status.values() if v[0] in ("ci", "prod"))}



def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="repo root")
    ap.add_argument("--json", help="write the full result here")
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    facts = collect(root)
    out = check(facts["guards"], facts["ci"], facts["prod"])
    out["tests_have_ci"] = facts["tests_have_ci"]

    if not a.quiet:
        print(f"{out['guards']} guards under {GUARD_GLOB}, "
              f"{out['wired']} with an automatic trigger\n")
        for g, (kind, detail) in sorted(out["status"].items()):
            mark = {"ci": "OK  ", "prod": "OK  ", "exempt": "manual",
                    "known-unwired": "⏰  ", "UNWIRED": "BAD "}[kind]
            print(f"{mark} {g:<26} {kind:<14} {detail[:70]}")
        print()
        if not facts["tests_have_ci"]:
            print("⏰   the test suite itself has no automatic trigger: no "
                  "workflow with a schedule/push/pull_request trigger runs "
                  "pytest. Wiring assertions live in tests, so they only run "
                  "when a human types the command.\n")
        for w in out["warnings"]:
            print(f"WARN {w}")
    for v in out["violations"]:
        print(f"BAD  {v}")
    print(f"\n{'OK' if out['ok'] else 'VIOLATIONS'}: {len(out['violations'])} "
          f"violations, {len(out['warnings'])} known-unwired")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
