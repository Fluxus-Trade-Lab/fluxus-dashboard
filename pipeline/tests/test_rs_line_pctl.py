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
