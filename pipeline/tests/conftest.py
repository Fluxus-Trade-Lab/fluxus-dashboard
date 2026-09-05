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

import importlib
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


# --------------------------------------------------------------------------
# No unit test may spend real wall-clock time in a backoff.
#
# 2026-09-04: the shared Yahoo limiter (`yahoo_budget`) was wired into
# `fundamentals_store.refresh`, and `TestWallRetry` -- a test whose whole job
# is to wall on purpose -- began sleeping the real ladder: 30s, then 60s, and
# up. The suite stopped finishing. Two unrelated red tests in
# `test_audit_wiring` had been sitting behind that wall unseen, and no
# workflow runs pytest, so nothing said a word.
#
# Neither change was wrong alone. What was missing is this: a module that
# sleeps for real is reachable from unit tests the moment anyone wires it in,
# and the wiring is exactly the kind of edit nobody thinks to test.
#
# The fixture removes the WAIT, never the DECISION to wait: every requested
# duration is recorded, so a test can still assert that a backoff was asked
# for and how long it would have been. Ask for the `slept` fixture to read it.
@pytest.fixture(autouse=True)
def _no_real_backoff_sleeps(monkeypatch, request):
    recorded: list[float] = []

    def _record(seconds):
        recorded.append(float(seconds))

    # Every module that can sleep in a vendor-backoff path. Adding a module
    # here is cheaper than discovering it the way we discovered the second
    # one: a regression test written for the FIRST sleep failed on the
    # SECOND, still 90 seconds long, in the same call stack.
    patched = 0
    for mod_path in ("pipeline.adapters.yahoo_budget",
                     "pipeline.adapters.fundamentals_store"):
        try:
            mod = importlib.import_module(mod_path)
        except ImportError:                # module absent -> nothing to patch
            continue
        # Deliberately NOT `except Exception`: the first version of this loop
        # used one and swallowed a NameError from a missing import, leaving
        # the fixture inert. The `assert patched` below is what made that
        # loud instead of silent -- keep both.
        if not hasattr(mod, "_sleep"):
            raise AssertionError(
                f"{mod_path} has no `_sleep` indirection -- either it lost one "
                "or this list is stale. A silently unpatched module is how the "
                "suite stopped finishing on 2026-09-04.")
        monkeypatch.setattr(mod, "_sleep", _record, raising=True)
        patched += 1
    assert patched, "no backoff module could be patched -- the fixture is inert"
    request.node._recorded_sleeps = recorded
    yield recorded


@pytest.fixture
def slept(_no_real_backoff_sleeps):
    """Seconds the limiter ASKED to sleep, in order. Nothing actually waited."""
    return _no_real_backoff_sleeps


# --------------------------------------------------------------------------
# No unit test may reach the vendor over the network.
#
# Same shape as `_no_real_backoff_sleeps` above, and found the same way. On
# 2026-09-04 `run_all` gained an S&P 500 membership fetch for the index-scoped
# breadth family; `test_run_all_end_to_end` promptly started scraping 26 pages
# of Finviz on every run, taking it from milliseconds to 22 seconds and making
# the suite's total runtime depend on a website being up.
#
# A test that silently talks to a vendor is worse than a slow test: it passes
# or fails on someone else's uptime, and it can be rate-limited by our own
# nightly job. So the default is an empty membership set -- which is exactly
# the "vendor unavailable" path, and the path whose behaviour (NULL columns,
# never a fallback to the whole universe) most needs covering.
#
# A test that wants real membership asks for the `sp500_members` fixture and
# sets it explicitly. Nothing here reaches the network either way.
@pytest.fixture(autouse=True)
def _no_vendor_network(monkeypatch, request):
    box = {"members": set()}

    def _stub(self, index="sp500"):
        return set(box["members"])

    try:
        from pipeline.adapters import finviz_adapter as _fa
    except ImportError:
        yield box
        return
    if not hasattr(_fa.FinvizAdapter, "fetch_index_members"):
        raise AssertionError(
            "FinvizAdapter.fetch_index_members is gone -- either it moved or "
            "this list is stale. An unpatched vendor call is how the suite "
            "started scraping 26 pages per run on 2026-09-04.")
    monkeypatch.setattr(_fa.FinvizAdapter, "fetch_index_members", _stub, raising=True)
    yield box


@pytest.fixture
def sp500_members(_no_vendor_network):
    """Set membership for a test: `sp500_members['members'] = {"AAPL", ...}`."""
    return _no_vendor_network
