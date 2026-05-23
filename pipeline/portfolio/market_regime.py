"""Classify each calendar day as 'bull' or 'pullback' market regime.

Rule: SPY closes above its 21-period EMA → bull. Otherwise → pullback.
Computed once for the full date range we care about, then looked up by date.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import pandas as pd

from pipeline.portfolio.ohlc_cache import fetch_ohlc

logger = logging.getLogger(__name__)


class RegimeIndex:
    """Map calendar date → 'bull' or 'pullback'."""

    def __init__(self, regime_series: pd.Series):
        """`regime_series`: pd.Series indexed by date, values 'bull'/'pullback'."""
        # Convert index to date for clean lookups
        if isinstance(regime_series.index, pd.DatetimeIndex):
            regime_series = regime_series.copy()
            regime_series.index = [ts.date() for ts in regime_series.index]
        self._s = regime_series

    def at(self, d: date) -> Optional[str]:
        """Return 'bull' or 'pullback' for date d, or the nearest prior trading day.

        If d falls on a weekend/holiday, walks back up to 5 days to find the most
        recent trading day. Returns None if no data available.
        """
        for offset in range(6):
            try:
                d_lookup = d - pd.Timedelta(days=offset).to_pytimedelta()
                if d_lookup in self._s.index:
                    return self._s.loc[d_lookup]
            except KeyError:
                continue
        return None


def build_regime_index(start: date, end: date) -> RegimeIndex:
    """Pull SPY OHLC, compute 21EMA, label each day."""
    df = fetch_ohlc('SPY', start, end)
    if df is None or df.empty:
        logger.warning("Could not fetch SPY for regime — defaulting to all-bull")
        # neutral fallback
        idx = pd.date_range(start, end, freq='B')
        return RegimeIndex(pd.Series('bull', index=idx))

    ema21 = df['Close'].ewm(span=21, adjust=False).mean()
    regime = (df['Close'] >= ema21).map(lambda b: 'bull' if b else 'pullback')
    return RegimeIndex(regime)
