# Ticker Event Archive + Signal Timelines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mine five months of committed screener JSONs into a `(date, ticker, screener)` event archive, score which stocks are heating up now, and surface both a ranked list and a per-ticker signal timeline interleaved with the user's own fills.

**Architecture:** A pure extractor turns any daily screener JSON into event rows; a one-time git-mining backfill replays 88 commits through it; `run_all` appends daily. A pure `compute_heat()` scores distinct-screener confluence over a rolling window. Two derived JSONs feed a Screener-page ranked list and a new ticker-page timeline section. Spec: `docs/plans/2026-07-31-ticker-events-design.md`.

**Tech Stack:** Python 3.11+/pandas/pytest · React 19 · Tailwind 4

## Global Constraints

- Extractor, heat scoring, and archive helpers are **pure**: no I/O, no clock, no reads outside their arguments. Malformed input yields zero rows, never an exception.
- No `date.today()` / `datetime.now()` in engine code (repo guard `tests/test_no_naive_clock.py`). Event dates come from the committed data / git commit date, never the host clock.
- **No-peek:** `compute_heat(events, as_of)` must ignore rows dated after `as_of`.
- New pipeline outputs must not break existing ones: the daily-append and JSON writes live in their own `try/except` so a failure here never affects other screener outputs (the pattern `run_all.py` already uses for breadth).
- `ticker_events.json` is capped to the trailing **6 months**; heat window is **15** trading sessions. Both are single named constants.
- Screener weights live in ONE `WEIGHTS` dict; nothing else hardcodes them.
- Anti-dopamine palette: existing CSS vars only (`--color-profit`, `--color-loss`, `--color-signal-caution`, `--color-surface`, `--color-border`, `--color-text*`, `--color-hover-bg`, `--color-bg`).
- No JS test harness exists — do not add one; frontend verified in-browser (Task 8).
- Python tests: `python3 -m pytest` from repo root. Known baseline: 4 pre-existing failures in `pipeline/tests/test_content_processor.py` — ignore.

---

### Task 1: Event extractor

**Files:**
- Create: `pipeline/screeners/ticker_events.py`
- Create: `pipeline/tests/test_ticker_events.py`

**Interfaces:**
- Produces:
  - `EVENT_COLUMNS: list[str]` — exactly
    `['date','ticker','screener','group','change_pct','rel_volume','volume','sector','atr_ext','num_contractions','pct_to_pivot']`
  - `SCREENER_FILES: dict[str, str]` — screener name → container key:
    `{'gainers_4pct':'tickers','vol_up_gainers':'tickers','episodic_pivot':'tickers','vcp':'results','momentum_97':'buckets','healthy_charts':'rs_groups','ema21_watch':'rs_groups'}`
  - `extract_events(screener: str, payload: dict, date_iso: str) -> list[dict]` —
    pure. Handles all three container shapes: flat list under `tickers` or
    `results` (group `''`), and nested `{group: [rows]}` under `buckets` or
    `rs_groups` (group = the key, e.g. `'97'`). Each output dict has every key
    in `EVENT_COLUMNS`; missing metrics are `None`. Rows without a `ticker`
    string are skipped. A payload of the wrong shape yields `[]`.

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_ticker_events.py`:

```python
"""Tests for the ticker event archive."""
import pytest


class TestExtractEvents:
    def test_flat_tickers_shape(self):
        from pipeline.screeners.ticker_events import extract_events, EVENT_COLUMNS
        payload = {'count': 2, 'tickers': [
            {'ticker': 'ABC', 'change_pct': 0.062, 'volume': 1_200_000,
             'sector': 'Technology', 'atr_ext': 1.4},
            {'ticker': 'XYZ', 'change_pct': 0.041, 'volume': 900_000,
             'sector': 'Energy', 'atr_ext': 0.9},
        ]}
        rows = extract_events('gainers_4pct', payload, '2026-05-04')
        assert len(rows) == 2
        assert set(rows[0]) == set(EVENT_COLUMNS)
        assert rows[0]['date'] == '2026-05-04'
        assert rows[0]['ticker'] == 'ABC'
        assert rows[0]['screener'] == 'gainers_4pct'
        assert rows[0]['group'] == ''
        assert rows[0]['change_pct'] == 0.062
        assert rows[0]['num_contractions'] is None

    def test_results_shape_vcp(self):
        from pipeline.screeners.ticker_events import extract_events
        payload = {'count': 1, 'results': [
            {'ticker': 'DEF', 'num_contractions': 3, 'pct_to_pivot': 0.021,
             'atr_ext': 0.5},
        ]}
        rows = extract_events('vcp', payload, '2026-05-04')
        assert len(rows) == 1
        assert rows[0]['screener'] == 'vcp'
        assert rows[0]['num_contractions'] == 3
        assert rows[0]['pct_to_pivot'] == 0.021
        assert rows[0]['change_pct'] is None

    def test_nested_buckets_carry_group(self):
        from pipeline.screeners.ticker_events import extract_events
        payload = {'count': 3, 'buckets': {
            '100': [{'ticker': 'AAA', 'change_pct': 0.01}],
            '97': [{'ticker': 'BBB'}, {'ticker': 'CCC'}],
        }}
        rows = extract_events('momentum_97', payload, '2026-05-04')
        assert len(rows) == 3
        by_ticker = {r['ticker']: r for r in rows}
        assert by_ticker['AAA']['group'] == '100'
        assert by_ticker['BBB']['group'] == '97'
        assert all(r['screener'] == 'momentum_97' for r in rows)

    def test_nested_rs_groups(self):
        from pipeline.screeners.ticker_events import extract_events
        payload = {'count': 1, 'rs_groups': {'90': [{'ticker': 'GHI'}]}}
        rows = extract_events('ema21_watch', payload, '2026-05-04')
        assert len(rows) == 1 and rows[0]['group'] == '90'

    def test_plain_string_entries_supported(self):
        """Some screeners may store bare symbols rather than dicts."""
        from pipeline.screeners.ticker_events import extract_events
        payload = {'tickers': ['JKL', 'MNO']}
        rows = extract_events('episodic_pivot', payload, '2026-05-04')
        assert [r['ticker'] for r in rows] == ['JKL', 'MNO']
        assert rows[0]['change_pct'] is None

    def test_empty_and_malformed_yield_no_rows(self):
        from pipeline.screeners.ticker_events import extract_events
        assert extract_events('gainers_4pct', {'count': 0, 'tickers': []}, '2026-05-04') == []
        assert extract_events('gainers_4pct', {}, '2026-05-04') == []
        assert extract_events('gainers_4pct', {'tickers': 'not-a-list'}, '2026-05-04') == []
        assert extract_events('vcp', {'results': [{'no_ticker': 1}]}, '2026-05-04') == []
        assert extract_events('unknown_screener', {'tickers': [{'ticker': 'A'}]}, '2026-05-04') == []

    def test_screener_files_covers_all_seven(self):
        from pipeline.screeners.ticker_events import SCREENER_FILES
        assert set(SCREENER_FILES) == {
            'gainers_4pct', 'vol_up_gainers', 'episodic_pivot', 'vcp',
            'momentum_97', 'healthy_charts', 'ema21_watch'}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_ticker_events.py -v`
Expected: FAIL with "No module named 'pipeline.screeners.ticker_events'".

- [ ] **Step 3: Implement**

Create `pipeline/screeners/ticker_events.py`:

```python
"""Ticker event archive — which stocks appeared on which screener, when.

The daily cron commits every screener's JSON, so git history is a
point-in-time record of screener membership. This module turns any one of
those payloads into flat event rows; the backfill tool replays history
through it and run_all appends today's.

Pure functions only: no I/O, no clock. Malformed input yields zero rows.
Spec: docs/plans/2026-07-31-ticker-events-design.md
"""

from __future__ import annotations

from typing import Any, Dict, List

EVENT_COLUMNS: List[str] = [
    'date', 'ticker', 'screener', 'group',
    'change_pct', 'rel_volume', 'volume', 'sector', 'atr_ext',
    'num_contractions', 'pct_to_pivot',
]

# screener name -> the key holding its rows. 'buckets'/'rs_groups' are nested
# {group: [rows]}; 'tickers'/'results' are flat lists.
SCREENER_FILES: Dict[str, str] = {
    'gainers_4pct': 'tickers',
    'vol_up_gainers': 'tickers',
    'episodic_pivot': 'tickers',
    'vcp': 'results',
    'momentum_97': 'buckets',
    'healthy_charts': 'rs_groups',
    'ema21_watch': 'rs_groups',
}

_NESTED_KEYS = {'buckets', 'rs_groups'}
_METRICS = ['change_pct', 'rel_volume', 'volume', 'sector', 'atr_ext',
            'num_contractions', 'pct_to_pivot']


def _row(entry: Any, screener: str, group: str, date_iso: str) -> Dict[str, Any] | None:
    """One event row from one screener entry (dict or bare symbol)."""
    if isinstance(entry, str):
        ticker, metrics = entry, {}
    elif isinstance(entry, dict):
        ticker, metrics = entry.get('ticker'), entry
    else:
        return None
    if not isinstance(ticker, str) or not ticker:
        return None
    row = {'date': date_iso, 'ticker': ticker, 'screener': screener, 'group': group}
    for key in _METRICS:
        row[key] = metrics.get(key)
    return row


def extract_events(screener: str, payload: Dict[str, Any], date_iso: str) -> List[Dict[str, Any]]:
    """Flat event rows for one screener's daily payload. Pure and total."""
    container = SCREENER_FILES.get(screener)
    if container is None or not isinstance(payload, dict):
        return []
    blob = payload.get(container)
    rows: List[Dict[str, Any]] = []

    if container in _NESTED_KEYS:
        if not isinstance(blob, dict):
            return []
        for group, entries in blob.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                row = _row(entry, screener, str(group), date_iso)
                if row is not None:
                    rows.append(row)
        return rows

    if not isinstance(blob, list):
        return []
    for entry in blob:
        row = _row(entry, screener, '', date_iso)
        if row is not None:
            rows.append(row)
    return rows
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_ticker_events.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/ticker_events.py pipeline/tests/test_ticker_events.py
git commit -m "feat(events): pure screener-payload event extractor"
```

---

### Task 2: Archive store — load, upsert-day, atomic write

**Files:**
- Modify: `pipeline/screeners/ticker_events.py`
- Test: `pipeline/tests/test_ticker_events.py`

**Interfaces:**
- Consumes: `EVENT_COLUMNS` (Task 1).
- Produces:
  - `class EventArchiveError(RuntimeError)`
  - `load_events(csv_path: str) -> pd.DataFrame` — sorted by
    `(date, ticker, screener)`, missing columns added as NA, empty frame with
    `EVENT_COLUMNS` when the file is absent, **raises `EventArchiveError`** when
    the file exists but is unparseable or lacks a `date` column.
  - `upsert_day(frame: pd.DataFrame, rows: list[dict]) -> pd.DataFrame` —
    replaces **all** rows for the dates present in `rows` (idempotent re-runs),
    appends the new ones, returns a sorted copy. Empty `rows` returns the frame
    unchanged.
  - `write_events(frame: pd.DataFrame, csv_path: str) -> None` — atomic
    (`tempfile.mkstemp` in the same dir + `os.replace`), columns in
    `EVENT_COLUMNS` order, mode `0o644`, temp file removed on failure.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_ticker_events.py`:

```python
import pandas as pd


def _rows(date, *specs):
    """specs: (ticker, screener) pairs -> minimal event rows."""
    from pipeline.screeners.ticker_events import EVENT_COLUMNS
    out = []
    for ticker, screener in specs:
        row = {c: None for c in EVENT_COLUMNS}
        row.update({'date': date, 'ticker': ticker, 'screener': screener, 'group': ''})
        out.append(row)
    return out


class TestArchiveStore:
    def test_missing_file_returns_empty_frame(self, tmp_path):
        from pipeline.screeners.ticker_events import load_events, EVENT_COLUMNS
        frame = load_events(str(tmp_path / 'nope.csv'))
        assert list(frame.columns) == EVENT_COLUMNS and len(frame) == 0

    def test_upsert_replaces_whole_day(self, tmp_path):
        from pipeline.screeners.ticker_events import load_events, upsert_day
        frame = load_events(str(tmp_path / 'a.csv'))
        frame = upsert_day(frame, _rows('2026-05-04', ('ABC', 'vcp'), ('XYZ', 'vcp')))
        assert len(frame) == 2
        # Re-running the same day with fewer rows replaces, never accumulates
        frame = upsert_day(frame, _rows('2026-05-04', ('ABC', 'vcp')))
        assert len(frame) == 1
        frame = upsert_day(frame, _rows('2026-05-05', ('QQQ', 'gainers_4pct')))
        assert len(frame) == 2
        assert list(frame['date']) == ['2026-05-04', '2026-05-05']

    def test_upsert_empty_rows_is_noop(self, tmp_path):
        from pipeline.screeners.ticker_events import load_events, upsert_day
        frame = upsert_day(load_events(str(tmp_path / 'a.csv')),
                           _rows('2026-05-04', ('ABC', 'vcp')))
        assert len(upsert_day(frame, [])) == 1

    def test_write_then_load_roundtrip_and_mode(self, tmp_path):
        import os
        import stat
        from pipeline.screeners.ticker_events import load_events, upsert_day, write_events
        p = str(tmp_path / 'events.csv')
        frame = upsert_day(load_events(p), _rows('2026-05-04', ('ABC', 'vcp')))
        write_events(frame, p)
        again = load_events(p)
        assert len(again) == 1 and again.iloc[0]['ticker'] == 'ABC'
        assert stat.S_IMODE(os.stat(p).st_mode) == 0o644
        assert [f for f in tmp_path.iterdir() if f.name != 'events.csv'] == []

    def test_sorted_by_date_ticker_screener(self, tmp_path):
        from pipeline.screeners.ticker_events import load_events, upsert_day
        frame = upsert_day(load_events(str(tmp_path / 'a.csv')),
                           _rows('2026-05-04', ('ZZZ', 'vcp'), ('AAA', 'vcp'), ('AAA', 'gainers_4pct')))
        assert list(frame['ticker']) == ['AAA', 'AAA', 'ZZZ']
        assert list(frame['screener'])[:2] == ['gainers_4pct', 'vcp']

    def test_corrupt_file_raises(self, tmp_path):
        from pipeline.screeners.ticker_events import load_events, EventArchiveError
        p = tmp_path / 'events.csv'
        p.write_text('\x00\x01 not a csv')
        with pytest.raises(EventArchiveError):
            load_events(str(p))

    def test_missing_date_column_raises(self, tmp_path):
        from pipeline.screeners.ticker_events import load_events, EventArchiveError
        p = tmp_path / 'events.csv'
        p.write_text('ticker,screener\nABC,vcp\n')
        with pytest.raises(EventArchiveError):
            load_events(str(p))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_ticker_events.py::TestArchiveStore -v`
Expected: FAIL with import errors for `load_events` / `upsert_day` / `write_events`.

- [ ] **Step 3: Implement**

Add to the imports at the top of `pipeline/screeners/ticker_events.py`:

```python
import logging
import os
import tempfile
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
```

Append to the module:

```python
class EventArchiveError(RuntimeError):
    """The archive exists but cannot be read. Never silently reset it."""


def load_events(csv_path: str) -> pd.DataFrame:
    """Load the canonical event archive; add missing columns; sort."""
    path = Path(csv_path)
    if not path.exists():
        logger.info("No ticker event archive at %s — starting empty", csv_path)
        return pd.DataFrame(columns=EVENT_COLUMNS)
    try:
        frame = pd.read_csv(path, dtype={'date': str, 'ticker': str,
                                         'screener': str, 'group': str})
    except Exception as exc:  # noqa: BLE001 — any parse failure is fatal
        raise EventArchiveError(f"Cannot read ticker events {csv_path}: {exc}") from exc
    if 'date' not in frame.columns:
        raise EventArchiveError(f"Ticker events {csv_path} has no 'date' column")
    for col in EVENT_COLUMNS:
        if col not in frame.columns:
            frame[col] = pd.NA
    frame['group'] = frame['group'].fillna('')
    frame = frame.sort_values(['date', 'ticker', 'screener']).reset_index(drop=True)
    return frame[EVENT_COLUMNS]


def upsert_day(frame: pd.DataFrame, rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """Replace every row for the dates present in `rows`. Returns a sorted copy."""
    if not rows:
        return frame
    dates = {r['date'] for r in rows}
    kept = frame[~frame['date'].isin(dates)]
    new = pd.DataFrame([{c: r.get(c) for c in EVENT_COLUMNS} for r in rows])
    out = pd.concat([kept, new], ignore_index=True)
    return out.sort_values(['date', 'ticker', 'screener']).reset_index(drop=True)


def write_events(frame: pd.DataFrame, csv_path: str) -> None:
    """Atomically write the archive: temp file in the same dir, then rename."""
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frame[EVENT_COLUMNS]
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix='.csv.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            out.to_csv(f, index=False)
        os.replace(tmp_name, path)
        os.chmod(path, 0o644)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    logger.info("Wrote ticker events (%d rows) to %s", len(out), csv_path)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_ticker_events.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/ticker_events.py pipeline/tests/test_ticker_events.py
git commit -m "feat(events): canonical event archive — load, day upsert, atomic write"
```

---

### Task 3: Heat scoring

**Files:**
- Create: `pipeline/screeners/ticker_heat.py`
- Create: `pipeline/tests/test_ticker_heat.py`

**Interfaces:**
- Consumes: an events frame shaped like `load_events()` output.
- Produces:
  - `WEIGHTS: dict[str, int]` — the ONLY place weights live:
    quality ×3 `episodic_pivot`, `vcp`, `momentum_97`; participation ×1
    `gainers_4pct`, `vol_up_gainers`, `ema21_watch`, `healthy_charts`.
  - `HEAT_WINDOW: int = 15`, `REPEAT_FACTOR: float = 0.25`
  - `compute_heat(events: pd.DataFrame, as_of: str, window: int = HEAT_WINDOW) -> list[dict]`
    — pure, no clock, ignores rows dated after `as_of`. Window = the last
    `window` **distinct dates present in the archive** at or before `as_of`.
    Per ticker in that window:
    `score = Σ_screener weight × (1 + REPEAT_FACTOR × (hits − 1))`, rounded 2dp.
    Returns dicts `{ticker, score, screeners:[{name, hits, last_date}],
    first_seen, last_seen, days_span, sector}` sorted by score desc then
    ticker asc. `days_span` = count of distinct archive dates from
    `first_seen` to `last_seen` inclusive. `sector` = the most recent non-null
    sector seen for that ticker in the window, else `None`.

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_ticker_heat.py`:

```python
"""Tests for heat scoring — which tickers are stacking signals."""
import pandas as pd
import pytest

from pipeline.screeners.ticker_events import EVENT_COLUMNS


def _ev(date, ticker, screener, **kw):
    row = {c: None for c in EVENT_COLUMNS}
    row.update({'date': date, 'ticker': ticker, 'screener': screener, 'group': ''})
    row.update(kw)
    return row


def _frame(rows):
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


class TestComputeHeat:
    def test_distinct_screeners_beat_repeats(self):
        """A 5x gainers_4pct name must rank below vcp + episodic_pivot."""
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev(f'2026-05-{d:02d}', 'NOISY', 'gainers_4pct') for d in range(1, 6)]
        rows += [_ev('2026-05-04', 'QUIET', 'vcp'),
                 _ev('2026-05-05', 'QUIET', 'episodic_pivot')]
        heat = compute_heat(_frame(rows), '2026-05-05')
        assert [h['ticker'] for h in heat] == ['QUIET', 'NOISY']
        quiet = heat[0]
        assert quiet['score'] == pytest.approx(6.0)      # 3 + 3, no repeats
        noisy = heat[1]
        assert noisy['score'] == pytest.approx(1 + 0.25 * 4)   # 1 * (1 + .25*4) = 2.0

    def test_score_shape_and_fields(self):
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev('2026-05-01', 'ABC', 'vcp', sector='Technology'),
                _ev('2026-05-03', 'ABC', 'gainers_4pct', sector='Technology'),
                _ev('2026-05-05', 'ABC', 'vcp', sector=None)]
        heat = compute_heat(_frame(rows), '2026-05-05')
        assert len(heat) == 1
        h = heat[0]
        assert set(h) == {'ticker', 'score', 'screeners', 'first_seen',
                          'last_seen', 'days_span', 'sector'}
        assert h['first_seen'] == '2026-05-01' and h['last_seen'] == '2026-05-05'
        assert h['days_span'] == 3          # 3 distinct archive dates in range
        assert h['sector'] == 'Technology'  # most recent non-null
        names = {s['name']: s for s in h['screeners']}
        assert names['vcp']['hits'] == 2 and names['vcp']['last_date'] == '2026-05-05'
        # vcp: 3*(1+.25*1)=3.75, gainers_4pct: 1 -> 4.75
        assert h['score'] == pytest.approx(4.75)

    def test_no_peek_ignores_rows_after_as_of(self):
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev('2026-05-01', 'ABC', 'vcp'),
                _ev('2026-05-09', 'ABC', 'episodic_pivot'),
                _ev('2026-05-09', 'FUTURE', 'vcp')]
        heat = compute_heat(_frame(rows), '2026-05-01')
        assert [h['ticker'] for h in heat] == ['ABC']
        assert heat[0]['score'] == pytest.approx(3.0)

    def test_window_counts_archive_dates_not_calendar_days(self):
        from pipeline.screeners.ticker_heat import compute_heat
        dates = [f'2026-05-{d:02d}' for d in range(1, 21)]   # 20 archive dates
        rows = [_ev(d, 'ABC', 'gainers_4pct') for d in dates]
        rows.append(_ev(dates[0], 'OLD', 'vcp'))             # falls out of a 15-window
        heat = compute_heat(_frame(rows), dates[-1], window=15)
        assert [h['ticker'] for h in heat] == ['ABC']

    def test_unknown_screener_ignored(self):
        from pipeline.screeners.ticker_heat import compute_heat
        heat = compute_heat(_frame([_ev('2026-05-01', 'ABC', 'not_a_screener')]),
                            '2026-05-01')
        assert heat == []

    def test_empty_inputs(self):
        from pipeline.screeners.ticker_heat import compute_heat
        assert compute_heat(_frame([]), '2026-05-01') == []
        assert compute_heat(_frame([_ev('2026-05-01', 'ABC', 'vcp')]), '2020-01-01') == []

    def test_ties_break_on_ticker(self):
        from pipeline.screeners.ticker_heat import compute_heat
        rows = [_ev('2026-05-01', 'BBB', 'vcp'), _ev('2026-05-01', 'AAA', 'vcp')]
        heat = compute_heat(_frame(rows), '2026-05-01')
        assert [h['ticker'] for h in heat] == ['AAA', 'BBB']

    def test_weights_single_source(self):
        from pipeline.screeners.ticker_heat import WEIGHTS
        assert WEIGHTS['vcp'] == 3 and WEIGHTS['episodic_pivot'] == 3
        assert WEIGHTS['momentum_97'] == 3 and WEIGHTS['gainers_4pct'] == 1
        assert len(WEIGHTS) == 7
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_ticker_heat.py -v`
Expected: FAIL with "No module named 'pipeline.screeners.ticker_heat'".

- [ ] **Step 3: Implement**

Create `pipeline/screeners/ticker_heat.py`:

```python
"""Heat scoring — which tickers are stacking signals right now.

Confluence over repetition: distinct screeners carry their full weight,
repeat hits on the same screener add a fraction. Setup-quality screeners
outweigh participation ones. Pure and no-peek: rows after `as_of` are
invisible. Spec: docs/plans/2026-07-31-ticker-events-design.md
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
            score += weight * (1 + REPEAT_FACTOR * (hits - 1))
            screeners.append({'name': name, 'hits': int(hits),
                              'last_date': str(sub['date'].max())})
        first_seen, last_seen = str(grp['date'].min()), str(grp['date'].max())
        span = date_index[last_seen] - date_index[first_seen] + 1
        sectors = grp.sort_values('date')['sector'].dropna()
        out.append({
            'ticker': str(ticker),
            'score': round(score, 2),
            'screeners': sorted(screeners, key=lambda s: -WEIGHTS[s['name']]),
            'first_seen': first_seen,
            'last_seen': last_seen,
            'days_span': int(span),
            'sector': str(sectors.iloc[-1]) if len(sectors) else None,
        })

    out.sort(key=lambda h: (-h['score'], h['ticker']))
    return out
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_ticker_heat.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/ticker_heat.py pipeline/tests/test_ticker_heat.py
git commit -m "feat(events): heat scoring — weighted distinct-screener confluence"
```

---

### Task 4: Output builders

**Files:**
- Modify: `pipeline/screeners/ticker_heat.py`
- Test: `pipeline/tests/test_ticker_heat.py`

**Interfaces:**
- Consumes: `compute_heat`.
- Produces:
  - `HEATING_UP_LIMIT: int = 50`, `EVENTS_JSON_MONTHS: int = 6`
  - `build_heating_up(events, as_of) -> dict` → `{'as_of': as_of, 'rows': [...]}`
    (top `HEATING_UP_LIMIT` from `compute_heat`).
  - `build_ticker_events_index(events, as_of, months=EVENTS_JSON_MONTHS) -> dict`
    → `{'as_of': as_of, 'events': {TICKER: [{date, screener, group, change_pct,
    rel_volume, volume, atr_ext, num_contractions, pct_to_pivot}, ...]}}`,
    rows dated after `as_of` excluded, limited to the trailing `months` calendar
    months before `as_of`, each ticker's list newest-first, NaN → None.

- [ ] **Step 1: Write the failing tests**

Append to `pipeline/tests/test_ticker_heat.py`:

```python
class TestBuilders:
    def test_heating_up_caps_and_orders(self):
        from pipeline.screeners.ticker_heat import build_heating_up, HEATING_UP_LIMIT
        rows = []
        for i in range(60):
            rows.append(_ev('2026-05-01', f'T{i:03d}', 'vcp'))
            if i < 10:                      # ten names get a second screener
                rows.append(_ev('2026-05-02', f'T{i:03d}', 'episodic_pivot'))
        out = build_heating_up(_frame(rows), '2026-05-02')
        assert out['as_of'] == '2026-05-02'
        assert len(out['rows']) == HEATING_UP_LIMIT
        assert [r['ticker'] for r in out['rows'][:3]] == ['T000', 'T001', 'T002']
        assert out['rows'][0]['score'] > out['rows'][-1]['score']

    def test_index_groups_by_ticker_newest_first(self):
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2026-05-01', 'ABC', 'vcp', num_contractions=3),
                _ev('2026-05-05', 'ABC', 'gainers_4pct', change_pct=0.06),
                _ev('2026-05-05', 'XYZ', 'vcp')]
        out = build_ticker_events_index(_frame(rows), '2026-05-05')
        assert set(out['events']) == {'ABC', 'XYZ'}
        abc = out['events']['ABC']
        assert [e['date'] for e in abc] == ['2026-05-05', '2026-05-01']
        assert abc[0]['screener'] == 'gainers_4pct'
        assert abc[0]['change_pct'] == 0.06
        assert abc[1]['num_contractions'] == 3
        assert 'ticker' not in abc[0]     # implied by the key

    def test_index_excludes_future_and_old_rows(self):
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2025-01-05', 'OLD', 'vcp'),
                _ev('2026-05-01', 'ABC', 'vcp'),
                _ev('2026-06-01', 'FUTURE', 'vcp')]
        out = build_ticker_events_index(_frame(rows), '2026-05-05', months=6)
        assert set(out['events']) == {'ABC'}

    def test_index_is_json_safe(self):
        import json
        import numpy as np
        from pipeline.screeners.ticker_heat import build_ticker_events_index
        rows = [_ev('2026-05-01', 'ABC', 'vcp', change_pct=np.nan)]
        out = build_ticker_events_index(_frame(rows), '2026-05-01')
        assert out['events']['ABC'][0]['change_pct'] is None
        json.dumps(out)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_ticker_heat.py::TestBuilders -v`
Expected: FAIL with import errors for `build_heating_up` / `build_ticker_events_index`.

- [ ] **Step 3: Implement**

Append to `pipeline/screeners/ticker_heat.py`:

```python
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
            {k: (None if pd.isna(r[k]) else r[k]) for k in _INDEX_FIELDS}
            for _, r in grp.iterrows()
        ]
    return {'as_of': as_of, 'events': out}
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_ticker_heat.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/screeners/ticker_heat.py pipeline/tests/test_ticker_heat.py
git commit -m "feat(events): heating-up and per-ticker index builders"
```

---

### Task 5: Git-mining backfill tool

**Files:**
- Create: `pipeline/tools/backfill_ticker_events.py`
- Create: `pipeline/tests/test_backfill_ticker_events.py`

**Interfaces:**
- Consumes: `extract_events`, `SCREENER_FILES`, `load_events`, `upsert_day`, `write_events`.
- Produces:
  - `snapshot_dates(git_log_output: str) -> list[tuple[str, str]]` — pure; parses
    `"<sha> <YYYY-MM-DD>"` lines into `[(sha, date)]`, newest-first input →
    oldest-first output, one entry per date (keep the **last** commit for a
    date, i.e. that day's final state).
  - `rows_from_snapshot(payloads: dict[str, dict], date_iso: str) -> list[dict]`
    — pure; runs `extract_events` for each `{screener: payload}` and concatenates.
  - `summarize(rows) -> dict` — pure; `{'total': int, 'by_screener': {...},
    'by_month': {...}, 'tickers': int}` for the dry-run report.
  - CLI: `python3 -m pipeline.tools.backfill_ticker_events [--dry-run] [--csv PATH]`

- [ ] **Step 1: Write the failing tests**

Create `pipeline/tests/test_backfill_ticker_events.py`:

```python
"""Tests for the ticker-event git backfill (pure functions only — no git calls)."""
import pytest


class TestSnapshotDates:
    def test_parses_and_orders_oldest_first(self):
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "ccc 2026-05-06\nbbb 2026-05-05\naaa 2026-05-04\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04'), ('bbb', '2026-05-05'),
                                       ('ccc', '2026-05-06')]

    def test_one_commit_per_date_keeps_last_of_day(self):
        """git log is newest-first, so the FIRST line for a date is that day's final state."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "late 2026-05-05\nearly 2026-05-05\naaa 2026-05-04\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04'), ('late', '2026-05-05')]

    def test_ignores_blank_and_malformed_lines(self):
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "\naaa 2026-05-04\ngarbage\n\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04')]


class TestRowsFromSnapshot:
    def test_concatenates_all_screeners(self):
        from pipeline.tools.backfill_ticker_events import rows_from_snapshot
        payloads = {
            'gainers_4pct': {'tickers': [{'ticker': 'ABC', 'change_pct': 0.05}]},
            'vcp': {'results': [{'ticker': 'DEF', 'num_contractions': 2}]},
            'momentum_97': {'buckets': {'97': [{'ticker': 'GHI'}]}},
        }
        rows = rows_from_snapshot(payloads, '2026-05-04')
        assert len(rows) == 3
        assert {r['screener'] for r in rows} == {'gainers_4pct', 'vcp', 'momentum_97'}
        assert all(r['date'] == '2026-05-04' for r in rows)

    def test_missing_payload_is_skipped(self):
        from pipeline.tools.backfill_ticker_events import rows_from_snapshot
        rows = rows_from_snapshot({'vcp': None, 'gainers_4pct': {'tickers': []}}, '2026-05-04')
        assert rows == []


class TestSummarize:
    def test_counts(self):
        from pipeline.tools.backfill_ticker_events import summarize
        rows = [
            {'date': '2026-05-04', 'ticker': 'ABC', 'screener': 'vcp'},
            {'date': '2026-05-04', 'ticker': 'DEF', 'screener': 'vcp'},
            {'date': '2026-06-02', 'ticker': 'ABC', 'screener': 'gainers_4pct'},
        ]
        s = summarize(rows)
        assert s['total'] == 3
        assert s['by_screener'] == {'vcp': 2, 'gainers_4pct': 1}
        assert s['by_month'] == {'2026-05': 2, '2026-06': 1}
        assert s['tickers'] == 2

    def test_empty(self):
        from pipeline.tools.backfill_ticker_events import summarize
        assert summarize([]) == {'total': 0, 'by_screener': {}, 'by_month': {}, 'tickers': 0}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest pipeline/tests/test_backfill_ticker_events.py -v`
Expected: FAIL with "No module named 'pipeline.tools.backfill_ticker_events'".

- [ ] **Step 3: Implement**

Create `pipeline/tools/backfill_ticker_events.py`:

```python
"""One-time backfill of the ticker event archive from git history.

The daily cron commits every screener JSON, so `git show <sha>:<path>` recovers
exactly what each screener said on each past trading day. This tool replays
those snapshots through the same extractor the daily append uses.

Dates come from the git commit date (the cron commits the session it just
processed) — never the host clock. Not part of the cron; run manually:

    python3 -m pipeline.tools.backfill_ticker_events --dry-run
    python3 -m pipeline.tools.backfill_ticker_events

NOTE: a screener that was legitimately empty on a day is indistinguishable
from one that failed that day; this tool records what the commit contained
and never interpolates. Use --dry-run's per-month counts to spot holes.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pipeline.screeners.ticker_events import (
    SCREENER_FILES, extract_events, load_events, upsert_day, write_events,
)

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_CSV = _REPO / 'data' / 'history' / 'ticker_events.csv'


def snapshot_dates(git_log_output: str) -> List[Tuple[str, str]]:
    """Parse '<sha> <date>' lines (git's newest-first order) -> oldest-first.

    One commit per date: git lists newest first, so the first line seen for a
    date is that day's final committed state.
    """
    seen: Dict[str, str] = {}
    for line in git_log_output.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, date = parts
        if len(date) != 10 or date.count('-') != 2:
            continue
        seen.setdefault(date, sha)
    return [(seen[d], d) for d in sorted(seen)]


def rows_from_snapshot(payloads: Dict[str, Any], date_iso: str) -> List[Dict[str, Any]]:
    """All event rows for one day, across every screener payload present."""
    rows: List[Dict[str, Any]] = []
    for screener, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        rows.extend(extract_events(screener, payload, date_iso))
    return rows


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Dry-run report figures."""
    return {
        'total': len(rows),
        'by_screener': dict(Counter(r['screener'] for r in rows)),
        'by_month': dict(Counter(r['date'][:7] for r in rows)),
        'tickers': len({r['ticker'] for r in rows}),
    }


# ── git access (not unit-tested; exercised by --dry-run) ─────────────

def _git(args: List[str]) -> str:
    return subprocess.run(['git', *args], cwd=_REPO, check=True,
                          capture_output=True, text=True).stdout


def _commits_for(screener: str) -> str:
    return _git(['log', '--format=%H %ad', '--date=short', '--',
                 f'data/output/{screener}.json'])


def _payload_at(sha: str, screener: str) -> Dict[str, Any] | None:
    try:
        return json.loads(_git(['show', f'{sha}:data/output/{screener}.json']))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--csv', default=str(_DEFAULT_CSV))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    # Union of every screener's commit dates; each date maps to that
    # screener's own commit for the day.
    per_screener: Dict[str, Dict[str, str]] = {}
    all_dates: set[str] = set()
    for screener in SCREENER_FILES:
        pairs = snapshot_dates(_commits_for(screener))
        per_screener[screener] = {d: sha for sha, d in pairs}
        all_dates.update(per_screener[screener])
    logger.info("Found %d snapshot dates across %d screeners",
                len(all_dates), len(SCREENER_FILES))

    rows: List[Dict[str, Any]] = []
    for i, date in enumerate(sorted(all_dates), 1):
        payloads = {}
        for screener, by_date in per_screener.items():
            sha = by_date.get(date)
            if sha:
                payload = _payload_at(sha, screener)
                if payload is not None:
                    payloads[screener] = payload
        rows.extend(rows_from_snapshot(payloads, date))
        if i % 20 == 0:
            logger.info("  ...%d/%d dates, %d rows so far", i, len(all_dates), len(rows))

    s = summarize(rows)
    print(f"\nMined {s['total']} events across {s['tickers']} tickers")
    print("\nBy screener:")
    for k, v in sorted(s['by_screener'].items(), key=lambda kv: -kv[1]):
        print(f"  {k:<18}{v}")
    print("\nBy month (holes here mean the pipeline was down, not a quiet tape):")
    for k, v in sorted(s['by_month'].items()):
        print(f"  {k}  {v}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    frame = load_events(args.csv)
    for date in sorted({r['date'] for r in rows}):
        frame = upsert_day(frame, [r for r in rows if r['date'] == date])
    write_events(frame, args.csv)
    print(f"\nWrote {len(frame)} rows to {args.csv}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest pipeline/tests/test_backfill_ticker_events.py -v`
Expected: all PASS.

- [ ] **Step 5: Verify the clock guard**

Run: `python3 -m pytest pipeline/tests/test_no_naive_clock.py -v`
Expected: PASS — the new files contain no `date.today()` / `datetime.now()`.

- [ ] **Step 6: Commit**

```bash
git add pipeline/tools/backfill_ticker_events.py pipeline/tests/test_backfill_ticker_events.py
git commit -m "feat(events): git-mining backfill with dry-run report"
```

---

### Task 6: Wire the daily append into run_all

**Files:**
- Modify: `pipeline/screeners/run_all.py`

**Interfaces:**
- Consumes: `extract_events`, `load_events`, `upsert_day`, `write_events`,
  `build_heating_up`, `build_ticker_events_index`, `market_today`.
- Produces: `data/history/ticker_events.csv` appended daily;
  `data/output/heating_up.json` = `{'timestamp': timestamp, **build_heating_up(...)}`;
  `data/output/ticker_events.json` = `{'timestamp': timestamp, **build_ticker_events_index(...)}`
  (compact separators — this one is the large file).

- [ ] **Step 1: Add the step**

In `pipeline/screeners/run_all.py`, insert a self-contained block **after the
ATR-enrichment step (step 7) and before the "8. Save outputs" loop**. This
placement matters: `results['vcp']` is only added at step 6 and the ATR pass at
step 7 mutates the ticker lists, so an earlier insertion point would miss VCP
entirely and record pre-enrichment rows. The block must not disturb any other
output:

```python
    # 7b. Ticker event archive + heat (isolated: never breaks other outputs)
    heating_up_payload = None
    ticker_events_payload = None
    try:
        from pipeline.screeners.ticker_events import (
            SCREENER_FILES, extract_events, load_events, upsert_day, write_events,
        )
        from pipeline.screeners.ticker_heat import (
            build_heating_up, build_ticker_events_index,
        )
        event_date = market_today().isoformat()
        today_rows = []
        for screener in SCREENER_FILES:
            payload = results.get(screener)
            if isinstance(payload, dict):
                today_rows.extend(extract_events(screener, payload, event_date))

        if not today_rows:
            logger.error(
                "Ticker events: all screeners empty for %s — skipping append "
                "(pipeline-failure signature, not a quiet tape)", event_date)
            events_frame = load_events(str(HISTORY_DIR / 'ticker_events.csv'))
        else:
            events_frame = upsert_day(
                load_events(str(HISTORY_DIR / 'ticker_events.csv')), today_rows)
            write_events(events_frame, str(HISTORY_DIR / 'ticker_events.csv'))
            logger.info("Ticker events: appended %d rows for %s",
                        len(today_rows), event_date)

        heating_up_payload = build_heating_up(events_frame, event_date)
        ticker_events_payload = build_ticker_events_index(events_frame, event_date)
    except Exception:  # noqa: BLE001 — isolate; every other output still ships
        logger.exception("Ticker event archive failed — its outputs will be skipped")
        heating_up_payload = None
        ticker_events_payload = None
```

`market_today` is already imported in this module (used by the breadth step); if
it is not, add `from pipeline.marketcal import market_today` at the top.

- [ ] **Step 2: Write the outputs**

Next to the existing `market_health.json` / `breadth_replay.json` writes, add:

```python
    if heating_up_payload is not None:
        (OUTPUT_DIR / 'heating_up.json').write_text(
            json.dumps({'timestamp': timestamp, **heating_up_payload},
                       indent=2, default=_json_serializer),
            encoding='utf-8')
        logger.info("Saved heating_up.json")

    if ticker_events_payload is not None:
        (OUTPUT_DIR / 'ticker_events.json').write_text(
            json.dumps({'timestamp': timestamp, **ticker_events_payload},
                       separators=(',', ':'), default=_json_serializer),
            encoding='utf-8')
        logger.info("Saved ticker_events.json")
```

- [ ] **Step 3: Verify nothing regressed**

Run: `python3 -m pytest pipeline/tests/ -v`
Expected: all PASS except the 4 known content-processor failures. `run_all` has
no test harness — paste both wiring hunks into your report.

- [ ] **Step 4: Commit**

```bash
git add pipeline/screeners/run_all.py
git commit -m "feat(events): daily event append + heating_up/ticker_events outputs"
```

---

### Task 7: Frontend — heating-up list and ticker timeline

**Files:**
- Create: `frontend/src/components/screener/HeatingUp.jsx`
- Create: `frontend/src/components/ticker/TickerSignalHistory.jsx`
- Create: `frontend/src/hooks/useTickerEvents.js`
- Modify: `frontend/src/components/screener/ScreenerPage.jsx`
- Modify: `frontend/src/components/ticker/TickerPage.jsx`

**Interfaces:**
- Consumes: `/data/output/heating_up.json`, `/data/output/ticker_events.json`.
- Produces:
  - `useHeatingUp()` (inside `HeatingUp.jsx`) — fetches `heating_up.json` on
    mount; renders nothing when absent.
  - `useTickerEvents(symbol)` — lazy-fetches `ticker_events.json` once, returns
    `{ events, loading }` where `events` is that symbol's array or `[]`.
  - `<TickerSignalHistory symbol={} trades={} />` — timeline of screener
    appearances interleaved with the user's fills for that symbol.

- [ ] **Step 1: The events hook**

Create `frontend/src/hooks/useTickerEvents.js`:

```javascript
import { useState, useEffect } from 'react'

// Module-level cache: ticker_events.json is large, fetch it at most once
// per session no matter how many ticker pages are visited.
let cache = null
let inflight = null

export function useTickerEvents(symbol) {
  const [events, setEvents] = useState(() => (cache ? cache.events?.[symbol] ?? [] : null))
  const [loading, setLoading] = useState(!cache)

  useEffect(() => {
    let cancelled = false

    const apply = (data) => {
      if (cancelled) return
      setEvents(data?.events?.[symbol] ?? [])
      setLoading(false)
    }

    if (cache) {
      apply(cache)
      return () => { cancelled = true }
    }

    if (!inflight) {
      inflight = fetch('/data/output/ticker_events.json')
        .then((r) => (r.ok ? r.json() : null))
        .then((json) => { cache = json; return json })
        .catch(() => { cache = null; return null })
        .finally(() => { inflight = null })
    }
    inflight.then(apply)

    return () => { cancelled = true }
  }, [symbol])

  return { events: events ?? [], loading }
}
```

- [ ] **Step 2: HeatingUp section**

Create `frontend/src/components/screener/HeatingUp.jsx`:

```jsx
import { useState, useEffect } from 'react'

const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])

const LABELS = {
  episodic_pivot: 'EP',
  vcp: 'VCP',
  momentum_97: 'MOM',
  gainers_4pct: '4%',
  vol_up_gainers: 'VOL',
  ema21_watch: '21EMA',
  healthy_charts: 'HLTH',
}

export default function HeatingUp({ limit = 25 }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetch('/data/output/heating_up.json')
      .then((r) => (r.ok ? r.json() : null))
      .then((json) => { if (!cancelled) setData(json) })
      .catch(() => { if (!cancelled) setData(null) })
    return () => { cancelled = true }
  }, [])

  if (!data?.rows?.length) return null
  const rows = data.rows.slice(0, limit)

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Heating Up · signals stacking
        </h3>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          as of {data.as_of}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <Th align="left">Ticker</Th>
              <Th>Heat</Th>
              <Th align="left">Signals</Th>
              <Th>Span</Th>
              <Th align="left">Sector</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.ticker} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
                <td className="px-2 py-1.5">
                  <a href={`#/ticker/${r.ticker}`} className="font-mono font-medium text-[var(--color-text)] hover:underline">
                    {r.ticker}
                  </a>
                </td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--color-text)]">
                  {r.score.toFixed(2)}
                </td>
                <td className="px-2 py-1.5">
                  <span className="flex flex-wrap gap-1">
                    {r.screeners.map((s) => (
                      <span
                        key={s.name}
                        title={`${s.name} · ${s.hits}× · last ${s.last_date}`}
                        className={`text-[9px] font-mono px-1 py-0.5 rounded border ${
                          QUALITY.has(s.name)
                            ? 'border-[var(--color-profit)] text-[var(--color-profit)]'
                            : 'border-[var(--color-border)] text-[var(--color-text-secondary)]'
                        }`}
                      >
                        {LABELS[s.name] ?? s.name}{s.hits > 1 ? `×${s.hits}` : ''}
                      </span>
                    ))}
                  </span>
                </td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--color-text-secondary)]">
                  {r.days_span}d
                </td>
                <td className="px-2 py-1.5 text-[var(--color-text-secondary)]">{r.sector ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Th({ children, align = 'right' }) {
  return (
    <th className={`px-2 py-1.5 text-${align} text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] whitespace-nowrap`}>
      {children}
    </th>
  )
}
```

- [ ] **Step 3: TickerSignalHistory section**

Create `frontend/src/components/ticker/TickerSignalHistory.jsx`:

```jsx
import { useMemo } from 'react'
import { useTickerEvents } from '../../hooks/useTickerEvents'

const LABELS = {
  episodic_pivot: 'Episodic Pivot',
  vcp: 'VCP',
  momentum_97: 'Momentum 97',
  gainers_4pct: 'Up 4% day',
  vol_up_gainers: 'Volume-up gainer',
  ema21_watch: '21 EMA watch',
  healthy_charts: 'Healthy chart',
}

const QUALITY = new Set(['episodic_pivot', 'vcp', 'momentum_97'])

function detail(e) {
  const bits = []
  if (e.change_pct != null) bits.push(`${(e.change_pct * 100).toFixed(1)}%`)
  if (e.rel_volume != null) bits.push(`${e.rel_volume.toFixed(1)}× vol`)
  if (e.num_contractions != null) bits.push(`${e.num_contractions} contractions`)
  if (e.pct_to_pivot != null) bits.push(`${(e.pct_to_pivot * 100).toFixed(1)}% to pivot`)
  if (e.group) bits.push(`RS ${e.group}`)
  return bits.join(' · ')
}

export default function TickerSignalHistory({ symbol, trades }) {
  const { events, loading } = useTickerEvents(symbol)

  const timeline = useMemo(() => {
    const signalItems = events.map((e) => ({
      kind: 'signal', date: e.date, screener: e.screener, detail: detail(e),
    }))
    const tradeItems = (trades ?? [])
      .filter((t) => t.ticker === symbol && t.entryDate)
      .map((t) => ({
        kind: 'trade',
        date: String(t.entryDate).slice(0, 10),
        direction: t.direction,
        price: t.entryPrice,
        qty: t.shares ?? t.currentQty,
      }))
    return [...signalItems, ...tradeItems].sort((a, b) => b.date.localeCompare(a.date))
  }, [events, trades, symbol])

  if (loading || !timeline.length) return null

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
        Signal History · screener appearances and your fills
      </h3>
      <ul className="space-y-1">
        {timeline.map((item, i) => (
          <li key={`${item.date}-${item.kind}-${i}`} className="flex items-baseline gap-3 text-[11px]">
            <span className="font-mono tabular-nums text-[var(--color-text-muted)] w-20 shrink-0">
              {item.date}
            </span>
            {item.kind === 'trade' ? (
              <>
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  item.direction === 'long' ? 'bg-[var(--color-profit)]' : 'bg-[var(--color-loss)]'
                }`} />
                <span className="font-medium text-[var(--color-text)]">
                  {item.direction === 'long' ? 'BOUGHT' : 'SOLD SHORT'}
                  {item.qty ? ` ${item.qty}` : ''}
                  {item.price != null ? ` @ ${item.price}` : ''}
                </span>
              </>
            ) : (
              <>
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  QUALITY.has(item.screener) ? 'bg-[var(--color-signal-caution)]' : 'bg-[var(--color-border)]'
                }`} />
                <span className="text-[var(--color-text)]">
                  {LABELS[item.screener] ?? item.screener}
                </span>
                <span className="text-[var(--color-text-secondary)]">{item.detail}</span>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 4: Mount both sections**

In `frontend/src/components/screener/ScreenerPage.jsx`: add
`import HeatingUp from './HeatingUp'`, then find the line

```jsx
          {results && <ResultsTable rows={results} />}
```

and insert directly **above** it, inside the same fragment:

```jsx
          <div className="mb-4">
            <HeatingUp />
          </div>
```

(This is inside the `activeTab === 0` branch, so the Watchlist tab is unaffected.)

In `frontend/src/components/ticker/TickerPage.jsx`: add
`import TickerSignalHistory from './TickerSignalHistory'`, then insert directly
**above** the existing `<div className="mb-4"><TickerTrades … /></div>` block:

```jsx
      <div className="mb-4">
        <TickerSignalHistory symbol={symbol} trades={enrichedAll} />
      </div>
```

- [ ] **Step 5: Build check**

Run: `cd frontend && npx vite build 2>&1 | tail -3 && cd ..`
Expected: success.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useTickerEvents.js frontend/src/components/screener/HeatingUp.jsx frontend/src/components/ticker/TickerSignalHistory.jsx frontend/src/components/screener/ScreenerPage.jsx frontend/src/components/ticker/TickerPage.jsx
git commit -m "feat(events-ui): heating-up list + ticker signal history timeline"
```

---

### Task 8: End-to-end — real backfill + browser verification

**Files:**
- Modify (data only): `data/history/ticker_events.csv`, `data/output/heating_up.json`, `data/output/ticker_events.json`

- [ ] **Step 1: Full Python suite**

Run: `python3 -m pytest pipeline/tests/ tests/ -q`
Expected: only the 4 known content-processor failures.

- [ ] **Step 2: Backfill dry-run**

```bash
python3 -m pipeline.tools.backfill_ticker_events --dry-run
```

Sanity gates before proceeding:
- total events in the tens of thousands (≈88 dates × a few hundred rows/day)
- `by_screener` shows all seven names present with non-trivial counts
- `by_month` spans 2026-03 → 2026-07 with **no month at zero** — a zero or
  near-zero month means the pipeline was down then, not that the tape was quiet;
  note it in your report rather than silently accepting it

If a gate fails, STOP and report before writing.

- [ ] **Step 3: Real backfill**

```bash
python3 -m pipeline.tools.backfill_ticker_events
```

Then verify the archive:

```bash
python3 - <<'EOF'
import pandas as pd
f = pd.read_csv('data/history/ticker_events.csv', dtype={'date': str})
assert not f.duplicated(subset=['date', 'ticker', 'screener']).any(), 'dup events!'
assert list(f['date']) == sorted(f['date']), 'not sorted!'
wd = pd.to_datetime(f['date']).dt.dayofweek
assert (wd < 5).all(), f"weekend rows: {sorted(set(f[wd >= 5]['date']))}"
print(f"{len(f)} rows, {f['date'].nunique()} dates, {f['ticker'].nunique()} tickers")
print(f"{f['date'].min()} .. {f['date'].max()}")
print(f['screener'].value_counts().to_string())
EOF
```

- [ ] **Step 4: Generate the two outputs**

```bash
python3 - <<'EOF'
import json, os, datetime as dt
from pipeline.screeners.ticker_events import load_events
from pipeline.screeners.ticker_heat import build_heating_up, build_ticker_events_index

frame = load_events('data/history/ticker_events.csv')
as_of = str(frame['date'].max())
ts = dt.datetime.now(dt.timezone.utc).isoformat()

heat = build_heating_up(frame, as_of)
index = build_ticker_events_index(frame, as_of)

json.dump({'timestamp': ts, **heat}, open('data/output/heating_up.json', 'w'), indent=2)
with open('data/output/ticker_events.json', 'w') as f:
    json.dump({'timestamp': ts, **index}, f, separators=(',', ':'))

print('as_of:', as_of, '| heating rows:', len(heat['rows']))
print('top 5:', [(r['ticker'], r['score'], [s['name'] for s in r['screeners']])
                 for r in heat['rows'][:5]])
print('index tickers:', len(index['events']),
      '| KB:', round(os.path.getsize('data/output/ticker_events.json') / 1024))
EOF
```

Sanity gates: top scores are dominated by names with *multiple distinct*
screeners (not one screener repeated); `ticker_events.json` under ~4 MB.

- [ ] **Step 5: Browser verification**

```bash
rm -rf frontend/public/data/output && cp -r data/output frontend/public/data/output
```

Start the dev server (preview tools; add a launch.json entry for this
worktree's `frontend` if one is not present). Verify:
1. `#/screener` — the Heating Up table renders above the results, chips show
   screener labels, quality chips (EP/VCP/MOM) are visually distinct, ticker
   links navigate to the ticker page.
2. Click through to a top-ranked ticker — Signal History renders above Trades,
   newest first, with the dates and screeners matching that ticker's rows in
   `ticker_events.csv` (spot-check two entries against the CSV).
3. Open a ticker you have traded — fills appear interleaved in the timeline at
   their entry dates.
4. Open a ticker with no events — the section is absent, no crash.
5. Console clean throughout.

Fix anything that fails, re-verify, then:

```bash
rm -rf frontend/public/data/output
```

- [ ] **Step 6: Commit the data**

```bash
git add data/history/ticker_events.csv data/output/heating_up.json data/output/ticker_events.json
git commit -m "data(events): backfilled ticker event archive + heating-up/index outputs"
```
