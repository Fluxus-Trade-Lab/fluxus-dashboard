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
_WINDOW_DAYS = 5      # trailing sessions used for the ratio
_ARCHIVE_DAYS = 30    # rolling archive kept on disk
_THRUST_RATIO = 3.0
_COLLAPSE_RATIO = 0.5


def _load_history(
    history_path: str,
    limit: Optional[int] = _WINDOW_DAYS,
) -> List[Dict[str, Any]]:
    """Load entries from *history_path*, most recent last.

    *limit* caps the result to the trailing N entries; pass ``None`` to get
    the full on-disk history (needed when rewriting the archive).

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
        if limit is None:
            return data
        # Keep only the most recent entries we need
        return data[-limit:]
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load history from %s: %s", history_path, exc)
        return []


def _upsert_entry(
    history: List[Dict[str, Any]],
    entry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Return *history* with *entry* replacing any same-date entry, else appended."""
    combined = [e for e in history if e.get("date") != entry["date"]]
    combined.append(entry)
    return combined


def _save_history(history_path: str, today_entry: Dict[str, Any]) -> None:
    """Upsert *today_entry* into the full on-disk history at *history_path*.

    The full archive is re-read here rather than reusing the trailing window
    the ratio is computed from — otherwise every run would rewrite the file
    with just that window and silently drop older entries.

    Only the most recent 30 days are retained to keep the file small.
    """
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    archive = _load_history(history_path, limit=None)
    combined = _upsert_entry(archive, today_entry)
    # Keep a rolling 30-day archive
    combined = combined[-_ARCHIVE_DAYS:]

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
        Session date to record today's counts under. Defaults to
        ``date.today()``; pin it in tests or backfills.

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

    # --- Load the trailing window of past sessions ---
    history = _load_history(history_path)

    # --- Build the 5-day window (past sessions + today) ---
    # Upsert so a same-day re-run replaces today's counts instead of double-counting.
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
    _save_history(history_path, today_entry)

    return {
        "ratio_5d": round(ratio_5d, 4),
        "gainers_today": gainers_today,
        "losers_today": losers_today,
        "gainers_5d": gainers_5d,
        "losers_5d": losers_5d,
        "signal": signal,
    }
