"""Tests for the extension/volume fields the competitor teardown called for.

`atr_from_sma50` is the ATR Matrix (Steve Jacobs, learnt from @jfsrev and
@RealSimpleAriel; oratnek uses the same number as both an entry gate and an
exit trigger): how many ATRs the price sits above its 50-day SMA.

`pocket_pivot_count` is factored out of the enrichment loop so the 10-session
window oratnek screens on and the 30-session window we already shipped are one
implementation measured over two lookbacks.

See data/research/screener_competitors_2026-08-17.md.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from pipeline.adapters.yfinance_adapter import pocket_pivot_count
from pipeline.screeners.run_all import compute_universe_scores


def _frame(**over) -> pd.DataFrame:
    """One universe row with everything compute_universe_scores touches."""
    base = {
        "ticker": "T", "close": 100.0, "atr": 3.0,
        "sma20_dist": 0.05, "sma50_dist": 0.10, "sma200_dist": 0.20,
        "market_cap": 5e9, "avg_volume": 5e6, "industry": "Software",
        "perf_1w": 0.02, "perf_1m": 0.05, "perf_3m": 0.10,
        "perf_6m": 0.20, "perf_1y": 0.30, "high_52w": 110.0,
    }
    base.update(over)
    return pd.DataFrame([base])


class TestAtrFromSma50:
    """ATR Matrix = (close - SMA50) / ATR.

    The input we carry is `sma50_dist = (close - SMA50) / SMA50`, verified
    against date-aligned yfinance bars on 2026-08-14 (ANET/NVDA/CORT/PATH/MSFT
    matched to four decimals). So SMA50 = close / (1 + sma50_dist), and the
    numerator is close * dist / (1 + dist) -- NOT close * dist.
    """

    def test_matches_the_direct_computation(self):
        # close 100, dist +10% => SMA50 = 90.909..., gap = 9.0909, ATR 3.
        out = compute_universe_scores(_frame())
        assert out["atr_from_sma50"].iloc[0] == pytest.approx(9.0909 / 3.0, abs=1e-3)

    def test_the_one_plus_dist_denominator_is_not_optional(self):
        """Regression on my own slip: `close * dist / atr` overstates the
        extension by a factor of (1 + dist) -- 30% too high on a name 30%
        above its 50-day line, which is exactly the extended tail the number
        exists to flag."""
        out = compute_universe_scores(_frame(close=100.0, sma50_dist=0.30, atr=3.0))
        naive = 100.0 * 0.30 / 3.0                      # 10.0 -- wrong
        correct = (100.0 * 0.30 / 1.30) / 3.0           # 7.69 -- right
        got = out["atr_from_sma50"].iloc[0]
        assert got == pytest.approx(correct, abs=1e-3)
        assert got != pytest.approx(naive, abs=1e-2)

    def test_below_the_50sma_is_negative(self):
        """Jacobs ignores anything below the SMA50, so the sign has to survive
        -- clamping at zero would hide the half of the universe he discards."""
        out = compute_universe_scores(_frame(sma50_dist=-0.10))
        assert out["atr_from_sma50"].iloc[0] < 0

    def test_missing_atr_yields_null_not_zero(self):
        out = compute_universe_scores(_frame(atr=None))
        assert pd.isna(out["atr_from_sma50"].iloc[0])

    def test_zero_atr_yields_null(self):
        """A halted or one-price name has ATR 0; inf would sort to the top of
        every 'most extended' view and NaN-poison the JSON. Null, exactly."""
        out = compute_universe_scores(_frame(atr=0.0))
        assert pd.isna(out["atr_from_sma50"].iloc[0])

    def test_near_zero_atr_yields_null_not_a_huge_number(self):
        """A name pinned at one price for weeks has an ATR that decays toward
        zero but never reaches it; dividing through gives ~1e5 -- finite, so
        it passes a null filter and tops every extension sort. Anything moving
        under 0.01% of price a day has no measurable range."""
        out = compute_universe_scores(_frame(close=100.0, atr=1e-6, sma50_dist=0.10))
        assert pd.isna(out["atr_from_sma50"].iloc[0])

    def test_dist_of_minus_one_yields_null_not_inf(self):
        """sma50_dist == -1 makes (1 + dist) zero; -inf would reach json.dumps
        as the non-JSON token -Infinity and take the whole file down."""
        out = compute_universe_scores(_frame(sma50_dist=-1.0))
        v = out["atr_from_sma50"].iloc[0]
        assert pd.isna(v)
        # and nothing in the column is ever infinite
        assert not any(math.isinf(x) for x in out["atr_from_sma50"].dropna())

    def test_is_rounded_like_its_siblings(self):
        out = compute_universe_scores(_frame(close=100.0, atr=3.0, sma50_dist=0.10))
        v = out["atr_from_sma50"].iloc[0]
        assert v == round(v, 4)

    def test_agrees_with_the_badge_column(self):
        """atr_enrichment.enrich_with_atr already ships atr_ext on every ticker
        badge. Two columns for one quantity must be one number -- atr_ext used
        to be |dist|*close/atr (unsigned, no (1+dist)) and disagreed with this
        one on 6.2% of names above the line and painted 40.7% of names BELOW
        the line green."""
        from pipeline.screeners.atr_enrichment import enrich_with_atr
        frame = _frame(close=100.0, atr=3.0, sma50_dist=0.30)
        out = compute_universe_scores(frame)
        badge = enrich_with_atr([{"ticker": "T"}], frame)[0]["atr_ext"]
        assert badge == pytest.approx(out["atr_from_sma50"].iloc[0], abs=1e-2)
        # and below the line the badge value is negative, not its mirror image
        frame_dn = _frame(close=100.0, atr=3.0, sma50_dist=-0.30)
        assert enrich_with_atr([{"ticker": "T"}], frame_dn)[0]["atr_ext"] < 0

    def test_missing_sma50_dist_yields_null(self):
        out = compute_universe_scores(_frame(sma50_dist=None))
        assert pd.isna(out["atr_from_sma50"].iloc[0])

    def test_it_is_not_the_old_ratio_column(self):
        """`sma50_r` stays what it always was (close/SMA50) so nothing reading
        it changes meaning; the new column is a different quantity."""
        out = compute_universe_scores(_frame())
        assert out["sma50_r"].iloc[0] == pytest.approx(1.10)
        assert out["atr_from_sma50"].iloc[0] != pytest.approx(1.10)


class TestPocketPivotCount:
    """Green bar whose volume exceeds the highest of the prior 10 bars."""

    def _series(self, n=40, vol=100.0):
        closes = [10.0] * n
        opens = [10.0] * n
        vols = [vol] * n
        return closes, opens, vols

    def test_counts_a_green_bar_on_record_volume(self):
        c, o, v = self._series()
        c[-1], o[-1], v[-1] = 11.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 1

    def test_a_red_bar_on_record_volume_does_not_count(self):
        c, o, v = self._series()
        c[-1], o[-1], v[-1] = 9.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 0

    def test_volume_must_beat_the_prior_ten_not_merely_rise(self):
        c, o, v = self._series()
        v[-5] = 900.0                    # a bigger bar inside the window
        c[-1], o[-1], v[-1] = 11.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 0

    def test_the_lookback_bounds_which_bars_are_examined(self):
        """The whole point of the 10-window: a pivot 20 sessions ago is in the
        30-count and out of the 10-count."""
        c, o, v = self._series()
        c[-20], o[-20], v[-20] = 11.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 0
        assert pocket_pivot_count(c, o, v, lookback=30) == 1

    def test_short_history_returns_none_not_zero(self):
        """Fewer than 11 bars means no bar has ten priors to compare against:
        nothing was examined, so the answer is 'unmeasured', not 'zero'. Every
        other short-history field in the enrichment block emits None."""
        c, o, v = self._series(n=5)
        assert pocket_pivot_count(c, o, v, lookback=10) is None

    def test_bar_ten_is_examined_when_history_is_exactly_eleven(self):
        """Regression: the loop started at index 11, so on an 11-bar history
        the last bar was never examined -- while the same-day pocket_pivot
        flag (vols[-11:-1]) did count it. Two answers to one question."""
        c, o, v = self._series(n=11)
        c[-1], o[-1], v[-1] = 11.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 1

    def test_a_nan_volume_bar_does_not_blank_the_next_ten_sessions(self):
        """Builtin max() over a slice whose FIRST element is NaN returns NaN,
        and `x > NaN` is False -- one missing bar silenced pivots for the ten
        sessions after it."""
        c, o, v = self._series()
        v[-11] = float("nan")
        c[-1], o[-1], v[-1] = 11.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 1

    def test_counts_multiple_pivots_in_the_window(self):
        """The second pivot's volume must EXCEED the first's, because the
        first is inside the second's own prior-ten window. Equal volume is
        not a second pivot -- pivots within ten sessions have to escalate."""
        c, o, v = self._series()
        c[-4], o[-4], v[-4] = 11.0, 10.0, 500.0
        c[-1], o[-1], v[-1] = 11.0, 10.0, 600.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 2

    def test_a_second_pivot_on_equal_volume_does_not_count(self):
        c, o, v = self._series()
        c[-4], o[-4], v[-4] = 11.0, 10.0, 500.0
        c[-1], o[-1], v[-1] = 11.0, 10.0, 500.0
        assert pocket_pivot_count(c, o, v, lookback=10) == 1
