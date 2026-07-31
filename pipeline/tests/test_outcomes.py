"""Tests for per-instance outcome measurement."""
import numpy as np
import pandas as pd
import pytest


def _bars(highs, lows, closes, opens=None, end='2026-05-29'):
    n = len(closes)
    idx = pd.bdate_range(end=end, periods=n)
    return pd.DataFrame({
        'Open': opens if opens is not None else closes,
        'High': highs, 'Low': lows, 'Close': closes,
    }, index=idx)


class TestAtr:
    def test_constant_range_gives_that_range(self):
        """Every bar spans exactly 2.0 with no gaps -> ATR converges to 2.0."""
        from pipeline.research.outcomes import atr
        n = 40
        bars = _bars(highs=[101.0] * n, lows=[99.0] * n, closes=[100.0] * n)
        a = atr(bars, period=14)
        assert a.iloc[-1] == pytest.approx(2.0, abs=1e-9)

    def test_first_period_entries_are_nan(self):
        from pipeline.research.outcomes import atr
        bars = _bars(highs=[101.0] * 20, lows=[99.0] * 20, closes=[100.0] * 20)
        a = atr(bars, period=14)
        assert a.iloc[:14].isna().all()
        assert not np.isnan(a.iloc[14])

    def test_true_range_uses_prior_close_gaps(self):
        """A gap up makes TR = high - prior_close, larger than high - low."""
        from pipeline.research.outcomes import atr
        highs = [101.0] * 19 + [120.0]
        lows = [99.0] * 19 + [118.0]
        closes = [100.0] * 19 + [119.0]
        bars = _bars(highs, lows, closes)
        a = atr(bars, period=14)
        prev = atr(bars.iloc[:-1], period=14).iloc[-1]
        # last TR = max(120-118, |120-100|, |118-100|) = 20
        expected = (prev * 13 + 20.0) / 14
        assert a.iloc[-1] == pytest.approx(expected, rel=1e-9)

    def test_short_input_all_nan(self):
        from pipeline.research.outcomes import atr
        bars = _bars(highs=[101.0] * 5, lows=[99.0] * 5, closes=[100.0] * 5)
        assert atr(bars, period=14).isna().all()
