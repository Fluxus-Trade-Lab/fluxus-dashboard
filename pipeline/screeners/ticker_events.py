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
