"""Volatility Contraction Score -- a faithful port of oratnek's VCS v2.

Source of truth: ``indicators/third_party/oratnek_vcs_v2.pine`` (verbatim,
Pine v6, received 2026-08-17). This replaces the earlier ``calculate_vcs``,
which was a MODIFIED port of an older version (min(13,3) stdev, a Kaufman-ER
quality term, .3/.3/.2/.2 weights) with no tests and no golden check. Every
constant below is the script's default; nothing is "improved".

The score, per the script (all lengths clamped to the bars available, which is
what ``lenLong = math.min(barCount, lenLongInput)`` does -- so windows EXPAND
during warm-up rather than returning na):

    ratioATR = sma(TR,13) / sma(TR,63)          A. price compression
    ratioStd = stdev(close,13) / stdev(close,63) B. price stability (population)
    volRatio = sma(vol,5) / max(sma(vol,50), 1) C. volume contraction
    efficiency = |close - close[13]| / sum(TR,13)
    trendFactor = max(0, 1 - efficiency)         D. a straight line is not a base
    physics = min(100, 100 * (0.4*s_atr + 0.4*s_std + 0.2*s_vol) * trendFactor)
        where s_x = max(0, 1 - ratio) * 2 for ATR/Std and * 1 for volume
    smooth = ema(physics, 3)
    daysTight = consecutive bars with smooth >= 70
    total = smooth * 0.85 + min(15, daysTight)
    score = total if lowest(low,13) >= lowest(low,63)[13] else total * 0.75

Score reading (his): 80+ critical compression, 60-80 developing, <60 expansion.
It measures compression, not direction.

Port-only rule: fewer than 76 bars (63 + 13) returns None -- Pine prints from
bar 1, but that number is warm-up noise and our screener treats null as
"unmeasured", which is the honest label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

LEN_SHORT = 13
LEN_LONG = 63
LEN_VOL = 50
SENSITIVITY = 2.0
TREND_PENALTY_WEIGHT = 1.0
HL_LOOKBACK = 63
PENALTY_FACTOR = 0.75
BONUS_MAX = 15
TIGHT_THRESHOLD = 70.0
MIN_BARS = LEN_LONG + LEN_SHORT


# ------------------------------------------------------------ Pine builtins --

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """``ta.tr(true)``: max(h-l, |h-pc|, |l-pc|); first bar (no prior close)
    falls back to h-l."""
    pc = close.shift(1)
    tr = pd.concat([high - low, (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    tr.iloc[0] = high.iloc[0] - low.iloc[0]
    return tr


def pine_sma(s: pd.Series, length: int) -> pd.Series:
    """``ta.sma(s, math.min(barCount, length))``: expanding until `length` bars
    exist, then rolling."""
    return s.rolling(length, min_periods=1).mean()


def pine_sum(s: pd.Series, length: int) -> pd.Series:
    return s.rolling(length, min_periods=1).sum()


def pine_stdev(s: pd.Series, length: int) -> pd.Series:
    """``ta.stdev``: population standard deviation, expanding during warm-up."""
    return s.rolling(length, min_periods=1).std(ddof=0)


def pine_lowest(s: pd.Series, length: int) -> pd.Series:
    return s.rolling(length, min_periods=1).min()


def pine_ema(s: pd.Series, length: int) -> pd.Series:
    """``ta.ema``: alpha = 2/(length+1), seeded on the first non-na value."""
    return s.ewm(span=length, adjust=False, ignore_na=True).mean()


# ------------------------------------------------------------------ result --

@dataclass
class VcsResult:
    score: Optional[float]
    physics_last: Optional[float] = None
    smooth_last: Optional[float] = None
    days_tight: Optional[int] = None
    consistency: Optional[int] = None
    total: Optional[float] = None
    higher_low: Optional[bool] = None
    series: Optional[pd.Series] = None      # full finalScore path, for inspection


def vcs(df: pd.DataFrame, *, len_short: int = LEN_SHORT, len_long: int = LEN_LONG,
        len_vol: int = LEN_VOL, sensitivity: float = SENSITIVITY,
        trend_penalty_weight: float = TREND_PENALTY_WEIGHT,
        hl_lookback: int = HL_LOOKBACK, penalty_factor: float = PENALTY_FACTOR,
        bonus_max: int = BONUS_MAX) -> VcsResult:
    """Run the score over ``df`` (High/Low/Close/Volume, oldest first) and
    return the last bar's reading plus its parts."""
    cols = {c.lower(): c for c in df.columns}
    high = pd.to_numeric(df[cols["high"]], errors="coerce").astype(float)
    low = pd.to_numeric(df[cols["low"]], errors="coerce").astype(float)
    close = pd.to_numeric(df[cols["close"]], errors="coerce").astype(float)
    vol = pd.to_numeric(df[cols["volume"]], errors="coerce").astype(float)
    n = len(df)
    if n < MIN_BARS:
        return VcsResult(score=None)

    tr = true_range(high, low, close)

    # A. price compression
    ratio_atr = pine_sma(tr, len_short) / pine_sma(tr, len_long).clip(lower=1e-6)
    # B. price stability
    ratio_std = pine_stdev(close, len_short) / pine_stdev(close, len_long).clip(lower=1e-6)
    # C. volume contraction (nan volume bars are skipped by the mean, as
    #    Pine's sma skips na when the window still has values)
    vol_ratio = pine_sma(vol, 5) / pine_sma(vol, len_vol).clip(lower=1.0)
    # D. efficiency filter -- close[lenShort] is na on the first lenShort bars
    net_change = (close - close.shift(len_short)).abs()
    total_travel = pine_sum(tr, len_short)
    efficiency = net_change / total_travel.clip(lower=1e-6)
    trend_factor = (1.0 - efficiency * trend_penalty_weight).clip(lower=0.0)
    # E. structure
    low_recent = pine_lowest(low, len_short)
    low_base = pine_lowest(low, hl_lookback).shift(len_short)
    has_history = pd.Series(np.arange(1, n + 1) - len_short > 0, index=df.index)
    higher_low = pd.Series(True, index=df.index)
    higher_low[has_history] = (low_recent >= low_base)[has_history]

    # score
    s_atr = (1.0 - ratio_atr.fillna(1.0)).clip(lower=0.0) * sensitivity
    s_std = (1.0 - ratio_std.fillna(1.0)).clip(lower=0.0) * sensitivity
    s_vol = (1.0 - vol_ratio.fillna(1.0)).clip(lower=0.0)
    raw = s_atr * 0.4 + s_std * 0.4 + s_vol * 0.2
    filtered = raw * trend_factor                       # na for the first lenShort bars
    physics = (filtered * 100.0).clip(upper=100.0)
    smooth = pine_ema(physics, 3)

    is_tight = (smooth >= TIGHT_THRESHOLD).fillna(False)
    # daysTight: consecutive tight bars, reset on any non-tight bar
    groups = (~is_tight).cumsum()
    days_tight = is_tight.groupby(groups).cumsum().astype(int)

    weight_physics = (100.0 - bonus_max) / 100.0
    consistency = days_tight.clip(upper=bonus_max)
    total = smooth * weight_physics + consistency
    final = total.where(higher_low, total * penalty_factor).fillna(0.0)

    last = -1
    return VcsResult(
        score=float(final.iloc[last]),
        physics_last=float(physics.iloc[last]) if np.isfinite(physics.iloc[last]) else None,
        smooth_last=float(smooth.iloc[last]) if np.isfinite(smooth.iloc[last]) else None,
        days_tight=int(days_tight.iloc[last]),
        consistency=int(consistency.iloc[last]),
        total=float(total.iloc[last]) if np.isfinite(total.iloc[last]) else None,
        higher_low=bool(higher_low.iloc[last]),
        series=final,
    )
