"""VCP detector -- bases where the selling is running out.

**What it looks for: contraction, not price.** A base of progressively
shallower pullbacks on declining volume. The premise (Minervini's pattern,
not ours) is that each successive dip finding buyers higher means the supply
overhang is being worked off, and that the last, tightest contraction is
where a stop can sit close enough to make the position size worth taking.
Depth ratios of 30-75% between contractions are what "progressively
shallower" is operationalised as.

**What it cannot tell you: whether it resolves up.** A contraction sequence
is a description of the last 90 days; it carries no claim about the next
ten. Tight bases fail, and when they fail they fail from exactly the place
that made them attractive. What the pattern buys is not a higher hit rate but
a cheaper stop -- which is a sizing advantage, not a direction call.

It also cannot see the reason for the contraction. A name coiling ahead of an
earnings date and one coiling on genuine accumulation look identical here.

Two-layer architecture below.

Layer 1 (``layer1_finviz_filter``):
    Minervini's Trend Template (7 of his 8 legs; leg 3, the 200-day slope,
    is not on the row) plus our own price / market-cap / performance cuts,
    each declared in the function docstring.

Layer 2 (``layer2_detect_vcp``):
    Precise pattern detection on 90-day OHLCV history fetched via
    yfinance.  Finds swing highs/lows, builds a contraction sequence,
    and verifies that contractions are progressively shallower, each about
    half the previous (30-75 % band -- the band is ours) on declining volume,
    2-6 of them. Since 2026-09-18 every one of these GATES the row; before,
    the ratio and volume checks were flags that never filtered.

``run_vcp_pipeline`` orchestrates both layers end-to-end.

Reference: plan.md section 2.5
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Minervini's contraction count range ("two to four", "as many as five or six").
MIN_CONTRACTIONS = 2
MAX_CONTRACTIONS = 6
# Tolerance around Minervini's "about half" -- SELF-MADE (he gives none).
RATIO_BAND = (0.30, 0.75)


# =====================================================================
# Layer 1 — Finviz coarse filter
# =====================================================================


def layer1_finviz_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Coarse filter: Minervini's Trend Template, plus our own liquidity cuts.

    Source: Mark Minervini, *Trade Like a Stock Market Wizard* (2013), the
    eight-point Trend Template. Leg by leg, as implemented:
      1. price above the 150-day (30-week) and 200-day MA   -> wk_sma30_dist > 0, sma200_dist > 0
      2. 150-day MA above the 200-day MA                     -> wk_sma30 > sma200
      3. 200-day MA trending up for at least 1 month         -> NOT APPLIED (see below)
      4. 50-day MA above both the 150-day and 200-day MA     -> sma50 > wk_sma30, sma50 > sma200
      5. price above the 50-day MA                           -> sma50_dist > 0
      6. price at least 30% above the 52-week low            -> low_52w >= 0.30
      7. price within at least 25% of the 52-week high       -> high_52w >= -0.25
      8. RS ranking no less than 70                          -> rs_rating >= 70
    DECLARED deviations (2026-09-21, audit recheck; METRIC_SOURCES VCP-L1 row):
      * 150-day MA is read as the 30-week SMA (wk_sma30, Friday closes,
        stage_analysis.weinstein_fields). Minervini writes "150-day (30-week)"
        himself; the row carries no daily 150-SMA.
      * leg 3 is not applied: the row has no 200-day MA slope. Not replaced
        by a proxy.
      * leg 8 reads our rs_rating, an IBD-style community reconstruction
        (METRIC_SOURCES rs_rating row), not IBD's own RS Rating.
      * OURS, not his: close > $10, market cap >= $1B, perf_1m > 0 and
        |perf_1w| < |perf_1m|. They cut the ~2,400 rows to a fetchable list
        for Layer 2; they are not Trend Template legs.
    Until 2026-09-21 legs 1/2/4 (150-day) and 8 (RS) were missing and the
    extra cuts were undeclared (audit 09-18 C #43).
    A column wholly absent (fallback universe) skips its leg with a warning;
    a missing value on a row fails that row.
    """
    # Ensure numeric types — scraped data may have None/object columns
    num_cols = ['close', 'market_cap', 'sma50_dist', 'sma200_dist',
                'low_52w', 'high_52w', 'perf_1w', 'perf_1m',
                'wk_sma30', 'wk_sma30_dist', 'rs_rating']
    df = df.copy()
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    mask = (
        df['close'].notna() &
        df['perf_1w'].notna() &
        df['perf_1m'].notna() &
        # ours (liquidity / fetch-budget cuts)
        (df['close'] > 10) &
        (df['market_cap'] >= 1e9) &
        (df['perf_1m'] > 0) &
        (df['perf_1w'].abs() < df['perf_1m'].abs()) &
        # Trend Template legs 1 (200 half), 5, 6, 7
        (df['sma50_dist'] > 0) &
        (df['sma200_dist'] > 0) &
        (df['low_52w'] >= 0.30) &
        (df['high_52w'] >= -0.25)
    )

    if {'wk_sma30', 'wk_sma30_dist'} <= set(df.columns):
        sma50 = df['close'] / (1 + df['sma50_dist'])
        sma200 = df['close'] / (1 + df['sma200_dist'])
        ma150 = df['wk_sma30']
        mask &= (
            (df['wk_sma30_dist'] > 0) &          # leg 1: price above the 150-day
            (ma150 > sma200) &                   # leg 2
            (sma50 > ma150) & (sma50 > sma200)   # leg 4
        )
    else:
        logger.warning("VCP L1: no wk_sma30 on the universe -- Trend Template 150-day legs skipped")

    if 'rs_rating' in df.columns:
        mask &= df['rs_rating'] >= 70            # leg 8: "no less than 70"
    else:
        logger.warning("VCP L1: no rs_rating on the universe -- Trend Template RS leg skipped")

    return df[mask.fillna(False)]


# =====================================================================
# Layer 2 — Precise VCP detection on OHLC history
# =====================================================================


def layer2_detect_vcp(ohlc_data: pd.DataFrame, ticker: str) -> dict | None:
    """Precise VCP detection using OHLC history."""
    if len(ohlc_data) < 40:
        return None

    close = ohlc_data['Close'].values
    high = ohlc_data['High'].values
    low = ohlc_data['Low'].values
    volume = ohlc_data['Volume'].values

    # 1. Find swing highs (local maxima over 5-bar window)
    swing_highs = []
    swing_lows = []
    window = 5

    for i in range(window, len(high) - window):
        if high[i] == max(high[i-window:i+window+1]):
            swing_highs.append((i, high[i]))
        if low[i] == min(low[i-window:i+window+1]):
            swing_lows.append((i, low[i]))

    if len(swing_highs) < 2:
        return None

    # 2. Build contraction sequence
    contractions = []
    for i, (hi_idx, hi_val) in enumerate(swing_highs):
        # Find deepest low between this high and next high
        next_hi_idx = swing_highs[i+1][0] if i+1 < len(swing_highs) else len(close)-1
        lows_between = [(idx, val) for idx, val in swing_lows
                       if hi_idx < idx < next_hi_idx]
        if not lows_between:
            continue
        deepest = min(lows_between, key=lambda x: x[1])
        depth = (hi_val - deepest[1]) / hi_val * 100

        if 2 < depth < 75:  # Filter noise and crashes
            contractions.append({
                'high_idx': hi_idx, 'high': hi_val,
                'low_idx': deepest[0], 'low': deepest[1],
                'depth_pct': depth,
                'avg_volume': float(np.mean(volume[hi_idx:deepest[0]+1]))
            })

    # Minervini (Trade Like a Stock Market Wizard, 2013, ch. 10 -- the VCP):
    # "typically two to four contractions", "as many as five or six". 2..6 is
    # his stated range; the floor was already here, the ceiling was not (one of
    # the 27 names on 2026-09-17 had exactly 6, none more -- audit 09-18 #43).
    if not (MIN_CONTRACTIONS <= len(contractions) <= MAX_CONTRACTIONS):
        return None

    # 3. Verify contractions are getting shallower
    depths = [c['depth_pct'] for c in contractions[-4:]]  # Last 4 contractions
    is_contracting = all(depths[i] >= depths[i+1] for i in range(len(depths)-1))

    if not is_contracting:
        return None

    # 4. Each contraction about half the prior one. Minervini: "each
    # successive contraction is generally contained to about half (plus or
    # minus a reasonable amount) of the previous pullback or contraction".
    # The HALF is his; the tolerance band RATIO_BAND (0.30-0.75) is OURS -- he
    # gives no number for "a reasonable amount" -- kept from the pre-09-18
    # code, not newly chosen, and flagged self-made in METRIC_SOURCES.
    ratios = [depths[i+1] / depths[i] for i in range(len(depths)-1) if depths[i] > 0]
    ratios_healthy = all(RATIO_BAND[0] <= r <= RATIO_BAND[1] for r in ratios) if ratios else False

    # 5. Volume contracts with price. Minervini: volume contracts as the
    # contractions tighten, drying up at the right side of the base. He gives
    # no ratio, so the reading is the plain one: each contraction's average
    # volume no higher than the one before (no threshold invented).
    vols = [c['avg_volume'] for c in contractions[-4:]]
    vol_declining = all(vols[i] >= vols[i+1] for i in range(len(vols)-1))

    # 2026-09-18 (Andy: 「全部按原文」): both are CONSTITUENT conditions of the
    # pattern, not annotations. Until today they were computed and shipped as
    # flags while every row passed regardless -- 27 names on vcp.json 09-17,
    # 4 of them met both (audit 09-18 #43).
    if not (ratios_healthy and vol_declining):
        return None

    # 6. Calculate pivot and distance
    pivot = contractions[-1]['high']
    current_price = close[-1]
    pct_to_pivot = (pivot - current_price) / current_price * 100

    if pct_to_pivot > 10 or pct_to_pivot < -2:
        return None  # Too far from pivot or already broken out

    return {
        'ticker': ticker,
        'num_contractions': len(contractions),
        'max_depth': round(contractions[0]['depth_pct'], 1),
        'last_depth': round(contractions[-1]['depth_pct'], 1),
        'pivot': round(pivot, 2),
        'pct_to_pivot': round(pct_to_pivot, 1),
        'volume_declining': vol_declining,
        'ratios_healthy': ratios_healthy,
    }


# =====================================================================
# Pipeline orchestrator
# =====================================================================


def run_vcp_pipeline(universe: pd.DataFrame, yf_adapter: Any) -> Dict[str, Any]:
    """Run the full two-layer VCP detection pipeline.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz-sourced universe with standard columns (close, market_cap,
        sma50_dist, sma200_dist, low_52w, high_52w, perf_1w, perf_1m,
        ticker).
    yf_adapter : object
        An adapter instance that exposes ``fetch_ohlc(tickers, period)``
        returning ``dict[str, pd.DataFrame]`` keyed by ticker.

    Returns
    -------
    dict
        ``{'count': N, 'results': [<layer2_detect_vcp output>, ...]}``
        Only tickers that pass both layers are included.
    """
    if universe.empty:
        logger.warning("Empty universe passed to VCP pipeline")
        return {"count": 0, "results": []}

    # --- Layer 1: coarse filter on Finviz data ---
    candidates = layer1_finviz_filter(universe)
    candidate_tickers = candidates["ticker"].tolist()

    logger.info(
        "VCP Layer 1: %d / %d stocks pass coarse filter",
        len(candidate_tickers),
        len(universe),
    )

    if not candidate_tickers:
        return {"count": 0, "results": []}

    # --- Fetch OHLC history for candidates ---
    try:
        ohlc_dict = yf_adapter.fetch_ohlc(candidate_tickers, period="90d")
    except Exception as exc:
        logger.error("VCP: failed to fetch OHLC data: %s", exc)
        return {"count": 0, "results": []}

    # --- Layer 2: precise VCP detection on each candidate ---
    results: List[Dict[str, Any]] = []
    for ticker in candidate_tickers:
        ohlc = ohlc_dict.get(ticker)
        if ohlc is None or ohlc.empty:
            logger.debug("VCP Layer 2: no OHLC data for %s — skipping", ticker)
            continue

        try:
            vcp = layer2_detect_vcp(ohlc, ticker)
        except Exception as exc:
            logger.warning("VCP Layer 2: error processing %s: %s", ticker, exc)
            continue

        if vcp is not None:
            results.append(vcp)

    # Sort by proximity to pivot (closest first)
    results.sort(key=lambda r: abs(r["pct_to_pivot"]))

    logger.info(
        "VCP Layer 2: %d / %d candidates confirmed as VCP patterns",
        len(results),
        len(candidate_tickers),
    )

    return {"count": len(results), "results": results}
