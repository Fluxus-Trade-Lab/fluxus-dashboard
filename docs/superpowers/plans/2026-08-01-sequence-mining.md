# Sequence Mining Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether ordered screener sequences ("Episodic Pivot, then a 4% day within 10 sessions") lead anywhere — reporting MFE/MAE in R and SPY-relative returns against a random-entry baseline, with a split-sample stability check and n on every row.

**Architecture:** A one-time price-panel builder downloads OHLC for the archive's tickers into a local cache. Pure functions in a new `pipeline/research/` package measure per-instance outcomes and enumerate sequence instances from the event archive. A CLI joins them, applies three anti-false-positive guards, and writes a ranked markdown + CSV report. Nothing is added to `data/output/` and no UI is built. Spec: `docs/plans/2026-08-01-sequence-mining-design.md`.

**Tech Stack:** Python 3.11+ / pandas / yfinance / pytest

## Global Constraints

- `pipeline/research/outcomes.py` and `pipeline/research/sequences.py` are **pure**: no I/O, no clock, no network, no reads outside their arguments. Missing/insufficient data returns `None` or an empty result — never an exception.
- No `date.today()` / `datetime.now()` in engine code. Dates come from the event archive and the price index.
- **Sequence windows are counted in archive-session index, not calendar days** — 17 archive dates are absent by design, so calendar arithmetic would be wrong.
- Outcomes are measured from the **next session's open after the signal date**, and the signal date for a pair/triple is its **last leg** (the confirmation).
- Every reported statistic is **sequence minus random-entry baseline**; nothing is reported as a bare absolute.
- Instances lost to missing price data are **counted and reported per sequence**, never silently dropped.
- Cache files go under `.cache/` (already gitignored). Reports go to `data/research/` and are committed.
- Do not modify `data/history/ticker_events.csv`, anything in `data/output/`, or any existing screener/breadth module.
- Python tests: `python3 -m pytest` from repo root. Known baseline: 4 pre-existing failures in `pipeline/tests/test_content_processor.py` — ignore.
- Reproducibility: the same `--seed` must yield an identical report.

---

### Task 1: Package scaffold + ATR

**Files:**
- Create: `pipeline/research/__init__.py`
- Create: `pipeline/research/outcomes.py`
- Create: `pipeline/tests/test_outcomes.py`

**Interfaces:**
- Produces: `atr(bars: pd.DataFrame, period: int = 14) -> pd.Series` — Wilder's ATR over a DataFrame with `High`/`Low`/`Close` columns, DatetimeIndex ascending. Returns a Series aligned to `bars.index`; the first `period` entries are NaN. Pure.

- [ ] **Step 1: Write the failing test**

Create `pipeline/tests/test_outcomes.py`:

```python
"""Tests for per-instance outcome measurement."""
import numpy as np
import pandas as pd
import pytest


def _bars(highs, lows, closes, opens=None, end='2026-05-29'):
    n = len(closes)
    idx = pd.bdate_range(end=end, periods=n)
    return pd.DataFrame({
        'Open': opens if opens is not None else closes,
        'High': highs, 'Low': lows, 'Close': closes,
    }, index=idx)


class TestAtr:
    def test_constant_range_gives_that_range(self):
        """Every bar spans exactly 2.0 with no gaps -> ATR converges to 2.0."""
        from pipeline.research.outcomes import atr
        n = 40
        bars = _bars(highs=[101.0] * n, lows=[99.0] * n, closes=[100.0] * n)
        a = atr(bars, period=14)
        assert a.iloc[-1] == pytest.approx(2.0, abs=1e-9)

    def test_first_period_entries_are_nan(self):
        from pipeline.research.outcomes import atr
        bars = _bars(highs=[101.0] * 20, lows=[99.0] * 20, closes=[100.0] * 20)
        a = atr(bars, period=14)
        assert a.iloc[:14].isna().all()
        assert not np.isnan(a.iloc[14])

    def test_true_range_uses_prior_close_gaps(self):
        """A gap up makes TR = high - prior_close, larger than high - low."""
        from pipeline.research.outcomes import atr
        highs = [101.0] * 19 + [120.0]
        lows = [99.0] * 19 + [118.0]
        closes = [100.0] * 19 + [119.0]
        bars = _bars(highs, lows, closes)
        a = atr(bars, period=14)
        prev = atr(bars.iloc[:-1], period=14).iloc[-1]
        # last TR = max(120-118, |120-100|, |118-100|) = 20
        expected = (prev * 13 + 20.0) / 14
        assert a.iloc[-1] == pytest.approx(expected, rel=1e-9)

    def test_short_input_all_nan(self):
        from pipeline.research.outcomes import atr
        bars = _bars(highs=[101.0] * 5, lows=[99.0] * 5, closes=[100.0] * 5)
        assert atr(bars, period=14).isna().all()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_outcomes.py -v`
Expected: FAIL with "No module named 'pipeline.research'".

- [ ] **Step 3: Implement**

Create empty `pipeline/research/__init__.py`.

Create `pipeline/research/outcomes.py`:

```python
"""Per-instance outcome measurement for signal research.

Given one ticker's bars and a signal date, measure what happened next:
forward returns, SPY-relative excess, and maximum favorable/adverse
excursion expressed in ATR-multiples (R) so results read in the same
units as a stop/target framework.

Pure functions only: no I/O, no clock, no network. Insufficient data
returns None rather than raising.
Spec: docs/plans/2026-08-01-sequence-mining-design.md
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import pandas as pd


def atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's ATR aligned to bars.index; first `period` entries are NaN."""
    high, low, close = bars['High'], bars['Low'], bars['Close']
    prev_close = close.shift(1)
    true_range = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    # Wilder smoothing == EMA with alpha = 1/period; require a full window first
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period + 1).mean()
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_outcomes.py -v`
Expected: all PASS. If `test_first_period_entries_are_nan` fails on the boundary,
check `min_periods` — the first true range is NaN (no prior close), so a full
window is only available at index `period`.

- [ ] **Step 5: Commit**

```bash
git add pipeline/research/__init__.py pipeline/research/outcomes.py pipeline/tests/test_outcomes.py
git commit -m "feat(research): research package + Wilder ATR"
```

---

### Task 2: measure_outcome

**Files:**
- Modify: `pipeline/research/outcomes.py`
- Test: `pipeline/tests/test_outcomes.py`

**Interfaces:**
- Consumes: `atr` (Task 1).
- Produces:

```python
HORIZONS = (5, 10, 21)

measure_outcome(bars: pd.DataFrame, spy: pd.DataFrame, signal_date: str,
                horizons: Sequence[int] = HORIZONS,
                atr_period: int = 14) -> dict | None
```

  Returns `None` when: `signal_date` is not in `bars.index`; there is no next
  session; ATR at `signal_date` is NaN or ≤ 0; or fewer than `max(horizons)`
  bars exist after the entry bar. Otherwise a dict with `entry_date` (the next
  session, ISO), `entry_open`, `atr` and, per horizon `h`: `ret_{h}`,
  `excess_{h}`, `mfe_r_{h}`, `mae_r_{h}`.

  Definitions, entry = next session's open after `signal_date`:
  - `ret_h` = `close[entry_idx + h - 1] / entry_open - 1`
  - `excess_h` = `ret_h` − SPY's return over the same entry→exit dates
  - `mfe_r_h` = `(max High over bars[entry_idx : entry_idx+h] − entry_open) / atr`
  - `mae_r_h` = `(min Low over the same slice − entry_open) / atr`
  SPY return uses the same calendar dates; if either SPY date is missing,
  `excess_h` is `None` for that horizon (the rest of the dict still returns).

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_outcomes.py`:

```python
def _flat_spy(index, level=400.0):
    return pd.DataFrame({'Open': level, 'High': level, 'Low': level,
                         'Close': level}, index=index)


class TestMeasureOutcome:
    def _setup(self):
        """40 warm-up bars at 100 (ATR 2.0), then a known 6-bar excursion."""
        warm_h = [101.0] * 40
        warm_l = [99.0] * 40
        warm_c = [100.0] * 40
        # entry bar opens at 100; over the next 5 bars high hits 110, low hits 96
        fwd_o = [100.0, 104.0, 106.0, 103.0, 105.0]
        fwd_h = [104.0, 107.0, 110.0, 106.0, 108.0]
        fwd_l = [99.0, 103.0, 105.0, 96.0, 104.0]
        fwd_c = [103.0, 106.0, 105.0, 104.0, 107.0]
        bars = _bars(warm_h + fwd_h, warm_l + fwd_l, warm_c + fwd_c,
                     opens=warm_c + fwd_o)
        return bars

    def test_known_excursion_in_r(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index)
        signal_date = bars.index[39].strftime('%Y-%m-%d')   # last warm-up bar
        out = measure_outcome(bars, spy, signal_date, horizons=(5,))
        assert out is not None
        assert out['entry_date'] == bars.index[40].strftime('%Y-%m-%d')
        assert out['entry_open'] == pytest.approx(100.0)
        assert out['atr'] == pytest.approx(2.0, abs=1e-6)
        # close at entry_idx + 5 - 1 = index 44 -> 107.0
        assert out['ret_5'] == pytest.approx(107.0 / 100.0 - 1)
        # SPY flat -> excess equals ret
        assert out['excess_5'] == pytest.approx(out['ret_5'])
        # max high 110 -> (110-100)/2 = 5.0 R ; min low 96 -> (96-100)/2 = -2.0 R
        assert out['mfe_r_5'] == pytest.approx(5.0)
        assert out['mae_r_5'] == pytest.approx(-2.0)

    def test_excess_subtracts_spy(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index).copy()
        # SPY rises 3% from entry date to exit date
        spy.loc[spy.index[40], 'Close'] = 400.0
        spy.loc[spy.index[44], 'Close'] = 412.0
        out = measure_outcome(bars, spy, bars.index[39].strftime('%Y-%m-%d'),
                              horizons=(5,))
        assert out['excess_5'] == pytest.approx(out['ret_5'] - (412.0 / 400.0 - 1))

    def test_none_when_signal_date_absent(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        assert measure_outcome(bars, _flat_spy(bars.index), '1999-01-04',
                               horizons=(5,)) is None

    def test_none_when_insufficient_forward_bars(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index)
        late = bars.index[-2].strftime('%Y-%m-%d')
        assert measure_outcome(bars, spy, late, horizons=(5,)) is None

    def test_none_when_atr_undefined(self):
        from pipeline.research.outcomes import measure_outcome
        short = _bars([101.0] * 12, [99.0] * 12, [100.0] * 12)
        assert measure_outcome(short, _flat_spy(short.index),
                               short.index[2].strftime('%Y-%m-%d'),
                               horizons=(5,)) is None

    def test_none_when_no_next_session(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        last = bars.index[-1].strftime('%Y-%m-%d')
        assert measure_outcome(bars, _flat_spy(bars.index), last,
                               horizons=(5,)) is None

    def test_missing_spy_date_nulls_only_excess(self):
        from pipeline.research.outcomes import measure_outcome
        bars = self._setup()
        spy = _flat_spy(bars.index).drop(index=bars.index[44])
        out = measure_outcome(bars, spy, bars.index[39].strftime('%Y-%m-%d'),
                              horizons=(5,))
        assert out is not None
        assert out['excess_5'] is None
        assert out['ret_5'] is not None
        assert out['mfe_r_5'] == pytest.approx(5.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_outcomes.py::TestMeasureOutcome -v`
Expected: FAIL with "cannot import name 'measure_outcome'".

- [ ] **Step 3: Implement**

Append to `pipeline/research/outcomes.py`:

```python
HORIZONS = (5, 10, 21)


def measure_outcome(bars: pd.DataFrame, spy: pd.DataFrame, signal_date: str,
                    horizons: Sequence[int] = HORIZONS,
                    atr_period: int = 14) -> Optional[Dict[str, Any]]:
    """What happened after `signal_date`. Entry = next session's open.

    Returns None when the instance is unmeasurable (unknown date, no next
    session, undefined ATR, or too few forward bars) — callers count these
    as coverage loss rather than dropping them silently.
    """
    index = bars.index
    dates = index.strftime('%Y-%m-%d')
    matches = (dates == signal_date).nonzero()[0]
    if len(matches) == 0:
        return None
    sig_idx = int(matches[0])
    entry_idx = sig_idx + 1
    max_h = max(horizons)
    if entry_idx >= len(bars) or entry_idx + max_h > len(bars):
        return None

    atr_series = atr(bars, period=atr_period)
    atr_at_signal = atr_series.iloc[sig_idx]
    if pd.isna(atr_at_signal) or atr_at_signal <= 0:
        return None

    entry_open = float(bars['Open'].iloc[entry_idx])
    if entry_open <= 0:
        return None

    spy_dates = spy.index.strftime('%Y-%m-%d')
    spy_close = pd.Series(spy['Close'].values, index=spy_dates)
    entry_date = dates[entry_idx]

    out: Dict[str, Any] = {
        'entry_date': entry_date,
        'entry_open': round(entry_open, 4),
        'atr': round(float(atr_at_signal), 4),
    }

    for h in horizons:
        window = bars.iloc[entry_idx:entry_idx + h]
        exit_date = dates[entry_idx + h - 1]
        ret = float(window['Close'].iloc[-1]) / entry_open - 1
        out[f'ret_{h}'] = round(ret, 6)
        out[f'mfe_r_{h}'] = round((float(window['High'].max()) - entry_open)
                                  / float(atr_at_signal), 4)
        out[f'mae_r_{h}'] = round((float(window['Low'].min()) - entry_open)
                                  / float(atr_at_signal), 4)
        if entry_date in spy_close.index and exit_date in spy_close.index:
            spy_entry = float(spy_close.loc[entry_date])
            spy_exit = float(spy_close.loc[exit_date])
            spy_ret = spy_exit / spy_entry - 1 if spy_entry > 0 else 0.0
            out[f'excess_{h}'] = round(ret - spy_ret, 6)
        else:
            out[f'excess_{h}'] = None

    return out
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_outcomes.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/research/outcomes.py pipeline/tests/test_outcomes.py
git commit -m "feat(research): measure_outcome — forward returns, excess, MFE/MAE in R"
```

---

### Task 3: Sequence enumeration

**Files:**
- Create: `pipeline/research/sequences.py`
- Create: `pipeline/tests/test_sequences.py`

**Interfaces:**
- Consumes: an events frame shaped like `pipeline.screeners.ticker_events.load_events` output (columns incl. `date`, `ticker`, `screener`).
- Produces:

```python
session_index(events: pd.DataFrame) -> dict[str, int]

find_pair_instances(events: pd.DataFrame, a: str, b: str,
                    window: int = 10) -> list[dict]

find_triple_instances(events: pd.DataFrame, a: str, b: str, c: str,
                      window: int = 10) -> list[dict]
```

  `session_index` maps each distinct archive date to its ordinal position
  (0-based, ascending).

  A pair instance: ticker has screener `a` on `d1` and `b` on `d2` with
  `0 < idx(d2) − idx(d1) <= window`. For each `d1`, only the **first**
  qualifying `d2` counts. Instances are keyed by `(ticker, d1)` so the same
  `d1` never produces two rows. Output dicts:
  `{'ticker', 'signal_date' (= d2), 'leg_dates': [d1, d2], 'gap': idx(d2)-idx(d1)}`.
  Sorted by `(signal_date, ticker)`.

  Triple: `a` on `d1`, first qualifying `b` on `d2` (within `window` of `d1`),
  then first qualifying `c` on `d3` (within `window` of `d2`).
  `signal_date` = `d3`, `leg_dates` = `[d1, d2, d3]`,
  `gap` = `idx(d3) − idx(d1)`.

  All pure. Unknown screener names or an empty frame yield `[]`.

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_sequences.py`:

```python
"""Tests for sequence enumeration over the event archive."""
import pandas as pd
import pytest


def _events(rows):
    """rows: (date, ticker, screener) tuples."""
    return pd.DataFrame(
        [{'date': d, 'ticker': t, 'screener': s} for d, t, s in rows],
        columns=['date', 'ticker', 'screener'],
    )


# 10 consecutive archive sessions, deliberately NOT contiguous calendar days
DATES = ['2026-05-01', '2026-05-04', '2026-05-05', '2026-05-06', '2026-05-07',
         '2026-05-08', '2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14']


class TestSessionIndex:
    def test_maps_dates_to_ordinals(self):
        from pipeline.research.sequences import session_index
        ev = _events([(d, 'ABC', 'vcp') for d in DATES])
        idx = session_index(ev)
        assert idx[DATES[0]] == 0 and idx[DATES[-1]] == 9

    def test_ignores_duplicates_and_sorts(self):
        from pipeline.research.sequences import session_index
        ev = _events([(DATES[3], 'A', 'vcp'), (DATES[1], 'B', 'vcp'),
                      (DATES[3], 'C', 'vcp')])
        assert session_index(ev) == {DATES[1]: 0, DATES[3]: 1}


class TestFindPairInstances:
    def test_finds_planted_sequence(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([
            (DATES[0], 'ABC', 'episodic_pivot'),
            (DATES[3], 'ABC', 'gainers_4pct'),
            (DATES[2], 'XYZ', 'vcp'),          # different screener, no match
        ])
        got = find_pair_instances(ev, 'episodic_pivot', 'gainers_4pct', window=10)
        assert len(got) == 1
        assert got[0]['ticker'] == 'ABC'
        assert got[0]['signal_date'] == DATES[3]
        assert got[0]['leg_dates'] == [DATES[0], DATES[3]]
        assert got[0]['gap'] == 3

    def test_window_boundary_inclusive_then_exclusive(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([(DATES[0], 'ABC', 'vcp'), (DATES[3], 'ABC', 'gainers_4pct')])
        assert len(find_pair_instances(ev, 'vcp', 'gainers_4pct', window=3)) == 1
        assert len(find_pair_instances(ev, 'vcp', 'gainers_4pct', window=2)) == 0

    def test_same_day_is_not_a_sequence(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([(DATES[2], 'ABC', 'vcp'), (DATES[2], 'ABC', 'gainers_4pct')])
        assert find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10) == []

    def test_only_first_qualifying_b_counts(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'gainers_4pct'),
            (DATES[4], 'ABC', 'gainers_4pct'),   # later b for the same a
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert len(got) == 1 and got[0]['signal_date'] == DATES[2]

    def test_separate_a_events_each_produce_an_instance(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([
            (DATES[0], 'ABC', 'vcp'), (DATES[1], 'ABC', 'gainers_4pct'),
            (DATES[5], 'ABC', 'vcp'), (DATES[6], 'ABC', 'gainers_4pct'),
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert [g['signal_date'] for g in got] == [DATES[1], DATES[6]]

    def test_b_before_a_is_not_a_sequence(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([(DATES[0], 'ABC', 'gainers_4pct'), (DATES[3], 'ABC', 'vcp')])
        assert find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10) == []

    def test_tickers_are_independent(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([(DATES[0], 'ABC', 'vcp'), (DATES[1], 'XYZ', 'gainers_4pct')])
        assert find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10) == []

    def test_empty_and_unknown(self):
        from pipeline.research.sequences import find_pair_instances
        assert find_pair_instances(_events([]), 'vcp', 'gainers_4pct') == []
        ev = _events([(DATES[0], 'ABC', 'vcp')])
        assert find_pair_instances(ev, 'vcp', 'nope') == []

    def test_sorted_by_signal_date_then_ticker(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _events([
            (DATES[0], 'ZZZ', 'vcp'), (DATES[2], 'ZZZ', 'gainers_4pct'),
            (DATES[0], 'AAA', 'vcp'), (DATES[2], 'AAA', 'gainers_4pct'),
            (DATES[0], 'MMM', 'vcp'), (DATES[1], 'MMM', 'gainers_4pct'),
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert [(g['signal_date'], g['ticker']) for g in got] == [
            (DATES[1], 'MMM'), (DATES[2], 'AAA'), (DATES[2], 'ZZZ')]


class TestFindTripleInstances:
    def test_finds_planted_triple(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _events([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'gainers_4pct'),
            (DATES[5], 'ABC', 'vol_up_gainers'),
        ])
        got = find_triple_instances(ev, 'vcp', 'gainers_4pct', 'vol_up_gainers',
                                    window=10)
        assert len(got) == 1
        assert got[0]['signal_date'] == DATES[5]
        assert got[0]['leg_dates'] == [DATES[0], DATES[2], DATES[5]]
        assert got[0]['gap'] == 5

    def test_each_leg_respects_the_window(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _events([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[1], 'ABC', 'gainers_4pct'),
            (DATES[6], 'ABC', 'vol_up_gainers'),   # 5 sessions after leg 2
        ])
        assert len(find_triple_instances(ev, 'vcp', 'gainers_4pct',
                                         'vol_up_gainers', window=5)) == 1
        assert find_triple_instances(ev, 'vcp', 'gainers_4pct',
                                     'vol_up_gainers', window=4) == []

    def test_missing_third_leg_yields_nothing(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _events([(DATES[0], 'ABC', 'vcp'), (DATES[2], 'ABC', 'gainers_4pct')])
        assert find_triple_instances(ev, 'vcp', 'gainers_4pct',
                                     'vol_up_gainers', window=10) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_sequences.py -v`
Expected: FAIL with "No module named 'pipeline.research.sequences'".

- [ ] **Step 3: Implement**

Create `pipeline/research/sequences.py`:

```python
"""Sequence enumeration over the point-in-time event archive.

An instance of "A then B" is one ticker showing screener A on an archive
session and B on a later session within `window` SESSIONS (not calendar
days — the archive deliberately omits non-session and untrustworthy days,
so calendar arithmetic would misstate the gap).

Outcomes are measured from the LAST leg: that is the confirmation, and
the earliest point a trade could be taken.

Pure functions only: no I/O, no clock.
Spec: docs/plans/2026-08-01-sequence-mining-design.md
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def session_index(events: pd.DataFrame) -> Dict[str, int]:
    """Archive date -> 0-based ordinal position, ascending."""
    if len(events) == 0:
        return {}
    dates = sorted(set(events['date'].astype(str)))
    return {d: i for i, d in enumerate(dates)}


def _dates_by_screener(events: pd.DataFrame, screener: str) -> Dict[str, List[str]]:
    """ticker -> sorted list of dates on which `screener` fired."""
    sub = events[events['screener'] == screener]
    out: Dict[str, List[str]] = {}
    for ticker, grp in sub.groupby('ticker', sort=False):
        out[str(ticker)] = sorted(set(grp['date'].astype(str)))
    return out


def _first_after(candidates: List[str], start_idx: int, window: int,
                 idx: Dict[str, int]) -> str | None:
    """Earliest candidate date strictly after start_idx and within window."""
    for d in candidates:
        gap = idx[d] - start_idx
        if 0 < gap <= window:
            return d
    return None


def find_pair_instances(events: pd.DataFrame, a: str, b: str,
                        window: int = 10) -> List[Dict[str, Any]]:
    """Instances of `a` then `b` within `window` archive sessions."""
    if len(events) == 0:
        return []
    idx = session_index(events)
    a_dates = _dates_by_screener(events, a)
    b_dates = _dates_by_screener(events, b)

    out: List[Dict[str, Any]] = []
    for ticker, firsts in a_dates.items():
        seconds = b_dates.get(ticker)
        if not seconds:
            continue
        for d1 in firsts:
            d2 = _first_after(seconds, idx[d1], window, idx)
            if d2 is None:
                continue
            out.append({'ticker': ticker, 'signal_date': d2,
                        'leg_dates': [d1, d2], 'gap': idx[d2] - idx[d1]})
    out.sort(key=lambda r: (r['signal_date'], r['ticker']))
    return out


def find_triple_instances(events: pd.DataFrame, a: str, b: str, c: str,
                          window: int = 10) -> List[Dict[str, Any]]:
    """Instances of `a` then `b` then `c`, each leg within `window` sessions."""
    if len(events) == 0:
        return []
    idx = session_index(events)
    a_dates = _dates_by_screener(events, a)
    b_dates = _dates_by_screener(events, b)
    c_dates = _dates_by_screener(events, c)

    out: List[Dict[str, Any]] = []
    for ticker, firsts in a_dates.items():
        seconds, thirds = b_dates.get(ticker), c_dates.get(ticker)
        if not seconds or not thirds:
            continue
        for d1 in firsts:
            d2 = _first_after(seconds, idx[d1], window, idx)
            if d2 is None:
                continue
            d3 = _first_after(thirds, idx[d2], window, idx)
            if d3 is None:
                continue
            out.append({'ticker': ticker, 'signal_date': d3,
                        'leg_dates': [d1, d2, d3], 'gap': idx[d3] - idx[d1]})
    out.sort(key=lambda r: (r['signal_date'], r['ticker']))
    return out
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_sequences.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/research/sequences.py pipeline/tests/test_sequences.py
git commit -m "feat(research): pair/triple sequence enumeration in session space"
```

---

### Task 4: Statistics, baseline, split-sample

**Files:**
- Modify: `pipeline/research/sequences.py`
- Test: `pipeline/tests/test_sequences.py`

**Interfaces:**
- Consumes: `session_index` (Task 3).
- Produces:

```python
MIN_N = 20

summarize(outcomes: list[dict], horizons=(5, 10, 21), lost: int = 0) -> dict
random_instances(events: pd.DataFrame, n: int, seed: int,
                 rng_tickers: list[str] | None = None) -> list[dict]
split_dates(events: pd.DataFrame) -> tuple[str, str]
is_unstable(first_half: dict, second_half: dict, key: str) -> bool
```

  - `summarize` — over a list of `measure_outcome` dicts, returns
    `{'n', 'lost', 'median_excess_{h}', 'mean_excess_{h}', 'median_mfe_r_{h}',
    'median_mae_r_{h}', 'win_rate_{h}'}` for each horizon. `None` values are
    skipped per-statistic (an instance with `excess_5 is None` still counts
    toward `mfe_r_5`). Empty input → `{'n': 0, 'lost': lost}` and every
    statistic `None`. `win_rate_h` = share of non-None `excess_h` > 0.
  - `random_instances` — `n` draws of `{'ticker', 'signal_date'}` sampled
    uniformly from the archive's (ticker, date) universe using
    `random.Random(seed)`; deterministic for a given seed. Tickers restricted
    to `rng_tickers` when provided.
  - `split_dates` — returns `(midpoint_date, last_date)`; the first half is
    dates `<= midpoint`, the second half `> midpoint`. Midpoint is the median
    archive session.
  - `is_unstable` — True when the two halves disagree in sign on `key`, or
    when either half has `n < MIN_N`. A sequence flagged unstable is excluded
    from the ranking.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_sequences.py`:

```python
def _outcome(excess_5=None, mfe=1.0, mae=-1.0, ret=0.01):
    return {'entry_date': '2026-05-05', 'entry_open': 100.0, 'atr': 2.0,
            'ret_5': ret, 'excess_5': excess_5, 'mfe_r_5': mfe, 'mae_r_5': mae}


class TestSummarize:
    def test_basic_statistics(self):
        from pipeline.research.sequences import summarize
        outs = [_outcome(excess_5=0.10, mfe=3.0, mae=-1.0),
                _outcome(excess_5=-0.02, mfe=1.0, mae=-2.0),
                _outcome(excess_5=0.04, mfe=2.0, mae=-0.5)]
        s = summarize(outs, horizons=(5,), lost=2)
        assert s['n'] == 3 and s['lost'] == 2
        assert s['median_excess_5'] == pytest.approx(0.04)
        assert s['mean_excess_5'] == pytest.approx((0.10 - 0.02 + 0.04) / 3)
        assert s['median_mfe_r_5'] == pytest.approx(2.0)
        assert s['median_mae_r_5'] == pytest.approx(-1.0)
        assert s['win_rate_5'] == pytest.approx(2 / 3)

    def test_none_excess_skipped_but_r_still_counted(self):
        from pipeline.research.sequences import summarize
        outs = [_outcome(excess_5=None, mfe=4.0, mae=-1.0),
                _outcome(excess_5=0.06, mfe=2.0, mae=-3.0)]
        s = summarize(outs, horizons=(5,))
        assert s['n'] == 2
        assert s['median_excess_5'] == pytest.approx(0.06)   # only the one
        assert s['win_rate_5'] == pytest.approx(1.0)
        assert s['median_mfe_r_5'] == pytest.approx(3.0)     # both counted

    def test_empty(self):
        from pipeline.research.sequences import summarize
        s = summarize([], horizons=(5,), lost=7)
        assert s['n'] == 0 and s['lost'] == 7
        assert s['median_excess_5'] is None and s['win_rate_5'] is None


class TestRandomInstances:
    def test_deterministic_for_a_seed(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B', 'C')])
        first = random_instances(ev, n=10, seed=42)
        second = random_instances(ev, n=10, seed=42)
        assert first == second
        assert len(first) == 10
        assert set(first[0]) == {'ticker', 'signal_date'}

    def test_different_seeds_differ(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B', 'C')])
        assert random_instances(ev, n=10, seed=1) != random_instances(ev, n=10, seed=2)

    def test_draws_come_from_the_archive_universe(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B')])
        for inst in random_instances(ev, n=20, seed=7):
            assert inst['ticker'] in {'A', 'B'}
            assert inst['signal_date'] in DATES

    def test_ticker_restriction(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B', 'C')])
        for inst in random_instances(ev, n=15, seed=3, rng_tickers=['B']):
            assert inst['ticker'] == 'B'


class TestSplitAndStability:
    def test_split_dates_midpoint(self):
        from pipeline.research.sequences import split_dates
        ev = _events([(d, 'A', 'vcp') for d in DATES])
        mid, last = split_dates(ev)
        assert mid == DATES[4] and last == DATES[-1]

    def test_unstable_on_sign_disagreement(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 50, 'median_excess_10': 0.05}
        b = {'n': 50, 'median_excess_10': -0.03}
        assert is_unstable(a, b, 'median_excess_10') is True

    def test_stable_when_both_positive_and_powered(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 30, 'median_excess_10': 0.05}
        b = {'n': 25, 'median_excess_10': 0.02}
        assert is_unstable(a, b, 'median_excess_10') is False

    def test_unstable_when_a_half_is_underpowered(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 30, 'median_excess_10': 0.05}
        b = {'n': 3, 'median_excess_10': 0.04}
        assert is_unstable(a, b, 'median_excess_10') is True

    def test_unstable_when_a_half_has_no_value(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 30, 'median_excess_10': 0.05}
        b = {'n': 30, 'median_excess_10': None}
        assert is_unstable(a, b, 'median_excess_10') is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_sequences.py::TestSummarize -v`
Expected: FAIL with "cannot import name 'summarize'".

- [ ] **Step 3: Implement**

Append to `pipeline/research/sequences.py` (add `import random` and
`import statistics` at the top of the module):

```python
MIN_N = 20


def summarize(outcomes: List[Dict[str, Any]],
              horizons: Any = (5, 10, 21), lost: int = 0) -> Dict[str, Any]:
    """Aggregate measured outcomes. None values are skipped per-statistic."""
    out: Dict[str, Any] = {'n': len(outcomes), 'lost': lost}

    def _vals(key: str) -> List[float]:
        return [o[key] for o in outcomes
                if o.get(key) is not None and not pd.isna(o.get(key))]

    for h in horizons:
        excess = _vals(f'excess_{h}')
        mfe = _vals(f'mfe_r_{h}')
        mae = _vals(f'mae_r_{h}')
        out[f'median_excess_{h}'] = round(statistics.median(excess), 6) if excess else None
        out[f'mean_excess_{h}'] = round(statistics.fmean(excess), 6) if excess else None
        out[f'median_mfe_r_{h}'] = round(statistics.median(mfe), 4) if mfe else None
        out[f'median_mae_r_{h}'] = round(statistics.median(mae), 4) if mae else None
        out[f'win_rate_{h}'] = (round(sum(1 for v in excess if v > 0) / len(excess), 4)
                                if excess else None)
    return out


def random_instances(events: pd.DataFrame, n: int, seed: int,
                     rng_tickers: List[str] | None = None) -> List[Dict[str, str]]:
    """`n` uniform draws from the archive's (ticker, date) universe. Deterministic."""
    if len(events) == 0 or n <= 0:
        return []
    tickers = sorted(set(rng_tickers if rng_tickers is not None
                         else events['ticker'].astype(str)))
    dates = sorted(set(events['date'].astype(str)))
    if not tickers or not dates:
        return []
    rng = random.Random(seed)
    return [{'ticker': rng.choice(tickers), 'signal_date': rng.choice(dates)}
            for _ in range(n)]


def split_dates(events: pd.DataFrame) -> tuple[str, str]:
    """(midpoint_date, last_date). First half is <= midpoint."""
    dates = sorted(set(events['date'].astype(str)))
    return dates[(len(dates) - 1) // 2], dates[-1]


def is_unstable(first_half: Dict[str, Any], second_half: Dict[str, Any],
                key: str) -> bool:
    """True when the halves disagree in sign, or either is under-powered."""
    a, b = first_half.get(key), second_half.get(key)
    if a is None or b is None:
        return True
    if first_half.get('n', 0) < MIN_N or second_half.get('n', 0) < MIN_N:
        return True
    return (a > 0) != (b > 0)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_sequences.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/research/sequences.py pipeline/tests/test_sequences.py
git commit -m "feat(research): summary stats, random baseline, split-sample stability"
```

---

### Task 5: Price panel builder

**Files:**
- Create: `pipeline/tools/build_price_panel.py`
- Create: `pipeline/tests/test_build_price_panel.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces:
  - `panel_tickers(events: pd.DataFrame) -> list[str]` — pure; sorted distinct
    tickers from the events frame plus `'SPY'`.
  - `coverage_report(requested: list[str], returned: list[str]) -> dict` —
    pure; `{'requested': int, 'returned': int, 'missing': sorted list}`.
  - CLI: `python3 -m pipeline.tools.build_price_panel [--refresh] [--cache PATH]`
    writes `.cache/price_panel.pkl` — a dict `{ticker: DataFrame}` with
    `Open/High/Low/Close` and a tz-naive DatetimeIndex — and
    `data/research/price_coverage.json`.
  - Download span: from 60 business days before the archive's first date to
    25 business days after its last date, via `yf.download(..., start=, end=,
    auto_adjust=True, group_by='ticker', threads=True)` in batches of 200.

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_build_price_panel.py`:

```python
"""Tests for the price panel builder (pure functions only — no network)."""
import pandas as pd


def _events(rows):
    return pd.DataFrame([{'date': d, 'ticker': t, 'screener': 'vcp'}
                         for d, t in rows], columns=['date', 'ticker', 'screener'])


class TestPanelTickers:
    def test_distinct_sorted_plus_spy(self):
        from pipeline.tools.build_price_panel import panel_tickers
        ev = _events([('2026-05-04', 'ZZZ'), ('2026-05-05', 'AAA'),
                      ('2026-05-06', 'ZZZ')])
        assert panel_tickers(ev) == ['AAA', 'SPY', 'ZZZ']

    def test_spy_not_duplicated(self):
        from pipeline.tools.build_price_panel import panel_tickers
        ev = _events([('2026-05-04', 'SPY'), ('2026-05-05', 'AAA')])
        assert panel_tickers(ev) == ['AAA', 'SPY']

    def test_empty_events_still_yields_spy(self):
        from pipeline.tools.build_price_panel import panel_tickers
        assert panel_tickers(_events([])) == ['SPY']


class TestCoverageReport:
    def test_counts_and_missing_list(self):
        from pipeline.tools.build_price_panel import coverage_report
        rep = coverage_report(['AAA', 'BBB', 'CCC', 'SPY'], ['AAA', 'SPY'])
        assert rep['requested'] == 4 and rep['returned'] == 2
        assert rep['missing'] == ['BBB', 'CCC']

    def test_full_coverage(self):
        from pipeline.tools.build_price_panel import coverage_report
        rep = coverage_report(['AAA', 'SPY'], ['SPY', 'AAA'])
        assert rep['missing'] == [] and rep['returned'] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_build_price_panel.py -v`
Expected: FAIL with "No module named 'pipeline.tools.build_price_panel'".

- [ ] **Step 3: Implement**

Create `pipeline/tools/build_price_panel.py`:

```python
"""Build the OHLC price panel the sequence research needs.

The event archive records what fired and when, never what happened next.
This tool downloads daily bars for every ticker the archive mentions (plus
SPY) across the archive window, with lead-in for ATR warm-up and tail for
the longest forward horizon.

Coverage is REPORTED, not hidden: delisted and renamed tickers fail to
download, and those failures skew toward losers — dropping them silently
would bias every downstream result upward.

Not part of the cron. Run manually:
    python3 -m pipeline.tools.build_price_panel
    python3 -m pipeline.tools.build_price_panel --refresh
"""

from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from pipeline.screeners.ticker_events import load_events

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_EVENTS = _REPO / 'data' / 'history' / 'ticker_events.csv'
_DEFAULT_CACHE = _REPO / '.cache' / 'price_panel.pkl'
_COVERAGE = _REPO / 'data' / 'research' / 'price_coverage.json'

LEAD_IN_DAYS = 60      # ATR(14) warm-up plus slack
TAIL_DAYS = 25         # longest forward horizon (21) plus slack
BATCH_SIZE = 200


def panel_tickers(events: pd.DataFrame) -> List[str]:
    """Sorted distinct tickers in the archive, plus SPY."""
    if len(events) == 0:
        return ['SPY']
    return sorted(set(events['ticker'].astype(str)) | {'SPY'})


def coverage_report(requested: List[str], returned: List[str]) -> Dict[str, Any]:
    """What we asked for vs what we got — the survivorship disclosure."""
    missing = sorted(set(requested) - set(returned))
    return {'requested': len(requested), 'returned': len(returned),
            'missing': missing}


# ── network (not unit-tested) ────────────────────────────────────────

def _download(tickers: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    import yfinance as yf
    panel: Dict[str, pd.DataFrame] = {}
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        logger.info("Downloading %d-%d of %d", i, i + len(batch), len(tickers))
        data = yf.download(batch, start=start, end=end, group_by='ticker',
                           auto_adjust=True, progress=False, threads=True)
        for t in batch:
            try:
                frame = data[t][['Open', 'High', 'Low', 'Close']].dropna(how='all')
            except (KeyError, TypeError):
                continue
            if frame.empty:
                continue
            frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
            panel[t] = frame.sort_index()
    return panel


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--cache', default=str(_DEFAULT_CACHE))
    parser.add_argument('--events', default=str(_DEFAULT_EVENTS))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    cache = Path(args.cache)
    if cache.exists() and not args.refresh:
        print(f"Cache already present at {cache} — use --refresh to rebuild.")
        return 0

    events = load_events(args.events)
    if len(events) == 0:
        print("Event archive is empty — nothing to download.")
        return 1

    tickers = panel_tickers(events)
    first, last = str(events['date'].min()), str(events['date'].max())
    start = (pd.Timestamp(first) - pd.tseries.offsets.BDay(LEAD_IN_DAYS)).strftime('%Y-%m-%d')
    end = (pd.Timestamp(last) + pd.tseries.offsets.BDay(TAIL_DAYS)).strftime('%Y-%m-%d')
    logger.info("Panel: %d tickers, %s .. %s", len(tickers), start, end)

    panel = _download(tickers, start, end)
    rep = coverage_report(tickers, sorted(panel))

    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, 'wb') as f:
        pickle.dump(panel, f)
    _COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    _COVERAGE.write_text(json.dumps(rep, indent=2), encoding='utf-8')

    print(f"\nPanel written to {cache}")
    print(f"Coverage: {rep['returned']}/{rep['requested']} tickers "
          f"({len(rep['missing'])} missing — see {_COVERAGE})")
    if 'SPY' not in panel:
        print("WARNING: SPY missing — excess returns cannot be computed.")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

Append to `.gitignore` (after the existing `.cache/` line, which already
covers the panel — add only the research coverage note):

```
# Sequence-mining price panel lives in .cache/ (already ignored above)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_build_price_panel.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/tools/build_price_panel.py pipeline/tests/test_build_price_panel.py .gitignore
git commit -m "feat(research): price panel builder with coverage disclosure"
```

---

### Task 6: The mining CLI

**Files:**
- Create: `pipeline/research/mine_sequences.py`
- Create: `pipeline/tests/test_mine_sequences.py`

**Interfaces:**
- Consumes: `measure_outcome`/`HORIZONS` (Tasks 1-2); `find_pair_instances`,
  `find_triple_instances`, `summarize`, `random_instances`, `split_dates`,
  `is_unstable`, `MIN_N` (Tasks 3-4); the panel written by Task 5;
  `load_events`.
- Produces:
  - `measure_instances(instances, panel, spy, horizons) -> tuple[list[dict], int]`
    — pure given a panel dict; returns `(outcomes, lost_count)`. An instance
    whose ticker is absent from the panel, or whose `measure_outcome` returns
    `None`, counts toward `lost`.
  - `net_of_baseline(seq: dict, base: dict, horizons) -> dict` — pure; for each
    numeric statistic present in both, `seq - base`, keyed with a `net_` prefix;
    `None` when either side is `None`.
  - `render_markdown(rows: list[dict], meta: dict) -> str` — pure; the report.
  - CLI: `python3 -m pipeline.research.mine_sequences [--window 10]
    [--min-n 20] [--horizons 5,10,21] [--seed 42] [--triples]`
    writes `data/research/sequences_<as_of>.md` and `.csv`.

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_mine_sequences.py`:

```python
"""Tests for the sequence-mining CLI's pure pieces."""
import pandas as pd
import pytest


def _panel_frame(n=60, start_price=100.0, end='2026-06-30'):
    idx = pd.bdate_range(end=end, periods=n)
    closes = [start_price] * n
    return pd.DataFrame({'Open': closes, 'High': [c + 1 for c in closes],
                         'Low': [c - 1 for c in closes], 'Close': closes}, index=idx)


class TestMeasureInstances:
    def test_counts_missing_ticker_as_lost(self):
        from pipeline.research.mine_sequences import measure_instances
        panel = {'ABC': _panel_frame()}
        spy = _panel_frame()
        date = panel['ABC'].index[30].strftime('%Y-%m-%d')
        instances = [{'ticker': 'ABC', 'signal_date': date},
                     {'ticker': 'GONE', 'signal_date': date}]
        outcomes, lost = measure_instances(instances, panel, spy, horizons=(5,))
        assert len(outcomes) == 1 and lost == 1

    def test_counts_unmeasurable_as_lost(self):
        from pipeline.research.mine_sequences import measure_instances
        panel = {'ABC': _panel_frame()}
        spy = _panel_frame()
        late = panel['ABC'].index[-1].strftime('%Y-%m-%d')   # no forward bars
        outcomes, lost = measure_instances(
            [{'ticker': 'ABC', 'signal_date': late}], panel, spy, horizons=(5,))
        assert outcomes == [] and lost == 1

    def test_empty_input(self):
        from pipeline.research.mine_sequences import measure_instances
        assert measure_instances([], {}, _panel_frame(), horizons=(5,)) == ([], 0)


class TestNetOfBaseline:
    def test_subtracts_matching_keys(self):
        from pipeline.research.mine_sequences import net_of_baseline
        seq = {'median_excess_5': 0.08, 'win_rate_5': 0.6, 'median_mfe_r_5': 3.0,
               'median_mae_r_5': -1.0, 'mean_excess_5': 0.07}
        base = {'median_excess_5': 0.01, 'win_rate_5': 0.5, 'median_mfe_r_5': 2.0,
                'median_mae_r_5': -1.5, 'mean_excess_5': 0.02}
        net = net_of_baseline(seq, base, horizons=(5,))
        assert net['net_median_excess_5'] == pytest.approx(0.07)
        assert net['net_win_rate_5'] == pytest.approx(0.1)
        assert net['net_median_mfe_r_5'] == pytest.approx(1.0)
        assert net['net_median_mae_r_5'] == pytest.approx(0.5)

    def test_none_when_either_side_missing(self):
        from pipeline.research.mine_sequences import net_of_baseline
        net = net_of_baseline({'median_excess_5': 0.08}, {'median_excess_5': None},
                              horizons=(5,))
        assert net['net_median_excess_5'] is None
        net2 = net_of_baseline({}, {'median_excess_5': 0.01}, horizons=(5,))
        assert net2['net_median_excess_5'] is None


class TestRenderMarkdown:
    def _rows(self):
        return [
            {'sequence': 'vcp -> gainers_4pct', 'n': 40, 'lost': 3,
             'net_median_excess_10': 0.055, 'median_mfe_r_10': 3.1,
             'median_mae_r_10': -1.2, 'win_rate_10': 0.62,
             'under_powered': False, 'unstable': False},
            {'sequence': 'ema21_watch -> vcp', 'n': 8, 'lost': 0,
             'net_median_excess_10': 0.20, 'median_mfe_r_10': 5.0,
             'median_mae_r_10': -0.5, 'win_rate_10': 0.9,
             'under_powered': True, 'unstable': False},
            {'sequence': 'vcp -> vol_up_gainers', 'n': 35, 'lost': 1,
             'net_median_excess_10': 0.03, 'median_mfe_r_10': 2.0,
             'median_mae_r_10': -1.8, 'win_rate_10': 0.55,
             'under_powered': False, 'unstable': True},
        ]

    def test_limits_are_stated_first(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), {'as_of': '2026-07-30', 'window': 10,
                                            'seed': 42, 'min_n': 20,
                                            'sessions': 89, 'tickers': 3872,
                                            'coverage_missing': 120})
        head = md.split('## Ranked')[0]
        assert 'one regime' in head.lower()
        assert 'baseline' in head.lower()
        assert 'survivorship' in head.lower()

    def test_ranked_excludes_flagged_rows(self):
        from pipeline.research.mine_sequences import render_markdown
        md = render_markdown(self._rows(), {'as_of': '2026-07-30', 'window': 10,
                                            'seed': 42, 'min_n': 20,
                                            'sessions': 89, 'tickers': 3872,
                                            'coverage_missing': 0})
        ranked = md.split('## Ranked')[1].split('##')[0]
        assert 'vcp -> gainers_4pct' in ranked
        assert 'ema21_watch -> vcp' not in ranked      # under-powered
        assert 'vcp -> vol_up_gainers' not in ranked   # unstable
        # but both still appear somewhere in the report
        assert 'ema21_watch -> vcp' in md and 'vcp -> vol_up_gainers' in md

    def test_states_when_nothing_clears_the_bar(self):
        from pipeline.research.mine_sequences import render_markdown
        rows = [dict(self._rows()[1])]     # only an under-powered row
        md = render_markdown(rows, {'as_of': '2026-07-30', 'window': 10,
                                    'seed': 42, 'min_n': 20, 'sessions': 89,
                                    'tickers': 100, 'coverage_missing': 0})
        ranked = md.split('## Ranked')[1].split('##')[0]
        assert 'No sequence' in ranked
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_mine_sequences.py -v`
Expected: FAIL with "No module named 'pipeline.research.mine_sequences'".

- [ ] **Step 3: Implement**

Create `pipeline/research/mine_sequences.py`:

```python
"""Rank screener sequences by measured edge over a random-entry baseline.

Testing ~49 pairs (and optionally hundreds of triples) against five months
of one market regime WILL produce impressive-looking results by chance.
Three guards push back, and all three appear in the report:

  1. every statistic is reported net of a random-entry baseline drawn from
     the same ticker/date universe — beating zero is not the bar;
  2. each sequence is scored independently in the first and second half of
     the window, and a sign flip flags it `unstable`;
  3. anything below `--min-n` is shown but excluded from the ranking.

"No sequence clears the bar" is a legitimate result, and the report says so
plainly when it happens.

    python3 -m pipeline.research.mine_sequences --window 10 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import itertools
import logging
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

from pipeline.research.outcomes import HORIZONS, measure_outcome
from pipeline.research.sequences import (
    MIN_N, find_pair_instances, find_triple_instances, is_unstable,
    random_instances, split_dates, summarize,
)
from pipeline.screeners.ticker_events import load_events
from pipeline.screeners.ticker_heat import WEIGHTS

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_EVENTS = _REPO / 'data' / 'history' / 'ticker_events.csv'
_DEFAULT_PANEL = _REPO / '.cache' / 'price_panel.pkl'
_OUT_DIR = _REPO / 'data' / 'research'

RANK_KEY_TEMPLATE = 'net_median_excess_{h}'
RANK_HORIZON = 10


def measure_instances(instances: List[Dict[str, Any]],
                      panel: Dict[str, pd.DataFrame],
                      spy: pd.DataFrame,
                      horizons: Sequence[int] = HORIZONS
                      ) -> Tuple[List[Dict[str, Any]], int]:
    """Measure each instance; return (outcomes, count lost to missing data)."""
    outcomes: List[Dict[str, Any]] = []
    lost = 0
    for inst in instances:
        bars = panel.get(inst['ticker'])
        if bars is None:
            lost += 1
            continue
        out = measure_outcome(bars, spy, inst['signal_date'], horizons=horizons)
        if out is None:
            lost += 1
            continue
        outcomes.append(out)
    return outcomes, lost


_NET_KEYS = ('median_excess_{h}', 'mean_excess_{h}', 'median_mfe_r_{h}',
             'median_mae_r_{h}', 'win_rate_{h}')


def net_of_baseline(seq: Dict[str, Any], base: Dict[str, Any],
                    horizons: Sequence[int] = HORIZONS) -> Dict[str, Any]:
    """Sequence statistics minus the baseline's, prefixed `net_`."""
    out: Dict[str, Any] = {}
    for h in horizons:
        for template in _NET_KEYS:
            key = template.format(h=h)
            a, b = seq.get(key), base.get(key)
            out[f'net_{key}'] = None if a is None or b is None else round(a - b, 6)
    return out


def render_markdown(rows: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    """The report: limits first, then the ranking, then what was excluded."""
    rank_key = RANK_KEY_TEMPLATE.format(h=RANK_HORIZON)
    lines: List[str] = []
    lines.append(f"# Sequence mining — as of {meta['as_of']}\n")
    lines.append("## Read this before the table\n")
    lines.append(
        f"- **One regime.** {meta['sessions']} archive sessions across a single "
        "market environment. A sequence that works here may only be describing "
        "that environment.\n"
        f"- **Multiple comparisons.** Many sequences were tested; some will look "
        "excellent by chance. Every number below is reported **net of a "
        "random-entry baseline** drawn from the same tickers and dates, and any "
        "sequence whose two half-samples disagree in sign is flagged unstable "
        "and excluded from the ranking.\n"
        f"- **Survivorship.** Prices were fetched today, so delisted and renamed "
        f"tickers are missing ({meta['coverage_missing']} of "
        f"{meta['tickers']} tickers). Those failures skew toward losers, so the "
        "surviving numbers are, if anything, flattering. Per-sequence "
        "instances lost to missing prices are in the `lost` column.\n"
        f"- **Window.** {meta['window']} archive sessions. The archive omits "
        "non-session and untrustworthy days, so an N-session gap spans more "
        "calendar time than N days.\n"
        f"- Ranked on `{rank_key}`; `--min-n {meta['min_n']}`, `--seed "
        f"{meta['seed']}`.\n"
    )

    ranked = [r for r in rows if not r['under_powered'] and not r['unstable']]
    ranked.sort(key=lambda r: (r.get(rank_key) is None, -(r.get(rank_key) or 0)))

    lines.append("## Ranked sequences\n")
    if not ranked:
        lines.append(
            "**No sequence cleared the bar.** Every candidate was either "
            "under-powered or unstable across the two half-samples. That is a "
            "real result, not a tooling failure — on this much data, in this one "
            "regime, nothing here is distinguishable from random entry.\n")
    else:
        lines.append(f"| Sequence | n | lost | net median excess ({RANK_HORIZON}d) "
                     f"| median MFE (R) | median MAE (R) | win rate |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for r in ranked:
            lines.append(
                f"| {r['sequence']} | {r['n']} | {r['lost']} "
                f"| {_fmt_pct(r.get(rank_key))} "
                f"| {_fmt_num(r.get(f'median_mfe_r_{RANK_HORIZON}'))} "
                f"| {_fmt_num(r.get(f'median_mae_r_{RANK_HORIZON}'))} "
                f"| {_fmt_pct(r.get(f'win_rate_{RANK_HORIZON}'), pct=True)} |")
        lines.append("")

    unstable = [r for r in rows if r['unstable'] and not r['under_powered']]
    lines.append("## Excluded — unstable across half-samples\n")
    lines.append(_simple_list(unstable, rank_key) or "_None._\n")

    weak = [r for r in rows if r['under_powered']]
    lines.append(f"## Excluded — fewer than {meta['min_n']} instances\n")
    lines.append(_simple_list(weak, rank_key) or "_None._\n")

    return "\n".join(lines)


def _fmt_num(v: Any) -> str:
    return '—' if v is None else f"{v:.2f}"


def _fmt_pct(v: Any, pct: bool = False) -> str:
    if v is None:
        return '—'
    return f"{v * 100:.1f}%" if not pct else f"{v * 100:.0f}%"


def _simple_list(rows: List[Dict[str, Any]], rank_key: str) -> str:
    if not rows:
        return ''
    out = ["| Sequence | n | net median excess |", "|---|---:|---:|"]
    for r in sorted(rows, key=lambda r: -(r.get(rank_key) or 0)):
        out.append(f"| {r['sequence']} | {r['n']} | {_fmt_pct(r.get(rank_key))} |")
    return "\n".join(out) + "\n"


# ── CLI (I/O; the pieces above are pure) ─────────────────────────────

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--window', type=int, default=10)
    parser.add_argument('--min-n', type=int, default=MIN_N)
    parser.add_argument('--horizons', default='5,10,21')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--triples', action='store_true')
    parser.add_argument('--events', default=str(_DEFAULT_EVENTS))
    parser.add_argument('--panel', default=str(_DEFAULT_PANEL))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    horizons = tuple(int(h) for h in args.horizons.split(','))
    panel_path = Path(args.panel)
    if not panel_path.exists():
        print(f"No price panel at {panel_path}. Run:\n"
              f"  python3 -m pipeline.tools.build_price_panel")
        return 1
    with open(panel_path, 'rb') as f:
        panel: Dict[str, pd.DataFrame] = pickle.load(f)
    spy = panel.get('SPY')
    if spy is None:
        print("Panel has no SPY — excess returns cannot be computed.")
        return 1

    events = load_events(args.events)
    if len(events) == 0:
        print("Event archive is empty.")
        return 1

    mid, last = split_dates(events)
    first_half = events[events['date'].astype(str) <= mid]
    second_half = events[events['date'].astype(str) > mid]
    screeners = sorted(WEIGHTS)

    candidates: List[Tuple[str, Tuple[str, ...]]] = [
        (f"{a} -> {b}", (a, b))
        for a, b in itertools.product(screeners, repeat=2) if a != b
    ]
    if args.triples:
        candidates += [
            (f"{a} -> {b} -> {c}", (a, b, c))
            for a, b, c in itertools.product(screeners, repeat=3)
            if a != b and b != c
        ]
    logger.info("Evaluating %d candidate sequences", len(candidates))

    def _find(frame: pd.DataFrame, legs: Tuple[str, ...]) -> List[Dict[str, Any]]:
        if len(legs) == 2:
            return find_pair_instances(frame, legs[0], legs[1], window=args.window)
        return find_triple_instances(frame, legs[0], legs[1], legs[2],
                                     window=args.window)

    rows: List[Dict[str, Any]] = []
    for label, legs in candidates:
        instances = _find(events, legs)
        outcomes, lost = measure_instances(instances, panel, spy, horizons)
        seq_stats = summarize(outcomes, horizons=horizons, lost=lost)
        if seq_stats['n'] == 0:
            continue

        base_inst = random_instances(events, n=seq_stats['n'], seed=args.seed)
        base_out, base_lost = measure_instances(base_inst, panel, spy, horizons)
        base_stats = summarize(base_out, horizons=horizons, lost=base_lost)

        half_stats = []
        for half in (first_half, second_half):
            h_out, h_lost = measure_instances(_find(half, legs), panel, spy, horizons)
            half_stats.append(summarize(h_out, horizons=horizons, lost=h_lost))

        row: Dict[str, Any] = {'sequence': label, **seq_stats}
        row.update(net_of_baseline(seq_stats, base_stats, horizons))
        row['under_powered'] = seq_stats['n'] < args.min_n
        row['unstable'] = is_unstable(half_stats[0], half_stats[1],
                                      f'median_excess_{RANK_HORIZON}')
        rows.append(row)

    coverage = len(set(events['ticker'].astype(str)) - set(panel))
    meta = {'as_of': last, 'window': args.window, 'seed': args.seed,
            'min_n': args.min_n, 'sessions': events['date'].nunique(),
            'tickers': events['ticker'].nunique(), 'coverage_missing': coverage}

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = _OUT_DIR / f"sequences_{last}.md"
    csv_path = _OUT_DIR / f"sequences_{last}.csv"
    md_path.write_text(render_markdown(rows, meta), encoding='utf-8')
    if rows:
        fieldnames = sorted({k for r in rows for k in r})
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    ranked = [r for r in rows if not r['under_powered'] and not r['unstable']]
    print(f"\n{len(rows)} sequences evaluated, {len(ranked)} cleared the bar")
    print(f"Report: {md_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_mine_sequences.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the whole suite**

Run: `python3 -m pytest pipeline/tests/ tests/ -q`
Expected: only the 4 known content-processor failures.

- [ ] **Step 6: Commit**

```bash
git add pipeline/research/mine_sequences.py pipeline/tests/test_mine_sequences.py
git commit -m "feat(research): sequence mining CLI with baseline and stability guards"
```

---

### Task 7: Real run — build the panel and mine

**Files:**
- Modify (data only): `data/research/price_coverage.json`, `data/research/sequences_<as_of>.md`, `data/research/sequences_<as_of>.csv`

- [ ] **Step 1: Full suite**

Run: `python3 -m pytest pipeline/tests/ tests/ -q`
Expected: only the 4 known content-processor failures.

- [ ] **Step 2: Build the price panel (network, ~20-40 min)**

```bash
python3 -m pipeline.tools.build_price_panel
```

Sanity gates before proceeding — STOP and report if any fails:
- coverage ≥ 85% of requested tickers (below that, the survivorship hole is
  too large to interpret results at all)
- `SPY` present
- the panel's date range starts before the archive's first date and ends
  after its last

- [ ] **Step 3: Mine pairs**

```bash
python3 -m pipeline.research.mine_sequences --window 10 --seed 42
```

Then inspect and report:

```bash
python3 - <<'EOF'
import glob, pandas as pd
path = sorted(glob.glob('data/research/sequences_*.csv'))[-1]
df = pd.read_csv(path)
print(f"{len(df)} sequences | cleared: {(~df.under_powered & ~df.unstable).sum()}")
print(f"under-powered: {df.under_powered.sum()} | unstable: {df.unstable.sum()}")
ok = df[~df.under_powered & ~df.unstable].nlargest(10, 'net_median_excess_10')
print(ok[['sequence','n','lost','net_median_excess_10','median_mfe_r_10',
          'median_mae_r_10','win_rate_10']].to_string(index=False))
print("\ntotal instances lost to missing prices:", int(df['lost'].sum()))
EOF
```

- [ ] **Step 4: Reproducibility check**

Re-run the same command and confirm the CSV is byte-identical:

```bash
cp data/research/sequences_*.csv /tmp/seq_first.csv
python3 -m pipeline.research.mine_sequences --window 10 --seed 42
diff -q /tmp/seq_first.csv data/research/sequences_*.csv && echo "reproducible"
```

Expected: `reproducible`. If not, find the nondeterminism before continuing.

- [ ] **Step 5: Report honestly**

In your report, state plainly: how many sequences cleared the bar, the top
rows with their `n`, and — if nothing cleared — say so without softening it.
A null result is the expected outcome for a large share of these candidates
and must not be dressed up.

- [ ] **Step 6: Commit the reports**

```bash
git add data/research/
git commit -m "data(research): first sequence-mining report"
```
