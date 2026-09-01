"""Audit the audits: when a guard breaks, does its own test go red?

Every guard in this repo is required to carry a positive control -- prove it
reports a true positive before trusting its negative (Growth Gary, 2026-08-25).
That rule is applied by hand, one test at a time. This applies it in bulk:
inject a small semantic change into a guard's source, run only that guard's
tests, and record whether anything noticed.

A mutant that SURVIVES (tests still green) is a hole: on that line, the guard
could be wrong and no test in the repo would say so. It is not automatically a
bug -- some mutants are semantically equivalent, and the report says which ones
were reviewed -- but every survivor is a line the suite does not actually pin.

    python3 -m pipeline.tools.audit_mutation_sweep                 # all audit_*
    python3 -m pipeline.tools.audit_mutation_sweep --module audit_archives
    python3 -m pipeline.tools.audit_mutation_sweep --json out.json
    python3 -m pipeline.tools.audit_mutation_sweep --module audit_x --repeat 3

`--repeat N` exists because this instrument was caught disagreeing with
itself: same commit, same machine, same module, four runs, kill rates
43/47/49/43 (Plumber Joe, 2026-09-01). A rate that wanders 6pp cannot
carry a threshold. With --repeat, a mutant that is green in one trial and
red in another is reported as UNSTABLE and kept OUT of the kill rate --
the instrument says "I do not know" instead of voting at random.

THE REPO IS NEVER WRITTEN TO. Every mutant lives in a throwaway copy of
`pipeline/` under a temp dir (`data/` is symlinked, tests use tmp_path). The
first draft of this tool mutated the real file and restored it in a `finally`,
which held right up until the run was killed on a timeout and left a mutated
`audit_unpushed.py` sitting in the working tree. A cleanup path that only runs
when nothing goes wrong is not a cleanup path.

Exit code is always 0: this is a coverage instrument, not a gate. Turning it
into a gate would require a survivor budget, and we do not have a baseline yet.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "pipeline" / "tools"
TESTS = ROOT / "pipeline" / "tests"

CMP_SWAP = {ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Lt: ast.LtE, ast.LtE: ast.Lt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
            ast.In: ast.NotIn, ast.NotIn: ast.In,
            ast.Is: ast.IsNot, ast.IsNot: ast.Is}
BOOL_SWAP = {ast.And: ast.Or, ast.Or: ast.And}

TEST_TIMEOUT = 300      # seconds per pytest run; a hit is "no verdict", never a kill


def sites(tree):
    """Every place a small semantic change is possible, as (node, kind, how).

    Deliberately conservative: no statement deletion, no return-value swaps.
    Those produce mutants that die for uninteresting reasons (crashes) and
    inflate the kill rate into a number that means nothing."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                if type(op) in CMP_SWAP:
                    out.append((node, "compare", (i, CMP_SWAP[type(op)])))
        elif isinstance(node, ast.BoolOp) and type(node.op) in BOOL_SWAP:
            out.append((node, "boolop", BOOL_SWAP[type(node.op)]))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            out.append((node, "drop_not", None))
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                out.append((node, "bool", not node.value))
            elif isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                out.append((node, "number", node.value + 1))
    return out


def describe(node, kind, how, src_lines):
    line = getattr(node, "lineno", 0)
    text = src_lines[line - 1].strip() if 0 < line <= len(src_lines) else ""
    if kind == "compare":
        what = f"{type(node.ops[how[0]]).__name__} -> {how[1].__name__}"
    elif kind == "boolop":
        what = f"{type(node.op).__name__} -> {how.__name__}"
    elif kind == "drop_not":
        what = "drop `not`"
    else:
        what = f"{node.value!r} -> {how!r}"
    return {"line": line, "kind": kind, "change": what, "source": text[:120]}


def build_mutant(src, index):
    """Re-parse from source each time so mutations never compound."""
    tree = ast.parse(src)
    cands = sites(tree)
    node, kind, how = cands[index]
    if kind == "compare":
        i, new = how
        node.ops[i] = new()
    elif kind == "boolop":
        node.op = how()
    elif kind == "drop_not":
        # replace the UnaryOp in place by copying its operand's fields over it
        inner = copy.deepcopy(node.operand)
        node.__class__ = inner.__class__
        node.__dict__ = inner.__dict__
    else:
        node.value = how
    return ast.unparse(ast.fix_missing_locations(tree))


class Workspace:
    """A throwaway copy of `pipeline/` that mutants are written into.

    `data/` is symlinked rather than copied (174MB, and these tests build
    their fixtures in tmp_path). Nothing here can reach the real tree.

    Tests run under `-B` / PYTHONDONTWRITEBYTECODE, and that is load-bearing.
    CPython validates a cached .pyc by (source mtime truncated to whole
    SECONDS, source size). Consecutive mutants are both `ast.unparse` output
    of the same module, so they differ in size only by the mutation's own
    length delta -- which is ZERO for `20 -> 21`, `0 -> 1`, `==` -> `!=`, and
    for 22 of the 48 adjacent pairs in audit_universe_shape. Written inside
    the same second, mutant N was executed as mutant N-1, and the verdict
    printed against N belonged to N-1.

    That is the 6pp run-to-run wander Plumber Joe measured on 2026-09-01
    (43/47/49/43). It was never flaky tests: with bytecode caching off the
    same module gives 45/45/45 with bit-identical survivor sets, and every
    mutant that had been flipping has a byte delta of exactly 0 from its
    predecessor. Turn the flag off and the instrument starts lying again."""

    def __enter__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="mutsweep-"))
        shutil.copytree(ROOT / "pipeline", self.dir / "pipeline")
        (self.dir / "data").symlink_to(ROOT / "data")
        for name in ("pytest.ini", "setup.cfg", "pyproject.toml", "conftest.py"):
            if (ROOT / name).exists():
                shutil.copy2(ROOT / name, self.dir / name)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def module_path(self, module):
        return self.dir / "pipeline" / "tools" / f"{module}.py"

    def run_tests(self, module):
        """Run the guard's tests once. Returns (green, rc, seconds).

        `green` is tri-state on purpose: True (all passed), False (something
        failed), or None (no verdict -- the run timed out, so we learned
        nothing about whether the suite would have caught this mutant).
        The first version returned a bool and folded timeouts into False,
        which counts "the machine was busy" as "the test caught it"."""
        t0 = time.time()
        try:
            r = subprocess.run(
                [sys.executable, "-B", "-m", "pytest", f"pipeline/tests/test_{module}.py",
                 "-q", "-x", "--no-header", "-p", "no:cacheprovider"],
                cwd=self.dir, capture_output=True, text=True, timeout=TEST_TIMEOUT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        except subprocess.TimeoutExpired:
            return None, None, round(time.time() - t0, 1)
        return r.returncode == 0, r.returncode, round(time.time() - t0, 1)


def sweep(module, verbose=True, repeat=1):
    if not (TESTS / f"test_{module}.py").exists():
        return {"module": module, "error": f"no test file test_{module}.py"}

    src = (TOOLS / f"{module}.py").read_text()
    src_lines = src.splitlines()
    cands = sites(ast.parse(src))

    survivors, unstable, killed, errored, timed_out = [], [], 0, 0, 0
    with Workspace() as ws:
        mod_path = ws.module_path(module)
        if ws.run_tests(module)[0] is not True:
            return {"module": module, "error": "baseline is already red; refusing to sweep"}

        for i in range(len(cands)):
            node, kind, how = sites(ast.parse(src))[i]
            info = describe(node, kind, how, src_lines)
            info["index"] = i          # descriptors are NOT unique; the index is
            try:
                mutant = build_mutant(src, i)
            except Exception:                             # unparse failure
                errored += 1
                continue
            if mutant == ast.unparse(ast.parse(src)):     # semantically a no-op
                errored += 1
                continue
            mod_path.write_text(mutant)
            trials = [ws.run_tests(module) for _ in range(repeat)]
            mod_path.write_text(src)

            greens = [g for g, _, _ in trials]
            info["seconds"] = [sec for _, _, sec in trials]
            if None in greens:                            # at least one timeout
                verdict = "no_verdict"
                timed_out += 1
            elif all(greens):
                verdict = "survived"
                survivors.append(info)
            elif not any(greens):
                verdict = "killed"
                killed += 1
            else:                                         # green here, red there
                verdict = "unstable"
                info["trials"] = greens
                unstable.append(info)
            if verbose:
                print(f"  [{i+1}/{len(cands)}] L{info['line']:<4} {info['change']:<28} "
                      f"{verdict.upper() if verdict != 'killed' else 'killed'}", flush=True)

    # Only mutants with a stable verdict get a vote. An unstable mutant is not
    # 43%-of-a-kill: it is the instrument saying it does not know, and averaging
    # it into the rate is what made the rate wander 6pp between identical runs.
    total = killed + len(survivors)
    return {"module": module, "mutants": total, "killed": killed,
            "survived": len(survivors), "skipped": errored,
            "unstable": len(unstable), "no_verdict": timed_out, "repeat": repeat,
            "kill_rate": round(killed / total, 3) if total else None,
            "survivors": survivors, "unstable_mutants": unstable}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--module", action="append",
                    help="module stem under pipeline/tools (default: every audit_*)")
    ap.add_argument("--json", type=Path, help="write the full report here")
    ap.add_argument("-q", "--quiet", action="store_true")
    ap.add_argument("--repeat", type=int, default=1, metavar="N",
                    help="run each mutant N times; a mutant that is green in one "
                         "trial and red in another is reported as UNSTABLE and "
                         "kept out of the kill rate (default 1)")
    a = ap.parse_args(argv)

    mods = a.module or sorted(p.stem for p in TOOLS.glob("audit_*.py")
                              if p.stem != Path(__file__).stem)
    t0 = time.time()
    report = {"modules": []}
    for m in mods:
        if not a.quiet:
            print(f"\n{m}")
        report["modules"].append(sweep(m, verbose=not a.quiet, repeat=a.repeat))
    report["seconds"] = round(time.time() - t0, 1)

    print("\n" + "=" * 68)
    for r in report["modules"]:
        if r.get("error"):
            print(f"{r['module']:24s} {r['error']}")
            continue
        extra = ""
        if r.get("unstable"):
            extra += f"   ⚠ {r['unstable']} UNSTABLE"
        if r.get("no_verdict"):
            extra += f"   {r['no_verdict']} timed out (no verdict)"
        print(f"{r['module']:24s} {r['killed']:3d}/{r['mutants']:3d} killed "
              f"({r['kill_rate']:.0%})   {r['survived']} survived{extra}")
    if a.json:
        a.json.write_text(json.dumps(report, indent=1))
        print(f"\nreport -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
