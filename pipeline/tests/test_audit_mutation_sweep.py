"""Tests for the instrument that tests the guards.

`audit_mutation_sweep` shipped 2026-08-29 and ran for four nights with no test
file of its own -- the tool whose entire job is to ask "does this guard have a
positive control?" had none. This file is that positive control.

Every test here builds a throwaway repo (one fake guard, one fake test) and
points the sweep at it, so nothing depends on the real guards or their kill
rates, which change whenever anyone touches a test.

The two tests that matter are the injection ones. `test_unstable_*` injects a
genuinely flaky test and asserts the sweep says UNSTABLE; `test_timeout_*`
injects a hang and asserts the sweep says "no verdict" rather than "killed".
Both were red before the 2026-09-02 change and are the reason it exists.
"""
from __future__ import annotations

import ast
import json
import subprocess
import textwrap

import pytest

from pipeline.tools import audit_mutation_sweep as sweep_mod


def make_repo(tmp_path, guard_src, test_src, name="fake_guard"):
    """A minimal repo the sweep can be pointed at: one guard, one test."""
    tools = tmp_path / "pipeline" / "tools"
    tests = tmp_path / "pipeline" / "tests"
    tools.mkdir(parents=True)
    tests.mkdir(parents=True)
    (tmp_path / "pipeline" / "__init__.py").write_text("")
    (tools / "__init__.py").write_text("")
    (tools / f"{name}.py").write_text(textwrap.dedent(guard_src))
    (tests / f"test_{name}.py").write_text(textwrap.dedent(test_src))
    return name


@pytest.fixture
def point_sweep_at(monkeypatch):
    def _point(tmp_path):
        monkeypatch.setattr(sweep_mod, "ROOT", tmp_path)
        monkeypatch.setattr(sweep_mod, "TOOLS", tmp_path / "pipeline" / "tools")
        monkeypatch.setattr(sweep_mod, "TESTS", tmp_path / "pipeline" / "tests")
    return _point


# --------------------------------------------------------------------------
# the ordinary verdicts

def test_a_pinned_constant_is_killed(tmp_path, point_sweep_at):
    name = make_repo(tmp_path, "LIMIT = 10\n", """
        from pipeline.tools.fake_guard import LIMIT

        def test_limit():
            assert LIMIT == 10
    """)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False)
    assert r["mutants"] == 1, r
    assert r["killed"] == 1 and r["survived"] == 0
    assert r["kill_rate"] == 1.0


def test_an_unpinned_constant_survives(tmp_path, point_sweep_at):
    name = make_repo(tmp_path, "LIMIT = 10\n", """
        from pipeline.tools import fake_guard

        def test_it_imports():
            assert hasattr(fake_guard, "LIMIT")
    """)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False)
    assert r["killed"] == 0 and r["survived"] == 1
    assert r["kill_rate"] == 0.0
    assert r["survivors"][0]["change"] == "10 -> 11"


def test_survivors_carry_an_index_because_descriptors_collide(tmp_path, point_sweep_at):
    """Two mutants on one line can share (line, kind, change).

    Comparing runs by descriptor silently merged them -- 15 survivors became a
    14-element set -- which is the kind of off-by-one that makes two different
    runs look identical. The index disambiguates."""
    name = make_repo(tmp_path, "PAIR = (10, 10)\n", """
        from pipeline.tools import fake_guard

        def test_it_imports():
            assert fake_guard.PAIR
    """)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False)
    assert r["survived"] == 2, r
    descriptors = {(s["line"], s["kind"], s["change"]) for s in r["survivors"]}
    assert len(descriptors) == 1, "precondition: the two descriptors do collide"
    assert len({s["index"] for s in r["survivors"]}) == 2


# --------------------------------------------------------------------------
# the injections -- these are the positive controls

FLAKY_TEST = """
    import os, pathlib
    from pipeline.tools import fake_guard

    def test_limit():
        counter = pathlib.Path(os.environ["FAKE_COUNTER"])
        n = int(counter.read_text() or "0")
        counter.write_text(str(n + 1))
        if fake_guard.LIMIT == 10:
            return                      # unmutated: green every time
        assert n % 2 == 0               # mutated: green, red, green, red...
"""


def test_unstable_mutant_is_reported_and_kept_out_of_the_kill_rate(
        tmp_path, point_sweep_at, monkeypatch):
    """Injected flakiness must surface as UNSTABLE, not as a coin-flip vote.

    Before this, the same mutant voted 'killed' on one run and 'survived' on
    the next, and the kill rate wandered 6pp between identical runs
    (Plumber Joe, 2026-09-01: 43/47/49/43 on audit_universe_shape)."""
    counter = tmp_path / "counter.txt"
    counter.write_text("0")
    monkeypatch.setenv("FAKE_COUNTER", str(counter))
    name = make_repo(tmp_path, "LIMIT = 10\n", FLAKY_TEST)
    point_sweep_at(tmp_path)

    r = sweep_mod.sweep(name, verbose=False, repeat=3)
    assert r["unstable"] == 1, r
    assert r["killed"] == 0 and r["survived"] == 0
    assert r["mutants"] == 0, "an unstable mutant must not be in the denominator"
    assert r["kill_rate"] is None
    trials = r["unstable_mutants"][0]["trials"]
    assert True in trials and False in trials, trials


def test_without_repeat_the_same_flakiness_is_invisible(
        tmp_path, point_sweep_at, monkeypatch):
    """The negative half of the control: repeat=1 cannot see it.

    This is the state the instrument was in for four nights -- it reported a
    crisp verdict for a mutant it had no crisp verdict about."""
    counter = tmp_path / "counter.txt"
    counter.write_text("0")
    monkeypatch.setenv("FAKE_COUNTER", str(counter))
    name = make_repo(tmp_path, "LIMIT = 10\n", FLAKY_TEST)
    point_sweep_at(tmp_path)

    r = sweep_mod.sweep(name, verbose=False, repeat=1)
    assert r["unstable"] == 0
    assert r["killed"] + r["survived"] == 1


def test_a_timeout_is_no_verdict_not_a_kill(tmp_path, point_sweep_at, monkeypatch):
    """A mutant that hangs was counted as killed. That reads 'the machine was
    busy' as 'the suite caught it' -- a false positive control, and one that
    gets *more* generous the more loaded the machine is."""
    monkeypatch.setattr(sweep_mod, "TEST_TIMEOUT", 3)
    name = make_repo(tmp_path, "LIMIT = 10\n", """
        import time
        from pipeline.tools import fake_guard

        def test_limit():
            if fake_guard.LIMIT != 10:
                time.sleep(30)          # only the mutant hangs
            assert True
    """)
    point_sweep_at(tmp_path)

    r = sweep_mod.sweep(name, verbose=False)
    assert r["no_verdict"] == 1, r
    assert r["killed"] == 0, "a timeout is not evidence the test caught anything"
    assert r["mutants"] == 0


def test_no_bytecode_cache_is_left_for_the_mutated_module(
        tmp_path, point_sweep_at, monkeypatch):
    """The mutant must be compiled from source every time, never from a .pyc.

    CPython validates a cached .pyc by (source mtime in whole SECONDS, source
    size). Two consecutive mutants of the same module are both `ast.unparse`
    output, so they differ in size only by the mutation's own length delta --
    zero for `20 -> 21`, `0 -> 1`, `==` -> `!=`. Inside one second, mutant N
    ran as mutant N-1 and the verdict printed against N belonged to N-1.

    Measured on audit_universe_shape, 2026-09-02: three identical invocations
    gave 41% / 45% / 47% with ten mutants flipping, and every flipping mutant
    had a byte delta of exactly 0 from its predecessor. With bytecode caching
    off: 45% / 45% / 45%, bit-identical survivor sets."""
    kept = {}
    real_exit = sweep_mod.Workspace.__exit__
    monkeypatch.setattr(sweep_mod.Workspace, "__exit__",
                        lambda self, *e: kept.setdefault("dir", self.dir) and None)

    name = make_repo(tmp_path, "LIMIT = 10\n", """
        from pipeline.tools.fake_guard import LIMIT

        def test_limit():
            assert LIMIT == 10
    """)
    point_sweep_at(tmp_path)
    try:
        sweep_mod.sweep(name, verbose=False)
        caches = list((kept["dir"] / "pipeline").rglob("__pycache__"))
        stale = [c for c in caches if any(p.name.startswith(name) for p in c.iterdir())]
        assert not stale, f"a .pyc for the mutated module survived: {stale}"
    finally:
        import shutil
        shutil.rmtree(kept.get("dir", tmp_path / "nope"), ignore_errors=True)
        monkeypatch.setattr(sweep_mod.Workspace, "__exit__", real_exit)


# --------------------------------------------------------------------------
# slicing -- a full sweep is ~1100 pytest runs and does not fit in one sitting

SIX_SITES = "A = (1, 2, 3, 4, 5, 6)\n"
IMPORTS_ONLY = """
    from pipeline.tools import fake_guard

    def test_it_imports():
        assert fake_guard.A
"""


def test_a_slice_runs_only_the_mutants_in_its_range(tmp_path, point_sweep_at):
    """The failure this pins: the range argument is accepted and ignored.

    A sweep that quietly runs all six mutants still returns a plausible-looking
    report; the only thing that gives it away is the count."""
    name = make_repo(tmp_path, SIX_SITES, IMPORTS_ONLY)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False, index_from=2, index_to=4)
    assert r["mutants"] == 2, r
    assert {s["index"] for s in r["survivors"]} == {2, 3}


def test_slices_carry_the_whole_module_site_count_not_the_slice_size(
        tmp_path, point_sweep_at):
    """`total_sites` is what makes slices mergeable and what catches a merge
    across an edit to the guard. If it were the slice size it would be a
    restatement of `mutants` and would say nothing."""
    name = make_repo(tmp_path, SIX_SITES, IMPORTS_ONLY)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False, index_from=4, index_to=6)
    assert r["total_sites"] == 6, r
    assert r["index_from"] == 4 and r["index_to"] == 6


def test_complementary_slices_reconstruct_the_whole_module(tmp_path, point_sweep_at):
    """The failure this pins: slices that overlap or leave a gap.

    Off-by-one at the boundary is invisible per-slice -- each report looks
    fine -- and only shows up when the pieces are added back together."""
    name = make_repo(tmp_path, SIX_SITES, IMPORTS_ONLY)
    point_sweep_at(tmp_path)
    whole = sweep_mod.sweep(name, verbose=False)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    assert a["mutants"] + b["mutants"] == whole["mutants"]
    assert a["killed"] + b["killed"] == whole["killed"]
    merged = {s["index"] for s in a["survivors"]} | {s["index"] for s in b["survivors"]}
    assert merged == {s["index"] for s in whole["survivors"]}


def test_a_range_past_the_end_is_an_empty_slice_not_a_crash(tmp_path, point_sweep_at):
    """Chunked runs walk off the end by construction -- the last chunk of a
    fixed stride is short. That has to be an empty report, not a traceback,
    and its kill rate has to be None rather than a divide-by-zero or a 0%
    that would drag a merged average down."""
    name = make_repo(tmp_path, SIX_SITES, IMPORTS_ONLY)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False, index_from=99, index_to=200)
    assert r["mutants"] == 0 and r["survived"] == 0
    assert r["kill_rate"] is None
    assert r["total_sites"] == 6


def test_workspace_carries_github_so_workflow_reading_guards_can_be_swept(
        tmp_path, point_sweep_at):
    """A guard that reads `.github/` must be sweepable.

    Until 2026-09-21 the workspace copied `pipeline/` and symlinked `data/` and
    nothing else, so `audit_schedule_windows` -- whose entire job is reading the
    workflow crons -- came back "baseline is already red; refusing to sweep".
    Nothing was wrong with its tests: 86 mutants, 56% killed once the workspace
    stopped being incomplete. The failure mode this pins is a diagnosis that
    points at the wrong thing."""
    name = make_repo(tmp_path, '''
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[2]
        LIMIT = 10

        def cron_lines():
            text = (ROOT / ".github" / "workflows" / "fake.yml").read_text()
            return [ln for ln in text.splitlines() if "cron" in ln]
    ''', """
        from pipeline.tools.fake_guard import cron_lines, LIMIT

        def test_reads_the_workflow():
            assert len(cron_lines()) == 2
            assert LIMIT == 10
    """)
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "fake.yml").write_text("on:\n  schedule:\n"
                                 "    - cron: '20 20 * * 1-5'\n"
                                 "    - cron: '30 1 * * 1-5'\n")
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False)
    assert not r.get("error"), r
    assert r["mutants"] > 0, r


def test_workspace_carries_the_second_test_root_so_guards_that_read_it_sweep(
        tmp_path, point_sweep_at):
    """A guard that reads the repo's other test root (`tests/`) must be sweepable.

    Same shape as the `.github` test above, found five days later on a
    different guard. Until 2026-09-26 the workspace copied `pipeline/`,
    `.github/` and the config files, so `audit_ci_test_coverage` came back
    "baseline is already red; refusing to sweep" -- and the test that was red
    was its own T3, "declared path 'tests' does not exist". Nothing was wrong
    with its tests: 174 mutants, sweepable as soon as the workspace stopped
    being incomplete. Two instances make it a rule: whatever a guard READS
    from outside `pipeline/` has to be in the workspace, or the sweep accuses
    the tests of a hole the sweep itself dug."""
    name = make_repo(tmp_path, '''
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[2]
        LIMIT = 10

        def second_root_files():
            return sorted(p.name for p in (ROOT / "tests").glob("test_*.py"))
    ''', """
        from pipeline.tools.fake_guard import second_root_files, LIMIT

        def test_reads_the_second_root():
            assert second_root_files() == ["test_alpha.py", "test_beta.py"]
            assert LIMIT == 10
    """)
    second = tmp_path / "tests"
    second.mkdir()
    (second / "test_alpha.py").write_text("def test_a():\n    assert True\n")
    (second / "test_beta.py").write_text("def test_b():\n    assert True\n")
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep(name, verbose=False)
    assert not r.get("error"), r
    assert r["mutants"] > 0, r


# ---------------------------------------------------------------------------
# The ledger (2026-10-02, T-1002-10).
#
# Added because the rate kept being quoted out of prose and kept being wrong:
# 09-24 took the number on the left of a "54 -> 57%" arrow (twice, and it
# picked the wrong guard to work on), 09-28 copied a three-week-old survivor
# count forward, 10-01 handed the next shift "audit_ledger is 52.5%" when it
# had been 98% since 09-25. Four instances, so: one home for the number, and a
# freshness verdict the reader does not have to take on trust.
#
# The controls below are built per FAILURE MODE, not one per function -- a
# single happy-path assertion proves only that the code recognises "nothing
# happened". The modes that matter here:
#   (a) a reading is filed that was never a whole-module sweep
#   (b) a reading is believed FRESH when the guard moved underneath it
#   (c) a reading is believed FRESH when it cannot be placed at all
#       (unknown sha, no sha, dirty tree) -- the silent false negative
# ---------------------------------------------------------------------------


def git_repo(tmp_path):
    """A real git repo with one guard and one test, both committed."""
    guard = """
        LIMIT = 3
        def over(n):
            return n > LIMIT
    """
    test = """
        from pipeline.tools.fake_guard import over
        def test_limit():
            assert over(4) and not over(3)
    """
    make_repo(tmp_path, guard, test)
    run = lambda *a: subprocess.run(["git", "-C", str(tmp_path), *a],
                                    capture_output=True, text=True, check=True)
    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@t")
    run("config", "user.name", "t")
    run("add", "-A")
    run("commit", "-q", "-m", "init")
    head = run("rev-parse", "HEAD").stdout.strip()
    return head, run


def reading(**over):
    base = {"killed": 9, "mutants": 10, "survived": 1, "unstable": 0,
            "kill_rate": 0.9, "total_sites": 10, "repeat": 1,
            "commit": None, "uncommitted": [], "measured_at": "2026-10-02T04:00:00+0900"}
    base.update(over)
    return base


def test_a_whole_module_sweep_is_filed_with_the_commit_it_was_taken_at(
        tmp_path, point_sweep_at):
    head, _ = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    r = sweep_mod.sweep("fake_guard", verbose=False)
    entry = sweep_mod.record(r)
    assert entry is not None
    assert entry["commit"] == head
    assert entry["killed"] == r["killed"] and entry["mutants"] == r["mutants"]
    on_disk = json.loads(sweep_mod.ledger_path(tmp_path).read_text())
    assert on_disk["modules"]["fake_guard"]["kill_rate"] == r["kill_rate"]


def test_a_slice_is_refused_so_its_rate_never_lands_under_the_module_name(
        tmp_path, point_sweep_at):
    """(a) The failure this prevents is publishing 12/13 as a guard's score."""
    git_repo(tmp_path)
    point_sweep_at(tmp_path)
    partial = sweep_mod.sweep("fake_guard", verbose=False, index_from=0, index_to=1)
    assert partial["kill_rate"] is not None          # the slice HAS a rate
    assert sweep_mod.record(partial) is None         # and it is still not a reading
    assert not sweep_mod.ledger_path(tmp_path).exists()


def test_a_reading_on_an_untouched_guard_is_fresh(tmp_path, point_sweep_at):
    head, _ = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    f = sweep_mod.freshness(reading(commit=head), "fake_guard", repo=tmp_path)
    assert f["verdict"] == "FRESH"
    assert f["commits"] == 0


def test_editing_the_guard_makes_the_reading_stale(tmp_path, point_sweep_at):
    """(b) via git."""
    head, run = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    (tmp_path / "pipeline" / "tools" / "fake_guard.py").write_text(
        "LIMIT = 4\ndef over(n):\n    return n > LIMIT\n")
    run("commit", "-qam", "bump the limit")
    f = sweep_mod.freshness(reading(commit=head), "fake_guard", repo=tmp_path)
    assert f["verdict"] == "STALE"
    assert f["commits"] == 1


def test_editing_only_the_test_file_also_makes_the_reading_stale(
        tmp_path, point_sweep_at):
    """(b) the half the site count cannot see.

    A kill rate is a fact about the guard AND its tests. Adding a test changes
    the rate without changing one mutation site, so a freshness check that only
    counted sites would call this reading FRESH -- which is precisely the
    situation on 09-25 (`audit_ledger` 66% -> 98%, source untouched)."""
    head, run = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    t = tmp_path / "pipeline" / "tests" / "test_fake_guard.py"
    t.write_text(t.read_text() + "\ndef test_more():\n    assert not over(2)\n")
    run("commit", "-qam", "one more test")
    before = sweep_mod.freshness(reading(commit=head), "fake_guard", repo=tmp_path)
    assert before["verdict"] == "STALE"
    # and the site count really is blind to it, which is why git has to be asked
    sites_now = len(sweep_mod.sites(ast.parse(
        (tmp_path / "pipeline" / "tools" / "fake_guard.py").read_text())))
    assert sites_now == reading()["total_sites"] or sites_now != 10
    assert sweep_mod.freshness(reading(commit=head, total_sites=sites_now),
                               "fake_guard", repo=tmp_path,
                               sites_now=sites_now)["verdict"] == "STALE"


def test_a_commit_this_clone_does_not_have_reads_unknown_not_fresh(
        tmp_path, point_sweep_at):
    """(c) The silent false negative, and the reason this is not a date check.

    `git log <missing sha>..HEAD` exits NON-ZERO with EMPTY stdout. Count the
    lines of that output and a reading that cannot be placed in this history at
    all scores "0 commits touched it" = FRESH. Same shape as grepping a ref
    that does not exist and believing the zero hits."""
    git_repo(tmp_path)
    point_sweep_at(tmp_path)
    absent = "0" * 40
    rc, out = sweep_mod._git(
        ["log", "--oneline", f"{absent}..HEAD", "--",
         *sweep_mod.guard_paths("fake_guard")], tmp_path)
    assert rc != 0 and out.strip() == ""        # the trap, demonstrated
    f = sweep_mod.freshness(reading(commit=absent), "fake_guard", repo=tmp_path)
    assert f["verdict"] == "UNKNOWN"


def test_a_reading_with_no_commit_reads_unknown(tmp_path, point_sweep_at):
    """(c) same mode, via a ledger written before commits were recorded."""
    git_repo(tmp_path)
    point_sweep_at(tmp_path)
    assert sweep_mod.freshness(reading(commit=None), "fake_guard",
                               repo=tmp_path)["verdict"] == "UNKNOWN"


def test_a_reading_taken_on_a_dirty_guard_reads_unknown(tmp_path, point_sweep_at):
    """(c) the commit is real, but the measured bytes were never in it."""
    head, _ = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    entry = reading(commit=head, uncommitted=["pipeline/tools/fake_guard.py"])
    f = sweep_mod.freshness(entry, "fake_guard", repo=tmp_path)
    assert f["verdict"] == "UNKNOWN"
    assert "uncommitted" in f["why"]


def test_record_captures_a_dirty_guard_so_the_reading_is_not_trusted_later(
        tmp_path, point_sweep_at):
    head, _ = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    g = tmp_path / "pipeline" / "tools" / "fake_guard.py"
    g.write_text(g.read_text() + "\n# touched after the commit\n")
    entry = sweep_mod.record(sweep_mod.sweep("fake_guard", verbose=False), repo=tmp_path)
    assert entry["uncommitted"] == ["pipeline/tools/fake_guard.py"]
    assert sweep_mod.freshness(entry, "fake_guard", repo=tmp_path)["verdict"] == "UNKNOWN"


def test_record_uses_the_commit_at_workspace_entry_not_after_the_sweep_runs(
        tmp_path, point_sweep_at, monkeypatch):
    """(mechanism, T-1002-16) A commit landing WHILE the sweep is running must
    not be credited with bytes it never contained.

    T-1002-10's review caught this: a filed reading's `measured_at` postdated
    its own recorded `commit` by about as long as a 44-mutant sweep takes to
    run, which only makes sense if the commit was read at the END of the
    sweep rather than at the start. Here a commit is made to land mid-sweep
    (right after the baseline check, well after `Workspace.__enter__` has
    already copied the guard's bytes into the throwaway tree) and the filed
    reading must still carry the OLDER commit and the dirty state that was
    true when those bytes were actually copied.

    Positive control: this is exactly the scenario that goes red if `record()`
    is reverted to asking git for `HEAD` / `status --porcelain` itself after
    the sweep finishes -- it would then report the newer commit and an empty
    `uncommitted`, because by that time the mid-sweep commit has already
    absorbed the dirty file."""
    head_before, run = git_repo(tmp_path)
    guard = tmp_path / "pipeline" / "tools" / "fake_guard.py"
    guard.write_text(guard.read_text() + "\n# dirty before the sweep starts\n")
    point_sweep_at(tmp_path)

    real_run_tests = sweep_mod.Workspace.run_tests
    calls = {"n": 0}

    def run_tests_then_commit_once(self, module):
        result = real_run_tests(self, module)
        calls["n"] += 1
        if calls["n"] == 1:
            # By now Workspace.__enter__ has already read HEAD and the dirty
            # state for this sweep -- this commit must NOT be what gets filed.
            run("commit", "-qam", "a commit that lands mid-sweep")
        return result

    monkeypatch.setattr(sweep_mod.Workspace, "run_tests", run_tests_then_commit_once)

    r = sweep_mod.sweep("fake_guard", verbose=False)
    head_after = run("rev-parse", "HEAD").stdout.strip()
    assert head_after != head_before, "precondition: a commit really landed mid-sweep"

    entry = sweep_mod.record(r, repo=tmp_path)
    assert entry["commit"] == head_before
    assert entry["uncommitted"] == ["pipeline/tools/fake_guard.py"]


def test_a_guard_whose_site_count_moved_is_stale_without_asking_git(
        tmp_path, point_sweep_at):
    """(b) via the second ruler, for the tarball/shallow-clone case."""
    head, _ = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    f = sweep_mod.freshness(reading(commit=head, total_sites=10), "fake_guard",
                            repo=tmp_path, sites_now=11)
    assert f["verdict"] == "STALE"
    assert "11" in f["why"] and "10" in f["why"]


def test_an_unmeasured_guard_outranks_a_low_but_known_one(tmp_path, point_sweep_at):
    """The ordering is the point: 'which guard tonight' is answered by what is
    least KNOWN, not by the smallest number on file. A guard nobody swept is
    less known than one sitting at 50%."""
    head, _ = git_repo(tmp_path)
    point_sweep_at(tmp_path)
    tools = tmp_path / "pipeline" / "tools"
    (tools / "audit_measured.py").write_text("X = 1\n")
    (tools / "audit_never.py").write_text("Y = 2\n")
    sweep_mod.ledger_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    sweep_mod.ledger_path(tmp_path).write_text(json.dumps({
        "_schema": sweep_mod.LEDGER_SCHEMA,
        "modules": {"audit_measured": reading(commit=head, kill_rate=0.5,
                                              total_sites=0)}}))
    rows = sweep_mod.ledger_rows(repo=tmp_path)
    order = [r["module"] for r in rows]
    assert order.index("audit_never") < order.index("audit_measured")
    assert [r["verdict"] for r in rows if r["module"] == "audit_never"] == ["NEVER"]


def test_the_ledger_path_follows_root_so_tests_never_write_into_the_repo(tmp_path):
    """The bug this is the control for already has a history in this repo: a
    tool that resolved a real-tree path at import time, and a test suite that
    wrote into `data/history/` for four days before anyone noticed
    (2026-08-23, test_quality.py)."""
    assert sweep_mod.ledger_path(tmp_path) == tmp_path / sweep_mod.LEDGER_REL
    assert sweep_mod.ledger_path(tmp_path) != sweep_mod.ledger_path()


# --------------------------------------------------------------------------
# merging slices back into a reading
#
# `record()` has required this step since it was written -- "the merged numbers
# have to be assembled before they can be filed" -- and until 2026-10-04 the
# only place the addition existed was the hand-written set union in
# `test_complementary_slices_reconstruct_the_whole_module` above. The practical
# cost: a full sweep of `audit_reads_declarations` is 52 mutants at ~17.6s each
# (measured 2026-10-04), about 15 minutes against a 10-minute foreground
# ceiling, so it could be swept in halves and never filed. The three biggest
# guards (123 / 130 / 165 sites) sat at NEVER for the same reason.
#
# Every check in `merge_slices` is a refusal rather than a warning because each
# one, when wrong, yields a PLAUSIBLE rate. The tests below are organised by
# HOW the merge can be wrong, not by which line implements it: a gap, an
# overlap, a short tiling, an edit to the guard between slices, a different
# --repeat, a different commit, a report too old to carry the hash, and a
# hand-edited report. Each has to come back refused on its own.

MIXED_SITES = "A = (1, 2, 3, 4, 5, 6)\n"
PINS_BOTH_ENDS = """
    from pipeline.tools import fake_guard

    def test_the_ends_are_pinned():
        assert fake_guard.A[0] == 1
        assert fake_guard.A[5] == 6
"""


def test_merged_slices_equal_the_whole_module_sweep(tmp_path, point_sweep_at):
    """The headline: two ways of computing the same reading must agree.

    The whole-module sweep is computed by running all six mutants in one go;
    the merged reading is computed by running two halves and adding them. If
    `merge_slices` double-counted, dropped a survivor, or recomputed the rate
    over the wrong denominator, these two numbers would differ."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    whole = sweep_mod.sweep(name, verbose=False)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)

    merged = sweep_mod.merge_slices([a, b])
    assert not merged.get("error"), merged
    # the mix is load-bearing: a guard whose mutants all die, or all survive,
    # would pass this test even if the merge threw one half away.
    assert whole["killed"] == 2 and whole["survived"] == 4, whole
    for field in ("module", "mutants", "killed", "survived", "kill_rate",
                  "total_sites", "index_from", "index_to"):
        assert merged[field] == whole[field], (field, merged[field], whole[field])
    assert [s["index"] for s in merged["survivors"]] == \
           [s["index"] for s in whole["survivors"]]
    assert merged["merged_from"] == [[0, 3], [3, 6]]


def test_a_merged_reading_is_filed_while_its_own_slices_are_still_refused(
        tmp_path, point_sweep_at):
    """Both directions, in one test, because only the pair is informative.

    `record()` refusing everything would pass a test that only checked the
    slices; `record()` accepting anything would pass a test that only checked
    the merge."""
    git_repo(tmp_path)
    point_sweep_at(tmp_path)
    total = len(sweep_mod.sites(ast.parse(
        (tmp_path / "pipeline" / "tools" / "fake_guard.py").read_text())))
    a = sweep_mod.sweep("fake_guard", verbose=False, index_from=0, index_to=1)
    b = sweep_mod.sweep("fake_guard", verbose=False, index_from=1, index_to=total)

    assert sweep_mod.record(a) is None
    assert sweep_mod.record(b) is None
    assert not sweep_mod.ledger_path(tmp_path).exists()

    merged = sweep_mod.merge_slices([a, b])
    entry = sweep_mod.record(merged)
    assert entry is not None, merged
    assert entry["mutants"] == a["mutants"] + b["mutants"]
    assert entry["total_sites"] == total
    on_disk = json.loads(sweep_mod.ledger_path(tmp_path).read_text())
    assert on_disk["modules"]["fake_guard"]["kill_rate"] == merged["kill_rate"]


def test_a_gap_between_slices_is_refused(tmp_path, point_sweep_at):
    """Drop the middle and the rate is taken over four mutants out of six --
    a number that looks exactly like a reading."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=2)
    c = sweep_mod.sweep(name, verbose=False, index_from=4, index_to=6)
    r = sweep_mod.merge_slices([a, c])
    assert r.get("error"), r
    assert "gap at index 2" in r["error"], r["error"]


def test_overlapping_slices_are_refused(tmp_path, point_sweep_at):
    """An overlap counts a mutant twice, so `mutants` exceeds `total_sites`
    while every individual report is honest."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=4)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    r = sweep_mod.merge_slices([a, b])
    assert r.get("error"), r
    assert "overlap at index 3" in r["error"], r["error"]


def test_slices_that_stop_short_of_the_last_site_are_refused(
        tmp_path, point_sweep_at):
    """The off-by-one at the end: a stride that stops one site early.

    This is the one a tired operator actually hits, and it is invisible --
    the slices tile perfectly, they just do not reach the end."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=5)
    r = sweep_mod.merge_slices([a, b])
    assert r.get("error"), r
    assert "cover [0, 5)" in r["error"] and "6 sites" in r["error"], r["error"]


def test_an_edit_to_the_guard_between_slices_is_refused_even_with_the_site_count_unchanged(
        tmp_path, point_sweep_at):
    """The reason the hash exists rather than just `total_sites`.

    Most edits to a guard do not change how many mutation sites it has --
    change a constant, swap `>` for `>=` -- so `total_sites` matches across
    the edit and the indices silently refer to different lines in each half.
    Positive control for the hash itself: the same two slices with the same
    `total_sites` must merge when the bytes match and refuse when they do
    not, so this test asserts BOTH."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    guard = tmp_path / "pipeline" / "tools" / f"{name}.py"
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)

    # An element the test does not pin, so the baseline stays green -- an edit
    # that makes a guard's tests red is caught by "baseline is already red",
    # not by this check, and would not exercise it. Site 1 is now `9 -> 10`
    # where it used to be `2 -> 3`: same index, different line of meaning.
    guard.write_text("A = (1, 9, 3, 4, 5, 6)\n")        # same 6 sites, new bytes
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    assert not b.get("error"), b                        # the edit did not break it
    assert a["total_sites"] == b["total_sites"] == 6     # the weak check agrees
    assert a["src_sha256"] != b["src_sha256"]

    r = sweep_mod.merge_slices([a, b])
    assert r.get("error") and "src_sha256" in r["error"], r

    guard.write_text(MIXED_SITES)                       # put the bytes back
    b2 = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    assert not sweep_mod.merge_slices([a, b2]).get("error")


def test_slices_run_with_different_repeat_are_refused(tmp_path, point_sweep_at):
    """A 1-trial slice and a 3-trial slice do not share a definition of
    UNSTABLE, so adding their survivor sets mixes two instruments."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3, repeat=1)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6, repeat=2)
    r = sweep_mod.merge_slices([a, b])
    assert r.get("error") and "repeat" in r["error"], r


def test_slices_taken_at_different_commits_are_refused(tmp_path, point_sweep_at):
    """`commit` is the provenance `record()` files, and a reading has one.

    Hand-built rather than swept twice: what is under test is the refusal, and
    making a second commit here would also change the bytes, which the hash
    would catch first and would not prove this check works."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = dict(sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6),
             commit="deadbeef" * 5)
    a = dict(a, commit="cafebabe" * 5)
    r = sweep_mod.merge_slices([a, b])
    assert r.get("error") and "commit" in r["error"], r


def test_a_slice_from_before_the_hash_existed_is_refused_not_merged_on_faith(
        tmp_path, point_sweep_at):
    """Reports written before 2026-10-04 have no `src_sha256`.

    Treating a missing hash as "matches" would make every stale report on disk
    mergeable with a fresh one -- the exact case the hash was added for."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    old = {k: v for k, v in a.items() if k != "src_sha256"}
    r = sweep_mod.merge_slices([old, b])
    assert r.get("error") and "re-sweep" in r["error"], r


def test_an_empty_tail_slice_does_not_block_a_complete_merge(
        tmp_path, point_sweep_at):
    """Chunked runs walk off the end by construction, so the last report of a
    fixed stride is routinely empty. It ran nothing, so it is not part of the
    tiling -- refusing it would punish the caller for the arithmetic the tool
    told them to do."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    tail = sweep_mod.sweep(name, verbose=False, index_from=6, index_to=9)
    assert tail["mutants"] == 0
    r = sweep_mod.merge_slices([a, b, tail])
    assert not r.get("error"), r
    assert r["mutants"] == 6 and r["merged_from"] == [[0, 3], [3, 6]]


def test_a_mutant_index_outside_its_own_slice_is_refused(tmp_path, point_sweep_at):
    """Guards against a report assembled or trimmed by hand.

    The range fields and the survivor indices are two statements about the
    same thing; if they disagree, the report is not a sweep's output and its
    indices cannot be trusted to be disjoint from the other slice's."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep(name, verbose=False, index_from=3, index_to=6)
    assert b["survivors"], b
    tampered = dict(b, survivors=[dict(b["survivors"][0], index=1)])
    r = sweep_mod.merge_slices([a, tampered])
    assert r.get("error") and "outside its own slice" in r["error"], r


def test_slices_from_different_modules_never_add_up(tmp_path, point_sweep_at):
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    make_repo_second = (tmp_path / "pipeline" / "tools" / "other_guard.py")
    make_repo_second.write_text(MIXED_SITES)
    (tmp_path / "pipeline" / "tests" / "test_other_guard.py").write_text(
        textwrap.dedent(PINS_BOTH_ENDS).replace("fake_guard", "other_guard"))
    point_sweep_at(tmp_path)
    a = sweep_mod.sweep(name, verbose=False, index_from=0, index_to=3)
    b = sweep_mod.sweep("other_guard", verbose=False, index_from=3, index_to=6)
    r = sweep_mod.merge_slices([a, b])
    assert r.get("error") and "different modules" in r["error"], r


def test_merge_reads_the_file_shape_that_json_writes(tmp_path, point_sweep_at):
    """End to end through the CLI, because the halves arrive as files.

    `--json` writes `{"modules": [...]}`, and the operator passes two of those
    paths back in. If `slices_in` only understood a bare result, the whole
    feature would be unreachable from the command line while every unit test
    stayed green."""
    name = make_repo(tmp_path, MIXED_SITES, PINS_BOTH_ENDS)
    point_sweep_at(tmp_path)
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    sweep_mod.main(["--module", name, "-q", "--index-from", "0",
                    "--index-to", "3", "--json", str(first)])
    sweep_mod.main(["--module", name, "-q", "--index-from", "3",
                    "--index-to", "6", "--json", str(second)])

    found = sweep_mod.slices_in([first, second])
    assert sorted(found) == [name] and len(found[name]) == 2
    merged = sweep_mod.merge_slices(found[name])
    assert not merged.get("error"), merged
    assert merged["mutants"] == 6 and merged["index_to"] == 6
    assert sweep_mod.main(["--merge", str(first), str(second), "-q"]) == 0


MIXED_WITH_A_FLAKY_SITE = "LIMIT = 10\nA = (1, 2, 3)\n"
PINS_TUPLE_ENDS_AND_ONE_FLAKY = """
    import os, pathlib
    from pipeline.tools import fake_guard

    def test_tuple_ends_are_pinned():
        assert fake_guard.A[0] == 1
        assert fake_guard.A[2] == 3

    def test_limit_is_flaky_once_mutated():
        counter = pathlib.Path(os.environ["FAKE_COUNTER"])
        n = int(counter.read_text() or "0")
        counter.write_text(str(n + 1))
        if fake_guard.LIMIT == 10:
            return                      # unmutated: green every time
        assert n % 2 == 0               # mutated: green, red, green, red...
"""


def test_the_merged_rate_is_over_mutants_not_over_sites(
        tmp_path, point_sweep_at, monkeypatch):
    """`mutants` and `total_sites` are different numbers, and must be shown so.

    Every other merge test here uses a guard where the two are equal -- no
    mutant skipped, none unstable -- so `killed/mutants` and
    `killed/total_sites` give the same answer and a merge dividing by the
    wrong one passes. Measured 2026-10-04: swapping the denominator in
    `merge_slices` left the whole suite green. This guard separates them. One
    site is flaky under mutation, so at repeat=2 it comes back UNSTABLE and is
    kept OUT of the denominator (Plumber Joe's rule, 2026-09-01) while still
    counting as a site: 4 sites, 3 mutants, 2 killed. 2/3 is 67%, 2/4 is 50%.
    """
    counter = tmp_path / "counter.txt"
    counter.write_text("0")
    monkeypatch.setenv("FAKE_COUNTER", str(counter))
    name = make_repo(tmp_path, MIXED_WITH_A_FLAKY_SITE,
                     PINS_TUPLE_ENDS_AND_ONE_FLAKY)
    point_sweep_at(tmp_path)

    whole = sweep_mod.sweep(name, verbose=False, repeat=2)
    assert whole["total_sites"] == 4 and whole["mutants"] == 3, whole
    assert whole["unstable"] == 1 and whole["killed"] == 2, whole
    assert whole["kill_rate"] == round(2 / 3, 3), whole

    a = sweep_mod.sweep(name, verbose=False, repeat=2, index_from=0, index_to=2)
    b = sweep_mod.sweep(name, verbose=False, repeat=2, index_from=2, index_to=4)
    merged = sweep_mod.merge_slices([a, b])
    assert not merged.get("error"), merged
    assert merged["mutants"] == 3 and merged["total_sites"] == 4, merged
    assert merged["unstable"] == 1 and len(merged["unstable_mutants"]) == 1
    assert merged["kill_rate"] == round(2 / 3, 3), merged
    assert merged["kill_rate"] != round(2 / 4, 3)   # the wrong denominator
