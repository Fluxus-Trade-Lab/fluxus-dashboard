"""Stockbee 5-Day Breadth Ratio Screener.

Counts stocks gaining >= 4 % and losing >= 4 % in a single session,
then computes a rolling 5-day ratio of gainers to losers.  A ratio
above 3.0 signals a breadth thrust; below 0.5 signals a collapse.

History is persisted in a JSON file so that the pipeline can compute
the trailing 5-day window across consecutive daily runs.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── Thresholds ───────────────────────────────────────────────────────
_GAINER_PCT = 0.04    # 4 %
_LOSER_PCT = -0.04    # -4 %
_WINDOW_DAYS = 5      # trailing sessions summed into the ratio
_THRUST_RATIO = 3.0
_COLLAPSE_RATIO = 0.5


def _upsert_entry(
    entries: List[Dict[str, Any]],
    entry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Insert or replace the entry for ``entry['date']``. Returns a sorted copy.

    Mirrors ``breadth_store.upsert_row``: one row per date, so re-running the
    pipeline within a session overwrites the day rather than duplicating it.
    """
    kept = [e for e in entries if e.get("date") != entry.get("date")]
    # ISO dates sort lexicographically, which is chronological.
    return sorted(kept + [entry], key=lambda e: e.get("date") or "")


def _load_history(history_path: str) -> List[Dict[str, Any]]:
    """Load the most recent ``_WINDOW_DAYS`` entries from *history_path*.

    Returns an empty list when the file is missing, empty, or corrupt.
    """
    path = Path(history_path)
    if not path.exists():
        logger.info("No history file at %s — starting fresh", history_path)
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            logger.warning("History file is not a list — ignoring")
            return []
        # Keep only the most recent entries we need. Load a full window rather
        # than window-minus-today: on a same-day re-run the last entry *is*
        # today, and it gets replaced instead of adding a session.
        return data[-_WINDOW_DAYS:]
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load history from %s: %s", history_path, exc)
        return []


def _save_history(
    history_path: str,
    history: List[Dict[str, Any]],
    today_entry: Dict[str, Any],
) -> None:
    """Upsert *today_entry* into *history* and persist to *history_path*.

    Only the most recent 30 days are retained to keep the file small.
    """
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    combined = _upsert_entry(history, today_entry)
    # Keep a rolling 30-day archive
    combined = combined[-30:]

    try:
        path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
        logger.info("Saved breadth history (%d entries) to %s", len(combined), history_path)
    except OSError as exc:
        logger.error("Failed to write history to %s: %s", history_path, exc)


def run(
    universe: pd.DataFrame,
    history_path: str,
    today: Optional[date] = None,
) -> Dict[str, Any]:
    """Run the Stockbee 5-Day Ratio screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``change_pct``.
    history_path : str
        Path to the JSON file storing rolling daily gainer/loser counts.
    today : datetime.date, optional
        Session to record the counts under. Defaults to the current date;
        pass it explicitly to pin a trading day (tests, replays, backfills).

    Returns
    -------
    dict
        ``{'ratio_5d': float, 'gainers_today': int, 'losers_today': int,
        'gainers_5d': int, 'losers_5d': int, 'signal': str}``
    """
    if universe.empty:
        logger.warning("Empty universe passed to stockbee_ratio screener")
        return {
            "ratio_5d": 0.0,
            "gainers_today": 0,
            "losers_today": 0,
            "gainers_5d": 0,
            "losers_5d": 0,
            "signal": "NEUTRAL",
        }

    # --- Count today's gainers and losers ---
    gainers_today = int((universe["change_pct"] >= _GAINER_PCT).sum())
    losers_today = int((universe["change_pct"] <= _LOSER_PCT).sum())

    today_entry = {
        "date": (today or date.today()).isoformat(),
        "gainers": gainers_today,
        "losers": losers_today,
    }

    # --- Load past history ---
    history = _load_history(history_path)

    # --- Build the 5-day window (past history + today) ---
    # Upsert, so a same-day re-run replaces today rather than counting it twice.
    window = _upsert_entry(history, today_entry)[-_WINDOW_DAYS:]
    gainers_5d = sum(entry["gainers"] for entry in window)
    losers_5d = sum(entry["losers"] for entry in window)

    # --- Calculate ratio (avoid division by zero) ---
    if losers_5d > 0:
        ratio_5d = gainers_5d / losers_5d
    else:
        ratio_5d = float(gainers_5d) if gainers_5d > 0 else 0.0

    # --- Determine signal ---
    if ratio_5d > _THRUST_RATIO:
        signal = "THRUST"
    elif ratio_5d < _COLLAPSE_RATIO:
        signal = "COLLAPSE"
    else:
        signal = "NEUTRAL"

    logger.info(
        "stockbee_ratio: today G=%d L=%d | 5d G=%d L=%d | ratio=%.2f → %s",
        gainers_today,
        losers_today,
        gainers_5d,
        losers_5d,
        ratio_5d,
        signal,
    )

    # --- Persist today's counts ---
    _save_history(history_path, history, today_entry)

    return {
        "ratio_5d": round(ratio_5d, 4),
        "gainers_today": gainers_today,
        "losers_today": losers_today,
        "gainers_5d": gainers_5d,
        "losers_5d": losers_5d,
        "signal": signal,
    }
