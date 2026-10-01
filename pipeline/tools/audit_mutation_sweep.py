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
    python3 -m pipeline.tools.audit_mutation_sweep --module audit_x --list-sites
    python3 -m pipeline.tools.audit_mutation_sweep --module audit_x --index-from 0 --index-to 40

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
        # .github is COPIED, not symlinked: it is small, and a guard's tests
        # reading it must not be able to write through to the real repo. Left
        # out entirely (until 2026-09-21) it made audit_schedule_windows --
        # whose whole job is reading the workflow crons -- report "baseline is
        # already red", which reads as "that guard's tests are broken" when the
        # truth was "this workspace is missing what they read". A sweep that
        # cannot build a green baseline must say what is missing, not accuse
        # the tests.
        if (ROOT / ".github").exists():
            shutil.copytree(ROOT / ".github", self.dir / ".github")
        # `tests/` is the repository's SECOND test root and is copied for the
        # same reason as `.github`, found the same way: on 2026-09-26
        # `audit_ci_test_coverage` -- whose entire subject is that this root
        # exists and CI does not run it -- reported "baseline is already red",
        # and its own T3 ("a declared path no longer exists") was the thing
        # firing, on the path `tests`. The guard was right; the workspace was
        # missing what it reads. Second instance of one shape, so the rule is
        # written here rather than in another one-off branch: anything a guard
        # READS lives outside `pipeline/`, and a workspace that omits it
        # produces a diagnosis pointing at the tests instead of at itself.
        if (ROOT / "tests").exists():
            shutil.copytree(ROOT / "tests", self.dir / "tests")
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


def sweep(module, verbose=True, repeat=1, index_from=0, index_to=None):
    """Sweep mutants [index_from, index_to) of `module`. Defaults to all of them.

    The range exists because a full sweep of every guard is ~1100 pytest runs
    and the slow guards are minutes each, which does not fit in one sitting.
    Slicing lets the sweep be run in chunks and resumed, and the chunks are
    mergeable: `total_sites` is the same in every slice, so a set of slices
    covering [0, total_sites) reconstructs the whole-module numbers exactly.

    Site ordering is `ast.walk` over a freshly parsed tree, so indices are
    stable for a given source -- and only for that source. Edit the guard and
    the slices no longer line up; `total_sites` is in every report so a merge
    across an edit is caught rather than silently mixed."""
    if not (TESTS / f"test_{module}.py").exists():
        return {"module": module, "error": f"no test file test_{module}.py"}

    src = (TOOLS / f"{module}.py").read_text()
    src_lines = src.splitlines()
    cands = sites(ast.parse(src))

    lo = max(0, index_from)
    hi = len(cands) if index_to is None else min(index_to, len(cands))

    survivors, unstable, killed, errored, timed_out = [], [], 0, 0, 0
    with Workspace() as ws:
        mod_path = ws.module_path(module)
        if ws.run_tests(module)[0] is not True:
            return {"module": module, "error": "baseline is already red; refusing to sweep"}

        for i in range(lo, hi):
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
            "total_sites": len(cands), "index_from": lo, "index_to": hi,
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
    ap.add_argument("--index-from", type=int, default=0, metavar="I",
                    help="first mutant index to run (default 0)")
    ap.add_argument("--index-to", type=int, default=None, metavar="J",
                    help="stop before this mutant index; a full sweep is ~1100 "
                         "pytest runs, so run it in slices and merge the reports")
    ap.add_argument("--list-sites", action="store_true",
                    help="print every mutation site with its index and exit, "
                         "without running anything (use it to plan slices)")
    ap.add_argument("--ledger", action="store_true",
                    help=f"file each whole-module result in {LEDGER_REL} so the "
                         "rate has one home and nobody has to quote it out of "
                         "a dated markdown (slices are refused -- see record())")
    ap.add_argument("--show-ledger", action="store_true",
                    help="print the filed rates, lowest-known first, each with "
                         "a FRESH/STALE/UNKNOWN verdict git computed; exit "
                         "without sweeping anything")
    a = ap.parse_args(argv)

    mods = a.module or sorted(p.stem for p in TOOLS.glob("audit_*.py")
                              if p.stem != Path(__file__).stem)
    if a.show_ledger:
        print_ledger(ledger_rows(modules=a.module))
        return 0
    if a.list_sites:
        for m in mods:
            path = TOOLS / f"{m}.py"
            src_lines = path.read_text().splitlines()
            cands = sites(ast.parse(path.read_text()))
            print(f"\n{m}  ({len(cands)} sites)")
            for i, (node, kind, how) in enumerate(cands):
                d = describe(node, kind, how, src_lines)
                print(f"  [{i:4d}] L{d['line']:<4} {d['change']:<28} {d['source'][:60]}")
        return 0

    t0 = time.time()
    report = {"modules": []}
    for m in mods:
        if not a.quiet:
            print(f"\n{m}")
        r = sweep(m, verbose=not a.quiet, repeat=a.repeat,
                  index_from=a.index_from, index_to=a.index_to)
        report["modules"].append(r)
        if a.ledger:
            filed = record(r)
            if filed is None:
                why = r.get("error") or (f"slice {r.get('index_from')}:"
                                         f"{r.get('index_to')} of {r.get('total_sites')}")
                print(f"  not filed: only a whole-module sweep with a rate is a "
                      f"reading ({why})", flush=True)
            else:
                print(f"  filed in {LEDGER_REL}: {filed['killed']}/{filed['mutants']} "
                      f"at {(filed['commit'] or '?')[:9]}", flush=True)

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
        if r.get("index_from") or (r.get("index_to") is not None
                                   and r.get("index_to") != r.get("total_sites")):
            extra += f"   [slice {r['index_from']}:{r['index_to']} of {r['total_sites']}]"
        rate = f"({r['kill_rate']:.0%})" if r["kill_rate"] is not None else "(n/a)"
        print(f"{r['module']:24s} {r['killed']:3d}/{r['mutants']:3d} killed "
              f"{rate}   {r['survived']} survived{extra}")
    if a.json:
        a.json.write_text(json.dumps(report, indent=1))
        print(f"\nreport -> {a.json}")
    return 0



# ---------------------------------------------------------------------------
# The ledger: where a kill rate lives between sweeps.
#
# A full sweep is hours, so a rate is measured once and then quoted for weeks.
# Quoted out of PROSE, which is how every one of these went wrong:
#
#   09-24  the night report quoted `audit_ledger` 42/80 = 53% and
#          `audit_archives` 54/101 = 53%. Both reports were written as
#          "54 -> 57%" (before -> after fixing); the transcription took the
#          number on the LEFT of the arrow. Two numbers, both wrong, and the
#          cost was concrete: it picked the wrong guard to work on that night.
#   09-27  three rates left "recompute before you start": one right, one with
#          both numerator and denominator wrong, one hole already closed.
#   09-28  "audit_universe_shape has 18 survivors nobody has read" -- written
#          on 09-02 and copied forward into every report for three weeks.
#   10-01  "audit_ledger is 52.5%, the 09-02 number, four weeks old" -- it had
#          been 98% since 09-25. That is the sentence that was handed to the
#          10-02 night shift as its first task.
#
# Four instances of one shape, so it gets a mechanism rather than a fifth
# reminder to recompute (三次律). The ledger is the number's only home; prose
# cites it. And the ledger does not ask you to trust its own freshness: a
# reading carries the commit it was taken at, and `--show-ledger` asks git
# whether the guard or its test has moved since.
# ---------------------------------------------------------------------------

LEDGER_REL = Path("data") / "research" / "audit_mutation_ledger.json"
LEDGER_SCHEMA = "audit_mutation_ledger/1"


def ledger_path(root=None):
    """Resolved from ROOT at CALL time, not frozen at import.

    The tests point the sweep at a throwaway tree by monkeypatching ROOT; a
    module-level `LEDGER = ROOT / ...` would keep writing into the real
    repository from inside them."""
    return (root or ROOT) / LEDGER_REL


def _git(args, repo):
    """(returncode, stdout) for a git command. Never raises, never writes."""
    try:
        r = subprocess.run(["git", "-C", str(repo), *args],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None, ""
    return r.returncode, r.stdout


def guard_paths(module):
    """The two files a reading is about: the guard, and the tests that pin it."""
    return [f"pipeline/tools/{module}.py", f"pipeline/tests/test_{module}.py"]


def freshness(entry, module, repo=None, sites_now=None):
    """Is this reading still about the code that is in the tree now?

    Two independent rulers, because each is blind where the other sees:

      * git -- has any commit touched the guard or its test since the reading?
      * the site count -- does the tree still present the same number of
        mutation sites the reading was taken over?

    git is unavailable in a tarball and incomplete in a shallow clone; the site
    count cannot see an edit to the TEST file, which has no mutation sites of
    its own and is half of what decides a kill rate. Neither alone is enough.

    UNKNOWN is load-bearing and is the whole reason this function exists rather
    than a date comparison. `git log <sha>..HEAD` for a sha this clone does not
    have exits non-zero with an EMPTY stdout, and reading that empty output as
    "no commits touched it" reports FRESH for a reading that cannot be placed
    in this history at all. Same shape as grepping a ref that does not exist
    and believing the zero hits.
    """
    repo = repo or ROOT
    sites_then = entry.get("total_sites")

    if sites_now is not None and sites_then is not None and sites_now != sites_then:
        return {"verdict": "STALE", "commits": None,
                "why": f"guard now has {sites_now} mutation sites, "
                       f"the reading was taken over {sites_then}"}

    if entry.get("uncommitted"):
        return {"verdict": "UNKNOWN", "commits": None,
                "why": "reading was taken with uncommitted changes to "
                       + ", ".join(entry["uncommitted"])}

    sha = entry.get("commit")
    if not sha:
        return {"verdict": "UNKNOWN", "commits": None,
                "why": "reading records no commit, so it cannot be placed"}

    rc, _ = _git(["cat-file", "-e", f"{sha}^{{commit}}"], repo)
    if rc != 0:
        return {"verdict": "UNKNOWN", "commits": None,
                "why": f"commit {sha[:9]} is not in this clone's history "
                       "(rebased away, or a shallow checkout)"}

    rc, out = _git(["log", "--oneline", f"{sha}..HEAD", "--", *guard_paths(module)], repo)
    if rc != 0:
        return {"verdict": "UNKNOWN", "commits": None,
                "why": f"git could not compare {sha[:9]}..HEAD"}

    moved = [ln for ln in out.splitlines() if ln.strip()]
    if moved:
        return {"verdict": "STALE", "commits": len(moved),
                "why": f"{len(moved)} commit(s) touched the guard or its test "
                       f"since {sha[:9]}: {moved[0][:60]}"}
    return {"verdict": "FRESH", "commits": 0,
            "why": f"nothing touched the guard or its test since {sha[:9]}"}


def read_ledger(path=None):
    path = path or ledger_path()
    if not path.exists():
        return {"_schema": LEDGER_SCHEMA, "modules": {}}
    data = json.loads(path.read_text())
    data.setdefault("modules", {})
    return data


def record(result, repo=None, path=None, now=None):
    """Put one WHOLE-MODULE reading into the ledger. Returns the entry, or None.

    A SLICE IS NOT A READING. Slices exist because a full sweep does not fit in
    one sitting, and `kill_rate` on a slice is the rate over those indices
    only -- writing it under the module's name would publish `12/13 = 92%` as
    the guard's score. Only `[0, total_sites)` is recorded; partial sweeps are
    refused so the merged numbers have to be assembled before they can be
    filed, which is exactly the step that makes them true."""
    repo = repo or ROOT
    if result.get("error") or result.get("kill_rate") is None:
        return None
    if result.get("index_from") or result.get("index_to") != result.get("total_sites"):
        return None

    module = result["module"]
    _, head = _git(["rev-parse", "HEAD"], repo)
    _, dirty = _git(["status", "--porcelain", "--", *guard_paths(module)], repo)
    entry = {
        "killed": result["killed"],
        "mutants": result["mutants"],
        "survived": result["survived"],
        "unstable": result.get("unstable", 0),
        "kill_rate": result["kill_rate"],
        "total_sites": result["total_sites"],
        "repeat": result.get("repeat", 1),
        "commit": head.strip() or None,
        "uncommitted": sorted(ln[3:].strip() for ln in dirty.splitlines() if ln.strip()),
        "measured_at": now or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    p = path or ledger_path(repo)
    data = read_ledger(p)
    data["modules"][module] = entry
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    return entry


def ledger_rows(repo=None, path=None, modules=None):
    """One row per guard, ordered the way the question is actually asked.

    The question a research shift opens with is "which guard should I work on
    tonight", and the honest answer is not "the lowest number on file" -- a
    guard nobody has measured, or one whose reading no longer describes the
    code, is less known than one sitting at 63%. So the groups come first
    (unmeasured, then unplaceable, then stale, then fresh) and the rate only
    orders within a group."""
    repo = repo or ROOT
    tools = repo / "pipeline" / "tools"
    data = read_ledger(path or ledger_path(repo))
    mods = modules or sorted(p.stem for p in tools.glob("audit_*.py")
                             if p.stem != Path(__file__).stem)
    rank = {"NEVER": 0, "UNKNOWN": 1, "STALE": 2, "FRESH": 3}
    rows = []
    for m in mods:
        entry = data["modules"].get(m)
        if not entry:
            rows.append({"module": m, "verdict": "NEVER", "entry": None,
                         "why": "no reading on file", "kill_rate": None})
            continue
        try:
            sites_now = len(sites(ast.parse((tools / f"{m}.py").read_text())))
        except (OSError, SyntaxError):
            sites_now = None
        f = freshness(entry, m, repo=repo, sites_now=sites_now)
        rows.append({"module": m, "verdict": f["verdict"], "entry": entry,
                     "why": f["why"], "kill_rate": entry.get("kill_rate")})
    rows.sort(key=lambda r: (rank[r["verdict"]],
                             r["kill_rate"] if r["kill_rate"] is not None else -1,
                             r["module"]))
    return rows


def print_ledger(rows):
    print(f"{'guard':24s} {'rate':>8s}  {'killed':>9s}  {'state':8s} why")
    print("-" * 100)
    for r in rows:
        e = r["entry"] or {}
        rate = f"{r['kill_rate']:.0%}" if r["kill_rate"] is not None else "--"
        tally = f"{e['killed']}/{e['mutants']}" if e else "--"
        print(f"{r['module']:24s} {rate:>8s}  {tally:>9s}  {r['verdict']:8s} {r['why']}")
    print()
    print("A rate is quotable only on a FRESH row. STALE/UNKNOWN/NEVER mean "
          "re-measure before citing:")
    print("  python3 -m pipeline.tools.audit_mutation_sweep --module <guard> --ledger")

if __name__ == "__main__":
    raise SystemExit(main())
