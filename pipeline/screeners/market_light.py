"""market_light.json -- the course's morning read, Lessons 6 / 6B / 7.

Requested by UI Claire (DATA_CONTRACTS §七, 2026-09-11, e5546418) on Studio Q's
ruling in docs/plans/2026-09-11-market-state-by-the-course.md §五 (L99-L124).
The shape is fixed by the consumer, frontend/src/hooks/useMarketLight.js.

WHAT IS STANDARD HERE AND WHAT IS OURS -- read this before changing a constant.

Three blocks are the course's own definitions, and each one was replicated
against a number the course prints before this file was written (2026-09-11):

  +N / -N      Close vs the 21-day SMA, same-sign runs, runs of <=4 days
               DROPPED (not merged -- merging welds two long runs into one and
               the longest up-run jumps from 68 to 141). Source:
               SwingMasterclass/_pdf/cycle_bench.json. Replicated on
               auto-adjusted SPY and QQQ, 2010-01-01 -> 2026-08-31: all seven
               numbers per ticker match exactly (up_mean 21.4, dn_mean 12.7,
               n_up 125, n_dn 82, longest up 68 from 2025-04-24, longest down
               32 from 2022-04-11 for SPY; QQQ likewise).
  Seven gears  SwingMasterclass/_pdf/charts.py::throttle_gears, copied line for
               line: 21 EMA, each rule overwrites the one before so the highest
               applicable number wins, "slam" = close below today, close above
               yesterday, and the low above the line on >=22 of the prior 30
               sessions. Replicated on MA 2025: slam fires 2025-02-21, first
               maximum defense after it 2025-03-05, gear 1 never fires -- the
               three things the lesson says about that chart.
  Light        Lesson 6 Core drill: SPY daily, 10 vs 20, both rising; 3/3 is
               green, "anything else = RED, sit still" (L6:183).

⚠️ One piece is self-invented and must stay labelled that way (METRIC_SOURCES):
"rising" = MA today > MA yesterday. The course only says "rising / sloping up";
Studio Q ruled this minimum-assumption reading (plan L106) and forbade an
"N days ago" parameter -- the 08-31 invented-window trap.

⚠️ And one course number this does NOT reproduce, reported, not tuned away:
Lesson 6 prints 54.5% green / 20.7% red / 24.8% mixed for SPY 2015-2026. On the
auto-adjusted prices the course's own chart scripts use, this reads 56.5 / 19.3
/ 24.1. The 54.5 matches only on UNadjusted prices (54.7 / 20.5 / 24.8), and
the two "longest run" dates in the same paragraph (2024-01-18 -> 04-04 all yes,
2022-08-30 -> 10-14 all no) reproduce under NO definition tried -- EMA or SMA,
10/20 or 10/21, adjusted or not, "rising" over 1, 2, 3, 5 or 10 days. Under
the 1-day rule the green run is broken on 7 days, every one a single-day dip in
the 10 EMA. That is a course-content issue for Studio Q, the same family as
cycle_bench.json's finding that two hand-typed means had drifted. This file
follows the course's canonical data (auto-adjusted, as `ohlc()` fetches) rather
than switching price basis per metric to make each printed number match.

The brightness block (Q1 setups, Q2 leaders) is our mapping onto the course's
semantics and is shipped `provisional: true` until Studio Q signs off under the
§七 row. The verdict when the light is GREEN needs a combination rule the
course does not give; until it is agreed the verdict is null on green days.
On red days the course decides it alone: avoid.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Lesson 6 light. MA type is a PARAMETER until Andy rules NEEDS_ANDY gap 1
# (the drill text says "MA"; the only measured passage says EMA, L6:135-137).
LIGHT_MA = 'EMA'
FAST, SLOW = 10, 20

# +N count. cycle_bench.json's line is the 21-day SMA; NEEDS_ANDY gap 2 is that
# Lesson 6B also calls the same line an EMA. Parameter, not a literal.
PLUS_N_MA = 'SMA'
PLUS_N_LEN = 21
NOISE_MAX = 4          # runs of this many days or fewer are noise (cycle_bench)

GEAR_LEN = 21          # throttle_gears uses the 21 EMA
HISTORY_DAYS = 60      # the consumer's light strip; Claire asked for >= 60

GEARS = {
    1: ('first exposure', '第一档'),
    2: ('add', '加仓'),
    3: ('press', '踩下去'),
    4: ('ease off', '松油门'),
    5: ('brake', '点刹'),
    6: ('slam the brake', '急刹'),
    7: ('maximum defense', '最大防御'),
}

# Q1 -- which watchlist panels count as "a name you can write a script for
# today under the L10-L11 setups". The `entries` zone is the one titled
# "Can I enter today?"; each panel is tagged with the course setup it serves.
# BO (base-and-break) and HTF (high tight flag) have NO panel today, so this
# count under-reads those two setups -- said in the payload, not hidden.
# `ma_reclaim` is deliberately NOT here. Its recipe is "yesterday's close under
# the MA, today's at/above it" -- climbing back from BELOW. The course's PB is a
# pullback TO the average inside a green-light trend (L10.3), the opposite
# direction; `liquid_leader_pullback` is that one ("0.5-1 ATR from the 21EMA",
# and it cites the course, M2_L09). On 2026-09-10 including ma_reclaim read 43
# names, excluding it 21, and it overlapped the other five panels on only 3 --
# almost pure addition.
Q1_PANELS = {
    'liquid_leader_pullback': 'PB',
    'episodic_pivot': 'EP',
    'll_hl_1st': 'URAR',
    'll_hl_2nd': 'URAR',
    'll_hl_trend_break': 'URAR',
}
Q1_SETUPS_WITHOUT_PANEL = ('BO', 'HTF')


def _ma(s: pd.Series, n: int, kind: str) -> pd.Series:
    if kind == 'EMA':
        return s.ewm(span=n).mean()
    if kind == 'SMA':
        return s.rolling(n).mean()
    raise ValueError(f"ma type must be EMA or SMA, got {kind!r}")


def light_frame(close: pd.Series, ma_type: str = LIGHT_MA,
                fast: int = FAST, slow: int = SLOW) -> pd.DataFrame:
    """Per-day Lesson 6 answers. `rising` = today > yesterday (self-invented,
    see module docstring). A day with any NaN MA has checks_passed = NaN, not 0:
    "not measurable" is not "all three said no"."""
    f, s = _ma(close, fast, ma_type), _ma(close, slow, ma_type)
    out = pd.DataFrame({
        'close': close, 'fast': f, 'slow': s,
        'fast_above_slow': f > s,
        'fast_rising': f > f.shift(1),
        'slow_rising': s > s.shift(1),
    })
    ok = f.notna() & s.notna() & f.shift(1).notna() & s.shift(1).notna()
    n = (out['fast_above_slow'].astype(int) + out['fast_rising'].astype(int)
         + out['slow_rising'].astype(int))
    out['checks_passed'] = n.where(ok)
    return out


def plus_n(close: pd.Series, ma_type: str = PLUS_N_MA,
           length: int = PLUS_N_LEN) -> Optional[int]:
    """Signed length of the CURRENT run of closes on one side of the line.

    The live count is the raw run -- Lesson 6B's ladder starts at +1, so day one
    of a run is +1, not "noise". Whether the run has cleared the <=4-day noise
    band is a separate flag (`plus_n_noise`); the band is what cycle_bench
    drops when it computes cycle statistics, not a reason to hide today's count.
    """
    line = _ma(close, length, ma_type)
    valid = line.notna()
    if not valid.any():
        return None
    above = (close > line)[valid]
    last = bool(above.iloc[-1])
    run = 0
    for v in reversed(above.tolist()):
        if bool(v) != last:
            break
        run += 1
    return run if last else -run


def gear_series(df: pd.DataFrame, length: int = GEAR_LEN) -> pd.Series:
    """Lesson 6B.2's seven gears, verbatim from the course's throttle_gears.

    Highest applicable gear wins because each rule overwrites the last. 0 means
    no gear applies (the course has no name for it). Do not reorder these lines:
    the order IS the precedence."""
    e = df['Close'].ewm(span=length).mean()
    h, l, c, o = (df[x].astype(float) for x in ('High', 'Low', 'Close', 'Open'))
    al = l > e
    run = al.groupby((~al).cumsum()).cumcount() + 1
    g = pd.Series(0, index=df.index)
    g[(c > e) & (c > o)] = 1
    g[al] = 2
    g[al & (run >= 3)] = 3
    g[(l < e) & (c > e)] = 4
    g[c < e] = 5
    g[(c < e) & (c.shift(1) > e) & (al.shift(1).rolling(30).sum() >= 22)] = 6
    g[h < e] = 7
    return g


def instrument_block(df: pd.DataFrame, light_ma: str = LIGHT_MA,
                     plus_n_ma: str = PLUS_N_MA) -> Optional[Dict[str, Any]]:
    """One ticker's light + count + gear + 60-day strip. None if unusable."""
    if df is None or len(df) < SLOW + 2 or 'Close' not in df:
        return None
    lf = light_frame(df['Close'].astype(float), light_ma)
    today = lf.iloc[-1]
    if pd.isna(today['checks_passed']):
        return None
    prev = lf.iloc[-2]
    checks = [
        {'key': 'fast_above_slow', 'pass': bool(today['fast_above_slow']),
         'a': round(float(today['fast']), 4), 'b': round(float(today['slow']), 4)},
        {'key': 'fast_rising', 'pass': bool(today['fast_rising']),
         'a': round(float(today['fast']), 4), 'b': round(float(prev['fast']), 4)},
        {'key': 'slow_rising', 'pass': bool(today['slow_rising']),
         'a': round(float(today['slow']), 4), 'b': round(float(prev['slow']), 4)},
    ]
    passed = int(today['checks_passed'])
    pn = plus_n(df['Close'].astype(float), plus_n_ma)
    gear = None
    if {'Open', 'High', 'Low'} <= set(df.columns):
        gn = int(gear_series(df).iloc[-1])
        gear = {'n': gn, 'label': GEARS[gn][0] if gn else None,
                'label_zh': GEARS[gn][1] if gn else None}
    hist = lf.dropna(subset=['checks_passed']).tail(HISTORY_DAYS)
    return {
        'checks': checks,
        'checks_passed': passed,
        'light': 'green' if passed == 3 else 'red',
        'plus_n': pn,
        'plus_n_noise': (abs(pn) <= NOISE_MAX) if pn is not None else None,
        'gear': gear,
        'history': [
            {'date': d.strftime('%Y-%m-%d'), 'close': round(float(r['close']), 4),
             'fast': round(float(r['fast']), 4), 'slow': round(float(r['slow']), 4),
             'checks_passed': int(r['checks_passed'])}
            for d, r in hist.iterrows()
        ],
    }


def setups_block(watchlist: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """Q1 -- unique names across the setup-bearing panels. Provisional."""
    if not watchlist or not watchlist.get('zones'):
        return None
    names: set = set()
    by_panel: Dict[str, int] = {}
    capped: List[str] = []
    seen_panel = False
    for zone in watchlist['zones']:
        for p in zone.get('panels', []):
            key = p.get('key')
            if key not in Q1_PANELS:
                continue
            seen_panel = True
            # ⚠️ The panel's list lives under `tickers`, not `rows`. The first
            # version read `rows`, got nothing, and reported count 0 on a day
            # ma_reclaim alone had 25 names -- caught only because the
            # end-to-end run was checked against the panel sizes by hand.
            rows = p.get('tickers') or []
            tickers = {str(r.get('ticker')).upper() for r in rows
                       if isinstance(r, Mapping) and r.get('ticker')}
            # `count` is the panel's own pre-truncation total; the list is cut
            # for display and `truncated` says so. Read the flag, do not infer
            # it from the list happening to be 25 long.
            by_panel[key] = int(p['count']) if p.get('count') is not None else len(tickers)
            if p.get('truncated'):
                capped.append(key)
            names |= tickers
    if not seen_panel:
        return None
    count = len(names)
    return {
        'count': count,
        'count_is_floor': bool(capped),
        'band': 'bright' if count >= 10 else ('none' if count == 0 else
                                             ('dim' if count <= 3 else 'unspecified')),
        'by_panel': by_panel,
        'capped_panels': capped,
        'setups_without_panel': list(Q1_SETUPS_WITHOUT_PANEL),
        'provisional': True,
    }


def leaders_block(groups: Optional[Mapping[str, Any]],
                  ladder: Optional[Mapping[str, Any]],
                  universe_rows: Optional[Iterable[Mapping[str, Any]]],
                  n: int = 10) -> Optional[Dict[str, Any]]:
    """Q2 -- the strongest names of the current thematic wave, each with a
    status. Provisional. Only `kind == 'theme'` groups count: the lesson says
    "current thematic wave", and factor groups (Small Caps, High Beta) are not
    one. Status is binary on purpose -- see STATUS_RULE."""
    if not groups or not ladder or universe_rows is None:
        return None
    states = ladder.get('themes') or {}
    leading = {name for name, rungs in states.items()
               if isinstance(rungs, Mapping) and rungs.get('2w') == 'Leading'}
    members: Dict[str, str] = {}
    for g in groups.get('themes', []):
        if g.get('kind') != 'theme' or g.get('group') not in leading:
            continue
        for t in g.get('tickers') or []:
            members.setdefault(str(t).upper(), g['group'])
    if not members:
        return {'leaders': [], 'themes': sorted(leading), 'provisional': True}
    by_t = {str(r.get('ticker')).upper(): r for r in universe_rows}
    # rs_rating is a 1-99 integer and the top of a leading theme is a wall of
    # 97-99 ties; ranking on it alone makes the ten names reshuffle night to
    # night by dict order -- a fake "change" on the page. Ties break on the
    # continuous 3-month performance, then the ticker, so the list is stable.
    def _key(t):
        r = by_t[t]
        return (-(r.get('rs_rating') or 0), -(r.get('perf_3m') or float('-inf')), t)
    ranked = sorted((t for t in members if t in by_t and by_t[t].get('rs_rating') is not None),
                    key=_key)[:n]
    out = []
    for t in ranked:
        r = by_t[t]
        close, ema21 = r.get('close'), r.get('ema21')
        out.append({'ticker': t, 'theme': members[t], 'status': _status(r),
                    'above_ema21': (bool(close >= ema21) if close is not None and ema21 is not None else None),
                    'rs_rating': r.get('rs_rating')})
    return {'leaders': out, 'themes': sorted({members[t] for t in ranked}),
            'status_rule': STATUS_RULE, 'provisional': True}


STATUS_RULE = ("holding = above the 50 SMA, the line Lesson 6B gives to institutions; "
               "broken = below it. Whether the name also holds the 21 EMA (swing money) "
               "is reported beside it as above_ema21, not folded into the label. The course's "
               "three healthy sub-states (holding / extending / basing) all read "
               "'bright', so the verdict only needs healthy-vs-broken; splitting "
               "them would need thresholds the course does not give. Gap-down is "
               "not yet applied: with a zero threshold nearly every red open would "
               "count as broken -- threshold to agree with Studio Q.")


def _status(r: Mapping[str, Any]) -> Optional[str]:
    """Binary on the 50 SMA. The first version also required the 21 EMA and
    returned None for a name between the two lines -- above the institutions'
    line, below the swing line -- which is a pullback inside a healthy trend,
    not "unknown". A None there rendered as "not measured" for a name we had
    measured perfectly well."""
    sma50 = r.get('sma50_dist')
    if sma50 is None:
        return None
    return 'broken' if sma50 < 0 else 'holding'


def verdict(spy: Optional[Mapping[str, Any]]) -> Optional[str]:
    """Red decides it alone -- 'avoid' (L6:183, "sit still"). Green needs a rule
    for combining the three brightness questions that the course does not give;
    until Studio Q and DATA agree it under the §七 row, green returns None."""
    if not spy:
        return None
    return 'avoid' if spy.get('light') == 'red' else None


def build(histories: Mapping[str, pd.DataFrame],
          watchlist: Optional[Mapping[str, Any]] = None,
          groups: Optional[Mapping[str, Any]] = None,
          ladder: Optional[Mapping[str, Any]] = None,
          universe_rows: Optional[Iterable[Mapping[str, Any]]] = None,
          light_ma: str = LIGHT_MA, plus_n_ma: str = PLUS_N_MA) -> Dict[str, Any]:
    spy = instrument_block(histories.get('SPY'), light_ma, plus_n_ma)
    qqq = instrument_block(histories.get('QQQ'), light_ma, plus_n_ma)
    # ⚠️ The consumer reads `brightness.leaders` as an ARRAY of
    # {ticker, theme, status} (useMarketLight.js). The first version nested the
    # list inside an object with its metadata, so the page would have received
    # a dict where it maps over a list and drawn nothing. The list goes where
    # the contract says; the metadata sits beside it under `leaders_meta`.
    lb = leaders_block(groups, ladder, universe_rows)
    date = spy['history'][-1]['date'] if spy and spy['history'] else None
    return {
        'date': date,
        'ma_type': light_ma,
        'plus_n_ma': plus_n_ma,
        'rising_rule': 'MA today > MA yesterday (self-invented operationalization, plan L106)',
        'spy': spy,
        'qqq': qqq,            # side note only -- never enters the verdict (plan L111)
        'brightness': {
            'setups': setups_block(watchlist),
            'leaders': lb['leaders'] if lb else None,
            'leaders_meta': ({k: v for k, v in lb.items() if k != 'leaders'} if lb else None),
        },
        'verdict': verdict(spy),
        'verdict_pending': (None if (spy and spy.get('light') == 'red') else
                            'green-day combination rule not yet agreed with Studio Q'),
    }
