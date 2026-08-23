"""Gates B1/B2/B3 as Stockbee published them -- fixtures are hand-built bars.

The study's numbers are only as good as these three predicates, and each one
has an off-by-one that would not show up in any aggregate: B3 must look at
the days BEFORE the breakout (not including it), B2 must compare the prior
day to bars before the prior day, B1 must read the breakout day itself.
"""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.tools.stockbee_gate_study import arm, gates


def bars(rows):
    """rows = [(open unused, high, low, close)] oldest first."""
    idx = pd.bdate_range("2026-01-01", periods=len(rows))
    return pd.DataFrame(
        {"High": [r[0] for r in rows], "Low": [r[1] for r in rows],
         "Close": [r[2] for r in rows]}, index=idx)


def flat(n, c=100.0):
    return [(c + 0.5, c - 0.5, c)] * n


class TestB3:
    def test_three_up_days_before_breakout_fails(self):
        # ... 97 98 99 100 then the breakout day: c[-1]>c[-2]>c[-3]>c[-4]
        df = bars(flat(10) + [(97.5, 96.5, 97), (98.5, 97.5, 98),
                              (99.5, 98.5, 99), (100.5, 99.5, 100),
                              (105, 100, 105)])
        assert gates(df, len(df) - 1)["B3"] is False

    def test_two_up_days_before_breakout_passes(self):
        df = bars(flat(10) + [(99.5, 98.5, 99), (98.5, 97.5, 98),
                              (99.5, 98.5, 99), (100.5, 99.5, 100),
                              (105, 100, 105)])
        assert gates(df, len(df) - 1)["B3"] is True

    def test_the_breakout_day_itself_is_not_counted(self):
        """A breakout after two up days must pass -- the big up day is day 0,
        not one of the three prior days. Counting it would flip this."""
        df = bars(flat(10) + [(98.5, 97.5, 98), (99.5, 98.5, 99),
                              (100.5, 99.5, 100), (110, 100, 110)])
        assert gates(df, len(df) - 1)["B3"] is True


class TestB2:
    def test_narrow_prior_day_passes(self):
        df = bars([(105, 95, 100)] * 10 + [(100.1, 99.9, 100), (108, 100, 108)])
        assert gates(df, len(df) - 1)["B2"] is True

    def test_wide_up_prior_day_fails(self):
        df = bars([(100.5, 99.5, 100)] * 10 + [(120, 95, 118), (125, 118, 125)])
        assert gates(df, len(df) - 1)["B2"] is False

    def test_negative_prior_day_passes_even_when_wide(self):
        """'narrow range day OR negative bar' -- the OR is his, not ours."""
        df = bars([(100.5, 99.5, 100)] * 10 + [(120, 90, 95), (105, 95, 105)])
        assert gates(df, len(df) - 1)["B2"] is True


class TestB1:
    def test_close_at_high_passes(self):
        df = bars(flat(10) + [(100.5, 99.5, 100), (110, 100, 110)])
        assert gates(df, len(df) - 1)["B1"] is True

    def test_close_at_low_fails(self):
        df = bars(flat(10) + [(100.5, 99.5, 100), (110, 100, 100.5)])
        assert gates(df, len(df) - 1)["B1"] is False

    def test_exactly_on_the_threshold_passes(self):
        df = bars(flat(10) + [(100.5, 99.5, 100), (110, 100, 107)])   # (107-100)/10 = 0.70
        assert gates(df, len(df) - 1)["B1"] is True

    def test_zero_range_day_does_not_divide_by_zero(self):
        df = bars(flat(10) + [(100.5, 99.5, 100), (110, 110, 110)])
        assert gates(df, len(df) - 1)["B1"] is True


class TestGuards:
    def test_too_few_bars_returns_none(self):
        assert gates(bars(flat(5)), 4) is None

    def test_index_past_the_end_returns_none(self):
        df = bars(flat(20))
        assert gates(df, len(df)) is None

    def test_ball_is_the_conjunction(self):
        df = bars(flat(10) + [(100.5, 99.5, 100), (110, 100, 100.5)])   # B1 false
        g = gates(df, len(df) - 1)
        assert g["Ball"] is False and g["B3"] is True


class TestArm:
    def test_arm_is_stable_and_ticker_only(self):
        assert arm("AAPL") == arm("AAPL")
        assert arm("AAPL") in {"discovery", "holdout"}

    def test_split_is_roughly_seventy_thirty(self):
        names = [f"T{i}" for i in range(3000)]
        share = sum(arm(t) == "discovery" for t in names) / len(names)
        assert 0.65 < share < 0.75
