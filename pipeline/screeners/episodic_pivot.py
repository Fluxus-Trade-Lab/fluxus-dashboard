"""Episodic pivots -- the day the story changed.

**What it looks for: a repricing, not a rally.** A gap of 10% or more on 3x
relative volume, market cap above $500M. The size of the gap is the filter's
whole logic: a move that large overnight is not accumulation, it is the
market marking the name to a different set of facts -- an earnings surprise,
an approval, a contract. The premise is that such a repricing is often the
start of a leg rather than the end of one, because estimates take weeks to
catch up to news that arrived in a night.

**What it cannot tell you: whether the gap holds.** It fires on the open,
before the session has decided anything. A gap that closes red on the day is
the same row in this table as one that never fills. The $500M floor removes
the worst of the noise but not the pattern where the news is real and the
price already reflected all of it.

It also has no memory. A name gapping 10% for the third time this year on a
thesis that has failed twice looks identical to a first-time repricing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# ── Filter thresholds ────────────────────────────────────────────────
_MIN_GAP_PCT = 0.10        # 10 % gap-up
_MIN_REL_VOLUME = 3.0      # 3x average volume
_MIN_MARKET_CAP = 500_000_000  # $500 M


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """Run the Episodic Pivot screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least the columns
        ``change_pct``, ``rel_volume``, ``market_cap``, ``ticker``,
        and ``sector``.

    Returns
    -------
    dict
        ``{'count': N, 'tickers': [{'ticker': str, 'change_pct': float,
        'rel_volume': float, 'market_cap': float, 'sector': str}]}``
        sorted by ``change_pct`` descending.
    """
    if universe.empty:
        logger.warning("Empty universe passed to episodic_pivot screener")
        return {"count": 0, "tickers": []}

    required_cols = {"ticker", "change_pct", "rel_volume", "market_cap", "sector"}
    missing = required_cols - set(universe.columns)
    if missing:
        logger.error("Missing required columns: %s", missing)
        return {"count": 0, "tickers": []}

    df = universe.copy()

    mask = (
        (df["change_pct"] >= _MIN_GAP_PCT)
        & (df["rel_volume"] >= _MIN_REL_VOLUME)
        & (df["market_cap"] >= _MIN_MARKET_CAP)
    )
    filtered = df.loc[mask].sort_values("change_pct", ascending=False)

    logger.info(
        "episodic_pivot: %d / %d stocks pass (gap >= %.0f%%, rvol >= %.1f, mcap >= $%.0fM)",
        len(filtered),
        len(df),
        _MIN_GAP_PCT * 100,
        _MIN_REL_VOLUME,
        _MIN_MARKET_CAP / 1e6,
    )

    tickers: List[Dict[str, Any]] = []
    for _, row in filtered.iterrows():
        tickers.append(
            {
                "ticker": row["ticker"],
                "change_pct": round(float(row["change_pct"]), 4),
                "rel_volume": round(float(row["rel_volume"]), 2),
                "market_cap": float(row["market_cap"]),
                "sector": row.get("sector", ""),
            }
        )

    return {"count": len(tickers), "tickers": tickers}
