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
    Coarse filter on the Finviz universe.  Reduces ~2 400 stocks down to
    ~100-200 candidates using price, market-cap, moving-average, and
    performance criteria.

Layer 2 (``layer2_detect_vcp``):
    Precise pattern detection on 90-day OHLCV history fetched via
    yfinance.  Finds swing highs/lows, builds a contraction sequence,
    and verifies that contractions are progressively shallower with
    healthy depth ratios (30-75 %) and declining volume.

``run_vcp_pipeline`` orchestrates both layers end-to-end.

Reference: plan.md section 2.5
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =====================================================================
# Layer 1 — Finviz coarse filter
# =====================================================================


def layer1_finviz_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Coarse filter using Finviz data. ~2400 -> ~100-200 candidates."""
    # Ensure numeric types — scraped data may have None/object columns
    num_cols = ['close', 'market_cap', 'sma50_dist', 'sma200_dist',
                'low_52w', 'high_52w', 'perf_1w', 'perf_1m']
    df = df.copy()
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    mask = (
        df['close'].notna() &
        df['perf_1w'].notna() &
        df['perf_1m'].notna() &
        (df['close'] > 10) &
        (df['market_cap'] >= 1e9) &
        (df['sma50_dist'] > 0) &
        (df['sma200_dist'] > 0) &
        (df['low_52w'] >= 0.30) &
        (df['high_52w'] >= -0.25) &
        (df['perf_1m'] > 0) &
        (df['perf_1w'].abs() < df['perf_1m'].abs())
    )
    return df[mask]


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

    if len(contractions) < 2:
        return None

    # 3. Verify contractions are getting shallower
    depths = [c['depth_pct'] for c in contractions[-4:]]  # Last 4 contractions
    is_contracting = all(depths[i] >= depths[i+1] for i in range(len(depths)-1))

    if not is_contracting:
        return None

    # 4. Check depth ratios (each ~50% of prior, tolerance 30-75%)
    ratios = [depths[i+1] / depths[i] for i in range(len(depths)-1) if depths[i] > 0]
    ratios_healthy = all(0.3 <= r <= 0.75 for r in ratios) if ratios else False

    # 5. Check volume declining
    vols = [c['avg_volume'] for c in contractions[-4:]]
    vol_declining = all(vols[i] >= vols[i+1] for i in range(len(vols)-1))

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
