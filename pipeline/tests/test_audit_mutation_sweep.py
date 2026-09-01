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
