"""4%+ daily gainers -- who moved today.

**What it looks for: participation.** Every name up 4% or more in a single
session, nothing else asked. It is a census of today's movers, not a
selection of good ones.

**What it cannot tell you.** Nothing about why, and nothing about whether the
move continues. A 4% day is a 4% day whether it is the first thrust out of a
year-long base or a dead-cat bounce on a broken name. There is no volume
requirement here, so a move on no participation looks the same as one on
heavy accumulation -- ``vol_up_gainers`` is the same screen with that filter
added, and is the one to read when you want the move to have a buyer behind
it.

Its real use is aggregate, not individual: the *count* of 4% gainers against
the count of 4% losers is the input to the Stockbee breadth ratio, and that
count says more about the tape than any single row in this list.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# Minimum daily percentage change (as a decimal fraction, e.g. 0.04 = 4 %).
_MIN_CHANGE_PCT = 0.04


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """Run the 4 %+ Gainers screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``ticker``, ``change_pct``,
        ``volume``, and ``sector`` columns.

    Returns
    -------
    dict
        ``{'count': N, 'tickers': [{'ticker', 'change_pct', 'volume', 'sector'}, ...]}``
        sorted by ``change_pct`` descending.
    """
    if universe.empty:
        logger.warning("Empty universe passed to gainers_4pct screener")
        return {"count": 0, "tickers": []}

    df = universe.copy()

    # Ensure numeric types for the filter columns.
    df["change_pct"] = pd.to_numeric(df["change_pct"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    mask = df["change_pct"] >= _MIN_CHANGE_PCT
    gainers = df.loc[mask].sort_values("change_pct", ascending=False)

    logger.info(
        "gainers_4pct: %d / %d stocks gained >= %.0f%%",
        len(gainers),
        len(df),
        _MIN_CHANGE_PCT * 100,
    )

    tickers: List[Dict[str, Any]] = []
    for _, row in gainers.iterrows():
        tickers.append(
            {
                "ticker": row["ticker"],
                "change_pct": round(float(row["change_pct"]), 4),
                "volume": int(row["volume"]) if pd.notna(row["volume"]) else 0,
                "sector": row.get("sector", ""),
            }
        )

    return {"count": len(tickers), "tickers": tickers}
