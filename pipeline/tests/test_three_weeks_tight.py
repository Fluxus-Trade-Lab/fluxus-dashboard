"""IBD's Three Weeks Tight compares each week with the one BEFORE it.

Until 2026-09-04 `wk_tight_3` asked whether three weekly closes fitted inside
one 1.5% band: `(max - min) / last <= 0.015`. That is a different test, and it
fails in the direction that matters. A stock closing +1.4% then +1.4% week
over week satisfies IBD and fails the band -- and a quiet drift up on
shrinking volume is the thing the pattern is named for: holders declining to
take profits after a breakout.

Threshold 1.5% comes from the CAN SLIM chart-pattern sheet on this machine
("3 Tight Closes: closes within 1.5%, vol drops, secondary BP; all BP +10
cents"); IBD's articles say roughly 1%, sometimes up to 1.5%.
"""
import pandas as pd
import pytest

from pipeline.adapters.yfinance_adapter import three_weeks_tight


def weeks(*closes):
    return pd.Series(list(closes),
                     index=pd.date_range("2026-08-07", periods=len(closes), freq="W-FRI"))


class TestPairwiseNotBandwidth:
    def test_the_case_the_old_test_rejected(self):
        """+1.4%, +1.4%: IBD passes it, the band-width version does not."""
        w = weeks(100.0, 101.4, 102.8)
        ok, _ = three_weeks_tight(w)
        assert ok is True
        band = (max(w) - min(w)) / w.iloc[-1]
        assert band > 0.015, "if the band also passes, this test proves nothing"

    def test_flat_closes_pass(self):
        ok, _ = three_weeks_tight(weeks(100.0, 100.5, 100.2))
        assert ok is True

    def test_one_wide_week_fails(self):
        ok, _ = three_weeks_tight(weeks(100.0, 100.5, 104.0))
        assert ok is False

    def test_the_band_is_15_basis_points_of_a_hundred_and_a_half(self):
        """1.5% exactly is inside; a hair more is out."""
        assert three_weeks_tight(weeks(100.0, 101.5, 101.5))[0] is True
        assert three_weeks_tight(weeks(100.0, 101.6, 101.6))[0] is False

    def test_it_compares_adjacent_weeks_not_the_first_one(self):
        """Each step is measured against its own predecessor.

        Two +1.4% steps drift 2.8% from where they started, which a
        first-versus-last test would reject.
        """
        ok, _ = three_weeks_tight(weeks(100.0, 101.4, 102.8))
        assert ok is True
        assert abs(102.8 / 100.0 - 1) > 0.015


class TestBuyPoint:
    def test_it_is_the_highest_of_the_three_weeks_plus_ten_cents(self):
        w = weeks(100.0, 100.5, 100.2)
        h = weeks(101.0, 102.5, 101.8)
        ok, bp = three_weeks_tight(w, h)
        assert ok is True
        assert bp == pytest.approx(102.60)     # 102.5 + 0.10

    def test_no_highs_means_no_buy_point_not_a_guess(self):
        ok, bp = three_weeks_tight(weeks(100.0, 100.5, 100.2))
        assert ok is True and bp is None

    def test_a_failed_pattern_has_no_buy_point(self):
        ok, bp = three_weeks_tight(weeks(100.0, 100.5, 104.0), weeks(101.0, 102.5, 105.0))
        assert ok is False and bp is None


class TestShape:
    def test_two_weeks_is_not_three(self):
        assert three_weeks_tight(weeks(100.0, 100.5))[0] is False

    def test_only_the_last_three_weeks_count(self):
        """A wild quarter followed by three tight weeks still qualifies."""
        ok, _ = three_weeks_tight(weeks(50.0, 90.0, 100.0, 100.5, 100.2))
        assert ok is True

    def test_a_zero_close_does_not_raise(self):
        assert three_weeks_tight(weeks(0.0, 100.0, 100.5))[0] is False
