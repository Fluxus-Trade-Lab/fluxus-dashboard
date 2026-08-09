"""Safety tests for _git_publish (I5): pin to PUBLISH_BRANCH + ff-only pull."""
import subprocess
from datetime import date
from pathlib import Path

from pipeline.gex import engine


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True)


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "gex@test")
    _git(root, "config", "user.name", "gex")
    _git(root, "commit", "-q", "--allow-empty", "-m", "init")
    return root


def _make_bare_origin(bare: Path, source: Path) -> None:
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)],
                   check=True)
    _git(source, "remote", "add", "origin", str(bare))
    _git(source, "push", "-q", "-u", "origin", "main")


def _touch_data(out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text("{}")


def _run_publish(cwd: Path, out_dir: Path, capsys, push=True):
    import os
    old = os.getcwd()
    try:
        os.chdir(cwd)
        engine._git_publish(out_dir, date(2026, 7, 12), push=push)
    finally:
        os.chdir(old)
    return capsys.readouterr().out


def test_commit_is_local_when_on_feature_branch(tmp_path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "checkout", "-q", "-b", "feat/x")
    out = repo / "data" / "gex"
    _touch_data(out, "latest.json")
    log = _run_publish(repo, out, capsys)
    assert "not 'main'" in log and "skipping push" in log
    # commit did land locally on feat/x
    branch_log = subprocess.run(["git", "log", "--oneline", "feat/x"],
                                cwd=repo, capture_output=True, text=True).stdout
    assert "daily gex data 2026-07-12" in branch_log


def test_push_succeeds_when_on_main_and_ff(tmp_path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _make_bare_origin(tmp_path / "origin.git", repo)
    out = repo / "data" / "gex"
    _touch_data(out, "latest.json")
    log = _run_publish(repo, out, capsys)
    assert "skipping push" not in log
    # bare repo should have the new commit
    bare_log = subprocess.run(["git", "log", "--oneline", "main"],
                              cwd=tmp_path / "origin.git",
                              capture_output=True, text=True).stdout
    assert "daily gex data 2026-07-12" in bare_log


def test_refuses_push_when_diverged_from_origin(tmp_path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _make_bare_origin(tmp_path / "origin.git", repo)
    # Second clone commits to origin/main; local repo now behind.
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(tmp_path / "origin.git"),
                    str(other)], check=True)
    _git(other, "config", "user.email", "gex@test")
    _git(other, "config", "user.name", "gex")
    (other / "hello.txt").write_text("hi")
    _git(other, "add", "hello.txt")
    _git(other, "commit", "-q", "-m", "other commit")
    _git(other, "push", "-q", "origin", "main")
    # Now local repo makes its own commit (divergence when local main has a
    # commit origin doesn't, and origin has a commit local doesn't).
    (repo / "local.txt").write_text("local")
    _git(repo, "add", "local.txt")
    _git(repo, "commit", "-q", "-m", "local commit")
    out = repo / "data" / "gex"
    _touch_data(out, "latest.json")
    log = _run_publish(repo, out, capsys)
    assert "not ff" in log and "skipping push" in log
    # commit stays local
    local_log = subprocess.run(["git", "log", "--oneline", "main"], cwd=repo,
                               capture_output=True, text=True).stdout
    assert "daily gex data 2026-07-12" in local_log
    # bare origin did NOT get the gex commit
    bare_log = subprocess.run(["git", "log", "--oneline", "main"],
                              cwd=tmp_path / "origin.git",
                              capture_output=True, text=True).stdout
    assert "daily gex data 2026-07-12" not in bare_log


def test_skips_commit_when_no_changes(tmp_path, capsys):
    repo = _init_repo(tmp_path / "repo")
    out = repo / "data" / "gex"
    out.mkdir(parents=True)  # empty — nothing to add
    log = _run_publish(repo, out, capsys, push=False)
    assert "no data changes" in log
