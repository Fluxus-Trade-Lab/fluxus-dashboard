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


def danger_at(hist: pd.DataFrame, date_iso: str) -> Dict[str, Any]:
    """Danger signals as of the last session <= date_iso. Pure.

    Slices `hist` to sessions on or before `date_iso` and evaluates the five
    danger signals on that slice's last bar, so the returned date always
    matches the session the signals were computed on (keeps panels and the
    pinned verdict date in sync — see FINDING A).
    """
    session_dates = hist.index.strftime('%Y-%m-%d')
    keep = session_dates <= date_iso
    sub = hist.loc[keep] if keep.any() else hist
    last = _danger_frame(sub).iloc[-1]
    signals = {k: bool(last[k]) for k in last.index}
    last_date = sub.index[-1].strftime('%Y-%m-%d')
    return {'signals': signals, 'count': sum(signals.values()), 'date': last_date}


def warn_counts(hist: pd.DataFrame, days: int = 130) -> List[Dict[str, Any]]:
    """Daily warning counts (0-5) for the trailing `days` sessions."""
    frame = _danger_frame(hist)
    counts = frame.sum(axis=1).astype(int).tail(days)
    return [{'date': d.strftime('%Y-%m-%d'), 'count': int(c)}
            for d, c in counts.items()]


def _round_or_none(x) -> Optional[float]:
    v = _num(x)
    return None if v is None else round(v, 2)


def market_health(spy_hist: pd.DataFrame, qqq_hist: pd.DataFrame,
                  days: int = 130) -> Dict[str, Any]:
    """Assemble the market_health payload for both benchmarks. Pure."""
    out: Dict[str, Any] = {}
    for key, hist in (('spy', spy_hist), ('qqq', qqq_hist)):
        tail = hist.tail(days)
        sma20 = hist['Close'].rolling(20).mean().tail(days)
        sma50 = hist['Close'].rolling(50).mean().tail(days)
        sma200 = hist['Close'].rolling(200).mean().tail(days)
        out[key] = {
            'candles': [{'date': d.strftime('%Y-%m-%d'),
                         'o': round(float(r['Open']), 2), 'h': round(float(r['High']), 2),
                         'l': round(float(r['Low']), 2), 'c': round(float(r['Close']), 2)}
                        for d, r in tail.iterrows()],
            'sma20': [_round_or_none(v) for v in sma20],
            'sma50': [_round_or_none(v) for v in sma50],
            'sma200': [_round_or_none(v) for v in sma200],
            'danger': {'signals': danger_signals(hist),
                       'count': sum(danger_signals(hist).values())},
            'warn_history': warn_counts(hist, days),
        }
    return out


def truncate_health(health: Dict[str, Any], date_iso: str) -> Optional[Dict[str, Any]]:
    """Cut all per-date arrays to dates <= date_iso (Time Machine / row codes)."""
    out: Dict[str, Any] = {}
    for key in ('spy', 'qqq'):
        blk = health[key]
        keep = sum(1 for c in blk['candles'] if c['date'] <= date_iso)
        if keep == 0:
            return None
        wh = [w for w in blk['warn_history'] if w['date'] <= date_iso]
        out[key] = {
            'candles': blk['candles'][:keep],
            'sma20': blk['sma20'][:keep],
            'sma50': blk['sma50'][:keep],
            'sma200': blk['sma200'][:keep],
            'danger': {'signals': {}, 'count': wh[-1]['count'] if wh else 0},
            'warn_history': wh,
        }
    return out


# ── Verdict composition (spec §1) ────────────────────────────────────

_EXPOSURE = {
    ('BULLISH', 'Low'): 'Full / normal size',
    ('BULLISH', 'Elevated'): 'Normal, tighter stops',
    ('BULLISH', 'High'): 'Reduced despite breadth — price warnings stack',
    ('MIXED', 'Low'): 'Reduced / selective',
    ('MIXED', 'Elevated'): 'Reduced / selective',
    ('MIXED', 'High'): 'Defensive lean — wait for alignment',
    ('BEARISH', 'Low'): 'Defensive / capital preservation',
    ('BEARISH', 'Elevated'): 'Defensive / capital preservation',
    ('BEARISH', 'High'): 'Defensive / capital preservation',
    ('OVERSOLD', 'Low'): 'Defensive but alert — thrust watch',
    ('OVERSOLD', 'Elevated'): 'Defensive but alert — thrust watch',
    ('OVERSOLD', 'High'): 'Defensive but alert — thrust watch',
    ('OVERBOUGHT', 'Low'): 'No chasing; harvest into strength',
    ('OVERBOUGHT', 'Elevated'): 'No chasing; harvest into strength',
    ('OVERBOUGHT', 'High'): 'No chasing; harvest into strength',
}

_PLAYBOOK = {
    'BULLISH': 'Trend participation — press winners, normal pyramids',
    'MIXED': 'Smaller size, cleaner setups, demand confirmation',
    'BEARISH': 'Capital preservation — selective shorts or cash',
    'OVERSOLD': 'Bottom-hunt protocol — wait for a 300+ up-4% thrust day',
    'OVERBOUGHT': 'Late-stage strength — take partials, raise stops',
}

_GUIDANCE = {
    ('BULLISH', 'Low'): 'Breadth and both benchmarks agree; full participation is supported.',
    ('BULLISH', 'Elevated'): 'Breadth is constructive but price warnings are stacking; participate with tighter risk.',
    ('BULLISH', 'High'): 'Breadth says bull, price action disagrees loudly; size down until they reconcile.',
    ('MIXED', 'Low'): 'Signals disagree across timeframes; smaller positions and cleaner setups until the tape picks a side.',
    ('MIXED', 'Elevated'): 'Mixed breadth with mounting warnings; reduce exposure and demand confirmation before adding.',
    ('MIXED', 'High'): 'Mixed breadth and heavy price warnings; defensive posture until alignment returns.',
    ('BEARISH', 'Low'): 'Breadth is negative; protect capital and let the downtrend exhaust itself.',
    ('BEARISH', 'Elevated'): 'Negative breadth with active warnings; capital preservation is the position.',
    ('BEARISH', 'High'): 'Full risk-off: breadth and price agree on the downside.',
    ('OVERSOLD', 'Low'): 'T2108 in the oversold zone; stop pressing shorts and watch for a reversal thrust day.',
    ('OVERSOLD', 'Elevated'): 'Deeply oversold; the next 300+ up-4% day is the signal that matters.',
    ('OVERSOLD', 'High'): 'Max-pain zone; historically where bottoms form — watch for the thrust, do not front-run it.',
    ('OVERBOUGHT', 'Low'): 'T2108 overbought; strength is late-stage — harvest, do not initiate chases.',
    ('OVERBOUGHT', 'Elevated'): 'Overbought with warnings building; tighten stops into strength.',
    ('OVERBOUGHT', 'High'): 'Overbought and deteriorating; distribution risk is elevated.',
}


def _health_last(health: Optional[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    if not health:
        return None
    blk = health.get(key)
    if not blk or not blk.get('candles'):
        return None
    return {
        'close': blk['candles'][-1]['c'],
        'sma20': blk['sma20'][-1], 'sma50': blk['sma50'][-1], 'sma200': blk['sma200'][-1],
        'count': blk['warn_history'][-1]['count'] if blk.get('warn_history') else
                 blk.get('danger', {}).get('count', 0),
    }


def _bench_state(h: Optional[Dict[str, Any]]) -> Optional[str]:
    """Downtrend conditions take precedence over Uptrend on overlap (deliberate: fail bearish)."""
    if h is None:
        return None
    t = THRESHOLDS['spy_danger']
    if (h['sma200'] is not None and h['close'] < h['sma200']) or h['count'] >= t['bear_min']:
        return 'Downtrend'
    if h['count'] <= t['bull_max'] and h['sma20'] is not None and h['close'] > h['sma20']:
        return 'Uptrend'
    return 'Mixed'


def _danger_vote(count: Optional[int]) -> str:
    if count is None:
        return 'neutral'
    t = THRESHOLDS['spy_danger']
    if count <= t['bull_max']:
        return 'bull'
    if count >= t['bear_min']:
        return 'bear'
    return 'neutral'


def evaluate(frame: pd.DataFrame, health: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Rule-derived verdict for the last row of `frame`. Pure and total."""
    row = frame.iloc[-1].to_dict()
    date_iso = str(row.get('date', ''))
    if health is not None and date_iso:
        health = truncate_health(health, date_iso)

    votes = breadth_votes(row)
    spy = _health_last(health, 'spy')
    qqq = _health_last(health, 'qqq')
    votes['spy_danger'] = _danger_vote(spy['count'] if spy else None)
    votes['qqq_danger'] = _danger_vote(qqq['count'] if qqq else None)
    if spy and qqq and spy['sma50'] is not None and qqq['sma50'] is not None:
        above = (spy['close'] > spy['sma50'], qqq['close'] > qqq['sma50'])
        votes['bench_trend'] = 'bull' if all(above) else 'bear' if not any(above) else 'neutral'
    else:
        votes['bench_trend'] = 'neutral'

    score = sum(v == 'bull' for v in votes.values()) - sum(v == 'bear' for v in votes.values())
    env = 'BULLISH' if score >= 4 else 'BEARISH' if score <= -4 else 'MIXED'

    notes: List[str] = []
    t21 = _num(row.get('t2108'))
    z = THRESHOLDS['t2108_zone']
    if t21 is not None and t21 < z['oversold']:
        env = 'OVERSOLD'
        notes.append('T2108 below 20 — reversal watch: look for a bullish thrust day')
    elif t21 is not None and t21 > z['overbought']:
        env = 'OVERBOUGHT'
        notes.append('T2108 above 80 — chase risk')

    up4, down4 = _num(row.get('up_4pct')), _num(row.get('down_4pct'))
    n = THRESHOLDS['thrust']['count']
    if up4 is not None and down4 is not None and up4 >= n and down4 >= n:
        notes.append('Churn/volatile: 300+ stocks both up and down 4% — unresolved tape')
    mc = _num(row.get('mcclellan_osc'))
    if mc is not None and abs(mc) >= THRESHOLDS['mcclellan']['extreme']:
        notes.append(f"McClellan at {mc:+.0f} — extreme reading")
    if health is None:
        notes.append('Price signals unavailable — breadth-only verdict')

    warn_total = (spy['count'] if spy else 0) + (qqq['count'] if qqq else 0)
    risk = 'Low' if warn_total <= 2 else 'Elevated' if warn_total <= 6 else 'High'

    spy_state, qqq_state = _bench_state(spy), _bench_state(qqq)
    alignment = None if spy_state is None or qqq_state is None else (
        'Aligned' if spy_state == qqq_state else 'Divergent')

    r5, r10 = votes['ratio_5d'], votes['ratio_10d']
    qs, s13 = votes['qtr_spread'], votes['spread_13_34']
    if r5 == r10 == 'bull' and qs == s13 == 'bull':
        confirmation = 'Confirmed bull — ratios and spreads agree'
    elif r5 == r10 == 'bear' and qs == s13 == 'bear':
        confirmation = 'Confirmed bear — ratios and spreads agree'
    else:
        parts = []
        if r5 != r10:
            parts.append('5D vs 10D ratios disagree')
        if qs != s13:
            parts.append('quarterly vs 13%/34d spreads disagree')
        confirmation = 'Inconclusive' + (' — ' + '; '.join(parts) if parts else ' — signals split')

    return {
        'env': env, 'score': int(score), 'risk': risk, 'warn_total': int(warn_total),
        'exposure': _EXPOSURE[(env, risk)], 'playbook': _PLAYBOOK[env],
        'guidance': _GUIDANCE[(env, risk)],
        'spy_state': spy_state, 'qqq_state': qqq_state, 'alignment': alignment,
        'confirmation': confirmation, 'notes': notes, 'votes': votes,
    }


# ── Percentile context + per-row codes (spec §1, §3) ─────────────────

def percentile_context(frame: pd.DataFrame) -> Dict[str, int]:
    """Today's percentile rank per headline metric vs the whole archive."""
    derived = {
        'nh_nl_net': pd.to_numeric(frame.get('new_highs'), errors='coerce')
                     - pd.to_numeric(frame.get('new_lows'), errors='coerce'),
        'qtr_spread': pd.to_numeric(frame.get('up_25pct_qtr'), errors='coerce')
                      - pd.to_numeric(frame.get('down_25pct_qtr'), errors='coerce'),
    }
    ctx: Dict[str, int] = {}
    for key in ('up_4pct', 'down_4pct', 'ratio_5d', 't2108', 'mcclellan_osc',
                'nh_nl_net', 'qtr_spread'):
        series = derived[key] if key in derived else pd.to_numeric(frame.get(key), errors='coerce')
        if series is None or len(series) == 0:
            continue
        today = series.iloc[-1]
        if pd.isna(today):
            continue
        ranked = series.dropna()
        ctx[key] = int(round(float((ranked <= today).mean()) * 100))
    return ctx


def annotate_rows(rows: List[Dict[str, Any]], frame: pd.DataFrame,
                  health: Optional[Dict[str, Any]]) -> None:
    """Attach compact verdict codes v={env,risk,warn} to breadth.json rows."""
    dates = list(frame['date'].astype(str))
    index_of = {d: i for i, d in enumerate(dates)}
    for row in rows:
        i = index_of.get(str(row.get('date')))
        if i is None:
            row['v'] = None
            continue
        v = evaluate(frame.iloc[:i + 1].reset_index(drop=True), health)
        row['v'] = {'env': v['env'], 'risk': v['risk'], 'warn': v['warn_total']}


def run_signals(breadth_result: Dict[str, Any], frame: pd.DataFrame,
                spy_hist: Optional[pd.DataFrame],
                qqq_hist: Optional[pd.DataFrame]) -> Optional[Dict[str, Any]]:
    """Attach verdict + row codes to a breadth.json payload; return health dict."""
    health = None
    if spy_hist is not None and qqq_hist is not None \
            and len(spy_hist) >= 50 and len(qqq_hist) >= 50:
        health = market_health(spy_hist, qqq_hist)
        last_date = str(frame['date'].iloc[-1]) if len(frame) else None
        if last_date:
            # Pin the panels' danger block to the same session as the verdict
            # so the UI never shows a banner and panels disagreeing (FINDING A).
            health['spy']['danger'] = danger_at(spy_hist, last_date)
            health['qqq']['danger'] = danger_at(qqq_hist, last_date)
    verdict = evaluate(frame, health)
    verdict['context'] = percentile_context(frame)
    breadth_result['verdict'] = verdict
    annotate_rows(breadth_result.get('history', {}).get('rows', []), frame, health)
    return health
