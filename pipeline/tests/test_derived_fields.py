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
        """A name pinned at one price has an ATR that decays toward zero but
        never reaches it; dividing through gives a large finite number that
        tops every extension sort. On the 2026-08-14 universe every name with
        ATR under 0.5% of price was a $10 SPAC shell (249 of them, all
        'Shell Companies') or a takeover target pinned to its deal price (AES,
        BYND, OGN...); a 1e-4 floor caught none of them and put nine shells
        in the 'most extended' top 25. The floor is 0.5%."""
        out = compute_universe_scores(_frame(close=10.0, atr=0.002, sma50_dist=0.003))
        assert pd.isna(out["atr_from_sma50"].iloc[0]), "a $10 shell with 0.02% ATR must not be 'extended'"
        out = compute_universe_scores(_frame(close=100.0, atr=0.4, sma50_dist=0.10))
        assert pd.isna(out["atr_from_sma50"].iloc[0]), "0.4% is under the floor"
        out = compute_universe_scores(_frame(close=100.0, atr=0.6, sma50_dist=0.10))
        assert not pd.isna(out["atr_from_sma50"].iloc[0]), "0.6% is a real, if quiet, name"

    def test_vector_path_on_a_mixed_frame(self):
        """Every other test here is one row; a regression in .where alignment
        or the inf replace would pass them all. Five rows, one good, four bad
        in different ways: the good one is right and no bad one is inf."""
        from pipeline.screeners.atr_enrichment import atr_multiple_from_sma50
        df = pd.DataFrame({
            "close": [100.0, 0.0, 100.0, None, 100.0],
            "atr":   [3.0,   3.0, 0.0,   3.0,  "x"],
            "sma50_dist": [0.30, 0.10, 0.10, 0.10, -1.0],
        }, index=[7, 3, 9, 1, 5])          # deliberately unsorted index
        out = atr_multiple_from_sma50(df["close"], df["atr"], df["sma50_dist"])
        assert list(out.index) == [7, 3, 9, 1, 5]
        assert out.loc[7] == pytest.approx((100 * 0.30 / 1.30) / 3.0, abs=1e-6)
        assert out.drop(7).isna().all()
        assert not any(math.isinf(x) for x in out.dropna())

    def test_array_like_inputs_are_not_silently_truncated(self):
        """A list or ndarray is not a scalar; taking the scalar branch would
        return the first element only. Either handle it as a vector or raise."""
        import numpy as np
        from pipeline.screeners.atr_enrichment import atr_multiple_from_sma50
        out = atr_multiple_from_sma50(np.array([100.0, 50.0]), np.array([3.0, 1.0]),
                                      np.array([0.30, 0.10]))
        assert len(out) == 2
        assert out.iloc[1] == pytest.approx((50 * 0.10 / 1.10) / 1.0, abs=1e-6)

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

    def test_levels_form_agrees_with_dist_form(self):
        """The ETF loop has close, atr and SMA50 as levels, not a dist. Its own
        inline formula was the third implementation of this quantity -- and
        the naive one (dist*close/atr), plus a falsy-zero that nulled a name
        sitting exactly on its 50-day. Same helper, same answer, zero is zero."""
        from pipeline.screeners.atr_enrichment import (atr_multiple_from_levels,
                                                       atr_multiple_from_sma50)
        close, atr, sma50 = 100.0, 3.0, 76.923077          # dist = +0.30
        by_levels = atr_multiple_from_levels(close, atr, sma50)
        by_dist = atr_multiple_from_sma50(close, atr, close / sma50 - 1.0)
        assert by_levels == pytest.approx(by_dist, abs=1e-6)
        assert by_levels == pytest.approx((close - sma50) / atr, abs=1e-6)
        assert atr_multiple_from_levels(100.0, 3.0, 100.0) == 0.0     # on the line, not null
        assert atr_multiple_from_levels(100.0, 3.0, None) is None
        assert atr_multiple_from_levels(100.0, 3.0, 0.0) is None      # no SMA50 yet

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

    def test_same_day_flag_agrees_with_the_count_on_nan_and_short_history(self):
        """The enrichment loop's `pocket_pivot` flag is `pocket_pivot_count`
        over the last bar only. Its own inline max() had the NaN bug the
        count fixed, and it said False on <11 bars where the count says
        None -- two answers to one question, again."""
        from pipeline.adapters.yfinance_adapter import pocket_pivot_today
        c, o, v = self._series()
        v[-11] = float("nan")
        c[-1], o[-1], v[-1] = 11.0, 10.0, 500.0
        assert pocket_pivot_today(c, o, v) is True
        assert pocket_pivot_count(c, o, v, lookback=10) == 1
        c, o, v = self._series(n=8)
        assert pocket_pivot_today(c, o, v) is None

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


class TestEma21AtrDist:
    """`ema21_atr_dist` = (close - EMA21) / ATR -- the ATR reading the 21EMA
    Watch preset always meant. Same helper as atr_from_sma50 (same floor,
    same null rules), so the two sides of that preset are one implementation.
    The old `ema21_r` (close/SMA20 ratio) stays untouched."""

    def test_is_close_minus_ema21_over_atr(self):
        out = compute_universe_scores(_frame(close=100.0, atr=2.0, ema21=96.0))
        assert out["ema21_atr_dist"].iloc[0] == pytest.approx(2.0)

    def test_below_the_ema_is_negative(self):
        out = compute_universe_scores(_frame(close=100.0, atr=2.0, ema21=101.0))
        assert out["ema21_atr_dist"].iloc[0] == pytest.approx(-0.5)

    def test_missing_ema21_or_atr_is_null(self):
        assert pd.isna(compute_universe_scores(_frame(ema21=None))["ema21_atr_dist"].iloc[0])
        assert pd.isna(compute_universe_scores(_frame(ema21=96.0, atr=0.0))["ema21_atr_dist"].iloc[0])

    def test_frame_without_an_ema21_column_still_scores(self):
        """The fallback universe path has no ema21: the column must come out
        null, not KeyError the whole scoring step."""
        df = _frame().drop(columns=[c for c in ["ema21"] if c in _frame().columns])
        out = compute_universe_scores(df)
        assert "ema21_atr_dist" in out and pd.isna(out["ema21_atr_dist"].iloc[0])

    def test_old_ratio_column_untouched(self):
        out = compute_universe_scores(_frame(ema21=96.0))
        assert out["ema21_r"].iloc[0] == pytest.approx(1.05)


class TestStockbeeAnticipationInputs:
    """Stockbee's three anticipation scans share one skeleton: a 'has been
    strong' ratio and a 'quiet today' gate (|change| <= 1%, min 3-day volume >
    100k). We carry the three ratios as columns and let a preset combine them
    with VCS. Telechart syntax, verbatim:
        TI65           avgc7/avgc65 > 1.05
        Double Trouble c/minl252  >= 1.8
        MDT            c/avgc126  > 1.19
    """

    def test_ratios_from_bars(self):
        import numpy as np
        from pipeline.adapters.yfinance_adapter import stockbee_ratios
        n = 260
        close = np.linspace(50.0, 100.0, n)                # steady climb
        hist = pd.DataFrame({"Close": close, "Low": close - 1, "Volume": 200_000.0})
        r = stockbee_ratios(hist)
        assert r["ti65"] == pytest.approx(close[-7:].mean() / close[-65:].mean())
        assert r["mdt"] == pytest.approx(close[-1] / close[-126:].mean())
        assert r["min_vol_3d"] == pytest.approx(200_000.0)

    def test_short_history_is_null_not_zero(self):
        from pipeline.adapters.yfinance_adapter import stockbee_ratios
        hist = pd.DataFrame({"Close": [1.0] * 30, "Low": [1.0] * 30, "Volume": [1.0] * 30})
        r = stockbee_ratios(hist)
        assert r["ti65"] is None and r["mdt"] is None       # 65 / 126 bars needed
        assert r["min_vol_3d"] == 1.0                        # 3 bars is enough

    def test_double_trouble_ratio_in_scoring(self):
        """c/minl252 from what we already carry. NOTE the enrichment stores
        low_52w as a FRACTION (close/min(low) - 1: 0.8 = 80% above the low),
        not a price -- an earlier count that divided by it as a price said
        1,675 names; the fraction reading says 303. c_low52w = 1 + low_52w."""
        out = compute_universe_scores(_frame(low_52w=0.8))
        assert out["c_low52w"].iloc[0] == pytest.approx(1.8)
        assert pd.isna(compute_universe_scores(_frame(low_52w=None))["c_low52w"].iloc[0])


class TestLiquidLeader:
    """Course definition (SwingMasterclass M2_L09): ADV >= 2M shares, above the
    50-SMA, RS rank top 20% (we read rs_3m >= 80 on the tradeable percentile).
    A qualification list, not an entry signal."""

    def test_flag(self):
        assert compute_universe_scores(_frame(avg_volume=3e6, sma50_dist=0.05, perf_3m=0.5))["liquid_leader"].iloc[0] in (True, False)

    def test_needs_all_three(self):
        import pandas as pd
        rows = pd.concat([_frame(ticker=f"T{i}", avg_volume=3e6, sma50_dist=0.05, perf_3m=0.01 * i) for i in range(20)], ignore_index=True)
        out = compute_universe_scores(rows)
        top = out.sort_values("rs_3m", ascending=False).iloc[0]
        assert top["liquid_leader"] is True or top["liquid_leader"] == True  # noqa: E712
        low = out.sort_values("rs_3m").iloc[0]
        assert not bool(low["liquid_leader"])
        # under the volume floor -> never
        rows2 = rows.copy(); rows2["avg_volume"] = 1e6
        assert not compute_universe_scores(rows2)["liquid_leader"].any()
        # below the 50-SMA -> never
        rows3 = rows.copy(); rows3["sma50_dist"] = -0.02
        assert not compute_universe_scores(rows3)["liquid_leader"].any()

    def test_missing_inputs_are_false_not_error(self):
        out = compute_universe_scores(_frame(avg_volume=None))
        assert bool(out["liquid_leader"].iloc[0]) is False
