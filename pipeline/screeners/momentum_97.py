"""Momentum RS-97 screener -- the top 3% of composite relative strength.

**What it looks for: names that are moving now.**

The composite is the equal-weighted average of four percentile ranks --
perf_1w, perf_1m, perf_3m, perf_6m -- so the last five sessions carry the
same weight as the last two quarters. That is the whole design: a stock that
was ordinary a month ago and has since taken off can reach the top of this
list, which is exactly what it is for. Use it to find starts.

**What it cannot tell you.** With a week weighted as heavily as a quarter,
three different things score alike:

  * a genuine new trend beginning
  * a sharp bounce inside a downtrend, which looks identical for a few weeks
  * the fifth attempt at a level that has already rejected four times

The score cannot separate them, and neither can any other single number --
that is what the chart and the setup are for. Names surfaced here have
typically already made a large part of the move by the time they appear;
treat the list as candidates to examine, not as entries.

**How it differs from ``rs_ibd``.** That one weights 3mo/6mo/1yr and answers
"who has been winning". This one answers "who is winning right now". They
share roughly half their top 200 on a given day; the halves they do not share
are different kinds of stock, not better and worse ones. Keep both -- they
are two questions, and the second cannot be answered by the first.

Buckets (100, 99, 98, 97) are percentiles of the composite within the
tradeable universe.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Timeframes used to build the composite RS score and their weights.
_RS_COLS: list[str] = ["perf_1w", "perf_1m", "perf_3m", "perf_6m"]

# Percentile cutoff – we keep the 97th percentile and above.
_CUTOFF_PERCENTILE = 97

# Buckets we report on.
_BUCKETS: list[int] = [100, 99, 98, 97]


def _compute_composite_rs(df: pd.DataFrame) -> pd.Series:
    """Return a 0-100 composite RS score for every row in *df*.

    Each timeframe column is ranked in percentile terms (0-100) across the
    universe, then the four ranks are averaged into a single composite score.
    """
    pct_ranks = pd.DataFrame(index=df.index)
    for col in _RS_COLS:
        if col not in df.columns:
            logger.warning("Column %s missing – treating as NaN", col)
            pct_ranks[col] = np.nan
        else:
            pct_ranks[col] = df[col].rank(pct=True, na_option="bottom") * 100

    composite = pct_ranks.mean(axis=1)
    return composite


def _assign_bucket(score: float, universe_scores: pd.Series) -> int:
    """Map a composite RS *score* to the nearest bucket label (100/99/98/97).

    Bucket boundaries are derived from the actual percentile distribution of
    the universe so that "100" truly means the top-1 %, etc.
    """
    for bucket in _BUCKETS:
        threshold = np.percentile(universe_scores.dropna(), bucket)
        if score >= threshold:
            return bucket
    return _BUCKETS[-1]


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """Run the Momentum-97 screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least the columns listed in
        ``_RS_COLS`` plus ``ticker`` and ``sector``.

    Returns
    -------
    dict
        ``{'count': N, 'buckets': {'100': [...], '99': [...], ...}}``
        where each ticker entry is
        ``{'ticker': str, 'composite_rs': float, 'sector': str}``.
    """
    if universe.empty:
        logger.warning("Empty universe passed to momentum_97 screener")
        return {"count": 0, "buckets": {str(b): [] for b in _BUCKETS}}

    df = universe.copy()
    df["composite_rs"] = _compute_composite_rs(df)

    # Determine the 97th-percentile threshold on the composite score.
    cutoff_value = np.percentile(
        df["composite_rs"].dropna(), _CUTOFF_PERCENTILE
    )
    leaders = df.loc[df["composite_rs"] >= cutoff_value].copy()
    logger.info(
        "momentum_97: %d / %d stocks pass the RS-%d cutoff (>= %.2f)",
        len(leaders),
        len(df),
        _CUTOFF_PERCENTILE,
        cutoff_value,
    )

    # Assign each leader to a bucket.
    leaders["bucket"] = leaders["composite_rs"].apply(
        lambda s: _assign_bucket(s, df["composite_rs"])
    )

    buckets: Dict[str, List[Dict[str, Any]]] = {str(b): [] for b in _BUCKETS}
    for _, row in (
        leaders.sort_values("composite_rs", ascending=False).iterrows()
    ):
        entry = {
            "ticker": row["ticker"],
            "composite_rs": round(float(row["composite_rs"]), 2),
            "sector": row.get("sector", ""),
        }
        bucket_key = str(int(row["bucket"]))
        if bucket_key in buckets:
            buckets[bucket_key].append(entry)

    return {"count": int(len(leaders)), "buckets": buckets}
