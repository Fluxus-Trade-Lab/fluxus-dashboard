"""Tests for flow.delta_approx — moneyness-based delta estimation."""
import pytest
from pipeline.flow.delta_approx import estimate_delta


class TestEstimateDelta:
    def test_atm_call(self):
        d = estimate_delta(5500.0, 5500.0, "C")
        assert d == pytest.approx(0.50)

    def test_atm_put(self):
        d = estimate_delta(5500.0, 5500.0, "P")
        assert d == pytest.approx(-0.50)

    def test_itm_call(self):
        d = estimate_delta(5500.0, 5470.0, "C", bandwidth=30.0)
        assert d == pytest.approx(0.95)

    def test_deep_itm_call_clamped(self):
        d = estimate_delta(5500.0, 5400.0, "C", bandwidth=30.0)
        assert d == pytest.approx(0.95)

    def test_otm_call(self):
        d = estimate_delta(5500.0, 5530.0, "C", bandwidth=30.0)
        assert d == pytest.approx(0.05)

    def test_deep_otm_call_clamped(self):
        d = estimate_delta(5500.0, 5600.0, "C", bandwidth=30.0)
        assert d == pytest.approx(0.05)

    def test_itm_put(self):
        d = estimate_delta(5500.0, 5530.0, "P", bandwidth=30.0)
        assert d == pytest.approx(-0.95)

    def test_otm_put(self):
        d = estimate_delta(5500.0, 5470.0, "P", bandwidth=30.0)
        assert d == pytest.approx(-0.05)

    def test_put_call_parity(self):
        for strike in [5450, 5480, 5500, 5520, 5550]:
            dc = estimate_delta(5500.0, strike, "C")
            dp = estimate_delta(5500.0, strike, "P")
            assert dc - dp == pytest.approx(1.0)

    def test_halfway_from_atm(self):
        d = estimate_delta(5500.0, 5485.0, "C", bandwidth=30.0)
        assert d == pytest.approx(0.75)

    def test_custom_bandwidth(self):
        d = estimate_delta(5500.0, 5490.0, "C", bandwidth=20.0)
        assert d == pytest.approx(0.75)

    def test_zero_bandwidth_defaults(self):
        d = estimate_delta(5500.0, 5500.0, "C", bandwidth=0.0)
        assert d == pytest.approx(0.50)

    def test_negative_bandwidth_defaults(self):
        d = estimate_delta(5500.0, 5500.0, "C", bandwidth=-10.0)
        assert d == pytest.approx(0.50)
