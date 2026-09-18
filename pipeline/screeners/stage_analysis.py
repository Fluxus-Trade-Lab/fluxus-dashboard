"""Stage analysis, two rulers, plus IBD's Up/Down Volume -- the bar-derived
inputs to True Market Leaders (Moglen 2020; see pipeline/screeners/tml_moglen.py).

Everything here is computed from the daily bars the nightly enrichment already
downloaded (yfinance_adapter.enrich_universe, period=1y). No fetch.

1. ``stage_tdn`` -- a line-by-line port of the Pine script on Andy's machine,
   ``indicators/third_party/tradedudenyc_candles_stage_analysis_modified.pine``
   (header: "Stage definitions are copied from @TradeDudeNYC's indicator
   (https://www.tradingview.com/v/agQTA0Vq/) & modified later"). All inputs at
   the script's defaults: ATR 14 (Wilder), EMA5, EMA10, EMA20, SMA50, breakout
   lookback 20, basing band 1.0 ATR, MA compression 1.5 ATR. Only the stage
   selection is ported; colours and labels are display.

   Pine semantics reproduced, not approximated: ``ta.ema`` / ``ta.rma`` are
   SMA-seeded (na for the first length-1 bars); ``ta.atr`` = rma of
   ``ta.tr(true)`` (first bar's TR = high - low); ``ta.highest(high, 20)[1]``
   is the prior 20 bars' high, today excluded; a comparison against na is
   false. During warm-up (SMA50 or ATR not yet defined) we publish None
   rather than the stage the Pine would paint from na-driven falsehoods.

   Two things in the original that look like bugs and are reproduced anyway:
     * 2D ("Exhausted Bullish") is unreachable: exhBull = upAlign and
       atrx >= 11 implies extBull (upAlign and atrx >= 7), which is tested
       first and returns 2C.
     * The 2D label in ``stageName`` reads "2C Exhausted Bullish"; we use the
       constant's own name, 2D.

2. ``weinstein_stage`` -- THE ruler TML uses (Andy 2026-09-18: 「Stage
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

   ``stage_tdn`` (the Pine port above) is kept as an UNVERIFIED reference
   field only; TML does not read it.

3. ``ud_vol_ratio_50`` -- IBD's Up/Down Volume ratio: total volume on up days
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

# --- Pine inputs, at the script's defaults -------------------------------
LEN_ATR = 14
LEN_EMA5 = 5
LEN_EMA10 = 10
LEN_EMA20 = 20
LEN_SMA50 = 50
BO_LOOKBACK = 20
BASING_BAND_ATR = 1.0
MA_COMPRESSION_ATR = 1.5

STAGES = ("1A", "1B", "2A", "2B", "2C", "2D", "3A", "3B", "4A", "4B", "4C", "NA")

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


# ------------------------------------------------------------------ Pine primitives
def pine_sma(src: pd.Series, length: int) -> pd.Series:
    return src.rolling(length, min_periods=length).mean()


def _seeded(src: pd.Series, length: int, alpha: float) -> pd.Series:
    x = src.to_numpy(dtype=float)
    out = np.full(len(x), np.nan)
    if len(x) >= length:
        prev = float(np.mean(x[:length]))
        out[length - 1] = prev
        for i in range(length, len(x)):
            prev = alpha * x[i] + (1.0 - alpha) * prev
            out[i] = prev
    return pd.Series(out, index=src.index)


def pine_ema(src: pd.Series, length: int) -> pd.Series:
    """ta.ema: SMA seed, alpha = 2 / (length + 1)."""
    return _seeded(src, length, 2.0 / (length + 1))


def pine_rma(src: pd.Series, length: int) -> pd.Series:
    """ta.rma (Wilder): SMA seed, alpha = 1 / length."""
    return _seeded(src, length, 1.0 / length)


def pine_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """ta.tr(true): high - low on the first bar (handle_na = true)."""
    pc = close.shift(1)
    tr = pd.concat([high - low, (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    tr.iloc[0] = high.iloc[0] - low.iloc[0]
    return tr


def pine_atr(high, low, close, length: int = LEN_ATR) -> pd.Series:
    return pine_rma(pine_true_range(high, low, close), length)


# ------------------------------------------------------------------ 1. stage_tdn
def stage_tdn_series(hist: pd.DataFrame) -> pd.Series:
    """Stage code per bar ('1A'..'4C', 'NA'); None during warm-up.

    numpy arrays throughout: a comparison involving NaN is False, which is
    exactly Pine's "comparison against na is false"."""
    idx = hist.index
    close_s = pd.to_numeric(hist["Close"], errors="coerce").astype(float)
    high_s = pd.to_numeric(hist["High"], errors="coerce").astype(float)
    low_s = pd.to_numeric(hist["Low"], errors="coerce").astype(float)
    close, high, low = close_s.to_numpy(), high_s.to_numpy(), low_s.to_numpy()

    # === Stage Analysis Core Calculations ===
    ema5 = pine_ema(close_s, LEN_EMA5).to_numpy()
    ema10 = pine_ema(close_s, LEN_EMA10).to_numpy()
    ema20 = pine_ema(close_s, LEN_EMA20).to_numpy()
    sma50 = pine_sma(close_s, LEN_SMA50).to_numpy()
    atr = pine_atr(high_s, low_s, close_s, LEN_ATR).to_numpy()

    with np.errstate(invalid="ignore", divide="ignore"):
        # ATR multiple from SMA50 (signed)
        atrx = (close - sma50) / atr
        ma_spread = np.maximum(np.maximum(ema10, ema20), sma50) - np.minimum(np.minimum(ema10, ema20), sma50)

        # Trend alignment (the + slope terms are commented out in the original)
        ema10_prev = np.concatenate([[np.nan], ema10[:-1]])
        ema10_up = ema10 > ema10_prev
        up_align = (close > ema10) & (ema10 > ema20) & (ema20 > sma50)
        down_align = (close < ema10) & (ema10 < ema20) & (ema20 < sma50)

        # Breakout / breakdown: ta.highest(high, 20)[1] / ta.lowest(low, 20)[1]
        hh = high_s.rolling(BO_LOOKBACK, min_periods=BO_LOOKBACK).max().shift(1).to_numpy()
        ll = low_s.rolling(BO_LOOKBACK, min_periods=BO_LOOKBACK).min().shift(1).to_numpy()
        breakout = close > hh
        breakdown = close < ll

        # Extensions
        ext_bull = up_align & (atrx >= 7)
        exh_bull = up_align & (atrx >= 11)
        ext_bear = down_align & (atrx <= -7)

        # Transitional proxies
        basing = (np.abs(close - sma50) <= BASING_BAND_ATR * atr) & (ma_spread <= MA_COMPRESSION_ATR * atr)
        mean_rev = ~up_align & ~down_align & ~basing & (close >= ema20) & (ema10 >= ema20)
        _fade_core = (up_align & ((close < ema10) | ~ema10_up)) | ((ema10 >= ema20) & (close < ema10))
        fade_a = ~ext_bull & (close >= sma50) & _fade_core
        exh_a = exh_bull & (close >= sma50) & _fade_core
        fade_b = ~ext_bear & (close >= sma50) & (ema10 < ema20)
        bear_stack = (sma50 > ema10) & (ema10 > ema5)
        basing_1a = (close < sma50) & (close > ema10) & (ema10 < ema20)

    # === Stage selection === (the if / else-if ladder, in the original order)
    conds = [
        ext_bull, ext_bear,
        up_align & breakout, up_align,
        exh_a,
        down_align & breakdown, down_align,
        bear_stack, fade_b, fade_a, mean_rev, basing_1a,
    ]
    choices = ["2C", "4C", "2B", "2A", "2D", "4B", "4A", "4A", "3B", "3A", "1B", "1A"]
    arr = np.select(conds, choices, default="NA").astype(object)
    warm = np.isnan(sma50) | np.isnan(atr) | np.isnan(ema20)
    arr[warm] = None
    return pd.Series(arr, index=idx, dtype=object)


def stage_tdn(hist: pd.DataFrame) -> Optional[str]:
    try:
        s = stage_tdn_series(hist)
    except Exception:
        return None
    return None if not len(s) else s.iloc[-1]


# ------------------------------------------------------------------ 2. Weinstein 30-week
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
    return {"stage_tdn": stage_tdn(hist), **weinstein_fields(hist),
            "ud_vol_ratio_50": up_down_vol_ratio(hist)}
