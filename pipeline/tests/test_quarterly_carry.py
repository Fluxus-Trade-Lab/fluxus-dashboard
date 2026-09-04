"""Quarterly ticker sections carried forward instead of re-read every night.

earnings_history, quarterly_metrics and analyst change once a quarter. Reading
them nightly costs three yfinance endpoints per tracked ticker -- about a
thousand requests a night -- for numbers that are identical on eighty of those
nights, and it spends them inside the same window that gets the runner
throttled.

The tests that matter here are the refusals: carrying forward the wrong thing
is worse than fetching. A stale stamp, a missing stamp, or a section left
empty by a throttled fetch must all send the caller back to the vendor --
otherwise one bad night freezes into a week of silence.
"""
from datetime import date

import pytest

from pipeline.tickers.ticker_data_fetcher import (
    QUARTERLY_SECTIONS, _quarterly_carry,
)


def _prior(stamp="2026-09-01T00:00:00Z", **over):
    d = {
        "earnings_history": [{"q": "2026Q2", "eps": 1.2}],
        "quarterly_metrics": {"revenue": 1e9},
        "analyst": {"target": 210.0},
        "quarterly_asof": stamp,
    }
    d.update(over)
    return d


TODAY = date(2026, 9, 4)


def test_a_fresh_stamp_is_carried():
    got = _quarterly_carry(_prior(), today=TODAY)
    assert got is not None
    for k in QUARTERLY_SECTIONS:
        assert got[k] == _prior()[k]
    assert got["quarterly_asof"] == "2026-09-01T00:00:00Z"


def test_carried_sections_keep_the_old_stamp_not_today():
    """A file assembled from two nights must say so, or the age is a lie."""
    got = _quarterly_carry(_prior("2026-08-30T00:00:00Z"), today=TODAY)
    assert got["quarterly_asof"] == "2026-08-30T00:00:00Z"


def test_a_stale_stamp_is_refetched():
    assert _quarterly_carry(_prior("2026-08-20T00:00:00Z"), today=TODAY) is None


def test_the_boundary_day_is_still_carried():
    assert _quarterly_carry(_prior("2026-08-28T00:00:00Z"), today=TODAY) is not None


def test_one_day_past_the_boundary_is_refetched():
    assert _quarterly_carry(_prior("2026-08-27T00:00:00Z"), today=TODAY) is None


def test_no_prior_file_means_fetch():
    assert _quarterly_carry(None, today=TODAY) is None
    assert _quarterly_carry({}, today=TODAY) is None


def test_a_file_without_a_stamp_means_fetch():
    """Every file written before this change. They must not be trusted."""
    p = _prior()
    del p["quarterly_asof"]
    assert _quarterly_carry(p, today=TODAY) is None


def test_an_unparseable_stamp_means_fetch():
    assert _quarterly_carry(_prior("last tuesday"), today=TODAY) is None


def test_a_future_stamp_means_fetch():
    """A clock that ran backwards must not buy a section unlimited freshness."""
    assert _quarterly_carry(_prior("2026-12-01T00:00:00Z"), today=TODAY) is None


@pytest.mark.parametrize("empty_key", QUARTERLY_SECTIONS)
def test_an_empty_section_is_refetched(empty_key):
    """The signature of last night's throttled fetch. Never carry it."""
    assert _quarterly_carry(_prior(**{empty_key: None}), today=TODAY) is None
    assert _quarterly_carry(_prior(**{empty_key: []}), today=TODAY) is None


def test_next_earnings_is_not_a_carried_section():
    """It moves, and it is the field an open position acts on."""
    assert "next_earnings" not in QUARTERLY_SECTIONS
