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
import time
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd

logger = logging.getLogger(__name__)

# The windows are the column's name. Not tunable knobs -- change these and it
# is a different measurement that must ship under a different name.
NEAR = 5
BASE = 50

# Transport, not measurement: batch sizes and the pause change how reliably we
# reach the vendor, never what the number means. The retry batch is smaller
# because the misses arrive per-batch, so a smaller batch loses less when one
# is refused.
_CHUNK = 500
_RETRY_CHUNK = 100
_RETRY_PAUSE_S = 20
# What this feed carries on a healthy run: 97.6% on 2026-08-11, against 51.6%
# on the throttled run that put this guard here. Only a log threshold -- it
# gates nothing and enters no calculation.
_EXPECT_COVERAGE = 0.90


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


def _one_pass(names: Sequence[str], out: Dict[str, Optional[float]],
              chunk: int, label: str) -> None:
    """Fill `out` for `names`, in batches. Never raises."""
    import yfinance as yf

    from pipeline.adapters.yahoo_budget import BUDGET

    for i in range(0, len(names), chunk):
        batch = list(names[i:i + chunk])
        BUDGET.before_batch(f"vol_5d_50d {label}")
        try:
            df = yf.download(batch, period="3mo", interval="1d",
                             group_by="column", threads=True,
                             progress=False, auto_adjust=False)
        except Exception as e:  # noqa: BLE001 -- vendor errors are data, not bugs
            logger.warning("vol_5d_50d %s: batch %d-%d failed: %s",
                           label, i, i + len(batch), e)
            BUDGET.note_batch(len(batch), 0, e, f"vol_5d_50d {label}")
            continue
        if df is None or df.empty:
            logger.warning("vol_5d_50d %s: batch %d-%d came back empty",
                           label, i, i + len(batch))
            BUDGET.note_batch(len(batch), 0, None, f"vol_5d_50d {label}")
            continue
        try:
            vol = df['Volume']
        except KeyError:
            BUDGET.note_batch(len(batch), 0, None, f"vol_5d_50d {label}")
            continue
        # single-ticker downloads come back unstacked
        if isinstance(vol, pd.Series):
            vol = vol.to_frame(batch[0])
        got = 0
        for t in batch:
            if t in vol.columns:
                out[t] = ratio_from_volumes(vol[t])
                got += 1
        BUDGET.note_batch(len(batch), got, None, f"vol_5d_50d {label}")


def fetch_volume_ratios(tickers: Iterable[str], chunk: int = _CHUNK,
                        ) -> Dict[str, Optional[float]]:
    """Batch-download daily volumes and return {ticker: vol_5d_50d | None}.

    Two passes, because one is demonstrably not enough. The first cron run of
    this column measured 2,904 of 5,625 against 5,481 the day before, and the
    misses arrived in blocks -- whole 500-name batches at 8/500 and 13/500
    beside neighbours at 486/500. That shape is the vendor throttling a long
    run, not thousands of names simultaneously losing their history, and a
    single pass turns one throttled batch into 500 unmeasured rows.

    So the leftovers go around again in smaller batches after a pause. A name
    that is genuinely dataless (delisted, too new) simply fails twice and
    stays None, which is the honest answer; a throttled one usually lands.

    Never raises: the universe build must not die on a vendor hiccup, and a
    total failure returns all-None, which the UI already draws as unmeasured.
    """
    names: List[str] = [t for t in tickers if t]
    out: Dict[str, Optional[float]] = {t: None for t in names}

    _one_pass(names, out, chunk, "pass 1")

    missing = [t for t in names if out[t] is None]
    if missing:
        logger.info("vol_5d_50d: retrying %d names in smaller batches", len(missing))
        time.sleep(_RETRY_PAUSE_S)
        _one_pass(missing, out, _RETRY_CHUNK, "pass 2")

    measured = sum(1 for v in out.values() if v is not None)
    share = measured / len(names) if names else 0
    logger.info("vol_5d_50d: measured %d / %d tickers (%.1f%%)",
                measured, len(names), share * 100)
    # Loud, because a silent halving is how a column stops meaning anything.
    if share < _EXPECT_COVERAGE:
        logger.warning("vol_5d_50d: coverage %.1f%% is below the %.0f%% the feed "
                       "normally carries -- suspect throttling, not the market",
                       share * 100, _EXPECT_COVERAGE * 100)
    return out


def ratios_from_bars(tickers: Sequence[str],
                     bars: Dict[str, pd.DataFrame],
                     ) -> Dict[str, Optional[float]]:
    """vol_5d_50d for every name whose daily bars we already hold.

    The enrichment pass upstream downloads a year of bars for this same
    universe minutes earlier; fifty sessions of Volume live inside it. A
    name absent from `bars`, or holding a frame without Volume, is simply
    not answered here -- the caller asks the vendor for those.
    """
    out: Dict[str, Optional[float]] = {}
    for t in tickers:
        frame = bars.get(t)
        if frame is None or 'Volume' not in getattr(frame, 'columns', ()):
            continue
        out[t] = ratio_from_volumes(frame['Volume'])
    return out


def enrich_universe(df: pd.DataFrame,
                    bars: Optional[Dict[str, pd.DataFrame]] = None,
                    ) -> pd.DataFrame:
    """Add a `vol_5d_50d` column to the scored universe, in place.

    `bars` is the panel the yfinance enrichment pass just downloaded for this
    same universe. The two paths do not share download parameters -- the
    enrichment pass takes yfinance's auto_adjust default, this module passes
    auto_adjust=False -- so equivalence was measured, not assumed: on a
    200-name random sample (2026-09-04, seed 20260904), 191 names were
    measurable on both paths and all 191 ratios were identical; 9 were
    unmeasurable on both; zero names were answered by one path and not the
    other. Volume is untouched by auto_adjust, so the second download bought
    nothing and cost a full universe sweep -- ~5,600 requests inside the same
    half hour that gets the runner throttled.

    Whatever `bars` cannot answer still goes to the vendor, so a fallback
    universe (built without the enrichment pass) behaves exactly as before.
    """
    if df.empty or 'ticker' not in df.columns:
        df['vol_5d_50d'] = None
        return df

    names: List[str] = df['ticker'].dropna().tolist()
    ratios: Dict[str, Optional[float]] = {}
    if bars:
        ratios = ratios_from_bars(names, bars)
        logger.info("vol_5d_50d: %d / %d names answered from the bars already "
                    "downloaded (no second fetch)", len(ratios), len(names))

    remaining = [t for t in names if t not in ratios]
    if remaining:
        ratios.update(fetch_volume_ratios(remaining))

    df['vol_5d_50d'] = df['ticker'].map(ratios)
    return df
