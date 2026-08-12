"""Tests for completed-session labelling."""

from __future__ import annotations

import datetime as dt

from pipeline.marketcal import MARKET_TZ, last_completed_session


def et(y, m, d, hh, mm=0):
    return dt.datetime(y, m, d, hh, mm, tzinfo=MARKET_TZ)


class TestLastCompletedSession:
    def test_premarket_monday_labels_friday(self):
        """The defect this exists for: a 05:44 ET Monday run scraped Friday's
        close and stamped it Monday, planting 589 rows of Friday's tape under
        2026-08-10 in an append-only archive."""
        assert last_completed_session(et(2026, 8, 10, 5, 44)) == dt.date(2026, 8, 7)

    def test_during_the_session_the_close_has_not_happened(self):
        assert last_completed_session(et(2026, 8, 10, 12, 0)) == dt.date(2026, 8, 7)

    def test_after_the_close_the_session_counts(self):
        assert last_completed_session(et(2026, 8, 10, 16, 1)) == dt.date(2026, 8, 10)
        # The post-close cron fires 17:30-18:30 ET; this is its case.
        assert last_completed_session(et(2026, 8, 11, 18, 8)) == dt.date(2026, 8, 11)

    def test_weekend_rolls_back_to_friday(self):
        assert last_completed_session(et(2026, 8, 9, 13, 0)) == dt.date(2026, 8, 7)

    def test_naive_datetime_is_treated_as_et(self):
        naive = dt.datetime(2026, 8, 10, 5, 44)
        assert last_completed_session(naive) == dt.date(2026, 8, 7)

    def test_jst_evening_is_et_premarket(self):
        """The actual clock the mistake was made on: 18:44 JST Monday."""
        jst = dt.datetime(2026, 8, 10, 18, 44, tzinfo=dt.timezone(dt.timedelta(hours=9)))
        assert last_completed_session(jst) == dt.date(2026, 8, 7)
