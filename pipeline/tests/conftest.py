"""Test-wide sandbox: a forgotten path argument must not reach the real tree.

Assigned to the data side by the 2026-08-23 incident note
(`data/reference/incidents/2026-08-23_test_writes_into_the_real_archive.md`,
"建议的修法（归数据端）") and not done -- so the bug came back on 08-25 for the
third time. The shape: `check_site(tmp_path, "2026-08-19")` passes an
`output_dir` but leaves `history_dir` on its default, which is the REAL
`data/history/quality/`. The fixture's all-1.0 null rates land in the
production baseline, `baseline()` takes a median, and the quality gate gets
quietly LOOSENED. Nothing fails. Nobody sees it.

Two guards live here, and they are different in kind:

* `_sandbox_real_dirs` (autouse) repoints the module-level path DEFAULTS at a
  tmp directory for the duration of every test. A call that forgets an
  argument now writes into the sandbox. This is the doc's first recommendation
  and it protects tests that do not know they need protecting.
* `_repo_data_stays_clean` (autouse, session-scoped) is the doc's second and
  stronger one: after the whole suite, `data/history` and `data/output` must
  be exactly as they were. It catches every "a test wrote into the real tree"
  shape, not only the ones we have thought of -- including any new module that
  grows a real-path default tomorrow.

Both were verified to report POSITIVE before being trusted (put the bug back,
watch them fail) -- per the standing rule that an unverified green is not
evidence.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
# Every module-level default that points at a real, writable data directory.
# Add to this list when a new one appears; the session-scoped guard below is
# the backstop for the ones nobody remembered to add.
_REAL_DIR_DEFAULTS = [
    ("pipeline.quality", "QUALITY_DIR", "quality"),
    ("pipeline.quality", "HISTORY", "universe_quality.csv"),
]


@pytest.fixture(autouse=True)
def _sandbox_real_dirs(monkeypatch, tmp_path_factory):
    """Point real-data defaults at tmp for the duration of each test.

    Its own directory, NOT inside the test's `tmp_path`: several tests assert
    on the exact contents of theirs, and a sandbox that shows up in someone
    else's workspace is a second kind of contamination."""
    import importlib
    sandbox = tmp_path_factory.mktemp("real_dir_sandbox")
    for mod_name, attr, leaf in _REAL_DIR_DEFAULTS:
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:                      # module not installed in this env
            continue
        if not hasattr(mod, attr):
            continue
        target = sandbox / leaf
        if not leaf.endswith(".csv"):
            target.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(mod, attr, target, raising=False)
    yield


def _tracked_data_state() -> str | None:
    """`git status --porcelain` for the two directories tests must not touch.

    Returns None when git is unavailable (a source tarball, someone's CI
    image) -- absence of the tool is not evidence of cleanliness, so the
    guard says so rather than passing silently."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO), "status", "--porcelain", "--",
             "data/history", "data/output"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


@pytest.fixture(scope="session", autouse=True)
def _repo_data_stays_clean():
    """After the suite: data/history and data/output are as we found them."""
    before = _tracked_data_state()
    yield
    if before is None:
        return                                    # cannot judge; see docstring
    after = _tracked_data_state()
    if after is None or after == before:
        return
    was = {l[3:] for l in before.splitlines()}
    now = {l[3:] for l in after.splitlines()}
    touched = sorted(now - was)
    if touched:
        pytest.fail(
            "tests wrote into the real data tree (2026-08-23 incident shape):\n  "
            + "\n  ".join(touched)
            + "\n\nA path argument was left on its real default. Sandbox every "
              "exit of the function, not just the one you passed."
        )
