"""Weinstein stage analysis plus IBD's Up/Down Volume -- the bar-derived
inputs to True Market Leaders (Moglen 2020; see pipeline/screeners/tml_moglen.py).

Everything here is computed from the daily bars the nightly enrichment already
downloaded (yfinance_adapter.enrich_universe, period=1y). No fetch.

1. ``weinstein_stage`` -- THE ruler TML uses (Andy 2026-09-18: 「Stage
   Analysis本身就来自Weinstein，这点很重要。而本机pine脚本没有完全得到验证」;
   「按Weinstein原书来验证」). Stan Weinstein, *Secrets for Profiting in Bull
   and Bear Markets* (1988); local copy Trading/03_Trading_Strategies/
   Books_References/stan-weinstein-s-secrets-...pdf. Quotes below are from
   its text (`pdftotext -layout`), page numbers as printed.

   The MA (Ch.1, p.~10): "A 30-week MA is simply the closing price for this
   Friday night added to the prior 29 Friday weekly closings. Divide that
   figure by 30" -- a SIMPLE MA of weekly closes (his Mansfield charts plot a
   weighted one; the definition he gives is simple, so simple it is).

   The stages (Ch.2, pp.33-39):
     Stage 1: "Initially the 30-week MA loses its downside slope and starts
       to flatten out ... intermittent rallies and declines will toss the
       stock above and below the MA ... several swings between support at
       the bottom of the trading range and resistance at the top"
     Stage 2: "a breakout above the top of the resistance zone and the
       30-week MA should occur on impressive volume"; "the 30-week MA
       usually starts turning up shortly after the breakout"; "all downside
       corrections were contained above the rising 30-week MA"
     Stage 3: "First the 30-week MA loses its upward slope and starts to
       flatten out. Whereas Stage 2 price declines always held at or above
       the MA, the stock will now tiptoe below and above the MA"; and "There
       is always the chance that the stock will break out on the upside
       again, beginning yet another Stage 2 upleg"
     Stage 4: "a stock eventually breaks below the bottom of its support
       zone"; "a downside break into Stage 4 doesn't necessarily need such a
       huge increase in volume to be considered valid"
   Entry rules (Ch.1, p.~10): investor -- "breaks out above resistance and
   also moves above its 30-week MA, which must no longer be declining";
   trader -- "already above its 30-week MA, when the MA is rising ... after
   a stock consolidates in a new trading range and pulls back close to the
   moving average, then breaks out again above resistance" (= Moglen's
   "Stage 2 base").
   Breakout volume (Ch.4, p.105), his numbers, copied: "either a one-week
   volume spike that is at least twice the average volume of the past month
   ... or a volume build-up over the past three to four weeks that is at
   least twice the average volume of the past several weeks coupled with at
   least some increase on the breakout week"; footnote 5: "If you are using
   daily charts instead of weekly graphs, look for a volume increase on the
   breakout day of better than twice the average volume of the prior week."

   What the book leaves unnumbered, OUR operationalization (named constants
   below, swappable for Steve Jacobs's reading once found):
     * rising / flat / declining MA: this week's MA vs last week's, with
       tolerance WK_FLAT_TOL (0: any tick up is rising)
     * resistance / support zone: the prior BASE_WEEKS (10) weeks' highest
       high / lowest low, this week excluded
     * "the past month" = 4 weeks; "the past three to four weeks" = 4;
       "the past several weeks" = the 8 weeks before those (VOL_SEVERAL_WEEKS)
     * "some increase on the breakout week" = its mean daily volume above the
       prior week's
     * the week's volume is its MEAN DAILY volume, so an unfinished week (the
       nightly run on a Wednesday) compares fairly; the daily route checks
       each session of the week against the 5 sessions before it
     * transitions, weekly: 4 -> 1 when the MA stops declining; 1 -> 2 on a
       breakout week (close above resistance and the MA, MA not declining,
       volume by any of the three routes); 2 -> 3 on a weekly close under
       the MA or an MA that stops rising; 3 -> 2 on a breakout week with a
       rising MA (the trader's re-entry); 1 -> 4 and 3 -> 4 on a close under
       support and under the MA (no volume needed, per the book)
     * seed: the first readable week (week 31 of the 1y history) has no
       remembered past, so it takes the four-quadrant reading
       (above & rising 2 / below & not rising 4 / below & rising 3 /
       above & not rising 1). With 52 weeks of bars that leaves ~22 weeks of
       machine history -- a stage entered before that is read from the seed.
   Not modelled: higher highs / higher lows inside Stage 2; "churning"
   volume in Stage 3; relative strength (his Ch.4 adds it as a filter).

   A line-by-line port of the Pine script on Andy's machine ("Candles Stage
   Analysis", credited to @TradeDudeNYC and modified) was built and dropped
   (2026-09-18): Andy judged it unverified, it agreed with this ruler on only
   40.4% of 1,832 names, and its 2D sub-stage turned out to be unreachable.

2. ``ud_vol_ratio_50`` -- IBD's Up/Down Volume ratio: total volume on up days
   divided by total volume on down days over the last 50 sessions; an up day
   closes above the prior close, a down day below, unchanged days count in
   neither (Investor's Business Daily, "Use Up/Down Volume Ratio To Gauge
   Demand For Shares"; Linn Software's UDVR reference states the same
   construction). None when there is no down day in the window.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

WK_MA_LEN = 30                  # "the prior 29 Friday weekly closings" + this one
# --- Weinstein: the book's numbers ----------------------------------------
BREAKOUT_VOL_MULT = 2.0         # "at least twice" / "better than twice" (Ch.4 p.105)
VOL_MONTH_WEEKS = 4             # "the average volume of the past month"
VOL_BUILDUP_WEEKS = 4           # "a volume build-up over the past three to four weeks"
DAILY_VOL_PRIOR_DAYS = 5        # footnote 5: "the average volume of the prior week"
# --- Weinstein: OUR operationalization (the book gives no number) ---------
WK_FLAT_TOL = 0.0               # rising / declining = this week's MA vs last week's
BASE_WEEKS = 10                 # resistance / support = prior 10 weeks' high / low
VOL_SEVERAL_WEEKS = 8           # "the past several weeks" before the build-up
UD_WINDOW = 50


def _weinstein_quadrant(above: bool, rising: bool) -> int:
    if above and rising:
        return 2
    if not above and not rising:
        return 4
    return 3 if rising else 1


def _roll(x: np.ndarray, n: int, fn) -> np.ndarray:
    """Trailing n-window reduction (today included), NaN until n values."""
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        from numpy.lib.stride_tricks import sliding_window_view
        out[n - 1:] = fn(sliding_window_view(x, n), axis=1)
    return out


def _lag(x: np.ndarray, k: int = 1) -> np.ndarray:
    return np.concatenate([np.full(k, np.nan), x[:-k]]) if len(x) > k else np.full(len(x), np.nan)


def _weekly(hist: pd.DataFrame) -> Dict[str, np.ndarray]:
    """W-FRI weekly bars in numpy (pandas resample was ~5 ms a name, a
    minute a night over 5,600): close = last, high = max, low = min,
    vol_d = the week's MEAN DAILY volume, day_spike = the week's largest
    session volume / mean of the 5 sessions before that session."""
    c = pd.to_numeric(hist["Close"], errors="coerce").to_numpy(dtype=float)
    h = pd.to_numeric(hist["High"], errors="coerce").to_numpy(dtype=float)
    lo = pd.to_numeric(hist["Low"], errors="coerce").to_numpy(dtype=float)
    v = pd.to_numeric(hist["Volume"], errors="coerce").to_numpy(dtype=float)
    keep = ~np.isnan(c)
    days = hist.index.values.astype("datetime64[D]")[keep]
    c, h, lo, v = c[keep], h[keep], lo[keep], np.nan_to_num(v[keep])
    with np.errstate(invalid="ignore", divide="ignore"):
        prior = _lag(_roll(v, DAILY_VOL_PRIOR_DAYS, np.mean))
        spike = np.where(prior > 0, v / prior, np.nan)
    # 1970-01-01 was a Thursday: (days + 3) % 7 is Mon=0 .. Sun=6; the W-FRI
    # label is the Friday on/after the date
    dow = (days.astype(np.int64) + 3) % 7
    label = days.astype(np.int64) + (4 - dow) % 7
    starts = np.flatnonzero(np.r_[True, label[1:] != label[:-1]])
    ends = np.r_[starts[1:], len(label)]
    return {"close": c[ends - 1],
            "high": np.fmax.reduceat(h, starts),
            "low": np.fmin.reduceat(lo, starts),
            "vol_d": np.add.reduceat(v, starts) / (ends - starts),
            "day_spike": np.fmax.reduceat(spike, starts)}


def breakout_volume_ok(w: Dict[str, np.ndarray]) -> np.ndarray:
    """Weinstein Ch.4 p.105, per week: any of
      (a) "a one-week volume spike that is at least twice the average volume
          of the past month"
      (b) "a volume build-up over the past three to four weeks that is at
          least twice the average volume of the past several weeks coupled
          with at least some increase on the breakout week"
      (c) footnote 5, daily: "a volume increase on the breakout day of better
          than twice the average volume of the prior week" (any session of
          the week)."""
    vd = w["vol_d"]
    with np.errstate(invalid="ignore"):
        a = vd >= BREAKOUT_VOL_MULT * _lag(_roll(vd, VOL_MONTH_WEEKS, np.mean))
        build = _roll(vd, VOL_BUILDUP_WEEKS, np.mean)                     # incl. this week
        before = _lag(_roll(vd, VOL_SEVERAL_WEEKS, np.mean), VOL_BUILDUP_WEEKS)
        b = (build >= BREAKOUT_VOL_MULT * before) & (vd > _lag(vd))
        c = w["day_spike"] > BREAKOUT_VOL_MULT
    return a | b | c


def weinstein_series(hist: pd.DataFrame) -> pd.DataFrame:
    """Weekly frame: close, ma, ma_prev, rising, falling, breakout,
    breakdown, stage (state machine). Weeks before the 30-week MA and its
    one-week slope exist are dropped."""
    w = _weekly(hist)
    close = w["close"]
    ma = _roll(close, WK_MA_LEN, np.mean)
    ma_prev = _lag(ma)
    with np.errstate(invalid="ignore"):
        rising = ma > ma_prev * (1 + WK_FLAT_TOL)
        falling = ma < ma_prev * (1 - WK_FLAT_TOL)
        above = close > ma
        resistance = _lag(_roll(w["high"], BASE_WEEKS, np.max))
        support = _lag(_roll(w["low"], BASE_WEEKS, np.min))
        # "a breakout above the top of the resistance zone and the 30-week MA
        # should occur on impressive volume"
        breakout = above & (close > resistance) & breakout_volume_ok(w)
        # "breaks below the bottom of its support zone" -- volume not required
        breakdown = (close < ma) & (close < support)

    ok = ~np.isnan(ma_prev)
    stages = []
    state = None
    for i in np.flatnonzero(ok):
        if state is None:
            # Seed: the first week we can read has no remembered history, so
            # it takes the four-quadrant reading (see module docstring).
            state = _weinstein_quadrant(bool(above[i]), bool(rising[i]))
        elif state == 2:
            # "Stage 2 price declines always held at or above the MA"
            if not above[i] or not rising[i]:
                state = 3
        elif state == 3:
            # "break out on the upside again, beginning yet another Stage 2 upleg"
            if breakout[i] and rising[i]:
                state = 2
            elif breakdown[i]:
                state = 4
        elif state == 4:
            # "the 30-week MA loses its downside slope and starts to flatten out"
            if not falling[i]:
                state = 1
        elif state == 1:
            # investor entry: "... 30-week MA, which must no longer be declining"
            if breakout[i] and not falling[i]:
                state = 2
            elif breakdown[i]:
                state = 4
        stages.append(state)
    return pd.DataFrame({"close": close[ok], "ma": ma[ok], "ma_prev": ma_prev[ok],
                         "rising": rising[ok], "falling": falling[ok], "breakout": breakout[ok],
                         "breakdown": breakdown[ok], "stage": stages})


def weinstein_fields(hist: pd.DataFrame) -> Dict[str, object]:
    out: Dict[str, object] = {"wk_sma30": None, "wk_sma30_dist": None,
                              "wk_sma30_rising": None, "weinstein_stage": None}
    try:
        wk = weinstein_series(hist)
        if not len(wk):
            return out
        last = wk.iloc[-1]
        now = float(last["ma"])
        close = float(pd.to_numeric(hist["Close"], errors="coerce").dropna().iloc[-1])
        out["wk_sma30"] = now
        out["wk_sma30_dist"] = (close - now) / now if now else None
        # TML's "Rising 30 Week MA": strictly above last week's value
        out["wk_sma30_rising"] = bool(now > float(last["ma_prev"]))
        out["weinstein_stage"] = int(last["stage"])
        return out
    except Exception:
        return {k: None for k in out}


# ------------------------------------------------------------------ 3. IBD Up/Down Volume
def up_down_vol_ratio(hist: pd.DataFrame, n: int = UD_WINDOW) -> Optional[float]:
    try:
        c = pd.to_numeric(hist["Close"], errors="coerce").to_numpy(dtype=float)
        v = pd.to_numeric(hist["Volume"], errors="coerce").to_numpy(dtype=float)
        if len(c) < n + 1:
            return None
        d = np.diff(c)[-n:]
        vv = v[-n:]
        up = float(np.nansum(vv[d > 0]))
        dn = float(np.nansum(vv[d < 0]))
        return up / dn if dn > 0 else None
    except Exception:
        return None


def moglen_bar_fields(hist: pd.DataFrame) -> Dict[str, object]:
    """All bar-derived TML inputs in one dict; never raises."""
    return {**weinstein_fields(hist), "ud_vol_ratio_50": up_down_vol_ratio(hist)}
