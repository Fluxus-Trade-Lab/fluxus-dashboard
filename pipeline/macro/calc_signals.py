"""Power 3 Signal, Trend Status, and Power Trend calculators.

Standalone signal calculation functions that can be used independently of
the yfinance adapter.  These mirror the inline logic in
``YfinanceAdapter.fetch_ma_data`` (plan.md section 2.4) but are factored out so
that:

* Tests can exercise them without network calls.
* Other modules (e.g. a future breadth pipeline) can reuse them.
* The adapter can delegate here instead of duplicating logic.

Signal hierarchy (Power 3):
    POWER_3  (green)  -- EMA8 > EMA21 > SMA50 > SMA200
    CAUTION  (yellow) -- EMA8 > EMA21, close > SMA200
    WARNING  (orange) -- close > SMA200
    RISK_OFF (red)    -- close <= SMA200
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Power 3 Signal
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_power_3_signal(
    ema8: float,
    ema21: float,
    sma50: float,
    sma200: float,
    close: float,
) -> Dict[str, str]:
    """Determine the Power 3 Signal for a single ticker.

    The Power 3 Signal is a layered moving-average regime indicator:

    * **POWER_3** (green): EMA8 > EMA21 > SMA50 > SMA200 -- full uptrend.
    * **CAUTION** (yellow): EMA8 > EMA21 and close > SMA200 -- weakening but
      still above the long-term trend.
    * **WARNING** (orange): close > SMA200 -- intermediate trend broken, but
      long-term support holds.
    * **RISK_OFF** (red): close <= SMA200 -- below all key supports.

    Parameters
    ----------
    ema8 : float
        8-period Exponential Moving Average.
    ema21 : float
        21-period Exponential Moving Average.
    sma50 : float
        50-period Simple Moving Average.
    sma200 : float
        200-period Simple Moving Average.
    close : float
        Most recent closing price.

    Returns
    -------
    dict
        ``{'signal': str, 'color': str}`` where *signal* is one of
        ``POWER_3``, ``CAUTION``, ``WARNING``, ``RISK_OFF`` and *color*
        is the corresponding display colour.
    """
    if ema8 > ema21 > sma50 > sma200:
        return {"signal": "POWER_3", "color": "green"}
    if ema8 > ema21 and close > sma200:
        return {"signal": "CAUTION", "color": "yellow"}
    if close > sma200:
        return {"signal": "WARNING", "color": "orange"}
    return {"signal": "RISK_OFF", "color": "red"}


# ═══════════════════════════════════════════════════════════════════════════════
# Power Trend (Mike Webster / IBD Market School)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Attribution matters here because we got it wrong twice.  This block used to be
# labelled "Oratnek-style"; the internal task book filed it under Minervini.  It
# is neither.  Power Trend comes from **Mike Webster** (O'Neil Capital
# Management / IBD), who built it with two colleagues while putting IBD Market
# School together.  In his own recording on this machine --
# `data/research/videos_2026-08/webster_21ema_wro9_GxQpyUfZv4U.txt` -- he says at
# :31 that "Power trend is heavily based on the ... something we came up with ...
# three of us came up with", at :57-:58 that the signal he contributed is your
# *low* being above the 21-day for consecutive days ("third or more consecutive
# day that closes up with ... our low is above your 21 day"), and that the
# 50-day rule came from Chuck: "make sure that that 50-day is flat or on an
# incline not a decline".
#
# The four numeric conditions and the OFF condition below are the written form
# of that, from the two write-ups that credit Webster by name: TradingSim
# "Riding the Power Trend" and Deepvue "Mike Webster Indicators".  Full citation
# trail: `data/research/ops/recap_vocab_sources_2026-09-06.md` section 7.
#
# ── Deviations we are keeping, and why ────────────────────────────────────────
# 1. **Two early-failure OFF conditions are not implemented.**  The written
#    standard lists two besides the EMA21/SMA50 cross: the index breaking its
#    50-day while more than 10% off its high, and the index closing below the
#    low of the follow-through day that started the move.  The second needs a
#    follow-through day, which this repo does not compute (index volume is not
#    in `data/output/` at all).  The first names a threshold but not which high
#    it is measured from, and we are not going to invent that reference.  Effect:
#    our state can stay ON slightly longer than the standard's on a fast break.
# 2. **`sma50_rising` is strict (>).**  Webster's recollection of Chuck's rule is
#    "flat or on an incline"; the written form is "rising".  We take the written,
#    stricter reading -- a flat 50-day fails here.
# 3. **EMA21 uses pandas' default `adjust=True`**, matching the `ema21` field the
#    adapter already publishes in the same signal dict.  Textbook EMA is the
#    recursive `adjust=False` form; over the 200+ bars we always feed this the
#    two agree to well under a basis point, and having one definition of EMA21
#    per signal blob is worth more than the difference.

#: Condition (1): consecutive sessions with the daily LOW above the 21-day EMA.
LOW_ABOVE_EMA21_DAYS = 10
#: Condition (2): consecutive sessions with the 21-day EMA above the 50-day SMA.
EMA21_ABOVE_SMA50_DAYS = 5

#: Bars needed before any of this means anything: 200 for the SMA200 that
#: `calculate_ma_structure` wants, and comfortably more than the 50 + streak the
#: Power Trend itself needs.
_MIN_BARS = 60

_POWER_TREND_KEYS = (
    "low_gt_ema21_10d",
    "ema21_gt_sma50_5d",
    "sma50_rising",
    "close_gt_open",
    "is_power_trend",
)


def _trailing_streak(flags: pd.Series) -> pd.Series:
    """For each bar, how many consecutive True values end there (inclusive)."""
    flags = flags.fillna(False).astype(bool)
    groups = (~flags).cumsum()
    return flags.groupby(groups).cumsum().astype(int)


def calculate_power_trend(hist: pd.DataFrame) -> Dict[str, bool]:
    """Evaluate Mike Webster's Power Trend, as a state that turns on and off.

    Four conditions turn the trend **on** when they hold together:

    1. **low_gt_ema21_10d** -- the daily *low* has closed above the 21-day EMA
       for at least 10 consecutive sessions.
    2. **ema21_gt_sma50_5d** -- the 21-day EMA has been above the 50-day SMA for
       at least 5 consecutive sessions.
    3. **sma50_rising** -- the 50-day SMA is rising today.
    4. **close_gt_open** -- today closed above its open.

    One condition turns it **off**: the 21-day EMA crossing back below the
    50-day SMA.  In between it simply stays on -- a red candle, or a day where
    the low dips through the 21-day, does *not* end it.  That persistence is the
    indicator; a daily recompute of the four conditions is not the same object
    and will read "off" on most days of a perfectly healthy trend.

    Parameters
    ----------
    hist : pd.DataFrame
        Daily OHLC with ``Open``, ``Low`` and ``Close`` columns, oldest first.
        At least 60 rows; the state is replayed forward over whatever is given,
        so a longer history gives a more faithful ON/OFF history.

    Returns
    -------
    dict
        The four condition booleans as of the last bar, plus ``is_power_trend``
        -- the persisted state, which is *not* the conjunction of the four.
    """
    required = {"Open", "Low", "Close"}
    missing = required - set(hist.columns)
    if hist.empty or len(hist) < _MIN_BARS or missing:
        logger.warning(
            "calculate_power_trend: insufficient history (%d rows, missing=%s)",
            len(hist), sorted(missing),
        )
        return {k: False for k in _POWER_TREND_KEYS}

    close = hist["Close"]
    ema21 = close.ewm(span=21).mean()
    sma50 = close.rolling(50).mean()

    cond_low = _trailing_streak(hist["Low"] > ema21) >= LOW_ABOVE_EMA21_DAYS
    cond_ema = _trailing_streak(ema21 > sma50) >= EMA21_ABOVE_SMA50_DAYS
    cond_slope = sma50.diff() > 0
    cond_green = close > hist["Open"]

    turns_on = cond_low & cond_ema & cond_slope & cond_green
    # OFF is evaluated against a *valid* SMA50 only; before bar 50 there is no
    # 50-day to cross, and NaN comparisons would silently read as "no cross".
    turns_off = (ema21 < sma50) & sma50.notna()

    state = False
    for on, off in zip(turns_on.to_numpy(), turns_off.to_numpy()):
        if state and off:
            state = False
        if not state and on:
            state = True

    return {
        "low_gt_ema21_10d": bool(cond_low.iloc[-1]),
        "ema21_gt_sma50_5d": bool(cond_ema.iloc[-1]),
        "sma50_rising": bool(cond_slope.iloc[-1]),
        "close_gt_open": bool(cond_green.iloc[-1]),
        "is_power_trend": bool(state),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MA Structure (ours, not anybody's published standard)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_ma_structure(
    hist: pd.DataFrame,
    sma50: float,
    sma200: float,
) -> Dict[str, bool]:
    """Three moving-average checks of our own, kept out of Power Trend's name.

    These three used to ride along inside the ``power_trend`` block and were
    displayed as if Webster had specified them.  He did not -- none of the three
    appears in any published statement of the Power Trend, and the golden cross
    in particular is a different indicator entirely.  They are still useful
    context on the dashboard, so they keep running; they just no longer claim to
    be a standard reading.

    * **3d_gt_50sma** -- the last 3 closes all held above the 50-day SMA.
    * **3d_gt_200sma** -- the last 3 closes all held above the 200-day SMA.
    * **50sma_gt_200sma** -- golden cross in effect.
    """
    if hist.empty or len(hist) < 3:
        logger.warning("calculate_ma_structure: insufficient history (%d rows)", len(hist))
        return {"3d_gt_50sma": False, "3d_gt_200sma": False, "50sma_gt_200sma": False}

    last_3_close_min = float(hist["Close"].iloc[-3:].min())
    return {
        "3d_gt_50sma": bool(last_3_close_min > sma50),
        "3d_gt_200sma": bool(last_3_close_min > sma200),
        "50sma_gt_200sma": bool(sma50 > sma200),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Trend Status (Oratnek-style distance percentages)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_trend_status(
    close: float,
    hist: pd.DataFrame,
    ema21: float,
    sma50: float,
    sma200: float,
) -> Dict[str, float]:
    """Compute percentage distances from key moving averages and the 52-week high.

    Positive values mean the close is *above* the reference; negative means
    *below*.  This is the Oratnek "Trend Status" panel that lets traders
    quickly see how extended (or compressed) a ticker is relative to its
    structural supports.

    Parameters
    ----------
    close : float
        Most recent closing price.
    hist : pd.DataFrame
        OHLC DataFrame with a ``Close`` column spanning at least 252 rows
        for a meaningful 52-week high.
    ema21 : float
        21-period Exponential Moving Average.
    sma50 : float
        50-period Simple Moving Average.
    sma200 : float
        200-period Simple Moving Average.

    Returns
    -------
    dict
        Keys: ``9ema_dist``, ``21ema_dist``, ``50sma_dist``,
        ``200sma_dist``, ``52w_high_dist`` -- each a rounded float
        representing percent distance.
    """
    if hist.empty or close == 0:
        return {
            "9ema_dist": 0.0,
            "21ema_dist": 0.0,
            "50sma_dist": 0.0,
            "200sma_dist": 0.0,
            "52w_high_dist": 0.0,
        }

    ema9 = float(hist["Close"].ewm(span=9, adjust=False).mean().iloc[-1])
    high_52w = float(hist["Close"].max())

    return {
        "9ema_dist": round((close - ema9) / close * 100, 2),
        "21ema_dist": round((close - ema21) / close * 100, 2),
        "50sma_dist": round((close - sma50) / close * 100, 2),
        "200sma_dist": round((close - sma200) / close * 100, 2),
        "52w_high_dist": round((close - high_52w) / high_52w * 100, 2),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Aggregate market signal from multiple tickers
# ═══════════════════════════════════════════════════════════════════════════════

# Signal priority for aggregation (lower index = more bullish).
_SIGNAL_PRIORITY: List[str] = ["POWER_3", "CAUTION", "WARNING", "RISK_OFF"]

# Display colours keyed by signal name.
_SIGNAL_COLORS: Dict[str, str] = {
    "POWER_3": "green",
    "CAUTION": "yellow",
    "WARNING": "orange",
    "RISK_OFF": "red",
}


def generate_all_signals(ticker_signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate Power 3 signals from multiple tickers into a market-wide view.

    The aggregate signal is the **weakest** (most bearish) signal across all
    tickers supplied.  This implements the conservative "weakest-link" approach
    -- if any major index is in RISK_OFF, the aggregate is RISK_OFF.

    Additionally the function counts how many tickers fall into each regime
    bucket to give a quick "breadth of strength" reading.

    Parameters
    ----------
    ticker_signals : dict
        Mapping of ticker symbol to its signal dict.  Each value must
        contain at least ``{'signal': str, 'color': str}`` as returned by
        :func:`calculate_power_3_signal`.

        Example::

            {
                'SPY': {'signal': 'POWER_3', 'color': 'green', ...},
                'QQQ': {'signal': 'CAUTION', 'color': 'yellow', ...},
                'IWM': {'signal': 'WARNING', 'color': 'orange', ...},
                'RSP': {'signal': 'POWER_3', 'color': 'green', ...},
            }

    Returns
    -------
    dict
        ``{
            'aggregate_signal': str,
            'aggregate_color': str,
            'signal_counts': {'POWER_3': N, 'CAUTION': N, ...},
            'total_tickers': int,
            'all_power_3': bool,
            'tickers': {<original ticker_signals dict>},
        }``
    """
    if not ticker_signals:
        logger.warning("generate_all_signals called with empty ticker_signals")
        return {
            "aggregate_signal": "RISK_OFF",
            "aggregate_color": "red",
            "signal_counts": {s: 0 for s in _SIGNAL_PRIORITY},
            "total_tickers": 0,
            "all_power_3": False,
            "tickers": {},
        }

    # Count occurrences of each signal level.
    signal_counts: Dict[str, int] = {s: 0 for s in _SIGNAL_PRIORITY}
    worst_priority = 0  # index into _SIGNAL_PRIORITY; higher = more bearish

    for ticker, sig_data in ticker_signals.items():
        sig_name = sig_data.get("signal", "RISK_OFF")
        if sig_name in signal_counts:
            signal_counts[sig_name] += 1
        else:
            logger.warning("Unknown signal '%s' for ticker %s, treating as RISK_OFF", sig_name, ticker)
            signal_counts["RISK_OFF"] += 1
            sig_name = "RISK_OFF"

        idx = _SIGNAL_PRIORITY.index(sig_name) if sig_name in _SIGNAL_PRIORITY else len(_SIGNAL_PRIORITY) - 1
        worst_priority = max(worst_priority, idx)

    aggregate_signal = _SIGNAL_PRIORITY[worst_priority]
    all_power_3 = signal_counts.get("POWER_3", 0) == len(ticker_signals)

    return {
        "aggregate_signal": aggregate_signal,
        "aggregate_color": _SIGNAL_COLORS[aggregate_signal],
        "signal_counts": signal_counts,
        "total_tickers": len(ticker_signals),
        "all_power_3": all_power_3,
        "tickers": ticker_signals,
    }
