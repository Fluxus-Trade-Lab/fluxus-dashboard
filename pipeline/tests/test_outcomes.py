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


def _flat_spy(index, level=400.0):
    return pd.DataFrame({'Open': level, 'High': level, 'Low': level,
                         'Close': level}, index=index)


class TestMeasureOutcome:
    def _setup(self):
        """40 warm-up bars at 100 (ATR 2.0), then a known 6-bar excursion."""
        warm_h = [101.0] * 40
        warm_l = [99.0] * 40
        warm_c = [100.0] * 40
        # entry bar opens at 100; over the next 5 bars high hits 110, low hits 96
        fwd_o = [100.0, 104.0, 106.0, 103.0, 105.0]
        fwd_h = [104.0, 107.0, 110.0, 106.0, 108.0]
        fwd_l = [99.0, 103.0, 105.0, 96.0, 104.0]
        fwd_c = [103.0, 106.0, 105.0, 104.0, 107.0]
        bars = _bars(warm_h + fwd_h, warm_l + fwd_l, warm_c + fwd_c,
                     opens=warm_c + fwd_o)
        return bars

    def test_known_excursion_in_r(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index)
        signal_date = bars.index[39].strftime('%Y-%m-%d')   # last warm-up bar
        out = measure_outcome(bars, spy, signal_date, horizons=(5,))
        assert out is not None
        assert out['entry_date'] == bars.index[40].strftime('%Y-%m-%d')
        assert out['entry_open'] == pytest.approx(100.0)
        assert out['atr'] == pytest.approx(2.0, abs=1e-6)
        # close at entry_idx + 5 - 1 = index 44 -> 107.0
        assert out['ret_5'] == pytest.approx(107.0 / 100.0 - 1)
        # SPY flat -> excess equals ret
        assert out['excess_5'] == pytest.approx(out['ret_5'])
        # max high 110 -> (110-100)/2 = 5.0 R ; min low 96 -> (96-100)/2 = -2.0 R
        assert out['mfe_r_5'] == pytest.approx(5.0)
        assert out['mae_r_5'] == pytest.approx(-2.0)

    def test_excess_subtracts_spy(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index).copy()
        # SPY rises 3% from entry date to exit date
        spy.loc[spy.index[40], 'Close'] = 400.0
        spy.loc[spy.index[44], 'Close'] = 412.0
        out = measure_outcome(bars, spy, bars.index[39].strftime('%Y-%m-%d'),
                              horizons=(5,))
        assert out['excess_5'] == pytest.approx(out['ret_5'] - (412.0 / 400.0 - 1))

    def test_none_when_signal_date_absent(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        assert measure_outcome(bars, _flat_spy(bars.index), '1999-01-04',
                               horizons=(5,)) is None

    def test_none_when_insufficient_forward_bars(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index)
        late = bars.index[-2].strftime('%Y-%m-%d')
        assert measure_outcome(bars, spy, late, horizons=(5,)) is None

    def test_none_when_atr_undefined(self):
        from pipeline.research.outcomes import measure_outcome
        short = _bars([101.0] * 12, [99.0] * 12, [100.0] * 12)
        assert measure_outcome(short, _flat_spy(short.index),
                               short.index[2].strftime('%Y-%m-%d'),
                               horizons=(5,)) is None

    def test_none_when_no_next_session(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        last = bars.index[-1].strftime('%Y-%m-%d')
        assert measure_outcome(bars, _flat_spy(bars.index), last,
                               horizons=(5,)) is None

    def test_missing_spy_date_nulls_only_excess(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index).drop(index=bars.index[44])
        out = measure_outcome(bars, spy, bars.index[39].strftime('%Y-%m-%d'),
                              horizons=(5,))
        assert out is not None
        assert out['excess_5'] is None
        assert out['ret_5'] is not None
        assert out['mfe_r_5'] == pytest.approx(5.0)
