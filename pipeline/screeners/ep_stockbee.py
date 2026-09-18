"""Episodic Pivot -- Stockbee's own scan, verbatim.

Andy 2026-09-18: 「全部按原文 ... 12 注册 EP Stockbee和 EP Qullamaggie 然后我们以后
可以测试下。」 One of two EP screeners registered side by side so the two
authors' definitions can be compared on our own archive; the other is
``ep_qullamaggie``.

Source (Pradeep Bonde, "My process flow for Episodic Pivots (EP)", 2014-07,
https://stockbee.blogspot.com/2014/07/my-process-flow-for-episodic-pivots-ep.html,
re-read 2026-09-18):

    "During the day Run EP scan c/c1>1.04 and v>3*avgv50.1 and v>=300000
     multiple times, see if there is stock with neglect+ game changing earnings"

Telechart syntax, read literally:
    c/c1 > 1.04          close over the prior close, strictly above +4%
    v > 3*avgv50.1       today's volume strictly above 3x the 50-day average
                         volume AS OF YESTERDAY (the ``.1`` suffix = one bar ago,
                         so today's own volume is not inside its benchmark)
    v >= 300000          absolute floor, inclusive

Columns: ``change_pct`` (c/c1 - 1), ``volume`` (v), ``avg_vol50_prev``
(avgv50.1, from the daily bars the enrichment already downloads --
``yfinance_adapter.stockbee_ratios``). No market-cap floor: the scan has none.

**What the scan is not.** His EP is the scan PLUS a human read -- "neglect +
game changing earnings" -- and the buy is usually pre-market ("Most EP where
I made big money I bought in pre market"). Neither the catalyst nor neglect
is measurable here; this list is the scan's candidate set, not his EP. Our run
is after the close, so "multiple times during the day" collapses to one read
of the full-day bar.

Replaces the retired ``episodic_pivot`` (close +10% x rel_volume 3 x cap
$500M), which matched none of the three published EP definitions (audit
2026-09-18 #44).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Mapping, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# The scan's three numbers, verbatim. Not knobs.
C_OVER_C1 = 1.04           # c/c1 > 1.04 (strict)
VOL_MULT = 3.0             # v > 3*avgv50.1 (strict)
MIN_VOLUME = 300_000       # v >= 300000 (inclusive)

SOURCE = ("Stockbee 2014-07 'My process flow for Episodic Pivots (EP)': "
          "c/c1>1.04 and v>3*avgv50.1 and v>=300000")
UNMEASURED = "neglect + game-changing earnings (his human read; no data here)"


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
    """The scan on one row -- the ONE implementation (the screener and the
    watchlist panel both call it). A missing input fails the row."""
    chg, v, av = _f(r, "change_pct"), _f(r, "volume"), _f(r, "avg_vol50_prev")
    if chg is None or v is None or av is None:
        return False
    return (1.0 + chg) > C_OVER_C1 and v > VOL_MULT * av and v >= MIN_VOLUME


def mask(universe: pd.DataFrame) -> pd.Series:
    """Row-wise pass/fail of the scan over a frame."""
    if universe.empty:
        return pd.Series([], dtype=bool, index=universe.index)
    return universe.apply(lambda row: passes(row.to_dict()), axis=1).astype(bool)


def run(universe: pd.DataFrame) -> Dict[str, Any]:
    """``{'count', 'tickers': [...], 'definition', 'unmeasured'}``, sorted by
    volume over its 50-day average, loudest first."""
    out: Dict[str, Any] = {"count": 0, "tickers": [], "definition": SOURCE, "unmeasured": UNMEASURED}
    if universe is None or universe.empty or "ticker" not in universe.columns:
        logger.warning("ep_stockbee: empty universe")
        return out
    df = universe.loc[mask(universe)].copy()
    df["_vmult"] = _num(df, "volume") / _num(df, "avg_vol50_prev")
    df = df.sort_values("_vmult", ascending=False)
    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        rows.append({
            "ticker": r["ticker"],
            "change_pct": round(float(r["change_pct"]), 4),
            "volume": float(r["volume"]),
            "vol_x_avg50": round(float(r["_vmult"]), 2),
            "rel_volume": None if pd.isna(r.get("rel_volume")) else round(float(r["rel_volume"]), 2),
            "market_cap": None if pd.isna(r.get("market_cap")) else float(r["market_cap"]),
            "sector": r.get("sector", "") if not pd.isna(r.get("sector", "")) else "",
        })
    logger.info("ep_stockbee: %d / %d pass (%s)", len(rows), len(universe), SOURCE)
    out.update(count=len(rows), tickers=rows)
    return out
