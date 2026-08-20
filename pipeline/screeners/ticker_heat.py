"""Heat scoring -- which tickers are stacking signals right now.

**What it looks for: agreement between screens.** Every other screener here
answers one question. Heat asks how many of them a name is answering at once,
and weights confluence above repetition: three distinct screens beat the same
screen firing three days running, and setup-quality screens (VCP, healthy
charts) outweigh participation ones (4% gainers).

**What it cannot tell you: whether the screens are independent.** They are
not. `gainers_4pct` and `vol_up_gainers` share a condition by construction, so
a name clearing both has produced roughly one piece of evidence, not two. The
weights lean against this; they do not eliminate it. Read a high score as
"several different lenses noticed this", never as a probability.

It is also strictly backward-looking -- a count of what has already fired.
A name at the top of this list is by definition one that has already moved,
which is the same reason to look and the same reason to be careful about
where the stop would have to go.

Confluence over repetition: distinct screeners carry their full weight,
repeat hits on the same screener add a fraction, capped at REPEAT_CAP so
that no single screener's repeat noise can outweigh genuine multi-screener
confluence. Setup-quality screeners outweigh participation ones. Pure and
no-peek: rows after `as_of` are invisible.
Spec: docs/plans/2026-07-31-ticker-events-design.md
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
REPEAT_CAP = 1.5        # per-screener repeat multiplier caps out here
# Same-DAY confluence: >=3 distinct weighted screeners on one date is a
# single loud event, not three quiet ones. MRNA 2026-08-19 (+177% EP) fired
# four on the day and scored 9.0 against a 9.5 top-50 cutoff -- the additive
# design is deaf to one-day bombs by construction (it was built for slow
# multi-day confluence). The bonus is per qualifying DAY, so a name that
# lights the board twice earns it twice.
# >=3 was the first cut and it fired 23.5 times a DAY on the archive (4% /
# Vol Up / Momentum are correlated -- any big up day lights three), inflating
# the whole board (+286 names, cutoff 9.5 -> 12.0, MRNA still out). >=4 is
# 4.2 a day and is the actual bomb signature (MRNA's day fired four).
CONFLUENCE_MIN = 4      # distinct weighted screeners on one date
CONFLUENCE_BONUS = 2.0  # added per qualifying date


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
            score += weight * min(1 + REPEAT_FACTOR * (hits - 1), REPEAT_CAP)
            screeners.append({'name': name, 'hits': int(hits),
                              'last_date': str(sub['date'].max())})
        by_day = grp.groupby(grp['date'].astype(str))['screener'].nunique()
        conf_days = int((by_day >= CONFLUENCE_MIN).sum())
        score += CONFLUENCE_BONUS * conf_days
        first_seen, last_seen = str(grp['date'].min()), str(grp['date'].max())
        span = date_index[last_seen] - date_index[first_seen] + 1
        sectors = grp.sort_values('date')['sector'].dropna()
        out.append({
            'ticker': str(ticker),
            'score': round(score, 2),
            'confluence_days': conf_days,
            'screeners': sorted(screeners, key=lambda s: -WEIGHTS[s['name']]),
            'first_seen': first_seen,
            'last_seen': last_seen,
            'days_span': int(span),
            'sector': str(sectors.iloc[-1]) if len(sectors) else None,
        })

    out.sort(key=lambda h: (-h['score'], h['ticker']))
    return out


HEATING_UP_LIMIT = 50
EVENTS_JSON_MONTHS = 6

_INDEX_FIELDS = ['date', 'screener', 'group', 'change_pct', 'rel_volume',
                 'volume', 'atr_ext', 'num_contractions', 'pct_to_pivot']


def build_heating_up(events: pd.DataFrame, as_of: str) -> Dict[str, Any]:
    """Top-scoring tickers for the heating-up list."""
    return {'as_of': as_of,
            'rows': compute_heat(events, as_of)[:HEATING_UP_LIMIT]}


def build_ticker_events_index(events: pd.DataFrame, as_of: str,
                              months: int = EVENTS_JSON_MONTHS) -> Dict[str, Any]:
    """Per-ticker event lists (newest first) for the trailing `months`."""
    out: Dict[str, List[Dict[str, Any]]] = {}
    if len(events) == 0:
        return {'as_of': as_of, 'events': out}

    cutoff = (pd.Timestamp(as_of) - pd.DateOffset(months=months)).strftime('%Y-%m-%d')
    dates = events['date'].astype(str)
    sub = events[(dates <= as_of) & (dates > cutoff)]

    for ticker, grp in sub.groupby('ticker', sort=True):
        grp = grp.sort_values(['date', 'screener'], ascending=[False, True])
        out[str(ticker)] = [
            {k: r[k] for k in _INDEX_FIELDS if not pd.isna(r[k])}
            for _, r in grp.iterrows()
        ]
    return {'as_of': as_of, 'events': out}
