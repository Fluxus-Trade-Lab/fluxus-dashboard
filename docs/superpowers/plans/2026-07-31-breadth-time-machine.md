# Breadth Time Machine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replay the whole breadth page at any past trading date using only information available through that date — via a nightly precomputed replay file plus a client-side slider.

**Architecture:** The Python engine stays the single source of truth: a new pure `build_replay()` emits `data/output/breadth_replay.json` with every archive date's metric row, its prefix-computed verdict, and full-depth SPY/QQQ health including a new per-date `signals_history`. The frontend lazy-loads that file and slices it to the selected date with a pure JS function that returns exactly the prop shapes the existing components already consume. Spec: `docs/plans/2026-07-31-breadth-time-machine-design.md`.

**Tech Stack:** Python 3.11+/pandas/pytest · React 19 · lightweight-charts v5 · Tailwind 4

## Global Constraints

- All new Python functions are **pure**: no I/O, no clock, no reads outside their arguments. NaN inputs never raise.
- No `date.today()` / `datetime.now()` in engine code (repo guard `tests/test_no_naive_clock.py`).
- **No-peek rule:** `replay.verdicts[d]` must equal `evaluate(frame[:d], health truncated to d)` — the browser never recomputes a verdict.
- Live behavior unchanged: with the Time Machine at "Latest", the page must render byte-identically to today, and `breadth_replay.json` must not be fetched at all.
- Existing breadth component internals must not change — `sliceToDate` adapts data to them, not the reverse.
- `data/output/breadth.json` and `market_health.json` stay additive-only (`market_health` gains `signals_history`; nothing renamed).
- Anti-dopamine palette: existing CSS vars only (`--color-signal-caution` for the amber pinned state).
- Python tests: `python3 -m pytest` from repo root. Known baseline: 4 pre-existing failures in `pipeline/tests/test_content_processor.py` — ignore.
- No JS test harness exists — do not add one; frontend verified in-browser (Task 8).

---

### Task 1: `signals_history` in market_health

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py` (`market_health`)
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Consumes: existing `_danger_frame(hist)` (per-date boolean frame of the 5 signals), `danger_at(hist, date_iso) -> {'signals','count','date'}`.
- Produces: `signals_history(hist: pd.DataFrame, days: int | None = None) -> list[dict]` — `[{'date','signals':{5 bools},'count':int}]` for the trailing `days` sessions, or **all** sessions when `days is None`. `market_health(...)` output gains `signals_history` per ticker (trailing `days`, same length as `candles`).

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
class TestSignalsHistory:
    def test_shape_and_keys(self):
        from pipeline.screeners.breadth_signals import signals_history
        closes = [100.0 + (i % 9) - 4 for i in range(220)]
        hist = _hist(closes)
        sh = signals_history(hist, days=130)
        assert len(sh) == 130
        assert set(sh[0]) == {'date', 'signals', 'count'}
        assert set(sh[0]['signals']) == {'below_20sma', 'stoch_cross', 'stoch_down',
                                         'lower_lows', 'close_below_lows'}
        assert all(s['count'] == sum(s['signals'].values()) for s in sh)
        assert sh[-1]['date'] == hist.index[-1].strftime('%Y-%m-%d')

    def test_days_none_returns_all_sessions(self):
        from pipeline.screeners.breadth_signals import signals_history
        hist = _hist([100.0 + (i % 5) for i in range(210)])
        assert len(signals_history(hist, days=None)) == 210

    def test_matches_danger_at_for_each_date(self):
        """The history entry for date D must equal danger_at(hist, D)."""
        from pipeline.screeners.breadth_signals import signals_history, danger_at
        hist = _hist([100.0 + (i % 11) - 5 for i in range(230)])
        sh = signals_history(hist, days=None)
        for entry in (sh[-1], sh[-40], sh[-100]):
            da = danger_at(hist, entry['date'])
            assert da['signals'] == entry['signals']
            assert da['count'] == entry['count']
            assert da['date'] == entry['date']

    def test_market_health_includes_signals_history(self):
        from pipeline.screeners.breadth_signals import market_health
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = market_health(spy, qqq, days=130)
        for key in ('spy', 'qqq'):
            sh = health[key]['signals_history']
            assert len(sh) == 130 == len(health[key]['candles'])
            assert sh[-1]['date'] == health[key]['candles'][-1]['date']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestSignalsHistory -v`
Expected: FAIL with "cannot import name 'signals_history'".

- [ ] **Step 3: Implement**

In `pipeline/screeners/breadth_signals.py`, directly after `warn_counts`, add:

```python
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
```

In `market_health`, inside the per-ticker `out[key] = {...}` dict, add after
`'warn_history': warn_counts(hist, days),`:

```python
            'signals_history': signals_history(hist, days),
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): per-date signals_history in market_health"
```

---

### Task 2: Atomic verdict assignment in run_signals

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py` (`run_signals`)
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Produces: `run_signals` unchanged in signature and success-path output, but mutates `breadth_result` **only after** verdict, context, and row annotations all succeed. On any exception the passed-in `breadth_result` is left untouched (no partial `verdict` key).

- [ ] **Step 1: Write the failing test**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
class TestRunSignalsAtomicity:
    def test_breadth_result_untouched_when_annotate_fails(self, monkeypatch):
        from pipeline.screeners import breadth_signals as bs
        rows = [{'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows)
        result = {'history': {'rows': [dict(r) for r in rows]}, 'mm': {}, 'breadth': {}}

        def boom(*args, **kwargs):
            raise RuntimeError('annotate exploded')

        monkeypatch.setattr(bs, 'annotate_rows', boom)
        with pytest.raises(RuntimeError):
            bs.run_signals(result, frame, None, None)
        assert 'verdict' not in result
        assert all('v' not in r for r in result['history']['rows'])

    def test_success_path_unchanged(self):
        from pipeline.screeners.breadth_signals import run_signals
        rows = [{'date': '2026-07-28', **_bull_row()},
                {'date': '2026-07-29', **_bull_row()}]
        frame = _frame(rows)
        result = {'history': {'rows': [dict(r) for r in rows]}, 'mm': {}, 'breadth': {}}
        spy = _ohlc([100.0 + i * 0.1 for i in range(250)])
        qqq = _ohlc([200.0 + i * 0.2 for i in range(250)])
        health = run_signals(result, frame, spy, qqq)
        assert health is not None
        assert 'context' in result['verdict']
        assert all(r.get('v') for r in result['history']['rows'])
```

- [ ] **Step 2: Run tests to verify the first fails**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestRunSignalsAtomicity -v`
Expected: `test_breadth_result_untouched_when_annotate_fails` FAILS (`verdict` is
already assigned before `annotate_rows` runs); the second test passes.

- [ ] **Step 3: Implement**

In `pipeline/screeners/breadth_signals.py`, replace the tail of `run_signals`
(from `verdict = evaluate(...)` to `return health`) with:

```python
    verdict = evaluate(frame, health)
    verdict['context'] = percentile_context(frame)
    # Annotate a copy first: a failure here must not leave breadth_result
    # holding a verdict with missing/partial per-row codes (Spec 2 residual).
    rows = [dict(r) for r in breadth_result.get('history', {}).get('rows', [])]
    annotate_rows(rows, frame, health)
    breadth_result['verdict'] = verdict
    if 'history' in breadth_result:
        breadth_result['history']['rows'] = rows
    return health
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS (including the pre-existing `TestRunSignals` cases).

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "fix(breadth): assign verdict atomically after row annotation succeeds"
```

---

### Task 3: `build_replay` — the history book

**Files:**
- Modify: `pipeline/screeners/breadth_signals.py`
- Test: `pipeline/tests/test_breadth_signals.py`

**Interfaces:**
- Consumes: `evaluate`, `percentile_context`, `market_health`, `truncate_health`, `signals_history`, `danger_at`.
- Produces:

```python
build_replay(frame: pd.DataFrame,
             spy_hist: pd.DataFrame | None,
             qqq_hist: pd.DataFrame | None) -> dict
```

returning (pure, no clock — the caller adds `timestamp`):

```
{'dates': [ISO...ascending],
 'rows': {date: {archive row, NaN->None}},
 'verdicts': {date: verdict block incl. 'context'},
 'health': {'spy': {'candles','sma20','sma50','sma200','signals_history'},
            'qqq': {...}} or None}
```

`health` covers the **full** archive span (`market_health(..., days=None)`);
`verdicts[d]` = `evaluate(frame[:d], health)` (evaluate truncates internally,
so no future leak) with `context` = `percentile_context(frame[:d])`.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_signals.py`:

```python
class TestBuildReplay:
    def _frame_and_hists(self, n=12):
        rows = []
        for i in range(n):
            body = _bull_row() if i % 2 == 0 else _bear_row()
            rows.append({'date': f'2026-07-{i + 1:02d}', **body})
        frame = _frame(rows)
        spy = _ohlc([100.0 + i * 0.1 for i in range(260)], end='2026-07-12')
        qqq = _ohlc([200.0 + i * 0.2 for i in range(260)], end='2026-07-12')
        return frame, spy, qqq

    def test_top_level_shape(self):
        from pipeline.screeners.breadth_signals import build_replay
        frame, spy, qqq = self._frame_and_hists()
        r = build_replay(frame, spy, qqq)
        assert set(r) == {'dates', 'rows', 'verdicts', 'health'}
        assert r['dates'] == list(frame['date'])
        assert set(r['rows']) == set(r['dates']) == set(r['verdicts'])
        for key in ('spy', 'qqq'):
            assert set(r['health'][key]) == {'candles', 'sma20', 'sma50',
                                             'sma200', 'signals_history'}

    def test_no_peek_every_date_matches_independent_evaluate(self):
        """The no-peek rule: every stored verdict equals a fresh prefix evaluate."""
        from pipeline.screeners.breadth_signals import (
            build_replay, evaluate, percentile_context, market_health)
        frame, spy, qqq = self._frame_and_hists()
        r = build_replay(frame, spy, qqq)
        health = market_health(spy, qqq, days=None)
        for i, d in enumerate(r['dates']):
            prefix = frame.iloc[:i + 1].reset_index(drop=True)
            expected = evaluate(prefix, health)
            expected['context'] = percentile_context(prefix)
            assert r['verdicts'][d] == expected, d

    def test_rows_are_json_safe(self):
        import json
        import numpy as np
        from pipeline.screeners.breadth_signals import build_replay
        frame, spy, qqq = self._frame_and_hists()
        frame.loc[0, 'mcclellan_osc'] = np.nan
        r = build_replay(frame, spy, qqq)
        assert r['rows'][r['dates'][0]]['mcclellan_osc'] is None
        json.dumps(r)  # must not raise

    def test_health_none_degrades(self):
        from pipeline.screeners.breadth_signals import build_replay
        frame, _, _ = self._frame_and_hists()
        r = build_replay(frame, None, None)
        assert r['health'] is None
        first = r['verdicts'][r['dates'][0]]
        assert first['spy_state'] is None
        assert any('unavailable' in n.lower() for n in first['notes'])

    def test_health_spans_full_history(self):
        from pipeline.screeners.breadth_signals import build_replay
        frame, spy, qqq = self._frame_and_hists()
        r = build_replay(frame, spy, qqq)
        # days=None -> every session of the input history, not just 130
        assert len(r['health']['spy']['candles']) == len(spy)
        assert len(r['health']['spy']['signals_history']) == len(spy)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py::TestBuildReplay -v`
Expected: FAIL with "cannot import name 'build_replay'".

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_signals.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_signals.py -v`
Expected: all PASS. If `test_no_peek_every_date_matches_independent_evaluate` fails,
compare one date's stored vs expected dict key-by-key — a mismatch means
`evaluate` is seeing un-truncated health somewhere.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_signals.py pipeline/tests/test_breadth_signals.py
git commit -m "feat(breadth): build_replay — per-date rows + prefix verdicts + full-span health"
```

---

### Task 4: Wire replay into run_all + 3y benchmark history

**Files:**
- Modify: `pipeline/adapters/yfinance_adapter.py` (`fetch_ma_data`, ~line 499-583)
- Modify: `pipeline/screeners/run_all.py` (breadth signals `else:` block ~line 315-334; output writes ~line 368-385)

**Interfaces:**
- Consumes: `build_replay` (Task 3).
- Produces: `fetch_ma_data(tickers=None, return_history=False, history_period='1y')` — new kwarg; the downloaded frames are fetched with `period=history_period`. `run_all` calls it with `history_period='3y'` so replay health covers the archive; **`market_health.json` keeps its 130-day display window** (unchanged, `market_health()` default). New output `data/output/breadth_replay.json` = `{'timestamp': timestamp, **build_replay(...)}`, written inside the existing signals `try` so a failure only logs (breadth.json still ships).

- [ ] **Step 1: Add the history_period kwarg**

In `pipeline/adapters/yfinance_adapter.py`, change the signature:

```python
    def fetch_ma_data(self, tickers: list[str] = None, return_history: bool = False,
                      history_period: str = '1y'):
```

and the download line inside the loop:

```python
                hist = _flatten_yf_columns(yf.download(ticker, period=history_period, progress=False))
```

- [ ] **Step 2: Request 3y in run_all**

In `pipeline/screeners/run_all.py`, update the fetch call:

```python
    signals, ma_histories = yf_adapter.fetch_ma_data(
        ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC', 'BTC-USD', '^VIX'],
        return_history=True,
        history_period='3y',
    )
```

- [ ] **Step 3: Build the replay payload**

In the signals `else:`/`try:` block, after the `market_health_payload = run_signals(...)`
call, add:

```python
            from pipeline.screeners.breadth_signals import build_replay
            replay_payload = build_replay(
                breadth_frame,
                ma_histories.get('SPY'), ma_histories.get('QQQ'),
            )
```

and initialize `replay_payload = None` next to `market_health_payload = None`
both before the outer `try` and in the signals `except` handler.

- [ ] **Step 4: Write the file**

Next to the existing `market_health.json` write block, add:

```python
    if replay_payload is not None:
        (OUTPUT_DIR / 'breadth_replay.json').write_text(
            json.dumps({'timestamp': timestamp, **replay_payload},
                       indent=2, default=_json_serializer),
            encoding='utf-8')
        logger.info("Saved breadth_replay.json")
```

- [ ] **Step 5: Verify nothing regressed**

Run: `python3 -m pytest pipeline/tests/ -v`
Expected: all PASS except the 4 known content-processor failures. `run_all` has
no test harness — paste the three wiring hunks into your report.

- [ ] **Step 6: Commit**

```bash
git add pipeline/adapters/yfinance_adapter.py pipeline/screeners/run_all.py
git commit -m "feat(breadth): emit breadth_replay.json; 3y benchmark history for replay depth"
```

---

### Task 5: `sliceToDate` — the pure JS adapter

**Files:**
- Create: `frontend/src/components/breadth/sliceReplay.js`

**Interfaces:**
- Consumes: the `breadth_replay.json` shape from Task 3 (+ `timestamp`).
- Produces: `sliceToDate(replay, date) -> { breadth, marketHealth }` where
  `breadth` matches what `BreadthPage` reads from `data.breadth`
  (`verdict, mm, breadth, history{dates,pct_above_200sma,pct_above_50sma,pct_above_20sma,mcclellan_osc,rows}, data_quality`)
  and `marketHealth` matches `data.market_health`
  (`{stale:false, spy:{candles,sma20,sma50,sma200,danger{signals,count,date},warn_history}, qqq:{...}}`).
  Both truncated to `date`; history window = last 100 rows up to `date`;
  health arrays cut to sessions ≤ `date`; `danger` = the `signals_history`
  entry at/just before `date`. Returns `null` for an unknown date.

- [ ] **Step 1: Implement**

Create `frontend/src/components/breadth/sliceReplay.js`:

```javascript
// Pure adapter: turn the replay book into exactly the props the live
// breadth components already consume, truncated to `date`. No recomputation
// happens here — verdicts come precomputed from the Python engine.

const HISTORY_WINDOW = 100

function cutSeries(block, keep) {
  return {
    candles: block.candles.slice(0, keep),
    sma20: block.sma20.slice(0, keep),
    sma50: block.sma50.slice(0, keep),
    sma200: block.sma200.slice(0, keep),
  }
}

function healthAt(block, date) {
  const keep = block.candles.filter((c) => c.date <= date).length
  if (!keep) return null
  const sigs = block.signals_history.filter((s) => s.date <= date)
  const last = sigs[sigs.length - 1]
  return {
    ...cutSeries(block, keep),
    danger: last
      ? { signals: last.signals, count: last.count, date: last.date }
      : { signals: {}, count: 0 },
    warn_history: sigs.map((s) => ({ date: s.date, count: s.count })),
  }
}

export function sliceToDate(replay, date) {
  if (!replay?.verdicts?.[date]) return null

  const upto = replay.dates.filter((d) => d <= date)
  const windowDates = upto.slice(-HISTORY_WINDOW)
  const rows = windowDates.map((d) => replay.rows[d])
  const last = rows[rows.length - 1] ?? {}

  const breadth = {
    universe_size: last.universe_size ?? null,
    spx_close: last.spx_close ?? null,
    verdict: replay.verdicts[date],
    mm: {
      up_4pct: last.up_4pct, down_4pct: last.down_4pct,
      ratio_5d: last.ratio_5d, ratio_10d: last.ratio_10d,
      up_25pct_qtr: last.up_25pct_qtr, down_25pct_qtr: last.down_25pct_qtr,
      up_25pct_month: last.up_25pct_month, down_25pct_month: last.down_25pct_month,
      up_50pct_month: last.up_50pct_month, down_50pct_month: last.down_50pct_month,
      up_13pct_34d: last.up_13pct_34d, down_13pct_34d: last.down_13pct_34d,
    },
    breadth: {
      t2108: last.t2108,
      pct_above_200sma: last.pct_above_200sma,
      pct_above_50sma: last.pct_above_50sma,
      pct_above_20sma: last.pct_above_20sma,
      advances: last.advances, declines: last.declines,
      new_highs: last.new_highs, new_lows: last.new_lows,
      ad_line: last.ad_line, mcclellan_osc: last.mcclellan_osc,
    },
    history: {
      dates: windowDates,
      pct_above_200sma: rows.map((r) => r.pct_above_200sma),
      pct_above_50sma: rows.map((r) => r.pct_above_50sma),
      pct_above_20sma: rows.map((r) => r.pct_above_20sma),
      mcclellan_osc: rows.map((r) => r.mcclellan_osc),
      rows,
    },
    data_quality: { stale: false },
  }

  let marketHealth = null
  if (replay.health) {
    const spy = healthAt(replay.health.spy, date)
    const qqq = healthAt(replay.health.qqq, date)
    if (spy && qqq) marketHealth = { stale: false, spy, qqq }
  }

  return { breadth, marketHealth }
}
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`
Expected: success (module is imported by Task 7; a lone new module still type-checks at build).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/breadth/sliceReplay.js
git commit -m "feat(breadth-ui): pure sliceToDate adapter for replay data"
```

---

### Task 6: `useTimeMachine` hook

**Files:**
- Create: `frontend/src/components/breadth/useTimeMachine.js`

**Interfaces:**
- Consumes: `sliceToDate` (Task 5).
- Produces: `useTimeMachine()` returning
  `{ active, date, dates, playing, loading, error, sliced, engage, setDate, step, togglePlay, jumpYtd, exitToLatest }`.
  - `engage()` lazy-fetches `/data/output/breadth_replay.json` **once** and pins to the latest date.
  - `sliced` = `sliceToDate(replay, date)` or `null` when not active.
  - `step(delta)` moves by index within `dates`, clamped.
  - `togglePlay()` advances one session per 500 ms; auto-stops at the last date.
  - `jumpYtd()` pins the first session of the latest date's calendar year.
  - `exitToLatest()` sets `active=false` (live mode; replay stays cached).

- [ ] **Step 1: Implement**

Create `frontend/src/components/breadth/useTimeMachine.js`:

```javascript
import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { sliceToDate } from './sliceReplay'

const PLAY_INTERVAL_MS = 500

export function useTimeMachine() {
  const [replay, setReplay] = useState(null)
  const [active, setActive] = useState(false)
  const [date, setDateState] = useState(null)
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const dates = replay?.dates ?? []

  const engage = useCallback(async () => {
    setActive(true)
    if (replay) return
    setLoading(true)
    try {
      const res = await fetch('/data/output/breadth_replay.json')
      if (!res.ok) throw new Error(`replay fetch failed: ${res.status}`)
      const json = await res.json()
      setReplay(json)
      setDateState(json.dates[json.dates.length - 1])
      setError(null)
    } catch (err) {
      setError(err.message)
      setActive(false)
    } finally {
      setLoading(false)
    }
  }, [replay])

  const setDate = useCallback((d) => {
    setPlaying(false)
    setDateState(d)
  }, [])

  const step = useCallback((delta) => {
    setPlaying(false)
    setDateState((cur) => {
      const i = dates.indexOf(cur)
      if (i === -1) return cur
      const next = Math.min(Math.max(i + delta, 0), dates.length - 1)
      return dates[next]
    })
  }, [dates])

  const togglePlay = useCallback(() => setPlaying((p) => !p), [])

  const jumpYtd = useCallback(() => {
    setPlaying(false)
    if (!dates.length) return
    const year = dates[dates.length - 1].slice(0, 4)
    const first = dates.find((d) => d.startsWith(year))
    if (first) setDateState(first)
  }, [dates])

  const exitToLatest = useCallback(() => {
    setPlaying(false)
    setActive(false)
    if (dates.length) setDateState(dates[dates.length - 1])
  }, [dates])

  useEffect(() => {
    if (!playing) return undefined
    timerRef.current = setInterval(() => {
      setDateState((cur) => {
        const i = dates.indexOf(cur)
        if (i === -1 || i >= dates.length - 1) {
          setPlaying(false)
          return cur
        }
        return dates[i + 1]
      })
    }, PLAY_INTERVAL_MS)
    return () => clearInterval(timerRef.current)
  }, [playing, dates])

  const sliced = useMemo(
    () => (active && replay && date ? sliceToDate(replay, date) : null),
    [active, replay, date],
  )

  return { active, date, dates, playing, loading, error, sliced,
           engage, setDate, step, togglePlay, jumpYtd, exitToLatest }
}
```

- [ ] **Step 2: Build check**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`
Expected: success.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/breadth/useTimeMachine.js
git commit -m "feat(breadth-ui): useTimeMachine hook — lazy replay fetch, stepping, play"
```

---

### Task 7: TimeMachineBar + BreadthPage integration

**Files:**
- Create: `frontend/src/components/breadth/TimeMachineBar.jsx`
- Modify: `frontend/src/components/breadth/BreadthPage.jsx`

**Interfaces:**
- Consumes: `useTimeMachine` (Task 6).
- Produces: `<TimeMachineBar tm={tm} />`; `BreadthPage` renders the bar above
  `VerdictBanner` and, when `tm.active && tm.sliced`, feeds every child from
  `tm.sliced.breadth` / `tm.sliced.marketHealth` instead of the live props.

- [ ] **Step 1: TimeMachineBar**

Create `frontend/src/components/breadth/TimeMachineBar.jsx`:

```jsx
export default function TimeMachineBar({ tm }) {
  const idx = tm.dates.indexOf(tm.date)

  if (!tm.active) {
    return (
      <div className="flex items-center gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-4 py-2">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Market Time Machine
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)] flex-1">
          Replay the dashboard using only information available through a past trading date.
        </span>
        <button
          onClick={tm.engage}
          disabled={tm.loading}
          className="text-[11px] px-2 py-1 rounded border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-hover-bg)] disabled:opacity-50"
        >
          {tm.loading ? 'Loading…' : 'Enable'}
        </button>
        {tm.error && (
          <span className="text-[10px] text-[var(--color-loss)]">{tm.error}</span>
        )}
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-signal-caution)] rounded px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-signal-caution)]">
          Historical snapshot · {tm.date} · future observations excluded
        </span>
        <div className="flex items-center gap-1">
          <BarButton onClick={() => tm.step(-1)} label="◀" />
          <BarButton onClick={tm.togglePlay} label={tm.playing ? '❚❚ Pause' : '▶ Play'} />
          <BarButton onClick={() => tm.step(1)} label="▶" />
          <BarButton onClick={tm.jumpYtd} label="YTD" />
          <BarButton onClick={tm.exitToLatest} label="Latest" />
        </div>
      </div>
      <input
        type="range"
        min={0}
        max={Math.max(tm.dates.length - 1, 0)}
        value={idx < 0 ? 0 : idx}
        onChange={(e) => tm.setDate(tm.dates[Number(e.target.value)])}
        className="w-full accent-[var(--color-signal-caution)]"
      />
      <div className="flex justify-between text-[9px] font-mono text-[var(--color-text-muted)] mt-1">
        <span>{tm.dates[0]}</span>
        <span>{tm.dates[tm.dates.length - 1]}</span>
      </div>
    </div>
  )
}

function BarButton({ onClick, label }) {
  return (
    <button
      onClick={onClick}
      className="text-[10px] font-mono px-2 py-1 rounded border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-hover-bg)]"
    >
      {label}
    </button>
  )
}
```

- [ ] **Step 2: Integrate into BreadthPage**

In `frontend/src/components/breadth/BreadthPage.jsx`: add imports

```jsx
import TimeMachineBar from './TimeMachineBar'
import { useTimeMachine } from './useTimeMachine'
```

At the top of the component (before the early return), add:

```jsx
  const tm = useTimeMachine()
```

Replace the two source lines so children read replayed data when pinned —
change `const breadth = data?.breadth` and `const mh = data?.market_health` to:

```jsx
  const liveBreadth = data?.breadth
  const breadth = (tm.active && tm.sliced) ? tm.sliced.breadth : liveBreadth
  const mh = (tm.active && tm.sliced) ? tm.sliced.marketHealth : data?.market_health
```

Then render the bar as the first child of the returned `<div className="space-y-3">`:

```jsx
      <TimeMachineBar tm={tm} />
```

Keep the "No breadth data available" early return, but base it on `liveBreadth`
so the bar itself never disappears:

```jsx
  if (!liveBreadth) {
```

(and inside that branch, render `<div className="space-y-3"><TimeMachineBar tm={tm} />` followed by the existing message div.)

- [ ] **Step 3: Build check**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`
Expected: success.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/breadth/TimeMachineBar.jsx frontend/src/components/breadth/BreadthPage.jsx
git commit -m "feat(breadth-ui): Time Machine bar wired into the breadth page"
```

---

### Task 8: End-to-end — real replay file + browser verification

**Files:**
- Modify (data only): `data/output/breadth.json`, `data/output/market_health.json`, `data/output/breadth_replay.json`

- [ ] **Step 1: Full Python suite**

Run: `python3 -m pytest pipeline/tests/ tests/ -q`
Expected: only the 4 known content-processor failures.

- [ ] **Step 2: Generate all three files in one session (network: 2 downloads)**

```bash
python3 - <<'EOF'
import json, datetime as dt
import pandas as pd, yfinance as yf
from pipeline.screeners.breadth_store import load_archive
from pipeline.screeners.breadth_signals import run_signals, build_replay

def flat(df):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.droplevel(1, axis=1)
    df.index = pd.DatetimeIndex(df.index).tz_localize(None)
    return df

spy = flat(yf.download('SPY', period='3y', auto_adjust=True, progress=False))
qqq = flat(yf.download('QQQ', period='3y', auto_adjust=True, progress=False))
frame = load_archive('data/history/breadth_archive.csv')
ts = dt.datetime.now(dt.timezone.utc).isoformat()

breadth = json.load(open('data/output/breadth.json'))
health = run_signals(breadth, frame, spy, qqq)
replay = build_replay(frame, spy, qqq)

json.dump(breadth, open('data/output/breadth.json', 'w'), indent=1)
json.dump({'timestamp': ts, 'stale': False, **health},
          open('data/output/market_health.json', 'w'), indent=1)
json.dump({'timestamp': ts, **replay},
          open('data/output/breadth_replay.json', 'w'), indent=1)

last = replay['dates'][-1]
assert replay['verdicts'][last] == breadth['verdict'], 'replay/live verdict mismatch'
import os
print('dates:', len(replay['dates']), replay['dates'][0], '..', last)
print('replay size KB:', round(os.path.getsize('data/output/breadth_replay.json') / 1024))
print('health candles:', len(replay['health']['spy']['candles']))
print('latest env:', replay['verdicts'][last]['env'],
      '| 2026-07-15 env:', replay['verdicts'].get('2026-07-15', {}).get('env'))
EOF
```

Sanity gates: dates count equals the archive row count; the replay's latest
verdict equals the live one; health candles ≥ the archive span; file under
~1.5 MB.

- [ ] **Step 3: Browser verification**

```bash
rm -rf frontend/public/data/output && cp -r data/output frontend/public/data/output
```

Start the dev server (preview tools, `fluxus-dashboard` launch config or a
worktree entry), open `/#/breadth`, then verify:
1. Bar shows "Market Time Machine … Enable"; page identical to before; no
   request for `breadth_replay.json` in the network log.
2. Click Enable → replay fetched once, amber pinned banner appears at the
   latest date, page content unchanged from live.
3. Drag to **2026-07-15** → banner reads that date; verdict/tiles/charts/table
   all show that day as the most recent point (table's first row = 7/15);
   danger panels show that date.
4. ▶/◀ step one session; Play advances then stops at the end; YTD jumps to the
   first session of 2026; Latest exits to live mode.
5. Console clean throughout.

Fix anything that fails, re-verify, then:

```bash
rm -rf frontend/public/data/output
```

- [ ] **Step 4: Commit the data**

```bash
git add data/output/breadth.json data/output/market_health.json data/output/breadth_replay.json
git commit -m "data(breadth): replay book + regenerated verdict/health from one session"
```
