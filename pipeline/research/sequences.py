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
