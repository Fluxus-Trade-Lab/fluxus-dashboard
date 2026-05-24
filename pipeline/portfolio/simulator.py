"""Single-trade simulation engine — v2 with R-target trim ladder.

Given an entry, original position, stop, and a parameter set, walks daily OHLC
forward from entry and produces a realized R outcome.

State machine: PRE_TRIM → POST_T1 → POST_T2 → POST_T3 → CLOSED.

Pre-trim phase always uses the trade's CSV stop (we don't optimize the initial
tight stop — that's user-set). The grid optimizes what happens AFTER Trim 1
fires: trim sizes, trim triggers (signal OR R-target), full stop, gain ratchet.
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
    trim2_trigger: str              # signal: 'd_close_lt_10ema' | 'wk_close_lt_10ema' | 'd_close_lt_5d_low'
                                    # or R-target: 'r_5' | 'r_6' | 'r_8'
    trim2_size_pct: float           # 0.30 .. 0.70 of remaining at entry to POST_T1
    trim3_trigger: str              # 'none' | 'r_8' | 'r_10' | 'r_12' (R-target only)
    trim3_size_pct: float           # 0.50 .. 1.0 of remaining at entry to POST_T2
    full_stop_signal: str           # 'd_close_lt_20ema' | 'wk_close_lt_20ema' | 'd_close_lt_30ema' | 'trailing_2atr'
    gain_ratchet: str               # 'none' | '5R_to_3R' | '8R_to_5R'


def _is_r_trigger(s: str) -> Optional[float]:
    """Return the R multiple if s is an R-target trigger, else None."""
    if s.startswith('r_'):
        try:
            return float(s[2:])
        except ValueError:
            return None
    return None


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

    Returned shape: (n_bars, 13) — columns:
        0 Open  1 High  2 Low  3 Close
        4 ema10  5 ema13  6 ema20  7 ema30
        8 wk_close  9 wk_ema10  10 wk_ema20
        11 atr14  12 low_5d
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
    R_per_share = R / original_qty

    # state
    state = 'PRE_TRIM'
    qty_remaining = original_qty
    pl_realized = 0.0
    ratchet_armed = False

    trim1_qty = int(round(original_qty * p.trim1_size_pct))

    # T2 trigger config
    t2_R_mult = _is_r_trigger(p.trim2_trigger)  # float or None
    # T3 trigger config
    t3_R_mult = _is_r_trigger(p.trim3_trigger) if p.trim3_trigger != 'none' else None

    # ratchet thresholds
    ratchet_hi_R, ratchet_floor_R = {
        'none': (None, None),
        '5R_to_3R': (5.0, 3.0),
        '8R_to_5R': (8.0, 5.0),
    }[p.gain_ratchet]

    n = len(bars)

    def _exit(qty: int, price: float) -> None:
        nonlocal pl_realized, qty_remaining
        pl_realized += direction * (price - entry_price) * qty
        qty_remaining -= qty

    # iterate from bar 1 (entry day = bar 0, no actions taken there)
    for i in range(1, n):
        if qty_remaining <= 0:
            break

        bar = bars[i]
        o, h, l, c = bar[0], bar[1], bar[2], bar[3]
        ema10 = bar[4]
        ema20, ema30 = bar[6], bar[7]
        wk_close, wk_ema10, wk_ema20 = bar[8], bar[9], bar[10]
        low_5d = bar[12]

        # ── PRE_TRIM ─────────────────────────────────────────────────────────
        if state == 'PRE_TRIM':
            # initial CSV stop check — CLOSE-based (user's actual practice;
            # avoids wicking out on intraday spikes on high-ATR names).
            # If close violates, exit at next-day open. If the gap-open itself
            # is past the stop, that's the exit price (worst-case execution).
            stop_hit = (
                (direction == 1 and c <= stop_price) or
                (direction == -1 and c >= stop_price)
            )
            if stop_hit:
                if i + 1 < n:
                    next_open = bars[i + 1][0]
                    # if gap open is past stop, use that; else use stop
                    if direction == 1:
                        exit_at = min(next_open, stop_price)
                    else:
                        exit_at = max(next_open, stop_price)
                else:
                    exit_at = c
                _exit(qty_remaining, exit_at); break
            # trim1 trigger (R-target only — Trim 1 always uses R)
            trigger_price = entry_price + direction * (p.trim1_trigger_R * R_per_share)
            hit = (direction == 1 and h >= trigger_price) or (direction == -1 and l <= trigger_price)
            if hit:
                actual_qty = min(trim1_qty, qty_remaining)
                _exit(actual_qty, trigger_price)
                state = 'POST_T1'
                stop_price = entry_price  # breakeven
            continue

        # ── POST_T1 / POST_T2 ────────────────────────────────────────────────
        # Order: 1) hard stop check, 2) full-stop signal, 3) gain ratchet,
        #        4) T3 R-target (POST_T2 only), 5) T2 trigger (POST_T1 only)

        # 1) hard stop — also CLOSE-based now (breakeven stop post-T1).
        # Exit at next-day open, capped to actual gap.
        stop_triggered = False
        exit_at = None
        if (direction == 1 and c <= stop_price) or (direction == -1 and c >= stop_price):
            stop_triggered = True
            if i + 1 < n:
                next_open = bars[i + 1][0]
                if direction == 1:
                    exit_at = min(next_open, stop_price)
                else:
                    exit_at = max(next_open, stop_price)
            else:
                exit_at = c

        # 2) full-stop signal — confirmed on prior bar's CLOSE, exit at this bar's OPEN
        if not stop_triggered:
            prev = bars[i - 1]
            prev_c = prev[3]
            prev_ema20 = prev[6]; prev_ema30 = prev[7]
            prev_wk_close = prev[8]; prev_wk_ema20 = prev[10]
            prev_atr14 = prev[11]
            fired = False
            if p.full_stop_signal == 'd_close_lt_20ema':
                fired = (direction == 1 and prev_c < prev_ema20) or (direction == -1 and prev_c > prev_ema20)
            elif p.full_stop_signal == 'wk_close_lt_20ema':
                fired = (direction == 1 and prev_wk_close < prev_wk_ema20) or (direction == -1 and prev_wk_close > prev_wk_ema20)
            elif p.full_stop_signal == 'd_close_lt_30ema':
                fired = (direction == 1 and prev_c < prev_ema30) or (direction == -1 and prev_c > prev_ema30)
            elif p.full_stop_signal == 'trailing_2atr':
                trail = prev_c - direction * 2 * prev_atr14
                if direction == 1 and l <= trail:
                    stop_triggered = True; exit_at = trail
                elif direction == -1 and h >= trail:
                    stop_triggered = True; exit_at = trail
            if fired and not stop_triggered:
                stop_triggered = True; exit_at = o

        if stop_triggered:
            _exit(qty_remaining, exit_at)
            break

        # 3) gain ratchet
        if ratchet_hi_R is not None:
            current_R = direction * (c - entry_price) * original_qty / R
            if not ratchet_armed and current_R >= ratchet_hi_R:
                ratchet_armed = True
            if ratchet_armed and current_R < ratchet_floor_R:
                if i + 1 < n:
                    _exit(qty_remaining, bars[i + 1][0])
                else:
                    _exit(qty_remaining, c)
                break

        # 4) T3 R-target (only in POST_T2)
        if state == 'POST_T2' and t3_R_mult is not None and qty_remaining > 0:
            t3_price = entry_price + direction * (t3_R_mult * R_per_share)
            t3_hit = (direction == 1 and h >= t3_price) or (direction == -1 and l <= t3_price)
            if t3_hit:
                t3_qty = int(round(qty_remaining * p.trim3_size_pct))
                if t3_qty > 0:
                    _exit(t3_qty, t3_price)
                continue

        # 5) T2 trigger (only in POST_T1)
        if state == 'POST_T1' and qty_remaining > 0:
            t2_fire = False
            t2_price = None
            if t2_R_mult is not None:
                t2_target = entry_price + direction * (t2_R_mult * R_per_share)
                t2_fire = (direction == 1 and h >= t2_target) or (direction == -1 and l <= t2_target)
                t2_price = t2_target
            else:
                # signal-based — confirmed on this bar's close, execute next-day open
                if p.trim2_trigger == 'd_close_lt_10ema':
                    t2_fire = (direction == 1 and c < ema10) or (direction == -1 and c > ema10)
                elif p.trim2_trigger == 'wk_close_lt_10ema':
                    t2_fire = (direction == 1 and wk_close < wk_ema10) or (direction == -1 and wk_close > wk_ema10)
                elif p.trim2_trigger == 'd_close_lt_5d_low':
                    t2_fire = (direction == 1 and c < low_5d) or (direction == -1 and c > low_5d)
                t2_price = bars[i + 1][0] if i + 1 < n else c
            if t2_fire:
                t2_qty = int(round(qty_remaining * p.trim2_size_pct))
                if t2_qty > 0:
                    _exit(t2_qty, t2_price)
                state = 'POST_T2'

    # if we exited the loop with shares still held, close at the last bar's close
    if qty_remaining > 0:
        _exit(qty_remaining, bars[-1][3])

    return pl_realized / R


def attach_indicators(ohlc: pd.DataFrame) -> pd.DataFrame:
    """Public helper — used by reporter for inspection."""
    return _compute_indicators(ohlc)
