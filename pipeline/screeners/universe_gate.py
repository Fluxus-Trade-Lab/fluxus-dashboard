"""Market-cap floor for the screener lists that never had one.

Andy 2026-09-18 (verbatim, relayed by OPS): 「哦市值这个闸是要加上的。」

Until 2026-06-25 the Finviz universe WAS the >=$1B population (the scrape asks
for `cap_1.0to`), so gainers_4pct, vol_up_gainers, momentum_97, ema21_watch and
healthy_charts never needed a cap condition of their own. On 2026-06-26 upstream
stopped honouring that filter and ~3,000 sub-$1B names entered the pool; these
five lists have carried 36-68% small caps since (2026-09-17 archive). The nine
page presets, vcp and the watchlist/shortlist panels were unaffected because
they carry their own floor. Incident:
data/reference/incidents/2026-09-18_the_universe_changed_populations_and_nobody_logged_it.md

Same floor as the tradeable gate (pipeline/themes MIN_MARKET_CAP, $1B), and
cap ONLY -- no dollar-volume floor -- because the goal is the population these
lists had before 06-26, which was cap-filtered and nothing else. A missing
market cap is treated as below the floor, like the tradeable gate does.

These screeners rank INSIDE the frame they are given (momentum_97's 97th
percentile, ema21_watch / healthy_charts RS brackets), so the floor also puts
their percentiles back on the >=$1B population -- exactly the pre-06-26
definition. universe.json's own `momentum_97` column is still ranked on the
whole universe (run_all, before this gate) and can differ from the list.
episodic_pivot keeps its own 5e8 floor (a definition change, not in scope).
"""
from __future__ import annotations

import pandas as pd

from pipeline.themes import MIN_MARKET_CAP

GATED_SCREENERS = ('momentum_97', 'gainers_4pct', 'vol_up_gainers',
                   'ema21_watch', 'healthy_charts')


def cap_floor(universe: pd.DataFrame, floor: float = MIN_MARKET_CAP) -> pd.DataFrame:
    if universe is None or len(universe) == 0 or 'market_cap' not in universe:
        return universe
    cap = pd.to_numeric(universe['market_cap'], errors='coerce').fillna(0)
    return universe[cap >= floor]
