# Breadth Data v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the breadth archive the single trustworthy source of truth — fix A/D, McClellan, NH/NL, add 13%/34d, add a quality guard — and backfill ~2.2 years of marked history from raw OHLC.

**Architecture:** `data/history/breadth_archive.csv` becomes canonical (one row per trading date, `source` flag). A new `pipeline/screeners/breadth_store.py` owns load/upsert/derive/write + the quality guard; `breadth_metrics.py` keeps per-day snapshot math; `run()` composes them and emits `breadth.json` as a derived view. A one-time `pipeline/tools/backfill_breadth.py` reconstructs history from a 3y OHLC download. Spec: `docs/plans/2026-07-30-breadth-data-v2-design.md`.

**Tech Stack:** Python 3.11+ / pandas / yfinance / pytest

## Global Constraints

- All `date` values are US-market trading dates (ET) via `pipeline.marketcal.market_today()` or the yfinance session index — never `date.today()` / `datetime.now()` (`tests/test_no_naive_clock.py` enforces repo-wide).
- `breadth.json` schema is additive-only: every existing key keeps its name and shape (the current React components must render unchanged).
- No TradingView anywhere in the pipeline critical path.
- `derive()` must be a pure function of the frame passed in — no reads of "today" — so Spec 3's replay can call it on truncated frames.
- Derived series (`net_advances`, `rana`, `ad_line`, `mcclellan_osc`, `ratio_5d`, `ratio_10d`) are always recomputed by `derive()`; stored values are never trusted.
- Frontend files are out of scope; do not touch `frontend/`.
- Run tests with `python3 -m pytest` from the repo root.

---

### Task 1: `perf_34d` enrichment column

**Files:**
- Modify: `pipeline/adapters/yfinance_adapter.py:441-447` (the `enriched[ticker]` dict)
- Modify: `pipeline/screeners/run_all.py:354-369` (`universe_cols` list)
- Test: `pipeline/tests/test_adapters.py`

**Interfaces:**
- Produces: universe DataFrame column `perf_34d` (float fraction, e.g. `0.13` = +13% over 34 trading sessions; `None` when < 35 rows of history). Task 2 consumes it.

- [ ] **Step 1: Write the failing test**

Append to `pipeline/tests/test_adapters.py`:

```python
class TestPerf34d:
    def test_perf_34d_formula(self):
        # 40 sessions of linearly rising closes: 100, 101, ..., 139
        import pandas as pd
        closes = pd.Series([100.0 + i for i in range(40)])
        close = float(closes.iloc[-1])          # 139
        base = float(closes.iloc[-35])          # closes[5] = 105
        expected = close / base - 1             # ≈ 0.32381
        assert abs(expected - (139 / 105 - 1)) < 1e-12
        # The adapter must use iloc[-35] (34 sessions back), mirroring perf_1m's iloc[-21]
        from pipeline.adapters import yfinance_adapter
        import inspect
        src = inspect.getsource(yfinance_adapter)
        assert "'perf_34d'" in src and 'iloc[-35]' in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest pipeline/tests/test_adapters.py::TestPerf34d -v`
Expected: FAIL on the `'perf_34d' in src` assertion.

- [ ] **Step 3: Add the column**

In `pipeline/adapters/yfinance_adapter.py`, inside the `enriched[ticker] = {` dict, directly after the `'perf_1m'` line, add:

```python
                    'perf_34d': (close / float(hist['Close'].iloc[-35]) - 1) if n >= 35 else None,
```

In `pipeline/screeners/run_all.py` `universe_cols`, change the line

```python
        'ticker', 'close', 'change_pct', 'perf_1w', 'perf_1m', 'perf_3m',
```

to

```python
        'ticker', 'close', 'change_pct', 'perf_1w', 'perf_1m', 'perf_34d', 'perf_3m',
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_adapters.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/adapters/yfinance_adapter.py pipeline/screeners/run_all.py pipeline/tests/test_adapters.py
git commit -m "feat(breadth): perf_34d enrichment column for 13%/34d scan"
```

---

### Task 2: Snapshot — 13%/34d counts + true NH/NL

**Files:**
- Modify: `pipeline/screeners/breadth_metrics.py` (`compute_snapshot`, thresholds at lines 29-30)
- Test: `pipeline/tests/test_breadth_metrics.py`

**Interfaces:**
- Consumes: `perf_34d` column from Task 1 (may be absent/NaN — treat as not counted).
- Produces: `compute_snapshot(universe) -> dict` gains keys `up_13pct_34d: int`, `down_13pct_34d: int`. `new_highs`/`new_lows` semantics change to true 52w extremes (tolerance 0.001).

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_metrics.py`:

```python
class Test13Pct34d:
    def test_counts_13pct_34d(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(10)
        universe['perf_34d'] = [0.20, 0.13, 0.129, -0.14, -0.13, -0.05, None, 0.0, 0.5, -0.5]
        result = compute_snapshot(universe)
        assert result['up_13pct_34d'] == 3    # 0.20, 0.13, 0.5
        assert result['down_13pct_34d'] == 3  # -0.14, -0.13, -0.5

    def test_missing_column_counts_zero(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(10)  # has no perf_34d column
        result = compute_snapshot(universe)
        assert result['up_13pct_34d'] == 0
        assert result['down_13pct_34d'] == 0


class TestTrueNhNl:
    def test_new_high_requires_at_extreme(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(4)
        # high_52w is (close/52w_high - 1): 0 = at high, -0.0005 within tolerance,
        # -0.015 was a "new high" under the old 2% rule and must NOT count now.
        universe['high_52w'] = [0.0, -0.0005, -0.015, -0.30]
        universe['low_52w'] = [0.0, 0.0009, 0.015, 0.80]
        result = compute_snapshot(universe)
        assert result['new_highs'] == 2
        assert result['new_lows'] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_metrics.py::Test13Pct34d pipeline/tests/test_breadth_metrics.py::TestTrueNhNl -v`
Expected: FAIL (`up_13pct_34d` missing; `new_highs == 3` under the old 2% threshold).

- [ ] **Step 3: Implement**

In `pipeline/screeners/breadth_metrics.py` replace the threshold constants:

```python
_NEW_HIGH_THRESHOLD = -0.001  # true 52w high (0.1% float/quote tolerance)
_NEW_LOW_THRESHOLD = 0.001    # true 52w low
```

In `compute_snapshot`, after the `perf_3m` line add:

```python
    perf_34d = pd.to_numeric(universe.get('perf_34d', pd.Series(dtype=float)), errors='coerce')
```

After the `down_50pct_month` line add:

```python
    up_13pct_34d = int((perf_34d >= 0.13).sum())
    down_13pct_34d = int((perf_34d <= -0.13).sum())
```

Add both keys to the returned dict (after `down_50pct_month`) **and** to the
empty-universe dict at the top of the function:

```python
        'up_13pct_34d': up_13pct_34d,
        'down_13pct_34d': down_13pct_34d,
```

(empty-universe version: `'up_13pct_34d': 0, 'down_13pct_34d': 0,`)

- [ ] **Step 4: Run the full breadth test file; fix semantic-change fallout only**

Run: `python3 -m pytest pipeline/tests/test_breadth_metrics.py -v`
Expected: new tests PASS. If any existing test asserted NH/NL counts under the
old 2% rule, update that test's expectation to the new semantics (do not loosen
anything else).

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_metrics.py pipeline/tests/test_breadth_metrics.py
git commit -m "feat(breadth): 13%/34d scan counts + true 52w NH/NL semantics"
```

---

### Task 3: `breadth_store.load_archive` — loud, migrating loader

**Files:**
- Create: `pipeline/screeners/breadth_store.py`
- Create: `pipeline/tests/test_breadth_store.py`

**Interfaces:**
- Produces:
  - `BREADTH_COLUMNS: list[str]` — canonical CSV column order:
    `['date', 'source', 'universe_size', 'spx_close', 'up_4pct', 'down_4pct', 'ratio_5d', 'ratio_10d', 'up_25pct_qtr', 'down_25pct_qtr', 'up_25pct_month', 'down_25pct_month', 'up_50pct_month', 'down_50pct_month', 'up_13pct_34d', 'down_13pct_34d', 't2108', 'pct_above_200sma', 'pct_above_50sma', 'pct_above_20sma', 'advances', 'declines', 'new_highs', 'new_lows', 'net_advances', 'rana', 'ad_line', 'mcclellan_osc']`
  - `load_archive(csv_path: str) -> pd.DataFrame` — sorted ascending by date,
    dates unique (keep-last), missing columns added (`source`→`'live'`, others→NaN),
    empty frame with `BREADTH_COLUMNS` if file absent, **raises `BreadthArchiveError`**
    if the file exists but can't be parsed.
  - `class BreadthArchiveError(RuntimeError)`

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_breadth_store.py`:

```python
"""Tests for the canonical breadth archive store."""
import pytest
import pandas as pd


def _write_legacy_csv(path):
    """Legacy-format CSV: no source/net_advances/rana/13pct cols, dup + poisoned row."""
    path.write_text(
        "date,universe_size,spx_close,up_4pct,down_4pct,ratio_5d,ratio_10d,"
        "up_25pct_qtr,down_25pct_qtr,up_25pct_month,down_25pct_month,"
        "up_50pct_month,down_50pct_month,t2108,pct_above_200sma,pct_above_50sma,"
        "pct_above_20sma,advances,declines,new_highs,new_lows,ad_line,mcclellan_osc\n"
        "2026-07-24,2900,7400.0,100,50,1.5,1.4,300,200,80,60,20,10,45.0,46.0,47.0,38.0,1500,1300,40,20,1000,5.0\n"
        "2026-07-25,2950,7405.0,110,60,1.4,1.3,310,210,82,61,21,11,45.5,46.5,47.5,38.5,1550,1350,42,22,1200,6.0\n"
        "2026-07-26,3000,7411.0,178,454,0.96,1.07,2,4,0,1,0,0,0.27,0.47,0.3,0.2,1438,1437,11,6,12244,23.7\n"
        "2026-07-26,3000,7411.0,178,454,0.73,0.99,319,528,83,231,24,53,45.1,45.97,46.7,38.43,1438,1437,251,147,12245,11.7\n"
    )


class TestLoadArchive:
    def test_missing_file_returns_empty_frame_with_columns(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive, BREADTH_COLUMNS
        frame = load_archive(str(tmp_path / 'nope.csv'))
        assert list(frame.columns) == BREADTH_COLUMNS
        assert len(frame) == 0

    def test_legacy_csv_migrates_and_dedupes_keep_last(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive
        p = tmp_path / 'archive.csv'
        _write_legacy_csv(p)
        frame = load_archive(str(p))
        assert len(frame) == 3  # dup 07-26 collapsed
        last = frame.iloc[-1]
        assert last['date'] == '2026-07-26'
        assert float(last['t2108']) == 45.1  # keep-LAST kept the good row
        assert (frame['source'] == 'live').all()  # legacy rows marked live
        assert 'up_13pct_34d' in frame.columns    # missing cols added

    def test_sorted_ascending(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive
        p = tmp_path / 'archive.csv'
        _write_legacy_csv(p)
        frame = load_archive(str(p))
        assert list(frame['date']) == sorted(frame['date'])

    def test_corrupt_file_raises_loudly(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive, BreadthArchiveError
        p = tmp_path / 'archive.csv'
        p.write_text('\x00\x01 not a csv at all')
        with pytest.raises(BreadthArchiveError):
            load_archive(str(p))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_store.py -v`
Expected: FAIL with "No module named 'pipeline.screeners.breadth_store'".

- [ ] **Step 3: Implement**

Create `pipeline/screeners/breadth_store.py`:

```python
"""Canonical breadth archive store.

The CSV at data/history/breadth_archive.csv is the single source of truth for
breadth history: one row per US trading date (ET), sorted ascending, dates
unique. `source` marks each row 'live' (measured by the daily pipeline) or
'backfill' (reconstructed from raw OHLC with today's universe — survivorship-
biased; see docs/plans/2026-07-30-breadth-data-v2-design.md).

Derived series (net_advances, rana, ad_line, mcclellan_osc, ratios) are always
recomputed by derive() over the full frame; stored values are never trusted.
derive() is a pure function of its input frame so the Time Machine (Spec 3)
can replay any truncated frame through the same code path.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

BREADTH_COLUMNS = [
    'date', 'source', 'universe_size', 'spx_close',
    'up_4pct', 'down_4pct', 'ratio_5d', 'ratio_10d',
    'up_25pct_qtr', 'down_25pct_qtr',
    'up_25pct_month', 'down_25pct_month',
    'up_50pct_month', 'down_50pct_month',
    'up_13pct_34d', 'down_13pct_34d',
    't2108', 'pct_above_200sma', 'pct_above_50sma', 'pct_above_20sma',
    'advances', 'declines', 'new_highs', 'new_lows',
    'net_advances', 'rana', 'ad_line', 'mcclellan_osc',
]


class BreadthArchiveError(RuntimeError):
    """The archive exists but cannot be read. Never silently reset it."""


def load_archive(csv_path: str) -> pd.DataFrame:
    """Load the canonical archive; migrate legacy columns; dedupe keep-last."""
    path = Path(csv_path)
    if not path.exists():
        logger.info("No breadth archive at %s — starting empty", csv_path)
        return pd.DataFrame(columns=BREADTH_COLUMNS)
    try:
        frame = pd.read_csv(path, dtype={'date': str})
    except Exception as exc:  # noqa: BLE001 — any parse failure is fatal
        raise BreadthArchiveError(f"Cannot read breadth archive {csv_path}: {exc}") from exc
    if 'date' not in frame.columns:
        raise BreadthArchiveError(f"Breadth archive {csv_path} has no 'date' column")
    if 'source' not in frame.columns:
        frame['source'] = 'live'
    frame['source'] = frame['source'].fillna('live')
    for col in BREADTH_COLUMNS:
        if col not in frame.columns:
            frame[col] = pd.NA
    frame = frame.drop_duplicates(subset='date', keep='last')
    frame = frame.sort_values('date').reset_index(drop=True)
    return frame[BREADTH_COLUMNS]
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_store.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_store.py pipeline/tests/test_breadth_store.py
git commit -m "feat(breadth): canonical archive loader — migrating, deduping, loud on corruption"
```

---

### Task 4: `breadth_store.derive` — the pure derived-series function

**Files:**
- Modify: `pipeline/screeners/breadth_store.py`
- Test: `pipeline/tests/test_breadth_store.py`

**Interfaces:**
- Consumes: a frame with base columns (`advances`, `declines`, `up_4pct`, `down_4pct`).
- Produces: `derive(frame: pd.DataFrame) -> pd.DataFrame` — returns a **copy** with
  `net_advances`, `rana`, `ad_line`, `mcclellan_osc`, `ratio_5d`, `ratio_10d`
  recomputed over the whole frame. Pure: no I/O, no clock, input not mutated.
  - `net_advances = advances - declines`
  - `rana = (A-D)/(A+D) * 1000` (0.0 where `A+D == 0`), rounded 2dp
  - `mcclellan_osc = ema19(rana) - ema39(rana)` (`ewm(span=..., adjust=False)`), rounded 2dp
  - `ad_line = cumsum(net_advances)` (int)
  - `ratio_Nd = rolling-N sum(up_4pct) / rolling-N sum(down_4pct)` (min_periods=1;
    where the down-sum is 0: the up-sum as float), rounded 4dp

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_store.py`:

```python
class TestDerive:
    def _frame(self, advances, declines, up4=None, down4=None):
        import pandas as pd
        n = len(advances)
        return pd.DataFrame({
            'date': [f'2026-01-{i+1:02d}' for i in range(n)],
            'advances': advances,
            'declines': declines,
            'up_4pct': up4 if up4 is not None else [0] * n,
            'down_4pct': down4 if down4 is not None else [0] * n,
        })

    def test_ad_line_is_true_cumulative(self):
        from pipeline.screeners.breadth_store import derive
        frame = derive(self._frame([300, 100, 250], [100, 300, 50]))
        assert list(frame['net_advances']) == [200, -200, 200]
        assert list(frame['ad_line']) == [200, 0, 200]

    def test_rana_is_universe_size_invariant(self):
        from pipeline.screeners.breadth_store import derive
        # Same 2:1 breadth on a 300-name day and a 3000-name day → identical rana
        frame = derive(self._frame([200, 2000], [100, 1000]))
        assert frame['rana'].iloc[0] == frame['rana'].iloc[1] == pytest.approx(333.33, abs=0.01)

    def test_rana_zero_when_no_participants(self):
        from pipeline.screeners.breadth_store import derive
        frame = derive(self._frame([0], [0]))
        assert frame['rana'].iloc[0] == 0.0

    def test_mcclellan_exact_value_after_step(self):
        from pipeline.screeners.breadth_store import derive
        # 39 zero-rana days then one day of rana=1000:
        # ema19 alpha=2/20 → 100.0; ema39 alpha=2/40 → 50.0; osc = 50.0 exactly.
        adv = [0] * 39 + [1000]
        dec = [0] * 40   # rana: 0 for first 39 (0/0→0), then 1000*1000/1000
        frame = derive(self._frame(adv, dec))
        assert frame['mcclellan_osc'].iloc[-1] == pytest.approx(50.0, abs=0.01)
        assert frame['mcclellan_osc'].iloc[-2] == pytest.approx(0.0, abs=0.01)

    def test_ratios_rolling_window(self):
        from pipeline.screeners.breadth_store import derive
        up4 = [10, 20, 30, 40, 50, 60]
        down4 = [5, 5, 5, 5, 5, 5]
        frame = derive(self._frame([0] * 6, [0] * 6, up4, down4))
        # day 6 ratio_5d = (20+30+40+50+60)/(5*5) = 200/25 = 8.0
        assert frame['ratio_5d'].iloc[-1] == pytest.approx(8.0)
        # day 1 (window of 1): 10/5
        assert frame['ratio_5d'].iloc[0] == pytest.approx(2.0)

    def test_ratio_zero_downs_returns_up_sum(self):
        from pipeline.screeners.breadth_store import derive
        frame = derive(self._frame([0], [0], [7], [0]))
        assert frame['ratio_5d'].iloc[0] == pytest.approx(7.0)

    def test_pure_no_mutation(self):
        from pipeline.screeners.breadth_store import derive
        original = self._frame([300], [100])
        snapshot = original.copy(deep=True)
        derive(original)
        pd.testing.assert_frame_equal(original, snapshot)

    def test_prefix_consistency_for_replay(self):
        """derive(frame[:k]) must equal derive(frame)[:k] — Spec 3 depends on this."""
        from pipeline.screeners.breadth_store import derive
        frame = self._frame([300, 100, 250, 400], [100, 300, 50, 90],
                            [10, 20, 30, 40], [5, 6, 7, 8])
        full = derive(frame)
        prefix = derive(frame.iloc[:2].reset_index(drop=True))
        for col in ['net_advances', 'rana', 'ad_line', 'mcclellan_osc', 'ratio_5d', 'ratio_10d']:
            assert list(prefix[col]) == list(full[col].iloc[:2]), col
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_store.py::TestDerive -v`
Expected: FAIL with "cannot import name 'derive'".

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_store.py`:

```python
def derive(frame: pd.DataFrame) -> pd.DataFrame:
    """Recompute all derived series over the full frame. Pure — no I/O, no clock."""
    out = frame.copy()
    if len(out) == 0:
        return out
    adv = pd.to_numeric(out['advances'], errors='coerce').fillna(0)
    dec = pd.to_numeric(out['declines'], errors='coerce').fillna(0)
    up4 = pd.to_numeric(out['up_4pct'], errors='coerce').fillna(0)
    down4 = pd.to_numeric(out['down_4pct'], errors='coerce').fillna(0)

    net = adv - dec
    out['net_advances'] = net.astype(int)

    total = adv + dec
    rana = pd.Series(0.0, index=out.index)
    nonzero = total > 0
    rana[nonzero] = (net[nonzero] / total[nonzero]) * 1000
    out['rana'] = rana.round(2)

    ema19 = rana.ewm(span=19, adjust=False).mean()
    ema39 = rana.ewm(span=39, adjust=False).mean()
    out['mcclellan_osc'] = (ema19 - ema39).round(2)

    out['ad_line'] = net.cumsum().astype(int)

    for n, col in ((5, 'ratio_5d'), (10, 'ratio_10d')):
        up_sum = up4.rolling(n, min_periods=1).sum()
        down_sum = down4.rolling(n, min_periods=1).sum()
        # Divide where the down-sum is positive; else fall back to the up-sum
        # (mirrors the legacy compute_ratios zero-division behavior).
        ratio = (up_sum / down_sum).where(down_sum > 0, up_sum)
        out[col] = ratio.astype(float).round(4)
    return out
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_store.py -v`
Expected: all PASS. If `test_mcclellan_exact_value_after_step` fails, check that
rana on the step day is exactly 1000 (`advances=1000, declines=0`) and that
`adjust=False` is set on both ewm calls.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_store.py pipeline/tests/test_breadth_store.py
git commit -m "feat(breadth): derive() — cumulative A/D, RANA McClellan, rolling ratios, replay-safe"
```

---

### Task 5: Upsert, atomic write, quality guard

**Files:**
- Modify: `pipeline/screeners/breadth_store.py`
- Test: `pipeline/tests/test_breadth_store.py`

**Interfaces:**
- Produces:
  - `upsert_row(frame: pd.DataFrame, row: dict) -> pd.DataFrame` — replaces any
    existing row with the same `date` (regardless of source), appends otherwise,
    returns sorted copy.
  - `write_archive(frame: pd.DataFrame, csv_path: str) -> None` — atomic
    (temp file in same dir + `os.replace`), columns in `BREADTH_COLUMNS` order.
  - `check_quality(frame: pd.DataFrame, snapshot: dict, null_rate: float) -> tuple[bool, str]`
    — `(True, '')` or `(False, reason)`. Rejects when `snapshot['universe_size'] < 1500`,
    `null_rate > 0.20`, or `|snapshot['pct_above_200sma'] − last row's| > 25`.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_store.py`:

```python
class TestUpsertAndWrite:
    def test_upsert_appends_new_date(self):
        from pipeline.screeners.breadth_store import load_archive, upsert_row
        frame = load_archive('/nonexistent/x.csv')
        frame = upsert_row(frame, {'date': '2026-07-28', 'source': 'live', 'advances': 100, 'declines': 50})
        assert len(frame) == 1

    def test_upsert_replaces_same_date(self):
        from pipeline.screeners.breadth_store import load_archive, upsert_row
        frame = load_archive('/nonexistent/x.csv')
        frame = upsert_row(frame, {'date': '2026-07-28', 'source': 'backfill', 'advances': 1, 'declines': 1})
        frame = upsert_row(frame, {'date': '2026-07-28', 'source': 'live', 'advances': 100, 'declines': 50})
        assert len(frame) == 1
        assert frame.iloc[0]['source'] == 'live'
        assert frame.iloc[0]['advances'] == 100

    def test_write_then_load_roundtrip(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive, upsert_row, write_archive
        p = str(tmp_path / 'a.csv')
        frame = upsert_row(load_archive(p), {'date': '2026-07-28', 'source': 'live',
                                             'advances': 100, 'declines': 50, 'up_4pct': 10, 'down_4pct': 5})
        write_archive(frame, p)
        again = load_archive(p)
        assert len(again) == 1
        assert again.iloc[0]['date'] == '2026-07-28'

    def test_write_is_atomic_no_partial_on_same_dir(self, tmp_path):
        from pipeline.screeners.breadth_store import write_archive, load_archive, upsert_row
        p = str(tmp_path / 'a.csv')
        frame = upsert_row(load_archive(p), {'date': '2026-07-28', 'source': 'live',
                                             'advances': 1, 'declines': 1})
        write_archive(frame, p)
        leftovers = [f for f in tmp_path.iterdir() if f.name != 'a.csv']
        assert leftovers == []  # temp file cleaned up by os.replace


class TestQualityGuard:
    def _last_frame(self, pct200=46.0):
        import pandas as pd
        return pd.DataFrame({'date': ['2026-07-25'], 'pct_above_200sma': [pct200]})

    def _good_snapshot(self):
        return {'universe_size': 3000, 'pct_above_200sma': 45.0}

    def test_accepts_good_row(self):
        from pipeline.screeners.breadth_store import check_quality
        ok, reason = check_quality(self._last_frame(), self._good_snapshot(), null_rate=0.02)
        assert ok and reason == ''

    def test_rejects_small_universe(self):
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'universe_size': 1400}
        ok, reason = check_quality(self._last_frame(), snap, null_rate=0.02)
        assert not ok and 'universe' in reason

    def test_rejects_high_null_rate(self):
        from pipeline.screeners.breadth_store import check_quality
        ok, reason = check_quality(self._last_frame(), self._good_snapshot(), null_rate=0.35)
        assert not ok and 'null' in reason

    def test_rejects_pct200_jump(self):
        """The 2026-07-26 poisoned row: 46.0 → 0.47 must be rejected."""
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'pct_above_200sma': 0.47}
        ok, reason = check_quality(self._last_frame(46.0), snap, null_rate=0.02)
        assert not ok and 'pct_above_200sma' in reason

    def test_first_ever_row_skips_delta_check(self):
        from pipeline.screeners.breadth_store import check_quality, load_archive
        empty = load_archive('/nonexistent/x.csv')
        ok, _ = check_quality(empty, self._good_snapshot(), null_rate=0.02)
        assert ok
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_store.py::TestUpsertAndWrite pipeline/tests/test_breadth_store.py::TestQualityGuard -v`
Expected: FAIL with import errors for `upsert_row` / `write_archive` / `check_quality`.

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/breadth_store.py`:

```python
def upsert_row(frame: pd.DataFrame, row: dict) -> pd.DataFrame:
    """Insert or replace the row for row['date']. Returns a sorted copy."""
    kept = frame[frame['date'] != row['date']]
    new = pd.DataFrame([{col: row.get(col, pd.NA) for col in BREADTH_COLUMNS}])
    out = pd.concat([kept, new], ignore_index=True)
    return out.sort_values('date').reset_index(drop=True)


def write_archive(frame: pd.DataFrame, csv_path: str) -> None:
    """Atomically write the archive: temp file in the same dir, then rename."""
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frame[BREADTH_COLUMNS]
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix='.csv.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            out.to_csv(f, index=False)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    logger.info("Wrote breadth archive (%d rows) to %s", len(out), csv_path)


# ── Quality guard thresholds (see design doc §4) ─────────────────────
_MIN_UNIVERSE = 1500
_MAX_NULL_RATE = 0.20
_MAX_PCT200_JUMP = 25.0


def check_quality(frame: pd.DataFrame, snapshot: dict, null_rate: float) -> tuple[bool, str]:
    """Reject implausible snapshots before they poison the archive."""
    size = snapshot.get('universe_size', 0)
    if size < _MIN_UNIVERSE:
        return False, f"universe_size {size} < {_MIN_UNIVERSE}"
    if null_rate > _MAX_NULL_RATE:
        return False, f"sma200_dist null rate {null_rate:.0%} > {_MAX_NULL_RATE:.0%}"
    if len(frame) > 0:
        prev = pd.to_numeric(frame['pct_above_200sma'], errors='coerce').iloc[-1]
        cur = snapshot.get('pct_above_200sma')
        if pd.notna(prev) and cur is not None and abs(cur - float(prev)) > _MAX_PCT200_JUMP:
            return False, (f"pct_above_200sma jumped {float(prev):.1f} -> {cur:.1f} "
                           f"(> {_MAX_PCT200_JUMP} pts)")
    return True, ''
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_breadth_store.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/breadth_store.py pipeline/tests/test_breadth_store.py
git commit -m "feat(breadth): upsert, atomic archive write, quality guard"
```

---

### Task 6: Rewire `run()` on the store; retire the JSON history

**Files:**
- Modify: `pipeline/screeners/breadth_metrics.py` (replace `run()`, `compute_ad_line`,
  `compute_mcclellan`, `compute_ratios`, `_load_history`, `_save_history`, `_append_csv`)
- Modify: `pipeline/screeners/run_all.py:300-305` (call site)
- Delete: `data/history/breadth_metrics_history.json`
- Test: `pipeline/tests/test_breadth_metrics.py`

**Interfaces:**
- Consumes: Task 3-5 store functions; Task 2 snapshot.
- Produces: `run(universe: pd.DataFrame, csv_path: str, spx_close: float | None = None) -> dict`
  — note the **history_path parameter is gone**. Output dict: existing keys unchanged
  (`universe_size`, `spx_close`, `mm{...}`, `breadth{...}`, `history{dates, pct_above_*,
  mcclellan_osc, rows}`), plus `mm.up_13pct_34d`, `mm.down_13pct_34d`,
  `data_quality: {stale: bool, reason?: str, as_of?: str}`, and `source` inside each
  history row. History = last 100 rows of the archive.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_breadth_metrics.py`:

```python
class TestRunOnStore:
    def _run(self, tmp_path, universe=None):
        from pipeline.screeners.breadth_metrics import run
        universe = universe if universe is not None else _make_universe(2000)
        return run(universe, str(tmp_path / 'archive.csv'), spx_close=7400.0)

    def test_output_schema_backward_compatible(self, tmp_path):
        result = self._run(tmp_path)
        for key in ['universe_size', 'spx_close', 'mm', 'breadth', 'history']:
            assert key in result
        for key in ['up_4pct', 'down_4pct', 'ratio_5d', 'ratio_10d',
                    'up_25pct_qtr', 'down_25pct_qtr', 'up_13pct_34d', 'down_13pct_34d']:
            assert key in result['mm']
        for key in ['t2108', 'pct_above_200sma', 'advances', 'declines',
                    'new_highs', 'new_lows', 'ad_line', 'mcclellan_osc']:
            assert key in result['breadth']
        for key in ['dates', 'pct_above_200sma', 'pct_above_50sma',
                    'pct_above_20sma', 'mcclellan_osc', 'rows']:
            assert key in result['history']
        assert result['data_quality'] == {'stale': False}
        assert result['history']['rows'][-1]['source'] == 'live'

    def test_rerun_same_day_is_idempotent(self, tmp_path):
        import pandas as pd
        self._run(tmp_path)
        self._run(tmp_path)
        frame = pd.read_csv(tmp_path / 'archive.csv')
        assert len(frame) == 1

    def test_guard_rejection_keeps_archive_and_flags_stale(self, tmp_path):
        import pandas as pd
        self._run(tmp_path)                                  # good day 1
        bad = _make_universe(500)                            # universe collapse
        result = self._run(tmp_path, universe=bad)
        assert result['data_quality']['stale'] is True
        assert 'universe' in result['data_quality']['reason']
        frame = pd.read_csv(tmp_path / 'archive.csv')
        assert len(frame) == 1                               # untouched
        # output still serves yesterday's data
        assert len(result['history']['rows']) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_breadth_metrics.py::TestRunOnStore -v`
Expected: FAIL (old `run()` signature takes `history_path` positionally; schema differs).

- [ ] **Step 3: Rewrite `run()` and delete dead code**

In `pipeline/screeners/breadth_metrics.py`:

1. Delete `compute_ad_line`, `compute_mcclellan`, `compute_ratios`,
   `_load_history`, `_save_history`, `_append_csv` and the `csv`/`json` imports
   they used (derived math now lives in `breadth_store.derive`; keep the module
   docstring but update it to mention the store).
2. Add import: `from pipeline.screeners.breadth_store import (load_archive, upsert_row, derive, write_archive, check_quality)`
3. Replace `run()` with:

```python
def run(
    universe: pd.DataFrame,
    csv_path: str,
    spx_close: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute today's breadth snapshot, update the canonical archive, emit breadth.json.

    The archive CSV is the single source of truth (see breadth_store). On quality
    rejection the archive is untouched and the output is served stale from its tail.
    """
    snapshot = compute_snapshot(universe)
    frame = load_archive(csv_path)

    if len(universe) > 0:
        null_rate = float(
            pd.to_numeric(universe.get('sma200_dist', pd.Series(dtype=float)),
                          errors='coerce').isna().mean()
        )
    else:
        null_rate = 1.0

    ok, reason = check_quality(frame, snapshot, null_rate)
    if ok:
        row = {
            'date': market_today().isoformat(),
            'source': 'live',
            'spx_close': spx_close,
            **snapshot,
        }
        frame = derive(upsert_row(frame, row))
        write_archive(frame, csv_path)
        quality: Dict[str, Any] = {'stale': False}
    else:
        logger.error("Breadth quality guard rejected today's row: %s", reason)
        frame = derive(frame)
        quality = {'stale': True, 'reason': reason}
        if len(frame) > 0:
            quality['as_of'] = str(frame['date'].iloc[-1])

    return _build_output(frame, quality, snapshot, spx_close)


def _build_output(
    frame: pd.DataFrame,
    quality: Dict[str, Any],
    snapshot: Dict[str, Any],
    spx_close: Optional[float],
) -> Dict[str, Any]:
    """Derive the breadth.json payload from the archive tail (last 100 rows)."""
    tail = frame.tail(100)
    rows = [
        {k: (None if pd.isna(v) else v) for k, v in r.items()}
        for r in tail.to_dict(orient='records')
    ]
    last = rows[-1] if rows else {}

    def _col(name: str) -> list:
        return [r.get(name) for r in rows]

    return {
        'universe_size': last.get('universe_size', snapshot['universe_size']),
        'spx_close': last.get('spx_close', spx_close),
        'mm': {
            'up_4pct': last.get('up_4pct'),
            'down_4pct': last.get('down_4pct'),
            'ratio_5d': last.get('ratio_5d'),
            'ratio_10d': last.get('ratio_10d'),
            'up_25pct_qtr': last.get('up_25pct_qtr'),
            'down_25pct_qtr': last.get('down_25pct_qtr'),
            'up_25pct_month': last.get('up_25pct_month'),
            'down_25pct_month': last.get('down_25pct_month'),
            'up_50pct_month': last.get('up_50pct_month'),
            'down_50pct_month': last.get('down_50pct_month'),
            'up_13pct_34d': last.get('up_13pct_34d'),
            'down_13pct_34d': last.get('down_13pct_34d'),
        },
        'breadth': {
            't2108': last.get('t2108'),
            'pct_above_200sma': last.get('pct_above_200sma'),
            'pct_above_50sma': last.get('pct_above_50sma'),
            'pct_above_20sma': last.get('pct_above_20sma'),
            'advances': last.get('advances'),
            'declines': last.get('declines'),
            'new_highs': last.get('new_highs'),
            'new_lows': last.get('new_lows'),
            'ad_line': last.get('ad_line'),
            'mcclellan_osc': last.get('mcclellan_osc'),
        },
        'history': {
            'dates': _col('date'),
            'pct_above_200sma': _col('pct_above_200sma'),
            'pct_above_50sma': _col('pct_above_50sma'),
            'pct_above_20sma': _col('pct_above_20sma'),
            'mcclellan_osc': _col('mcclellan_osc'),
            'rows': rows,
        },
        'data_quality': quality,
    }
```

4. In `pipeline/screeners/run_all.py:300-305`, replace the call:

```python
    breadth_result = run_breadth_metrics(
        universe,
        str(HISTORY_DIR / 'breadth_archive.csv'),
        spx_close=spx_close,
    )
```

- [ ] **Step 4: Run the breadth suites; update tests of deleted functions**

Run: `python3 -m pytest pipeline/tests/test_breadth_metrics.py pipeline/tests/test_breadth_store.py -v`
Expected: `TestRunOnStore` PASS. `TestMcClellan` / `TestAdLine` (they test the
deleted `compute_mcclellan` / `compute_ad_line`) now fail on import — delete those
two test classes; their behavior is covered by `TestDerive` in test_breadth_store.py.

- [ ] **Step 5: Retire the JSON history and run the whole test suite**

```bash
git rm data/history/breadth_metrics_history.json
python3 -m pytest pipeline/tests/ -v
```

Expected: all PASS (including `test_no_naive_clock.py`).

- [ ] **Step 6: Commit**

```bash
git add pipeline/screeners/breadth_metrics.py pipeline/screeners/run_all.py pipeline/tests/test_breadth_metrics.py
git commit -m "feat(breadth): run() on canonical store — guard, stale output, JSON history retired"
```

---

### Task 7: Backfill tool

**Files:**
- Create: `pipeline/tools/backfill_breadth.py`
- Test: `pipeline/tests/test_backfill_breadth.py`

**Interfaces:**
- Consumes: `breadth_store` (Task 3-5): `load_archive`, `derive`, `write_archive`,
  `BREADTH_COLUMNS`.
- Produces:
  - `compute_backfill_rows(closes: pd.DataFrame, spx: pd.Series) -> pd.DataFrame`
    — pure. `closes`: date-indexed (DatetimeIndex, ascending) wide frame of
    adjusted closes, one column per ticker. Returns one archive row per date with
    ≥ 200 prior sessions, `source='backfill'`, base columns only (derived columns
    left NA — `derive()` fills them after merge).
  - `merge_backfill(existing: pd.DataFrame, backfill: pd.DataFrame) -> pd.DataFrame`
    — pure. Existing (live) rows win on date collision.
  - CLI: `python3 -m pipeline.tools.backfill_breadth [--years 3] [--dry-run] [--csv PATH] [--cache PATH]`

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_backfill_breadth.py`:

```python
"""Tests for the one-time breadth backfill tool (pure functions only — no network)."""
import numpy as np
import pandas as pd
import pytest


def _make_closes(n_days=260, n_tickers=50, seed=7):
    """Random-walk closes, business-day index ending 2026-07-24."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end='2026-07-24', periods=n_days)
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, (n_days, n_tickers)), axis=0))
    return pd.DataFrame(prices, index=idx, columns=[f'S{i}' for i in range(n_tickers)])


class TestComputeBackfillRows:
    def test_only_dates_with_200_prior_sessions(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(260)
        spx = closes['S0']
        rows = compute_backfill_rows(closes, spx)
        assert len(rows) == 260 - 200
        assert (rows['source'] == 'backfill').all()

    def test_dates_are_iso_session_dates(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(210)
        rows = compute_backfill_rows(closes, closes['S0'])
        assert rows['date'].iloc[0] == closes.index[200].strftime('%Y-%m-%d')

    def test_counts_match_hand_computation_on_last_day(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(220)
        rows = compute_backfill_rows(closes, closes['S0'])
        last_date = closes.index[-1]
        chg = closes.loc[last_date] / closes.iloc[-2] - 1
        assert rows.iloc[-1]['up_4pct'] == int((chg >= 0.04).sum())
        assert rows.iloc[-1]['advances'] == int((chg > 0).sum())
        sma200 = closes.rolling(200).mean().loc[last_date]
        assert rows.iloc[-1]['pct_above_200sma'] == pytest.approx(
            float((closes.loc[last_date] > sma200).sum()) / closes.shape[1] * 100, abs=0.01)

    def test_new_highs_true_extremes(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        # Monotonically rising market: every scored day, every stock is at its 52w high
        idx = pd.bdate_range(end='2026-07-24', periods=210)
        closes = pd.DataFrame(
            {'A': np.linspace(100, 200, 210), 'B': np.linspace(50, 80, 210)}, index=idx)
        rows = compute_backfill_rows(closes, closes['A'])
        assert (rows['new_highs'] == 2).all()
        assert (rows['new_lows'] == 0).all()

    def test_universe_size_counts_non_nan(self):
        from pipeline.tools.backfill_breadth import compute_backfill_rows
        closes = _make_closes(210, n_tickers=10)
        closes.iloc[-1, 0] = np.nan  # one ticker missing on the last day
        rows = compute_backfill_rows(closes, closes['S1'])
        assert rows.iloc[-1]['universe_size'] == 9


class TestMergeBackfill:
    def test_live_wins_on_collision(self):
        from pipeline.tools.backfill_breadth import merge_backfill
        live = pd.DataFrame([{'date': '2026-07-24', 'source': 'live', 'advances': 999}])
        back = pd.DataFrame([
            {'date': '2026-07-23', 'source': 'backfill', 'advances': 1},
            {'date': '2026-07-24', 'source': 'backfill', 'advances': 2},
        ])
        merged = merge_backfill(live, back)
        assert len(merged) == 2
        row = merged[merged['date'] == '2026-07-24'].iloc[0]
        assert row['source'] == 'live' and row['advances'] == 999
        assert list(merged['date']) == ['2026-07-23', '2026-07-24']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_backfill_breadth.py -v`
Expected: FAIL with "No module named 'pipeline.tools.backfill_breadth'".

- [ ] **Step 3: Implement**

Create `pipeline/tools/backfill_breadth.py`:

```python
"""One-time breadth history backfill from raw OHLC.

Reconstructs ~2.2 years of daily breadth rows (source='backfill') by applying
TODAY'S universe membership to a 3-year adjusted-close download. This is
survivorship-biased and point-in-time-wrong by construction — reconstructed
days read slightly stronger than reality. The 'source' flag exists so downstream
consumers can tell reconstruction from measurement.

Dates come from the yfinance session index (US exchange dates) — never the host
clock. Not part of the daily cron; run manually:

    python3 -m pipeline.tools.backfill_breadth --dry-run
    python3 -m pipeline.tools.backfill_breadth
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.screeners.breadth_store import (
    BREADTH_COLUMNS, derive, load_archive, write_archive,
)

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_CSV = _REPO / 'data' / 'history' / 'breadth_archive.csv'
_UNIVERSE_JSON = _REPO / 'data' / 'output' / 'universe.json'
_MIN_PRIOR_SESSIONS = 200


def compute_backfill_rows(closes: pd.DataFrame, spx: pd.Series) -> pd.DataFrame:
    """Pure reconstruction: one archive row per date with >=200 prior sessions.

    closes: DatetimeIndex (ascending) x tickers, adjusted close.
    spx: date-indexed S&P 500 close (may be missing dates -> NaN spx_close).
    Derived columns are left NA; breadth_store.derive() fills them post-merge.
    """
    chg = closes / closes.shift(1) - 1
    p1m = closes / closes.shift(21) - 1
    p34 = closes / closes.shift(34) - 1
    p3m = closes / closes.shift(63) - 1
    sma20 = closes.rolling(20).mean()
    sma40 = closes.rolling(40).mean()
    sma50 = closes.rolling(50).mean()
    sma200 = closes.rolling(200).mean()
    hi252 = closes.rolling(252, min_periods=_MIN_PRIOR_SESSIONS).max()
    lo252 = closes.rolling(252, min_periods=_MIN_PRIOR_SESSIONS).min()

    rows = []
    for i in range(_MIN_PRIOR_SESSIONS, len(closes)):
        date = closes.index[i]
        c = closes.iloc[i]
        n = int(c.notna().sum())
        if n == 0:
            continue
        d_chg, d_1m, d_34, d_3m = chg.iloc[i], p1m.iloc[i], p34.iloc[i], p3m.iloc[i]
        adv = int((d_chg > 0).sum())
        dec = int((d_chg < 0).sum())
        spx_val = spx.get(date)
        rows.append({
            'date': date.strftime('%Y-%m-%d'),
            'source': 'backfill',
            'universe_size': n,
            'spx_close': float(spx_val) if pd.notna(spx_val) else None,
            'up_4pct': int((d_chg >= 0.04).sum()),
            'down_4pct': int((d_chg <= -0.04).sum()),
            'up_25pct_qtr': int((d_3m >= 0.25).sum()),
            'down_25pct_qtr': int((d_3m <= -0.25).sum()),
            'up_25pct_month': int((d_1m >= 0.25).sum()),
            'down_25pct_month': int((d_1m <= -0.25).sum()),
            'up_50pct_month': int((d_1m >= 0.50).sum()),
            'down_50pct_month': int((d_1m <= -0.50).sum()),
            'up_13pct_34d': int((d_34 >= 0.13).sum()),
            'down_13pct_34d': int((d_34 <= -0.13).sum()),
            't2108': round(float((c > sma40.iloc[i]).sum()) / n * 100, 2),
            'pct_above_200sma': round(float((c > sma200.iloc[i]).sum()) / n * 100, 2),
            'pct_above_50sma': round(float((c > sma50.iloc[i]).sum()) / n * 100, 2),
            'pct_above_20sma': round(float((c > sma20.iloc[i]).sum()) / n * 100, 2),
            'advances': adv,
            'declines': dec,
            'new_highs': int((c >= hi252.iloc[i] * (1 - 0.001)).sum()),
            'new_lows': int((c <= lo252.iloc[i] * (1 + 0.001)).sum()),
        })
    out = pd.DataFrame(rows)
    for col in BREADTH_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    return out[BREADTH_COLUMNS]


def merge_backfill(existing: pd.DataFrame, backfill: pd.DataFrame) -> pd.DataFrame:
    """Merge backfill under existing rows. Existing (live) rows win on collision."""
    add = backfill[~backfill['date'].isin(set(existing['date']))]
    merged = pd.concat([existing, add], ignore_index=True)
    return merged.sort_values('date').reset_index(drop=True)


# ── Network + CLI (not unit-tested; exercised by --dry-run) ──────────

def _load_tickers() -> list[str]:
    data = json.loads(_UNIVERSE_JSON.read_text(encoding='utf-8'))
    return sorted({r['ticker'] for r in data['rows'] if r.get('ticker')})


def _download_closes(tickers: list[str], years: int, cache: Path) -> pd.DataFrame:
    if cache.exists():
        logger.info("Using cached closes: %s", cache)
        return pd.read_parquet(cache)
    import yfinance as yf
    frames = []
    batch_size = 200
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        logger.info("Downloading batch %d-%d of %d", i, i + len(batch), len(tickers))
        data = yf.download(batch, period=f'{years}y', group_by='ticker',
                           auto_adjust=True, progress=False, threads=True)
        for t in batch:
            try:
                frames.append(data[t]['Close'].rename(t))
            except KeyError:
                logger.warning("No data for %s", t)
    closes = pd.concat(frames, axis=1).sort_index()
    closes.index = pd.DatetimeIndex(closes.index).tz_localize(None)
    cache.parent.mkdir(parents=True, exist_ok=True)
    closes.to_parquet(cache)
    return closes


def _download_spx(years: int) -> pd.Series:
    import yfinance as yf
    spx = yf.download('^GSPC', period=f'{years}y', auto_adjust=True, progress=False)
    close = spx['Close']
    if isinstance(close, pd.DataFrame):  # yfinance MultiIndex quirk
        close = close.iloc[:, 0]
    close.index = pd.DatetimeIndex(close.index).tz_localize(None)
    return close


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--years', type=int, default=3)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--csv', default=str(_DEFAULT_CSV))
    parser.add_argument('--cache', default=str(_REPO / 'data' / 'history' / 'backfill_closes.parquet'))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    tickers = _load_tickers()
    logger.info("Universe: %d tickers", len(tickers))
    closes = _download_closes(tickers, args.years, Path(args.cache))
    spx = _download_spx(args.years)

    backfill = compute_backfill_rows(closes, spx)
    existing = load_archive(args.csv)
    merged = derive(merge_backfill(existing, backfill))

    n_back = int((merged['source'] == 'backfill').sum())
    n_live = int((merged['source'] == 'live').sum())
    print(f"\nMerged archive: {len(merged)} rows "
          f"({n_back} backfill, {n_live} live), "
          f"{merged['date'].iloc[0]} .. {merged['date'].iloc[-1]}")
    print("\nNull rates:")
    print((merged.isna().mean().round(3)).to_string())
    print("\nMetric ranges (min..max):")
    for col in ['universe_size', 'up_4pct', 'down_4pct', 'pct_above_200sma',
                't2108', 'new_highs', 'new_lows', 'mcclellan_osc', 'ad_line']:
        vals = pd.to_numeric(merged[col], errors='coerce')
        print(f"  {col}: {vals.min():.1f} .. {vals.max():.1f}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0
    write_archive(merged, args.csv)
    print(f"\nWrote {args.csv}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

Also ensure `pipeline/tools/__init__.py` exists (create empty if missing).

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_backfill_breadth.py -v`
Expected: all PASS. (These exercise only the pure functions — no network.)

- [ ] **Step 5: Run the repo-wide clock test**

Run: `python3 -m pytest pipeline/tests/test_no_naive_clock.py -v`
Expected: PASS — the tool contains no `date.today()` / `datetime.now()`.

- [ ] **Step 6: Commit**

```bash
git add pipeline/tools/backfill_breadth.py pipeline/tests/test_backfill_breadth.py pipeline/tools/__init__.py
git commit -m "feat(breadth): one-time 3y backfill tool — marked rows, live-wins merge, dry-run"
```

---

### Task 8: TradingView cross-check helper (optional, ad-hoc)

**Files:**
- Create: `pipeline/tools/validate_breadth_tv.py`

**Interfaces:**
- Consumes: `breadth_store.load_archive`.
- Produces: CLI that prints our last-N-day `%>200/50/20` + T2108 as a compact
  table for manual comparison against TradingView symbols (S5TH, MMTH, etc.)
  read via the local TV MCP in a Claude session. No network, no TV API — this
  is deliberately just "our half" of the comparison.

- [ ] **Step 1: Implement (no unit test — read-only print helper)**

Create `pipeline/tools/validate_breadth_tv.py`:

```python
"""Print our breadth %>MA series for manual TradingView cross-checking.

Usage:  python3 -m pipeline.tools.validate_breadth_tv [--days 10] [--csv PATH]

Compare against TradingView symbols (read via the local TV MCP or the app):
  S5TH / MMTH  — % of S&P 500 / all stocks above 200-day MA
  S5FI / MMFI  — above 50-day
  S5TW / MMTW  — above 20-day

Levels WILL differ (different universes); direction and turning points should
agree. If direction disagrees for several days, investigate our pipeline first.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.screeners.breadth_store import load_archive

_DEFAULT_CSV = Path(__file__).resolve().parents[2] / 'data' / 'history' / 'breadth_archive.csv'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days', type=int, default=10)
    parser.add_argument('--csv', default=str(_DEFAULT_CSV))
    args = parser.parse_args(argv)

    frame = load_archive(args.csv).tail(args.days)
    print(f"{'date':<12}{'src':<10}{'%>200':>8}{'%>50':>8}{'%>20':>8}{'T2108':>8}")
    for _, r in frame.iterrows():
        print(f"{r['date']:<12}{r['source']:<10}"
              f"{float(r['pct_above_200sma']):>8.1f}{float(r['pct_above_50sma']):>8.1f}"
              f"{float(r['pct_above_20sma']):>8.1f}{float(r['t2108']):>8.1f}")
    print("\nCompare vs TV: S5TH/MMTH (200), S5FI/MMFI (50), S5TW/MMTW (20).")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
```

- [ ] **Step 2: Smoke-run against the real archive**

Run: `python3 -m pipeline.tools.validate_breadth_tv --days 5`
Expected: 5 rows printed from the real `data/history/breadth_archive.csv`, no traceback.

- [ ] **Step 3: Commit**

```bash
git add pipeline/tools/validate_breadth_tv.py
git commit -m "feat(breadth): TV cross-check print helper (manual, out of critical path)"
```

---

### Task 9: End-to-end verification + real backfill (network)

**Files:**
- Modify (data only): `data/history/breadth_archive.csv`, `data/output/breadth.json`

- [ ] **Step 1: Full test suite**

Run: `python3 -m pytest pipeline/tests/ -v`
Expected: all PASS.

- [ ] **Step 2: Backfill dry-run (network, ~20-40 min first run, then cached)**

```bash
python3 -m pipeline.tools.backfill_breadth --dry-run
```

Inspect the printed summary. Sanity gates before proceeding:
- date range starts ~2024-07 and ends at the last completed US session
- `universe_size` for backfill rows within ~2500-3100
- `pct_above_200sma` never < 5 or > 98
- `new_highs`/`new_lows` in the tens-to-low-hundreds, not thousands
- `mcclellan_osc` roughly within ±150

If any gate fails, STOP and investigate before writing.

- [ ] **Step 3: Real backfill write**

```bash
python3 -m pipeline.tools.backfill_breadth
```

Then verify the poisoned row is gone and the merge is sane:

```bash
python3 - <<'EOF'
import pandas as pd
f = pd.read_csv('data/history/breadth_archive.csv')
assert f['date'].is_unique, "duplicate dates!"
dup26 = f[f['date'] == '2026-07-26']
assert len(dup26) == 1 and float(dup26['t2108'].iloc[0]) == 45.1, "poisoned row survived!"
print(f['source'].value_counts().to_string())
print(f"{f['date'].iloc[0]} .. {f['date'].iloc[-1]}  ({len(f)} rows)")
EOF
```

- [ ] **Step 4: Regenerate breadth.json through the real `run()` path**

Run the pipeline's breadth step (or full pipeline) locally, then confirm the
frontend contract:

```bash
python3 - <<'EOF'
import json
d = json.load(open('data/output/breadth.json'))
assert d['data_quality']['stale'] in (True, False)
assert 'up_13pct_34d' in d['mm']
assert len(d['history']['rows']) <= 100
assert all('source' in r for r in d['history']['rows'])
# legacy keys the React components read:
for k in ['up_4pct', 'ratio_5d']: assert k in d['mm']
for k in ['t2108', 'ad_line', 'mcclellan_osc']: assert k in d['breadth']
print("breadth.json contract OK")
EOF
```

Note: if run outside market hours the guard may reject on stale universe data —
that's the guard working; verify with the archive from Step 3 instead.

- [ ] **Step 5: Cross-check vs TradingView (manual)**

Run `python3 -m pipeline.tools.validate_breadth_tv --days 10`, read S5TH/MMTH
via the TV MCP in-session, confirm direction/turning points agree.

- [ ] **Step 6: Commit the data**

```bash
git add data/history/breadth_archive.csv data/output/breadth.json
git commit -m "data(breadth): 3y marked backfill + regenerated breadth.json"
```

Do NOT commit `data/history/backfill_closes.parquet` (download cache — add to
`.gitignore` if git status shows it):

```bash
echo 'data/history/backfill_closes.parquet' >> .gitignore
git add .gitignore && git commit -m "chore: ignore backfill download cache"
```
