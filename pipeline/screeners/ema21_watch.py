"""21-EMA pullback watchlist -- strong names that have come back to the line.

**What it looks for: an entry inside an existing trend.** Names sitting
between 2% below and 3% above their 20-SMA (a ~90% proxy for the 21-EMA),
filtered to RS bracket 80 and above. The premise is that a leader pulling
back to its rising average is offering a second entry at a place where the
stop is close, which is what makes the position size work.

**What it cannot tell you: whether the trend is still alive.** A name that has
topped passes through this band on its way down and looks exactly like one
pausing on its way up. The screen sees distance from a line, not the
direction the name is travelling through it. That distinction is the entire
trade, and it lives on the chart -- the shape of the pullback, whether volume
dried up into it, whether the low is higher than the last one.

The RS bracket is the guard against the worst version of this: a name still
in the top fifth of the field is less likely to be pulling back for good. It
is a guard, not a guarantee.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# sma20_dist range that approximates "near the 21-EMA".
_SMA20_LOWER = -0.02
_SMA20_UPPER = 0.03

# RS bracket edges (descending).  Stocks with a perf_3m percentile rank
# >= 95 go into the "100" bucket, >= 90 into "95", etc.
_RS_BRACKETS: list[int] = list(range(100, -1, -5))  # 100, 95, 90, ...

# Minimum RS bracket to include in output.
_MIN_RS_BRACKET = 80


def _perf_3m_rs(series: pd.Series) -> pd.Series:
    """Return 0-100 percentile rank of *series* across the universe.

    `na_option="top"`, not `"bottom"`. Pandas names the option by rank
    position, so "bottom" hands every missing value the LARGEST rank -- the
    top of this scale. That is invisible while the feed is complete and
    catastrophic when it is not: on 2026-08-12 the yfinance enrichment left
    23.8% of perf_3m missing, those rows took the top 23.8% of the ranking,
    and no real name could reach past 76.2 -- under the bracket floor of 80,
    so this screener returned zero rows on a perfectly ordinary tape.
    """
    return series.rank(pct=True, na_option="top") * 100


def _bracket_label(rs: float) -> int:
    """Snap a continuous RS value to the nearest 5-point bracket label.

    Examples: 99.3 -> 100, 94.1 -> 95, 80.0 -> 80.
    """
    for bracket in _RS_BRACKETS:
        if rs >= bracket:
            return bracket
    return 0


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """Run the 21-EMA Pullback Watchlist screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``ticker``, ``sma20_dist``,
        ``sma50_dist``, ``sma200_dist``, ``perf_3m``, and ``sector``.

    Returns
    -------
    dict
        ``{'count': N, 'rs_groups': {'100': [...], '95': [...], ...}}``
        where each ticker entry is
        ``{'ticker': str, 'rs': float, 'sma20_dist': float, 'sector': str}``.
    """
    if universe.empty:
        logger.warning("Empty universe passed to ema21_watch screener")
        return {"count": 0, "rs_groups": {}}

    df = universe.copy()

    # Coerce key columns.
    for col in ("sma20_dist", "sma50_dist", "sma200_dist", "perf_3m"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Compute RS (percentile rank on perf_3m, 0-100).
    df["rs"] = _perf_3m_rs(df["perf_3m"])

    # --- Filters ---
    # 1. Near the 21-EMA (proxy: sma20_dist).
    near_ema = (df["sma20_dist"] >= _SMA20_LOWER) & (
        df["sma20_dist"] <= _SMA20_UPPER
    )
    # 2. Uptrend: above both the 50-SMA and 200-SMA.
    uptrend = (df["sma50_dist"] > 0) & (df["sma200_dist"] > 0)

    hits = df.loc[near_ema & uptrend].copy()
    logger.info(
        "ema21_watch: %d / %d stocks near 21-EMA in uptrend",
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
            "sma20_dist": round(float(row["sma20_dist"]), 4),
            "sector": row.get("sector", ""),
        }
        rs_groups.setdefault(label, []).append(entry)

    return {"count": int(len(hits)), "rs_groups": rs_groups}
