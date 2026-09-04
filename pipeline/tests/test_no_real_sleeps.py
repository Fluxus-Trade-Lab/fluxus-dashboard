"""The suite must not be able to spend real time in a vendor backoff.

2026-09-04: wiring `yahoo_budget` into `fundamentals_store.refresh` made
`TestWallRetry` -- a test that walls on purpose -- sleep the real ladder
(30s, 60s, ...). pytest stopped finishing, and two red tests in
`test_audit_wiring` sat unnoticed behind the hang for as long as it lasted.
Nothing caught it because no workflow runs pytest.

These tests pin the fixture that fixes it, and pin the distinction that makes
the fixture safe: the WAIT is removed, the DECISION to wait is preserved and
observable.
"""
import time

import pytest


def test_a_backoff_costs_no_wall_clock_time(slept):
    from pipeline.adapters.yahoo_budget import YahooBudget
    b = YahooBudget()
    for _ in range(40):                        # drive it onto the ladder
        b.note_batch(requested=10, returned=0, label="t")
    t0 = time.monotonic()
    waited = b.before_batch(label="t")
    elapsed = time.monotonic() - t0
    assert elapsed < 1.0, f"the limiter really slept {elapsed:.1f}s"
    assert waited > 0, "it must still report that it held"


def test_the_decision_to_back_off_is_still_observable(slept):
    """Removing the wait must not remove the evidence.

    A fixture that silently made backoff disappear would be worse than the
    hang: the limiter's behaviour would stop being testable at all.
    """
    from pipeline.adapters.yahoo_budget import YahooBudget
    b = YahooBudget()
    for _ in range(40):
        b.note_batch(requested=10, returned=0, label="t")
    b.before_batch(label="t")
    assert slept, "no sleep was requested -- the backoff did not happen"
    assert sum(slept) >= 30, f"first rung of the ladder is 30s, got {slept}"


def test_a_clean_caller_never_asks_to_sleep(slept):
    """Negative control: without refusals there is nothing to record."""
    from pipeline.adapters.yahoo_budget import YahooBudget
    b = YahooBudget()
    b.note_batch(requested=10, returned=10, label="t")
    assert b.before_batch(label="t") == 0.0
    assert slept == []


def test_the_walling_fundamentals_test_finishes_promptly():
    """The exact scenario that hung, as a regression test.

    Guarded by wall-clock so it fails loudly rather than hanging the suite
    again -- a hang is the one failure mode that reports nothing.
    """
    import pipeline.adapters.fundamentals_store as F

    state = {"n": 0, "seen": set()}

    def fetch(t):
        state["n"] += 1
        if t in state["seen"]:
            return {"eps_growth_next_y": 1.0}
        state["seen"].add(t)
        return None if state["n"] > 5 else {"eps_growth_next_y": 1.0}

    t0 = time.monotonic()
    r = F.refresh({}, [f"T{i}" for i in range(60)], budget=60,
                  fetch=fetch, workers=1)
    elapsed = time.monotonic() - t0
    assert elapsed < 10, f"walling took {elapsed:.0f}s -- the limiter is sleeping for real"
    assert r["retries"] == 1
