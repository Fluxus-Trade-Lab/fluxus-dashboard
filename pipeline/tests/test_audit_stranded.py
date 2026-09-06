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
    """Structural only -- the branch list changes nightly, so pin nothing else."""
    root = Path(__file__).resolve().parents[2]
    if not (root / ".git").exists():
        pytest.skip("not a git checkout")
    res = S.check(root)
    assert res["refs_seen"] > 0, "一个 ref 都没看到 = 我们在对空气打分"
    for r in res["branches"]:
        assert r["lines_stranded"] <= r["lines_missing"]
        assert 0.0 <= r["missing_share"] <= 1.0
        assert r["delivered"] == (r["lines_missing"] == 0)
