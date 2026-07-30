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


# ── SPY/QQQ danger signals (spec §2) ─────────────────────────────────

def compute_stochastics(hist: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """(fast, slow) stochastic (14,3,3). H14==L14 carries previous raw forward."""
    h14 = hist['High'].rolling(14).max()
    l14 = hist['Low'].rolling(14).min()
    span = h14 - l14
    raw = (hist['Close'] - l14) / span * 100
    raw = raw.where(span > 0)          # NaN where flat
    raw = raw.ffill().fillna(50.0)     # carry forward; seed 50 at the start
    fast = raw.rolling(3).mean()
    slow = fast.rolling(3).mean()
    return fast, slow


def _danger_frame(hist: pd.DataFrame) -> pd.DataFrame:
    """Per-date boolean frame of the five danger signals."""
    close, low = hist['Close'], hist['Low']
    sma20 = close.rolling(20).mean()
    fast, slow = compute_stochastics(hist)
    lower = low < low.shift(1)
    return pd.DataFrame({
        'below_20sma': close < sma20,
        'stoch_cross': fast < slow,
        'stoch_down': (fast < fast.shift(1)) & (slow < slow.shift(1)),
        'lower_lows': lower & lower.shift(1, fill_value=False) & lower.shift(2, fill_value=False),
        'close_below_lows': close < pd.concat(
            [low.shift(1), low.shift(2), low.shift(3)], axis=1).min(axis=1),
    }).fillna(False)


def danger_signals(hist: pd.DataFrame) -> Dict[str, bool]:
    """The five signals evaluated on the last bar."""
    last = _danger_frame(hist).iloc[-1]
    return {k: bool(last[k]) for k in last.index}


def warn_counts(hist: pd.DataFrame, days: int = 130) -> List[Dict[str, Any]]:
    """Daily warning counts (0-5) for the trailing `days` sessions."""
    frame = _danger_frame(hist)
    counts = frame.sum(axis=1).astype(int).tail(days)
    return [{'date': d.strftime('%Y-%m-%d'), 'count': int(c)}
            for d, c in counts.items()]
