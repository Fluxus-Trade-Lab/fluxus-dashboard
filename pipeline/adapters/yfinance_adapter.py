"""
yfinance data adapter — secondary source for ETF/macro data and VCP Layer 2.
Cherry-picked calculation functions from traderwillhu/market_dashboard build_data.py.
Per plan.md §2.4.
"""
import logging
import time

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import rankdata

from .base_adapter import BaseAdapter
from ..constants.tickers import STOCK_GROUPS
from ..constants.leveraged import get_leveraged_etfs

logger = logging.getLogger(__name__)


def _flatten_yf_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns for single-ticker downloads.
    yfinance >=0.2.31 returns MultiIndex columns like ('Close', 'SPY')
    even for single-ticker downloads. This flattens them to just 'Close'.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# Cherry-picked calculation functions from build_data.py lines 176-240
# ══════════════════════════════════════════════════════════════════════════════

def calculate_atr(hist_data: pd.DataFrame, period: int = 14) -> float | None:
    """ATR via EMA of True Range. Cherry-picked from existing codebase."""
    try:
        hl = hist_data['High'] - hist_data['Low']
        hc = (hist_data['High'] - hist_data['Close'].shift()).abs()
        lc = (hist_data['Low'] - hist_data['Close'].shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean().iloc[-1]
    except Exception:
        return None


def calculate_sma(hist_data: pd.DataFrame, period: int = 50) -> float | None:
    """Simple Moving Average. Cherry-picked from existing codebase."""
    try:
        return hist_data['Close'].rolling(window=period).mean().iloc[-1]
    except Exception:
        return None


def calculate_ema(hist_data: pd.DataFrame, period: int = 10) -> float | None:
    """Exponential Moving Average. Cherry-picked from existing codebase."""
    try:
        return hist_data['Close'].ewm(span=period, adjust=False).mean().iloc[-1]
    except Exception:
        return None


def calculate_rrs(stock_data: pd.DataFrame, spy_data: pd.DataFrame,
                  atr_length: int = 14, length_rolling: int = 50,
                  length_sma: int = 20, atr_multiplier: float = 1.0) -> pd.DataFrame | None:
    """Volatility-adjusted Relative Strength vs SPY (VARS).
    Cherry-picked from existing codebase.
    RRS = (actual_move - expected_move) / stock_ATR
    where expected = (SPY_move / SPY_ATR) * stock_ATR
    """
    try:
        merged = pd.merge(
            stock_data[['High', 'Low', 'Close']],
            spy_data[['High', 'Low', 'Close']],
            left_index=True, right_index=True,
            suffixes=('_stock', '_spy'), how='inner'
        )
        if len(merged) < atr_length + 1:
            return None

        for prefix in ['stock', 'spy']:
            h = merged[f'High_{prefix}']
            l = merged[f'Low_{prefix}']
            c = merged[f'Close_{prefix}']
            tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
            merged[f'atr_{prefix}'] = tr.ewm(alpha=1/atr_length, adjust=False).mean()

        sc = merged['Close_stock'] - merged['Close_stock'].shift(1)
        spy_c = merged['Close_spy'] - merged['Close_spy'].shift(1)
        spy_pi = spy_c / merged['atr_spy']
        expected = spy_pi * merged['atr_stock'] * atr_multiplier
        rrs = (sc - expected) / merged['atr_stock']
        rolling_rrs = rrs.rolling(window=length_rolling, min_periods=1).mean()
        rrs_sma = rolling_rrs.rolling(window=length_sma, min_periods=1).mean()

        return pd.DataFrame(
            {'RRS': rrs, 'rollingRRS': rolling_rrs, 'RRS_SMA': rrs_sma},
            index=merged.index
        )
    except Exception:
        return None


def pocket_pivot_count(closes, opens, vols, lookback: int = 30) -> int:
    """How many of the last `lookback` bars were pocket pivots.

    A pocket pivot here is a green bar whose volume exceeds the highest volume
    of the ten bars before it. (Morales's original compares only the DOWN days
    among those ten; ours compares all ten, which is a stricter bar. Audited
    2026-08-11 and deliberately left as-is.)

    Factored out of the enrichment loop so the 10-session window oratnek
    screens on and the 30-session window we already shipped are one
    implementation read over two lookbacks -- a second inline copy would drift.
    """
    n = len(closes)
    if n < 11:
        return 0
    count = 0
    for j in range(max(11, n - lookback), n):
        if closes[j] > opens[j] and vols[j] > max(vols[max(0, j - 10):j]):
            count += 1
    return count


def calculate_vcs(hist: pd.DataFrame, len_short: int = 13, len_long: int = 63,
                   len_vol: int = 50, sensitivity: float = 2.0,
                   trend_penalty_weight: float = 1.0, hl_lookback: int = 63,
                   penalty_factor: float = 0.75, bonus_max: int = 15) -> float | None:
    """Volatility Contraction Score (0-100).
    Ported from Pine Script by @oratnek_ill, with two enhancements:

    B (Adaptive Volatility): Uses min(13-day, 3-day) stdev so the score
       enters tight regime fast after a pole (3-day drops first) and exits
       slowly during breakout (13-day holds longer).

    D (Trend Quality): Replaces the original efficiency penalty with a
       dual-timeframe Kaufman ER differential. Rewards "coiled springs"
       (strong long-term trend + tight short-term) instead of penalizing
       momentum poles.
    """
    try:
        n = len(hist)
        if n < len_long + len_short:
            return None

        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        vol = hist['Volume']

        # True Range
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)

        # A. Price Compression: short ATR / long ATR
        tr_short = tr.rolling(len_short).mean()
        tr_long = tr.rolling(len_long).mean()
        ratio_atr = tr_short / tr_long.clip(lower=1e-6)

        # B. Adaptive Price Stability: min(slow, fast) stdev / long stdev
        #    Fast to enter tight regime, slow to leave during breakout
        std_short_slow = close.rolling(len_short).std()
        std_short_fast = close.rolling(3).std()
        std_short = pd.concat([std_short_slow, std_short_fast], axis=1).min(axis=1)
        std_long = close.rolling(len_long).std()
        ratio_std = std_short / std_long.clip(lower=1e-6)

        # C. Volume Contraction: 5-day vol / 50-day vol
        vol_avg = vol.rolling(len_vol).mean()
        vol_short_avg = vol.rolling(5).mean()
        vol_ratio = vol_short_avg / vol_avg.clip(lower=1.0)

        # D. Trend Quality: dual-timeframe Kaufman ER differential
        #    High long-term ER (strong trend) + low short-term ER (tight) = high score
        def _kaufman_er(series, length):
            net = (series - series.shift(length)).abs()
            gross = series.diff().abs().rolling(length).sum()
            return net / gross.clip(lower=1e-6)

        er_long = _kaufman_er(close, len_long)
        er_short = _kaufman_er(close, len_short)
        gap = er_long - er_short
        quality_score = (0.4 + gap * trend_penalty_weight).clip(0.0, 1.0)

        # Score components: ATR 30%, StdDev 30%, Volume 20%, Trend Quality 20%
        s_atr = (1.0 - ratio_atr.fillna(1.0)).clip(lower=0.0) * sensitivity
        s_std = (1.0 - ratio_std.fillna(1.0)).clip(lower=0.0) * sensitivity
        s_vol = (1.0 - vol_ratio.fillna(1.0)).clip(lower=0.0)

        raw_score = s_atr * 0.3 + s_std * 0.3 + s_vol * 0.2 + quality_score * 0.2
        physics_score = (raw_score * 100).clip(upper=100)
        smooth_physics = physics_score.ewm(span=3, adjust=False).mean()

        # Consistency bonus: consecutive days >= 70
        is_tight = smooth_physics >= 70
        groups = (~is_tight).cumsum()
        days_tight = is_tight.groupby(groups).cumsum()

        weight_physics = (100.0 - bonus_max) / 100.0
        weighted_physics = smooth_physics * weight_physics
        consistency = days_tight.clip(upper=bonus_max)
        total_score = weighted_physics + consistency

        # E. Structure check: higher low
        low_recent = low.rolling(len_short).min()
        low_base = low.rolling(hl_lookback).min().shift(len_short)
        is_higher_low = low_recent >= low_base

        final_score = total_score.copy()
        final_score[~is_higher_low] *= penalty_factor
        final_score = final_score.fillna(0.0)

        return round(float(final_score.iloc[-1]), 1)
    except Exception:
        return None


def calculate_abc_rating(hist_data: pd.DataFrame) -> str | None:
    """ABC trend rating. Cherry-picked from existing codebase.
    A = EMA10 > EMA20 > SMA50 (strong uptrend)
    C = EMA10 < EMA20 < SMA50 (downtrend)
    B = mixed (transitioning)
    """
    try:
        ema10 = calculate_ema(hist_data, 10)
        ema20 = calculate_ema(hist_data, 20)
        sma50 = calculate_sma(hist_data, 50)
        if ema10 is None or ema20 is None or sma50 is None:
            return None
        if ema10 > ema20 and ema20 > sma50:
            return "A"
        if ema10 < ema20 and ema20 < sma50:
            return "C"
        return "B"
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Adapter class
# ══════════════════════════════════════════════════════════════════════════════

class YfinanceAdapter(BaseAdapter):
    """Secondary adapter for ETF/macro data and VCP OHLC lookups."""

    def fetch_universe(self) -> pd.DataFrame:
        raise NotImplementedError("Use FinvizAdapter for full universe")

    def fetch_etf_data(self, tickers: list[str] = None) -> pd.DataFrame:
        """Fetch ETF data with performance + RRS calculations.
        Uses batch download (not per-ticker) for speed.
        """
        if tickers is None:
            tickers = list({t for group in STOCK_GROUPS.values() for t in group})

        # Ensure SPY is included for RRS calculation
        if 'SPY' not in tickers:
            tickers = ['SPY'] + tickers

        # Single batch download — much faster than per-ticker
        logger.info(f"Downloading {len(tickers)} tickers via yfinance batch...")
        data = yf.download(tickers, period='1y', group_by='ticker',
                           progress=False, threads=True)

        spy_hist = None
        if 'SPY' in data.columns.get_level_values(0):
            spy_hist = data['SPY'][['High', 'Low', 'Close']].dropna()

        results = []
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    hist = data.dropna()
                else:
                    hist = data[ticker].dropna()

                if len(hist) < 20:
                    continue

                close = float(hist['Close'].iloc[-1])
                atr = calculate_atr(hist)
                sma50 = calculate_sma(hist, 50)
                atr_pct = (atr / close) * 100 if atr and close else None
                dist_sma50_atr = (
                    (100 * (close / sma50 - 1) / atr_pct)
                    if (sma50 and atr_pct and atr_pct != 0) else None
                )

                # ABC Rating
                abc = calculate_abc_rating(hist)

                # RRS vs SPY — a SELF-percentile, not a cross-sectional one.
                #
                # `recent_21` is this ETF's own last 21 readings, so the score
                # answers "where does today sit inside this fund's own recent
                # month" — improvement against its own baseline. It does NOT
                # answer "how strong is this fund against the others", which is
                # what the letters RRS and the UI column header both suggest.
                #
                # Measured 2026-08-09, 11 sector ETFs: the score ranks against
                # the underlying RRS *level* at Spearman +0.075 — the two are
                # effectively unrelated. XLK was the strongest sector on the
                # week (+3.52pp over SPY) and scored 5, the bottom bucket,
                # because a fund that has been strong for months is rarely at
                # an extreme within its own trailing 21 days. Same reason the
                # score runs *negative* against perf_3m (-0.193).
                #
                # Kept as-is deliberately: "improvement against own baseline"
                # is a real second-order momentum reading, and perf_1w/perf_1m
                # already answer the strength question elsewhere on the page.
                # Do not sort a "who is strongest" list by this column.
                #
                # Two properties that follow from the construction and will
                # look like bugs if you don't expect them: values are quantised
                # to multiples of 5 ((k-1)/20 x 100 over 21 ranks), and the
                # scale is bounded 0..100 by definition rather than empirically.
                rs_score = None
                rrs_windows = {}
                if spy_hist is not None and ticker != 'SPY':
                    rrs_data = calculate_rrs(
                        hist[['High', 'Low', 'Close']], spy_hist
                    )
                    if rrs_data is not None and len(rrs_data) >= 21:
                        recent_21 = rrs_data['rollingRRS'].iloc[-21:]
                        ranks = rankdata(recent_21, method='average')
                        rs_score = ((ranks[-1] - 1) / (len(recent_21) - 1)) * 100

                    # Same construction over three lookbacks, so a card can show
                    # whether strength is arriving or leaving. There is no
                    # one-day window: a percentile needs something to rank
                    # against, and a single point ranks against nothing.
                    if rrs_data is not None:
                        series = rrs_data['rollingRRS']
                        for label, n in (('1w', 5), ('1m', 21), ('3m', 63)):
                            if len(series) < n:
                                rrs_windows[f'rrs_{label}'] = None
                                continue
                            window = series.iloc[-n:]
                            r = rankdata(window, method='average')
                            rrs_windows[f'rrs_{label}'] = round(
                                ((r[-1] - 1) / (len(window) - 1)) * 100)

                # Leveraged ETF mapping
                long_etfs, short_etfs = get_leveraged_etfs(ticker)

                # Sparkline: last 20 days normalized to first day
                sparkline = []
                if len(hist) >= 20:
                    spark_data = hist['Close'].iloc[-20:]
                    base = float(spark_data.iloc[0])
                    if base > 0:
                        sparkline = [round(float(v) / base, 4) for v in spark_data]

                results.append({
                    'ticker': ticker,
                    'close': close,
                    'change_pct': float((close - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) if len(hist) >= 2 else None,
                    'intraday_pct': float((close - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]),
                    'perf_1w': float((close - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) if len(hist) >= 5 else None,
                    'perf_1m': float((close - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) if len(hist) >= 21 else None,
                    'perf_3m': float((close - hist['Close'].iloc[-63]) / hist['Close'].iloc[-63]) if len(hist) >= 63 else None,
                    'high_52w_dist': float((close - hist['Close'].max()) / hist['Close'].max()),
                    'atr_pct': round(atr_pct, 1) if atr_pct else None,
                    'dist_sma50_atr': round(dist_sma50_atr, 2) if dist_sma50_atr else None,
                    # Not comparable with the stock-side rs_* columns. This is
                    # the 21-day percentile of a *rolling ATR-normalised
                    # relative-strength ratio* vs SPY; the stock columns are
                    # cross-sectional percentiles of raw returns. Same three
                    # letters, different construction, different scale.
                    # `is not None`, not truthiness: 0.0 is the most informative
                    # reading this column has — today sits at the bottom of the
                    # fund's own trailing month — and a falsy test deleted it.
                    # Eight of the nine nulls on 2026-08-09 (XTN EWY EWT TAN EEM
                    # ICLN WGMI BLOK) were genuine zeros with 251 bars each, so
                    # the published distribution was truncated at its left edge:
                    # the minimum observed value was 5, never 0.
                    'rrs_rank': round(rs_score, 0) if rs_score is not None else None,
                    # 1w/1m/3m percentiles of the same rolling RRS series.
                    **rrs_windows,
                    'abc': abc,
                    'sparkline': sparkline,
                    'long_etfs': long_etfs,
                    'short_etfs': short_etfs,
                })
            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")

        logger.info(f"Processed {len(results)}/{len(tickers)} tickers successfully")
        return pd.DataFrame(results)

    def enrich_universe(self, universe: pd.DataFrame,
                        batch_size: int = 500) -> pd.DataFrame:
        """Add performance/technical columns to a Finviz-sourced universe.

        Finviz free tier only provides Overview columns (ticker, sector,
        industry, market_cap, close, change_pct, volume).  This method
        batch-downloads 1-year OHLC from yfinance and computes the missing
        STANDARD_COLUMNS: perf_*, sma*_dist, atr, rel_volume, avg_volume,
        high_52w, low_52w.
        """
        tickers = universe['ticker'].dropna().unique().tolist()
        logger.info(f"Enriching {len(tickers)} tickers with yfinance data...")

        all_data: dict = {}

        def sweep(symbols: list, size: int, tag: str) -> None:
            """One pass of batched downloads into `all_data`."""
            for i in range(0, len(symbols), size):
                batch = symbols[i:i + size]
                logger.info(f"  yfinance {tag} batch {i // size + 1}: "
                            f"{len(batch)} tickers")
                try:
                    data = yf.download(batch, period='1y', group_by='ticker',
                                       progress=False, threads=True)
                    if data.empty:
                        continue
                    for t in batch:
                        try:
                            if len(batch) == 1:
                                hist = _flatten_yf_columns(data).dropna()
                            else:
                                hist = data[t].dropna()
                            if len(hist) >= 20:
                                all_data[t] = hist
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"  Batch download failed: {e}")

        sweep(tickers, batch_size, "pass 1")

        # One pass is not enough on a rate-limited egress. Yahoo throttles the
        # GitHub runner's shared IP, and when it does, the misses arrive in
        # blocks — whole batches return empty, not scattered names. Measured:
        # 2.0% missing from a residential IP, 8.2% and then 22.4% from CI, and
        # the 22.4% night knocked three screeners over at once. The tickers a
        # throttled batch dropped are recoverable the same minute; they just
        # have to be asked for again, smaller and slower.
        #
        # Retries target only what is still missing, in quarter-size batches
        # after a pause. The loop stops early when a round recovers nothing —
        # the residue at that point is delisted symbols and unit tickers, which
        # no amount of retrying converts into price history. ~2% of the
        # universe is the healthy floor, not a failure.
        for attempt in (1, 2):
            missing = [t for t in tickers if t not in all_data]
            if len(missing) <= max(1, int(0.03 * len(tickers))):
                break
            logger.warning(
                "  %d/%d tickers still missing after %s pass(es) — retrying "
                "in smaller batches", len(missing), len(tickers), attempt)
            time.sleep(20 * attempt)
            before = len(all_data)
            sweep(missing, max(50, batch_size // 4), f"retry {attempt}")
            if len(all_data) == before:
                logger.warning("  retry %d recovered nothing — stopping", attempt)
                break

        final_missing = len(tickers) - len(all_data)
        logger.info(f"  Got OHLC for {len(all_data)}/{len(tickers)} tickers "
                    f"({final_missing} missing, "
                    f"{final_missing / max(1, len(tickers)) * 100:.1f}%)")

        # Compute columns for each ticker
        enriched: dict[str, dict] = {}
        for ticker, hist in all_data.items():
            try:
                close = float(hist['Close'].iloc[-1])
                n = len(hist)

                sma20 = float(hist['Close'].rolling(20).mean().iloc[-1])
                sma50 = float(hist['Close'].rolling(50).mean().iloc[-1]) if n >= 50 else None
                sma40 = float(hist['Close'].rolling(40).mean().iloc[-1]) if n >= 40 else None
                sma200 = float(hist['Close'].rolling(200).mean().iloc[-1]) if n >= 200 else None

                atr = calculate_atr(hist)
                avg_vol = float(hist['Volume'].rolling(20).mean().iloc[-1])
                vol = float(hist['Volume'].iloc[-1])

                # --- New fields ---
                last_open = float(hist['Open'].iloc[-1])
                last_high = float(hist['High'].iloc[-1])
                last_low = float(hist['Low'].iloc[-1])
                ema21 = float(hist['Close'].ewm(span=21, adjust=False).mean().iloc[-1])
                # Phase 1: additional EMAs for trailing-stop UI
                ema10 = float(hist['Close'].ewm(span=10, adjust=False).mean().iloc[-1])
                ema20 = float(hist['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
                weekly_closes_for_ema = hist['Close'].resample('W-FRI').last().dropna()
                wk_ema10 = float(weekly_closes_for_ema.ewm(span=10, adjust=False).mean().iloc[-1]) if len(weekly_closes_for_ema) >= 1 else None
                wk_ema20 = float(weekly_closes_for_ema.ewm(span=20, adjust=False).mean().iloc[-1]) if len(weekly_closes_for_ema) >= 1 else None

                # From Open %: intraday move from open
                from_open_pct = (close - last_open) / last_open if last_open > 0 else None

                # DCR%: Daily Closing Range (close - low) / (high - low)
                hl_range = last_high - last_low
                dcr_pct = (close - last_low) / hl_range if hl_range > 0 else None

                # Pocket Pivot: green candle + vol > max(prior 10 bars vol)
                pp = False
                pp_count = 0
                pp_count_10 = 0
                if n >= 11:
                    closes = hist['Close'].values
                    opens = hist['Open'].values
                    vols = hist['Volume'].values
                    # Last bar pocket pivot
                    if closes[-1] > opens[-1]:
                        max_prior_vol = max(vols[-11:-1])
                        pp = bool(vols[-1] > max_prior_vol)
                    # Two windows off one implementation: 30 is what we
                    # already shipped, 10 is the window oratnek screens on
                    # ("a day within the last 10 sessions that posted the
                    # highest volume in 10 days along with a green candle").
                    pp_count = pocket_pivot_count(closes, opens, vols, 30)
                    pp_count_10 = pocket_pivot_count(closes, opens, vols, 10)

                # Trend Base: price > 50SMA AND 10WMA > 30WMA
                trend_base = False
                if sma50 is not None and close > sma50:
                    # Resample to weekly for WMA
                    weekly = hist['Close'].resample('W').last().dropna()
                    if len(weekly) >= 30:
                        wma10 = float(weekly.rolling(10).mean().iloc[-1])
                        wma30 = float(weekly.rolling(30).mean().iloc[-1])
                        trend_base = bool(wma10 > wma30)

                # VCS
                vcs = calculate_vcs(hist)

                # 21EMA Low Dist%: how far today's low is from 21EMA
                ema21_low_dist = (last_low - ema21) / ema21 if ema21 > 0 else None

                # Sugar Babies breakout counts: days with vol >= 9M AND change >= 4%.
                # Pradeep's literal rule for habitual big-volume movers.
                closes = hist['Close'].values
                vols = hist['Volume'].values
                bo_1m = bo_3m = bo_6m = bo_1y = 0
                if n >= 2:
                    prev_close = closes[:-1]
                    today_close = closes[1:]
                    chg = (today_close - prev_close) / prev_close
                    today_vol = vols[1:]
                    is_bo = (today_vol >= 9_000_000) & (chg >= 0.04)
                    bo_1y = int(is_bo.sum())
                    bo_6m = int(is_bo[-126:].sum()) if n - 1 >= 126 else bo_1y
                    bo_3m = int(is_bo[-63:].sum()) if n - 1 >= 63 else min(bo_1y, int(is_bo.sum()))
                    bo_1m = int(is_bo[-21:].sum()) if n - 1 >= 21 else min(bo_1y, int(is_bo.sum()))

                enriched[ticker] = {
                    # Belt for the Finviz 'Change %' rename: with a second
                    # source, a header change upstream degrades this column to
                    # ~2% missing instead of 100%. Fill-only merge, so Finviz
                    # still wins when it parses.
                    'change_pct': (close / float(hist['Close'].iloc[-2]) - 1) if n >= 2 else None,
                    'perf_1w': (close / float(hist['Close'].iloc[-5]) - 1) if n >= 5 else None,
                    'perf_1m': (close / float(hist['Close'].iloc[-21]) - 1) if n >= 21 else None,
                    'perf_34d': (close / float(hist['Close'].iloc[-35]) - 1) if n >= 35 else None,
                    'perf_3m': (close / float(hist['Close'].iloc[-63]) - 1) if n >= 63 else None,
                    'perf_6m': (close / float(hist['Close'].iloc[-126]) - 1) if n >= 126 else None,
                    'perf_1y': (close / float(hist['Close'].iloc[0]) - 1) if n >= 200 else None,
                    'perf_ytd': None,  # Would need calendar-year start
                    'sma20_dist': (close - sma20) / sma20 if sma20 else None,
                    'sma50_dist': (close - sma50) / sma50 if sma50 else None,
                    'sma40_dist': (close - sma40) / sma40 if sma40 else None,
                    'sma200_dist': (close - sma200) / sma200 if sma200 else None,
                    'atr': atr,
                    'rel_volume': vol / avg_vol if avg_vol > 0 else None,
                    'avg_volume': avg_vol,
                    'high_52w': (close / float(hist['High'].max()) - 1),
                    'low_52w': (close / float(hist['Low'].min()) - 1),
                    'from_open_pct': from_open_pct,
                    'dcr_pct': dcr_pct,
                    'pocket_pivot': pp,
                    'pp_count_30d': pp_count,
                    'pp_count_10d': pp_count_10,
                    'trend_base': trend_base,
                    'vcs': vcs,
                    'ema21_low_dist': ema21_low_dist,
                    'ema10': ema10,
                    'ema20': ema20,
                    'wk_ema10': wk_ema10,
                    'wk_ema20': wk_ema20,
                    'bo_count_1m': bo_1m,
                    'bo_count_3m': bo_3m,
                    'bo_count_6m': bo_6m,
                    'bo_count_1y': bo_1y,
                }
            except Exception as e:
                logger.debug(f"  Enrich failed for {ticker}: {e}")

        logger.info(f"  Enriched {len(enriched)}/{len(all_data)} tickers")

        # Merge enriched data back into universe
        enrich_df = pd.DataFrame.from_dict(enriched, orient='index')
        enrich_df.index.name = 'ticker'
        enrich_df = enrich_df.reset_index()

        # Update: only overwrite columns that are currently None/NaN
        for col in enrich_df.columns:
            if col == 'ticker':
                continue
            if col in universe.columns:
                # Merge on ticker, fill missing values from enrichment
                mapping = enrich_df.set_index('ticker')[col]
                mask = universe[col].isna()
                universe.loc[mask, col] = universe.loc[mask, 'ticker'].map(mapping)
            else:
                universe[col] = universe['ticker'].map(
                    enrich_df.set_index('ticker')[col]
                )

        return universe

    def fetch_ma_data(self, tickers: list[str] = None, return_history: bool = False,
                      history_period: str = '1y'):
        """Calculate MA data for Power 3 Signal and Trend Status.
        Per plan.md §2.4 fetch_ma_data.

        With ``return_history=True`` returns ``(signals, histories)`` where
        ``histories`` maps ticker -> full downloaded OHLC DataFrame covering
        ``history_period``.
        """
        if tickers is None:
            tickers = ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC']

        signals = {}
        histories = {}
        for ticker in tickers:
            try:
                hist = _flatten_yf_columns(yf.download(ticker, period=history_period, progress=False))
                if len(hist) < 200:
                    logger.warning(f"{ticker}: insufficient history ({len(hist)} rows)")
                    continue
                histories[ticker] = hist

                close = float(hist['Close'].iloc[-1])

                ema8 = float(hist['Close'].ewm(span=8).mean().iloc[-1])
                ema21 = float(hist['Close'].ewm(span=21).mean().iloc[-1])
                sma50 = float(hist['Close'].rolling(50).mean().iloc[-1])
                sma200 = float(hist['Close'].rolling(200).mean().iloc[-1])
                sma20 = float(hist['Close'].rolling(20).mean().iloc[-1])

                # Power 3 Signal: EMA8 > EMA21 > SMA50 (and all above SMA200)
                power_3 = ema8 > ema21 > sma50 > sma200

                if power_3:
                    signal, color = "POWER_3", "green"
                elif ema8 > ema21 and close > sma200:
                    signal, color = "CAUTION", "yellow"
                elif close > sma200:
                    signal, color = "WARNING", "orange"
                else:
                    signal, color = "RISK_OFF", "red"

                # 52-week fields must stay 52-week regardless of how much
                # history the caller asked for. run_all now requests '3y' so the
                # replay book has depth; anchoring on the last 252 sessions keeps
                # the meaning of this field independent of history_period.
                close_52w = hist['Close'].tail(252)
                high_52w = float(close_52w.max())

                signals[ticker] = {
                    'signal': signal,
                    'color': color,
                    'close': close,
                    'ema8': ema8,
                    'ema21': ema21,
                    'sma50': sma50,
                    'sma200': sma200,
                    'sma20': sma20,
                    # Oratnek's Power Trend checks
                    'power_trend': {
                        '3d_gt_20sma': bool(hist['Close'].iloc[-3:].min() > sma20),
                        '3d_gt_50sma': bool(hist['Close'].iloc[-3:].min() > sma50),
                        '3d_gt_200sma': bool(hist['Close'].iloc[-3:].min() > sma200),
                        '20sma_gt_50sma': bool(sma20 > sma50),
                        '50sma_gt_200sma': bool(sma50 > sma200),
                    },
                    # Trend Status (Oratnek style)
                    'trend_status': {
                        '9ema_dist': round(float((close - hist['Close'].ewm(span=9).mean().iloc[-1]) / close * 100), 2),
                        '21ema_dist': round(float((close - ema21) / close * 100), 2),
                        '50sma_dist': round(float((close - sma50) / close * 100), 2),
                        '200sma_dist': round(float((close - sma200) / close * 100), 2),
                        '52w_high_dist': round(float((close - high_52w) / high_52w * 100), 2),
                    },
                }
            except Exception as e:
                logger.warning(f"Error fetching MA data for {ticker}: {e}")

        if return_history:
            return signals, histories
        return signals

    def fetch_ohlc(self, tickers: list[str], period: str = '90d') -> dict:
        """Fetch OHLC for VCP Layer 2 detection."""
        result = {}
        logger.info(f"Fetching OHLC for {len(tickers)} tickers, period={period}")

        data = yf.download(tickers, period=period, group_by='ticker',
                           progress=False, threads=True)

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    df = _flatten_yf_columns(data)
                    result[ticker] = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                else:
                    df = data[ticker][['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
                    result[ticker] = df
            except Exception:
                pass

        logger.info(f"Got OHLC for {len(result)}/{len(tickers)} tickers")
        return result
