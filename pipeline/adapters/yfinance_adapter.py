"""
yfinance data adapter — secondary source for ETF/macro data and VCP Layer 2.
Cherry-picked calculation functions from traderwillhu/market_dashboard build_data.py.
Per plan.md §2.4.
"""
import logging

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

                # RRS vs SPY
                rs_score = None
                if spy_hist is not None and ticker != 'SPY':
                    rrs_data = calculate_rrs(
                        hist[['High', 'Low', 'Close']], spy_hist
                    )
                    if rrs_data is not None and len(rrs_data) >= 21:
                        recent_21 = rrs_data['rollingRRS'].iloc[-21:]
                        ranks = rankdata(recent_21, method='average')
                        rs_score = ((ranks[-1] - 1) / (len(recent_21) - 1)) * 100

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
                    'rs': round(rs_score, 0) if rs_score else None,
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

        # Download in batches to avoid yfinance timeouts
        all_data = {}
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            logger.info(f"  yfinance batch {i // batch_size + 1}: "
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

        logger.info(f"  Got OHLC for {len(all_data)}/{len(tickers)} tickers")

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

                # From Open %: intraday move from open
                from_open_pct = (close - last_open) / last_open if last_open > 0 else None

                # DCR%: Daily Closing Range (close - low) / (high - low)
                hl_range = last_high - last_low
                dcr_pct = (close - last_low) / hl_range if hl_range > 0 else None

                # Pocket Pivot: green candle + vol > max(prior 10 bars vol)
                pp = False
                pp_count = 0
                if n >= 11:
                    closes = hist['Close'].values
                    opens = hist['Open'].values
                    vols = hist['Volume'].values
                    # Last bar pocket pivot
                    if closes[-1] > opens[-1]:
                        max_prior_vol = max(vols[-11:-1])
                        pp = bool(vols[-1] > max_prior_vol)
                    # Count pocket pivots in last 30 bars
                    lookback = min(n, 30)
                    for j in range(max(11, n - lookback), n):
                        if closes[j] > opens[j] and vols[j] > max(vols[max(0, j-10):j]):
                            pp_count += 1

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

                enriched[ticker] = {
                    'perf_1w': (close / float(hist['Close'].iloc[-5]) - 1) if n >= 5 else None,
                    'perf_1m': (close / float(hist['Close'].iloc[-21]) - 1) if n >= 21 else None,
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
                    'trend_base': trend_base,
                    'vcs': vcs,
                    'ema21_low_dist': ema21_low_dist,
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

    def fetch_ma_data(self, tickers: list[str] = None) -> dict:
        """Calculate MA data for Power 3 Signal and Trend Status.
        Per plan.md §2.4 fetch_ma_data.
        """
        if tickers is None:
            tickers = ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC']

        signals = {}
        for ticker in tickers:
            try:
                hist = _flatten_yf_columns(yf.download(ticker, period='1y', progress=False))
                if len(hist) < 200:
                    logger.warning(f"{ticker}: insufficient history ({len(hist)} rows)")
                    continue

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
                        '52w_high_dist': round(float((close - hist['Close'].max()) / hist['Close'].max() * 100), 2),
                    },
                }
            except Exception as e:
                logger.warning(f"Error fetching MA data for {ticker}: {e}")

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
