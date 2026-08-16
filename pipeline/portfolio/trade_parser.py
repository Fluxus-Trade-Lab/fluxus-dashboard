"""Parse the portfolio CSV export into typed Trade records.

CSV schema (header on row 3, two `_meta` rows above):
    Ticker, Direction, Sector, Entry Date, Entry Price, Original Qty,
    Current Qty, Stop Price, Initial Stop, Closed, Trim1 Date, Trim1 Price,
    Trim1 Qty, Trim1 Type, Trim2 Date, Trim2 Price, Trim2 Qty, Trim2 Type,
    Trim3 Date, Trim3 Price, Trim3 Qty, Trim3 Type

`Stop Price` is the *current/trailing* stop (used for "where would I be stopped now"
and live capital-at-risk). `Initial Stop` is the *locked-at-entry* stop and is the
denominator for every R-multiple calculation. The two values are equal at entry and
only diverge if the user trails the stop. Older CSVs without the `Initial Stop`
column backfill `initial_stop := stop_price`.

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
    """A single trade as recorded in the portfolio CSV.

    `stop_price` is the live/trailing stop. `initial_stop` is locked at entry and
    is the R-multiple denominator — it never moves once the position is opened.
    """
    ticker: str
    direction: str  # 'long' or 'short'
    sector: str
    entry_date: date
    entry_price: float
    original_qty: int
    current_qty: int
    stop_price: float       # current / trailing stop
    initial_stop: Optional[float]   # locked at entry — R denominator; None = unknown
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
    def R_dollars(self) -> Optional[float]:
        """Initial $ at risk = |entry - initial_stop| × original_qty.

        None when the entry stop is unknown. It used to be backfilled from the
        live stop, which is the one substitution that cannot be made here:
        Andy trails stops in the tracker, so by the time a trade is read the
        live stop is not the stop the position was sized against. Substituting
        it divides every R by the wrong number and leaves no trace, because the
        result still looks like an R. An absent R is a reading; a wrong one is
        not.
        """
        if self.initial_stop is None:
            return None
        return abs(self.entry_price - self.initial_stop) * self.original_qty

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
    def has_R(self) -> bool:
        """True when this trade has a usable R denominator.

        `R_dollars is not None and R_dollars > 0` appeared at six call sites
        the day initial_stop became optional, and a comparison that reads
        `R_dollars > 0` raises rather than returning False once None is
        possible — the kind of break that only shows up on the one book that
        has a blank stop. One definition, asked by name.
        """
        R = self.R_dollars
        return R is not None and R > 0

    @property
    def realized_R(self) -> Optional[float]:
        """Realized P/L in R-multiples; None when R is unknown or zero."""
        if not self.has_R:
            return None
        return self.realized_pl / self.R_dollars


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
    has_initial_stop_col = False
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
                has_initial_stop_col = any(
                    c.strip().lower() == 'initial stop' for c in header
                )
                if not has_initial_stop_col:
                    logger.info(
                        f"{path.name}: legacy CSV without 'Initial Stop' column — "
                        "backfilling initial_stop := stop_price for every row."
                    )
                continue
            try:
                trade = _row_to_trade(row, row_idx, has_initial_stop_col)
                if trade is not None:
                    trades.append(trade)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Row {row_idx}: skipping due to parse error: {e}")
    logger.info(f"Parsed {len(trades)} trades from {path}")
    return trades


def _row_to_trade(
    row: list[str],
    row_idx: int,
    has_initial_stop_col: bool = True,
) -> Optional[Trade]:
    """Parse one CSV row → Trade.

    If `has_initial_stop_col` is False (older CSV exports), the row is treated as
    the legacy 21-column layout (no `Initial Stop`) and `initial_stop` is
    backfilled from `stop_price`.
    """
    expected_cols = 22 if has_initial_stop_col else 21
    if len(row) < expected_cols:
        row = row + [''] * (expected_cols - len(row))

    ticker = row[0].strip()
    direction = row[1].strip().lower()
    sector = row[2].strip() or 'Unknown'
    entry_date = _parse_date(row[3])
    entry_price = _parse_float(row[4])
    original_qty = _parse_int(row[5])
    current_qty = _parse_int(row[6]) or 0
    stop_price = _parse_float(row[7])

    if has_initial_stop_col:
        initial_stop = _parse_float(row[8])
        closed_col = 9
        trim_base = 10
    else:
        initial_stop = None  # backfilled below
        closed_col = 8
        trim_base = 9

    closed = row[closed_col].strip().upper() == 'YES'

    if not ticker or entry_date is None or entry_price is None or original_qty is None:
        logger.warning(f"Row {row_idx}: missing required fields, skipping")
        return None
    if direction not in ('long', 'short'):
        logger.warning(f"Row {row_idx}: bad direction {direction!r}, skipping")
        return None

    trims: list[TrimEvent] = []
    for i in range(3):  # Trim1, Trim2, Trim3
        base = trim_base + i * 4
        d = _parse_date(row[base])
        p = _parse_float(row[base + 1])
        q = _parse_int(row[base + 2])
        t_type = row[base + 3].strip()
        if d and p is not None and q is not None and t_type:
            trims.append(TrimEvent(date=d, price=p, qty=q, type=t_type))

    final_stop = stop_price if stop_price is not None else entry_price * 0.95
    # No backfill. This used to read `initial_stop or final_stop`, which is
    # only correct while no stop has ever been trailed — and stops get trailed
    # in the tracker, so from the first trail onward it wrote a moved
    # denominator into that trade's R forever. Unknown stays unknown; the R
    # properties return None and every reader is expected to say so rather
    # than print a number it does not have. (Andy's call, 2026-08-17, agreeing
    # with the Apps Script, which stopped doing this first.)
    final_initial = initial_stop

    return Trade(
        ticker=ticker,
        direction=direction,
        sector=sector,
        entry_date=entry_date,
        entry_price=entry_price,
        original_qty=original_qty,
        current_qty=current_qty,
        stop_price=final_stop,
        initial_stop=final_initial,
        closed=closed,
        trims=tuple(trims),
    )


def find_latest_csv(folder: Path = Path('data/portfolio')) -> Optional[Path]:
    """Return the most-recent portfolio_*.csv in the designated folder."""
    candidates = sorted(folder.glob('portfolio_*.csv'), reverse=True)
    return candidates[0] if candidates else None
