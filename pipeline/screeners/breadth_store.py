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

import datetime as dt
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


def derive(frame: pd.DataFrame) -> pd.DataFrame:
    """Recompute all derived series over the full frame. Pure — no I/O, no clock."""
    out = frame.copy()
    if len(out) == 0:
        return out
    adv = pd.to_numeric(out['advances'], errors='coerce').fillna(0)
    dec = pd.to_numeric(out['declines'], errors='coerce').fillna(0)
    up4 = pd.to_numeric(out['up_4pct'], errors='coerce').fillna(0)
    down4 = pd.to_numeric(out['down_4pct'], errors='coerce').fillna(0)

    net = adv - dec
    out['net_advances'] = net.astype(int)

    total = adv + dec
    rana = pd.Series(0.0, index=out.index)
    nonzero = total > 0
    rana[nonzero] = (net[nonzero] / total[nonzero]) * 1000
    out['rana'] = rana.round(2)

    ema19 = rana.ewm(span=19, adjust=False).mean()
    ema39 = rana.ewm(span=39, adjust=False).mean()
    out['mcclellan_osc'] = (ema19 - ema39).round(2)

    out['ad_line'] = net.cumsum().astype(int)

    for n, col in ((5, 'ratio_5d'), (10, 'ratio_10d')):
        up_sum = up4.rolling(n, min_periods=1).sum()
        down_sum = down4.rolling(n, min_periods=1).sum()
        # Divide where the down-sum is positive; else fall back to the up-sum
        # (mirrors the legacy compute_ratios zero-division behavior).
        ratio = (up_sum / down_sum).where(down_sum > 0, up_sum)
        out[col] = ratio.astype(float).round(4)
    return out


def upsert_row(frame: pd.DataFrame, row: dict) -> pd.DataFrame:
    """Insert or replace the row for row['date']. Returns a sorted copy."""
    kept = frame[frame['date'] != row['date']]
    new = pd.DataFrame([{col: row.get(col, pd.NA) for col in BREADTH_COLUMNS}])
    out = pd.concat([kept, new], ignore_index=True)
    return out.sort_values('date').reset_index(drop=True)


def write_archive(frame: pd.DataFrame, csv_path: str) -> None:
    """Atomically write the archive: temp file in the same dir, then rename."""
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frame[BREADTH_COLUMNS]
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix='.csv.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            out.to_csv(f, index=False)
        os.replace(tmp_name, path)
        os.chmod(path, 0o644)  # mkstemp creates 0600; the archive is public data
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    logger.info("Wrote breadth archive (%d rows) to %s", len(out), csv_path)


# ── Quality guard thresholds (see design doc §4) ─────────────────────
_MIN_UNIVERSE = 1500
_MAX_NULL_RATE = 0.20
_MAX_PCT200_JUMP = 25.0
# The Δ-check compares against the archive tail, so a bad tail can wedge the
# guard shut forever. Skip it when the baseline cannot be trusted: the previous
# row is itself implausible, or it is too stale for a one-day jump limit.
_IMPLAUSIBLE_PREV_PCT200 = 5.0
_MAX_PREV_ROW_AGE_DAYS = 7


def _iso_to_date(value) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def check_quality(
    frame: pd.DataFrame,
    snapshot: dict,
    null_rate: float,
    today_iso: str,
) -> tuple[bool, str]:
    """Reject implausible snapshots before they poison the archive.

    ``today_iso`` is the candidate row's market date (ET, from marketcal) — it
    is only used to age the Δ-check baseline, never as a clock.
    """
    size = snapshot.get('universe_size', 0)
    if size < _MIN_UNIVERSE:
        return False, f"universe_size {size} < {_MIN_UNIVERSE}"
    if null_rate > _MAX_NULL_RATE:
        return False, f"sma200_dist null rate {null_rate:.0%} > {_MAX_NULL_RATE:.0%}"
    if len(frame) > 0:
        prev = pd.to_numeric(frame['pct_above_200sma'], errors='coerce').iloc[-1]
        cur = snapshot.get('pct_above_200sma')

        skip = None
        if pd.notna(prev) and float(prev) < _IMPLAUSIBLE_PREV_PCT200:
            skip = (f"previous row pct_above_200sma {float(prev):.1f} is itself "
                    f"implausible (< {_IMPLAUSIBLE_PREV_PCT200})")
        else:
            prev_date = _iso_to_date(frame['date'].iloc[-1])
            today = _iso_to_date(today_iso)
            if prev_date is not None and today is not None:
                age = (today - prev_date).days
                if age > _MAX_PREV_ROW_AGE_DAYS:
                    skip = (f"previous row {prev_date.isoformat()} is {age} calendar "
                            f"days stale (> {_MAX_PREV_ROW_AGE_DAYS})")

        if skip is not None:
            logger.warning("Breadth Δ-check skipped: %s", skip)
        elif pd.notna(prev) and cur is not None and abs(cur - float(prev)) > _MAX_PCT200_JUMP:
            return False, (f"pct_above_200sma jumped {float(prev):.1f} -> {cur:.1f} "
                           f"(> {_MAX_PCT200_JUMP} pts)")
    return True, ''
