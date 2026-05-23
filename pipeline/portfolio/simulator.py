"""Single-trade simulation engine.

Given an entry, original position, stop, and a parameter set, walks daily OHLC
forward from entry and produces a realized R outcome.

State machine: PRE_TRIM → POST_T1 → POST_T2 → CLOSED.

Pre-trim phase always uses the trade's CSV stop (we don't optimize the initial
tight stop — that's user-set). The grid optimizes what happens AFTER Trim 1
fires: trim sizes, trailing rules, gain ratchet, sell-into-strength layer.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from pipeline.portfolio.trade_parser import Trade

logger = logging.getLogger(__name__)


# ── parameter dataclass ────────────────────────────────────────────────────

@dataclass(frozen=True)
class SimParams:
    trim1_trigger_R: float          # e.g., 2.0, 2.5, 3.0
    trim1_size_pct: float           # 0.30 .. 0.70 of original_qty
    trim2_signal: str               # 'd_close_lt_10ema' | 'wk_close_lt_10ema' | 'd_close_lt_13ema' | 'd_close_lt_5d_low'
    trim2_size_pct: float           # 0.5 .. 1.0 of remaining at entry to POST_T1
    full_stop_signal: str           # 'd_close_lt_20ema' | 'wk_close_lt_20ema' | 'd_close_lt_30ema' | 'trailing_2atr'
    gain_ratchet: str               # 'none' | '5R_to_3R' | '8R_to_5R'
    sell_strength: str              # 'none' | 'trim_30_on_15pct' | 'trim_50_on_20pct'


# ── derived series helpers ─────────────────────────────────────────────────

def _compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMAs, ATR, 5-day low to a daily-OHLC DataFrame. Returns new DF."""
    out = df.copy()
    close = out['Close']
    out['ema10'] = close.ewm(span=10, adjust=False).mean()
    out['ema13'] = close.ewm(span=13, adjust=False).mean()
    out['ema20'] = close.ewm(span=20, adjust=False).mean()
    out['ema21'] = close.ewm(span=21, adjust=False).mean()
    out['ema30'] = close.ewm(span=30, adjust=False).mean()

    # Weekly closes resampled back to daily for "weekly close < EMA" rule
    weekly_close = close.resample('W-FRI').last()
    weekly_ema10 = weekly_close.ewm(span=10, adjust=False).mean()
    weekly_ema20 = weekly_close.ewm(span=20, adjust=False).mean()
    # broadcast weekly value back to each day of that week
    out['wk_close'] = weekly_close.reindex(out.index, method='ffill')
    out['wk_ema10'] = weekly_ema10.reindex(out.index, method='ffill')
    out['wk_ema20'] = weekly_ema20.reindex(out.index, method='ffill')

    # 14-day ATR (true range)
    tr1 = out['High'] - out['Low']
    tr2 = (out['High'] - close.shift(1)).abs()
    tr3 = (out['Low'] - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    out['atr14'] = tr.rolling(14, min_periods=1).mean()

    # 5-day rolling low
    out['low_5d'] = out['Low'].rolling(5, min_periods=1).min()
    return out


# ── single-trade simulation ────────────────────────────────────────────────

def prep_bars(trade: Trade, ohlc: pd.DataFrame) -> Optional[np.ndarray]:
    """Pre-compute indicators and return the numpy array of bars from entry forward.

    Returned shape: (n_bars, 13) — columns Open, High, Low, Close, ema10, ema13,
    ema20, ema30, wk_close, wk_ema10, wk_ema20, atr14, low_5d.
    Returns None if the trade can't be simulated.
    """
    if trade.R_dollars <= 0:
        return None
    if ohlc is None or len(ohlc) < 5:
        return None
    entry_ts = pd.Timestamp(trade.entry_date)
    df = _compute_indicators(ohlc)
    df = df[df.index >= entry_ts]
    if len(df) < 2:
        return None
    return df[['Open', 'High', 'Low', 'Close',
               'ema10', 'ema13', 'ema20', 'ema30',
               'wk_close', 'wk_ema10', 'wk_ema20',
               'atr14', 'low_5d']].values


def simulate(trade: Trade, ohlc: pd.DataFrame, p: SimParams) -> Optional[float]:
    """Return the realized R-multiple for `trade` under params `p`.

    Returns None if the simulation could not be run (missing data, zero R).
    """
    bars = prep_bars(trade, ohlc)
    if bars is None:
        return None
    return _simulate_from_bars(trade, bars, p)


def _simulate_from_bars(trade: Trade, bars: np.ndarray, p: SimParams) -> float:
    """Inner sim loop on a pre-prepped numpy bars array."""
    direction = 1 if trade.direction == 'long' else -1
    entry_price = trade.entry_price
    stop_price = trade.stop_price
    original_qty = trade.original_qty
    R = trade.R_dollars

    # state
    state = 'PRE_TRIM'
    qty_remaining = original_qty
    pl_realized = 0.0
    ratchet_armed = False
    ratchet_floor_R = None
    strength_done = False

    # parse trim1 size, trim2 size
    trim1_qty = int(round(original_qty * p.trim1_size_pct))
    # qty after trim1 will be (original - trim1_qty)
    # trim2 size is % of THAT remaining (per spec)
    # gain ratchet thresholds
    ratchet_hi_R, ratchet_floor_R_target = {
        'none': (None, None),
        '5R_to_3R': (5.0, 3.0),
        '8R_to_5R': (8.0, 5.0),
    }[p.gain_ratchet]
    # sell-strength config
    if p.sell_strength == 'none':
        strength_pct = None
        strength_trim_pct = 0.0
    elif p.sell_strength == 'trim_30_on_15pct':
        strength_pct = 0.15
        strength_trim_pct = 0.30
    elif p.sell_strength == 'trim_50_on_20pct':
        strength_pct = 0.20
        strength_trim_pct = 0.50
    else:
        strength_pct = None
        strength_trim_pct = 0.0

    n = len(bars)

    def _exit(qty: int, price: float) -> None:
        nonlocal pl_realized, qty_remaining
        pl_realized += direction * (price - entry_price) * qty
        qty_remaining -= qty

    # bars[i] = [Open, High, Low, Close, ema10, ema13, ema20, ema30,
    #            wk_close, wk_ema10, wk_ema20, atr14, low_5d]
    # We start iterating from bar 1 (entry day is bar 0; no actions taken there).
    for i in range(1, n):
        if qty_remaining <= 0:
            break

        bar = bars[i]
        o, h, l, c = bar[0], bar[1], bar[2], bar[3]
        ema10, ema13, ema20, ema30 = bar[4], bar[5], bar[6], bar[7]
        wk_close, wk_ema10, wk_ema20 = bar[8], bar[9], bar[10]
        atr14 = bar[11]
        low_5d = bar[12]

        # ── PRE_TRIM ─────────────────────────────────────────────────────────
        if state == 'PRE_TRIM':
            # check initial stop (CSV stop) first
            if direction == 1 and l <= stop_price:
                _exit(qty_remaining, stop_price)
                break
            if direction == -1 and h >= stop_price:
                _exit(qty_remaining, stop_price)
                break
            # check trim1 trigger
            trigger_price = entry_price + direction * (p.trim1_trigger_R * R / original_qty)
            hit = (direction == 1 and h >= trigger_price) or (direction == -1 and l <= trigger_price)
            if hit:
                # execute trim1 at trigger price
                actual_qty = min(trim1_qty, qty_remaining)
                _exit(actual_qty, trigger_price)
                state = 'POST_T1'
                stop_price = entry_price  # breakeven
            continue

        # ── POST_T1 / POST_T2 ────────────────────────────────────────────────
        # 1) check breakeven / trailing stop first (covers full_stop_signal)
        # 2) check sell-strength
        # 3) check gain ratchet
        # 4) check trim-2 signal (only in POST_T1)

        # Determine full-stop trigger
        stop_triggered = False
        # breakeven (we set stop_price = entry on POST_T1)
        if direction == 1 and l <= stop_price:
            stop_triggered = True
            exit_at = stop_price
        elif direction == -1 and h >= stop_price:
            stop_triggered = True
            exit_at = stop_price

        # custom full_stop_signal — confirmed on prior bar's CLOSE, exit at this bar's OPEN
        if not stop_triggered and i >= 1:
            prev = bars[i - 1]
            prev_c = prev[3]
            prev_ema20 = prev[6]
            prev_ema30 = prev[7]
            prev_wk_close = prev[8]
            prev_wk_ema20 = prev[10]
            prev_atr14 = prev[11]
            fired = False
            if p.full_stop_signal == 'd_close_lt_20ema':
                fired = (direction == 1 and prev_c < prev_ema20) or (direction == -1 and prev_c > prev_ema20)
            elif p.full_stop_signal == 'wk_close_lt_20ema':
                fired = (direction == 1 and prev_wk_close < prev_wk_ema20) or (direction == -1 and prev_wk_close > prev_wk_ema20)
            elif p.full_stop_signal == 'd_close_lt_30ema':
                fired = (direction == 1 and prev_c < prev_ema30) or (direction == -1 and prev_c > prev_ema30)
            elif p.full_stop_signal == 'trailing_2atr':
                # 2 ATR below prior close for longs
                trail = prev_c - direction * 2 * prev_atr14
                fired = (direction == 1 and prev_c < trail) or False  # always false by construction; use as floor
                # better: stop is trail; exit if current low <= trail
                if direction == 1 and l <= trail:
                    stop_triggered = True
                    exit_at = trail
                elif direction == -1 and h >= trail:
                    stop_triggered = True
                    exit_at = trail
            if fired and not stop_triggered:
                stop_triggered = True
                exit_at = o

        if stop_triggered:
            _exit(qty_remaining, exit_at)
            break

        # 2) sell-into-strength layer (only fires once)
        if not strength_done and strength_pct is not None:
            move_from_entry = direction * (c - entry_price) / entry_price
            if move_from_entry >= strength_pct:
                qty_to_trim = int(round(qty_remaining * strength_trim_pct))
                if qty_to_trim > 0:
                    _exit(qty_to_trim, c)
                    strength_done = True

        # 3) gain ratchet
        if ratchet_hi_R is not None:
            current_R = direction * (c - entry_price) * original_qty / R
            if not ratchet_armed and current_R >= ratchet_hi_R:
                ratchet_armed = True
            if ratchet_armed and current_R < ratchet_floor_R_target:
                # exit residual on next-day open
                if i + 1 < n:
                    _exit(qty_remaining, bars[i + 1][0])
                else:
                    _exit(qty_remaining, c)
                break

        # 4) trim-2 signal (only fires in POST_T1)
        if state == 'POST_T1' and qty_remaining > 0:
            t2_fire = False
            if p.trim2_signal == 'd_close_lt_10ema':
                t2_fire = (direction == 1 and c < ema10) or (direction == -1 and c > ema10)
            elif p.trim2_signal == 'wk_close_lt_10ema':
                t2_fire = (direction == 1 and wk_close < wk_ema10) or (direction == -1 and wk_close > wk_ema10)
            elif p.trim2_signal == 'd_close_lt_13ema':
                t2_fire = (direction == 1 and c < ema13) or (direction == -1 and c > ema13)
            elif p.trim2_signal == 'd_close_lt_5d_low':
                t2_fire = (direction == 1 and c < low_5d) or (direction == -1 and c > low_5d)
            if t2_fire and i + 1 < n:
                trim2_qty = int(round(qty_remaining * p.trim2_size_pct))
                if trim2_qty > 0:
                    _exit(trim2_qty, bars[i + 1][0])
                state = 'POST_T2'

    # if we exited the loop with shares still held, close at the last bar's close
    if qty_remaining > 0:
        _exit(qty_remaining, bars[-1][3])

    return pl_realized / R


def attach_indicators(ohlc: pd.DataFrame) -> pd.DataFrame:
    """Public helper — used by reporter for inspection."""
    return _compute_indicators(ohlc)
