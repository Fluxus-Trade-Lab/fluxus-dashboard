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

    def test_all_time_high_volatility_reads_100(self):
        from pipeline.adapters.yfinance_adapter import atr_pctl
        h = self._hist([1.0] * 200 + [20.0] * 5)
        assert atr_pctl(h, 252) == 100.0

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
