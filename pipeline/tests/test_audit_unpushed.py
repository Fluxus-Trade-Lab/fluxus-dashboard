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


# ============================================================================
# 2026-09-24（T-0924-11）· 变异测出 30 个点里 16 个活着（14/30 = 47%）。
# 形状和前两夜那两道闸一模一样：性质测过了，**读取端的失败态和 `main()`** 没人看。
# 这道闸的处境还更尴尬一点——它是查「有没有活死在盘上」的那把尺子，
# 而它自己一半的行可以坏掉而没有东西会说话。
# ============================================================================

import json as _json


# ---- ① 读取端：git 说不出话的时候 ------------------------------------------

def test_a_directory_that_is_not_a_repo_is_not_unpushed_work(tmp_path):
    """docstring 写着「a broken worktree must not kill the sweep」——
    不杀死不等于读成有罪。git 一句话都答不上来时，计数必须是 0 而不是 1，
    否则这道闸会对着一个坏掉的目录喊「这里有 1 个 commit 要没了」。
    """
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    rep = U.audit_worktree(plain)
    assert rep["unpushed"] == 0
    assert rep["violations"] == []
    assert rep["branch"] == "(detached)"


def test_tracking_config_pointing_at_a_deleted_remote_branch_is_not_a_violation(pair):
    """真会发生：分支在远端被删了，本地 tracking 配置还留着。

    ⚠️ 这条测试原本是冲着 `a = int(ahead) if ahead.isdigit() else 0` 那个 `else 0` 去的，
    **造不出来**：`@{u}` 一旦答不出名字，`rev-list @{u}..HEAD` 那一句根本不会被执行；
    而 `@{u}` 答得出名字，就意味着远端跟踪 ref 在，rev-list 也答得出数。
    两句 git 是一起成立或一起失败的，那个 `else 0` 因此不可达（2026-09-24 实测）。
    留下这条测的是它**真正**证明的东西：配置指向一个已被删掉的远端分支时，
    这棵树读出来是「没配 tracking」的警告，而不是「有活要没了」的违规。
    """
    _, work = pair
    _run(work, "config", "branch.main.merge", "refs/heads/deleted-on-the-remote")
    rep = U.audit_worktree(work)
    assert rep["upstream"] is None
    assert rep["ahead"] == 0
    assert rep["violations"] == []
    assert any(x.startswith("U2 no upstream configured") for x in rep["warnings"])


def test_the_upstream_is_reported_as_itself_and_as_none_when_absent(pair):
    _, work = pair
    assert U.audit_worktree(work)["upstream"] == "origin/main"
    _run(work, "checkout", "-b", "untracked-branch")
    assert U.audit_worktree(work)["upstream"] is None      # 空串不是「没有」


def test_a_worktree_path_with_a_space_is_read_whole(pair):
    """`worktree list --porcelain` 每行是 `worktree <路径>`，路径里可以有空格。

    maxsplit 从 1 变成 2，这道闸就会去查 `/tmp/a` 而不是 `/tmp/a b/wt`——
    而那个目录不存在，于是它把一棵**活的、装着未推工作的树**报成 U4「目录没了」。
    """
    _, work = pair
    spaced = work.parent / "a tree with spaces"
    _run(work, "worktree", "add", str(spaced), "-b", "spaced")
    assert spaced in U.worktrees(work)


# ---- ② 分级：U1 / U2 / U3 各自的边界 ---------------------------------------

def test_a_clean_tracking_branch_warns_about_nothing(pair):
    """`a and not n` 写成 `a or not n`，干净的树会被挂上「领先 0 个 commit」。"""
    _, work = pair
    rep = U.audit_worktree(work)
    assert rep["ahead"] == 0
    assert rep["warnings"] == [], rep["warnings"]


def test_u1_work_is_not_also_reported_as_u2(pair):
    """U2 的定义是「这些 commit 在别的远端 ref 上」——
    U1 的 commit 哪儿都不在，同一批工作不能既是 U1 又是 U2。"""
    _, work = pair
    _run(work, "checkout", "-b", "side")
    _commit(work, "b")
    _run(work, "push", "-u", "origin", "side")
    _commit(work, "c")
    rep = U.audit_worktree(work)
    assert len(rep["violations"]) == 1 and rep["violations"][0].startswith("U1 1")
    assert rep["warnings"] == [], rep["warnings"]


def test_u3_counts_tracked_changes_only_even_when_untracked_files_outnumber_them(pair):
    """原来那条用了 1 改 1 未跟踪，两种写法都数出 1——**它对这个判据是瞎的**。
    未跟踪的多于已跟踪的，两个数才分得开。"""
    _, work = pair
    (work / "a").write_text("changed", encoding="utf-8")
    (work / "u1").write_text("x", encoding="utf-8")
    (work / "u2").write_text("x", encoding="utf-8")
    rep = U.audit_worktree(work)
    assert rep["dirty"] == 1
    assert any(x.startswith("U3 1 uncommitted") for x in rep["warnings"])


def test_a_missing_directory_reports_nothing_else_about_itself(tmp_path):
    """U4 那条早返回带出去的是一份空报告，不是一份填了数的报告。"""
    rep = U.audit_worktree(tmp_path / "gone")
    assert rep["ahead"] == 0
    assert rep["branch"] is None
    assert len(rep["warnings"]) == 1


def test_the_sweep_totals_are_zero_on_a_clean_repo(pair):
    _, work = pair
    out = U.run(work, trees=[work])
    assert (out["violations"], out["warnings"]) == (0, 0)


# ---- ③ main()：退出码与那一行人读的字（此前一行没测过）---------------------

def test_main_is_green_and_says_clean(pair, capsys):
    _, work = pair
    assert U.main(["--repo", str(work)]) == 0
    out = capsys.readouterr().out
    assert "OK  main" in out
    assert "clean" in out
    assert out.strip().endswith("over 1 worktree(s)")


def test_main_returns_one_and_flags_the_tree_that_holds_the_dying_work(pair, capsys):
    _, work = pair
    _commit(work, "b")
    assert U.main(["--repo", str(work)]) == 1
    out = capsys.readouterr().out
    assert "BAD main" in out
    assert "U1 1 commit(s) on this disk only" in out
    assert "UNPUSHED WORK: 1 violation(s)" in out


def test_main_writes_a_report_that_names_the_worktree(pair, tmp_path):
    _, work = pair
    _commit(work, "b")
    dest = tmp_path / "unpushed.json"
    assert U.main(["--repo", str(work), "--json", str(dest)]) == 1
    payload = _json.loads(dest.read_text())
    assert payload["ok"] is False and payload["violations"] == 1
    assert payload["worktrees"][0]["worktree"] == str(work)
