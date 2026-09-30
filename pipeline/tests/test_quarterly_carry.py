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
    QUARTERLY_SECTIONS, _next_earnings_carry, _quarterly_carry,
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


def test_next_earnings_is_not_a_quarterly_section():
    """It has its own carry rule (date-based, see below), not the
    stamp-age rule the true quarterly sections share."""
    assert "next_earnings" not in QUARTERLY_SECTIONS


# ── next_earnings: carried while its date has not passed (T-1001-04) ───────
#
# `calendarEvents` came back empty for 249/251 tracked tickers on both the
# 2026-09-28 and 2026-09-29 nightly runs -- from the first ticker fetched,
# while quarterly_metrics/analyst/info succeeded the same nights, and the
# identical calls for the identical tickers succeed when re-run outside the
# runner. That is a vendor/runner-side block on one endpoint, not 249
# separate "no earnings data" answers -- so carrying the last known date
# forward (until it passes) is a better failure mode than going blank.

def _prior_ne(ne_date="2026-09-10", asof="2026-09-01T00:00:00Z", **over):
    d = {
        "next_earnings": {"date": ne_date, "revenue_low": 1e9, "revenue_high": 1.1e9},
        "next_earnings_asof": asof,
    }
    d.update(over)
    return d


def test_a_future_date_is_carried():
    got = _next_earnings_carry(_prior_ne("2026-09-10"), today=TODAY)
    assert got is not None
    assert got["next_earnings"] == _prior_ne()["next_earnings"]
    assert got["next_earnings_asof"] == "2026-09-01T00:00:00Z"


def test_todays_date_is_still_carried():
    """The boundary: earnings today have not passed yet."""
    assert _next_earnings_carry(_prior_ne(str(TODAY)), today=TODAY) is not None


def test_a_past_date_is_not_carried():
    """This is the one thing the original no-carry rule protected against:
    an open position must never be told a passed date is still upcoming."""
    assert _next_earnings_carry(_prior_ne("2026-09-01"), today=TODAY) is None


def test_no_prior_next_earnings_means_fetch():
    assert _next_earnings_carry(None, today=TODAY) is None
    assert _next_earnings_carry({}, today=TODAY) is None


def test_an_empty_prior_section_means_fetch():
    assert _next_earnings_carry(_prior_ne(ne_date=None), today=TODAY) is None
    assert _next_earnings_carry({"next_earnings": {}}, today=TODAY) is None


def test_an_unparseable_date_means_fetch():
    assert _next_earnings_carry(_prior_ne("soon"), today=TODAY) is None


def test_a_carry_without_any_stamp_means_fetch():
    """Pre-T-1001-04 files have no next_earnings_asof and no fetched_at
    fallback to borrow from in this fixture -- must not be trusted."""
    p = _prior_ne()
    del p["next_earnings_asof"]
    assert _next_earnings_carry(p, today=TODAY) is None


def test_falls_back_to_fetched_at_when_asof_is_missing():
    """A file written before next_earnings_asof existed still carries `date`,
    dated by the file's own fetched_at."""
    p = _prior_ne()
    del p["next_earnings_asof"]
    p["fetched_at"] = "2026-08-31T00:00:00Z"
    got = _next_earnings_carry(p, today=TODAY)
    assert got is not None
    assert got["next_earnings_asof"] == "2026-08-31T00:00:00Z"
