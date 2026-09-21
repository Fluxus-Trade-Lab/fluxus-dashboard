"""Sugar Babies -- Stockbee's watchlist of habitual 9M-EP names (2026-09-21).

Andy 2026-09-21: 「B 照建议做」 -- count Stockbee 9 million EPs, not 4% breakouts,
and rank instead of thresholding.

Pradeep Bonde, Investors Underground interview (YouTube A_0ep4ekGWM, last ~10
min): Sugar Babies are "stocks which have high number of 9 million EPs in a
given period", over six months or a year; he watches 25-30 of them, because on
their breakouts they tend to make 40-50% in 3-5 days. He trades them with his
momentum-burst and anticipation setups -- a long watchlist, not a signal.

What is his and what is ours:
  his   -- the unit (9M EPs), the windows (6 months / 1 year), a watchlist of
           25-30 names ranked by how often.
  ours  -- the event formula (yfinance_adapter.ep9m_days composes his EP scan
           with his 9M volume), TOP_N = 30 (top of his 25-30), the order
           (6-month count first: fully measured; the "1y" count covers only
           ~200 bars of the one-year download, so it breaks ties only; then
           the most recent 9M EP -- a name still printing them ahead of one
           gone quiet since spring -- and only then the ticker), and the
           $1B floor (the screener universe rule, Andy 09-18), and no shell
           companies (Andy 09-21 「排除」).
This replaces the 09-04 preset `bo_count_1y >= 10 and bo_count_3m >= 2`, whose
unit (4% breakouts) and both thresholds were ours.
"""
from __future__ import annotations

import pandas as pd

from pipeline.screeners.universe_gate import cap_floor

TOP_N = 30
SHELL_INDUSTRY = "Shell Companies"


def ranks(universe: pd.DataFrame) -> pd.Series:
    """1..TOP_N for the Sugar Babies, NaN for everyone else (index = universe's)."""
    out = pd.Series(float("nan"), index=universe.index, dtype=float)
    if universe is None or len(universe) == 0 or "ep9m_count_6m" not in universe:
        return out
    pool = cap_floor(universe)
    # Shell companies (SPACs / blank checks, vendor industry "Shell Companies")
    # are out -- Andy 2026-09-21 「排除」. Pradeep's words say nothing either way;
    # this cut is ours.
    if "industry" in pool:
        pool = pool[pool["industry"].fillna("") != SHELL_INDUSTRY]
    c6 = pd.to_numeric(pool["ep9m_count_6m"], errors="coerce")
    c1 = pd.to_numeric(pool.get("ep9m_count_1y"), errors="coerce") if "ep9m_count_1y" in pool \
        else pd.Series(0.0, index=pool.index)
    last = pool["ep9m_last"].fillna("") if "ep9m_last" in pool else pd.Series("", index=pool.index)
    pool = pool.assign(_c6=c6, _c1=c1.fillna(0), _last=last)[c6 >= 1]
    if not len(pool):
        return out
    order = pool.sort_values(["_c6", "_c1", "_last", "ticker"],
                             ascending=[False, False, False, True])
    top = order.index[:TOP_N]
    out.loc[top] = range(1, len(top) + 1)
    return out
