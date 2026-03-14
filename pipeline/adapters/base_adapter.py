"""
Abstract base class for all data adapters.
Defines the unified output schema and interface contract.
Per plan.md §2.2.
"""
from abc import ABC, abstractmethod
import pandas as pd

# Unified output schema — every adapter normalizes to these columns
STANDARD_COLUMNS = [
    'ticker', 'close', 'change_pct',           # Price basics
    'perf_1w', 'perf_1m', 'perf_3m',           # Performance
    'perf_6m', 'perf_1y', 'perf_ytd',
    'sma20_dist', 'sma50_dist', 'sma200_dist', # MA distances (%)
    'atr', 'rel_volume', 'avg_volume', 'volume',# Volume/volatility
    'market_cap', 'sector', 'industry',         # Classification
    'high_52w', 'low_52w',                      # Range
    'eps_growth_next_y',                         # Fundamentals (optional)
    'eps_growth_this_y', 'revenue_growth',
]


class BaseAdapter(ABC):
    """Abstract base for all data adapters. Swap adapters = swap data source."""

    @abstractmethod
    def fetch_universe(self) -> pd.DataFrame:
        """Fetch full stock universe. Returns DataFrame with STANDARD_COLUMNS."""
        pass

    @abstractmethod
    def fetch_etf_data(self, tickers: list[str]) -> pd.DataFrame:
        """Fetch ETF/macro data for specific tickers."""
        pass

    @abstractmethod
    def fetch_ohlc(self, tickers: list[str], period: str = '90d') -> dict:
        """Fetch OHLC history for specific tickers. Used by VCP Layer 2."""
        pass

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate output meets schema requirements."""
        missing = set(STANDARD_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        if len(df) < 100:
            raise ValueError(f"Suspiciously few rows: {len(df)}")
        return True
