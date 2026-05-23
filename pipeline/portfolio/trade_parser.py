"""Parse the portfolio CSV export into typed Trade records.

CSV schema (header on row 3, two `_meta` rows above):
    Ticker, Direction, Sector, Entry Date, Entry Price, Original Qty,
    Current Qty, Stop Price, Closed, Trim1 Date, Trim1 Price, Trim1 Qty,
    Trim1 Type, Trim2 Date, Trim2 Price, Trim2 Qty, Trim2 Type,
    Trim3 Date, Trim3 Price, Trim3 Qty, Trim3 Type

Trim Type vocabulary:
    trim_1_2  = sell ½ of original position
    trim_1_3  = sell ⅓ of original position
    trim_1_5  = sell ⅕ of original position
    sell_rest = exit all remaining shares
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrimEvent:
    date: date
    price: float
    qty: int
    type: str  # 'trim_1_2', 'trim_1_3', 'trim_1_5', 'sell_rest'


@dataclass(frozen=True)
class Trade:
    """A single trade as recorded in the portfolio CSV."""
    ticker: str
    direction: str  # 'long' or 'short'
    sector: str
    entry_date: date
    entry_price: float
    original_qty: int
    current_qty: int
    stop_price: float
    closed: bool
    trims: tuple[TrimEvent, ...] = field(default_factory=tuple)

    @property
    def exit_date(self) -> Optional[date]:
        """Date the position was fully closed; None if still open."""
        if not self.closed or not self.trims:
            return None
        return max(t.date for t in self.trims)

    @property
    def hold_business_days(self) -> Optional[int]:
        """Business days between entry and final exit; None if still open."""
        ex = self.exit_date
        if ex is None:
            return None
        # naive business-day count: subtract whole weeks * 5 + same-week offset
        # close enough for archetype bucketing — not used for compounding
        days = (ex - self.entry_date).days
        whole_weeks = days // 7
        offset = days % 7
        # business days in the offset (Mon=0 .. Sun=6)
        entry_weekday = self.entry_date.weekday()
        biz_offset = sum(1 for i in range(1, offset + 1)
                         if (entry_weekday + i) % 7 < 5)
        return whole_weeks * 5 + biz_offset

    @property
    def R_dollars(self) -> float:
        """Initial $ at risk = |entry - stop| × original_qty."""
        return abs(self.entry_price - self.stop_price) * self.original_qty

    @property
    def has_multiday_trims(self) -> bool:
        """True iff trims fall on ≥2 distinct dates (true two-leg trade)."""
        return len({t.date for t in self.trims}) >= 2

    @property
    def realized_pl(self) -> float:
        """Sum of realized P/L across all trims, signed for direction."""
        sign = 1.0 if self.direction == 'long' else -1.0
        return sum(sign * (t.price - self.entry_price) * t.qty for t in self.trims)

    @property
    def realized_R(self) -> Optional[float]:
        """Realized P/L expressed in R-multiples; None if R was 0 (no stop)."""
        R = self.R_dollars
        if R <= 0:
            return None
        return self.realized_pl / R


def _parse_date(s: str) -> Optional[date]:
    """Parse an ISO datetime string like '2026-01-05T15:00:00.000Z' → date."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    # The CSV uses '2026-01-05T15:00:00.000Z' or '2026-01-05' for trim dates
    for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    logger.warning(f"Could not parse date: {s!r}")
    return None


def _parse_float(s: str) -> Optional[float]:
    if not s or not s.strip():
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_int(s: str) -> Optional[int]:
    if not s or not s.strip():
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_csv(path: Path) -> list[Trade]:
    """Parse the portfolio export CSV into Trade records.

    Skips meta rows at the top (rows starting with `_meta`).
    Logs a warning and skips any row that can't be parsed.
    """
    trades: list[Trade] = []
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = None
        for row_idx, row in enumerate(reader, start=1):
            if not row:
                continue
            if row[0].startswith('_meta'):
                continue
            if header is None:
                header = row
                continue
            try:
                trade = _row_to_trade(row, row_idx)
                if trade is not None:
                    trades.append(trade)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Row {row_idx}: skipping due to parse error: {e}")
    logger.info(f"Parsed {len(trades)} trades from {path}")
    return trades


def _row_to_trade(row: list[str], row_idx: int) -> Optional[Trade]:
    # 21 columns expected
    if len(row) < 21:
        # pad with empties if the writer dropped trailing commas
        row = row + [''] * (21 - len(row))
    ticker = row[0].strip()
    direction = row[1].strip().lower()
    sector = row[2].strip() or 'Unknown'
    entry_date = _parse_date(row[3])
    entry_price = _parse_float(row[4])
    original_qty = _parse_int(row[5])
    current_qty = _parse_int(row[6]) or 0
    stop_price = _parse_float(row[7])
    closed = row[8].strip().upper() == 'YES'

    if not ticker or entry_date is None or entry_price is None or original_qty is None:
        logger.warning(f"Row {row_idx}: missing required fields, skipping")
        return None
    if direction not in ('long', 'short'):
        logger.warning(f"Row {row_idx}: bad direction {direction!r}, skipping")
        return None

    trims: list[TrimEvent] = []
    for i in range(3):  # Trim1, Trim2, Trim3
        base = 9 + i * 4
        d = _parse_date(row[base])
        p = _parse_float(row[base + 1])
        q = _parse_int(row[base + 2])
        t_type = row[base + 3].strip()
        if d and p is not None and q is not None and t_type:
            trims.append(TrimEvent(date=d, price=p, qty=q, type=t_type))

    return Trade(
        ticker=ticker,
        direction=direction,
        sector=sector,
        entry_date=entry_date,
        entry_price=entry_price,
        original_qty=original_qty,
        current_qty=current_qty,
        stop_price=stop_price if stop_price is not None else entry_price * 0.95,
        closed=closed,
        trims=tuple(trims),
    )


def find_latest_csv(folder: Path = Path('data/portfolio')) -> Optional[Path]:
    """Return the most-recent portfolio_*.csv in the designated folder."""
    candidates = sorted(folder.glob('portfolio_*.csv'), reverse=True)
    return candidates[0] if candidates else None
