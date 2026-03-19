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
    """Append today's entry and save rolling history.

    If today's date already exists in history, replace it (idempotent).
    """
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    today_date = today_entry.get('date')
    # Remove any existing entry for today (idempotent re-runs)
    deduped = [e for e in history if e.get('date') != today_date]
    combined = deduped + [today_entry]
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

    # 8. Build history for frontend (chart arrays + full rows for table)
    # Deduplicate by date (today_entry replaces any existing same-date entry)
    seen_dates = set()
    all_entries = []
    for e in history + [today_entry]:
        d = e.get('date')
        if d not in seen_dates:
            seen_dates.add(d)
            all_entries.append(e)
    history_output = {
        # Chart arrays (used by BreadthCharts.jsx)
        'dates': [e['date'] for e in all_entries],
        'pct_above_200sma': [e.get('pct_above_200sma', 0) for e in all_entries],
        'pct_above_50sma': [e.get('pct_above_50sma', 0) for e in all_entries],
        'pct_above_20sma': [e.get('pct_above_20sma', 0) for e in all_entries],
        'mcclellan_osc': [e.get('mcclellan_osc', 0) for e in all_entries],
        # Full rows (used by BreadthTable.jsx)
        'rows': all_entries,
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
        'history': history_output,
    }
