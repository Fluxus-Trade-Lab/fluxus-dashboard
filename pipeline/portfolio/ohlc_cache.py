"""Cached yfinance OHLC fetcher.

Per-ticker daily OHLC is stored as parquet at `.cache/ohlc/{TICKER}.pkl`.
Re-runs read from cache instead of refetching. Cache invalidates if the
stored data doesn't cover the requested date range, in which case we
refetch and merge.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

CACHE_DIR = Path('.cache/ohlc')


def _cache_path(ticker: str) -> Path:
    safe = ticker.replace('/', '_').replace('^', '_')
    return CACHE_DIR / f'{safe}.pkl'


def _load_cache(ticker: str) -> Optional[pd.DataFrame]:
    p = _cache_path(ticker)
    if not p.exists():
        return None
    try:
        df = pd.read_pickle(p)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Bad cache for {ticker}: {e} — refetching")
        try:
            p.unlink()
        except OSError:
            pass
        return None


def _save_cache(ticker: str, df: pd.DataFrame) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_pickle(_cache_path(ticker))


def fetch_ohlc(ticker: str, start: date, end: date,
               force_refresh: bool = False) -> Optional[pd.DataFrame]:
    """Return daily OHLC for `ticker` covering [start, end].

    Uses on-disk cache. Refetches only if cached range doesn't cover [start, end].
    Returns None on failure.
    """
    cached = None if force_refresh else _load_cache(ticker)
    need_fetch = True
    if cached is not None and len(cached):
        cached_start = cached.index.min().date()
        cached_end = cached.index.max().date()
        if cached_start <= start and cached_end >= end:
            need_fetch = False

    if not need_fetch:
        # slice to requested range
        mask = (cached.index >= pd.Timestamp(start)) & (cached.index <= pd.Timestamp(end))
        return cached.loc[mask].copy()

    # Fetch with a generous buffer to satisfy future requests
    fetch_start = start - timedelta(days=10)
    fetch_end = end + timedelta(days=5)
    logger.info(f"Fetching {ticker} OHLC {fetch_start}..{fetch_end}")
    try:
        df = yf.download(
            ticker, start=fetch_start, end=fetch_end,
            progress=False, auto_adjust=True, threads=False,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"yfinance fetch failed for {ticker}: {e}")
        return None
    if df is None or df.empty:
        logger.warning(f"yfinance returned empty for {ticker}")
        return None

    # Flatten multi-index columns if yfinance returned them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Keep only the columns we need
    keep = [c for c in ['Open', 'High', 'Low', 'Close', 'Volume'] if c in df.columns]
    df = df[keep].dropna()

    # Merge with existing cache if present, dedup
    if cached is not None:
        merged = pd.concat([cached, df])
        merged = merged[~merged.index.duplicated(keep='last')].sort_index()
        _save_cache(ticker, merged)
        df_to_return = merged
    else:
        _save_cache(ticker, df)
        df_to_return = df

    mask = (df_to_return.index >= pd.Timestamp(start)) & (df_to_return.index <= pd.Timestamp(end))
    return df_to_return.loc[mask].copy()


def warm_cache(tickers: list[str], start: date, end: date) -> dict[str, pd.DataFrame]:
    """Convenience: prefetch a batch of tickers, return ticker → DataFrame."""
    out: dict[str, pd.DataFrame] = {}
    for t in tickers:
        df = fetch_ohlc(t, start, end)
        if df is not None and len(df):
            out[t] = df
    return out
