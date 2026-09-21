"""21-EMA pullback watchlist -- strong names that have come back to the line.

**What it looks for: an entry inside an existing trend.** Since 2026-09-21
(Andy: 「全都修了。」, audit C_lists_and_tickers.md #41) the list IS the
Screener page preset `21EMA Watch`, evaluated by the same port of the page
filter (`preset_hits.passes`) on the same preset file -- one rule, not two.
Its core is Alex Desjardins's TradersLab "21dma-structure Pullback" scan
(traderslab.gitbook.io/primetrading/alexs-scans-and-workflow-traderslab):
0 to 1 x ATR from the real 21EMA (`ema21_atr_dist`), -0.5 to 4 x ATR from the
50SMA (`sma50_atr_dist`, plain units), daily closing range >= 10%, weekly
return <= 15%. The preset adds its own non-Alex conditions (>= $1B, no
Healthcare, trend_base, ppCount >= 1, ADR 3-6) -- see METRIC_SOURCES.md, the
`21EMA Watch` row. Change the JSON and this list moves with the page.

Retired (was ours, never an author's): a -2%..+3% band around the 20-SMA as a
"~90% proxy" for the 21-EMA, plus above-SMA50/SMA200 and an RS-bracket floor
of 80. The real ema21 has shipped in the universe since 08-24, so the proxy
had no reason left; the RS floor was a second rule the page does not apply.

RS brackets remain, as GROUPING only (the output shape `rs_groups` that the
page and ticker_events read): perf_3m percentile across the frame given,
snapped to 5-point labels.

**What it cannot tell you: whether the trend is still alive.** A name that has
topped passes through this band on its way down and looks exactly like one
pausing on its way up. That distinction lives on the chart -- the shape of
the pullback, whether volume dried up into it, whether the low is higher.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping

import numpy as np
import pandas as pd

from pipeline.screeners import preset_hits

logger = logging.getLogger(__name__)

PRESET_NAME = "21EMA Watch"
_PRESETS_FILE = Path(__file__).resolve().parents[2] / preset_hits.PRESETS_PATH

# RS bracket edges (descending).  Stocks with a perf_3m percentile rank
# >= 95 go into the "100" bucket, >= 90 into "95", etc.
_RS_BRACKETS: list[int] = list(range(100, -1, -5))  # 100, 95, 90, ...


def preset_filters(path: Path = _PRESETS_FILE) -> Mapping[str, Any]:
    """The page preset's filter dict -- the single source of the rule."""
    for p in preset_hits.load_presets(path):
        if p["name"] == PRESET_NAME:
            return p["filters"]
    raise KeyError(f"preset {PRESET_NAME!r} not in {path}")


def _perf_3m_rs(series: pd.Series) -> pd.Series:
    """Return 0-100 percentile rank of *series* across the universe.

    `na_option="top"`, not `"bottom"`. Pandas names the option by rank
    position, so "bottom" hands every missing value the LARGEST rank -- the
    top of this scale. That is invisible while the feed is complete and
    catastrophic when it is not: on 2026-08-12 the yfinance enrichment left
    23.8% of perf_3m missing, those rows took the top 23.8% of the ranking,
    and no real name could reach past 76.2.
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


def run(universe: pd.DataFrame,
        filters: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Run the 21-EMA Pullback Watchlist screener (= the `21EMA Watch` preset).

    Parameters
    ----------
    universe : pd.DataFrame
        Scored universe rows: the preset's columns (``ema21_atr_dist``,
        ``sma50_atr_dist``, ``dcr_pct``, ``perf_1w``, ``pp_count_30d``,
        ``adr_pct``, ``trend_base``, ``market_cap``, ``sector``) plus
        ``perf_3m`` for the RS grouping and ``sma20_dist`` for the entry.
    filters : mapping, optional
        Preset filter dict; defaults to the page's `21EMA Watch`.

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

    if filters is None:
        filters = preset_filters()

    df = universe.copy()
    for col in ("sma20_dist", "perf_3m"):
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # RS (percentile rank on perf_3m, 0-100) across the frame -- grouping only.
    df["rs"] = _perf_3m_rs(df["perf_3m"])

    mask = [preset_hits.passes(r, filters) for r in df.to_dict("records")]
    hits = df.loc[mask].copy()
    logger.info("ema21_watch: %d / %d stocks pass the %s preset",
                len(hits), len(df), PRESET_NAME)

    hits["bracket"] = hits["rs"].apply(_bracket_label)

    rs_groups: Dict[str, List[Dict[str, Any]]] = {}
    for _, row in hits.sort_values("rs", ascending=False).iterrows():
        label = str(int(row["bracket"]))
        sma20 = row["sma20_dist"]
        entry = {
            "ticker": row["ticker"],
            "rs": round(float(row["rs"]), 2),
            "sma20_dist": None if pd.isna(sma20) else round(float(sma20), 4),
            "sector": row.get("sector", ""),
        }
        rs_groups.setdefault(label, []).append(entry)

    return {"count": int(len(hits)), "rs_groups": rs_groups}
