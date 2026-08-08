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

import random
import statistics
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


def _dedupe(instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse instances sharing a (ticker, signal_date) to the tightest one.

    Several leg-1 dates often funnel into the SAME confirmation date. The
    measured outcome is identical for all of them, so counting each one
    inflates `n` with copies of a single observation. We keep the smallest
    gap: the earliest-confirming, tightest version of the setup.
    """
    best: Dict[tuple, Dict[str, Any]] = {}
    for inst in instances:
        key = (inst['ticker'], inst['signal_date'])
        prev = best.get(key)
        if prev is None or inst['gap'] < prev['gap']:
            best[key] = inst
    out = list(best.values())
    out.sort(key=lambda r: (r['signal_date'], r['ticker']))
    return out


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
    return _dedupe(out)


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
    return _dedupe(out)


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
        out[f'win_rate_{h}'] = (round(sum(1 for v in excess if v > 0) / len(excess), 6)
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
