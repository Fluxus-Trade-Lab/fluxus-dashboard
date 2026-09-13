"""scripts/vercel_ignore_build.sh decides whether Vercel deploys a push.

The 2026-09-13 case these tests replay: a five-commit push whose last commit
only touched tests. Diffing HEAD^..HEAD saw no product path and skipped the
deploy, so data that had just been stripped of share counts and dollars stayed
live. The base must be the last successful deployment, not the parent commit.
Exit code contract (Vercel): 0 = skip, 1 = build.
"""
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / 'scripts' / 'vercel_ignore_build.sh'


def _git(cwd, *args):
    subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
                        'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'})
    return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=cwd, capture_output=True,
                          text=True).stdout.strip()


def _commit(repo, path, text):
    f = repo / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)
    _git(repo, 'add', '-A')
    return _git(repo, 'commit', '-q', '-m', path)


def _run(repo, previous_sha=None):
    env = {k: v for k, v in os.environ.items() if k != 'VERCEL_GIT_PREVIOUS_SHA'}
    if previous_sha is not None:
        env['VERCEL_GIT_PREVIOUS_SHA'] = previous_sha
    return subprocess.run(['bash', 'scripts/vercel_ignore_build.sh'], cwd=repo, env=env,
                          capture_output=True, text=True).returncode


def _repo(tmp_path):
    repo = tmp_path / 'r'
    repo.mkdir()
    _git(repo, 'init', '-q')
    (repo / 'scripts').mkdir()
    shutil.copy(SCRIPT, repo / 'scripts' / 'vercel_ignore_build.sh')
    deployed = _commit(repo, 'README.md', 'base')
    return repo, deployed


def test_multi_commit_push_whose_last_commit_is_tests_only_still_builds(tmp_path):
    repo, deployed = _repo(tmp_path)
    _commit(repo, 'data/output/trades/X.json', '{"realized_R": 1}')
    _commit(repo, 'pipeline/tests/test_x.py', 'def test(): pass')
    assert _run(repo, previous_sha=deployed) == 1


def test_the_old_parent_commit_rule_would_have_skipped_that_push(tmp_path):
    """Positive control: without the previous-deploy base the same push is skipped."""
    repo, _ = _repo(tmp_path)
    _commit(repo, 'data/output/trades/X.json', '{"realized_R": 1}')
    _commit(repo, 'pipeline/tests/test_x.py', 'def test(): pass')
    assert _run(repo, previous_sha=None) == 0


def test_docs_only_since_last_deploy_skips(tmp_path):
    repo, _ = _repo(tmp_path)
    deployed = _commit(repo, 'data/output/a.json', '{}')
    _commit(repo, 'docs/note.md', 'x')
    _commit(repo, 'data/research/r.md', 'y')
    assert _run(repo, previous_sha=deployed) == 0


def test_unknown_previous_sha_builds(tmp_path):
    repo, _ = _repo(tmp_path)
    _commit(repo, 'docs/note.md', 'x')
    assert _run(repo, previous_sha='0' * 40) == 1


def test_changing_the_ignore_script_itself_builds(tmp_path):
    repo, deployed = _repo(tmp_path)
    script = repo / 'scripts' / 'vercel_ignore_build.sh'
    script.write_text(script.read_text() + '\n# tweak\n')
    _git(repo, 'add', '-A')
    _git(repo, 'commit', '-q', '-m', 'tweak')
    assert _run(repo, previous_sha=deployed) == 1
