"""Screener pipeline orchestrator.

Entry point that runs the full data pipeline end-to-end:
1. Fetches Finviz universe data (or yfinance fallback)
2. Fetches yfinance ETF data (144 tickers)
3. Fetches MA signals for SPY, QQQ, IWM, RSP
4. Runs all 9 screeners
5. Enriches results with ATR coloring
6. Saves JSON outputs to data/output/
7. Updates history for Stockbee ratio

Per plan.md section 2.6.
"""
import json
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.adapters.finviz_adapter import FinvizAdapter
from pipeline.adapters.yfinance_adapter import YfinanceAdapter
from pipeline.screeners.momentum_97 import run as run_momentum_97
from pipeline.screeners.gainers_4pct import run as run_gainers_4pct
from pipeline.screeners.vol_up_gainers import run as run_vol_up_gainers
from pipeline.screeners.ema21_watch import run as run_ema21_watch
from pipeline.screeners.healthy_charts import run as run_healthy_charts
from pipeline.screeners.episodic_pivot import run as run_episodic_pivot
from pipeline.screeners.stockbee_ratio import run as run_stockbee_ratio
from pipeline.screeners.breadth_metrics import run as run_breadth_metrics
from pipeline.screeners.vcp_detector import run_vcp_pipeline
from pipeline.screeners.atr_enrichment import enrich_with_atr

OUTPUT_DIR = Path('data/output')
HISTORY_DIR = Path('data/history')

# Fallback universe: 200 liquid large-cap stocks for when Finviz is unavailable
FALLBACK_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'LLY', 'AVGO',
    'JPM', 'V', 'UNH', 'XOM', 'MA', 'JNJ', 'PG', 'COST', 'HD', 'ABBV',
    'MRK', 'CRM', 'AMD', 'NFLX', 'BAC', 'ORCL', 'CVX', 'KO', 'PEP', 'ADBE',
    'TMO', 'WMT', 'MCD', 'CSCO', 'ABT', 'ACN', 'LIN', 'DHR', 'CMCSA', 'NKE',
    'TXN', 'PM', 'NEE', 'INTC', 'VZ', 'IBM', 'QCOM', 'INTU', 'UNP', 'HON',
    'LOW', 'SPGI', 'COP', 'AMGN', 'RTX', 'BKNG', 'GE', 'CAT', 'AXP', 'NOW',
    'BA', 'PFE', 'SBUX', 'T', 'ISRG', 'ELV', 'MDT', 'BLK', 'GILD', 'DE',
    'GS', 'VRTX', 'ADP', 'SYK', 'MMC', 'SCHW', 'LRCX', 'TJX', 'MDLZ', 'ADI',
    'PGR', 'CB', 'CVS', 'ETN', 'REGN', 'BSX', 'MU', 'PANW', 'SNPS', 'KLAC',
    'AMAT', 'CI', 'ZTS', 'CME', 'FI', 'CDNS', 'SHW', 'DUK', 'HUM', 'ITW',
    'SO', 'ICE', 'CL', 'EMR', 'MCO', 'PH', 'ORLY', 'NOC', 'EOG', 'WM',
    'CSX', 'GD', 'AON', 'APD', 'FDX', 'NSC', 'SLB', 'TDG', 'FCX', 'PXD',
    'AJG', 'CARR', 'MSCI', 'WELL', 'MPC', 'PCAR', 'TT', 'PSX', 'OXY', 'SRE',
    'MCHP', 'FTNT', 'DXCM', 'ROP', 'AZO', 'CTAS', 'TEL', 'NEM', 'KMB', 'OKE',
    'AIG', 'DHI', 'CPRT', 'O', 'IDXX', 'ECL', 'MNST', 'STZ', 'D', 'BK',
    'HCA', 'GIS', 'KR', 'FAST', 'ON', 'CRWD', 'SMCI', 'PLTR', 'COIN', 'DASH',
    'MRVL', 'CEG', 'FANG', 'VST', 'WDAY', 'TEAM', 'DDOG', 'NET', 'ZS', 'SNOW',
    'ARM', 'SHOP', 'SQ', 'MELI', 'NU', 'UBER', 'ABNB', 'LULU', 'DECK', 'ELF',
    'APP', 'RKLB', 'AXON', 'TTD', 'HUBS', 'ENPH', 'SEDG', 'RIVN', 'LCID', 'CHWY',
    'DUOL', 'TOST', 'BROS', 'CAVA', 'BIRK', 'GEV', 'FICO', 'ANET', 'MPWR', 'WING',
]


def build_fallback_universe(yf_adapter: YfinanceAdapter) -> pd.DataFrame:
    """Build a universe DataFrame from yfinance when Finviz is unavailable.
    Downloads ~200 liquid stocks and computes the standard columns.
    """
    import yfinance as yf

    logger = logging.getLogger(__name__)
    logger.info(f"Building fallback universe from {len(FALLBACK_TICKERS)} stocks via yfinance...")

    # Batch download 6 months of data
    data = yf.download(FALLBACK_TICKERS, period='6mo', group_by='ticker',
                       progress=False, threads=True)

    rows = []
    for ticker in FALLBACK_TICKERS:
        try:
            if len(FALLBACK_TICKERS) == 1:
                hist = data.dropna()
            else:
                hist = data[ticker].dropna()

            if len(hist) < 50:
                continue

            close = float(hist['Close'].iloc[-1])
            prev_close = float(hist['Close'].iloc[-2])
            high_52w = float(hist['High'].max())
            low_52w = float(hist['Low'].min())

            sma20 = float(hist['Close'].rolling(20).mean().iloc[-1])
            sma50 = float(hist['Close'].rolling(50).mean().iloc[-1])
            sma40 = float(hist['Close'].rolling(40).mean().iloc[-1]) if len(hist) >= 40 else None
            sma200 = float(hist['Close'].rolling(200).mean().iloc[-1]) if len(hist) >= 200 else None

            # ATR calculation
            from pipeline.adapters.yfinance_adapter import calculate_atr
            atr = calculate_atr(hist)

            avg_vol = float(hist['Volume'].rolling(20).mean().iloc[-1])
            vol = float(hist['Volume'].iloc[-1])

            rows.append({
                'ticker': ticker,
                'close': close,
                'change_pct': (close - prev_close) / prev_close,
                'perf_1w': (close - float(hist['Close'].iloc[-5])) / float(hist['Close'].iloc[-5]) if len(hist) >= 5 else None,
                'perf_1m': (close - float(hist['Close'].iloc[-21])) / float(hist['Close'].iloc[-21]) if len(hist) >= 21 else None,
                'perf_3m': (close - float(hist['Close'].iloc[-63])) / float(hist['Close'].iloc[-63]) if len(hist) >= 63 else None,
                'perf_6m': (close - float(hist['Close'].iloc[-126])) / float(hist['Close'].iloc[-126]) if len(hist) >= 126 else None,
                'perf_1y': None,  # Only 6mo of data
                'perf_ytd': None,
                'sma20_dist': (close - sma20) / sma20 if sma20 else None,
                'sma50_dist': (close - sma50) / sma50 if sma50 else None,
                'sma40_dist': (close - sma40) / sma40 if sma40 else None,
                'sma200_dist': (close - sma200) / sma200 if sma200 else None,
                'atr': atr,
                'rel_volume': vol / avg_vol if avg_vol > 0 else None,
                'avg_volume': avg_vol,
                'volume': vol,
                'market_cap': None,  # Not available from yfinance batch
                'sector': None,
                'industry': None,
                'high_52w': (close - high_52w) / high_52w,
                'low_52w': (close - low_52w) / low_52w,
                'eps_growth_next_y': None,
            })
        except Exception as e:
            logger.debug(f"Fallback universe: skipping {ticker}: {e}")

    df = pd.DataFrame(rows)
    logger.info(f"Fallback universe built: {len(df)} stocks")
    return df


def _json_serializer(obj):
    """Handle numpy/pandas types in JSON serialization."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if pd.isna(obj):
        return None
    return str(obj)


def compute_universe_scores(universe: pd.DataFrame) -> pd.DataFrame:
    """Compute RS scores, composite metrics, and derived columns for the screener."""
    df = universe.copy()

    # Coerce performance columns to numeric
    perf_cols = ['perf_1w', 'perf_1m', 'perf_3m', 'perf_6m', 'perf_1y']
    for col in perf_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- Price RS percentile ranks (0-99 scale) ---
    df['rs_21d'] = df['perf_1m'].rank(pct=True, na_option='bottom') * 99
    df['rs_63d'] = df['perf_3m'].rank(pct=True, na_option='bottom') * 99
    df['rs_126d'] = df['perf_6m'].rank(pct=True, na_option='bottom') * 99

    # --- IBD-style RS (40% 3mo + 40% 6mo + 20% 1yr) ---
    r3 = df['perf_3m'].rank(pct=True, na_option='bottom') * 99
    r6 = df['perf_6m'].rank(pct=True, na_option='bottom') * 99
    r1y = df['perf_1y'].rank(pct=True, na_option='bottom') * 99
    df['rs_ibd'] = (0.4 * r3 + 0.4 * r6 + 0.2 * r1y)

    # --- F score (fundamental) ---
    eps = pd.to_numeric(df.get('eps_growth_next_y', pd.Series(dtype=float)), errors='coerce')
    rev = pd.to_numeric(df.get('revenue_growth', pd.Series(dtype=float)), errors='coerce')
    fundamental = eps.copy()
    both_available = eps.notna() & rev.notna()
    fundamental.loc[both_available] = (eps[both_available] + rev[both_available]) / 2
    df['f_score'] = fundamental.rank(pct=True, na_option='bottom') * 99
    df['f_score'] = df['f_score'].fillna(50)

    # --- I score (industry RS) ---
    industry_rs = df.groupby('industry')['rs_63d'].transform('mean')
    df['i_score'] = industry_rs.rank(pct=True, na_option='bottom') * 99

    # --- H score (hybrid composite) ---
    # Weights: F:2, I:3, 21d:1, 63d:2, 126d:2 -> total 10
    df['h_score'] = (
        df['f_score'] * 2 +
        df['i_score'] * 3 +
        df['rs_21d'] * 1 +
        df['rs_63d'] * 2 +
        df['rs_126d'] * 2
    ) / 10

    # --- Derived technical columns ---
    df['adr_pct'] = pd.to_numeric(df['atr'], errors='coerce') / pd.to_numeric(df['close'], errors='coerce') * 100
    df['ema21_r'] = 1 + pd.to_numeric(df['sma20_dist'], errors='coerce')
    df['sma50_r'] = 1 + pd.to_numeric(df['sma50_dist'], errors='coerce')

    # 52W high distance
    h = pd.to_numeric(df['high_52w'], errors='coerce')
    c = pd.to_numeric(df['close'], errors='coerce')
    if h.mean() > 1:  # absolute prices, not fractions
        df['high_52w_dist'] = (c - h) / h
    else:
        df['high_52w_dist'] = h

    # Round score columns to integers
    for col in ['rs_21d', 'rs_63d', 'rs_126d', 'rs_ibd', 'f_score', 'i_score', 'h_score']:
        df[col] = df[col].round(0).astype('Int64')

    # --- Performance percentile ranks (0-1 scale, relative to full universe) ---
    if 'perf_1w' in df.columns:
        df['perf_1w_pctile'] = df['perf_1w'].rank(pct=True, na_option='bottom').round(4)
    if 'perf_3m' in df.columns:
        df['perf_3m_pctile'] = df['perf_3m'].rank(pct=True, na_option='bottom').round(4)

    # --- Momentum 97 flag: 1W pctile >= 0.97 AND 3M pctile >= 0.85 ---
    _w = df.get('perf_1w_pctile', pd.Series(0, index=df.index))
    _m = df.get('perf_3m_pctile', pd.Series(0, index=df.index))
    df['momentum_97'] = (_w >= 0.97) & (_m >= 0.85)

    # Round derived columns to 4 decimals
    for col in ['adr_pct', 'ema21_r', 'sma50_r', 'high_52w_dist']:
        df[col] = df[col].round(4)

    # Round new enrichment columns
    for col in ['from_open_pct', 'dcr_pct', 'ema21_low_dist']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').round(4)

    if 'vcs' in df.columns:
        df['vcs'] = pd.to_numeric(df['vcs'], errors='coerce').round(1)

    return df


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logger = logging.getLogger(__name__)

    timestamp = datetime.now(timezone.utc).isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    finviz = FinvizAdapter()
    yf_adapter = YfinanceAdapter()

    # 1. Fetch universe (Finviz primary, yfinance fallback)
    universe = None
    try:
        logger.info("Fetching Finviz universe...")
        universe = finviz.fetch_universe()
        logger.info(f"Got {len(universe)} stocks from Finviz")
        # Finviz free-tier HTML only provides Overview columns.
        # Enrich with perf/technical data from yfinance.
        logger.info("Enriching Finviz universe with yfinance data...")
        universe = yf_adapter.enrich_universe(universe)
    except Exception as e:
        logger.warning(f"Finviz unavailable: {e}")
        logger.info("Using yfinance fallback universe...")
        universe = build_fallback_universe(yf_adapter)
        logger.info(f"Fallback universe: {len(universe)} stocks")

    # Compute universe scores for screener page
    scored_universe = compute_universe_scores(universe)

    # 2. Fetch ETF data
    logger.info("Fetching ETF data...")
    etf_data = yf_adapter.fetch_etf_data()
    logger.info(f"Got {len(etf_data)} ETFs from yfinance")

    # 3. Fetch MA signals
    logger.info("Fetching MA signals...")
    signals = yf_adapter.fetch_ma_data(['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC'])

    # 4. Run screeners
    logger.info("Running screeners...")
    results = {
        'momentum_97': run_momentum_97(universe),
        'gainers_4pct': run_gainers_4pct(universe),
        'vol_up_gainers': run_vol_up_gainers(universe),
        'ema21_watch': run_ema21_watch(universe),
        'healthy_charts': run_healthy_charts(universe),
        'episodic_pivot': run_episodic_pivot(universe),
    }

    # 5. Stockbee ratio (needs history)
    results['stockbee_ratio'] = run_stockbee_ratio(
        universe, str(HISTORY_DIR / 'breadth_history.json')
    )

    # 5b. Breadth metrics (Stockbee MM + classic breadth)
    logger.info("Running breadth metrics...")
    spx_close = signals.get('^GSPC', {}).get('close')
    breadth_result = run_breadth_metrics(
        universe,
        str(HISTORY_DIR / 'breadth_metrics_history.json'),
        str(HISTORY_DIR / 'breadth_archive.csv'),
        spx_close=spx_close,
    )

    # 6. VCP (two-layer — skip if universe too small)
    if len(universe) >= 50:
        logger.info("Running VCP detection...")
        results['vcp'] = run_vcp_pipeline(universe, yf_adapter)
    else:
        logger.info("Skipping VCP (universe too small)")
        results['vcp'] = {'count': 0, 'results': []}

    # 7. ATR enrichment
    for key in results:
        data = results[key]
        if isinstance(data, dict) and 'tickers' in data:
            data['tickers'] = enrich_with_atr(data['tickers'], universe)
        elif isinstance(data, dict) and 'results' in data:
            data['results'] = enrich_with_atr(data['results'], universe)
        for bucket_key in ('buckets', 'rs_groups'):
            if isinstance(data, dict) and bucket_key in data:
                for bucket_name, ticker_list in data[bucket_key].items():
                    data[bucket_key][bucket_name] = enrich_with_atr(ticker_list, universe)

    # 8. Save outputs
    for name, data in results.items():
        output = {'timestamp': timestamp, **data}
        (OUTPUT_DIR / f'{name}.json').write_text(
            json.dumps(output, indent=2, default=_json_serializer)
        )
        logger.info(f"Saved {name}.json")

    # Save signals
    (OUTPUT_DIR / 'signals.json').write_text(json.dumps(
        {'timestamp': timestamp, **signals}, indent=2, default=_json_serializer
    ))
    logger.info("Saved signals.json")

    # Save breadth metrics
    (OUTPUT_DIR / 'breadth.json').write_text(json.dumps(
        {'timestamp': timestamp, **breadth_result}, indent=2, default=_json_serializer
    ))
    logger.info("Saved breadth.json")

    # Save ETF data
    (OUTPUT_DIR / 'etf_data.json').write_text(
        etf_data.to_json(orient='records', indent=2)
    )
    logger.info("Saved etf_data.json")

    # Save full universe for screener page
    universe_cols = [
        'ticker', 'close', 'change_pct', 'perf_1w', 'perf_1m', 'perf_3m',
        'perf_6m', 'perf_1y', 'perf_ytd',
        'sma20_dist', 'sma50_dist', 'sma40_dist', 'sma200_dist',
        'atr', 'rel_volume', 'avg_volume', 'volume',
        'market_cap', 'sector', 'industry',
        'high_52w', 'low_52w', 'eps_growth_next_y',
        'rs_21d', 'rs_63d', 'rs_126d', 'rs_ibd',
        'f_score', 'i_score', 'h_score',
        'adr_pct', 'ema21_r', 'sma50_r', 'high_52w_dist',
        'from_open_pct', 'dcr_pct', 'pocket_pivot', 'pp_count_30d',
        'trend_base', 'vcs', 'ema21_low_dist',
        'perf_1w_pctile', 'perf_3m_pctile', 'momentum_97',
    ]
    export_cols = [c for c in universe_cols if c in scored_universe.columns]
    # Convert to object dtype so NaN becomes None (valid JSON null, not NaN)
    export_df = scored_universe[export_cols].astype(object).where(
        scored_universe[export_cols].notna(), None
    )
    universe_export = {
        'timestamp': timestamp,
        'count': len(scored_universe),
        'rows': export_df.to_dict('records'),
    }
    (OUTPUT_DIR / 'universe.json').write_text(
        json.dumps(universe_export, indent=None, default=_json_serializer)
    )
    logger.info("Saved universe.json")

    # Summary
    total_tickers = sum(
        d.get('count', 0) for d in results.values() if isinstance(d, dict)
    )
    logger.info(f"Done. {len(results)} screeners completed. Universe: {len(universe)} stocks.")


if __name__ == '__main__':
    main()
