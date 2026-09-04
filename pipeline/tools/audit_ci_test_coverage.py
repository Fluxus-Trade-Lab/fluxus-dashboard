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
        "tests.yml runs `pytest pipeline/tests` only; this root's 608 tests "
        "have no automatic trigger and one of them is red since 2026-08-27",
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
    "--durations", "--strict-markers", "-x", "--co", "--collect-only",
}
# Options that CHANGE which tests run and that we model explicitly.
_SELECTING = {"-m"}
# Options that change which tests run and that we do NOT model -> T5.
_UNMODELLED_SELECTORS = {"-k", "--ignore", "--deselect", "--ignore-glob",
                         "--last-failed", "--lf", "--failed-first", "--ff",
                         "--new-first", "--nf"}


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
        for nxt in lines[i + 1:i + 8]:
            if re.match(r"^\s*-\s", nxt):        # next step began
                break
            m = re.match(r"^\s*fetch-depth:\s*(\d+)", nxt)
            if m:
                depth = int(m.group(1))
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
        for block in _run_blocks(text):
            for line in block.splitlines():
                if not re.search(r"\bpytest\b", line):
                    continue
                rest = _invocation(line.strip())
                if rest is None:
                    continue
                targets, markers, unmodelled = parse_pytest_args(rest)
                steps.append({"workflow": wf.name, "command": line.strip(),
                              "depth": depth, "targets": targets,
                              "markers": markers, "unmodelled": unmodelled})
    return steps


# ---------- the suite side ----------

_HISTORY_HINTS = ("cat-file", "_has(", "shallow")


def _decorator_markers(fn: ast.AST, src: str) -> tuple[set[str], bool]:
    """(marker names, does a skipif depend on repository history)."""
    names: set[str] = set()
    history = False
    for dec in getattr(fn, "decorator_list", []):
        seg = ast.get_source_segment(src, dec) or ""
        node = dec.func if isinstance(dec, ast.Call) else dec
        attr = []
        while isinstance(node, ast.Attribute):
            attr.append(node.attr)
            node = node.value
        attr.reverse()
        if attr[:1] == ["mark"]:
            if len(attr) > 1 and attr[1] not in ("skipif", "skip", "xfail",
                                                 "parametrize", "usefixtures"):
                names.add(attr[1])
            if len(attr) > 1 and attr[1] == "skipif" and \
                    any(h in seg for h in _HISTORY_HINTS):
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
                if isinstance(node, ast.Assign) and any(
                        isinstance(t, ast.Name) and t.id == "pytestmark"
                        for t in node.targets):
                    seg = ast.get_source_segment(src, node) or ""
                    module_markers |= set(re.findall(r"mark\.(\w+)", seg))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith("test"):
                    continue
                marks, history = _decorator_markers(node, src)
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
          declared: Optional[dict] = None) -> dict:
    declared = DECLARED if declared is None else declared
    buckets = excluded_tests(tests, steps)
    v: list[tuple[str, str]] = []

    if not steps:
        v.append(("T6", "no automatically triggered workflow runs pytest"))

    for s in steps:
        for opt in s["unmodelled"]:
            v.append(("T5", f"{s['workflow']}: pytest option {opt} is not "
                            f"modelled -- refusing to report coverage"))

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
        elif key != "shallow-checkout" and not (ROOT / key).exists():
            v.append(("T3", f"declared path {key!r} does not exist"))

    return {"steps": steps, "buckets": buckets, "declared": declared,
            "violations": v, "total": len(tests)}


def render(res: dict) -> str:
    L = ["CI test coverage -- what the automatic trigger actually executes", ""]
    if not res["steps"]:
        L.append("  (no automatically triggered workflow runs pytest)")
    for s in res["steps"]:
        depth = "no checkout" if s["depth"] is None else (
            "full history" if s["depth"] == 0 else f"depth {s['depth']} (shallow)")
        L.append(f"  {s['workflow']}: {s['command']}")
        L.append(f"      checkout: {depth}"
                 + (f" | -m excludes {sorted(s['markers'])}" if s["markers"] else ""))
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
    res = check(tests, steps)
    print(render(res))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
