"""Breadth signal engine (Spec 2).

Pure functions only: evaluate() maps an archive prefix + market-health
snapshot to a rule-derived verdict. Every label traces to THRESHOLDS.
No I/O, no clock — Spec 3's Time Machine replays these functions over
historical prefixes. Spec: docs/plans/2026-07-31-breadth-signal-engine-design.md
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# ── Single source of truth for every threshold ───────────────────────
THRESHOLDS: Dict[str, Dict[str, float]] = {
    'ratio_5d':    {'bull': 1.0, 'bear': 0.5},
    'ratio_10d':   {'bull': 1.0, 'bear': 0.5},
    'thrust':      {'count': 300},
    'qtr_spread':  {},              # sign-based
    'spread_13_34': {},             # sign-based
    'mcclellan':   {'extreme': 70},
    'nh_nl':       {},              # sign-based
    'pct200':      {'bull': 50, 'bear': 30},
    't2108_zone':  {'strong_lo': 60, 'weak_hi': 40, 'oversold': 20, 'overbought': 80},
    'spy_danger':  {'bull_max': 1, 'bear_min': 4},
    'qqq_danger':  {'bull_max': 1, 'bear_min': 4},
    'bench_trend': {},              # both closes vs SMA50
}


def _num(x) -> Optional[float]:
    """None for missing/NaN, float otherwise."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def breadth_votes(row: Dict[str, Any]) -> Dict[str, str]:
    """Votes for the 9 breadth-only rules. Missing/NaN inputs vote neutral."""
    votes: Dict[str, str] = {}

    for key in ('ratio_5d', 'ratio_10d'):
        v = _num(row.get(key))
        t = THRESHOLDS[key]
        if v is None:
            votes[key] = 'neutral'
        elif v >= t['bull']:
            votes[key] = 'bull'
        elif v < t['bear']:
            votes[key] = 'bear'
        else:
            votes[key] = 'neutral'

    up4, down4 = _num(row.get('up_4pct')), _num(row.get('down_4pct'))
    n = THRESHOLDS['thrust']['count']
    if up4 is None or down4 is None:
        votes['thrust'] = 'neutral'
    elif up4 >= n and down4 >= n:
        votes['thrust'] = 'neutral'      # churn day — noted at composition
    elif up4 >= n and up4 > down4:
        votes['thrust'] = 'bull'
    elif down4 >= n and down4 > up4:
        votes['thrust'] = 'bear'
    else:
        votes['thrust'] = 'neutral'

    def _sign_vote(a, b) -> str:
        av, bv = _num(a), _num(b)
        if av is None or bv is None:
            return 'neutral'
        if av - bv > 0:
            return 'bull'
        if av - bv < 0:
            return 'bear'
        return 'neutral'

    votes['qtr_spread'] = _sign_vote(row.get('up_25pct_qtr'), row.get('down_25pct_qtr'))
    votes['spread_13_34'] = _sign_vote(row.get('up_13pct_34d'), row.get('down_13pct_34d'))
    votes['nh_nl'] = _sign_vote(row.get('new_highs'), row.get('new_lows'))

    mc = _num(row.get('mcclellan_osc'))
    votes['mcclellan'] = 'neutral' if mc is None else ('bull' if mc > 0 else 'bear' if mc < 0 else 'neutral')

    p200 = _num(row.get('pct_above_200sma'))
    t = THRESHOLDS['pct200']
    if p200 is None:
        votes['pct200'] = 'neutral'
    elif p200 >= t['bull']:
        votes['pct200'] = 'bull'
    elif p200 < t['bear']:
        votes['pct200'] = 'bear'
    else:
        votes['pct200'] = 'neutral'

    t21 = _num(row.get('t2108'))
    z = THRESHOLDS['t2108_zone']
    if t21 is None or t21 < z['oversold'] or t21 > z['overbought']:
        votes['t2108_zone'] = 'neutral'  # extremes handled by overrides
    elif z['strong_lo'] <= t21 <= z['overbought']:
        votes['t2108_zone'] = 'bull'
    elif z['oversold'] <= t21 <= z['weak_hi']:
        votes['t2108_zone'] = 'bear'
    else:
        votes['t2108_zone'] = 'neutral'

    return votes
