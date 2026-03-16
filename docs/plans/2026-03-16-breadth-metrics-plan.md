# Breadth Metrics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add self-calculated market breadth metrics (Stockbee MM scans + classic breadth + 100-day Lightweight Charts) to the Fluxus Capital Dashboard.

**Architecture:** New `breadth_metrics.py` screener consumes the existing Finviz universe DataFrame + a new `sma40_dist` column from yfinance enrichment. It computes daily snapshots, persists 100-day rolling history, appends to a CSV archive, and outputs `breadth.json`. The frontend adds a new "Breadth" page with three sections rendered via Lightweight Charts.

**Tech Stack:** Python 3.11 / pandas (pipeline), React 19 / Tailwind 4 / TradingView Lightweight Charts (frontend)

---

## Task 1: Add SMA40 to yfinance enrichment

**Files:**
- Modify: `pipeline/adapters/yfinance_adapter.py:268-285`
- Test: `pipeline/tests/test_adapters.py`

**Step 1: Write the failing test**

Add to the bottom of `pipeline/tests/test_adapters.py`:

```python
class TestSma40:
    def test_calculate_sma_40(self):
        hist = _make_ohlc(60)
        sma40 = calculate_sma(hist, 40)
        assert sma40 is not None
        assert isinstance(sma40, float)
        # SMA40 should be between SMA20 and SMA50
        sma20 = calculate_sma(hist, 20)
        sma50 = calculate_sma(hist, 50)
        # Just verify it returns a reasonable value (not testing ordering since synthetic data)
        assert sma40 != sma20
        assert sma40 != sma50
```

**Step 2: Run test to verify it passes (this is a sanity test using existing `calculate_sma`)**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/test_adapters.py::TestSma40 -v`
Expected: PASS (calculate_sma already supports any period)

**Step 3: Add sma40_dist to enrich_universe()**

In `pipeline/adapters/yfinance_adapter.py`, after line 269 (`sma50 = ...`), add:

```python
sma40 = float(hist['Close'].rolling(40).mean().iloc[-1]) if n >= 40 else None
```

Then in the `enriched[ticker]` dict (line 276-291), after `'sma50_dist'` (line 284), add:

```python
'sma40_dist': (close - sma40) / sma40 if sma40 else None,
```

Also add `'sma40_dist'` to `universe_cols` list in `run_all.py` line 319 (after `'sma50_dist'`).

**Step 4: Add sma40 to fallback universe**

In `run_all.py` `build_fallback_universe()`, after line 96 (`sma50 = ...`), add:

```python
sma40 = float(hist['Close'].rolling(40).mean().iloc[-1]) if len(hist) >= 40 else None
```

And in the rows.append dict (line 106-128), after `'sma50_dist'` (line 117), add:

```python
'sma40_dist': (close - sma40) / sma40 if sma40 else None,
```

**Step 5: Run full test suite**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/test_adapters.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add pipeline/adapters/yfinance_adapter.py pipeline/screeners/run_all.py pipeline/tests/test_adapters.py
git commit -m "feat: add sma40_dist to yfinance enrichment for T2108 calculation"
```

---

## Task 2: Add ^GSPC to fetch_ma_data

**Files:**
- Modify: `pipeline/adapters/yfinance_adapter.py:318-323`
- Modify: `pipeline/screeners/run_all.py:257`

**Step 1: Update fetch_ma_data default tickers**

In `pipeline/adapters/yfinance_adapter.py` line 323, change:

```python
tickers = ['SPY', 'QQQ', 'IWM', 'RSP']
```

to:

```python
tickers = ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC']
```

**Step 2: Update run_all.py call**

In `pipeline/screeners/run_all.py` line 257, change:

```python
signals = yf_adapter.fetch_ma_data(['SPY', 'QQQ', 'IWM', 'RSP'])
```

to:

```python
signals = yf_adapter.fetch_ma_data(['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC'])
```

**Step 3: Run tests**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/test_adapters.py -v`
Expected: All PASS (no tests call fetch_ma_data with network)

**Step 4: Commit**

```bash
git add pipeline/adapters/yfinance_adapter.py pipeline/screeners/run_all.py
git commit -m "feat: add ^GSPC to fetch_ma_data for SPX EOD price"
```

---

## Task 3: Create breadth_metrics.py — core calculation

**Files:**
- Create: `pipeline/screeners/breadth_metrics.py`
- Create: `pipeline/tests/test_breadth_metrics.py`

**Step 1: Write the failing test**

Create `pipeline/tests/test_breadth_metrics.py`:

```python
"""Tests for breadth_metrics screener."""
import pytest
import pandas as pd
import numpy as np


def _make_universe(n=100) -> pd.DataFrame:
    """Generate synthetic universe for breadth testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'ticker': [f'STOCK{i}' for i in range(n)],
        'close': np.random.uniform(10, 500, n),
        'change_pct': np.random.uniform(-0.10, 0.10, n),
        'perf_1m': np.random.uniform(-0.40, 0.60, n),
        'perf_3m': np.random.uniform(-0.40, 0.60, n),
        'sma20_dist': np.random.uniform(-0.20, 0.20, n),
        'sma40_dist': np.random.uniform(-0.20, 0.20, n),
        'sma50_dist': np.random.uniform(-0.20, 0.20, n),
        'sma200_dist': np.random.uniform(-0.20, 0.20, n),
        'high_52w': np.random.uniform(-0.50, 0.0, n),  # fraction, not price
        'low_52w': np.random.uniform(0.0, 1.0, n),
    })


class TestComputeSnapshot:
    def test_returns_expected_keys(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe()
        result = compute_snapshot(universe)
        # MM keys
        assert 'up_4pct' in result
        assert 'down_4pct' in result
        assert 'up_25pct_qtr' in result
        assert 'down_25pct_qtr' in result
        assert 'up_25pct_month' in result
        assert 'down_25pct_month' in result
        assert 'up_50pct_month' in result
        assert 'down_50pct_month' in result
        # Breadth keys
        assert 't2108' in result
        assert 'pct_above_200sma' in result
        assert 'pct_above_50sma' in result
        assert 'pct_above_20sma' in result
        assert 'advances' in result
        assert 'declines' in result
        assert 'new_highs' in result
        assert 'new_lows' in result
        assert 'net_advances' in result
        assert 'universe_size' in result

    def test_counts_are_non_negative(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe()
        result = compute_snapshot(universe)
        for key in ['up_4pct', 'down_4pct', 'advances', 'declines', 'new_highs', 'new_lows']:
            assert result[key] >= 0

    def test_percentages_in_range(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe()
        result = compute_snapshot(universe)
        for key in ['t2108', 'pct_above_200sma', 'pct_above_50sma', 'pct_above_20sma']:
            assert 0 <= result[key] <= 100

    def test_universe_size_matches(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(200)
        result = compute_snapshot(universe)
        assert result['universe_size'] == 200

    def test_empty_universe(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(0)
        result = compute_snapshot(universe)
        assert result['universe_size'] == 0
        assert result['advances'] == 0

    def test_all_up_4pct(self):
        from pipeline.screeners.breadth_metrics import compute_snapshot
        universe = _make_universe(50)
        universe['change_pct'] = 0.05  # all +5%
        result = compute_snapshot(universe)
        assert result['up_4pct'] == 50
        assert result['down_4pct'] == 0


class TestMcClellan:
    def test_mcclellan_with_sufficient_history(self):
        from pipeline.screeners.breadth_metrics import compute_mcclellan
        # Need at least 39 data points for EMA39
        np.random.seed(42)
        net_advances_history = list(np.random.randint(-100, 200, 50))
        result = compute_mcclellan(net_advances_history)
        assert 'mcclellan_osc' in result
        assert isinstance(result['mcclellan_osc'], float)

    def test_mcclellan_with_short_history(self):
        from pipeline.screeners.breadth_metrics import compute_mcclellan
        result = compute_mcclellan([100, 200, -50])
        assert result['mcclellan_osc'] is not None  # Should still compute with EWM


class TestAdLine:
    def test_ad_line_cumulative(self):
        from pipeline.screeners.breadth_metrics import compute_ad_line
        net_advances_history = [100, -50, 200, -30]
        result = compute_ad_line(net_advances_history)
        # Cumulative sum: 100, 50, 250, 220
        assert result == 220

    def test_ad_line_empty(self):
        from pipeline.screeners.breadth_metrics import compute_ad_line
        assert compute_ad_line([]) == 0
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/test_breadth_metrics.py -v`
Expected: FAIL (module not found)

**Step 3: Write the implementation**

Create `pipeline/screeners/breadth_metrics.py`:

```python
"""Self-calculated market breadth metrics.

Combines Stockbee Market Monitor scans with classic breadth indicators.
Consumes the Finviz universe DataFrame (with sma40_dist from yfinance
enrichment) and produces daily snapshots, rolling history, and a CSV archive.

Metrics computed:
- Stockbee MM: 4% up/down, 5d/10d ratios, 25% qtr/month, 50% month
- Classic: % above 20/40/50/200 SMA, A/D line, McClellan Oscillator, NH/NL
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────
_NEW_HIGH_THRESHOLD = -0.02  # within 2% of 52w high
_NEW_LOW_THRESHOLD = 0.02    # within 2% of 52w low
_HISTORY_DAYS = 100


def compute_snapshot(universe: pd.DataFrame) -> Dict[str, Any]:
    """Compute a single day's breadth snapshot from the universe.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz universe with columns: change_pct, perf_1m, perf_3m,
        sma20_dist, sma40_dist, sma50_dist, sma200_dist, high_52w, low_52w.

    Returns
    -------
    dict
        All daily breadth counts and percentages.
    """
    n = len(universe)
    if n == 0:
        return {
            'universe_size': 0,
            'up_4pct': 0, 'down_4pct': 0,
            'up_25pct_qtr': 0, 'down_25pct_qtr': 0,
            'up_25pct_month': 0, 'down_25pct_month': 0,
            'up_50pct_month': 0, 'down_50pct_month': 0,
            't2108': 0.0,
            'pct_above_200sma': 0.0, 'pct_above_50sma': 0.0,
            'pct_above_20sma': 0.0,
            'advances': 0, 'declines': 0,
            'new_highs': 0, 'new_lows': 0,
            'net_advances': 0,
        }

    chg = pd.to_numeric(universe['change_pct'], errors='coerce')
    perf_1m = pd.to_numeric(universe.get('perf_1m', pd.Series(dtype=float)), errors='coerce')
    perf_3m = pd.to_numeric(universe.get('perf_3m', pd.Series(dtype=float)), errors='coerce')

    # Stockbee MM scans
    up_4pct = int((chg >= 0.04).sum())
    down_4pct = int((chg <= -0.04).sum())
    up_25pct_qtr = int((perf_3m >= 0.25).sum())
    down_25pct_qtr = int((perf_3m <= -0.25).sum())
    up_25pct_month = int((perf_1m >= 0.25).sum())
    down_25pct_month = int((perf_1m <= -0.25).sum())
    up_50pct_month = int((perf_1m >= 0.50).sum())
    down_50pct_month = int((perf_1m <= -0.50).sum())

    # Classic breadth: % above MAs
    sma20 = pd.to_numeric(universe.get('sma20_dist', pd.Series(dtype=float)), errors='coerce')
    sma40 = pd.to_numeric(universe.get('sma40_dist', pd.Series(dtype=float)), errors='coerce')
    sma50 = pd.to_numeric(universe.get('sma50_dist', pd.Series(dtype=float)), errors='coerce')
    sma200 = pd.to_numeric(universe.get('sma200_dist', pd.Series(dtype=float)), errors='coerce')

    pct_above_20 = round(float((sma20 > 0).sum()) / n * 100, 2)
    t2108 = round(float((sma40 > 0).sum()) / n * 100, 2)
    pct_above_50 = round(float((sma50 > 0).sum()) / n * 100, 2)
    pct_above_200 = round(float((sma200 > 0).sum()) / n * 100, 2)

    # Advances / Declines
    advances = int((chg > 0).sum())
    declines = int((chg < 0).sum())

    # New 52w highs / lows
    high_52w = pd.to_numeric(universe.get('high_52w', pd.Series(dtype=float)), errors='coerce')
    low_52w = pd.to_numeric(universe.get('low_52w', pd.Series(dtype=float)), errors='coerce')
    new_highs = int((high_52w >= _NEW_HIGH_THRESHOLD).sum())
    new_lows = int((low_52w <= _NEW_LOW_THRESHOLD).sum())

    return {
        'universe_size': n,
        'up_4pct': up_4pct,
        'down_4pct': down_4pct,
        'up_25pct_qtr': up_25pct_qtr,
        'down_25pct_qtr': down_25pct_qtr,
        'up_25pct_month': up_25pct_month,
        'down_25pct_month': down_25pct_month,
        'up_50pct_month': up_50pct_month,
        'down_50pct_month': down_50pct_month,
        't2108': t2108,
        'pct_above_200sma': pct_above_200,
        'pct_above_50sma': pct_above_50,
        'pct_above_20sma': pct_above_20,
        'advances': advances,
        'declines': declines,
        'new_highs': new_highs,
        'new_lows': new_lows,
        'net_advances': advances - declines,
    }


def compute_ad_line(net_advances_history: List[int]) -> int:
    """Compute cumulative Advance/Decline line value.

    Parameters
    ----------
    net_advances_history : list of int
        Daily (advances - declines) values including today.

    Returns
    -------
    int
        Cumulative A/D line value.
    """
    if not net_advances_history:
        return 0
    return int(sum(net_advances_history))


def compute_mcclellan(net_advances_history: List[int]) -> Dict[str, float]:
    """Compute McClellan Oscillator from net advances history.

    McClellan = EMA19(net_advances) - EMA39(net_advances)

    Parameters
    ----------
    net_advances_history : list of int
        Daily (advances - declines) values.

    Returns
    -------
    dict
        ``{'mcclellan_osc': float}``
    """
    if not net_advances_history:
        return {'mcclellan_osc': 0.0}

    s = pd.Series(net_advances_history, dtype=float)
    ema19 = float(s.ewm(span=19, adjust=False).mean().iloc[-1])
    ema39 = float(s.ewm(span=39, adjust=False).mean().iloc[-1])
    return {'mcclellan_osc': round(ema19 - ema39, 2)}


def compute_ratios(
    history: List[Dict[str, Any]],
    today_up: int,
    today_down: int,
) -> Dict[str, float]:
    """Compute 5-day and 10-day breadth ratios.

    Parameters
    ----------
    history : list of dict
        Past daily entries with 'up_4pct' and 'down_4pct' keys.
    today_up : int
        Today's 4% gainer count.
    today_down : int
        Today's 4% loser count.

    Returns
    -------
    dict
        ``{'ratio_5d': float, 'ratio_10d': float}``
    """
    all_entries = history + [{'up_4pct': today_up, 'down_4pct': today_down}]

    def _ratio(entries):
        up = sum(e.get('up_4pct', 0) for e in entries)
        down = sum(e.get('down_4pct', 0) for e in entries)
        if down > 0:
            return round(up / down, 4)
        return float(up) if up > 0 else 0.0

    return {
        'ratio_5d': _ratio(all_entries[-5:]),
        'ratio_10d': _ratio(all_entries[-10:]),
    }


# ── History persistence ───────────────────────────────────────────────

def _load_history(history_path: str) -> List[Dict[str, Any]]:
    """Load rolling breadth history from JSON file."""
    path = Path(history_path)
    if not path.exists():
        logger.info("No breadth history at %s — starting fresh", history_path)
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            logger.warning("Breadth history is not a list — ignoring")
            return []
        return data[-(_HISTORY_DAYS - 1):]  # keep room for today
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load breadth history: %s", exc)
        return []


def _save_history(
    history_path: str,
    history: List[Dict[str, Any]],
    today_entry: Dict[str, Any],
) -> None:
    """Append today's entry and save rolling history."""
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    combined = history + [today_entry]
    combined = combined[-_HISTORY_DAYS:]
    try:
        path.write_text(json.dumps(combined, indent=2), encoding='utf-8')
        logger.info("Saved breadth history (%d entries) to %s", len(combined), history_path)
    except OSError as exc:
        logger.error("Failed to write breadth history: %s", exc)


def _append_csv(csv_path: str, row: Dict[str, Any]) -> None:
    """Append a single row to the breadth archive CSV."""
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    fieldnames = [
        'date', 'universe_size', 'spx_close',
        'up_4pct', 'down_4pct', 'ratio_5d', 'ratio_10d',
        'up_25pct_qtr', 'down_25pct_qtr',
        'up_25pct_month', 'down_25pct_month',
        'up_50pct_month', 'down_50pct_month',
        't2108', 'pct_above_200sma', 'pct_above_50sma', 'pct_above_20sma',
        'advances', 'declines', 'new_highs', 'new_lows',
        'ad_line', 'mcclellan_osc',
    ]

    try:
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        logger.info("Appended breadth row to %s", csv_path)
    except OSError as exc:
        logger.error("Failed to append CSV: %s", exc)


# ── Main entry point ─────────────────────────────────────────────────

def run(
    universe: pd.DataFrame,
    history_path: str,
    csv_path: str,
    spx_close: Optional[float] = None,
) -> Dict[str, Any]:
    """Run the full breadth metrics calculation.

    Parameters
    ----------
    universe : pd.DataFrame
        Scored universe with SMA distance columns.
    history_path : str
        Path to rolling JSON history file.
    csv_path : str
        Path to append-only CSV archive.
    spx_close : float, optional
        S&P 500 close price from ^GSPC.

    Returns
    -------
    dict
        Complete breadth output for breadth.json.
    """
    # 1. Compute today's snapshot
    snapshot = compute_snapshot(universe)

    # 2. Load history
    history = _load_history(history_path)

    # 3. Compute ratios from history
    ratios = compute_ratios(history, snapshot['up_4pct'], snapshot['down_4pct'])

    # 4. Build net_advances history for A/D and McClellan
    net_advances_history = [e.get('net_advances', 0) for e in history]
    net_advances_history.append(snapshot['net_advances'])

    ad_line = compute_ad_line(net_advances_history)
    mcclellan = compute_mcclellan(net_advances_history)

    # 5. Build today's history entry
    today_entry = {
        'date': date.today().isoformat(),
        **snapshot,
        **ratios,
        'ad_line': ad_line,
        **mcclellan,
    }

    # 6. Save history
    _save_history(history_path, history, today_entry)

    # 7. Append CSV
    csv_row = {**today_entry, 'spx_close': spx_close}
    _append_csv(csv_path, csv_row)

    # 8. Build history arrays for charting
    all_entries = history + [today_entry]
    history_arrays = {
        'dates': [e['date'] for e in all_entries],
        'pct_above_200sma': [e.get('pct_above_200sma', 0) for e in all_entries],
        'pct_above_50sma': [e.get('pct_above_50sma', 0) for e in all_entries],
        'pct_above_20sma': [e.get('pct_above_20sma', 0) for e in all_entries],
        'mcclellan_osc': [e.get('mcclellan_osc', 0) for e in all_entries],
    }

    # 9. Assemble output
    return {
        'universe_size': snapshot['universe_size'],
        'spx_close': spx_close,
        'mm': {
            'up_4pct': snapshot['up_4pct'],
            'down_4pct': snapshot['down_4pct'],
            'ratio_5d': ratios['ratio_5d'],
            'ratio_10d': ratios['ratio_10d'],
            'up_25pct_qtr': snapshot['up_25pct_qtr'],
            'down_25pct_qtr': snapshot['down_25pct_qtr'],
            'up_25pct_month': snapshot['up_25pct_month'],
            'down_25pct_month': snapshot['down_25pct_month'],
            'up_50pct_month': snapshot['up_50pct_month'],
            'down_50pct_month': snapshot['down_50pct_month'],
        },
        'breadth': {
            't2108': snapshot['t2108'],
            'pct_above_200sma': snapshot['pct_above_200sma'],
            'pct_above_50sma': snapshot['pct_above_50sma'],
            'pct_above_20sma': snapshot['pct_above_20sma'],
            'advances': snapshot['advances'],
            'declines': snapshot['declines'],
            'new_highs': snapshot['new_highs'],
            'new_lows': snapshot['new_lows'],
            'ad_line': ad_line,
            'mcclellan_osc': mcclellan['mcclellan_osc'],
        },
        'history': history_arrays,
    }
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/test_breadth_metrics.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add pipeline/screeners/breadth_metrics.py pipeline/tests/test_breadth_metrics.py
git commit -m "feat: add breadth_metrics screener with MM scans, classic breadth, McClellan"
```

---

## Task 4: Integrate breadth_metrics into run_all.py

**Files:**
- Modify: `pipeline/screeners/run_all.py:34,272-273,296-300,319`

**Step 1: Add import**

In `pipeline/screeners/run_all.py`, after line 34 (`from pipeline.screeners.stockbee_ratio import run as run_stockbee_ratio`), add:

```python
from pipeline.screeners.breadth_metrics import run as run_breadth_metrics
```

**Step 2: Add breadth call after stockbee_ratio**

After line 273 (end of stockbee_ratio block), add:

```python
    # 5b. Breadth metrics (Stockbee MM + classic breadth)
    logger.info("Running breadth metrics...")
    spx_close = signals.get('^GSPC', {}).get('close')
    breadth_result = run_breadth_metrics(
        universe,
        str(HISTORY_DIR / 'breadth_metrics_history.json'),
        str(HISTORY_DIR / 'breadth_archive.csv'),
        spx_close=spx_close,
    )
```

**Step 3: Add breadth.json save**

After the signals save block (after line 307), add:

```python
    # Save breadth metrics
    (OUTPUT_DIR / 'breadth.json').write_text(json.dumps(
        {'timestamp': timestamp, **breadth_result}, indent=2, default=_json_serializer
    ))
    logger.info("Saved breadth.json")
```

**Step 4: Run tests**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add pipeline/screeners/run_all.py
git commit -m "feat: integrate breadth_metrics into pipeline orchestrator"
```

---

## Task 5: Update GitHub Actions validation

**Files:**
- Modify: `.github/workflows/daily-data-update.yml:44-55`

**Step 1: Add breadth.json to validation**

In `.github/workflows/daily-data-update.yml`, in the EXPECTED_FILES array (line 44-55), add after `"data/output/vcp.json"`:

```yaml
            "data/output/breadth.json"
```

**Step 2: Commit**

```bash
git add .github/workflows/daily-data-update.yml
git commit -m "chore: add breadth.json to CI validation"
```

---

## Task 6: Install Lightweight Charts + add to useMarketData

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/hooks/useMarketData.js:5-16`

**Step 1: Install lightweight-charts**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm install lightweight-charts`

**Step 2: Add 'breadth' to FILES array**

In `frontend/src/hooks/useMarketData.js`, add `'breadth'` to the FILES array (line 15, before `'stockbee_ratio'`):

```javascript
const FILES = [
  'signals',
  'etf_data',
  'momentum_97',
  'gainers_4pct',
  'vol_up_gainers',
  'ema21_watch',
  'healthy_charts',
  'episodic_pivot',
  'vcp',
  'stockbee_ratio',
  'breadth',
]
```

**Step 3: Verify dev server still runs**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/hooks/useMarketData.js
git commit -m "feat: install lightweight-charts, add breadth to data loading"
```

---

## Task 7: Create MarketMonitor component (Section 1)

**Files:**
- Create: `frontend/src/components/breadth/MarketMonitor.jsx`

**Step 1: Create the component**

Create directory first: `mkdir -p frontend/src/components/breadth`

Create `frontend/src/components/breadth/MarketMonitor.jsx`:

```jsx
export default function MarketMonitor({ data }) {
  if (!data) return null

  const mm = data.mm || {}
  const breadth = data.breadth || {}

  const ratioColor = (val) =>
    val >= 2.0 ? 'text-green-600' : val <= 0.5 ? 'text-red-500' : 'text-stone-700'

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-3">
        Stockbee Market Monitor
      </h3>

      <div className="grid grid-cols-3 gap-3">
        {/* Primary */}
        <div>
          <div className="text-[9px] font-medium uppercase tracking-wide text-stone-400 mb-2">
            Primary
          </div>
          <div className="space-y-1">
            <Row label="Up 4%" value={mm.up_4pct} />
            <Row label="Down 4%" value={mm.down_4pct} />
            <Row
              label="Ratio 5D"
              value={mm.ratio_5d?.toFixed(2)}
              className={ratioColor(mm.ratio_5d)}
            />
            <Row
              label="Ratio 10D"
              value={mm.ratio_10d?.toFixed(2)}
              className={ratioColor(mm.ratio_10d)}
            />
            <Row label="Up 25% Qtr" value={mm.up_25pct_qtr} />
            <Row label="Down 25% Qtr" value={mm.down_25pct_qtr} />
          </div>
        </div>

        {/* Secondary */}
        <div>
          <div className="text-[9px] font-medium uppercase tracking-wide text-stone-400 mb-2">
            Secondary
          </div>
          <div className="space-y-1">
            <Row label="Up 25% Mo" value={mm.up_25pct_month} />
            <Row label="Down 25% Mo" value={mm.down_25pct_month} />
            <Row label="Up 50% Mo" value={mm.up_50pct_month} />
            <Row label="Down 50% Mo" value={mm.down_50pct_month} />
          </div>
        </div>

        {/* Reference */}
        <div>
          <div className="text-[9px] font-medium uppercase tracking-wide text-stone-400 mb-2">
            Reference
          </div>
          <div className="space-y-1">
            <Row label="Worden" value={data.universe_size?.toLocaleString()} />
            <Row
              label="T2108"
              value={breadth.t2108 != null ? `${breadth.t2108}%` : '\u2014'}
            />
            <Row
              label="SPX"
              value={data.spx_close != null ? data.spx_close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '\u2014'}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, className = 'text-stone-700' }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
        {label}
      </span>
      <span className={`font-mono text-xs ${className}`}>
        {value ?? '\u2014'}
      </span>
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds (component not yet imported anywhere, but no syntax errors)

**Step 3: Commit**

```bash
git add frontend/src/components/breadth/MarketMonitor.jsx
git commit -m "feat: add MarketMonitor component (Stockbee MM Section 1)"
```

---

## Task 8: Create ClassicBreadth component (Section 2)

**Files:**
- Create: `frontend/src/components/breadth/ClassicBreadth.jsx`

**Step 1: Create the component**

Create `frontend/src/components/breadth/ClassicBreadth.jsx`:

```jsx
export default function ClassicBreadth({ data }) {
  if (!data?.breadth) return null

  const b = data.breadth

  const mcColor =
    b.mcclellan_osc > 0 ? 'text-green-600' : b.mcclellan_osc < 0 ? 'text-red-500' : 'text-stone-700'

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-3">
        Classic Breadth
      </h3>

      <div className="grid grid-cols-3 gap-3">
        {/* % Above MAs */}
        <div className="space-y-1">
          <PctBar label="% > 200 SMA" value={b.pct_above_200sma} />
          <PctBar label="% > 50 SMA" value={b.pct_above_50sma} />
          <PctBar label="% > 20 SMA" value={b.pct_above_20sma} />
        </div>

        {/* A/D */}
        <div className="space-y-1">
          <Row label="Advances" value={b.advances} className="text-green-600" />
          <Row label="Declines" value={b.declines} className="text-red-500" />
          <Row label="A/D Line" value={b.ad_line?.toLocaleString()} />
          <Row label="McClellan" value={b.mcclellan_osc} className={mcColor} />
        </div>

        {/* NH / NL */}
        <div className="space-y-1">
          <Row label="New Highs" value={b.new_highs} className="text-green-600" />
          <Row label="New Lows" value={b.new_lows} className="text-red-500" />
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, className = 'text-stone-700' }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
        {label}
      </span>
      <span className={`font-mono text-xs ${className}`}>
        {value ?? '\u2014'}
      </span>
    </div>
  )
}

function PctBar({ label, value }) {
  const pct = value ?? 0
  const barColor =
    pct >= 60 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div>
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
          {label}
        </span>
        <span className="font-mono text-xs text-stone-700">
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="h-1 bg-stone-100 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/breadth/ClassicBreadth.jsx
git commit -m "feat: add ClassicBreadth component (Section 2)"
```

---

## Task 9: Create BreadthCharts component (Section 3)

**Files:**
- Create: `frontend/src/components/breadth/BreadthCharts.jsx`

**Step 1: Create the component**

Create `frontend/src/components/breadth/BreadthCharts.jsx`:

```jsx
import { useRef, useEffect } from 'react'
import { createChart, ColorType } from 'lightweight-charts'

export default function BreadthCharts({ data }) {
  if (!data?.history) return null

  return (
    <div className="space-y-3">
      <MaChart history={data.history} />
      <McClellanChart history={data.history} />
    </div>
  )
}

function MaChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !history?.dates?.length) return

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#78716c',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: '#f5f5f4' },
        horzLines: { color: '#f5f5f4' },
      },
      width: containerRef.current.clientWidth,
      height: 200,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
      crosshair: {
        horzLine: { visible: false, labelVisible: false },
      },
    })

    const dates = history.dates

    // % above 200 SMA (blue)
    const sma200Series = chart.addLineSeries({
      color: '#3b82f6',
      lineWidth: 1.5,
      title: '200 SMA',
    })
    sma200Series.setData(
      dates.map((d, i) => ({ time: d, value: history.pct_above_200sma[i] ?? 0 }))
    )

    // % above 50 SMA (amber)
    const sma50Series = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 1.5,
      title: '50 SMA',
    })
    sma50Series.setData(
      dates.map((d, i) => ({ time: d, value: history.pct_above_50sma[i] ?? 0 }))
    )

    // % above 20 SMA (stone)
    const sma20Series = chart.addLineSeries({
      color: '#a8a29e',
      lineWidth: 1,
      title: '20 SMA',
    })
    sma20Series.setData(
      dates.map((d, i) => ({ time: d, value: history.pct_above_20sma[i] ?? 0 }))
    )

    chart.timeScale().fitContent()
    chartRef.current = chart

    // Resize handler
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth })
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
  }, [history])

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-2">
        % Above Moving Averages — 100 Day
      </h3>
      <div ref={containerRef} />
    </div>
  )
}

function McClellanChart({ history }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current || !history?.dates?.length) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#78716c',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: '#f5f5f4' },
        horzLines: { color: '#f5f5f4' },
      },
      width: containerRef.current.clientWidth,
      height: 150,
      rightPriceScale: {
        borderVisible: false,
      },
      timeScale: {
        borderVisible: false,
      },
      crosshair: {
        horzLine: { visible: false, labelVisible: false },
      },
    })

    const dates = history.dates
    const mcData = dates.map((d, i) => {
      const val = history.mcclellan_osc[i] ?? 0
      return {
        time: d,
        value: val,
        color: val >= 0 ? '#22c55e' : '#ef4444',
      }
    })

    const mcSeries = chart.addHistogramSeries({
      title: 'McClellan',
    })
    mcSeries.setData(mcData)

    chart.timeScale().fitContent()
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth })
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
  }, [history])

  return (
    <div className="bg-white border border-stone-200 rounded px-3 py-3">
      <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500 mb-2">
        McClellan Oscillator — 100 Day
      </h3>
      <div ref={containerRef} />
    </div>
  )
}
```

**Step 2: Verify build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/breadth/BreadthCharts.jsx
git commit -m "feat: add BreadthCharts component with Lightweight Charts (Section 3)"
```

---

## Task 10: Create BreadthPage and wire into navigation

**Files:**
- Create: `frontend/src/components/breadth/BreadthPage.jsx`
- Modify: `frontend/src/components/Header.jsx:3-9`
- Modify: `frontend/src/components/Layout.jsx:9,60`

**Step 1: Create BreadthPage container**

Create `frontend/src/components/breadth/BreadthPage.jsx`:

```jsx
import MarketMonitor from './MarketMonitor'
import ClassicBreadth from './ClassicBreadth'
import BreadthCharts from './BreadthCharts'

export default function BreadthPage({ data }) {
  const breadth = data?.breadth

  if (!breadth) {
    return (
      <div className="text-stone-400 text-sm font-medium uppercase tracking-wide py-8 text-center">
        No breadth data available
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <MarketMonitor data={breadth} />
      <ClassicBreadth data={breadth} />
      <BreadthCharts data={breadth} />
    </div>
  )
}
```

**Step 2: Add to navigation**

In `frontend/src/components/Header.jsx`, add to NAV_ITEMS array (after line 8, the `briefing` entry):

```javascript
  { key: 'breadth', label: 'Breadth', hash: '#/breadth' },
```

**Step 3: Add to Layout routing**

In `frontend/src/components/Layout.jsx`, add import at line 10 (after BriefingPage):

```javascript
import BreadthPage from './breadth/BreadthPage'
```

Then in the routing section (after line 60, the `modelbooks` line), add:

```javascript
          {current === 'breadth' && <BreadthPage data={data} />}
```

**Step 4: Verify build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds

**Step 5: Commit**

```bash
git add frontend/src/components/breadth/BreadthPage.jsx frontend/src/components/Header.jsx frontend/src/components/Layout.jsx
git commit -m "feat: add Breadth page with navigation, wire up all 3 sections"
```

---

## Task 11: Create sample breadth.json for local dev

**Files:**
- Create: `data/output/breadth.json` (sample data for frontend dev)

**Step 1: Create sample data**

Create `data/output/breadth.json` with realistic sample data so the frontend can render without running the full pipeline:

```json
{
  "timestamp": "2026-03-16T00:00:00Z",
  "universe_size": 2485,
  "spx_close": 5638.94,
  "mm": {
    "up_4pct": 60,
    "down_4pct": 146,
    "ratio_5d": 0.3589,
    "ratio_10d": 0.4102,
    "up_25pct_qtr": 87,
    "down_25pct_qtr": 312,
    "up_25pct_month": 22,
    "down_25pct_month": 95,
    "up_50pct_month": 3,
    "down_50pct_month": 18
  },
  "breadth": {
    "t2108": 39.8,
    "pct_above_200sma": 58.3,
    "pct_above_50sma": 42.1,
    "pct_above_20sma": 35.6,
    "advances": 1420,
    "declines": 1065,
    "new_highs": 34,
    "new_lows": 89,
    "ad_line": 1842,
    "mcclellan_osc": -45.2
  },
  "history": {
    "dates": ["2026-03-16"],
    "pct_above_200sma": [58.3],
    "pct_above_50sma": [42.1],
    "pct_above_20sma": [35.6],
    "mcclellan_osc": [-45.2]
  }
}
```

**Step 2: Copy to frontend public dir (if applicable)**

Check if data is served from `frontend/public/data/output/` or from root `data/output/` (depends on vite config). If from public:

```bash
cp data/output/breadth.json frontend/public/data/output/breadth.json
```

**Step 3: Verify the app runs**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run dev`
Navigate to `#/breadth` in the browser. Verify all three sections render.

**Step 4: Commit**

```bash
git add data/output/breadth.json
git commit -m "chore: add sample breadth.json for local frontend development"
```

---

## Task 12: Run full pipeline test + build validation

**Step 1: Run all Python tests**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System && python -m pytest pipeline/tests/ -v`
Expected: All tests PASS

**Step 2: Run frontend build**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run build`
Expected: Build succeeds with no errors

**Step 3: Verify no lint errors**

Run: `cd /Users/taolezhu/Documents/AI-Trading-System/frontend && npm run lint`
Expected: No errors (warnings acceptable)

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Add sma40_dist to yfinance enrichment | `yfinance_adapter.py`, `run_all.py`, `test_adapters.py` |
| 2 | Add ^GSPC to fetch_ma_data | `yfinance_adapter.py`, `run_all.py` |
| 3 | Create breadth_metrics.py + tests | `breadth_metrics.py`, `test_breadth_metrics.py` |
| 4 | Integrate into run_all.py | `run_all.py` |
| 5 | Update GitHub Actions validation | `daily-data-update.yml` |
| 6 | Install Lightweight Charts + useMarketData | `package.json`, `useMarketData.js` |
| 7 | MarketMonitor component (Section 1) | `MarketMonitor.jsx` |
| 8 | ClassicBreadth component (Section 2) | `ClassicBreadth.jsx` |
| 9 | BreadthCharts component (Section 3) | `BreadthCharts.jsx` |
| 10 | BreadthPage + navigation wiring | `BreadthPage.jsx`, `Header.jsx`, `Layout.jsx` |
| 11 | Sample breadth.json for dev | `data/output/breadth.json` |
| 12 | Full test + build validation | None (verification only) |
