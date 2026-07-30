# Breadth Signal Engine + Decision-First UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rule-derived market verdict (Stockbee absolutes + our-history percentiles) computed in Python, SPY/QQQ danger signals in a new `market_health.json`, and a decision-first breadth page: verdict banner, state summary, health/ratio/spread charts, danger panels, dashboard chip.

**Architecture:** New pure-function engine `pipeline/screeners/breadth_signals.py` evaluates any archive prefix + market-health snapshot into a verdict (Spec 3 replay depends on this purity). `run_all.py` wires it after the breadth step and writes `market_health.json`. The frontend only renders precomputed JSON. Spec: `docs/plans/2026-07-31-breadth-signal-engine-design.md`.

**Tech Stack:** Python 3.11+/pandas/pytest · React 19 · lightweight-charts v5 · Tailwind 4

## Global Constraints

- `evaluate()` / `market_health()` / `percentile_context()` are **pure**: no I/O, no clock, no reads of anything outside their arguments. NaN inputs vote neutral; the engine never raises.
- No `date.today()` / `datetime.now()` anywhere (repo guard test `tests/test_no_naive_clock.py`).
- `breadth.json` stays additive-only: existing keys untouched; additions are `verdict` (latest block) and per-row `v` codes.
- Threshold values are the spec's exact numbers (§1 THRESHOLDS table); they live in ONE module-level `THRESHOLDS` dict and nothing else hardcodes them.
- Verdict prose is EN-only, from keyed template tables (i18n-ready structure).
- Frontend has no JS test harness — do not add one; frontend tasks are verified in-browser at the end (Task 12).
- Run Python tests with `python3 -m pytest` from the repo root. Known baseline: 4 pre-existing failures in `pipeline/tests/test_content_processor.py` — ignore them.
- Anti-dopamine palette: use existing CSS vars (`--color-profit`, `--color-loss`, `--color-signal-caution`, `--color-surface`, `--color-border`, `--color-text*`); no raw saturated hexes in JSX.

---

### Task 1: THRESHOLDS table + breadth votes

**Files:**
- Create: `pipeline/screeners/breadth_signals.py`
- Create: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Produces: `THRESHOLDS: dict` (keys exactly: `ratio_5d, ratio_10d, thrust, qtr_spread, spread_13_34, mcclellan, nh_nl, pct200, t2108_zone, spy_danger, qqq_danger, bench_trend`); `breadth_votes(row: dict) -> dict[str, str]` returning `'bull'|'bear'|'neutral'` for the 9 breadth-only keys (all except `spy_danger, qqq_danger, bench_trend`). `row` is one archive row as a dict (values may be None/NaN → neutral).

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_breadth_signals.py`:

```python
"""Tests for the breadth signal engine (Spec 2)."""
import math
import numpy as np
import pandas as pd
import pytest


def _row(**kw):
    base = {
        'ratio_5d': 1.2, 'ratio_10d': 1.1, 'up_4pct': 150, 'down_4pct': 100,
        'up_25pct_qtr': 400, 'down_25pct_qtr': 300,
        'up_13pct_34d': 500, 'down_13pct_34d': 400,
        'mcclellan_osc': 10.0, 'new_highs': 30, 'new_lows': 10,
        'pct_above_200sma': 55.0, 't2108': 50.0,
    }
    base.update(kw)
    return base


class TestBreadthVotes:
    def test_all_keys_present_and_valid(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        votes = breadth_votes(_row())
        assert set(votes) == {'ratio_5d', 'ratio_10d', 'thrust', 'qtr_spread',
                              'spread_13_34', 'mcclellan', 'nh_nl', 'pct200',
                              't2108_zone'}
        assert all(v in ('bull', 'bear', 'neutral') for v in votes.values())

    def test_ratio_boundaries(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(ratio_5d=1.0))['ratio_5d'] == 'bull'
        assert breadth_votes(_row(ratio_5d=0.99))['ratio_5d'] == 'neutral'
        assert breadth_votes(_row(ratio_5d=0.5))['ratio_5d'] == 'neutral'
        assert breadth_votes(_row(ratio_5d=0.49))['ratio_5d'] == 'bear'

    def test_thrust_rules(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(up_4pct=300, down_4pct=50))['thrust'] == 'bull'
        assert breadth_votes(_row(up_4pct=50, down_4pct=300))['thrust'] == 'bear'
        # both >= 300 -> churn, neutral vote
        assert breadth_votes(_row(up_4pct=350, down_4pct=320))['thrust'] == 'neutral'
        assert breadth_votes(_row(up_4pct=299, down_4pct=100))['thrust'] == 'neutral'

    def test_spreads_and_mcclellan_and_nhnl(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        v = breadth_votes(_row(up_25pct_qtr=100, down_25pct_qtr=200,
                               up_13pct_34d=100, down_13pct_34d=200,
                               mcclellan_osc=-5.0, new_highs=3, new_lows=9))
        assert v['qtr_spread'] == 'bear'
        assert v['spread_13_34'] == 'bear'
        assert v['mcclellan'] == 'bear'
        assert v['nh_nl'] == 'bear'
        assert breadth_votes(_row(up_25pct_qtr=200, down_25pct_qtr=200))['qtr_spread'] == 'neutral'

    def test_pct200_zones(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(pct_above_200sma=50.0))['pct200'] == 'bull'
        assert breadth_votes(_row(pct_above_200sma=40.0))['pct200'] == 'neutral'
        assert breadth_votes(_row(pct_above_200sma=29.9))['pct200'] == 'bear'

    def test_t2108_zones(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        assert breadth_votes(_row(t2108=70.0))['t2108_zone'] == 'bull'
        assert breadth_votes(_row(t2108=30.0))['t2108_zone'] == 'bear'
        assert breadth_votes(_row(t2108=50.0))['t2108_zone'] == 'neutral'
        # extremes vote neutral here — overrides handle them at composition
        assert breadth_votes(_row(t2108=10.0))['t2108_zone'] == 'neutral'
        assert breadth_votes(_row(t2108=90.0))['t2108_zone'] == 'neutral'

    def test_nan_and_none_vote_neutral(self):
        from pipeline.screeners.breadth_signals import breadth_votes
        v = breadth_votes(_row(ratio_5d=None, mcclellan_osc=float('nan'),
                               t2108=None, up_4pct=None))
        assert v['ratio_5d'] == 'neutral'
        assert v['mcclellan'] == 'neutral'
        assert v['t2108_zone'] == 'neutral'
        assert v['thrust'] == 'neutral'

    def test_thresholds_single_source(self):
        from pipeline.screeners import breadth_signals
        assert breadth_signals.THRESHOLDS['thrust']['count'] == 300
        assert breadth_signals.THRESHOLDS['t2108_zone']['oversold'] == 20
        assert breadth_signals.THRESHOLDS['t2108_zone']['overbought'] == 80
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: FAIL with "No module named 'pipeline.screeners.breadth_signals'".

- [ ] **Step 3: Implement**

Create `pipeline/screeners/breadth_signals.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): THRESHOLDS table + breadth-rule votes"
```

---

### Task 2: Stochastics + danger signals

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py`
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Consumes: a yfinance daily history DataFrame with columns `Close`, `High`, `Low` (DatetimeIndex ascending).
- Produces:
  - `compute_stochastics(hist: pd.DataFrame) -> tuple[pd.Series, pd.Series]` — (fast, slow): raw %K = (C−L14)/(H14−L14)×100 with H14==L14 carrying the previous raw forward (seed 50.0); fast = SMA3(raw); slow = SMA3(fast).
  - `danger_signals(hist: pd.DataFrame) -> dict[str, bool]` — keys exactly `below_20sma, stoch_cross, stoch_down, lower_lows, close_below_lows`, evaluated on the last bar.
  - `warn_counts(hist: pd.DataFrame, days: int = 130) -> list[dict]` — `[{'date': 'YYYY-MM-DD', 'count': int}]` for the trailing `days` sessions (count = how many of the 5 signals fired that day).

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
def _hist(closes, highs=None, lows=None, end='2026-07-29'):
    n = len(closes)
    idx = pd.bdate_range(end=end, periods=n)
    return pd.DataFrame({
        'Close': closes,
        'High': highs if highs is not None else [c + 1 for c in closes],
        'Low': lows if lows is not None else [c - 1 for c in closes],
    }, index=idx)


class TestStochastics:
    def test_hand_computed_with_fixed_range(self):
        from pipeline.screeners.breadth_signals import compute_stochastics
        # Highs pinned at 100, lows at 0 -> raw %K == close, hand-computable
        closes = [50.0] * 14 + [80.0, 60.0, 40.0]
        hist = _hist(closes, highs=[100.0] * 17, lows=[0.0] * 17)
        fast, slow = compute_stochastics(hist)
        assert fast.iloc[-1] == pytest.approx((80 + 60 + 40) / 3)
        # slow = SMA3(fast): fast[-3..-1] = mean(50,50,80), mean(50,80,60), mean(80,60,40)
        f3 = [(50 + 50 + 80) / 3, (50 + 80 + 60) / 3, (80 + 60 + 40) / 3]
        assert slow.iloc[-1] == pytest.approx(sum(f3) / 3)

    def test_flat_market_carries_forward_no_nan(self):
        from pipeline.screeners.breadth_signals import compute_stochastics
        hist = _hist([100.0] * 20, highs=[100.0] * 20, lows=[100.0] * 20)
        fast, slow = compute_stochastics(hist)
        assert not fast.tail(5).isna().any()
        assert fast.iloc[-1] == pytest.approx(50.0)  # seeded carry-forward

    def test_rising_market_pegs_100(self):
        from pipeline.screeners.breadth_signals import compute_stochastics
        closes = [100.0 + i for i in range(30)]
        hist = _hist(closes, highs=closes, lows=[c for c in closes])
        # highs == closes rising -> close is always the 14d high -> raw = 100
        fast, slow = compute_stochastics(hist)
        assert fast.iloc[-1] == pytest.approx(100.0)
        assert slow.iloc[-1] == pytest.approx(100.0)


class TestDangerSignals:
    def test_healthy_tape_no_signals(self):
        from pipeline.screeners.breadth_signals import danger_signals
        closes = [100.0 + i for i in range(40)]   # rising, above SMA20
        hist = _hist(closes)
        sig = danger_signals(hist)
        assert set(sig) == {'below_20sma', 'stoch_cross', 'stoch_down',
                            'lower_lows', 'close_below_lows'}
        assert sig['below_20sma'] is False
        assert sig['lower_lows'] is False
        assert sig['close_below_lows'] is False

    def test_breakdown_tape_fires_price_signals(self):
        from pipeline.screeners.breadth_signals import danger_signals
        closes = [100.0] * 30 + [95.0, 90.0, 85.0, 80.0]  # sharp break
        lows = [99.0] * 30 + [94.0, 89.0, 84.0, 79.0]      # 3+ lower lows
        hist = _hist(closes, lows=lows)
        sig = danger_signals(hist)
        assert sig['below_20sma'] is True
        assert sig['lower_lows'] is True     # 79 < 84 < 89 < 94
        assert sig['close_below_lows'] is True  # 80 < min(94, 89, 84)
        assert sig['stoch_cross'] is True    # falling tape: fast under slow
        assert sig['stoch_down'] is True

    def test_warn_counts_shape(self):
        from pipeline.screeners.breadth_signals import warn_counts
        closes = [100.0 + (i % 7) - 3 for i in range(200)]
        hist = _hist(closes)
        wc = warn_counts(hist, days=130)
        assert len(wc) == 130
        assert set(wc[0]) == {'date', 'count'}
        assert all(0 <= w['count'] <= 5 for w in wc)
        assert wc[-1]['date'] == hist.index[-1].strftime('%Y-%m-%d')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestStochastics pipeline/tests/test_breadth_signals.py::TestDangerSignals -v`
Expected: FAIL with import errors.

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_signals.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS. If `test_breakdown_tape_fires_price_signals` fails on
`stoch_cross`, print `compute_stochastics(hist)[0].tail()` vs `[1].tail()` —
a 30-flat-then-4-down fixture must have fast below slow by the last bar.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): stochastics + five SPY/QQQ danger signals"
```

---

### Task 3: market_health assembly + truncation

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py`
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Produces:
  - `market_health(spy_hist: pd.DataFrame, qqq_hist: pd.DataFrame, days: int = 130) -> dict` — `{'spy': {...}, 'qqq': {...}}`; per ticker: `candles` `[{date,o,h,l,c}]` (trailing `days`, floats rounded 2dp), `sma20`/`sma50`/`sma200` (same length, aligned to candles, None where insufficient history), `danger` `{'signals': {...5 bools}, 'count': int}`, `warn_history` (from `warn_counts`). Requires `Open` column in addition to Close/High/Low.
  - `truncate_health(health: dict, date_iso: str) -> dict | None` — same shape with all per-date arrays cut to dates ≤ `date_iso`; `danger.count` recomputed from the truncated `warn_history` last entry; returns None if no dates remain.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_signals.py` (extend `_hist` usage with an Open column via a helper):

```python
def _ohlc(closes, end='2026-07-29'):
    h = _hist(closes, end=end)
    h['Open'] = h['Close'].shift(1).fillna(h['Close'])
    return h


class TestMarketHealth:
    def test_shape_and_alignment(self):
        from pipeline.screeners.breadth_signals import market_health
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = market_health(spy, qqq, days=130)
        for key in ('spy', 'qqq'):
            blk = health[key]
            assert len(blk['candles']) == 130
            assert len(blk['sma20']) == len(blk['sma50']) == len(blk['sma200']) == 130
            assert set(blk['candles'][0]) == {'date', 'o', 'h', 'l', 'c'}
            assert set(blk['danger']) == {'signals', 'count'}
            assert blk['danger']['count'] == sum(blk['danger']['signals'].values())
            assert len(blk['warn_history']) == 130
            assert blk['warn_history'][-1]['date'] == blk['candles'][-1]['date']

    def test_truncate_health(self):
        from pipeline.screeners.breadth_signals import market_health, truncate_health
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = market_health(spy, qqq, days=130)
        cut_date = health['spy']['candles'][99]['date']
        t = truncate_health(health, cut_date)
        assert len(t['spy']['candles']) == 100
        assert t['spy']['candles'][-1]['date'] == cut_date
        assert t['spy']['danger']['count'] == t['spy']['warn_history'][-1]['count']
        assert truncate_health(health, '1990-01-01') is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestMarketHealth -v`
Expected: FAIL with import error.

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_signals.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): market_health payload + prefix truncation"
```

---

### Task 4: Verdict composition (evaluate)

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py`
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Consumes: `breadth_votes`, `THRESHOLDS`, `truncate_health` output shape.
- Produces: `evaluate(frame: pd.DataFrame, health: dict | None) -> dict` with keys exactly:
  `env` (`'BULLISH'|'MIXED'|'BEARISH'|'OVERSOLD'|'OVERBOUGHT'`), `score` (int),
  `risk` (`'Low'|'Elevated'|'High'`), `warn_total` (int 0-10),
  `exposure`, `playbook`, `guidance` (strings from template tables),
  `spy_state`/`qqq_state` (`'Uptrend'|'Mixed'|'Downtrend'` or None when health is None),
  `alignment` (`'Aligned'|'Divergent'` or None), `confirmation` (string),
  `notes` (list of strings), `votes` (dict of all 12 rule votes).
  `frame` = archive prefix (last row is "today"); health pre-truncated by caller or full (evaluate truncates internally to the frame's last date).

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
def _frame(rows):
    return pd.DataFrame(rows)


def _bull_row(**kw):
    return _row(ratio_5d=1.5, ratio_10d=1.3, up_4pct=350, down_4pct=80,
                up_25pct_qtr=500, down_25pct_qtr=200, up_13pct_34d=700,
                down_13pct_34d=300, mcclellan_osc=25.0, new_highs=40,
                new_lows=5, pct_above_200sma=62.0, t2108=65.0, **kw)


def _bear_row(**kw):
    return _row(ratio_5d=0.3, ratio_10d=0.4, up_4pct=60, down_4pct=400,
                up_25pct_qtr=150, down_25pct_qtr=600, up_13pct_34d=200,
                down_13pct_34d=800, mcclellan_osc=-40.0, new_highs=2,
                new_lows=30, pct_above_200sma=25.0, t2108=28.0, **kw)


def _health_stub(spy_count=0, qqq_count=0, close=100.0, sma20=95.0,
                 sma50=90.0, sma200=85.0, date='2026-07-29'):
    def blk(count):
        return {'candles': [{'date': date, 'o': close, 'h': close, 'l': close, 'c': close}],
                'sma20': [sma20], 'sma50': [sma50], 'sma200': [sma200],
                'danger': {'signals': {}, 'count': count},
                'warn_history': [{'date': date, 'count': count}]}
    return {'spy': blk(spy_count), 'qqq': blk(qqq_count)}


class TestEvaluate:
    def test_clean_bull_day(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bull_row()}])
        v = evaluate(frame, _health_stub())
        assert v['env'] == 'BULLISH'
        assert v['risk'] == 'Low'
        assert v['spy_state'] == 'Uptrend' and v['qqq_state'] == 'Uptrend'
        assert v['alignment'] == 'Aligned'
        assert 'Confirmed bull' in v['confirmation']
        assert len(v['votes']) == 12

    def test_clean_bear_day(self):
        from pipeline.screeners.breadth_signals import evaluate
        health = _health_stub(spy_count=5, qqq_count=4, close=80.0,
                              sma20=95.0, sma50=100.0, sma200=105.0)
        frame = _frame([{'date': '2026-07-29', **_bear_row()}])
        v = evaluate(frame, health)
        assert v['env'] == 'BEARISH'
        assert v['risk'] == 'High'          # 5 + 4 = 9 warnings
        assert v['spy_state'] == 'Downtrend'
        assert 'Confirmed bear' in v['confirmation']

    def test_oversold_override_outranks_score(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bear_row(t2108=15.0)}])
        v = evaluate(frame, _health_stub(spy_count=5, qqq_count=5))
        assert v['env'] == 'OVERSOLD'
        assert any('thrust' in n.lower() or 'reversal' in n.lower() for n in v['notes'])

    def test_overbought_override(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bull_row(t2108=85.0)}])
        v = evaluate(frame, _health_stub())
        assert v['env'] == 'OVERBOUGHT'

    def test_churn_day_noted(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_row(up_4pct=400, down_4pct=380)}])
        v = evaluate(frame, _health_stub())
        assert any('churn' in n.lower() or 'volatile' in n.lower() for n in v['notes'])

    def test_health_none_degrades(self):
        from pipeline.screeners.breadth_signals import evaluate
        frame = _frame([{'date': '2026-07-29', **_bull_row()}])
        v = evaluate(frame, None)
        assert v['spy_state'] is None and v['alignment'] is None
        assert v['warn_total'] == 0 and v['risk'] == 'Low'
        assert any('price signals unavailable' in n.lower() for n in v['notes'])
        assert v['votes']['spy_danger'] == 'neutral'

    def test_mixed_day_and_disagreement_named(self):
        from pipeline.screeners.breadth_signals import evaluate
        # Genuinely split tape: 3 bull votes (ratio_10d, 13/34 spread, bench),
        # 3 bear votes (qtr spread, mcclellan, nh_nl), rest neutral -> score 0.
        frame = _frame([{'date': '2026-07-29',
                         **_row(ratio_5d=0.6, ratio_10d=1.2,
                                up_25pct_qtr=200, down_25pct_qtr=300,
                                up_13pct_34d=500, down_13pct_34d=400,
                                mcclellan_osc=-5.0, new_highs=10, new_lows=20,
                                pct_above_200sma=45.0, t2108=50.0)}])
        v = evaluate(frame, _health_stub(spy_count=2, qqq_count=3))
        assert v['env'] == 'MIXED'
        assert 'Inconclusive' in v['confirmation']
        assert 'disagree' in v['confirmation']

    def test_prefix_purity(self):
        """A prefix's verdict must not change when later rows exist (Spec 3 replay guard)."""
        from pipeline.screeners.breadth_signals import evaluate
        prefix_rows = [{'date': '2026-07-27', **_bull_row()},
                       {'date': '2026-07-28', **_bull_row()}]
        v_alone = evaluate(_frame(prefix_rows), None)
        # Same prefix sliced out of a longer frame that ends with a bear day
        full = _frame(prefix_rows + [{'date': '2026-07-29', **_bear_row()}])
        v_sliced = evaluate(full.iloc[:2].reset_index(drop=True), None)
        assert v_alone == v_sliced
        assert v_alone['env'] == 'BULLISH'   # the later bear row leaked nothing
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestEvaluate -v`
Expected: FAIL with "cannot import name 'evaluate'".

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_signals.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): verdict composition — score, overrides, states, templates"
```

---

### Task 5: Percentile context + per-row verdict codes

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py`
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Produces:
  - `percentile_context(frame: pd.DataFrame) -> dict[str, int]` — keys `up_4pct, down_4pct, ratio_5d, t2108, mcclellan_osc, nh_nl_net, qtr_spread`; each = integer percentile rank of today's value vs the whole frame (`(col <= today).mean() * 100`, rounded). Missing today-value → key omitted.
  - `annotate_rows(rows: list[dict], frame: pd.DataFrame, health: dict | None) -> None` — mutates each row dict in `rows` (the breadth.json history rows), adding `'v': {'env': str, 'risk': str, 'warn': int}` computed by evaluating the archive prefix ending at that row's date. Rows whose date is not in `frame` get `v = None`.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
class TestPercentileContext:
    def test_ranks_on_known_frame(self):
        from pipeline.screeners.breadth_signals import percentile_context
        rows = [{'date': f'2026-07-{d:02d}', **_row(down_4pct=d * 10)} for d in range(1, 11)]
        frame = _frame(rows)   # down_4pct: 10..100, today = 100 -> 100th pctile
        ctx = percentile_context(frame)
        assert ctx['down_4pct'] == 100
        assert 0 <= ctx['t2108'] <= 100
        assert 'qtr_spread' in ctx and 'nh_nl_net' in ctx

    def test_missing_today_value_omitted(self):
        from pipeline.screeners.breadth_signals import percentile_context
        rows = [{'date': '2026-07-28', **_row()},
                {'date': '2026-07-29', **_row(mcclellan_osc=None)}]
        ctx = percentile_context(_frame(rows))
        assert 'mcclellan_osc' not in ctx


class TestAnnotateRows:
    def test_rows_get_codes_matching_prefix_evaluate(self):
        from pipeline.screeners.breadth_signals import annotate_rows, evaluate
        rows_data = [{'date': '2026-07-27', **_bull_row()},
                     {'date': '2026-07-28', **_bear_row()},
                     {'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows_data)
        json_rows = [dict(r) for r in rows_data]
        annotate_rows(json_rows, frame, None)
        for i, jr in enumerate(json_rows):
            expect = evaluate(frame.iloc[:i + 1].reset_index(drop=True), None)
            assert jr['v'] == {'env': expect['env'], 'risk': expect['risk'],
                               'warn': expect['warn_total']}

    def test_unknown_date_gets_none(self):
        from pipeline.screeners.breadth_signals import annotate_rows
        frame = _frame([{'date': '2026-07-29', **_bull_row()}])
        json_rows = [{'date': '1999-01-01'}]
        annotate_rows(json_rows, frame, None)
        assert json_rows[0]['v'] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestPercentileContext pipeline/tests/test_breadth_signals.py::TestAnnotateRows -v`
Expected: FAIL with import errors.

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_signals.py`:

```python
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
        ctx[key] = int(round(float((series <= today).mean()) * 100))
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): percentile context + per-row verdict codes"
```

---

### Task 6: Pipeline wiring — fetch_ma_data history + run_all integration

**Files:**
- Modify: `pipeline/adapters/yfinance_adapter.py` (`fetch_ma_data`, ~line 499)
- Modify: `pipeline/screeners/run_all.py` (breadth try/except block ~line 290-311, and the guarded breadth.json write ~line 349-356)
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Consumes: everything from Tasks 1-5.
- Produces:
  - `fetch_ma_data(tickers=None, return_history=False)` — default behavior unchanged; with `return_history=True` returns `(signals, histories)` where `histories: dict[str, pd.DataFrame]` holds each ticker's full downloaded 1y OHLC frame.
  - `run_signals(breadth_result: dict, frame: pd.DataFrame, spy_hist, qqq_hist) -> dict | None` in `breadth_signals.py` — orchestrator: builds health (or None if either hist is None/too short), attaches `breadth_result['verdict']` (evaluate + `context` from percentile_context), annotates `breadth_result['history']['rows']`, returns the market_health payload (or None). Pure except for mutating `breadth_result`.
  - `run_all.py` writes `data/output/market_health.json` as `{'timestamp': <same timestamp var used for other outputs>, 'stale': False, **health}` when health is not None; when the signals step fails or health is None and a previous `market_health.json` exists, it rewrites that file with `stale: true`; breadth.json write itself is unchanged in location and guard.

- [ ] **Step 1: Write the failing test (run_signals orchestration)**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
class TestRunSignals:
    def _breadth_result(self, rows):
        return {'history': {'rows': [dict(r) for r in rows]}, 'mm': {}, 'breadth': {}}

    def test_attaches_verdict_context_and_row_codes(self):
        from pipeline.screeners.breadth_signals import run_signals
        rows = [{'date': '2026-07-28', **_bull_row()},
                {'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows)
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        result = self._breadth_result(rows)
        health = run_signals(result, frame, spy, qqq)
        assert health is not None and 'spy' in health and 'qqq' in health
        assert result['verdict']['env'] in ('BULLISH', 'MIXED', 'BEARISH',
                                            'OVERSOLD', 'OVERBOUGHT')
        assert 'context' in result['verdict']
        assert all('v' in r for r in result['history']['rows'])

    def test_none_history_degrades(self):
        from pipeline.screeners.breadth_signals import run_signals
        rows = [{'date': '2026-07-29', **_bull_row()}]
        result = self._breadth_result(rows)
        health = run_signals(result, _frame(rows), None, None)
        assert health is None
        assert result['verdict']['spy_state'] is None
        assert any('unavailable' in n for n in result['verdict']['notes'])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestRunSignals -v`
Expected: FAIL with "cannot import name 'run_signals'".

- [ ] **Step 3: Implement run_signals**

Append to `pipeline/screeners/breadth_signals.py`:

```python
def run_signals(breadth_result: Dict[str, Any], frame: pd.DataFrame,
                spy_hist: Optional[pd.DataFrame],
                qqq_hist: Optional[pd.DataFrame]) -> Optional[Dict[str, Any]]:
    """Attach verdict + row codes to a breadth.json payload; return health dict."""
    health = None
    if spy_hist is not None and qqq_hist is not None \
            and len(spy_hist) >= 50 and len(qqq_hist) >= 50:
        health = market_health(spy_hist, qqq_hist)
    verdict = evaluate(frame, health)
    verdict['context'] = percentile_context(frame)
    breadth_result['verdict'] = verdict
    annotate_rows(breadth_result.get('history', {}).get('rows', []), frame, health)
    return health
```

- [ ] **Step 4: Extend fetch_ma_data**

In `pipeline/adapters/yfinance_adapter.py`, change the signature at ~line 499:

```python
    def fetch_ma_data(self, tickers: list[str] = None, return_history: bool = False):
```

At the top of the function body add `histories = {}`. Inside the per-ticker
loop, immediately after the `hist = _flatten_yf_columns(...)` /
insufficient-history check succeeds, add:

```python
                histories[ticker] = hist
```

At the end of the function, replace `return signals` with:

```python
        if return_history:
            return signals, histories
        return signals
```

- [ ] **Step 5: Wire run_all.py**

In `pipeline/screeners/run_all.py`:

1. Change the fetch call (~line 288):

```python
    signals, ma_histories = yf_adapter.fetch_ma_data(
        ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC', 'BTC-USD', '^VIX'],
        return_history=True,
    )
```

2. Inside the existing breadth `try` block, after `breadth_result = run_breadth_metrics(...)` succeeds, add:

```python
        from pipeline.screeners.breadth_store import load_archive
        from pipeline.screeners.breadth_signals import run_signals
        breadth_frame = load_archive(str(HISTORY_DIR / 'breadth_archive.csv'))
        market_health_payload = run_signals(
            breadth_result, breadth_frame,
            ma_histories.get('SPY'), ma_histories.get('QQQ'),
        )
```

and initialize `market_health_payload = None` alongside `breadth_result = None`
in the `except` path.

3. Next to the guarded breadth.json write (the `if breadth_result is not None:` block), add:

```python
    mh_path = OUTPUT_DIR / 'market_health.json'
    if market_health_payload is not None:
        mh_path.write_text(json.dumps(
            {'timestamp': timestamp, 'stale': False, **market_health_payload},
            default=_json_serializer), encoding='utf-8')
        logger.info("Saved market_health.json")
    elif mh_path.exists():
        try:
            prev = json.loads(mh_path.read_text(encoding='utf-8'))
            prev['stale'] = True
            mh_path.write_text(json.dumps(prev, default=_json_serializer), encoding='utf-8')
            logger.warning("market_health unavailable — marked previous file stale")
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Could not stale-mark market_health.json: %s", exc)
```

(Match the module's existing json.dumps style — reuse its `_json_serializer`
or `default=str` convention, whichever the file already uses for other outputs.)

- [ ] **Step 6: Run the full suite**

Run: `python3 -m pytest pipeline/tests/ -v`
Expected: all PASS except the 4 known content-processor failures. `run_all.py`
has no test harness — show the wiring diff in your report.

- [ ] **Step 7: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py pipeline/adapters/yfinance_adapter.py pipeline/screeners/run_all.py
git commit -m "feat(breadth): run_signals orchestration wired into run_all + market_health.json"
```

---

### Task 7: Frontend data plumbing + shared chart hook

**Files:**
- Modify: `frontend/src/hooks/useMarketData.js`
- Create: `frontend/src/components/breadth/useBreadthChart.js`
- Modify: `frontend/src/components/breadth/BreadthCharts.jsx` (import the hook instead of its local copy)

**Interfaces:**
- Produces:
  - `useMarketData` exposes `data.market_health` (object or `null` — a fetch failure for this one file must NOT break the others).
  - `useBreadthChart(containerRef, chartRef, deps, setupFn, height)` — the exact `useChart` hook currently local to `BreadthCharts.jsx` (theme-aware lightweight-charts v5 factory), exported from its own file; `deps` replaces the old `history` argument as the effect dependency.

- [ ] **Step 1: Make market_health a tolerant fetch**

In `frontend/src/hooks/useMarketData.js`: keep `FILES` as-is (do NOT add
market_health there — a 404 would reject the whole `Promise.all`). Inside
`fetchData`, after `const obj = Object.fromEntries(results)`, add:

```javascript
      // market_health is optional — tolerate absence (pipeline may not have shipped it yet)
      try {
        const mh = await fetch(`${BASE}/market_health.json`)
        obj.market_health = mh.ok ? await mh.json() : null
      } catch {
        obj.market_health = null
      }
```

- [ ] **Step 2: Extract the chart hook**

Create `frontend/src/components/breadth/useBreadthChart.js` containing the
`useChart` function currently at `BreadthCharts.jsx:40-97` verbatim, renamed
and exported:

```javascript
import { useEffect, useCallback } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

// Theme-aware lightweight-charts factory shared by all breadth charts.
export function useBreadthChart(containerRef, chartRef, deps, setupFn, height) {
  const setup = useCallback(setupFn, [])

  useEffect(() => {
    if (!containerRef.current || !deps) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const w = containerRef.current.clientWidth
    const h = height ?? Math.max(160, Math.round(w * 0.35))

    const root = getComputedStyle(document.documentElement)
    const bgColor = root.getPropertyValue('--color-surface').trim() || '#ffffff'
    const txtColor = root.getPropertyValue('--color-text-secondary').trim() || '#78716c'
    const gridColor = root.getPropertyValue('--color-border-light').trim() || '#f5f5f4'

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: bgColor },
        textColor: txtColor,
        fontSize: 10,
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      width: w,
      height: h,
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
      crosshair: { horzLine: { visible: false, labelVisible: false } },
    })

    setup(chart, deps)
    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        const newW = containerRef.current.clientWidth
        const newH = height ?? Math.max(160, Math.round(newW * 0.35))
        chartRef.current.applyOptions({ width: newW, height: newH })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
      }
    }
  }, [deps, height, setup])
}
```

- [ ] **Step 3: Refactor BreadthCharts.jsx to use it**

In `BreadthCharts.jsx`: delete the local `useChart` (lines 40-97), add
`import { useBreadthChart } from './useBreadthChart'`, and change both call
sites from `useChart(containerRef, chartRef, history, ...)` to
`useBreadthChart(containerRef, chartRef, history, ...)`. Remove the now-unused
`createChart`/`ColorType`/`useEffect`/`useCallback` imports it no longer needs
(keep `LineSeries`, `useRef`).

- [ ] **Step 4: Build check + commit**

Run: `cd frontend && npx vite build 2>&1 | tail -5 && cd ..`
Expected: build succeeds.

```bash
git add frontend/src/hooks/useMarketData.js frontend/src/components/breadth/useBreadthChart.js frontend/src/components/breadth/BreadthCharts.jsx
git commit -m "feat(breadth-ui): tolerant market_health fetch + shared chart hook"
```

---

### Task 8: VerdictBanner + Dashboard chip

**Files:**
- Create: `frontend/src/components/breadth/VerdictBanner.jsx`
- Create: `frontend/src/components/breadth/BreadthChip.jsx`
- Modify: `frontend/src/components/Layout.jsx` (dashboard section, above the MarketPosture grid)

**Interfaces:**
- Consumes: `data.breadth.verdict` (Task 6 shape), `data.breadth.data_quality`.
- Produces: `<VerdictBanner verdict={} dataQuality={} />`; `<BreadthChip verdict={} onNavigate={} />`.

- [ ] **Step 1: VerdictBanner**

Create `frontend/src/components/breadth/VerdictBanner.jsx`:

```jsx
const ENV_STYLE = {
  BULLISH: 'text-[var(--color-profit)]',
  BEARISH: 'text-[var(--color-loss)]',
  MIXED: 'text-[var(--color-signal-caution)]',
  OVERSOLD: 'text-[var(--color-signal-caution)]',
  OVERBOUGHT: 'text-[var(--color-signal-caution)]',
}

const ENV_LABEL = {
  BULLISH: 'Bullish market environment',
  BEARISH: 'Bearish market environment',
  MIXED: 'Mixed market environment',
  OVERSOLD: 'Oversold — reversal watch',
  OVERBOUGHT: 'Overbought — chase risk',
}

export default function VerdictBanner({ verdict, dataQuality }) {
  if (!verdict) return null
  const v = verdict

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <div className="flex items-baseline justify-between mb-3">
        <div className="flex items-baseline gap-3">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
            Market Environment · Decision First
          </h3>
          {dataQuality?.stale && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-[var(--color-signal-caution)] uppercase tracking-wide">
              Stale data · as of {dataQuality.as_of ?? '—'}
            </span>
          )}
        </div>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          score {v.score >= 0 ? `+${v.score}` : v.score} / 12
        </span>
      </div>

      <div className={`text-xl font-semibold mb-4 ${ENV_STYLE[v.env] ?? ''}`}>
        {ENV_LABEL[v.env] ?? v.env}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-4">
        <Col label="Risk level" value={v.risk} sub={`${v.warn_total} total warnings`} />
        <Col label="Exposure" value={v.exposure} />
        <Col label="SPY" value={v.spy_state ?? '—'} />
        <Col label="QQQ" value={v.qqq_state ?? '—'} />
        <Col label="Alignment" value={v.alignment ?? '—'} />
        <Col label="Breadth confirmation" value={v.confirmation} />
        <Col label="Playbook" value={v.playbook} />
      </div>

      <p className="text-[12px] text-[var(--color-text)] border-t border-[var(--color-border-light)] pt-3">
        <span className="font-medium">Guidance:</span> {v.guidance}
      </p>
      {v.notes?.length > 0 && (
        <ul className="mt-2 space-y-0.5">
          {v.notes.map((n) => (
            <li key={n} className="text-[11px] text-[var(--color-text-secondary)]">· {n}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Col({ label, value, sub }) {
  return (
    <div>
      <div className="text-[9px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] mb-1">
        {label}
      </div>
      <div className="text-[12px] text-[var(--color-text)] leading-snug">{value}</div>
      {sub && <div className="text-[10px] text-[var(--color-text-secondary)]">{sub}</div>}
    </div>
  )
}
```

- [ ] **Step 2: BreadthChip**

Create `frontend/src/components/breadth/BreadthChip.jsx`:

```jsx
const ENV_DOT = {
  BULLISH: 'bg-[var(--color-profit)]',
  BEARISH: 'bg-[var(--color-loss)]',
  MIXED: 'bg-[var(--color-signal-caution)]',
  OVERSOLD: 'bg-[var(--color-signal-caution)]',
  OVERBOUGHT: 'bg-[var(--color-signal-caution)]',
}

export default function BreadthChip({ verdict, onNavigate }) {
  if (!verdict) return null
  const summary = verdict.notes?.[0] ?? verdict.confirmation
  return (
    <button
      onClick={() => onNavigate('#/breadth')}
      className="w-full flex items-center gap-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-1.5 hover:bg-[var(--color-hover-bg)] text-left"
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ENV_DOT[verdict.env] ?? ''}`} />
      <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] shrink-0">
        Breadth
      </span>
      <span className="text-[11px] font-mono text-[var(--color-text)] shrink-0">{verdict.env}</span>
      <span className="text-[11px] text-[var(--color-text-secondary)] truncate">
        · {verdict.exposure} · {summary}
      </span>
    </button>
  )
}
```

- [ ] **Step 3: Insert the chip in Layout**

In `frontend/src/components/Layout.jsx`: add
`import BreadthChip from './breadth/BreadthChip'`; in the dashboard branch,
directly ABOVE the `MarketPosture` grid div, insert:

```jsx
          <BreadthChip verdict={data?.breadth?.verdict} onNavigate={navigate} />
```

- [ ] **Step 4: Build check + commit**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`
Expected: success.

```bash
git add frontend/src/components/breadth/VerdictBanner.jsx frontend/src/components/breadth/BreadthChip.jsx frontend/src/components/Layout.jsx
git commit -m "feat(breadth-ui): verdict banner + dashboard chip"
```

---

### Task 9: MarketStateSummary

**Files:**
- Create: `frontend/src/components/breadth/MarketStateSummary.jsx`

**Interfaces:**
- Consumes: `data.breadth.mm`, `data.breadth.breadth`, `data.breadth.verdict` (incl. `verdict.context` percentiles).
- Produces: `<MarketStateSummary mm={} breadth={} verdict={} />`.

- [ ] **Step 1: Implement**

Create `frontend/src/components/breadth/MarketStateSummary.jsx`:

```jsx
export default function MarketStateSummary({ mm, breadth, verdict }) {
  if (!mm || !breadth || !verdict) return null
  const ctx = verdict.context ?? {}
  const qtrSpread = (mm.up_25pct_qtr ?? 0) - (mm.down_25pct_qtr ?? 0)

  const thrustLabel =
    (mm.up_4pct ?? 0) >= 300 && (mm.down_4pct ?? 0) >= 300 ? 'churn / volatile'
    : (mm.up_4pct ?? 0) >= 300 ? 'bullish thrust'
    : (mm.down_4pct ?? 0) >= 300 ? 'bearish thrust'
    : 'no thrust'

  const t = breadth.t2108
  const t2108Zone =
    t == null ? '—' : t < 20 ? 'oversold' : t <= 40 ? 'weak' : t < 60 ? 'neutral'
    : t <= 80 ? 'strong' : 'overbought'

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Market State Summary
      </h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <Tile
          label="Up 4% / Down 4%"
          value={`${mm.up_4pct ?? '—'} / ${mm.down_4pct ?? '—'}`}
          note={thrustLabel}
          pct={ctx.down_4pct != null ? `down-4% ${ctx.down_4pct}th pctile` : null}
          tone={thrustLabel === 'bullish thrust' ? 'up' : thrustLabel === 'bearish thrust' ? 'down' : ''}
        />
        <Tile
          label="5-day / 10-day ratio"
          value={`${mm.ratio_5d?.toFixed(2) ?? '—'} / ${mm.ratio_10d?.toFixed(2) ?? '—'}`}
          note={mm.ratio_5d >= 1 === mm.ratio_10d >= 1 ? 'ratios agree' : 'ratios disagree'}
          pct={ctx.ratio_5d != null ? `5D ${ctx.ratio_5d}th pctile` : null}
          tone={mm.ratio_5d >= 1 && mm.ratio_10d >= 1 ? 'up' : mm.ratio_5d < 0.5 && mm.ratio_10d < 0.5 ? 'down' : ''}
        />
        <Tile
          label="Quarterly breadth (25%+)"
          value={`${mm.up_25pct_qtr ?? '—'} / ${mm.down_25pct_qtr ?? '—'}`}
          note={qtrSpread > 0 ? 'structural bull intact' : qtrSpread < 0 ? 'structural bear' : 'flat'}
          pct={ctx.qtr_spread != null ? `spread ${ctx.qtr_spread}th pctile` : null}
          tone={qtrSpread > 0 ? 'up' : qtrSpread < 0 ? 'down' : ''}
        />
        <Tile
          label="T2108"
          value={t != null ? `${t.toFixed(1)}%` : '—'}
          note={t2108Zone}
          pct={ctx.t2108 != null ? `${ctx.t2108}th pctile` : null}
          tone={t2108Zone === 'strong' ? 'up' : t2108Zone === 'weak' ? 'down' : ''}
        />
      </div>
      <p className="text-[12px] text-[var(--color-text)]">{verdict.guidance}</p>
    </div>
  )
}

function Tile({ label, value, note, pct, tone }) {
  const toneClass =
    tone === 'up' ? 'text-[var(--color-profit)]' : tone === 'down' ? 'text-[var(--color-loss)]' : 'text-[var(--color-text)]'
  return (
    <div className="bg-[var(--color-bg)] rounded p-3">
      <div className="text-[10px] text-[var(--color-text-secondary)] font-medium uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className={`text-lg font-mono tabular-nums ${toneClass}`}>{value}</div>
      <div className="text-[11px] text-[var(--color-text-secondary)]">{note}</div>
      {pct && <div className="text-[10px] text-[var(--color-text-muted)]">{pct}</div>}
    </div>
  )
}
```

- [ ] **Step 2: Build check + commit**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`

```bash
git add frontend/src/components/breadth/MarketStateSummary.jsx
git commit -m "feat(breadth-ui): market state summary tiles + percentile context"
```

---

### Task 10: HealthChart + DangerPanel

**Files:**
- Create: `frontend/src/components/breadth/HealthChart.jsx`
- Create: `frontend/src/components/breadth/DangerPanel.jsx`

**Interfaces:**
- Consumes: `data.market_health.spy|qqq` (Task 6 payload) and `data.breadth.history` (T2108 overlay series).
- Produces: `<HealthChart title="SPY Market Health" block={mh.spy} state={verdict.spy_state} t2108={{dates, values}} />`; `<DangerPanel title="SPY danger signals" danger={mh.spy.danger} />`.

- [ ] **Step 1: HealthChart**

Create `frontend/src/components/breadth/HealthChart.jsx`:

```jsx
import { useRef } from 'react'
import { CandlestickSeries, LineSeries } from 'lightweight-charts'
import { useBreadthChart } from './useBreadthChart'

export default function HealthChart({ title, block, state, t2108 }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, block, (chart, blk) => {
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: '#4d7c0f', downColor: '#b91c1c',
      wickUpColor: '#4d7c0f', wickDownColor: '#b91c1c',
      borderVisible: false,
    })
    candles.setData(blk.candles.map((c) => ({
      time: c.date, open: c.o, high: c.h, low: c.l, close: c.c,
    })))

    const mkLine = (values, color, width) => {
      const s = chart.addSeries(LineSeries, { color, lineWidth: width, priceLineVisible: false })
      s.setData(blk.candles
        .map((c, i) => ({ time: c.date, value: values[i] }))
        .filter((p) => p.value != null))
      return s
    }
    mkLine(blk.sma20, '#3b82f6', 1)
    mkLine(blk.sma50, '#f59e0b', 1)

    if (t2108?.dates?.length) {
      const overlay = chart.addSeries(LineSeries, {
        color: '#a8a29e', lineWidth: 1, priceScaleId: 't2108',
        priceLineVisible: false,
      })
      overlay.setData(t2108.dates.map((d, i) => ({ time: d, value: t2108.values[i] ?? 0 })))
      chart.priceScale('t2108').applyOptions({
        scaleMargins: { top: 0.05, bottom: 0.05 }, visible: false,
      })
      overlay.createPriceLine({ price: 20, color: '#d6d3d1', lineWidth: 1, lineStyle: 2 })
      overlay.createPriceLine({ price: 80, color: '#d6d3d1', lineWidth: 1, lineStyle: 2 })
    }
  })

  if (!block) return null
  const last = block.candles[block.candles.length - 1]
  const prev = block.candles[block.candles.length - 2]
  const dayPct = prev ? ((last.c / prev.c - 1) * 100).toFixed(2) : null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {title} {state ? `· ${state}` : ''}
        </h3>
        <span className="text-[10px] font-mono text-[var(--color-text-secondary)]">
          {last.c.toLocaleString()} {dayPct != null ? `(${dayPct}%)` : ''}
        </span>
      </div>
      <div ref={containerRef} />
      <div className="text-[9px] text-[var(--color-text-muted)] mt-1">
        20 SMA (blue) · 50 SMA (amber) · T2108 overlay (grey, 20/80 dashed)
      </div>
    </div>
  )
}
```

- [ ] **Step 2: DangerPanel**

Create `frontend/src/components/breadth/DangerPanel.jsx`:

```jsx
const SIGNAL_LABELS = {
  below_20sma: 'Price closes below 20 SMA',
  stoch_cross: 'Fast stochastic below slow stochastic',
  stoch_down: 'Fast & slow stochastic curved down',
  lower_lows: '3 consecutive days of lower lows',
  close_below_lows: 'Close lower than 3 previous lows',
}

export default function DangerPanel({ title, danger }) {
  if (!danger?.signals) return null
  const count = danger.count ?? 0
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-4 py-3">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {title}
        </h3>
        <span className={`text-[10px] font-mono ${count >= 4 ? 'text-[var(--color-loss)]' : count >= 2 ? 'text-[var(--color-signal-caution)]' : 'text-[var(--color-text-secondary)]'}`}>
          {count} / 5 active
        </span>
      </div>
      <ul className="space-y-1.5">
        {Object.entries(SIGNAL_LABELS).map(([key, label]) => {
          const active = danger.signals[key] === true
          return (
            <li key={key} className="flex items-center justify-between text-[11px]">
              <span className={active ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'}>
                {label}
              </span>
              <span className={`w-2 h-2 rounded-full ${active ? 'bg-[var(--color-loss)]' : 'bg-[var(--color-border)]'}`} />
            </li>
          )
        })}
      </ul>
    </div>
  )
}
```

- [ ] **Step 3: Build check + commit**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`

```bash
git add frontend/src/components/breadth/HealthChart.jsx frontend/src/components/breadth/DangerPanel.jsx
git commit -m "feat(breadth-ui): SPY/QQQ health charts + danger panels"
```

---

### Task 11: RatioChart + SpreadChart + page assembly

**Files:**
- Create: `frontend/src/components/breadth/RatioChart.jsx`
- Create: `frontend/src/components/breadth/SpreadChart.jsx`
- Modify: `frontend/src/components/breadth/BreadthPage.jsx`

**Interfaces:**
- Consumes: `data.breadth.history.rows` (ratio + 25% qtr fields), everything above.
- Produces: the final page order — Banner → StateSummary → SPY/QQQ health → Ratio+Spread → Danger panels → MarketMonitor → ClassicBreadth → BreadthCharts → BreadthTable.

- [ ] **Step 1: RatioChart**

Create `frontend/src/components/breadth/RatioChart.jsx`:

```jsx
import { useRef } from 'react'
import { LineSeries } from 'lightweight-charts'
import { useBreadthChart } from './useBreadthChart'

export default function RatioChart({ rows }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, rows, (chart, data) => {
    const r5 = chart.addSeries(LineSeries, { color: '#4d7c0f', lineWidth: 1.5, title: '5D' })
    r5.setData(data.filter((r) => r.ratio_5d != null)
      .map((r) => ({ time: r.date, value: r.ratio_5d })))
    const r10 = chart.addSeries(LineSeries, {
      color: '#78716c', lineWidth: 1, lineStyle: 2, title: '10D',
    })
    r10.setData(data.filter((r) => r.ratio_10d != null)
      .map((r) => ({ time: r.date, value: r.ratio_10d })))
    r5.createPriceLine({ price: 1.0, color: '#d6d3d1', lineWidth: 1, lineStyle: 2 })
  })

  if (!rows?.length) return null
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-2">
        Breadth Ratios (dashed reference = 1, up days equal down days)
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
```

- [ ] **Step 2: SpreadChart**

Create `frontend/src/components/breadth/SpreadChart.jsx`:

```jsx
import { useRef } from 'react'
import { BaselineSeries, LineSeries } from 'lightweight-charts'
import { useBreadthChart } from './useBreadthChart'

export default function SpreadChart({ rows }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useBreadthChart(containerRef, chartRef, rows, (chart, data) => {
    const pts = data.filter((r) => r.up_25pct_qtr != null && r.down_25pct_qtr != null)
    const spread = chart.addSeries(BaselineSeries, {
      baseValue: { type: 'price', price: 0 },
      topLineColor: '#4d7c0f', topFillColor1: 'rgba(77, 124, 15, 0.15)',
      topFillColor2: 'rgba(77, 124, 15, 0.02)',
      bottomLineColor: '#b91c1c', bottomFillColor1: 'rgba(185, 28, 28, 0.02)',
      bottomFillColor2: 'rgba(185, 28, 28, 0.15)',
      lineWidth: 1.5,
    })
    spread.setData(pts.map((r) => ({ time: r.date, value: r.up_25pct_qtr - r.down_25pct_qtr })))
    const up = chart.addSeries(LineSeries, { color: 'rgba(77,124,15,0.5)', lineWidth: 1 })
    up.setData(pts.map((r) => ({ time: r.date, value: r.up_25pct_qtr })))
    const down = chart.addSeries(LineSeries, { color: 'rgba(185,28,28,0.5)', lineWidth: 1 })
    down.setData(pts.map((r) => ({ time: r.date, value: r.down_25pct_qtr })))
  })

  if (!rows?.length) return null
  const last = rows[rows.length - 1]
  const spread = (last?.up_25pct_qtr ?? 0) - (last?.down_25pct_qtr ?? 0)
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-3 py-3">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Quarterly Breadth (stocks moving 25%+ over the quarter)
        </h3>
        <span className={`text-[10px] font-mono ${spread > 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
          {spread > 0 ? '+' : ''}{spread} spread
        </span>
      </div>
      <div ref={containerRef} />
    </div>
  )
}
```

- [ ] **Step 3: Assemble BreadthPage**

Replace `frontend/src/components/breadth/BreadthPage.jsx` with:

```jsx
import VerdictBanner from './VerdictBanner'
import MarketStateSummary from './MarketStateSummary'
import HealthChart from './HealthChart'
import RatioChart from './RatioChart'
import SpreadChart from './SpreadChart'
import DangerPanel from './DangerPanel'
import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'
import BreadthTable from './BreadthTable'

export default function BreadthPage({ data }) {
  const breadth = data?.breadth
  const mh = data?.market_health

  if (!breadth) {
    return (
      <div className="text-[var(--color-text-muted)] text-sm font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  const verdict = breadth.verdict
  const t2108Overlay = breadth.history
    ? { dates: breadth.history.dates, values: breadth.history.rows.map((r) => r.t2108) }
    : null
  const rows = breadth.history?.rows ?? []

  return (
    <div className="space-y-3">
      <VerdictBanner verdict={verdict} dataQuality={breadth.data_quality} />
      <MarketStateSummary mm={breadth.mm} breadth={breadth.breadth} verdict={verdict} />
      {mh && !mh.stale && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <HealthChart title="SPY Market Health" block={mh.spy} state={verdict?.spy_state} t2108={t2108Overlay} />
          <HealthChart title="QQQ Market Health" block={mh.qqq} state={verdict?.qqq_state} t2108={t2108Overlay} />
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <RatioChart rows={rows} />
        <SpreadChart rows={rows} />
      </div>
      {mh && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <DangerPanel title="SPY danger signals" danger={mh.spy?.danger} />
          <DangerPanel title="QQQ danger signals" danger={mh.qqq?.danger} />
        </div>
      )}
      <MarketMonitor data={breadth} />
      <ClassicBreadth data={breadth} />
      <BreadthCharts data={breadth} />
      <BreadthTable data={breadth} />
    </div>
  )
}
```

- [ ] **Step 4: Build check + commit**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`

```bash
git add frontend/src/components/breadth/RatioChart.jsx frontend/src/components/breadth/SpreadChart.jsx frontend/src/components/breadth/BreadthPage.jsx
git commit -m "feat(breadth-ui): ratio + quarterly spread charts, decision-first page order"
```

---

### Task 12: End-to-end — real data + browser verification

**Files:**
- Modify (data only): `data/output/breadth.json`, `data/output/market_health.json`

- [ ] **Step 1: Full Python suite**

Run: `python3 -m pytest pipeline/tests/ tests/ -q`
Expected: only the 4 known content-processor failures.

- [ ] **Step 2: Generate real verdict + market_health (network: 2 yfinance downloads)**

```bash
python3 - <<'EOF'
import json, datetime as dt
import pandas as pd
import yfinance as yf
from pipeline.screeners.breadth_store import load_archive
from pipeline.screeners.breadth_signals import run_signals

def flat(df):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1) if df.columns.nlevels > 1 else df
    df.index = pd.DatetimeIndex(df.index).tz_localize(None)
    return df

spy = flat(yf.download('SPY', period='1y', auto_adjust=True, progress=False))
qqq = flat(yf.download('QQQ', period='1y', auto_adjust=True, progress=False))
frame = load_archive('data/history/breadth_archive.csv')

breadth = json.load(open('data/output/breadth.json'))
health = run_signals(breadth, frame, spy, qqq)
assert health is not None, 'health build failed'

json.dump(breadth, open('data/output/breadth.json', 'w'), indent=1)
json.dump({'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
           'stale': False, **health},
          open('data/output/market_health.json', 'w'), indent=1)

v = breadth['verdict']
print('env:', v['env'], '| risk:', v['risk'], '| exposure:', v['exposure'])
print('spy:', v['spy_state'], 'qqq:', v['qqq_state'], '| conf:', v['confirmation'])
print('context:', v['context'])
print('rows with v:', sum(1 for r in breadth['history']['rows'] if r.get('v')))
EOF
```

Sanity gates: env is one of the five; warn counts 0-5 each; percentiles 0-100;
`rows with v` equals the row count. The archive's last row date and SPY's last
session must match — if SPY has a newer session than the archive (run before
the daily cron), that is fine: `evaluate` truncates health to the archive date.

- [ ] **Step 3: Copy data for the dev server and verify in browser**

```bash
rm -rf frontend/public/data/output && cp -r data/output frontend/public/data/output
```

Start the dev server (preview tools / launch.json `fluxus-dashboard` config),
navigate to `/#/breadth`, and verify: banner shows env + all seven columns;
stat tiles show percentile lines; SPY/QQQ candles render with T2108 overlay;
ratio chart has the dashed 1.0 line; spread chart fills green/red by sign;
danger panels show 5 rows each with dot states matching `market_health.json`;
dashboard (`/#/dashboard`) shows the chip; console has zero errors. Fix
whatever fails, re-verify, then:

```bash
rm -rf frontend/public/data/output
```

(the copy is dev-only; Vercel's build makes its own).

- [ ] **Step 4: Commit the data**

```bash
git add data/output/breadth.json data/output/market_health.json
git commit -m "data(breadth): first verdict + market_health payloads"
```
