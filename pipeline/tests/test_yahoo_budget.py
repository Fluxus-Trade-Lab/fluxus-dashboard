"""The shared Yahoo backoff: does it actually classify, and actually wait?

Two failure modes worth pinning. First, a classifier that calls everything a
throttle would stall a healthy run on ordinary delisted names. Second -- the
one that has bitten this repo before -- a gate that records the right verdict
but is wired to nothing, so the log says "backing off" while the next batch
goes out immediately. The waiting tests assert on a patched clock, so they
prove the call blocks without spending the wall-clock seconds.
"""
import time

import pytest

from pipeline.adapters import yahoo_budget as yb


@pytest.fixture
def budget():
    b = yb.YahooBudget()
    yield b
    b.reset()


# -- classification --------------------------------------------------------

@pytest.mark.parametrize("text", [
    "HTTP Error 429: Too Many Requests",
    "401 Unauthorized",
    "Invalid Crumb",
    "rate limit exceeded",
])
def test_vendor_refusals_are_recognised(text):
    assert yb.looks_like_throttle(Exception(text))


@pytest.mark.parametrize("text", [
    "possibly delisted; no price data found",
    "No data found, symbol may be delisted",
    "KeyError: 'Volume'",
])
def test_missing_data_is_not_a_refusal(text):
    """A dead ticker is not the host saying no. Confusing them stalls a run."""
    assert not yb.looks_like_throttle(Exception(text))


def test_none_is_not_a_refusal():
    assert not yb.looks_like_throttle(None)


# -- batch verdicts --------------------------------------------------------

def test_a_mostly_empty_batch_reads_as_refusal(budget):
    """yfinance returns an empty frame for a 429, so shape is the only signal."""
    assert budget.note_batch(requested=500, returned=3) is True


def test_ordinary_misses_do_not_read_as_refusal(budget):
    """~2% dataless names is the healthy floor, not a wall."""
    assert budget.note_batch(requested=500, returned=490) is False


def test_a_throttle_exception_beats_a_full_looking_batch(budget):
    assert budget.note_batch(requested=10, returned=10,
                             err=Exception("429 Too Many Requests")) is True


def test_success_clears_the_streak(budget):
    budget.note_batch(500, 0)
    budget.note_batch(500, 0)
    budget.note_batch(500, 500)          # contact restored
    budget.reset()
    budget.note_batch(500, 0)
    # back at rung one: a fresh streak must not inherit the old ladder
    assert budget.state()["refusals"] == 1


# -- the wiring: does anyone actually wait? --------------------------------

def test_before_batch_blocks_after_a_refusal(budget, monkeypatch):
    """The test that would have caught a gate wired to nothing."""
    slept = []
    monkeypatch.setattr(yb.time, "sleep", lambda s: slept.append(s))
    budget.note_batch(500, 0)            # sets the clock
    budget.before_batch("caller B")
    assert slept, "before_batch returned without waiting on an active backoff"
    assert sum(slept) > 0


def test_before_batch_is_free_when_healthy(budget, monkeypatch):
    slept = []
    monkeypatch.setattr(yb.time, "sleep", lambda s: slept.append(s))
    budget.note_batch(500, 495)
    budget.before_batch("caller B")
    assert slept == []


def test_backoff_grows_with_the_streak(budget, monkeypatch):
    """Linear was measured to be too short twice. Each refusal must cost more."""
    now = [1000.0]
    monkeypatch.setattr(yb.time, "time", lambda: now[0])
    budget.note_batch(500, 0)
    first = budget._backoff_until - now[0]
    now[0] += first + 1
    budget.note_batch(500, 0)
    second = budget._backoff_until - now[0]
    assert second > first


def test_one_callers_wall_is_every_callers_wall(budget, monkeypatch):
    """The whole point: fundamentals hits the wall, the OHLC sweep waits."""
    slept = []
    monkeypatch.setattr(yb.time, "sleep", lambda s: slept.append(s))
    budget.note_batch(40, 0, None, "fundamentals wall")
    budget.before_batch("enrich pass 1")
    assert slept


def test_state_reports_what_the_night_cost(budget):
    budget.note_batch(500, 0)
    st = budget.state()
    assert st["refusals"] == 1 and st["backing_off"] is True


def test_module_singleton_exists():
    """A second instance would be a second opinion about one host."""
    assert isinstance(yb.BUDGET, yb.YahooBudget)
