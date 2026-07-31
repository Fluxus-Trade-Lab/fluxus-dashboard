"""Per-instance outcome measurement for signal research.

Given one ticker's bars and a signal date, measure what happened next:
forward returns, SPY-relative excess, and maximum favorable/adverse
excursion expressed in ATR-multiples (R) so results read in the same
units as a stop/target framework.

Pure functions only: no I/O, no clock, no network. Insufficient data
returns None rather than raising.
Spec: docs/plans/2026-08-01-sequence-mining-design.md
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import pandas as pd


def atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR aligned to bars.index; first `period` entries are NaN."""
    high, low, close = bars['High'], bars['Low'], bars['Close']
    prev_close = close.shift(1)
    true_range = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Wilder smoothing == EMA with alpha = 1/period; require a full window first
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period + 1).mean()
