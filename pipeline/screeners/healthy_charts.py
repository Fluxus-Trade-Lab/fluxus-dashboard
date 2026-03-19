"""Healthy Charts Screener.

Identifies stocks with technically healthy chart structures:

* Trading above both the 50-SMA and 200-SMA (uptrend).
* Within 5-25 % of the 52-week high (consolidating, not extended).
* Positive 1-month momentum.
* Relative volume >= 0.5 (not a dead ticker).

Results are grouped by RS bracket (100, 95, 90, ...) using the
``perf_3m`` percentile rank, identical to the EMA-21 watchlist.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Distance-from-52-week-high band (expressed as negative fractions).
# A value of -0.10 means the stock is 10 % below its 52W high.
_HIGH52W_LOWER = -0.25  # no more than 25 % below the high
_HIGH52W_UPPER = -0.05  # at least 5 % below the high

# Minimum relative volume to exclude dead tickers.
_MIN_REL_VOLUME = 0.5

# RS bracket edges (descending).
_RS_BRACKETS: list[int] = list(range(100, -1, -5))

# Minimum RS bracket to include in output.
_MIN_RS_BRACKET = 80


def _perf_3m_rs(series: pd.Series) -> pd.Series:
    """Return 0-100 percentile rank of *series* across the universe."""
    return series.rank(pct=True, na_option="bottom") * 100


def _bracket_label(rs: float) -> int:
    """Snap a continuous RS value to the nearest 5-point bracket label."""
    for bracket in _RS_BRACKETS:
        if rs >= bracket:
            return bracket
    return 0


def _compute_high_52w_dist(df: pd.DataFrame) -> pd.Series:
    """Compute the fractional distance from the 52-week high.

    The ``high_52w`` column from Finviz is the raw 52-week-high price.
    We convert it to a relative distance: (close - high_52w) / high_52w,
    which yields a value in (-1, 0] for stocks below their high.

    If ``high_52w`` already looks like a fractional distance (all values
    between -1 and 0), we use it directly.
    """
    h = pd.to_numeric(df["high_52w"], errors="coerce")
    c = pd.to_numeric(df["close"], errors="coerce")

    # Heuristic: if the mean of high_52w is between -1 and 0 it is
    # already a relative distance (pre-computed upstream).
    if h.mean() < 0 and h.mean() > -1:
        return h

    # Otherwise compute from absolute price.
    dist = (c - h) / h.replace(0, np.nan)
    return dist


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """Run the Healthy Charts screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``ticker``, ``close``,
        ``sma50_dist``, ``sma200_dist``, ``high_52w``, ``perf_1m``,
        ``perf_3m``, ``rel_volume``, and ``sector``.

    Returns
    -------
    dict
        ``{'count': N, 'rs_groups': {'100': [...], '95': [...], ...}}``
        where each ticker entry is
        ``{'ticker': str, 'rs': float, 'high_52w_dist': float,
        'perf_1m': float, 'sector': str}``.
    """
    if universe.empty:
        logger.warning("Empty universe passed to healthy_charts screener")
        return {"count": 0, "rs_groups": {}}

    df = universe.copy()

    # Coerce key columns.
    for col in ("sma50_dist", "sma200_dist", "perf_1m", "perf_3m", "rel_volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Compute RS and 52W-high distance.
    df["rs"] = _perf_3m_rs(df["perf_3m"])
    df["high_52w_dist"] = _compute_high_52w_dist(df)

    # --- Filters ---
    uptrend = (df["sma50_dist"] > 0) & (df["sma200_dist"] > 0)
    near_high = (df["high_52w_dist"] >= _HIGH52W_LOWER) & (
        df["high_52w_dist"] <= _HIGH52W_UPPER
    )
    positive_momentum = df["perf_1m"] > 0
    alive = df["rel_volume"] >= _MIN_REL_VOLUME

    mask = uptrend & near_high & positive_momentum & alive
    hits = df.loc[mask].copy()

    logger.info(
        "healthy_charts: %d / %d stocks pass all filters",
        len(hits),
        len(df),
    )

    # Assign bracket labels.
    hits["bracket"] = hits["rs"].apply(_bracket_label)

    # Filter to RS >= _MIN_RS_BRACKET only.
    hits = hits.loc[hits["bracket"] >= _MIN_RS_BRACKET]

    # Build output grouped by RS bracket.
    rs_groups: Dict[str, List[Dict[str, Any]]] = {}
    for _, row in (
        hits.sort_values("rs", ascending=False).iterrows()
    ):
        label = str(int(row["bracket"]))
        entry = {
            "ticker": row["ticker"],
            "rs": round(float(row["rs"]), 2),
            "high_52w_dist": round(float(row["high_52w_dist"]), 4),
            "perf_1m": round(float(row["perf_1m"]), 4),
            "sector": row.get("sector", ""),
        }
        rs_groups.setdefault(label, []).append(entry)

    return {"count": int(len(hits)), "rs_groups": rs_groups}
