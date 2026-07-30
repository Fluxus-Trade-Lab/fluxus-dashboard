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
