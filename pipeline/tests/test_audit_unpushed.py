"""Unpushed-work sweep (pipeline/tools/audit_unpushed.py).

Real git repos in tmp_path -- the thing under test is git plumbing, so
faking it would only test the fake. The central case is the one the tool's
own first run got wrong: a branch with no tracking config whose commits are
already on a remote is SAFE, not 247 commits of unpushed work.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pipeline.tools import audit_unpushed as U


def _run(cwd, *args):
    subprocess.run(["git", *args], cwd=str(cwd), check=True,
                   capture_output=True, text=True)


def _commit(repo: Path, name: str):
    (repo / name).write_text(name, encoding="utf-8")
    _run(repo, "add", name)
    _run(repo, "commit", "-m", name)


@pytest.fixture
def pair(tmp_path):
    """A bare 'origin' plus a clone with one pushed commit on main."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _run(origin, "init", "--bare", "-b", "main")
    work = tmp_path / "work"
    _run(tmp_path, "clone", str(origin), "work")
    _run(work, "config", "user.email", "t@t")
    _run(work, "config", "user.name", "t")
    _commit(work, "a")
    _run(work, "push", "-u", "origin", "main")
    return origin, work


def test_clean_worktree_passes(pair):
    _, work = pair
    out = U.run(work, trees=[work])
    assert out["ok"] and out["violations"] == 0
    assert out["worktrees"][0]["unpushed"] == 0


def test_local_only_commit_is_U1(pair):
    _, work = pair
    _commit(work, "b")
    out = U.run(work, trees=[work])
    assert not out["ok"]
    v = out["worktrees"][0]["violations"]
    assert any(x.startswith("U1 1 commit(s) on this disk only") for x in v), v


def test_no_upstream_but_on_a_remote_is_only_a_warning(pair):
    """The false positive the first real run produced: tracking is not safety."""
    _, work = pair
    _commit(work, "b")
    _run(work, "checkout", "-b", "side")
    _commit(work, "c")
    _run(work, "push", "origin", "side")           # pushed, but no -u: no tracking
    rep = U.run(work, trees=[work])["worktrees"][0]
    assert rep["unpushed"] == 0, rep
    assert rep["violations"] == []
    assert any(x.startswith("U2 no upstream configured") for x in rep["warnings"]), rep["warnings"]


def test_ahead_of_upstream_counts_as_unpushed(pair):
    _, work = pair
    _run(work, "checkout", "-b", "side")
    _commit(work, "b")
    _run(work, "push", "-u", "origin", "side")
    _commit(work, "c")                              # ahead of its own upstream
    rep = U.run(work, trees=[work])["worktrees"][0]
    assert rep["unpushed"] == 1
    assert any(x.startswith("U1 1 commit(s)") for x in rep["violations"])


def test_dirty_tracked_file_is_U3_warning_not_violation(pair):
    _, work = pair
    (work / "a").write_text("changed", encoding="utf-8")
    (work / "untracked").write_text("x", encoding="utf-8")
    rep = U.run(work, trees=[work])["worktrees"][0]
    assert rep["dirty"] == 1                        # the untracked file does not count
    assert rep["violations"] == []
    assert any(x.startswith("U3 1 uncommitted") for x in rep["warnings"])


def test_missing_worktree_directory_is_U4(tmp_path):
    rep = U.audit_worktree(tmp_path / "gone")
    assert rep["violations"] == []
    assert any(x.startswith("U4") for x in rep["warnings"])


def test_sweep_covers_every_worktree(pair):
    """The whole point: a session only sees its own tree, this sees the set."""
    _, work = pair
    extra = work.parent / "wt2"
    _run(work, "worktree", "add", str(extra), "-b", "other")
    _commit(extra, "d")                             # the dead work lives HERE
    out = U.run(work)
    assert len(out["worktrees"]) == 2
    assert not out["ok"]
    bad = [r for r in out["worktrees"] if r["violations"]]
    assert len(bad) == 1 and bad[0]["branch"] == "other"
