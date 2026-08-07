"""Ticker event archive — which stocks appeared on which screener, when.

The daily cron commits every screener's JSON, so git history is a
point-in-time record of screener membership. This module turns any one of
those payloads into flat event rows; the backfill tool replays history
through it and run_all appends today's.

Pure functions only: no I/O, no clock. Malformed input yields zero rows.
Spec: docs/plans/2026-07-31-ticker-events-design.md
"""

from __future__ import annotations

import logging
import os
import statistics
import tempfile
from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

from pipeline.marketcal import is_trading_day

logger = logging.getLogger(__name__)

MIN_SCREENERS_PRESENT = 4      # of 7; <=3 reporting means a broken run
MIN_TOTAL_ROWS = 100           # healthy days run 350-1230; <100 is a broken run
MAX_MOMENTUM_97 = 1000         # a third of the universe cannot all be top-decile
MOMENTUM_MEDIAN_MULTIPLE = 5   # vs. the recent norm, when we have one
MOMENTUM_MEDIAN_WINDOW = 20    # days of history the norm is taken over
MOMENTUM_MEDIAN_MIN_DAYS = 5   # below this we have no usable norm

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


def is_plausible_day(rows: List[Dict[str, Any]],
                     momentum_median: float | None = None) -> Tuple[bool, str]:
    """Sniff-test one day's mined/appended rows. Pure.

    Catches the known failure signatures: a broken enrichment run that only
    a handful of screeners reported into, a day whose total row count
    collapsed (partial run), and a momentum_97 blowout where the "top
    decile" bucket swallowed a large slice of the universe.

    `momentum_median` is the recent norm for the momentum_97 count (e.g. a
    rolling median over accepted days). When supplied and positive it
    replaces the absolute ceiling with a relative one, which catches
    intermediate degradation the fixed 1000 ceiling waves through.
    """
    if not rows:
        return False, 'no rows'
    if len(rows) < MIN_TOTAL_ROWS:
        return False, f'only {len(rows)} rows total (< {MIN_TOTAL_ROWS})'
    screeners_present = {r['screener'] for r in rows if r.get('screener')}
    if len(screeners_present) < MIN_SCREENERS_PRESENT:
        return False, f'only {len(screeners_present)}/7 screeners reporting'
    momentum_count = sum(1 for r in rows if r.get('screener') == 'momentum_97')
    if momentum_median is not None and momentum_median > 0:
        ceiling = MOMENTUM_MEDIAN_MULTIPLE * momentum_median
        if momentum_count > ceiling:
            return False, (f'momentum_97 {momentum_count} > '
                           f'{MOMENTUM_MEDIAN_MULTIPLE}x recent median '
                           f'{momentum_median:g}')
    elif momentum_count > MAX_MOMENTUM_97:
        return False, f'momentum_97 {momentum_count} > 1000 (universe-wide)'
    return True, ''


def rolling_momentum_median(counts: 'Sequence[float]') -> float | None:
    """Recent norm for the daily momentum_97 count. Pure.

    Median over the last MOMENTUM_MEDIAN_WINDOW entries; None until we have
    at least MOMENTUM_MEDIAN_MIN_DAYS of history, because a norm drawn from
    one or two days is worse than no norm at all.
    """
    counts = list(counts)
    if len(counts) < MOMENTUM_MEDIAN_MIN_DAYS:
        return None
    return float(statistics.median(counts[-MOMENTUM_MEDIAN_WINDOW:]))


def is_session_date(date_iso: str, sessions: 'set[str] | None' = None) -> bool:
    """Was this date a real trading session? Pure, no clock, never raises.

    Primary test is the NYSE calendar (`marketcal.is_trading_day`): weekends
    and exchange holidays are rejected outright. This matters on the daily
    path, where today's date is always >= max(sessions) so the membership
    branch below can never fire — the cron runs on market holidays too.

    When `sessions` is a non-empty set and date_iso falls within its
    [min, max] range, membership is required as an *additional* constraint,
    catching ad-hoc closures the rule-based calendar doesn't model. Dates
    outside that range pass on the calendar alone.

    Anything unparseable is not a session.
    """
    try:
        year, month, day = (int(p) for p in date_iso.split('-'))
        day_date = _date(year, month, day)
    except (AttributeError, TypeError, ValueError):
        return False
    if not is_trading_day(day_date):
        return False
    if sessions:
        lo, hi = min(sessions), max(sessions)
        if lo <= date_iso <= hi:
            return date_iso in sessions
    return True


def load_sessions(csv_path: str) -> 'set[str]':
    """Verified trading-session dates from a breadth-archive-style CSV.

    Advisory input only: never raises. A missing or unreadable file just
    means we have no session calendar to cross-check against.
    """
    path = Path(csv_path)
    if not path.exists():
        return set()
    try:
        frame = pd.read_csv(path, usecols=['date'], dtype={'date': str})
    except Exception:  # noqa: BLE001 — advisory input, never fatal
        return set()
    return set(frame['date'].dropna())


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
