"""CI test coverage -- the suite is wired, but what does the wired run RUN?

`audit_wiring` asks whether a guard is called at all, and for the test suite it
answers with a bool: `tests_have_ci()` is True as soon as one automatically
triggered workflow mentions `pytest`. That bool went True on 2026-09-04 and the
gap it was written to close was declared closed.

It is not closed. A bool cannot see which tests the invocation leaves out, and
the invocation that made it True leaves out a lot:

  * `pytest pipeline/tests` -- the repository has a SECOND test root, `tests/`,
    with 608 collected tests. None of them has an automatic trigger. On
    2026-09-05 one of them was RED and had been red for nine days:
    `tests/test_no_naive_clock.py::test_no_bare_naive_clock_in_trading_code`
    went red at 6f66f5f9 (2026-08-27 16:18 JST, federation_board v0 landing
    three bare `datetime.now()/date.today()` calls in trading code) and is red
    at origin/main today. Green at its parent 494f4689, red at the child --
    bisected, not inferred.
  * `-m "not slow"` deselects 3, one of which is `test_run_all_end_to_end`,
    the end-to-end smoke DATA_RELIABILITY §六.0 credits with catching three
    real bugs on its first run.
  * `actions/checkout@v4` with no `fetch-depth` is a depth-1 clone, and four
    tests in `test_audit_regression_gate.py` skip on exactly that condition.
    Those four are the only ones that replay a REAL incident (the 08-27
    overwrite) against its measured numbers. Verified by cloning `--depth 1`
    and running them: 4 skipped, reason "shallow checkout".

    So the checks that pin our worst data incident do not execute in the run
    whose green we read, and the run says so in a line nobody reads:
    "1327 passed, 4 skipped, 3 deselected" -- and exits 0.

⚠️ Why this is a RATCHET, not an alarm -- same reasoning as `audit_wiring`.

Everything above needs edits to `.github/workflows/tests.yml`, which belongs to
no lane that can merge it tonight. An audit that simply went red on today's
state would be red for as long as that takes, and a permanently red check is a
check people learn to skip. So today's exclusions are DECLARED below with an
owner, a reason and the date they were found, and the audit is green on exactly
that set. Declared entries are IOUs. They are printed in full on every run.

It goes RED when the situation CHANGES:

  T1  a test root, marker or option excludes tests and is not declared
      -- a NEW blind spot, i.e. today's shape happening again
  T2  a declared entry is no longer excluded -- fixing it forces you to
      delete the excuse (the anti-rot half; without it this table becomes a
      permanent allowlist that describes a repository we no longer have)
  T3  a declared entry names a path or marker that no longer exists
  T4  a declared entry carries no owner or no reason
  T5  the pytest invocation uses an option this parser does not model
      -- refuse to report a green we cannot justify. An auditor that
      under-reads says nothing is wrong, which is the one direction that
      hurts (`audit_wiring._run_blocks_regex` learned this the same way)
  T6  no automatically triggered workflow runs pytest at all

⚠️ What this tool does NOT do: it does not run pytest. It reads the workflow
and the test sources. That is deliberate -- a tool that had to execute the
suite to report on it could not run inside the suite, and the number it would
report would be the number from THIS machine, not from the runner.

⚠️ KNOWN BLIND SPOTS -- read this before believing a green.

The first version of this file said "it goes RED when the situation CHANGES".
An adversarial review took that sentence apart the same night: five different
edits changed the situation and it stayed green. What it actually watches is
**the literal shape of the pytest command line**, and everything that moves an
exclusion off that line used to be invisible. Four of those are now CAVEATS --
the audit refuses to certify a run it cannot read, and says so at the top of
the report instead of quietly printing a number:

  * `if:` on the pytest step or its job -- `if: false` ran zero tests and the
    first version reported no violations at all
  * an argument built at runtime (`pytest $PYTEST_ARGS`) -- `$PYTEST_ARGS` was
    read as a target PATH, so a `--ignore=` inside it vanished completely
  * `paths:` / `branches:` filters on the trigger -- `_triggers` reads the key
    names, never the filters, so a workflow that only fires on `frontend/**`
    counted as full coverage
  * `--collect-only` -- it collects and runs nothing. This one was the worst:
    a step `pytest tests --collect-only` emptied the `tests` bucket, and the
    audit then printed T2, "declared exclusion 'tests' excludes nothing now --
    delete the entry". **The tool instructed a human into a false green.**

Still outside the射程, and said here rather than discovered later:

  * **runtime skips.** `pytest.skip()` inside a function body and
    `importorskip` are invisible to an ast pass over decorators. This
    repository has 8 such sites today (test_audit_ledger 370/381,
    test_backstop_gate 124, test_audit_archives 388,
    test_federation_board_lane 191, tests/profile/test_facilitation 154, and
    test_audit_wiring's importorskip). They are a different question -- a test
    excusing ITSELF, not a workflow excluding it -- but the count printed by
    this tool does not include them, and "614 tests no automatic run executes"
    means 614 **statically visible** exclusions.
  * `continue-on-error` / `|| true`. Those tests DO run; they just cannot make
    the job red. Out of射程 by definition, and named because "the green we
    read" has two halves and this file only audits one.
  * reusable workflows (`uses: ./.github/workflows/x.yml`) and composite
    actions. None in this repository today; if one appears, its pytest call is
    invisible here.
"""

from __future__ import annotations

import argparse
import ast
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable, Optional

from pipeline.tools.audit_wiring import AUTOMATIC_TRIGGERS, _run_blocks, _triggers

ROOT = Path(__file__).resolve().parents[2]

# Directories that hold pytest modules. `scripts/` is left out ON PURPOSE and
# said out loud rather than filtered silently: `scripts/test_conditional_claim.py`
# is a command-line tool whose name starts with `test_`, not a test module.
TEST_ROOTS = ("pipeline/tests", "tests")

# path/marker -> (owner, reason, date found). Delete an entry when it is fixed;
# T2 makes that mandatory rather than polite.
DECLARED: dict[str, tuple[str, str, str]] = {
    "tests": (
        "DATA ALEX / whoever owns .github/workflows",
        "tests.yml runs `pytest pipeline/tests` only; this root has no "
        "automatic trigger at all and one of its tests is red since "
        "2026-08-27 (counts here are ast test functions; pytest collects "
        "608 in this root and cannot collect tests/gex at all)",
        "2026-09-05",
    ),
    "marker:slow": (
        "DATA ALEX / whoever owns .github/workflows",
        "`-m \"not slow\"` drops 3, including test_run_all_end_to_end -- the "
        "one smoke test DATA_RELIABILITY §六.0 credits with three real bugs",
        "2026-09-05",
    ),
    "shallow-checkout": (
        "DATA ALEX / whoever owns .github/workflows",
        "actions/checkout with no fetch-depth is depth 1; the 4 tests that "
        "replay the 08-27 overwrite against its real numbers skip there",
        "2026-09-05",
    ),
}

# Options we model. Anything else in a pytest command trips T5.
_MODELLED = {
    "-q", "--quiet", "-v", "--tb", "--tb=short", "--tb=line", "--tb=long",
    "--tb=no", "-m", "-p", "--color", "-rs", "-ra", "--maxfail",
    "--durations", "--strict-markers", "-x",
}

# Trigger keys that narrow WHEN a workflow fires. `_triggers` reads key names
# only, so a workflow that fires solely on `paths: ['frontend/**']` looked like
# unconditional coverage.
_TRIGGER_FILTERS = ("paths:", "paths-ignore:", "branches:", "branches-ignore:",
                    "tags:", "tags-ignore:")
# Options that CHANGE which tests run and that we model explicitly.
_SELECTING = {"-m"}
# Options that change which tests run and that we do NOT model -> T5.
_UNMODELLED_SELECTORS = {"-k", "--ignore", "--deselect", "--ignore-glob",
                         "--last-failed", "--lf", "--failed-first", "--ff",
                         "--new-first", "--nf", "--collect-only", "--co"}
# `--collect-only` is listed above and NOT in _MODELLED on purpose: it is the
# one option that looks like a test run and executes nothing. Modelling it as
# harmless let a `pytest tests --collect-only` step empty the `tests` bucket,
# after which the audit printed T2 and told a human to delete the IOU. The
# tool instructed a person into a false green.


# ---------- the workflow side ----------

def checkout_depth(text: str) -> Optional[int]:
    """Shallowest `fetch-depth` among this workflow's checkout steps.

    Returns None when the workflow checks nothing out. `actions/checkout`
    defaults to a depth-1 clone, so an absent `fetch-depth` is 1, not "full" --
    reading the absence as "unspecified, probably fine" is how four tests came
    to skip in a green job.
    """
    depths: list[int] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "actions/checkout" not in line:
            continue
        depth = 1
        # Scan to the NEXT STEP, not a fixed number of lines. The first version
        # stopped after 7, and `repository/ref/token/path/clean/submodules` is
        # six keys -- enough to push `fetch-depth: 0` out of the window and
        # report a full checkout as shallow.
        for nxt in lines[i + 1:]:
            if re.match(r"^\s*-\s", nxt):        # next step began
                break
            if nxt.strip() and not nxt.startswith(" "):
                break                             # left the block entirely
            m = re.match(r"""^\s*fetch-depth:\s*['"]?(\d+)['"]?\s*(?:#.*)?$""", nxt)
            if m:
                depth = int(m.group(1))
                break
            if re.match(r"^\s*fetch-depth:\s*\$\{\{", nxt):
                depth = 1        # a runtime expression: assume the shallow default
                break
        depths.append(depth)
    if not depths:
        return None
    shallow = [d for d in depths if d != 0]
    # A workflow can check out more than once. We report the SHALLOWEST, which
    # over-reports when the pytest job is the one with full history -- the safe
    # direction. An auditor that over-reports makes noise; one that
    # under-reports says nothing is wrong.
    return min(shallow) if shallow else 0


def _marker_expr(tokens: list[str]) -> Optional[str]:
    for i, t in enumerate(tokens):
        if t == "-m" and i + 1 < len(tokens):
            return tokens[i + 1]
        if t.startswith("-m") and len(t) > 2:
            return t[2:]
    return None


def negated_markers(expr: str) -> tuple[set[str], bool]:
    """Markers a `-m` expression excludes, and whether we fully understood it.

    Only `not NAME` and conjunctions of it are modelled. Everything else
    returns understood=False and the caller must go red (T5) rather than
    report an exclusion set it cannot stand behind.
    """
    parts = [p.strip() for p in re.split(r"\band\b", expr)]
    out: set[str] = set()
    for p in parts:
        m = re.fullmatch(r"not\s+([A-Za-z_]\w*)", p)
        if not m:
            return out, False
        out.add(m.group(1))
    return out, bool(parts)


def _invocation(line: str) -> Optional[list[str]]:
    """Tokens AFTER the pytest command, or None if this line does not run it.

    `\bpytest\b` alone is not an invocation: `pip install pytest PyYAML` in the
    same workflow matches it, and reading that line as a test run gave the
    first draft of this tool a `-m pytest` marker expression it could not
    parse. Naming a program is not running it -- the same mistake
    `audit_wiring` documents for `grep audit_archives`, one layer up.
    """
    try:
        tokens = shlex.split(line)
    except ValueError:
        return None
    while tokens and re.fullmatch(r"[A-Za-z_]\w*=.*", tokens[0]):
        tokens.pop(0)                     # leading FOO=bar env assignments
    if not tokens:
        return None
    if tokens[0] in ("pytest", "py.test"):
        return tokens[1:]
    if tokens[0] in ("python", "python3") and tokens[1:3] == ["-m", "pytest"]:
        return tokens[3:]
    return None


def parse_pytest_args(rest: list[str]) -> tuple[list[str], set[str], list[str]]:
    """(target paths, markers the run excludes, options we cannot model)."""
    targets: list[str] = []
    unmodelled: list[str] = []
    marker_expr: Optional[str] = None
    skip_next = False
    for i, t in enumerate(rest):
        if skip_next:
            skip_next = False
            continue
        if not t.startswith("-"):
            targets.append(t)
            continue
        head, _, inline = t.partition("=")
        if head == "-m" or (t.startswith("-m") and len(t) > 2 and not inline):
            marker_expr = t[2:] if len(t) > 2 else (rest[i + 1] if i + 1 < len(rest) else "")
            skip_next = len(t) == 2
            continue
        if head in _UNMODELLED_SELECTORS:
            unmodelled.append(t)
            if not inline and head in ("-k", "--deselect", "--ignore",
                                       "--ignore-glob"):
                skip_next = True
            continue
        if head in _MODELLED or t in _MODELLED:
            if not inline and head in ("-p", "--tb", "--maxfail",
                                       "--durations", "--color"):
                skip_next = True
            continue
        unmodelled.append(t)
    markers: set[str] = set()
    if marker_expr is not None:
        markers, understood = negated_markers(marker_expr)
        if not understood:
            unmodelled.append(f"-m {marker_expr!r}")
    return targets, markers, unmodelled


def conditional_run_blocks(text: str) -> set[str]:
    """`run:` bodies whose step -- or whose job -- carries an `if:`.

    A step that does not execute excludes every test in it, and no amount of
    reading the command line shows that. `if: false` on the pytest step made
    the first version of this audit report a clean bill of health for a run
    that executed nothing.

    Steps are list items; a job's own keys sit at a shallower indent than its
    step items. So: split on step boundaries, and call an `if:` shallower than
    the first step item a JOB-level condition, which taints every step under
    it. `if: always()` on an unrelated step must NOT taint the pytest step --
    this repository has exactly that, and an audit that cried wolf about it
    would be ignored within a week.
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if re.match(r"^\s*-\s", ln)]
    if not starts:
        return set()
    step_indent = min(len(lines[i]) - len(lines[i].lstrip()) for i in starts)
    job_if = any(re.match(r"^\s*if:\s*\S", ln) and
                 (len(ln) - len(ln.lstrip())) < step_indent for ln in lines)
    tainted: set[str] = set()
    bounds = starts + [len(lines)]
    for a, b in zip(bounds, bounds[1:]):
        chunk = lines[a:b]
        if not any(re.search(r"\brun:", ln) for ln in chunk):
            continue
        if job_if or any(re.match(r"^\s*if:\s*\S", ln) for ln in chunk):
            for ln in chunk:
                t = ln.strip()
                if t and not t.startswith("#"):
                    tainted.add(t)
    return tainted


def trigger_filters(text: str) -> list[str]:
    """`paths:` / `branches:` style narrowing on the trigger block.

    `_triggers` reads key names and never the filters under them, so a
    workflow firing only on `paths: ['frontend/**']` read as full coverage.
    """
    out, in_on = [], False
    for ln in text.splitlines():
        if re.match(r"^\s*(on|True):\s*$", ln) or re.match(r"^on:\s*$", ln):
            in_on = True
            continue
        if in_on and ln.strip() and not ln.startswith(" "):
            in_on = False
        if in_on:
            for k in _TRIGGER_FILTERS:
                if ln.strip().startswith(k):
                    out.append(ln.strip())
    return out


def pytest_steps(workflows: Path) -> list[dict]:
    """Every pytest invocation that some automatic trigger will actually run."""
    steps: list[dict] = []
    if not workflows.is_dir():
        return steps
    for wf in sorted(workflows.glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8", errors="replace")
        if not (_triggers(text) & AUTOMATIC_TRIGGERS):
            continue
        depth = checkout_depth(text)
        conditional = conditional_run_blocks(text)
        filters = trigger_filters(text)
        for block in _run_blocks(text):
            for line in block.splitlines():
                if not re.search(r"\b(?:py\.test|pytest)\b", line):
                    continue
                rest = _invocation(line.strip())
                if rest is None:
                    continue
                targets, markers, unmodelled = parse_pytest_args(rest)
                caveats: list[str] = []
                if line.strip() in conditional:
                    caveats.append("the step or its job carries an `if:` -- "
                                   "it may execute nothing")
                for t in targets + list(unmodelled):
                    if "$" in t:
                        caveats.append(f"argument {t!r} is built at runtime -- "
                                       f"what it hides cannot be read here")
                for f in filters:
                    caveats.append(f"trigger is narrowed by {f!r} -- it may "
                                   f"never fire for a change to these tests")
                steps.append({"workflow": wf.name, "command": line.strip(),
                              "depth": depth, "targets": targets,
                              "markers": markers, "unmodelled": unmodelled,
                              "caveats": caveats})
    return steps


# ---------- the suite side ----------

# A skipif whose condition reaches for the repository or the environment.
# The first version matched three literal strings, so
# `skipif(shutil.which("git") is None)` read as unconditional -- a keyword
# guess dressed as a rule. `subprocess`/`git`/`run(` widen it to "this
# condition asks the machine something", which is the property that matters.
_HISTORY_HINTS = ("cat-file", "_has(", "shallow", "subprocess", "git",
                  "rev-parse", "which(")


_NOT_A_MARKER = {"skipif", "skip", "xfail", "parametrize", "usefixtures"}


def _decorator_markers(fn: ast.AST, src: str) -> tuple[set[str], bool]:
    """(marker names, does a skipif ask the machine a question).

    Matches on the TRAILING `.mark.<name>` rather than requiring the chain to
    begin with `mark`. `from pytest import mark` + `@mark.slow` was invisible
    to the first version, and invisible in the direction that hurts: a test
    deselected by `-m "not slow"` read as one that runs.
    """
    names: set[str] = set()
    history = False
    for dec in getattr(fn, "decorator_list", []):
        seg = ast.get_source_segment(src, dec) or ""
        node = dec.func if isinstance(dec, ast.Call) else dec
        attr = []
        while isinstance(node, ast.Attribute):
            attr.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            attr.append(node.id)
        attr.reverse()
        if "mark" not in attr:
            continue
        i = attr.index("mark")
        if i + 1 >= len(attr):
            continue
        name = attr[i + 1]
        if name not in _NOT_A_MARKER:
            names.add(name)
        if name == "skipif" and any(h in seg for h in _HISTORY_HINTS):
            history = True
    return names, history


def suite_tests(root: Path, test_roots: Iterable[str] = TEST_ROOTS) -> list[dict]:
    """Every test function in the repository, with its markers and gates."""
    out: list[dict] = []
    for rel in test_roots:
        base = root / rel
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("test_*.py")):
            src = path.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            module_markers: set[str] = set()
            for node in tree.body:
                is_pm = (isinstance(node, ast.Assign) and any(
                            isinstance(t, ast.Name) and t.id == "pytestmark"
                            for t in node.targets)) or (
                        isinstance(node, ast.AnnAssign) and
                        isinstance(node.target, ast.Name) and
                        node.target.id == "pytestmark")
                if is_pm:
                    seg = ast.get_source_segment(src, node) or ""
                    module_markers |= set(re.findall(r"mark\.(\w+)", seg))
            # A marker on a CLASS reaches every test method inside it.
            class_markers: dict[int, set[str]] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    cm, _ = _decorator_markers(node, src)
                    for sub in ast.walk(node):
                        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            class_markers.setdefault(id(sub), set()).update(cm)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith("test"):
                    continue
                marks, history = _decorator_markers(node, src)
                marks |= class_markers.get(id(node), set())
                out.append({
                    "file": str(path.relative_to(root)),
                    "root": rel,
                    "name": node.name,
                    "line": node.lineno,
                    "markers": marks | module_markers,
                    "history_gated": history,
                })
    return out


# ---------- the comparison ----------

def _covered_by(step: dict, rel_file: str) -> bool:
    if not step["targets"]:
        return True                       # bare `pytest` = the whole tree
    return any(rel_file == t.rstrip("/") or rel_file.startswith(t.rstrip("/") + "/")
               for t in step["targets"])


def excluded_tests(tests: list[dict], steps: list[dict]) -> dict[str, list[dict]]:
    """test -> why no automatic run executes it. Keys are DECLARED keys."""
    buckets: dict[str, list[dict]] = {}
    for t in tests:
        reasons = set()
        runs_somewhere = False
        for s in steps:
            if not _covered_by(s, t["file"]):
                continue
            if t["markers"] & s["markers"]:
                reasons.add("marker:" + sorted(t["markers"] & s["markers"])[0])
                continue
            if t["history_gated"] and (s["depth"] is None or s["depth"] != 0):
                reasons.add("shallow-checkout")
                continue
            runs_somewhere = True
        if runs_somewhere:
            continue
        if not reasons:
            reasons.add(t["root"])        # no step targets this root at all
        for r in reasons:
            buckets.setdefault(r, []).append(t)
    return buckets


def check(tests: list[dict], steps: list[dict],
          declared: Optional[dict] = None, repo: Optional[Path] = None) -> dict:
    declared = DECLARED if declared is None else declared
    repo = ROOT if repo is None else repo
    buckets = excluded_tests(tests, steps)
    v: list[tuple[str, str]] = []

    if not steps:
        v.append(("T6", "no automatically triggered workflow runs pytest"))

    for s in steps:
        for opt in s["unmodelled"]:
            v.append(("T5", f"{s['workflow']}: pytest option {opt} is not "
                            f"modelled -- refusing to report coverage"))
        for c in s.get("caveats", ()):
            v.append(("T5", f"{s['workflow']}: {c}"))

    for key, items in sorted(buckets.items()):
        if key not in declared:
            v.append(("T1", f"{len(items)} test(s) excluded by {key!r}, "
                            f"not declared (e.g. {items[0]['file']}::"
                            f"{items[0]['name']})"))

    for key, entry in sorted(declared.items()):
        if key not in buckets:
            v.append(("T2", f"declared exclusion {key!r} excludes nothing now "
                            f"-- delete the entry"))
        if len(entry) != 3 or not entry[0] or not entry[1]:
            v.append(("T4", f"declared exclusion {key!r} has no owner or reason"))
            continue
        if key.startswith("marker:"):
            marker = key.split(":", 1)[1]
            if not any(marker in t["markers"] for t in tests):
                v.append(("T3", f"declared marker {marker!r} is on no test"))
        elif key != "shallow-checkout" and not (repo / key).exists():
            v.append(("T3", f"declared path {key!r} does not exist"))

    # A T5 does not merely add a line: it means the exclusion set below was
    # computed from a command whose effect we could not read. The first
    # version printed the numbers anyway, which is the opposite of what its
    # own docstring promised ("refuse to report a green we cannot justify").
    certified = not any(code == "T5" for code, _ in v)
    return {"steps": steps, "buckets": buckets, "declared": declared,
            "violations": v, "total": len(tests), "certified": certified}


def render(res: dict) -> str:
    L = ["CI test coverage -- what the automatic trigger actually executes", ""]
    if not res.get("certified", True):
        L += ["⚠️  NOT CERTIFIED -- at least one invocation could not be read "
              "in full (see T5).",
              "    Every count below is a LOWER BOUND on what is excluded.", ""]
    if not res["steps"]:
        L.append("  (no automatically triggered workflow runs pytest)")
    for s in res["steps"]:
        depth = "no checkout" if s["depth"] is None else (
            "full history" if s["depth"] == 0 else f"depth {s['depth']} (shallow)")
        L.append(f"  {s['workflow']}: {s['command']}")
        L.append(f"      checkout: {depth}"
                 + (f" | -m excludes {sorted(s['markers'])}" if s["markers"] else ""))
        for c in s.get("caveats", ()):
            L.append(f"      ⚠️  {c}")
    excluded = sum(len(v) for v in res["buckets"].values())
    L += ["", f"tests in the repository: {res['total']}"
              f"  (test functions, counted by ast -- not pytest's collection"
              f" count, which expands parametrize)",
          f"tests no automatic run executes: {excluded}", ""]
    for key, items in sorted(res["buckets"].items(),
                             key=lambda kv: -len(kv[1])):
        owner, reason, found = res["declared"].get(key, ("?", "?", "?"))
        mark = "declared" if key in res["declared"] else "UNDECLARED"
        L.append(f"  [{mark}] {key}: {len(items)} test(s)")
        L.append(f"      owner: {owner}  (found {found})")
        L.append(f"      why:   {reason}")
        for t in items[:3]:
            L.append(f"      e.g.   {t['file']}::{t['name']}")
        if len(items) > 3:
            L.append(f"      ... and {len(items) - 3} more")
    L += ["", "A declared entry is an IOU, not a resolution.", ""]
    if res["violations"]:
        L.append("VIOLATIONS")
        for code, msg in res["violations"]:
            L.append(f"  {code}  {msg}")
    else:
        L.append("no violations (the declared set is exactly today's set)")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    tests = suite_tests(args.repo)
    steps = pytest_steps(args.repo / ".github" / "workflows")
    res = check(tests, steps, repo=args.repo)
    print(render(res))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
