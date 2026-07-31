"""Heat scoring — which tickers are stacking signals right now.

Confluence over repetition: distinct screeners carry their full weight,
repeat hits on the same screener add a fraction. Setup-quality screeners
outweigh participation ones. Pure and no-peek: rows after `as_of` are
invisible. Spec: docs/plans/2026-07-31-ticker-events-design.md
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

# The single source of truth for scoring weights.
WEIGHTS: Dict[str, int] = {
    # setup quality
    'episodic_pivot': 3,
    'vcp': 3,
    'momentum_97': 3,
    # participation
    'gainers_4pct': 1,
    'vol_up_gainers': 1,
    'ema21_watch': 1,
    'healthy_charts': 1,
}

HEAT_WINDOW = 15        # trailing archive dates
REPEAT_FACTOR = 0.25    # weight multiplier per extra hit on the same screener


def compute_heat(events: pd.DataFrame, as_of: str,
                 window: int = HEAT_WINDOW) -> List[Dict[str, Any]]:
    """Rank tickers by weighted distinct-screener confluence. Pure, no clock."""
    if len(events) == 0:
        return []
    upto = events[events['date'].astype(str) <= as_of]
    if len(upto) == 0:
        return []

    dates = sorted(set(upto['date'].astype(str)))[-window:]
    if not dates:
        return []
    win = upto[upto['date'].astype(str).isin(dates)]
    win = win[win['screener'].isin(WEIGHTS)]
    if len(win) == 0:
        return []

    date_index = {d: i for i, d in enumerate(sorted(set(upto['date'].astype(str))))}
    out: List[Dict[str, Any]] = []

    for ticker, grp in win.groupby('ticker', sort=True):
        screeners = []
        score = 0.0
        for name, sub in grp.groupby('screener', sort=True):
            hits = len(sub)
            weight = WEIGHTS[name]
            score += weight * (1 + REPEAT_FACTOR * (hits - 1))
            screeners.append({'name': name, 'hits': int(hits),
                              'last_date': str(sub['date'].max())})
        first_seen, last_seen = str(grp['date'].min()), str(grp['date'].max())
        span = date_index[last_seen] - date_index[first_seen] + 1
        sectors = grp.sort_values('date')['sector'].dropna()
        out.append({
            'ticker': str(ticker),
            'score': round(score, 2),
            'screeners': sorted(screeners, key=lambda s: -WEIGHTS[s['name']]),
            'first_seen': first_seen,
            'last_seen': last_seen,
            'days_span': int(span),
            'sector': str(sectors.iloc[-1]) if len(sectors) else None,
        })

    out.sort(key=lambda h: (-h['score'], h['ticker']))
    return out
