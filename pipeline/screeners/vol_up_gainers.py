"""Volume-confirmed 4%+ gainers -- moves someone had to pay for.

**What it looks for: a move with a buyer behind it.** Up 4%+ on relative
volume of 1.5x or better. The volume condition is doing the work -- price can
travel on nothing, but 50% more volume than usual means size had to be
absorbed, which is the footprint institutional accumulation leaves.

**What it cannot tell you.** Relative volume is measured against the name's
own average, so a normally-dead ticker clears 1.5x on very little real money.
Read the dollar volume, not the multiple, before treating a hit as
institutional. It also cannot distinguish accumulation from distribution: a
high-volume 4% day into a resistance level that has already rejected the name
four times scores identically to a clean breakout.

One day of confirmation is not a trend. This finds the day; whether it starts
anything is a chart question.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# Minimum daily percentage change (decimal fraction).
_MIN_CHANGE_PCT = 0.04

# Minimum relative volume (current volume / average volume).
_MIN_REL_VOLUME = 1.5


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """Run the Volume-Confirmed Gainers screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``ticker``, ``change_pct``,
        ``rel_volume``, ``volume``, and ``sector`` columns.

    Returns
    -------
    dict
        ``{'count': N, 'tickers': [{'ticker', 'change_pct', 'rel_volume',
        'volume', 'sector'}, ...]}`` sorted by ``change_pct`` descending.
    """
    if universe.empty:
        logger.warning("Empty universe passed to vol_up_gainers screener")
        return {"count": 0, "tickers": []}

    df = universe.copy()

    # Coerce to numeric so string-laden DataFrames don't blow up.
    for col in ("change_pct", "rel_volume", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    mask = (df["change_pct"] >= _MIN_CHANGE_PCT) & (
        df["rel_volume"] >= _MIN_REL_VOLUME
    )
    hits = df.loc[mask].sort_values("change_pct", ascending=False)

    logger.info(
        "vol_up_gainers: %d / %d stocks meet gain >= %.0f%% & rvol >= %.1f",
        len(hits),
        len(df),
        _MIN_CHANGE_PCT * 100,
        _MIN_REL_VOLUME,
    )

    tickers: List[Dict[str, Any]] = []
    for _, row in hits.iterrows():
        tickers.append(
            {
                "ticker": row["ticker"],
                "change_pct": round(float(row["change_pct"]), 4),
                "rel_volume": round(float(row["rel_volume"]), 2),
                "volume": int(row["volume"]) if pd.notna(row["volume"]) else 0,
                "sector": row.get("sector", ""),
            }
        )

    return {"count": len(tickers), "tickers": tickers}
