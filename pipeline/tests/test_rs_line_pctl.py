"""oratnek's "RS 1M" = self-percentile of the RS line over 21 sessions.
Golden: his 08-17 premarket page, 29 names, all reproduced exactly."""
from pathlib import Path

import pandas as pd
import pytest

from pipeline.adapters.yfinance_adapter import rs_line_pctl

FIX = Path(__file__).parent / "fixtures"


class TestRsLinePctl:
    def test_reproduces_all_29_of_his_numbers(self):
        closes = pd.read_csv(FIX / "oratnek_rs1m_closes_2026-08-14.csv", index_col=0, parse_dates=True)
        his = pd.read_csv(FIX / "oratnek_rs1m_values_2026-08-14.csv", index_col=0)["his_rs_1m"]
        misses = {}
        for t, v in his.items():
            got = round(rs_line_pctl(closes[t], closes["SPY"]))
            if got != v:
                misses[t] = (v, got)
        assert misses == {}, misses

    def test_at_a_one_month_rs_high_is_100_and_at_a_low_is_1_of_21(self):
        idx = pd.bdate_range("2026-01-01", periods=30)
        spy = pd.Series(100.0, index=idx)
        up = pd.Series(range(30), index=idx, dtype=float) + 100
        assert rs_line_pctl(up, spy) == 100.0
        assert rs_line_pctl(-up + 300, spy) == pytest.approx(100 / 21)

    def test_short_history_is_none(self):
        idx = pd.bdate_range("2026-01-01", periods=15)
        assert rs_line_pctl(pd.Series(1.0, index=idx), pd.Series(1.0, index=idx)) is None


class TestAtrPctl:
    """`atr_pctl` is the tightness reading the 2026-08-23 study picked (see its
    docstring). Same self-percentile shape as rs_line_pctl -- these lock the
    shape, not the edge."""

    def _hist(self, ranges):
        """Bars whose true range follows `ranges` (close flat at 100)."""
        import pandas as pd
        n = len(ranges)
        return pd.DataFrame({
            "High": [100 + r / 2 for r in ranges],
            "Low": [100 - r / 2 for r in ranges],
            "Close": [100.0] * n,
        }, index=pd.bdate_range("2024-01-01", periods=n))

    def test_all_time_low_volatility_reads_near_zero(self):
        from pipeline.adapters.yfinance_adapter import atr_pctl
        h = self._hist([5.0] * 200 + [0.05] * 40)      # long calm tail
        v = atr_pctl(h, 252)
        assert v is not None and v < 25, v

    def test_all_time_high_volatility_reads_the_ceiling(self):
        """The most volatile day in the window reads (n-1)/n x 100, not 100.

        The comparator went strict on 2026-09-04 to match the published IV
        Percentile definition -- "the share of days with volatility LOWER than
        today". Today is not lower than itself, so a series at its own maximum
        reads 99.58 on a 238-day window rather than 100. The old `<=` put the
        floor at 1/n instead of 0 and the ceiling at exactly 100, which is the
        one thing a percentile of this kind cannot be.
        """
        from pipeline.adapters.yfinance_adapter import atr_pctl
        h = self._hist([1.0] * 200 + [20.0] * 5)
        v = atr_pctl(h, 252)
        assert v is not None and 99.0 < v < 100.0, v

    def test_shorter_window_can_disagree_with_the_long_one(self):
        """The whole point of carrying both: quiet vs the quarter, loud vs the
        year is a real state, not a bug (P on 2026-08-21: 63d=8, 252d=41)."""
        from pipeline.adapters.yfinance_adapter import atr_pctl
        h = self._hist([1.0] * 120 + [12.0] * 60 + [6.0] * 20)
        assert atr_pctl(h, 63) < atr_pctl(h, 252)

    def test_too_little_history_returns_none(self):
        from pipeline.adapters.yfinance_adapter import atr_pctl
        assert atr_pctl(self._hist([2.0] * 30), 252) is None

    def test_is_a_self_percentile_not_a_price_level(self):
        """Doubling every price leaves the reading unchanged -- it is scale
        free, which is why it travels across names and adr_pct does not."""
        from pipeline.adapters.yfinance_adapter import atr_pctl
        h = self._hist([3.0] * 150 + [1.0] * 30)
        h2 = h * 2
        assert atr_pctl(h, 252) == atr_pctl(h2, 252)


class TestRange5Pctl:
    """`range5_pctl` exists to separate 真压缩 from 「ATR 还没追上价格」 --
    see its docstring. These lock the shape and the separation it enables."""

    def _bars(self, ranges, closes=None):
        import pandas as pd
        n = len(ranges)
        closes = closes or [100.0] * n
        return pd.DataFrame({
            "High": [c + r / 2 for c, r in zip(closes, ranges)],
            "Low": [c - r / 2 for c, r in zip(closes, ranges)],
            "Close": closes,
        }, index=pd.bdate_range("2024-01-01", periods=n))

    def test_quiet_tail_reads_low(self):
        from pipeline.adapters.yfinance_adapter import range5_pctl
        v = range5_pctl(self._bars([6.0] * 200 + [0.2] * 20))
        assert v is not None and v < 20, v

    def test_explosive_tail_reads_the_ceiling(self):
        """At its own max the reading sits just below 100, and TIES DO NOT COUNT.

        Two consequences of the 2026-09-04 strict comparator, both correct and
        both worth pinning. Today is not lower than itself, so a maximum can
        never read exactly 100. And when the tail repeats that maximum -- five
        identical 5-day ranges here -- none of those days counts as "lower",
        so the reading is (n-5)/n rather than (n-1)/n. The published IV
        Percentile behaves the same way; a run of equal days is genuinely not
        evidence that today is more extreme than they were.
        """
        from pipeline.adapters.yfinance_adapter import range5_pctl
        v = range5_pctl(self._bars([1.0] * 200 + [25.0] * 5))
        assert v is not None and 95.0 < v < 100.0, v

    def test_separates_the_two_compressed_states(self):
        """The PURR 2026-08-21 shape: a year of high volatility at a low price,
        a long advance that walks ATR% down, then a 3-bar burst. ATR% still
        ranks mid-pack against its own year while the 5-day range is at its
        yearly max -- one number cannot carry both facts, which is why the
        second field exists."""
        from pipeline.adapters.yfinance_adapter import atr_pctl, range5_pctl
        closes = [30.0] * 120 + [30.0 * 1.012 ** i for i in range(1, 120)] + [128.0, 150.0, 160.0]
        ranges = [3.0] * 120 + [3.0 * 1.012 ** i for i in range(1, 120)] + [25.0, 28.0, 22.0]
        h = self._bars(ranges, closes)
        # >99 rather than ==100: the comparator went strict on 2026-09-04, so
        # a series at its own maximum reads (n-1)/n x 100. The GAP is the
        # point of this test and is untouched by that change.
        assert range5_pctl(h, 252) > 99                # the tape is violent
        assert atr_pctl(h, 252) < 50                   # the ratio says otherwise
        assert range5_pctl(h, 252) - atr_pctl(h, 252) > 40

    def test_too_little_history_returns_none(self):
        from pipeline.adapters.yfinance_adapter import range5_pctl
        assert range5_pctl(self._bars([2.0] * 30)) is None
