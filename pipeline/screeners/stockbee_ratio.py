"""Stockbee 5-day breadth ratio -- how many names are participating.

**What it looks for: the tape, not a stock.** Counts names up 4%+ against
names down 4%+ each session and takes a rolling 5-day ratio. Above 3.0 is a
thrust -- buying broad enough that it is not a handful of leaders carrying an
index. Below 0.5 is the same reading inverted.

This is the one screen here that is not a shortlist. Nothing in it is
tradeable; it is an input to the question of how much risk the environment
deserves, which is upstream of which name to buy.

**What it cannot tell you: which way.** A thrust says participation widened,
not that it continues -- thrusts occur at the start of advances and inside
bear-market rallies, and the reading is identical. It is also count-based, so
a 4% move in a $200M name and in a $200B name are one vote each; the ratio
describes the number of things moving, never the money behind them.

History is persisted to JSON so the trailing 5-day window survives across
daily runs.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from pipeline.marketcal import last_trading_day

import pandas as pd

logger = logging.getLogger(__name__)

# ── Thresholds ───────────────────────────────────────────────────────
_GAINER_PCT = 0.04    # 4 %
_LOSER_PCT = -0.04    # -4 %
_HISTORY_DAYS = 4     # load past 4 days (+ today = 5-day window)
_THRUST_RATIO = 3.0
_COLLAPSE_RATIO = 0.5


def _load_history(history_path: str) -> List[Dict[str, Any]]:
    """Load the most recent ``_HISTORY_DAYS`` entries from *history_path*.

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
        # Keep only the most recent entries we need
        return data[-_HISTORY_DAYS:]
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load history from %s: %s", history_path, exc)
        return []


def _save_history(
    history_path: str,
    history: List[Dict[str, Any]],
    today_entry: Dict[str, Any],
) -> None:
    """Append *today_entry* to *history* and persist to *history_path*.

    Only the most recent 30 days are retained to keep the file small.
    """
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    combined = history + [today_entry]
    # Keep a rolling 30-day archive
    combined = combined[-30:]

    try:
        path.write_text(json.dumps(combined, indent=2), encoding="utf-8")
        logger.info("Saved breadth history (%d entries) to %s", len(combined), history_path)
    except OSError as exc:
        logger.error("Failed to write history to %s: %s", history_path, exc)


def run(universe: pd.DataFrame, history_path: str) -> Dict[str, Any]:
    """Run the Stockbee 5-Day Ratio screener.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with at least ``change_pct``.
    history_path : str
        Path to the JSON file storing rolling daily gainer/loser counts.

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

    # Session label, not wall date — a weekend run files under the last
    # session rather than minting one. See marketcal.last_trading_day.
    today_entry = {
        "date": last_trading_day().isoformat(),
        "gainers": gainers_today,
        "losers": losers_today,
    }

    # --- Load past history ---
    history = _load_history(history_path)

    # --- Build the 5-day window (past history + today) ---
    window = history + [today_entry]
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
