"""Stockbee's 4% scan has three conditions. We were shipping one and a half.

Until 2026-09-04 `bo_count_*` asked for `volume >= 9,000,000 AND change >= 4%`
under a comment calling it "Pradeep's literal rule". The 9M figure is from a
different Stockbee scan (EP 9 Million), where it applies to `maxv65` rather
than to the day's volume; the scan's own liquidity floor is 100,000, and its
range-expansion condition -- `volume > the previous bar's volume` -- was
missing entirely.

The two errors compounded in one direction. A 9M daily floor is true for
essentially every large cap, so the absent expansion condition never bit;
what remained was "the stock rose 4% today". Measured on our 2026-09-03
universe: of names averaging over 9M shares, 98.8% carried a count (median
18); 2M-9M, 73% (median 2); under 2M, 16-25% (median ZERO). The field ranked
stocks by the volume they trade -- in a scan written for small and mid caps.
"""
import numpy as np
import pytest

from pipeline.adapters.yfinance_adapter import breakout_days


def days(closes, volumes):
    return list(breakout_days(closes, volumes))


class TestTheThreeConditions:
    def test_all_three_met_is_a_breakout(self):
        assert days([100, 105], [500_000, 900_000]) == [True]

    def test_a_39_percent_day_is_not(self):
        assert days([100, 103.9], [500_000, 900_000]) == [False]

    def test_exactly_4_percent_counts(self):
        """The rule reads `>= 4`, so the boundary is inside."""
        assert days([100, 104], [500_000, 900_000]) == [True]

    def test_volume_that_did_not_expand_is_not_a_breakout(self):
        """The condition that was missing entirely before 2026-09-04."""
        assert days([100, 105], [900_000, 900_000]) == [False]
        assert days([100, 105], [900_000, 800_000]) == [False]

    def test_the_liquidity_floor_is_100k_not_9m(self):
        """A 500k-share day on a small cap is a breakout. It used to not be."""
        assert days([100, 105], [200_000, 500_000]) == [True]
        assert days([100, 105], [50_000, 99_999]) == [False]


class TestTheOldRuleWasDirectional:
    """Positive control for the whole change.

    If the old and new rules agreed on the names this scan exists to find,
    swapping them would be cosmetic and the measured 98.8%-vs-median-zero
    split could not have happened.
    """

    def test_a_small_cap_burst_was_invisible_and_now_is_not(self):
        closes = [10.0, 10.6]
        volumes = [300_000, 800_000]          # a real expansion, far under 9M
        assert days(closes, volumes) == [True]
        old_rule = (volumes[1] >= 9_000_000) and (closes[1] / closes[0] - 1 >= 0.04)
        assert old_rule is False, "the old rule would have seen this"

    def test_a_mega_cap_drift_up_was_counted_and_now_is_not(self):
        """The other half: 9M is true every day for a large cap, so the old
        rule degenerated to 'rose 4% today' with no expansion required."""
        closes = [100.0, 105.0]
        volumes = [40_000_000, 30_000_000]    # volume FELL
        assert days(closes, volumes) == [False]
        old_rule = (volumes[1] >= 9_000_000) and (closes[1] / closes[0] - 1 >= 0.04)
        assert old_rule is True, "the old rule counted this"


class TestShape:
    def test_output_is_aligned_to_the_bars_after_the_first(self):
        assert len(breakout_days([1, 2, 3, 4], [1e6] * 4)) == 3

    def test_one_bar_or_none_yields_nothing(self):
        assert list(breakout_days([100], [1e6])) == []
        assert list(breakout_days([], [])) == []

    def test_mismatched_lengths_do_not_raise(self):
        assert list(breakout_days([1, 2, 3], [1e6])) == []

    def test_nan_volume_is_not_a_breakout(self):
        """A missing bar must not read as a burst."""
        assert days([100, 105], [500_000, float("nan")]) == [False]

    def test_zero_previous_close_does_not_raise(self):
        out = days([0.0, 105.0], [500_000, 900_000])
        assert out in ([True], [False])       # either verdict, but no crash
