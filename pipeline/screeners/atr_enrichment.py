"""ATR Extension Enrichment Layer.

Not a standalone screener — this module adds ``atr_ext`` (ATR extension
from the 50-day SMA) and ``atr_color`` (green / amber / red) fields to
any list of ticker dicts.  It is designed to be called *after* each
screener produces its results so that every ticker badge on the
dashboard carries a visual heat indicator.

ATR Extension = (close - SMA50) / ATR  -- the ATR Matrix. Signed.

    - **below**  (atr_ext <  0):  Under the 50-day line -- Jacobs: ignore.
    - **green**  (atr_ext <= 4):  Near the mean — entry zone.
    - **amber**  (atr_ext <= 6):  Stretched — caution.
    - **red**    (atr_ext >  6):  Over-extended — avoid new entries.

History (2026-08-17): this used to be ``abs(sma50_dist) / (atr / close)``,
which (a) drops the ``(1 + dist)`` that turns a distance-over-SMA50 into a
distance-over-close and (b) drops the sign. On the 2026-08-14 universe that
put 6.2% of names above the line in a different colour band and painted
40.7% of names BELOW the line green. It now shares ``atr_multiple_from_sma50``
with ``run_all.compute_universe_scores`` (column ``atr_from_sma50``) so the
badge and the screener column are one number.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── The ATR Matrix, one implementation ───────────────────────────────
# A name moving under this fraction of its price per day has no measurable
# range: dividing by its ATR gives a huge finite number that tops every
# extension sort. Today's smallest live ATR fraction is ~4e-2; this is well
# below anything real.
_MIN_ATR_FRACTION = 1e-4


def atr_multiple_from_sma50(close, atr, sma50_dist):
    """(close - SMA50) / ATR, from the columns the universe carries.

    Works on scalars or aligned pandas Series. ``sma50_dist`` is
    ``(close - SMA50) / SMA50`` (verified against date-aligned bars on
    2026-08-14), so ``SMA50 = close / (1 + dist)`` and the gap is
    ``close * dist / (1 + dist)``. Dropping that denominator overstates a name
    30% above its line by 30%.

    Returns NaN (never inf) when any input is missing, when ``1 + dist`` is
    not positive (a -100% or corrupted dist), or when ATR is not a positive,
    measurable fraction of price.
    """
    c = pd.to_numeric(pd.Series(close) if not isinstance(close, pd.Series) else close, errors="coerce").astype(float)
    a = pd.to_numeric(pd.Series(atr) if not isinstance(atr, pd.Series) else atr, errors="coerce").astype(float)
    d = pd.to_numeric(pd.Series(sma50_dist) if not isinstance(sma50_dist, pd.Series) else sma50_dist, errors="coerce").astype(float)
    ok = (c > 0) & (a > 0) & ((1.0 + d) > 0) & ((a / c) >= _MIN_ATR_FRACTION)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (c * d / (1.0 + d)) / a
    out = out.where(ok)
    out = out.replace([np.inf, -np.inf], np.nan)
    if isinstance(close, pd.Series):
        return out
    v = float(out.iloc[0])
    return None if not np.isfinite(v) else v


# ── Color thresholds ─────────────────────────────────────────────────
_GREEN_MAX = 4.0
_AMBER_MAX = 6.0


def _classify_color(atr_ext: float | None) -> str:
    """Map an ATR extension value to a traffic-light color."""
    if atr_ext is None:
        return "amber"  # default when data is unavailable
    if atr_ext < 0:
        return "below"  # under the 50-day line: not an entry, not extended
    if atr_ext <= _GREEN_MAX:
        return "green"
    if atr_ext <= _AMBER_MAX:
        return "amber"
    return "red"


def enrich_with_atr(
    tickers: List[Dict[str, Any]],
    universe: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """Add ``atr_ext`` and ``atr_color`` to each ticker dict.

    Parameters
    ----------
    tickers : list[dict]
        List of ticker dicts (must contain at least a ``'ticker'`` key).
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``ticker``, ``atr``,
        ``close``, and ``sma50_dist`` columns.

    Returns
    -------
    list[dict]
        The same list, with ``atr_ext`` (float | None) and
        ``atr_color`` (str) added to each entry.
    """
    if universe.empty or not tickers:
        logger.debug("enrich_with_atr: nothing to enrich")
        return tickers

    # Build a lookup keyed by ticker for fast access
    required_cols = {"ticker", "atr", "close", "sma50_dist"}
    if not required_cols.issubset(universe.columns):
        missing = required_cols - set(universe.columns)
        logger.warning(
            "enrich_with_atr: universe missing columns %s — skipping", missing
        )
        for entry in tickers:
            entry.setdefault("atr_ext", None)
            entry.setdefault("atr_color", "amber")
        return tickers

    lookup: Dict[str, Dict[str, Any]] = {}
    for _, row in universe.iterrows():
        lookup[row["ticker"]] = {
            "atr": row.get("atr"),
            "close": row.get("close"),
            "sma50_dist": row.get("sma50_dist"),
        }

    enriched_count = 0
    for entry in tickers:
        symbol = entry.get("ticker")
        info = lookup.get(symbol)

        if info is None:
            entry["atr_ext"] = None
            entry["atr_color"] = "amber"
            continue

        atr = info["atr"]
        close = info["close"]
        sma50_dist = info["sma50_dist"]

        # One implementation with run_all's atr_from_sma50 column -- signed,
        # (1+dist)-correct, null (never inf) on unmeasurable inputs.
        atr_ext = atr_multiple_from_sma50(close, atr, sma50_dist)
        if atr_ext is not None:
            entry["atr_ext"] = round(atr_ext, 2)
            enriched_count += 1
        else:
            entry["atr_ext"] = None

        entry["atr_color"] = _classify_color(entry["atr_ext"])

    logger.info(
        "enrich_with_atr: enriched %d / %d tickers", enriched_count, len(tickers)
    )

    return tickers
