"""Can this auditor report red -- and does it tell stranded from stale?

Two kinds of test, same shape as `test_audit_wiring.py`:

  * POSITIVE CONTROLS -- one per violation class (S1..S4), each building a
    real git repo where the answer is known and asserting we say it.
  * DISCRIMINATION -- the traps that produced a wrong verdict on 2026-09-07,
    each pairing a "looks fine" tree against a "genuinely bad" tree:

      T1  a pathspec matching no blob must RAISE, never read as "clean".
          The zsh draft joined every filename into one pathspec, matched
          nothing, and `git diff --quiet` returned 0 -- ✅ DELIVERED for five
          stranded branches. The failure mode pointed at green.
      T2  main REPLACING the branch's lines must not read as "main is missing
          this". `fix/alex-stockbee-s2-prev-volume` had 8 test lines absent
          from main because main had swapped in a stronger test; "建议合" there
          would have been a regression.
      T3  append-only files, where main holds the branch's lines plus other
          people's, must read as DELIVERED. A symmetric equality test calls
          the three public boxes undelivered forever.

The last test runs against the real repository and asserts only structural
invariants -- it must not pin today's branch list, which changes nightly.
"""

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipeline.tools import audit_stranded as S


def git(repo, *args, **kw):
    p = subprocess.run(("git", "-C", str(repo)) + args,
                       capture_output=True, text=True, **kw)
    assert p.returncode == 0, f"git {args}: {p.stderr}"
    return p.stdout


@pytest.fixture
def repo(tmp_path):
    """A repo with a real `origin/main` remote-tracking ref."""
    up, wc = tmp_path / "up.git", tmp_path / "wc"
    git(tmp_path, "init", "--bare", "-b", "main", str(up))
    git(tmp_path, "clone", str(up), str(wc))
    git(wc, "config", "user.email", "t@t"); git(wc, "config", "user.name", "t")
    (wc / "pipeline" / "tests").mkdir(parents=True)
    (wc / "data" / "research").mkdir(parents=True)
    write(wc, "README.md", "base\n")
    commit(wc, "base")
    git(wc, "push", "-q", "origin", "main")
    git(wc, "fetch", "-q", "origin")
    return wc


def write(wc, path, text):
    f = wc / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)


def commit(wc, msg):
    git(wc, "add", "-A"); git(wc, "commit", "-q", "-m", msg)


def branch_with(wc, name, files, msg="work"):
    git(wc, "checkout", "-q", "-b", name, "origin/main")
    for p, t in files.items():
        write(wc, p, t)
    commit(wc, msg)
    git(wc, "push", "-q", "origin", name)
    git(wc, "checkout", "-q", "main"); git(wc, "fetch", "-q", "origin")
    return f"origin/{name}"


def advance_main(wc, files, msg="main moves"):
    git(wc, "checkout", "-q", "main"); git(wc, "reset", "-q", "--hard", "origin/main")
    for p, t in files.items():
        write(wc, p, t)
    commit(wc, msg)
    git(wc, "push", "-q", "origin", "main"); git(wc, "fetch", "-q", "origin")


def local_branch_with(wc, name, files, msg="work"):
    """Same as branch_with but NEVER pushed -- the fbclock shape."""
    git(wc, "checkout", "-q", "-b", name, "origin/main")
    for p, t in files.items():
        write(wc, p, t)
    commit(wc, msg)
    git(wc, "checkout", "-q", "main")
    return name


def codes(res):
    return sorted({c for c, _ in res["violations"]})


# ---------------------------------------------------------------- positive controls

def test_S1_whitelisted_work_left_to_rot(repo):
    """Undelivered, inside the producer's own authority, older than max-age."""
    branch_with(repo, "night-x", {"pipeline/tests/test_new.py": "def test_a():\n    pass\n"})
    old = datetime.now(timezone.utc) + timedelta(days=30)
    res = S.check(repo, max_age=2.0, now=old)
    assert "S1" in codes(res), res["violations"]


def test_S2_branch_whose_content_already_landed(repo):
    body = "def test_a():\n    pass\n"
    branch_with(repo, "done-x", {"pipeline/tests/test_done.py": body})
    advance_main(repo, {"pipeline/tests/test_done.py": body}, "someone merged it")
    res = S.check(repo)
    assert "S2" in codes(res), res["violations"]
    r = [b for b in res["branches"] if b["branch"].endswith("done-x")][0]
    assert r["delivered"] and r["lines_missing"] == 0


def test_S3_undelivered_outside_the_whitelist_needs_a_human(repo):
    branch_with(repo, "fb-x", {"pipeline/tools/federation_board.py": "import x\nnow()\n"})
    res = S.check(repo)
    assert "S3" in codes(res), res["violations"]


def test_S4_stale_is_not_stranded(repo):
    """Main moved on; the branch's absence is ambiguous, not a merge request."""
    branch_with(repo, "old-x", {"pipeline/tests/test_g.py": "assert grep_the_source()\n"})
    advance_main(repo, {"pipeline/tests/test_g.py": "assert actually_run_it()\n"},
                 "replace the weak test")
    res = S.check(repo)
    assert "S4" in codes(res), res["violations"]
    assert "S1" not in codes(res) and "S3" not in codes(res)


# ---------------------------------------------------------------- discrimination

def test_T1_a_pathspec_matching_nothing_raises_instead_of_saying_clean(repo):
    """The zsh trap: one bogus pathspec must not come back as 'no difference'."""
    br = branch_with(repo, "p-x", {"pipeline/tests/test_a.py": "a\n"})
    base = S._git(repo, "merge-base", "origin/main", br).strip()
    with pytest.raises(S.GitError):
        S.added_lines(repo, base, br, "pipeline/tests/test_a.py\npipeline/tests/test_b.py")
    # and the honest single path still works
    assert S.added_lines(repo, base, br, "pipeline/tests/test_a.py") == ["a"]


def test_T1b_git_diff_quiet_really_does_return_clean_on_a_bogus_path(repo):
    """The trap is in git, not in our imagination -- pin the behaviour."""
    br = branch_with(repo, "q-x", {"pipeline/tests/test_a.py": "a\n"})
    p = subprocess.run(("git", "-C", str(repo), "diff", "--quiet", "origin/main", br,
                        "--", "pipeline/tests/test_a.py\npipeline/tests/test_b.py"),
                       capture_output=True, text=True)
    assert p.returncode == 0, "如果这条断言红了,说明 git 变了,T1 的理由要重写"


def test_T2_main_replacing_the_line_is_not_main_missing_the_line(repo):
    """The direction trap, with the two verdicts required to differ."""
    branch_with(repo, "sup-x", {"pipeline/tests/test_s.py": "assert weak()\n"})
    advance_main(repo, {"pipeline/tests/test_s.py": "assert strong()\n"}, "stronger")
    sup = [b for b in S.check(repo)["branches"] if b["branch"].endswith("sup-x")][0]

    branch_with(repo, "gone-x", {"pipeline/tests/test_never.py": "assert real()\n"})
    gone = [b for b in S.check(repo)["branches"] if b["branch"].endswith("gone-x")][0]

    assert sup["lines_missing"] > 0 and gone["lines_missing"] > 0, "两边都『缺行』"
    assert sup["lines_stranded"] == 0, "被取代的不算真未送到"
    assert gone["lines_stranded"] > 0, "main 没碰过的才算真未送到"
    assert sup["stale_only"] and not gone["stale_only"]


def test_T3_append_only_box_counts_as_delivered(repo):
    """main holds the branch's line PLUS other people's -- that is delivered."""
    write(repo, "Fluxus_Brand/ops/material_inbox.md", "- old\n")
    commit(repo, "box"); git(repo, "push", "-q", "origin", "main"); git(repo, "fetch", "-q", "origin")
    branch_with(repo, "box-x", {"Fluxus_Brand/ops/material_inbox.md": "- old\n- mine\n"})
    advance_main(repo, {"Fluxus_Brand/ops/material_inbox.md": "- old\n- mine\n- theirs\n"},
                 "两个人各追一行")
    r = [b for b in S.check(repo)["branches"] if b["branch"].endswith("box-x")][0]
    assert r["delivered"], f"追加进公箱的行在 main 上，应判已送到: {r}"


def test_archive_branches_are_not_graded(repo):
    branch_with(repo, "archive/old-thing", {"pipeline/tests/test_z.py": "z\n"})
    res = S.check(repo)
    assert not any("archive/" in b["branch"] for b in res["branches"])


def test_whitelist_matches_the_constitution():
    assert S.is_safe_path("pipeline/tools/audit_stranded.py")
    assert S.is_safe_path("pipeline/tests/test_x.py")
    assert S.is_safe_path("data/research/night_reports/2026-09-07.md")
    assert S.is_safe_path("data/reference/incidents/x.md")
    assert not S.is_safe_path("pipeline/tools/federation_board.py")
    assert not S.is_safe_path("pipeline/screeners/run_all.py")
    assert not S.is_safe_path("frontend/src/App.jsx")
    assert not S.is_safe_path("data/reference/DATA_CONTRACTS.md")


# ---------------------------------------------------------------- the real repo

def test_real_repo_reports_a_denominator_and_never_silently_empty():
    """Structural only -- the branch list changes nightly, so pin nothing else.

    ⚠️ Bounded on purpose. Since 2026-09-09 the scan includes local branches,
    and this checkout carries one (`worktree-fluxus-data-art`) with ~96k lines
    across a whole subproject; a full `check()` here costs minutes and would
    put that on every `pytest pipeline/tests` run. Enumeration is the part that
    must hold on the real repo -- the per-line verdicts are covered by the
    fixture tests above, where the answers are known.
    """
    root = Path(__file__).resolve().parents[2]
    if not (root / ".git").exists():
        pytest.skip("not a git checkout")
    pairs = S.enumerate_branches(root)
    assert isinstance(pairs, list)
    names = [b for b, _ in pairs]
    assert len(names) == len(set(names)), f"同一条分支被数了两次: {names}"
    for b, local_only in pairs:
        assert S._git(root, "rev-list", "--count", f"{S.MAIN}..{b}").strip() != "0"
        on_origin = S._git_ok(root, "rev-parse", "--verify", "-q",
                              f"refs/remotes/origin/{b}") is not None
        if local_only:
            assert not b.startswith("origin/") and not on_origin, b
    smallest = sorted(names, key=lambda b: len(S._git(
        root, "log", f"{S.MAIN}..{b}", "--name-only", "--format=").splitlines()))[:3]
    for b in smallest:
        r = S.branch_report(root, b)
        assert r["lines_stranded"] <= r["lines_missing"]
        assert 0.0 <= r["missing_share"] <= 1.0
        assert r["delivered"] == (r["lines_missing"] == 0)
        assert isinstance(r["fast_forwardable"], bool)
        assert r["commits_behind"] >= 0


# ------------------------------------------------- 2026-09-09: the set, and the direction

def test_S5_a_branch_that_was_never_pushed_is_seen_at_all(repo):
    """POSITIVE CONTROL for the hole this check had until 2026-09-09.

    `fix/joe-fbclock-rebased-2026-09-08` sat five nights local-only. The scan
    enumerated `refs/remotes/origin` only, so the auditor written to stop
    exactly that loss reported zero violations about it.
    """
    local_branch_with(repo, "joe-local-x",
                      {"pipeline/tests/test_local.py": "def test_a():\n    pass\n"})
    res = S.check(repo)
    names = [b["branch"] for b in res["branches"]]
    assert "joe-local-x" in names, f"从未推送的分支必须被看见: {names}"
    assert "S5" in codes(res), res["violations"]
    r = [b for b in res["branches"] if b["branch"] == "joe-local-x"][0]
    assert r["local_only"] and r["lines_stranded"] > 0


def test_S5_negative_control_a_pushed_branch_is_not_flagged_unpushed(repo):
    """The other half: pushing it must actually clear S5, not just look tidier."""
    branch_with(repo, "pushed-x", {"pipeline/tests/test_p.py": "def test_a():\n    pass\n"})
    res = S.check(repo)
    r = [b for b in res["branches"] if b["branch"].endswith("pushed-x")][0]
    assert r["local_only"] is False
    assert "S5" not in codes(res), res["violations"]


def test_a_local_branch_with_an_origin_twin_is_not_double_counted(repo):
    """origin/<name> already covers it; counting both inflates every total."""
    branch_with(repo, "twin-x", {"pipeline/tests/test_t.py": "t\n"})
    res = S.check(repo)
    hits = [b for b in res["branches"] if b["branch"].endswith("twin-x")]
    assert len(hits) == 1, [b["branch"] for b in res["branches"]]
    assert hits[0]["branch"] == "origin/twin-x"


def test_fast_forwardable_says_whether_it_can_actually_land(repo):
    """「不在 main 上」和「能合进 main」是两件事,中间隔着一个方向。

    Both branches below are stranded by the same measure. Only one of them can
    be landed with a push, and three mornings of "建议合 y" could not say which.
    """
    branch_with(repo, "ff-x", {"pipeline/tests/test_ff.py": "def test_a():\n    pass\n"})
    ff = [b for b in S.check(repo)["branches"] if b["branch"].endswith("ff-x")][0]
    assert ff["fast_forwardable"] and ff["commits_behind"] == 0

    advance_main(repo, {"README.md": "base\nmain moved\n"}, "main moves on")
    ff2 = [b for b in S.check(repo)["branches"] if b["branch"].endswith("ff-x")][0]
    assert ff2["lines_stranded"] > 0, "还是滞留的 —— 变的只是能不能快进"
    assert not ff2["fast_forwardable"], "main 前进后必须报「需 rebase」"
    assert ff2["commits_behind"] == 1


def test_render_prints_the_landing_verdict(repo):
    branch_with(repo, "r-x", {"pipeline/tests/test_r.py": "def test_a():\n    pass\n"})
    out = S.render(S.check(repo))
    assert "落地：" in out and "可快进" in out, out
    advance_main(repo, {"README.md": "base\nmoved\n"}, "move")
    out2 = S.render(S.check(repo))
    assert "需 rebase" in out2, out2
