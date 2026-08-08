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


HORIZONS = (5, 10, 21)


def measure_outcome(bars: pd.DataFrame, spy: pd.DataFrame, signal_date: str,
                    horizons: Sequence[int] = HORIZONS,
                    atr_period: int = 14) -> Optional[Dict[str, Any]]:
    """What happened after `signal_date`. Entry = next session's open.

    Returns None when the instance is unmeasurable (unknown date, no next
    session, undefined ATR, or too few forward bars) — callers count these
    as coverage loss rather than dropping them silently.
    """
    index = bars.index
    dates = index.strftime('%Y-%m-%d')
    matches = (dates == signal_date).nonzero()[0]
    if len(matches) == 0:
        return None
    sig_idx = int(matches[0])
    entry_idx = sig_idx + 1
    max_h = max(horizons)
    if entry_idx >= len(bars) or entry_idx + max_h > len(bars):
        return None

    atr_series = atr(bars, period=atr_period)
    atr_at_signal = atr_series.iloc[sig_idx]
    if pd.isna(atr_at_signal) or atr_at_signal <= 0:
        return None

    entry_open = float(bars['Open'].iloc[entry_idx])
    if entry_open <= 0:
        return None

    spy_dates = spy.index.strftime('%Y-%m-%d')
    spy_close = pd.Series(spy['Close'].values, index=spy_dates)
    entry_date = dates[entry_idx]

    out: Dict[str, Any] = {
        'entry_date': entry_date,
        'entry_open': round(entry_open, 4),
        'atr': round(float(atr_at_signal), 4),
    }

    for h in horizons:
        window = bars.iloc[entry_idx:entry_idx + h]
        exit_date = dates[entry_idx + h - 1]
        ret = float(window['Close'].iloc[-1]) / entry_open - 1
        out[f'ret_{h}'] = round(ret, 6)
        out[f'mfe_r_{h}'] = round((float(window['High'].max()) - entry_open)
                                  / float(atr_at_signal), 4)
        out[f'mae_r_{h}'] = round((float(window['Low'].min()) - entry_open)
                                  / float(atr_at_signal), 4)
        if entry_date in spy_close.index and exit_date in spy_close.index:
            spy_entry = float(spy_close.loc[entry_date])
            spy_exit = float(spy_close.loc[exit_date])
            spy_ret = spy_exit / spy_entry - 1 if spy_entry > 0 else 0.0
            out[f'excess_{h}'] = round(ret - spy_ret, 6)
        else:
            out[f'excess_{h}'] = None

    return out
