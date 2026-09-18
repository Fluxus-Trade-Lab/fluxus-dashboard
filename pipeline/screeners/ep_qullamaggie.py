"""Episodic Pivot -- Qullamaggie's definition, as far as daily bars reach.

Andy 2026-09-18: 「全部按原文 ... 12 注册 EP Stockbee和 EP Qullamaggie 然后我们以后
可以测试下。」 Registered beside ``ep_stockbee`` so the two can be compared.

Source (Kristjan Kullamägi, "How to master a setup: Episodic Pivots",
https://qullamaggie.com/how-to-master-a-setup-episodic-pivots/, re-read
2026-09-18):

    "a gap up of 10% or more"
    "massive volume near the open, ideally the stock should trade the average
     daily volume the first 15-20 minutes or even quicker"
    "Preferably the huge volume is already present in after-hours or pre-market"

What is implemented:
    gap_pct >= 0.10      open / prior close - 1, from the daily bars
                         (``gap_pct`` in the enrichment). A GAP, not the
                         close-to-close move the retired screener measured.
    volume >= ADV        NECESSARY consequence of his volume rule, not the rule:
                         a stock that trades one average day's volume in the
                         first 15-20 minutes has at least one ADV by the close.
                         Below that the leg is certainly failed; above it the
                         leg is only possible. ADV here = ``avg_vol50_prev``
                         (50 sessions ending yesterday). He names no window --
                         the 50 is ours, borrowed from the Stockbee column.

What is NOT implemented, and cannot be from daily bars:
    the timing -- volume in the FIRST 15-20 MINUTES, or pre/after-hours.
    That needs intraday bars; the pipeline fetches none. So this list is a
    SUPERSET of his EPs: every one of his would be on it, not everything on
    it is one of his.
Also not implemented (qualitative in the source, no threshold): "the best
EPs are on stocks that have gone sideways for 3-6 months or more", and the
earnings / analyst-beat reads.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional

import pandas as pd

logger = logging.getLogger(__name__)

MIN_GAP = 0.10            # "a gap up of 10% or more" (inclusive)
MIN_ADV_MULT = 1.0        # necessary-condition floor derived from his volume rule

SOURCE = ("Qullamaggie 'How to master a setup: Episodic Pivots': gap up of 10% or more "
          "+ massive volume near the open (volume >= 1 ADV on the day = necessary part only)")
UNMEASURED = ("volume timing -- 'trade the average daily volume the first 15-20 minutes' "
              "needs intraday bars; list is a superset of his EPs")


def _f(r: Mapping[str, Any], k: str) -> Optional[float]:
    v = r.get(k)
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([float("nan")] * len(df), index=df.index)
    return pd.to_numeric(df[col], errors="coerce")


def passes(r: Mapping[str, Any]) -> bool:
    """The definition on one row -- the ONE implementation (screener and
    watchlist panel). A missing input fails the row."""
    gap, v, av = _f(r, "gap_pct"), _f(r, "volume"), _f(r, "avg_vol50_prev")
    if gap is None or v is None or av is None:
        return False
    return gap >= MIN_GAP and v >= MIN_ADV_MULT * av


def mask(universe: pd.DataFrame) -> pd.Series:
    if universe.empty:
        return pd.Series([], dtype=bool, index=universe.index)
    return universe.apply(lambda row: passes(row.to_dict()), axis=1).astype(bool)


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """``{'count', 'tickers': [...], 'definition', 'unmeasured'}``, sorted by
    gap size, largest first."""
    out: Dict[str, Any] = {"count": 0, "tickers": [], "definition": SOURCE, "unmeasured": UNMEASURED}
    if universe is None or universe.empty or "ticker" not in universe.columns:
        logger.warning("ep_qullamaggie: empty universe")
        return out
    df = universe.loc[mask(universe)].copy()
    df["_gap"] = _num(df, "gap_pct")
    df["_vmult"] = _num(df, "volume") / _num(df, "avg_vol50_prev")
    df = df.sort_values("_gap", ascending=False)
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        chg = r.get("change_pct")
        rows.append({
            "ticker": r["ticker"],
            "gap_pct": round(float(r["_gap"]), 4),
            "change_pct": None if pd.isna(chg) else round(float(chg), 4),
            "volume": float(r["volume"]),
            "vol_x_avg50": round(float(r["_vmult"]), 2),
            "rel_volume": None if pd.isna(r.get("rel_volume")) else round(float(r["rel_volume"]), 2),
            "market_cap": None if pd.isna(r.get("market_cap")) else float(r["market_cap"]),
            "sector": r.get("sector", "") if not pd.isna(r.get("sector", "")) else "",
        })
    logger.info("ep_qullamaggie: %d / %d pass (%s)", len(rows), len(universe), SOURCE)
    out.update(count=len(rows), tickers=rows)
    return out
