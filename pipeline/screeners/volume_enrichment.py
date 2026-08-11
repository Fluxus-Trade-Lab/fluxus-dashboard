"""vol_5d_50d -- five-day average volume over fifty-day average volume.

The screener's volume column (Andy, 2026-08-11, after TSF's Vol Surge). The
construction is TSF's stated one -- mean of the last five sessions' volume
over the mean of the last fifty -- computed from daily bars, not composed
from Finviz ratios: `rel_volume` is today over the THREE-MONTH average, and
rescaling one average into another would be an invented approximation wearing
a measured column's name.

Why a download and not the archive: the universe's `volume` field is a
scrape-time partial (median 0.05% of avg_volume, measured 2026-08-11), so
fifty days of archived universe.json cannot produce a daily-volume average.
The whole-universe yfinance batch is the same fetch the fallback universe
path already relies on; 5,618 names at period=3mo measured ~4 minutes.

Unmeasured stays unmeasured: a name with fewer than fifty sessions of bars
(IPO, halt, vendor gap) gets None, never a ratio over a shorter window --
a 12-day-old listing's "50-day average" does not exist.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# The windows are the column's name. Not tunable knobs -- change these and it
# is a different measurement that must ship under a different name.
NEAR = 5
BASE = 50
_CHUNK = 500


def ratio_from_volumes(vols: pd.Series) -> Optional[float]:
    """vol_5d_50d for one ticker's daily-volume series, or None.

    Requires BASE valid sessions -- the last NEAR of them are the near window,
    so one requirement covers both. Zero-volume base (halted the whole
    stretch) is unmeasurable, not infinite.
    """
    v = vols.dropna()
    if len(v) < BASE:
        return None
    base = float(v.iloc[-BASE:].mean())
    near = float(v.iloc[-NEAR:].mean())
    if base <= 0:
        return None
    return round(near / base, 4)


def fetch_volume_ratios(tickers: Iterable[str], chunk: int = _CHUNK,
                        ) -> Dict[str, Optional[float]]:
    """Batch-download daily volumes and return {ticker: vol_5d_50d | None}.

    Never raises: a failed chunk logs and leaves its tickers as None, because
    the universe build must not die on a vendor hiccup. Total failure returns
    all-None, which the UI already renders as unmeasured.
    """
    import yfinance as yf

    names: List[str] = [t for t in tickers if t]
    out: Dict[str, Optional[float]] = {t: None for t in names}

    for i in range(0, len(names), chunk):
        batch = names[i:i + chunk]
        try:
            df = yf.download(batch, period="3mo", interval="1d",
                             group_by="column", threads=True,
                             progress=False, auto_adjust=False)
        except Exception as e:  # noqa: BLE001 -- vendor errors are data, not bugs
            logger.warning("vol_5d_50d: chunk %d-%d failed: %s", i, i + len(batch), e)
            continue
        if df is None or df.empty:
            continue
        try:
            vol = df['Volume']
        except KeyError:
            continue
        # single-ticker downloads come back unstacked
        if isinstance(vol, pd.Series):
            vol = vol.to_frame(batch[0])
        for t in batch:
            if t in vol.columns:
                out[t] = ratio_from_volumes(vol[t])

    measured = sum(1 for v in out.values() if v is not None)
    logger.info("vol_5d_50d: measured %d / %d tickers", measured, len(names))
    return out


def enrich_universe(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `vol_5d_50d` column to the scored universe, in place."""
    if df.empty or 'ticker' not in df.columns:
        df['vol_5d_50d'] = None
        return df
    ratios = fetch_volume_ratios(df['ticker'].tolist())
    df['vol_5d_50d'] = df['ticker'].map(ratios)
    return df
