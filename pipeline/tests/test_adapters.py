"""
Integration tests for data adapters.
Tests constants integrity, calculation functions, and adapter interfaces.
"""
import pytest
import pandas as pd
import numpy as np

from pipeline.constants.tickers import STOCK_GROUPS, ALL_TICKERS
from pipeline.constants.leveraged import LEVERAGED_ETFS, get_leveraged_etfs
from pipeline.constants.colors import SECTOR_COLORS, Industries_COLORS, TICKER_TO_SECTOR
from pipeline.adapters.yfinance_adapter import (
    calculate_atr, calculate_sma, calculate_ema, calculate_rrs, calculate_abc_rating
)
from pipeline.adapters.base_adapter import STANDARD_COLUMNS
from pipeline.adapters.utils import parse_pct_string, parse_market_cap


# ── Constants tests ──────────────────────────────────────────────────────────

class TestConstants:
    def test_stock_groups_has_6_groups(self):
        assert len(STOCK_GROUPS) == 6

    def test_stock_groups_expected_keys(self):
        expected = {"Indices", "S&P Style ETFs", "Sel Sectors", "EW Sectors", "Industries", "Countries"}
        assert set(STOCK_GROUPS.keys()) == expected

    def test_all_tickers_count(self):
        # Should have ~144 unique tickers across groups (some duplicates like RSP, IWM)
        assert len(ALL_TICKERS) >= 120

    def test_spy_in_indices(self):
        assert "SPY" in STOCK_GROUPS["Indices"]

    def test_leveraged_etfs_count(self):
        assert len(LEVERAGED_ETFS) >= 48

    def test_get_leveraged_etfs_known(self):
        long, short = get_leveraged_etfs("QQQ")
        assert "TQQQ" in long
        assert "SQQQ" in short

    def test_get_leveraged_etfs_unknown(self):
        long, short = get_leveraged_etfs("NONEXISTENT")
        assert long == []
        assert short == []

    def test_sector_colors_count(self):
        assert len(SECTOR_COLORS) == 14

    def test_industries_colors_count(self):
        assert len(Industries_COLORS) >= 50

    def test_ticker_to_sector_mapping(self):
        assert TICKER_TO_SECTOR["SMH"] == "Information Technology"
        assert TICKER_TO_SECTOR["XBI"] == "Health Care"
        assert TICKER_TO_SECTOR["USO"] == "Commodities"


# ── Utils tests ──────────────────────────────────────────────────────────────

class TestUtils:
    def test_parse_pct_string_positive(self):
        assert parse_pct_string("3.50%") == pytest.approx(0.035)

    def test_parse_pct_string_negative(self):
        assert parse_pct_string("-1.20%") == pytest.approx(-0.012)

    def test_parse_pct_string_none(self):
        assert parse_pct_string(None) is None
        assert parse_pct_string("") is None
        assert parse_pct_string("-") is None

    def test_parse_market_cap_billions(self):
        assert parse_market_cap("1.5B") == 1_500_000_000

    def test_parse_market_cap_millions(self):
        assert parse_market_cap("250M") == 250_000_000

    def test_parse_market_cap_trillions(self):
        assert parse_market_cap("3.2T") == 3_200_000_000_000

    def test_parse_market_cap_none(self):
        assert parse_market_cap(None) == 0.0


# ── Calculation function tests (with synthetic data) ─────────────────────────

def _make_ohlc(n=60, base_price=100.0, volatility=2.0) -> pd.DataFrame:
    """Generate synthetic OHLC data for testing."""
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=n, freq='D')
    closes = base_price + np.cumsum(np.random.randn(n) * volatility)
    highs = closes + np.abs(np.random.randn(n) * volatility * 0.5)
    lows = closes - np.abs(np.random.randn(n) * volatility * 0.5)
    opens = closes + np.random.randn(n) * volatility * 0.3
    volumes = np.random.randint(1_000_000, 10_000_000, n)
    return pd.DataFrame({
        'Open': opens, 'High': highs, 'Low': lows,
        'Close': closes, 'Volume': volumes
    }, index=dates)


class TestCalculations:
    def setup_method(self):
        self.hist = _make_ohlc(60)

    def test_calculate_atr_returns_float(self):
        atr = calculate_atr(self.hist)
        assert atr is not None
        assert isinstance(atr, float)
        assert atr > 0

    def test_calculate_sma_returns_float(self):
        sma = calculate_sma(self.hist, 20)
        assert sma is not None
        assert isinstance(sma, float)

    def test_calculate_ema_returns_float(self):
        ema = calculate_ema(self.hist, 10)
        assert ema is not None
        assert isinstance(ema, float)

    def test_calculate_abc_rating_valid(self):
        abc = calculate_abc_rating(self.hist)
        assert abc in ('A', 'B', 'C', None)

    def test_calculate_rrs_returns_dataframe(self):
        # Use same date index so merge works (RRS requires overlapping dates)
        np.random.seed(42)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=120, freq='D')
        stock = pd.DataFrame({
            'High': 52 + np.random.randn(120), 'Low': 48 + np.random.randn(120),
            'Close': 50 + np.cumsum(np.random.randn(120) * 0.5),
        }, index=dates)
        spy = pd.DataFrame({
            'High': 402 + np.random.randn(120), 'Low': 398 + np.random.randn(120),
            'Close': 400 + np.cumsum(np.random.randn(120) * 0.5),
        }, index=dates)
        result = calculate_rrs(stock, spy)
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert 'RRS' in result.columns
        assert 'rollingRRS' in result.columns
        assert 'RRS_SMA' in result.columns

    def test_calculate_rrs_insufficient_data(self):
        stock = _make_ohlc(5)
        spy = _make_ohlc(5)
        result = calculate_rrs(stock, spy)
        assert result is None

    def test_calculate_atr_short_data(self):
        short = _make_ohlc(3)
        atr = calculate_atr(short)
        # Should still return a value (ewm works with any length)
        assert atr is not None


# ── Schema tests ─────────────────────────────────────────────────────────────

class TestSma40:
    def test_calculate_sma_40(self):
        hist = _make_ohlc(60)
        sma40 = calculate_sma(hist, 40)
        assert sma40 is not None
        assert isinstance(sma40, float)
        # SMA40 should be between SMA20 and SMA50
        sma20 = calculate_sma(hist, 20)
        sma50 = calculate_sma(hist, 50)
        # Just verify it returns a reasonable value (not testing ordering since synthetic data)
        assert sma40 != sma20
        assert sma40 != sma50


# ── Schema tests ─────────────────────────────────────────────────────────────

class TestSchema:
    def test_standard_columns_count(self):
        assert len(STANDARD_COLUMNS) == 24

    def test_standard_columns_required_fields(self):
        assert 'ticker' in STANDARD_COLUMNS
        assert 'close' in STANDARD_COLUMNS
        assert 'atr' in STANDARD_COLUMNS
        assert 'sector' in STANDARD_COLUMNS
