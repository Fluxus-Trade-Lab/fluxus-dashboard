"""Structure Pivot -- a faithful port of oratnek's "Advanced Structure Pivot".

Source of truth: ``indicators/third_party/oratnek_advanced_structure_pivot.pine``
(verbatim, Pine v6). This module reproduces its STATE, not its drawings: for
one ticker's daily bars it returns the structure the indicator would show on
the last bar -- LL, HL, 1st/2nd Pivot, TP1/TP2, phase, stop -- and the seven
Pine-Screener signals for that bar.

Why a bar-by-bar simulation and not a formula on the last N bars: the original
is stateful in four ways that cannot be read off a window --

* a pivot low of length L only exists from L bars after it (``ta.pivotlow``);
* every bar, every length's setup dies if that bar's low undercuts its HL;
* the winning length is re-chosen every bar (Tightest / Longest / Shortest);
* the phase (1 -> 2 -> 3) only advances, and the stop depends on it.

Where the script's published DESCRIPTION and its CODE disagree, the code wins:
phase transitions use ``high``, the fail check uses ``low``, both against
levels the description says are checked on ``close``.

Two things the Pine does that look like bugs and are reproduced anyway,
because the golden check is "same numbers as the chart":

* When no length is a setup, the shortest length's current pivot is
  OVERWRITTEN by any lower low (``win_long.curr_p := low``). That permanently
  changes what that length's next confirmed pivot compares against.
* ``find_winner`` with "Longest Length" sets ``upd := true`` for every
  candidate, so the last (longest) setup wins; "Shortest Length" keeps the
  first. Neither compares lengths explicitly.

Not ported: drawings, history stacks, alerts (touch-based, intraday), the
Pine-Screener RS / ADR / ATR% columns (we have our own; note his ATR% 50SMA is
``(close/s50-1)/(atr/close)`` -- the (1+dist)-less form -- so his "<5" gate is
in slightly different units from our ``atr_from_sma50``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

MIN_BARS = 30           # under this, "unmeasured": no 21-EMA and no room for two pivots

# Fib ratios exactly as the script's defaults.
FIB_FIRST = 0.618
FIB_TP1 = 1.764
FIB_TP2 = 2.618


@dataclass
class PivotState:
    """One detection length. Mirrors Pine's ``PivotState`` field for field."""
    len: int
    is_long: bool = True
    prev_p: Optional[float] = None
    prev_idx: Optional[int] = None
    curr_p: Optional[float] = None
    curr_idx: Optional[int] = None
    is_setup: bool = False
    break_val: Optional[float] = None
    break_idx: Optional[int] = None
    confirmed_at: Optional[int] = None      # port-only: bar on which curr was confirmed


@dataclass
class Result:
    """The indicator's state on the last bar."""
    df: pd.DataFrame
    states: List[PivotState]
    states_short: List[PivotState]
    winner: Optional[PivotState]
    setup: Optional[bool]                    # None = unmeasured
    ll: Optional[float] = None
    ll_idx: Optional[int] = None
    hl: Optional[float] = None
    hl_idx: Optional[int] = None
    pivot_2nd: Optional[float] = None
    pivot_2nd_idx: Optional[int] = None
    pivot_1st: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    phase: Optional[int] = None
    stop: Optional[float] = None
    ma: Optional[float] = None
    counter_val: Optional[float] = None
    signal: Optional[str] = None
    failed_today: bool = False
    created_today: bool = False
    setup_since: Optional[int] = None        # bar index the current structure was drawn
    ll_break_today: bool = False
    states_setup_any: bool = False

    def to_row(self) -> Dict[str, Any]:
        """Flat, JSON-safe fields for universe.json (prefix ``sp_``)."""
        close = float(self.df["close"].iloc[-1]) if len(self.df) else None
        n = len(self.df)

        def pct(level):
            if level is None or not close:
                return None
            return round((level / close - 1.0) * 100.0, 2)

        row: Dict[str, Any] = {
            "sp_setup": self.setup,
            "sp_len": self.winner.len if (self.setup and self.winner) else None,
            "sp_ll": _r(self.ll), "sp_hl": _r(self.hl),
            "sp_1st": _r(self.pivot_1st), "sp_2nd": _r(self.pivot_2nd),
            "sp_tp1": _r(self.tp1), "sp_tp2": _r(self.tp2),
            "sp_phase": self.phase if self.setup else None,
            "sp_stop": _r(self.stop) if self.setup else None,
            "sp_ma": _r(self.ma),
            "sp_signal": self.signal,
            "sp_days": (n - 1 - self.setup_since) if (self.setup and self.setup_since is not None) else None,
            "sp_dist_1st_pct": pct(self.pivot_1st) if self.setup else None,
            "sp_dist_2nd_pct": pct(self.pivot_2nd) if self.setup else None,
            "sp_counter": _r(self.counter_val),
            "sp_close": _r(close),
        }
        return row


def _r(x, nd: int = 4):
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(v) else round(v, nd)


# ------------------------------------------------------------------ pivots --

def _pivot_low(low: np.ndarray, b: int, L: int) -> Optional[float]:
    """Pine ``ta.pivotlow(low, L, L)`` evaluated on bar b: the low at b-L if it
    is strictly below every low in [b-2L, b] except itself; else None."""
    c = b - L
    if c - L < 0:
        return None
    v = low[c]
    left = low[c - L:c]
    right = low[c + 1:b + 1]
    if np.any(left <= v) or np.any(right <= v):
        return None
    return float(v)


def _pivot_high(high: np.ndarray, b: int, L: int) -> Optional[float]:
    c = b - L
    if c - L < 0:
        return None
    v = high[c]
    left = high[c - L:c]
    right = high[c + 1:b + 1]
    if np.any(left >= v) or np.any(right >= v):
        return None
    return float(v)


def _update(st: PivotState, b: int, high: np.ndarray, low: np.ndarray) -> None:
    """Pine ``method update(PivotState st)`` on bar b."""
    p = _pivot_low(low, b, st.len) if st.is_long else _pivot_high(high, b, st.len)
    if p is None:
        return
    setup_cond = False
    if st.curr_p is not None:
        setup_cond = (p > st.curr_p) if st.is_long else (p < st.curr_p)
    st.prev_p, st.prev_idx = st.curr_p, st.curr_idx
    st.curr_p, st.curr_idx = p, b - st.len
    st.confirmed_at = b
    st.is_setup = setup_cond
    st.break_val = None
    st.break_idx = None
    if setup_cond and st.prev_idx is not None:
        start_s, end_s = st.prev_idx + 1, st.curr_idx - 1
        if end_s >= start_s:
            seg = high[start_s:end_s + 1] if st.is_long else low[start_s:end_s + 1]
            k = int(np.argmax(seg)) if st.is_long else int(np.argmin(seg))
            # Pine keeps the FIRST extreme on ties (strict > / <): argmax/argmin do too.
            st.break_val = float(seg[k])
            st.break_idx = start_s + k


def _find_winner(states: List[PivotState], priority: str) -> Optional[PivotState]:
    w: Optional[PivotState] = None
    for st in states:
        if st.is_setup and st.break_val is not None:
            if w is None:
                upd = True
            elif priority == "tightest":
                upd = (st.break_val < w.break_val) if st.is_long else (st.break_val > w.break_val)
            elif priority == "longest":
                upd = True
            else:  # shortest
                upd = False
            if upd:
                w = st
    return w


def _counter_coordinates(arr: List[PivotState], limit_idx: int):
    """Pine ``get_counter_coordinates(arr, limit_idx, find_highs=true)``:
    anchor = highest pivot high at or before limit_idx; second point = the
    later pivot high (before limit_idx) with the steepest slope from anchor."""
    anchor_val, ax, ay = -1e6, None, None
    for st in arr:
        for idx, p in ((st.prev_idx, st.prev_p), (st.curr_idx, st.curr_p)):
            if idx is not None and p is not None and idx <= limit_idx and p > anchor_val:
                anchor_val, ax, ay = p, float(idx), p
    if ax is None:
        return None
    best_slope, rx, ry = None, None, None
    for st in arr:
        if st.curr_idx is not None and st.curr_p is not None:
            if st.curr_idx > ax and st.curr_idx < limit_idx:
                m = (st.curr_p - ay) / (st.curr_idx - ax)
                if best_slope is None or m > best_slope:
                    best_slope, rx, ry = m, float(st.curr_idx), st.curr_p
    if rx is None:
        return None
    return ax, ay, rx, ry


# ---------------------------------------------------------------- the run --

def run(df: pd.DataFrame, *, min_len: int = 2, max_len: int = 5,
        priority: str = "tightest",
        fib_first: float = FIB_FIRST, fib_tp1: float = FIB_TP1, fib_tp2: float = FIB_TP2,
        ma_len: int = 21, ma_type: str = "EMA", ma_src: str = "low") -> Result:
    """Simulate the indicator over ``df`` (columns open/high/low/close, oldest
    first) and return its state on the last bar."""
    cols = {c.lower(): c for c in df.columns}
    high = df[cols["high"]].to_numpy(dtype=float)
    low = df[cols["low"]].to_numpy(dtype=float)
    close = df[cols["close"]].to_numpy(dtype=float)
    n = len(df)

    states = [PivotState(L, True) for L in range(min_len, max_len + 1)]
    states_short = [PivotState(L, False) for L in range(min_len, max_len + 1)]

    if n < MIN_BARS:
        return Result(df=df, states=states, states_short=states_short, winner=None, setup=None)

    src = {"low": low, "high": high, "close": close}[ma_src]
    if ma_type.upper() == "SMA":
        ma_arr = pd.Series(src).rolling(ma_len).mean().to_numpy()
    else:
        ma_arr = pd.Series(src).ewm(span=ma_len, adjust=False).mean().to_numpy()

    # DrawObjects state
    sig = 0
    fib_1st = tp1 = tp2 = None
    phase = 1
    cnt_locked = False
    cnt = None            # (x1, y1, x2, y2)
    setup_since: Optional[int] = None

    last_ll_val: Optional[float] = None
    signal: Optional[str] = None
    failed_today = created_today = False
    ll_break_today = False
    winner: Optional[PivotState] = None
    cnt_val_long: Optional[float] = None
    current_stop: Optional[float] = None

    for b in range(n):
        ma_stop = ma_arr[b]
        lo, hi, cl = low[b], high[b], close[b]
        cl_prev = close[b - 1] if b > 0 else np.nan

        # --- Main Logic: Long ---
        for st in states:
            _update(st, b, high, low)
            if st.is_setup and st.curr_p is not None and lo < st.curr_p:
                st.is_setup = False
        # --- Main Logic: Short (Counter Trend only) ---
        for st in states_short:
            _update(st, b, high, low)
            if st.is_setup and st.curr_p is not None and hi > st.curr_p:
                st.is_setup = False

        w = _find_winner(states, priority)
        if w is None:
            w = states[0]
        if not w.is_setup and w.curr_p is not None and lo < w.curr_p:
            w.curr_p = float(lo)
            w.curr_idx = b
        winner = w

        # --- draw_long ---
        just_created = False
        local_fail = False
        local_created = False
        cnt_val_long = None

        wsig = (w.curr_idx if w.curr_idx is not None else -999999) * 1000 + w.len * 10 + (1 if w.is_setup else 0)
        if wsig != sig:
            fib_1st = tp1 = tp2 = None
            phase = 1
            cnt_locked = False
            cnt = None
            if w.curr_p is not None and w.is_setup and w.prev_idx is not None and w.break_idx is not None:
                rng = w.break_val - w.curr_p
                fib_1st = w.curr_p + rng * fib_first
                tp1 = w.curr_p + rng * fib_tp1
                tp2 = w.curr_p + rng * fib_tp2
                phase = 1
                setup_since = b
            if w.is_setup:
                just_created = True
                local_created = True
            sig = wsig

        # Counter trend (only when not a setup)
        if not w.is_setup:
            coords = cnt if cnt_locked else _counter_coordinates(states_short, w.curr_idx if w.curr_idx is not None else -1)
            if coords is not None:
                x1, y1, x2, y2 = coords
                m = (y2 - y1) / (x2 - x1)
                cnt_val_long = y2 + m * (b - x2)
                if not cnt_locked and cl > cnt_val_long:
                    cnt_locked = True
                    cnt = coords

        if w.is_setup:
            if phase == 1 and w.break_val is not None and hi >= w.break_val:
                phase = 2
            if phase == 2 and tp1 is not None and hi >= tp1:
                phase = 3
            if not just_created:
                if lo < ma_stop:                     # fail: LOW under the MA
                    w.is_setup = False
                    local_fail = True
                    fib_1st = tp1 = tp2 = None
                    phase = 1
                    sig = -1

        failed_today, created_today = local_fail, local_created

        # --- current stop & signals (computed after draw, as in the script) ---
        if fib_1st is None:
            current_stop = ma_stop
        else:
            current_stop = ma_stop if phase == 1 else (fib_1st if phase == 2 else max(fib_1st, ma_stop))

        if winner is not None:
            last_ll_val = winner.prev_p

        signal = None
        ll_break_today = False
        if w.is_setup:
            if fib_1st is not None and cl_prev <= fib_1st < cl and (w.break_val is None or cl <= w.break_val):
                signal = "1st_break"
            if w.break_val is not None and cl_prev <= w.break_val < cl and (tp1 is None or cl <= tp1):
                signal = "2nd_break"
            if tp1 is not None and cl_prev <= tp1 < cl and (tp2 is None or cl <= tp2):
                signal = "tp1_hit"
            if tp2 is not None and cl_prev <= tp2 < cl:
                signal = "tp2_hit"
            if cl_prev >= current_stop > cl:
                signal = "stop_hit"
        if last_ll_val is not None and cl_prev >= last_ll_val > cl:
            ll_break_today = True
            if signal is None:
                signal = "ll_break"
        if cnt_val_long is not None and cl_prev <= cnt_val_long < cl:
            if signal is None:
                signal = "counter_break"

    # ------------------------------------------------------------ result --
    w = winner
    setup = bool(w.is_setup) if w is not None else False
    res = Result(df=df, states=states, states_short=states_short, winner=w, setup=setup,
                 ma=float(ma_arr[-1]) if np.isfinite(ma_arr[-1]) else None,
                 counter_val=cnt_val_long, signal=signal,
                 failed_today=failed_today, created_today=created_today,
                 ll_break_today=ll_break_today,
                 states_setup_any=any(s.is_setup for s in states))
    if w is not None:
        res.ll, res.ll_idx = w.prev_p, w.prev_idx
        res.hl, res.hl_idx = w.curr_p, w.curr_idx
        if setup:
            res.pivot_2nd, res.pivot_2nd_idx = w.break_val, w.break_idx
            res.pivot_1st, res.tp1, res.tp2 = fib_1st, tp1, tp2
            res.phase = phase
            res.stop = current_stop
            res.setup_since = setup_since
    return res
