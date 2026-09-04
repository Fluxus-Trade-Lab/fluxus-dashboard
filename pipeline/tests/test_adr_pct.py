"""ADR% is not ATR%, and the gates on it borrowed a threshold from ADR%.

Until 2026-09-04 `adr_pct` in universe.json was ATR(14)/close*100 -- gap
inclusive, Wilder smoothed, divided by the last close -- published under the
ADR name. The 3.5-10 band it gates on came from Qullamaggie/Stockbee, whose
ADR% is `100 * (mean over 20 bars of High/Low - 1)`: intraday only,
arithmetic, each bar divided by its own low.

Measured before the change, on 400 names sampled across five dollar-volume
bands: ours/theirs had a median of 1.088 and an IQR of 0.146, so no constant
coefficient could reconcile them. At the production gate (>= 3.5), 226 names
passed on our reading against 205 on the standard -- 24 names, 10.6% of
everything that passed, were passing only because the ruler ran long.
"""
import pytest
import pandas as pd
import numpy as np


def _bars(highs, lows):
    return pd.Series([float(x) for x in highs]), pd.Series([float(x) for x in lows])


class TestFormula:
    def test_constant_range_is_exact(self):
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        h, l = _bars([11.0] * 20, [10.0] * 20)
        assert adr_pct_20(h, l) == pytest.approx(10.0)

    def test_each_bar_is_divided_by_its_own_low(self):
        """Not by the last close, and not by a common denominator.

        Two bars with the same absolute range but different price levels must
        contribute differently; if they don't, the denominator is wrong.
        """
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        h = pd.Series([11.0] * 10 + [101.0] * 10)
        l = pd.Series([10.0] * 10 + [100.0] * 10)
        # 10 bars at 10% and 10 bars at 1% -> arithmetic mean 5.5%
        assert adr_pct_20(h, l) == pytest.approx(5.5)

    def test_only_the_last_20_bars_count(self):
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        h = pd.Series([50.0] * 30 + [11.0] * 20)     # ancient wild bars
        l = pd.Series([10.0] * 30 + [10.0] * 20)
        assert adr_pct_20(h, l) == pytest.approx(10.0)

    def test_short_history_is_null_not_a_number(self):
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        h, l = _bars([11.0] * 19, [10.0] * 19)
        assert adr_pct_20(h, l) is None

    def test_nonpositive_low_is_null(self):
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        h, l = _bars([11.0] * 20, [10.0] * 19 + [0.0])
        assert adr_pct_20(h, l) is None


class TestNotTheSameAsATR:
    """Positive control for the whole change.

    If ADR% and ATR% agreed on gapping bars, swapping the formula would have
    been cosmetic and none of the gate movement below would be real.
    """

    def _atr_pct(self, h, l, c, n=14):
        pc = c.shift()
        tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
        return float(tr.ewm(alpha=1 / n, adjust=False).mean().iloc[-1] / c.iloc[-1] * 100)

    def test_a_gapping_series_reads_far_higher_under_ATR(self):
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        # Quiet 1% intraday ranges, but the price alternates between two
        # levels overnight -- exactly the MNST 2026-07 shape, where the
        # vendor's split adjustment left half the bars on the wrong scale.
        lvl = [50.0, 100.0] * 15
        l = pd.Series(lvl)
        h = l * 1.01
        c = (h + l) / 2
        adr = adr_pct_20(h, l)
        atr = self._atr_pct(h, l, c)
        assert adr == pytest.approx(1.0, abs=0.01)   # intraday truth
        assert atr > 20                              # gaps dominate
        # Real measured instance: MNST on 2026-09-03 read 13.22 our way and
        # 2.37 the standard way, on bars that oscillated $48 <-> $94.

    def test_they_agree_when_there_are_no_gaps(self):
        """Same bars, no overnight moves: the two must converge.

        Guards against 'they differ' passing for the wrong reason -- if this
        fails, the difference above is not about gaps at all.
        """
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        n = 60
        l = pd.Series([100.0] * n)
        h = pd.Series([101.0] * n)
        c = pd.Series([100.5] * n)          # every close inside its own bar
        adr = adr_pct_20(h, l)
        atr = self._atr_pct(h, l, c)
        assert abs(adr - atr) < 0.05


class TestMatchesTheOtherImplementation:
    """The repo already had the standard formula in leader_footprint.

    `pipeline/tools/leader_footprint.py` computes
    `((h / l - 1).rolling(20).mean() * 100)` -- correct all along, while the
    published column was ATR%. Two implementations of one quantity drift
    apart silently, so this pins them together as a CI assertion rather than
    a one-off check (the handoff ticket asks for exactly this).
    """

    def test_identical_on_random_bars(self):
        from pipeline.adapters.yfinance_adapter import adr_pct_20
        rng = np.random.default_rng(11)
        for _ in range(25):
            l = pd.Series(rng.uniform(5, 500, 40))
            h = l * (1 + rng.uniform(0.001, 0.15, 40))
            mine = adr_pct_20(h, l)
            theirs = float(((h / l - 1).rolling(20).mean() * 100).iloc[-1])
            assert mine == pytest.approx(theirs, rel=1e-12)
