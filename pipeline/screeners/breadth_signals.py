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
    # Both ratios read Stockbee's own ratio (Andy 2026-09-18: 「全部按原文，9 用
    # 课程版，12 注册 EP Stockbee和 EP Qullamaggie 然后我们以后可以测试下。」):
    # "total of 5 days 4% b/o divided by total of 5 days 4% b/d" and "same for
    # 10 days using 10 day data" -- Pradeep Bonde's replies on
    # stockbee.blogspot.com/p/mm.html (2018-08-30, 2017-03-09). Column:
    # ratio_*_stockbee, summed over his three-leg 4% count (RATIO_COLS below).
    #
    # 10-day line, verbatim from
    # stockbee.blogspot.com/2010/05/what-you-need-to-know-about-market.html :
    #   "When the 10 day ratio goes above 2 after market has been in bearish
    #    phase for sometime, it indicates bullish breadth thrust"
    #   "When the 10 day ratio goes below .5 after market has been bullish for
    #    sometime, it indicates a bearish thrust"
    # -> bull strictly > 2, bear strictly < .5 ('strict'). The self-made bull
    # line 1.0 (2026-07-31..09-18) is gone. NOT implemented: "after market has
    # been in bearish / bullish phase for sometime" -- he gives no measure of
    # "phase" or "sometime", and inventing one would be the thing Andy ruled out.
    #
    # 5-day line: he publishes the ratio but no line for it (checked:
    # 2011/10/5-day-breadth-ratio-see-big-improvement.html gives none). 1.0 /
    # 0.5 are OURS, self-made, unchanged; only the numerator became his.
    'ratio_5d':    {'bull': 1.0, 'bear': 0.5},
    'ratio_10d':   {'bull': 2.0, 'bear': 0.5, 'strict': True},
    # Pradeep Bonde's (Stockbee) own definition, followed as written (Andy
    # 2026-09-18: 「确认原作者定义准确与否，按照原作者的定义走」):
    #   * the count is his Market Monitor "stocks up 4% plus today":
    #     (100*(C-C1)/C1) >= 4 AND V >= 100000 AND V > V1, US common stocks,
    #     ETFs excluded -- stockbee.blogspot.com/2014/08/how-i-get-market-monitor-numbers.html
    #     (our column: up_4pct_stockbee / down_4pct_stockbee, same three legs);
    #   * a thrust is "back-to-back 300-plus days" -- an absolute 300, on
    #     consecutive sessions; one 300 day is not a thrust --
    #     stockbee.blogspot.com/2026/07/understand-market-breadth.html
    # Replaces the self-made rule (0.113 x universe_size on the price-only
    # up_4pct, single day) used 2026-08-09..09-18.
    'thrust':      {'count': 300, 'days': 2},
    # Sign of up minus down = his "breadth crossover": "When breadth turns from
    # positive to negative or the other way, it indicates confirmation of
    # primary breadth trend. In Market Monitor this is indicated by: # of
    # stocks up>25% in a quarter / # of stocks down>25% in a quarter ... # of
    # stocks up>13% in 34 days / # of stocks down>13% in 34 days" (2010/05 post
    # above). Counts are his scans (*_stockbee, SPREAD_COLS below).
    'qtr_spread':  {},              # sign-based
    'spread_13_34': {},             # sign-based
    'mcclellan':   {'extreme': 70},
    'nh_nl':       {},              # sign-based, common-stock counts (SPREAD_COLS)
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


# The Finviz fetch capped at 150 pages until 2026-08-09, and a cap that binds
# does not sample the market, it truncates it mid-alphabet. Rows that hit the cap
# exactly are undercounts of every whole-universe measure — up_4pct, new highs,
# new lows — because everything from M to Z was missing. Flagged rather than
# corrected: the counts cannot be recovered, and a replay crossing this stretch
# should say so instead of comparing across it silently.
TRUNCATED_UNIVERSE = 3000
# The 07-15..07-24 rows were backfilled from the same capped universe and land a
# few names short of the cap (2974-2980), so `== 3000` missed 8 of the 30 capped
# sessions (Nighty Zac 2026-09-17). The band is self-made: real uncapped sizes
# were 2559-2592 before 06-26 and 5600+ after 08-10. Bounded by the date the cap
# was lifted, so a future universe that happens to sit near 3,000 is not flagged.
TRUNCATED_BAND = (2950, TRUNCATED_UNIVERSE)
CAP_LIFTED = '2026-08-09'   # 2f782b53


def universe_truncated(row: Dict[str, Any]) -> bool:
    """True when this session's universe was cut off by the page cap."""
    size = _num(row.get('universe_size'))
    if size is None or not (TRUNCATED_BAND[0] <= size <= TRUNCATED_BAND[1]):
        return False
    day = str(row.get('date') or '')[:10]
    if not day:                      # undated row: keep the old exact-cap answer
        return size == TRUNCATED_UNIVERSE
    return day < CAP_LIFTED


THRUST_UP, THRUST_DOWN = 'up_4pct_stockbee', 'down_4pct_stockbee'

# Where each vote reads (2026-09-18). The unsuffixed archive columns are the
# older point-to-point / price-only / SPAC-inclusive counts; they keep their
# history but no longer vote. A row without these columns (the archive before
# they existed) is unmeasurable -- never voted on the old column instead.
RATIO_COLS = {'ratio_5d': 'ratio_5d_stockbee', 'ratio_10d': 'ratio_10d_stockbee'}
SPREAD_COLS = {
    'qtr_spread': ('up_25pct_qtr_stockbee', 'down_25pct_qtr_stockbee'),
    'spread_13_34': ('up_13pct_34d_stockbee', 'down_13pct_34d_stockbee'),
    # Standard new-high/new-low universe is common stocks only (SPACs out);
    # breadth_metrics.new_highs_common, METRIC_SOURCES ✅.
    'nh_nl': ('new_highs_common', 'new_lows_common'),
}


def thrust_count(row: Dict[str, Any]) -> Optional[float]:
    """Stockbee's thrust line: 300 names, whatever the universe (his number)."""
    return float(THRESHOLDS['thrust']['count'])


def thrust_state(row: Dict[str, Any]) -> Optional[str]:
    """'bull' / 'bear' / 'churn' / 'none', or None when it cannot be measured.

    Back-to-back: today AND the previous session both at/over the line. The
    previous session's counts ride in as `_prev_<col>` (evaluate() adds them).
    Rows without the Stockbee columns (the archive before 2026-09-05) or without
    a previous session are unmeasurable, never a vote on another rule."""
    n = thrust_count(row)
    up, dn = _num(row.get(THRUST_UP)), _num(row.get(THRUST_DOWN))
    pup, pdn = _num(row.get('_prev_' + THRUST_UP)), _num(row.get('_prev_' + THRUST_DOWN))
    if None in (up, dn, pup, pdn) or (up + dn) <= 0:
        return None
    bull, bear = up >= n and pup >= n, dn >= n and pdn >= n
    if bull and bear:
        return 'churn'
    return 'bull' if bull else 'bear' if bear else 'none'


def render_copy(text: str, row: Dict[str, Any]) -> str:
    """Fill {thrust} with this row's own thrust count. The copy said "300+" until
    2026-09-18 while vote_detail used 0.113 x universe (634 on 09-16) -- the page
    told people to wait for a number the engine no longer used."""
    return text.replace('{thrust}', f"{thrust_count(row):.0f}") if '{thrust}' in text else text


def breadth_votes(row: Dict[str, Any]) -> Dict[str, str]:
    """Votes for the 9 breadth-only rules. Missing/NaN inputs vote neutral."""
    votes: Dict[str, str] = {}

    for key, col in RATIO_COLS.items():
        v = _num(row.get(col))
        t = THRESHOLDS[key]
        if v is None:
            votes[key] = 'neutral'
        elif (v > t['bull']) if t.get('strict') else (v >= t['bull']):
            votes[key] = 'bull'
        elif v < t['bear']:
            votes[key] = 'bear'
        else:
            votes[key] = 'neutral'

    st = thrust_state(row)
    votes['thrust'] = st if st in ('bull', 'bear') else 'neutral'   # churn noted at composition

    def _sign_vote(a, b) -> str:
        av, bv = _num(a), _num(b)
        if av is None or bv is None:
            return 'neutral'
        if av - bv > 0:
            return 'bull'
        if av - bv < 0:
            return 'bear'
        return 'neutral'

    for key, (a, b) in SPREAD_COLS.items():
        votes[key] = _sign_vote(row.get(a), row.get(b))

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


def vote_detail(row: Dict[str, Any], votes: Dict[str, str],
                spy_warn: Optional[int] = None,
                qqq_warn: Optional[int] = None) -> List[Dict[str, Any]]:
    """Per vote: the value, the line it flips at, and the distance between them.

    The frontend draws one mark per vote carrying four things — side, line,
    distance, measurability. It must not re-derive the rules to do it: the
    thresholds live here, and a second copy in JavaScript would drift the first
    time one of them changed. So the rule stays in one place and the numbers
    travel.

    `margin` is in the metric's own unit and is never comparable across two
    votes. A McClellan of 3.2 and 1.31 points of 200-day breadth are not the
    same distance; `unit` is emitted so the reader is told which is which, and
    the drawing normalises inside each metric's own range rather than across
    them.
    """
    def n(k):
        return _num(row.get(k))

    def diff(a, b, unit):
        av, bv = n(a), n(b)
        return (None, None) if av is None or bv is None else (av - bv, unit)

    spec: List[Dict[str, Any]] = []

    def add(key, value, line, margin, unit, label):
        spec.append({
            'key': key, 'side': votes.get(key, 'neutral'), 'label': label,
            'value': value, 'line': line, 'margin': margin, 'unit': unit,
            'measurable': margin is not None,
        })

    for k, lbl in (('ratio_5d', '5-day ratio'), ('ratio_10d', '10-day ratio')):
        v, line = n(RATIO_COLS[k]), THRESHOLDS[k]['bull']
        add(k, v, line, None if v is None else v - line, 'ratio', lbl)

    # Back-to-back: the weaker of the two sessions is what has to clear the
    # line, so the margin is taken on it. Unmeasurable (None) before the
    # Stockbee columns existed or without a previous session.
    up4, pup4 = n(THRUST_UP), n('_prev_' + THRUST_UP)
    need = thrust_count(row)
    thrust_measurable = thrust_state(row) is not None
    add('thrust', up4, need, (min(up4, pup4) - need) if thrust_measurable else None,
        'names', 'Thrust')

    for k, lbl in (('qtr_spread', 'Quarterly spread'), ('spread_13_34', '13%/34d spread'),
                   ('nh_nl', 'New highs vs lows')):
        a, b = SPREAD_COLS[k]
        m, unit = diff(a, b, 'names')
        add(k, n(a), 0, m, unit, lbl)

    mc = n('mcclellan_osc')
    add('mcclellan', mc, 0, mc, 'points', 'McClellan')

    p200 = n('pct_above_200sma')
    line = THRESHOLDS['pct200']['bull']
    add('pct200', p200, line, None if p200 is None else p200 - line, 'points', '% above 200-day')

    t21, z = n('t2108'), THRESHOLDS['t2108_zone']
    add('t2108_zone', t21, z['strong_lo'],
        None if t21 is None else t21 - z['strong_lo'], 'points', 'T2108 zone')

    # Danger counts are inverted: fewer is safer. Emit the margin, not the raw
    # count, so "up is safer" holds for every mark in the row.
    for k, w, lbl in (('spy_danger', spy_warn, 'SPY warnings'),
                      ('qqq_danger', qqq_warn, 'QQQ warnings')):
        cap = THRESHOLDS[k]['bull_max']
        add(k, w, cap, None if w is None else cap - w, 'warnings', lbl)

    add('bench_trend', None, None, None, '', 'Benchmark trend')
    return spec


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


def warn_counts(hist: pd.DataFrame, days: Optional[int] = 130) -> List[Dict[str, Any]]:
    """Daily warning counts (0-5) for the trailing `days` sessions.

    `days=None` returns all sessions (Time Machine full-span health).
    """
    frame = _danger_frame(hist)
    counts = frame.sum(axis=1).astype(int)
    if days is not None:
        counts = counts.tail(days)
    return [{'date': d.strftime('%Y-%m-%d'), 'count': int(c)}
            for d, c in counts.items()]


def signals_history(hist: pd.DataFrame, days: Optional[int] = 130) -> List[Dict[str, Any]]:
    """Per-date five-signal booleans + count. `days=None` returns all sessions.

    Time Machine (Spec 3) needs the per-signal state at any past date; the
    trailing `warn_counts` view only carries totals.
    """
    frame = _danger_frame(hist)
    if days is not None:
        frame = frame.tail(days)
    cols = list(frame.columns)
    out: List[Dict[str, Any]] = []
    for d, row in frame.iterrows():
        sig = {k: bool(row[k]) for k in cols}
        out.append({'date': d.strftime('%Y-%m-%d'),
                    'signals': sig,
                    'count': sum(sig.values())})
    return out


def _round_or_none(x) -> Optional[float]:
    v = _num(x)
    return None if v is None else round(v, 2)


def market_health(spy_hist: pd.DataFrame, qqq_hist: pd.DataFrame,
                  days: Optional[int] = 130) -> Dict[str, Any]:
    """Assemble the market_health payload for both benchmarks. Pure.

    `days=None` covers every session of the input history (Time Machine).
    """
    out: Dict[str, Any] = {}
    for key, hist in (('spy', spy_hist), ('qqq', qqq_hist)):
        n = len(hist) if days is None else days
        tail = hist.tail(n)
        sma20 = hist['Close'].rolling(20).mean().tail(n)
        sma50 = hist['Close'].rolling(50).mean().tail(n)
        sma200 = hist['Close'].rolling(200).mean().tail(n)
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
            'signals_history': signals_history(hist, days),
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
    'OVERSOLD': 'Bottom-hunt protocol — wait for back-to-back {thrust}+ up-4% days',
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
    ('OVERSOLD', 'Elevated'): 'Deeply oversold; back-to-back {thrust}+ up-4% days are the signal that matters.',
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


# Three conditions that exist only for the Market Conditions score, on top of
# the nine the verdict votes. Every one splits at a natural boundary -- more
# than half the market, or a net-positive day -- so there is no tunable
# parameter here and nothing to overfit. They are NOT added to the verdict:
# that instrument is nine rules with published thresholds and stays that way.
def _conditions_extra(row: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key, col in (('pct50', 'pct_above_50sma'), ('pct20', 'pct_above_20sma')):
        v = _num(row.get(col))
        out[key] = 'neutral' if v is None else ('bull' if v > 50 else 'bear' if v < 50 else 'neutral')
    n = _num(row.get('net_advances'))
    out['net_adv'] = 'neutral' if n is None else ('bull' if n > 0 else 'bear' if n < 0 else 'neutral')
    return out


# Trailing price direction over a month, a quarter and a year. These are the
# slow half of the score and they are the reason different bottoms have
# different depths: breadth collapses in a week, trend does not. Without them
# every washout looked alike -- November 2025 and March 2026 both pinned the
# floor, when only one of them had a broken trend underneath it.
#
# Sign of a trailing return is a natural boundary; there is no threshold to
# tune. NaN while the window is still filling, which votes neutral rather than
# borrowing a direction it cannot see.
_SLOW_WINDOWS = {'px_1m': 21, 'px_3m': 63, 'px_1y': 252}


def _slow_conditions(frame: pd.DataFrame) -> Dict[str, List[str]]:
    # A frame without spx_close is not an error and must not raise: some
    # callers pass a minimal history. pd.to_numeric(None) returns a scalar NaN
    # rather than an empty Series, so the column is checked before use --
    # every slow condition then votes neutral, which is what "cannot see the
    # trend" should score.
    col = frame['spx_close'] if 'spx_close' in frame.columns else None
    if col is None:
        return {key: ['neutral'] * len(frame) for key in _SLOW_WINDOWS}

    close = pd.to_numeric(col, errors='coerce')
    out: Dict[str, List[str]] = {}
    for key, n in _SLOW_WINDOWS.items():
        chg = close / close.shift(n) - 1.0
        out[key] = ['neutral' if pd.isna(v) else ('bull' if v > 0 else 'bear' if v < 0 else 'neutral')
                    for v in chg]
    return out


# bull / neutral / bear -> 1 / 0.5 / 0.
#
# Counting only the bulls made an undecided condition score identically to a
# bearish one, which is the same category error as reading a missing
# measurement as a zero. It also guaranteed a floor: on the days everything
# turned at once the score pinned at 0 and stopped distinguishing between
# washouts. Half-credit for undecided fixes both.
_CONDITION_WEIGHT = {'bull': 1.0, 'neutral': 0.5, 'bear': 0.0}

# The measurements the score reads, each as a signed quantity where higher is
# always better. Spreads are differenced here rather than voted on, because the
# score wants magnitude and a vote throws magnitude away.
#
# Stockbee's own columns (2026-09-21, Andy 「用stockbee口径」): the 5/10-day
# ratios, the 25%/quarter and 13%/34-day spreads and the 4% net all read the
# `*_stockbee` scans, new highs/lows the common-stock set. Each of those columns
# starts on its own landing day (coverage_gaps.json); before it, that condition
# is unmeasured and drops out of the denominator -- never filled from the old
# price-only columns, which would put two definitions in one series.
# The 4% net was keyed 'thrust' until 2026-09-21: it is the sign of one day's
# up-minus-down, not Stockbee's thrust (back-to-back 300+, `thrust_state`), so
# it is named for what it measures.
_CONDITION_COLS = {'ratio_5d': 'ratio_5d_stockbee', 'ratio_10d': 'ratio_10d_stockbee',
                   't2108': 't2108', 'pct_above_200sma': 'pct_above_200sma',
                   'pct_above_50sma': 'pct_above_50sma',
                   'pct_above_20sma': 'pct_above_20sma',
                   'mcclellan_osc': 'mcclellan_osc', 'net_advances': 'net_advances'}
_CONDITION_SPREADS = {
    'nh_nl': ('new_highs_common', 'new_lows_common'),
    'qtr_spread': ('up_25pct_qtr_stockbee', 'down_25pct_qtr_stockbee'),
    'spread_13_34': ('up_13pct_34d_stockbee', 'down_13pct_34d_stockbee'),
    'net_4pct': (THRUST_UP, THRUST_DOWN),
}

# The neutral line for each measurement -- the value at which it stops being a
# positive and starts being a negative. Every one is either a published
# threshold or a natural boundary (more than half the market, a net-positive
# day, a rising price). None of them was chosen to make a chart look right.
_CONDITION_NEUTRAL = {
    'ratio_5d': 1.0, 'ratio_10d': 1.0,          # advancing = declining
    't2108': 50.0, 'pct_above_200sma': 50.0,    # half the market
    'pct_above_50sma': 50.0, 'pct_above_20sma': 50.0,
    'mcclellan_osc': 0.0, 'net_advances': 0.0,  # net positive day
    'nh_nl': 0.0, 'qtr_spread': 0.0, 'spread_13_34': 0.0, 'net_4pct': 0.0,
    'px_1m': 0.0, 'px_3m': 0.0, 'px_1y': 0.0,   # price higher than it was
}

# There is deliberately no steepness parameter here, and the reason is worth
# keeping. An earlier version gave partial credit on a logistic curve whose
# slope was set to ln(99) -- dressed up as "one interquartile range from
# neutral earns 99%", but actually chosen by scanning slopes until the reading
# landed where it was expected to. The justification was written afterwards.
# Smoothing the plain count turned out to separate the extremes better anyway
# (2026-04-17 and 2026-04-30 read 97 and 91, against 94 and 90 from the fitted
# curve), so the curve bought nothing except a number to tune.
# At least this many prior sessions before a spread estimate means anything.
_CONDITIONS_MIN_HISTORY = 60

# Light filter. Span 2 will not hide a turn; it stops one session flipping the
# reading, which is what Oratnek's EMA2 is for.
_CONDITIONS_SPAN = 2

def _condition_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Every measurement the score reads, oriented so higher is better."""
    out: Dict[str, pd.Series] = {}
    for key, col in _CONDITION_COLS.items():
        if col in frame.columns:
            out[key] = pd.to_numeric(frame[col], errors='coerce')
    for key, (up, down) in _CONDITION_SPREADS.items():
        if up in frame.columns and down in frame.columns:
            out[key] = (pd.to_numeric(frame[up], errors='coerce')
                        - pd.to_numeric(frame[down], errors='coerce'))
    if 'spx_close' in frame.columns:
        close = pd.to_numeric(frame['spx_close'], errors='coerce')
        for key, n in _SLOW_WINDOWS.items():
            out[key] = close / close.shift(n) - 1.0
    return pd.DataFrame(out, index=frame.index)


def conditions_series(frame: pd.DataFrame, days: Optional[int] = 260) -> Dict[str, Any]:
    """Market Conditions 0-100: where today sits in this market's own history.

    Oratnek's construction: fifteen conditions against absolute neutral
    lines, the positive share, EMA-2 smoothed. The plain count, on purpose.

    Three versions existed and the sequence is recorded in git (c484951 ->
    b07a152 -> 1afb4ba -> 1055c51). A percentile against the series' own
    history was tried and rejected: a percentile orbits 50 by construction,
    so a genuinely strong year reads as ordinary and the card can no longer
    say "this is a good market" — a different question from the one it asks.
    A logistic partial-credit curve was tried and retracted as after-the-fact
    curve fitting. The plain count remains, with its known cost stated below.

    KNOWN COST: the count saturates. Every condition merely positive and
    every condition overwhelmingly positive both read raw=100 (22 of the
    trailing 260 sessions, ~8.5%). The EMA-2 recovers ordering between
    nearby days (the two April days that tied at 100 read 97 and 91 after
    smoothing) but a long uniform stretch still pins the ceiling. Inside the
    top band this is cosmetic — Constructive starts at 78 and the band, not
    the digit, is the actionable layer. For statistics use
    pipeline/screeners/regime.py, whose bands are empirical quartiles.

    `positive` is still reported per session: how many of the same measurements
    are on the good side of neutral. It is the explainable number ("11 of 15"),
    the score is the comparable one, and they answer different questions.

    Both are kept: `raw` is the unsmoothed percentile mean, `score` is what the
    chart and the band read.
    """
    empty = {'today': None, 'raw_today': None, 'positive_today': None,
             'n_votes': 0, 'span': _CONDITIONS_SPAN, 'history': []}
    if frame is None or frame.empty:
        return empty

    # Percentiles need the whole run-up, so they are computed on the full frame
    # and sliced afterwards -- ranking the tail alone would score a quiet month
    # against nothing but itself.
    measures = _condition_frame(frame)
    if measures.empty or not len(measures.columns):
        return empty

    neutral = pd.Series({c: _CONDITION_NEUTRAL[c] for c in measures.columns})
    positive = (measures > neutral).sum(axis=1)
    counted = measures.notna().sum(axis=1)
    share = (positive / counted.replace(0, np.nan)) * 100

    tail_start = 0 if days is None else max(0, len(frame) - days)
    raw: List[Dict[str, Any]] = []
    for pos in range(tail_start, len(frame)):
        value = share.iloc[pos]
        if pd.isna(value):
            continue
        raw.append({
            'date': str(frame['date'].iloc[pos]) if 'date' in frame.columns else '',
            'raw': int(round(float(value))),
            'positive': int(positive.iloc[pos]),
            'of': int(counted.iloc[pos]),
        })

    if not raw:
        return empty

    # Seeded on the first value (adjust=False) so the line does not open with a
    # warm-up ramp that would read as a trend nobody traded.
    # Integers out. The score is "how many of fifteen are positive", smoothed;
    # a decimal place would claim a precision the count does not have, and the
    # separation the chart needs already survives rounding (the two April days
    # that used to tie read 97 and 91).
    smoothed = pd.Series([r['raw'] for r in raw], dtype=float) \
        .ewm(span=_CONDITIONS_SPAN, adjust=False).mean()
    history = [{**r, 'score': int(round(float(v)))} for r, v in zip(raw, smoothed)]

    return {
        'today': history[-1]['score'],
        'raw_today': history[-1]['raw'],
        'positive_today': history[-1]['positive'],
        'n_votes': history[-1]['of'],
        'span': _CONDITIONS_SPAN,
        'history': history,
    }


def evaluate(frame: pd.DataFrame, health: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Rule-derived verdict for the last row of `frame`. Pure and total."""
    row = frame.iloc[-1].to_dict()
    if len(frame) >= 2:                  # thrust is back-to-back (thrust_state)
        prev = frame.iloc[-2]
        for c in (THRUST_UP, THRUST_DOWN):
            row['_prev_' + c] = prev.get(c)
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
    n = thrust_count(row)
    t21 = _num(row.get('t2108'))
    z = THRESHOLDS['t2108_zone']
    if t21 is not None and t21 < z['oversold']:
        env = 'OVERSOLD'
        notes.append(f'T2108 below 20 — reversal watch: look for back-to-back {n:.0f}+ up-4% days')
    elif t21 is not None and t21 > z['overbought']:
        env = 'OVERBOUGHT'
        notes.append('T2108 above 80 — chase risk')

    if thrust_state(row) == 'churn':
        notes.append(f'Churn/volatile: back-to-back {n:.0f}+ stocks both up and down 4% — unresolved tape')
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
        'exposure': _EXPOSURE[(env, risk)], 'playbook': render_copy(_PLAYBOOK[env], row),
        'guidance': render_copy(_GUIDANCE[(env, risk)], row),
        'spy_state': spy_state, 'qqq_state': qqq_state, 'alignment': alignment,
        'confirmation': confirmation, 'notes': notes, 'votes': votes,
        'universe_size': _num(row.get('universe_size')),
        'universe_truncated': universe_truncated(row),
        'vote_detail': vote_detail(row, votes,
                                   spy['count'] if spy else None,
                                   qqq['count'] if qqq else None),
    }


# ── Percentile context + per-row codes (spec §1, §3) ─────────────────

# Universe eras (Nighty Zac 2026-09-18, data/research/breadth_universe_break_2026-09-18
# section 8). 2026-06-26: the >=$1B population (~2,590 names) became the whole market
# (upstream stopped honouring cap_1.0to); 2026-08-10: the page cap was lifted and the
# M-Z half came back (~5,620). A raw COUNT from one era is not comparable with another:
# ranking today's up-4% count against the whole archive put it ~39 percentile points
# too high. Ratios (ratio_5d, t2108, McClellan on RANA) are ranked on the whole archive.
UNIVERSE_BREAKS = ('2026-06-26', '2026-08-10')
_COUNT_KEYS = ('up_4pct', 'down_4pct', 'nh_nl_net', 'qtr_spread')
MIN_ERA_RANK_N = 20      # fewer same-era sessions than this: no percentile at all
_STOCKBEE_KEYS = ('up_4pct', 'down_4pct', 'ratio_5d', 'nh_nl_net', 'qtr_spread')
MIN_STOCKBEE_RANK_N = 60  # ours: sessions of the Stockbee column itself before it ranks


def universe_era(day: str) -> int:
    """0 before 06-26, 1 for the capped full-market stretch, 2 from 08-10."""
    return sum(str(day)[:10] >= b for b in UNIVERSE_BREAKS)


def _era_mask(frame: pd.DataFrame) -> pd.Series:
    dates = frame['date'].astype(str)
    today = universe_era(dates.iloc[-1])
    return dates.map(universe_era) == today


def context_basis(frame: pd.DataFrame) -> Dict[str, Any]:
    """What the count percentiles were ranked against: the era's first session and size."""
    if frame is None or len(frame) == 0 or 'date' not in frame:
        return {}
    era = frame[_era_mask(frame)]
    return {'counts_since': str(era['date'].iloc[0])[:10], 'counts_n': int(len(era))}


def percentile_context(frame: pd.DataFrame) -> Dict[str, int]:
    """Today's percentile rank per headline metric.

    Ratios rank against the whole archive; raw counts only against sessions of the
    same universe era (see UNIVERSE_BREAKS), and are omitted when the history
    crosses a break and today's era has fewer than MIN_ERA_RANK_N sessions."""
    def col(name):
        return pd.to_numeric(frame.get(name), errors='coerce') if name in frame \
            else pd.Series([np.nan] * len(frame), index=frame.index)
    # Output keys stay as the page reads them; the values behind them are the
    # Stockbee columns the page prints beside them (2026-09-21, Andy 「用stockbee
    # 口径」). Until then the percentile ranked the retired price-only count while
    # the digit next to it was Stockbee's -- two definitions in one cell.
    derived = {
        'up_4pct': col(THRUST_UP),
        'down_4pct': col(THRUST_DOWN),
        'ratio_5d': col('ratio_5d_stockbee'),
        'nh_nl_net': col('new_highs_common') - col('new_lows_common'),
        'qtr_spread': col('up_25pct_qtr_stockbee') - col('down_25pct_qtr_stockbee'),
    }
    ctx: Dict[str, int] = {}
    era = _era_mask(frame) if 'date' in frame and len(frame) else None
    crossed = era is not None and not bool(era.all())
    for key in ('up_4pct', 'down_4pct', 'ratio_5d', 't2108', 'mcclellan_osc',
                'nh_nl_net', 'qtr_spread'):
        series = derived[key] if key in derived else pd.to_numeric(frame.get(key), errors='coerce')
        if series is None or len(series) == 0:
            continue
        today = series.iloc[-1]
        if pd.isna(today):
            continue
        if key in _COUNT_KEYS and crossed:
            series = series[era.values]
        ranked = series.dropna()
        # Only when the history crosses a break: a young era is too short to rank.
        if key in _COUNT_KEYS and crossed and len(ranked) < MIN_ERA_RANK_N:
            continue
        # A Stockbee column ranks only against its own sessions, and not at all
        # until it has MIN_STOCKBEE_RANK_N of them: a percentile of six days is noise.
        if key in _STOCKBEE_KEYS and len(ranked) < MIN_STOCKBEE_RANK_N:
            continue
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
    verdict['context_basis'] = context_basis(frame)
    # Annotate a copy first: a failure here must not leave breadth_result
    # holding a verdict with missing/partial per-row codes (Spec 2 residual).
    rows = [dict(r) for r in breadth_result.get('history', {}).get('rows', [])]
    annotate_rows(rows, frame, health)
    breadth_result['verdict'] = verdict
    # Market Conditions: the same nine votes as a 0-100 line with two years
    # behind it. Sits beside the verdict rather than inside it -- one is
    # today's decision, the other is where today sits in its own history.
    breadth_result['conditions'] = conditions_series(frame)
    if 'history' in breadth_result:
        breadth_result['history']['rows'] = rows
    return health


def build_replay(frame: pd.DataFrame,
                 spy_hist: Optional[pd.DataFrame],
                 qqq_hist: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """Full point-in-time replay book: every archive date's row + verdict.

    Pure. `verdicts[d]` is computed from the prefix ending at `d` with health
    truncated to `d` by evaluate(), so no date can see the future (Spec 3
    no-peek rule). Health spans the whole input history (days=None) so the
    replay's charts and danger panels reach back as far as the archive.
    """
    health = None
    if spy_hist is not None and qqq_hist is not None \
            and len(spy_hist) >= 50 and len(qqq_hist) >= 50:
        health = market_health(spy_hist, qqq_hist, days=None)

    dates = [str(d) for d in frame['date']]
    rows: Dict[str, Any] = {}
    verdicts: Dict[str, Any] = {}
    for i, d in enumerate(dates):
        raw = frame.iloc[i].to_dict()
        rows[d] = {k: (None if pd.isna(v) else v) for k, v in raw.items()}
        prefix = frame.iloc[:i + 1].reset_index(drop=True)
        verdict = evaluate(prefix, health)
        verdict['context'] = percentile_context(prefix)
        verdict['context_basis'] = context_basis(prefix)
        verdicts[d] = verdict

    health_out = None
    if health is not None:
        health_out = {
            key: {
                'candles': health[key]['candles'],
                'sma20': health[key]['sma20'],
                'sma50': health[key]['sma50'],
                'sma200': health[key]['sma200'],
                'signals_history': health[key]['signals_history'],
            }
            for key in ('spy', 'qqq')
        }

    return {'dates': dates, 'rows': rows, 'verdicts': verdicts, 'health': health_out}
