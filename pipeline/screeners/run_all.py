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
from pipeline.marketcal import last_completed_session, last_trading_day

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
    logger = logging.getLogger(__name__)
    df = universe.copy()

    # Coerce performance columns to numeric
    perf_cols = ['perf_1w', 'perf_1m', 'perf_3m', 'perf_6m', 'perf_1y']
    for col in perf_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- Tradeable mask ---
    # Every score below is a *cross-sectional percentile*, so the field it is
    # measured against is part of the definition. Ranking against all 5,615
    # rows meant "RS 90" claimed to beat 90% of a universe where 2,408 names
    # cannot be traded at this account's size -- a percentile against a field
    # you cannot buy. The FIELD is therefore the tradeable subset: its members
    # are ranked among themselves and their scores are unchanged by anything
    # outside it.
    #
    # 2026-08-17 ("全部打分"): the rows outside the field used to be left null
    # -- 30% of the Screener page had no RS at all. They now get a score too,
    # read off the SAME ruler: where their perf value would fall in the
    # tradeable distribution. So RS 90 always means "would beat 90% of the
    # tradeable field", whichever row carries it; the `tradeable` column says
    # whether the name is in that field or merely measured against it. A row
    # with no perf value gets no score (inside the field a missing value takes
    # the lowest rank to keep everyone else's denominator; outside it there is
    # no denominator to protect).
    from pipeline.themes import is_tradeable  # noqa: PLC0415
    tradeable = df.apply(is_tradeable, axis=1)
    df['tradeable'] = tradeable
    logger.info("Scores computed on %d tradeable of %d rows",
                int(tradeable.sum()), len(df))

    def rank_tradeable(col: str, na: str = 'top') -> pd.Series:
        """Percentile rank within the tradeable set; NaN for everyone else.
        `na='keep'` ranks among the field members that HAVE a value and leaves
        the missing ones NaN (used by f_score, where missing means unknown).

        `na_option='top'`, not `'bottom'`. Pandas names these by where the NaN
        sits in the *ranking order*, not by where it lands on the score: with
        `'bottom'` a missing value takes the LARGEST rank, which after the x99
        becomes 99 -- top of the scale. That is what shipped, and it meant a row
        with no quarterly return was not merely excluded from the leaders, it
        WAS the leader: on 2026-08-09, 27 tradeable names had no perf_3m and
        every one of them scored rs_63d = 99 against a median of 49; 61 had no
        perf_6m and scored 98. Those scores then carried into rs_ibd at 0.4
        weight each, so a handful of names sat at the top of the IBD list for
        the single reason that we knew nothing about them.

        `'top'` gives a missing value the smallest rank instead, so no reading
        scores as the strongest reading. It still occupies a rank rather than
        being dropped, which keeps the denominator -- and therefore every other
        name's percentile -- unchanged.
        """
        out = pd.Series(np.nan, index=df.index, dtype=float)
        sub = df.loc[tradeable, col]
        out.loc[tradeable] = sub.rank(pct=True, na_option=na) * 99
        return out

    def score_against_tradeable(col: str, na: str = 'top') -> pd.Series:
        """`rank_tradeable` for the field, plus every other row placed on the
        field's ruler: its percentile among the tradeable values of `col`
        (average of the <= and < counts, i.e. the same mid-rank convention
        pandas' 'average' method uses for ties). Tradeable rows are returned
        bit-for-bit as `rank_tradeable` gives them."""
        out = rank_tradeable(col, na)
        ref = np.sort(pd.to_numeric(df.loc[tradeable, col], errors='coerce').dropna().to_numpy(dtype=float))
        if len(ref) == 0:
            return out
        # rank_tradeable's denominator: the whole field under 'top' (NaNs take
        # the lowest ranks), only the valued members under 'keep'
        n_field = int(tradeable.sum()) if na == 'top' else len(ref)
        others = ~tradeable & df[col].notna()
        x = pd.to_numeric(df.loc[others, col], errors='coerce').to_numpy(dtype=float)
        lo = np.searchsorted(ref, x, side='left')
        hi = np.searchsorted(ref, x, side='right')
        # inside the field a value with k values below it and t ties has
        # average rank k + (t+1)/2 ; the NaN block (n_field - len(ref)) sits
        # below every real value under na_option='top', so it counts in k.
        nan_block = n_field - len(ref)
        pos = nan_block + lo + (hi - lo + 1) / 2.0
        out.loc[others] = pos / n_field * 99
        return out

    # --- Price RS percentile ranks (0-99 scale) ---
    #
    # NAMING: these say sessions and mean calendar months. The underlying
    # perf_1m/3m/6m come from Finviz's Perf Month / Perf Quart / Perf Half,
    # which are calendar windows; yfinance enrichment only fills the gaps, and
    # it fills them with 21/63/126 *sessions*. Measured on 129 names with local
    # bars, under 4% of stored values match a session-based recompute -- so the
    # column is calendar-based in all but a rounding of cases.
    #
    # rs_1m / rs_3m / rs_6m are the honest names and are the ones to use. The
    # rs_21d / rs_63d / rs_126d aliases are kept only until the frontend moves
    # off them (ResultsTable, screenerFilter, TickerStats, ThemeMembers all
    # read the old keys today). Same Series object, not a recomputation.
    #
    # The ETF side is the opposite and stays that way: etf_data has no vendor
    # perf at all, so its perf_1w/1m/3m really are 5/21/63 sessions. Dashboard's
    # "1M" and the screener's "1M" are therefore different months by a few days.
    df['rs_1m'] = score_against_tradeable('perf_1m')
    df['rs_3m'] = score_against_tradeable('perf_3m')
    df['rs_6m'] = score_against_tradeable('perf_6m')
    df['rs_21d'] = df['rs_1m']
    df['rs_63d'] = df['rs_3m']
    df['rs_126d'] = df['rs_6m']

    # --- IBD-style RS: 40% 3mo + 40% 6mo + 20% 1yr ---
    #
    # What it looks for: leadership that has already been established. Every
    # window is a quarter or longer, so a name only scores well if it has been
    # ahead of the field for months and stayed there. It answers "who has been
    # winning", and it is the number to sort by when you want the list of names
    # institutions have been accumulating.
    #
    # What it structurally cannot see:
    #   * anything listed under a year ago -- perf_1y is missing, so recent
    #     IPOs and 2024-25 listings cannot reach the top however they trade
    #   * a move that started this month -- three long windows need a quarter
    #     before they register it
    #   * a leader that has stopped. A name can hold a top score on last
    #     year's advance while going nowhere now; this measures the record,
    #     not the current state. Read it beside rs_1m to see which it is.
    df['rs_ibd'] = (0.4 * df['rs_3m'] + 0.4 * df['rs_6m']
                    + 0.2 * score_against_tradeable('perf_1y'))

    # --- F score (fundamental) ---
    # Source since 2026-08-17: fundamentals_store (yfinance primary, Finviz
    # backup) -- see pipeline/adapters/fundamentals_store.py. Before that the
    # two columns were empty and this was a constant 50 for every row.
    # Rank each input on the tradeable ruler, THEN average the ranks. Averaging
    # the raw rates (the old formula) let one input drown the other: forward/
    # trailing EPS on a near-zero trailing EPS prints 19x and no revenue figure
    # can answer it. Ranks are bounded; a 19x and a 2x are both "top decile".
    # A row with only one of the two uses that one; with neither it is 50 --
    # "unknown", not "worst" (the old na_option='top' put unknowns at the
    # bottom, which at partial coverage squeezed every known name into the
    # top few points; the store fills over ~8 nights, and meanwhile the H
    # score must not rank the market by whether Yahoo had been asked yet).
    df['_eps'] = pd.to_numeric(df.get('eps_growth_next_y', pd.Series(dtype=float)), errors='coerce')
    df['_rev'] = pd.to_numeric(df.get('revenue_growth', pd.Series(dtype=float)), errors='coerce')
    r_eps = score_against_tradeable('_eps', na='keep')
    r_rev = score_against_tradeable('_rev', na='keep')
    df['f_score'] = pd.concat([r_eps, r_rev], axis=1).mean(axis=1, skipna=True).fillna(50.0)
    df.drop(columns=['_eps', '_rev'], inplace=True)

    # --- I score (industry RS) ---
    # Median, not mean: one Finviz corporate-action artefact (an aerospace row
    # printed +31,192% for perf_1m) moves its whole industry's mean score and
    # therefore every constituent's i_score, which carries weight 3 of 10 in
    # h_score. The median is unaffected.
    # Industry median over tradeable members only, to match the field the
    # constituent ranks were measured against. groups.json aggregates the same
    # way, so the two industry readings now describe the same member set.
    # A non-tradeable row reads its industry's (tradeable-member) median and is
    # placed on the tradeable ruler like the RS columns; an industry with no
    # tradeable member has no median and its rows get no i_score.
    industry_rs = df.loc[tradeable].groupby('industry')['rs_3m'].median()
    df['_i_raw'] = df['industry'].map(industry_rs)
    df['i_score'] = score_against_tradeable('_i_raw')
    df.drop(columns=['_i_raw'], inplace=True)

    # --- H score (hybrid composite) ---
    # Weights: F:2, I:3, 21d:1, 63d:2, 126d:2 -> total 10
    df['h_score'] = (
        df['f_score'] * 2 +
        df['i_score'] * 3 +
        df['rs_1m'] * 1 +
        df['rs_3m'] * 2 +
        df['rs_6m'] * 2
    ) / 10

    # --- Liquid Leader (course definition, SwingMasterclass M2_L09) ---
    # ADV >= 2M shares, above the 50-SMA, RS rank top 20% (rs_3m >= 80 on the
    # tradeable percentile). A QUALIFICATION list -- the water the entries
    # should be fished from -- not an entry. Alex Desjardins's "Liquid
    # Leaders" and Andy's course teach the same thing. Missing inputs -> False.
    _av = pd.to_numeric(df.get('avg_volume', pd.Series(dtype=float)), errors='coerce')
    _sd = pd.to_numeric(df.get('sma50_dist', pd.Series(dtype=float)), errors='coerce')
    # `tradeable` is part of the definition now that rs_3m exists outside the
    # field too: a sub-$2 name printing 2M shares is not a liquid leader.
    df['liquid_leader'] = ((_av >= 2_000_000) & (_sd > 0) & (df['rs_3m'] >= 80)
                           & tradeable).fillna(False).astype(bool)

    # --- Derived technical columns ---
    df['adr_pct'] = pd.to_numeric(df['atr'], errors='coerce') / pd.to_numeric(df['close'], errors='coerce') * 100
    # These two are RATIOS (close / MA), not ATR multiples, despite the `_r`.
    # Kept unchanged because things read them; the ATR reading is the separate
    # column below. See data/reference/screener_inventory_2026-08-17.md.
    df['ema21_r'] = 1 + pd.to_numeric(df['sma20_dist'], errors='coerce')
    df['sma50_r'] = 1 + pd.to_numeric(df['sma50_dist'], errors='coerce')

    # --- ATR Matrix: how many ATRs the price sits above its 50-day SMA ---
    # Steve Jacobs's framing (learnt from @jfsrev and @RealSimpleAriel), and
    # the same number oratnek uses as both an entry gate (<5, ideally <4) and
    # an exit trigger (>=7 -> trim). Jacobs's bands: <0 ignore, 0-4x entry,
    # 5-7x hold, >=7x scale out.
    #
    # We carry sma50_dist = (close - SMA50)/SMA50 -- verified against
    # date-aligned bars on 2026-08-14, five of six names to four decimals --
    # so SMA50 = close/(1+dist) and the gap is close*dist/(1+dist). Dropping
    # that denominator overstates a name 30% above its line by 30%, precisely
    # in the extended tail this column exists to flag.
    # One implementation with the atr_ext badge (atr_enrichment.py): the two
    # used to be different maths for the same quantity.
    from pipeline.screeners.atr_enrichment import atr_multiple_from_sma50
    df['atr_from_sma50'] = atr_multiple_from_sma50(
        df['close'], df['atr'], df['sma50_dist'])

    # --- (close - EMA21) / ATR: the reading the 21EMA Watch preset always
    # meant. Its filter used to point at ema21_r, which is close/SMA20 -- a
    # ratio near 1.0 -- so "within -0.5..1 ATR of the 21EMA" silently became
    # "price at or below the SMA20". Same helper, same floor, same null rules
    # as atr_from_sma50; the enrichment exports the true EMA21 for this. The
    # fallback universe has no ema21 column, so it must degrade to null.
    if 'ema21' in df.columns:
        _e = pd.to_numeric(df['ema21'], errors='coerce')
        _c = pd.to_numeric(df['close'], errors='coerce')
        # dist form: (close - ema21)/ema21, valid where ema21 > 0
        _d21 = ((_c - _e) / _e).where(_e > 0)
        df['ema21_atr_dist'] = atr_multiple_from_sma50(df['close'], df['atr'], _d21)
    else:
        df['ema21_atr_dist'] = np.nan

    # Double Trouble input: c / minl252. The enrichment stores low_52w as a
    # FRACTION (close/min(low) - 1), so the ratio is 1 + low_52w. Median, not
    # mean, decides the form: a handful of names print +800x and would drag a
    # mean over 1 even for fractions.
    _l = pd.to_numeric(df.get('low_52w', pd.Series(dtype=float)), errors='coerce')
    if _l.notna().any() and _l.median() > 1:          # absolute prices
        df['c_low52w'] = pd.to_numeric(df['close'], errors='coerce') / _l.where(_l > 0)
    else:
        df['c_low52w'] = 1.0 + _l

    # 52W high distance
    h = pd.to_numeric(df['high_52w'], errors='coerce')
    c = pd.to_numeric(df['close'], errors='coerce')
    if h.mean() > 1:  # absolute prices, not fractions
        df['high_52w_dist'] = (c - h) / h
    else:
        df['high_52w_dist'] = h

    # Round score columns to integers
    for col in ['rs_1m', 'rs_3m', 'rs_6m', 'rs_21d', 'rs_63d', 'rs_126d',
                'rs_ibd', 'f_score', 'i_score', 'h_score']:
        df[col] = df[col].round(0).astype('Int64')  # Int64 keeps NA where the input was missing

    # --- Performance percentile ranks (0-1 scale, relative to full universe) ---
    #
    # `na_option='top'` for the same reason as rank_tradeable above: pandas
    # names the option by rank position, so 'bottom' hands a missing value the
    # LARGEST rank — the top of the scale. These two slipped through the first
    # fix, and they feed both the 97 Club preset and the momentum_97 flag two
    # lines down: on 2026-08-12, 112 names with no weekly return sat at the
    # >=97th weekly percentile, ADSK among them.
    if 'perf_1w' in df.columns:
        df['perf_1w_pctile'] = df['perf_1w'].rank(pct=True, na_option='top').round(4)
    if 'perf_3m' in df.columns:
        df['perf_3m_pctile'] = df['perf_3m'].rank(pct=True, na_option='top').round(4)

    # --- Momentum 97 flag: 1W pctile >= 0.97 AND 3M pctile >= 0.85 ---
    _w = df.get('perf_1w_pctile', pd.Series(0, index=df.index))
    _m = df.get('perf_3m_pctile', pd.Series(0, index=df.index))
    df['momentum_97'] = (_w >= 0.97) & (_m >= 0.85)

    # Round derived columns to 4 decimals
    for col in ['adr_pct', 'ema21_r', 'sma50_r', 'high_52w_dist', 'atr_from_sma50', 'ema21_atr_dist', 'c_low52w', 'ti65', 'mdt']:
        if col in df.columns:            # ti65/mdt come from enrichment; absent on the fallback path
            df[col] = pd.to_numeric(df[col], errors='coerce').round(4)

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

    # 1b. Fundamentals for the F score: yfinance primary (rolling refresh,
    # BUDGET tickers a night, store committed under data/reference), Finviz's
    # own columns as backup. Own failure domain: a throttled night keeps last
    # week's readings, never blanks the column.
    try:
        from pipeline.adapters import fundamentals_store as FS
        fstore = FS.load()
        stats = FS.refresh(fstore, universe['ticker'].tolist())
        FS.save(fstore)
        universe = FS.apply(universe, fstore)
        cov = universe[['eps_growth_next_y', 'revenue_growth']].notna().any(axis=1).mean()
        logger.info("fundamentals: %s; coverage %.1f%% of universe (source counts %s)",
                    stats, cov * 100, universe['fund_source'].value_counts(dropna=False).to_dict())
    except Exception:
        logger.exception("fundamentals store failed - F score falls back to Finviz columns only")

    # Compute universe scores for screener page
    scored_universe = compute_universe_scores(universe)

    # 2. Fetch ETF data
    logger.info("Fetching ETF data...")
    etf_data = yf_adapter.fetch_etf_data()
    logger.info(f"Got {len(etf_data)} ETFs from yfinance")

    # 3. Fetch MA signals
    logger.info("Fetching MA signals...")
    signals, ma_histories = yf_adapter.fetch_ma_data(
        ['SPY', 'QQQ', 'IWM', 'RSP', '^GSPC', 'BTC-USD', '^VIX'],
        return_history=True,
        history_period='3y',
    )

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
    market_health_payload = None
    replay_payload = None
    try:
        breadth_result = run_breadth_metrics(
            universe,
            str(HISTORY_DIR / 'breadth_archive.csv'),
            spx_close=spx_close,
        )
    except Exception:  # noqa: BLE001 — isolate breadth; never abort the whole run
        logger.exception(
            "Breadth metrics failed — skipping breadth.json; "
            "all other outputs still written"
        )
        breadth_result = None
    else:
        # Signal/health computation is a separate failure domain: a crash here
        # (e.g. load_archive or run_signals) must not null out breadth_result,
        # which would silently drop breadth.json even though the metrics run
        # above succeeded (FINDING B).
        try:
            from pipeline.screeners.breadth_store import load_archive
            from pipeline.screeners.breadth_signals import run_signals
            breadth_frame = load_archive(str(HISTORY_DIR / 'breadth_archive.csv'))
            market_health_payload = run_signals(
                breadth_result, breadth_frame,
                ma_histories.get('SPY'), ma_histories.get('QQQ'),
            )
        except Exception:  # noqa: BLE001 — isolate signals; breadth.json still ships
            logger.exception(
                "Breadth signals failed — breadth.json will ship without "
                "verdict/health; market_health.json will be marked stale"
            )
            market_health_payload = None
        else:
            # The v2 state board is its own failure domain: it is a presentation
            # block, so a crash here must never cost breadth.json its verdict.
            # Worst case the v2 UI hides one section.
            try:
                from pipeline.screeners.state_board import build as build_state_board
                from pipeline.screeners.regime import build as build_regime
                board = build_state_board(breadth_frame, market_health_payload)
                breadth_result['state_board'] = board
                # The score is derived from the board, so it lives or dies with
                # it — no separate try, and no possibility of a score published
                # beside a board it was not computed from.
                breadth_result['regime'] = build_regime(board['rows'])
            except Exception:  # noqa: BLE001 — isolate; breadth.json still ships
                logger.exception(
                    "State board failed — breadth.json ships without it"
                )

            # Replay is its own failure domain: a build_replay crash must not
            # stale-mark market_health.json while breadth.json keeps a
            # health-derived verdict (the banner would show spy/qqq states
            # while the health panels are hidden). Worst case: no Time Machine.
            try:
                from pipeline.screeners.breadth_signals import build_replay
                replay_payload = build_replay(
                    breadth_frame,
                    ma_histories.get('SPY'), ma_histories.get('QQQ'),
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Replay build failed — breadth_replay.json not written; "
                    "breadth.json and market_health.json are unaffected"
                )
                replay_payload = None

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

    # 7b. Ticker event archive + heat (isolated: never breaks other outputs)
    heating_up_payload = None
    ticker_events_payload = None
    try:
        from pipeline.screeners.ticker_events import (
            MOMENTUM_MEDIAN_WINDOW, SCREENER_FILES, extract_events,
            is_plausible_day, is_session_date, load_events, load_sessions,
            rolling_momentum_median, upsert_day, write_events,
        )
        from pipeline.screeners.ticker_heat import (
            build_heating_up, build_ticker_events_index,
        )
        # Events are keyed by session; a weekend run must attach to Friday.
        # Completed session, not calendar session: a premarket run must
        # label its scrape with the close it actually contains. The event
        # archive is append-only, so a wrong label here is forever.
        event_date = last_completed_session().isoformat()
        today_rows = []
        for screener in SCREENER_FILES:
            payload = results.get(screener)
            if isinstance(payload, dict):
                today_rows.extend(extract_events(screener, payload, event_date))

        archive_path = str(HISTORY_DIR / 'ticker_events.csv')
        existing = load_events(archive_path)
        sessions = load_sessions(str(HISTORY_DIR / 'breadth_archive.csv'))

        # Grade today's momentum_97 count against its own recent norm rather
        # than a fixed ceiling — that is what catches partial degradation.
        momentum_median = None
        if len(existing):
            archive_dates = sorted(set(existing['date'].astype(str)))
            recent = archive_dates[-MOMENTUM_MEDIAN_WINDOW:]
            counts = existing[existing['date'].astype(str).isin(recent)]
            per_day = counts.groupby(counts['date'].astype(str))['screener'].apply(
                lambda s: int((s == 'momentum_97').sum()))
            momentum_median = rolling_momentum_median(
                [int(per_day.get(d, 0)) for d in recent])

        plausible, reason = is_plausible_day(
            today_rows, momentum_median=momentum_median)
        # Screener presets (the page filters them client-side; nothing was
        # logged, so four presets could not be validated at all -- 2026-08-19).
        # Judged AFTER the plausibility sniff on the seven core screeners so a
        # broken run cannot pass on preset rows alone. Own failure domain.
        try:
            from pipeline.screeners.preset_hits import extract_preset_events, load_presets
            preset_rows = extract_preset_events(
                scored_universe.to_dict('records'), load_presets(), event_date)
            today_rows.extend(preset_rows)
            logger.info("Ticker events: %d preset hits across %d presets",
                        len(preset_rows), len({r['screener'] for r in preset_rows}))
        except Exception:  # noqa: BLE001
            logger.exception("Preset hits failed -- ticker_events gets the seven screeners only")
        stale_reason = None
        if not is_session_date(event_date, sessions):
            stale_reason = 'not a trading session'
            logger.error(
                "Ticker events: %s is not a trading session — skipping append",
                event_date)
            events_frame = existing
        elif not plausible:
            stale_reason = reason
            logger.error(
                "Ticker events: %s looks implausible (%s) — skipping append "
                "(pipeline-failure signature, not a quiet tape)", event_date, reason)
            events_frame = existing
        else:
            events_frame = upsert_day(existing, today_rows)
            write_events(events_frame, archive_path)
            logger.info("Ticker events: appended %d rows for %s",
                        len(today_rows), event_date)

        # Never stamp outputs with a date the archive has no data for: on a
        # rejected day the header would otherwise claim today and show
        # yesterday's tape.
        as_of = event_date
        if stale_reason and len(events_frame):
            as_of = str(events_frame['date'].astype(str).max())
        heating_up_payload = build_heating_up(events_frame, as_of)
        if stale_reason:
            heating_up_payload['stale'] = True
            heating_up_payload['stale_reason'] = stale_reason
        ticker_events_payload = build_ticker_events_index(events_frame, as_of)
    except Exception:  # noqa: BLE001 — isolate; every other output still ships
        logger.exception("Ticker event archive failed — its outputs will be skipped")
        heating_up_payload = None
        ticker_events_payload = None

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

    # Save breadth metrics (skipped when the breadth step failed — the previous
    # breadth.json stays in place rather than being replaced by a partial one)
    if breadth_result is not None:
        (OUTPUT_DIR / 'breadth.json').write_text(json.dumps(
            {'timestamp': timestamp, **breadth_result}, indent=2, default=_json_serializer
        ))
        logger.info("Saved breadth.json")
    else:
        logger.warning("Skipped breadth.json (breadth step failed)")

    # Save market health (stale-mark the previous file when unavailable)
    mh_path = OUTPUT_DIR / 'market_health.json'
    if market_health_payload is not None:
        mh_path.write_text(json.dumps(
            {'timestamp': timestamp, 'stale': False, **market_health_payload},
            indent=2, default=_json_serializer
        ), encoding='utf-8')
        logger.info("Saved market_health.json")
    elif mh_path.exists():
        try:
            prev = json.loads(mh_path.read_text(encoding='utf-8'))
            prev['stale'] = True
            mh_path.write_text(json.dumps(
                prev, indent=2, default=_json_serializer
            ), encoding='utf-8')
            logger.warning("market_health unavailable — marked previous file stale")
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Could not stale-mark market_health.json: %s", exc)

    # Save breadth replay (skipped when signals/replay step failed)
    if replay_payload is not None:
        # Compact separators (no indent) for this file only: it is a ~1MB
        # machine-read book fetched by the browser, and indent=2 inflates it
        # by ~60% for no human benefit. Every other output keeps indent=2.
        (OUTPUT_DIR / 'breadth_replay.json').write_text(
            json.dumps({'timestamp': timestamp, **replay_payload},
                       separators=(',', ':'), default=_json_serializer),
            encoding='utf-8')
        logger.info("Saved breadth_replay.json")

    if heating_up_payload is not None:
        (OUTPUT_DIR / 'heating_up.json').write_text(
            json.dumps({'timestamp': timestamp, **heating_up_payload},
                       indent=2, default=_json_serializer),
            encoding='utf-8')
        logger.info("Saved heating_up.json")

    if ticker_events_payload is not None:
        (OUTPUT_DIR / 'ticker_events.json').write_text(
            json.dumps({'timestamp': timestamp, **ticker_events_payload},
                       separators=(',', ':'), default=_json_serializer),
            encoding='utf-8')
        logger.info("Saved ticker_events.json")

    # Save ETF data
    (OUTPUT_DIR / 'etf_data.json').write_text(
        etf_data.to_json(orient='records', indent=2)
    )
    logger.info("Saved etf_data.json")

    # vol_5d_50d -- the screener's volume column (5-day over 50-day average
    # volume, TSF's construction, from daily bars). Guarded: the universe must
    # ship even when the vendor does not.
    try:
        from pipeline.screeners.volume_enrichment import enrich_universe
        scored_universe = enrich_universe(scored_universe)
    except Exception as e:
        logger.warning(f"vol_5d_50d enrichment failed, column ships unmeasured: {e}")
        if 'vol_5d_50d' not in scored_universe.columns:
            scored_universe['vol_5d_50d'] = None

    # Save full universe for screener page
    universe_cols = [
        'ticker', 'close', 'change_pct', 'perf_1w', 'perf_1m', 'perf_34d', 'perf_3m',
        'perf_6m', 'perf_1y', 'perf_ytd',
        'sma20_dist', 'sma50_dist', 'sma40_dist', 'sma200_dist',
        'atr', 'rel_volume', 'avg_volume', 'volume', 'vol_5d_50d',
        'market_cap', 'sector', 'industry',
        'high_52w', 'low_52w', 'eps_growth_next_y', 'revenue_growth', 'eps_growth_this_y',
        'fund_source', 'fund_asof',
        'rs_1m', 'rs_3m', 'rs_6m',
        'rs_21d', 'rs_63d', 'rs_126d',   # deprecated aliases, drop once the UI moves
        'rs_ibd',
        'f_score', 'i_score', 'h_score', 'tradeable',   # tradeable: the field the scores are measured on
        'adr_pct', 'ema21_r', 'sma50_r', 'high_52w_dist',
        'from_open_pct', 'dcr_pct', 'pocket_pivot', 'pp_count_30d', 'pp_count_10d',
        'vol10_green', 'vol10_green_count_10d', 'vol10_green_count_30d',
        'atr_from_sma50', 'ema21_atr_dist', 'ema21', 'rs_line_pctl_21', 'rs_line_pctl_63', 'rs_line_pctl_126', 'perf_5d',
        'cross_ema21_up', 'cross_sma50_up',
        'ti65', 'mdt', 'min_vol_3d', 'c_low52w', 'liquid_leader', 'ad_ratio_20', 'cmf21',
        'bar_date', 'bars_stale', 'bar_scale_mismatch',
        'sp_setup', 'sp_len', 'sp_ll', 'sp_hl', 'sp_1st', 'sp_2nd', 'sp_tp1', 'sp_tp2',
        'sp_phase', 'sp_stop', 'sp_ma', 'sp_signal', 'sp_days', 'sp_dist_1st_pct',
        'sp_dist_2nd_pct', 'sp_counter',
        'trend_base', 'vcs', 'ema21_low_dist',
        'perf_1w_pctile', 'perf_3m_pctile', 'momentum_97',
        'bo_count_1m', 'bo_count_3m', 'bo_count_6m', 'bo_count_1y',
        'ema10', 'ema20', 'wk_ema10', 'wk_ema20',
    ]
    export_cols = [c for c in universe_cols if c in scored_universe.columns]
    # Convert to object dtype so NaN becomes None (valid JSON null, not NaN)
    export_df = scored_universe[export_cols].astype(object).where(
        scored_universe[export_cols].notna(), None
    )
    rows_out = export_df.to_dict('records')

    # Quality gate. A row count is not a shape check: the 2026-08-09 run
    # produced exactly 5,615 rows with avg_volume 7x more missing than usual,
    # and nothing noticed until a $49.5B name showed up as untradeable.
    from pipeline.quality import check as check_quality, tradeable_status
    from pipeline.themes import MIN_MARKET_CAP, MIN_DOLLAR_VOLUME
    quality = check_quality(rows_out, last_completed_session().isoformat())

    statuses = [tradeable_status(r, MIN_MARKET_CAP, MIN_DOLLAR_VOLUME)
                for r in rows_out]
    quality['tradeable'] = {
        s: statuses.count(s) for s in ('tradeable', 'excluded', 'unmeasurable')
    }
    logger.info("Universe quality: %s — tradeable %d, excluded %d, unmeasurable %d",
                quality['status'], quality['tradeable']['tradeable'],
                quality['tradeable']['excluded'], quality['tradeable']['unmeasurable'])

    universe_export = {
        'timestamp': timestamp,
        'count': len(scored_universe),
        'quality': quality,
        'rows': rows_out,
    }
    (OUTPUT_DIR / 'universe.json').write_text(
        json.dumps(universe_export, indent=None, default=_json_serializer)
    )
    logger.info("Saved universe.json")

    # Severe means a feed is broken, not noisy. Stopping here leaves yesterday's
    # outputs in place, which is the better of two bad days: a shifted universe
    # moves every percentile in the product without looking wrong anywhere.
    # Degraded only warns — one flaky vendor morning should not cost a day.
    if quality['status'] == 'severe':
        broken = [f for f, v in quality['fields'].items() if v['status'] == 'severe']
        raise SystemExit(
            f"Universe quality severe on {', '.join(broken)} — refusing to "
            f"publish. Yesterday's outputs are unchanged."
        )

    # Basket closes BEFORE the group layer. build_groups fills the benchmark's
    # (and the proxy themes') perf_6m from data/output/baskets/*.json and
    # refuses when the bars' perf_3m disagrees with etf_data's -- which they
    # always did while this fetch ran last: at group time the baskets on disk
    # were the previous session's, one bar behind etf_data, so rs_3m_6m came
    # out null for every theme (17 "disagree" warnings a night; severe on
    # 2026-08-17). Own failure domain; a failed fetch leaves yesterday's file.
    try:
        from pipeline.rotation.fetch_baskets import fetch as fetch_baskets
        fetch_baskets()
    except Exception:
        logger.exception("Basket fetch failed - rotation/groups read yesterday's baskets")

    # Group layer: industries + curated themes, scored and state-classified.
    # Depends on universe.json and etf_data.json having just been written, so
    # it runs last. Non-fatal: a failure here must not cost the whole daily
    # run, since every other output is already on disk by this point.
    try:
        # save() rather than a local write: it also appends the daily group
        # snapshot, and the two came apart once already — the snapshot lived in
        # build_groups.main(), which this pipeline never calls, so the archive
        # silently never grew.
        from pipeline.themes.build_groups import run as run_groups, save as save_groups
        groups_payload = run_groups()
        save_groups(groups_payload, OUTPUT_DIR)
        gs = groups_payload['summary']
        logger.info(
            "Saved groups.json - %d industries, %d themes "
            "(%d publishable, %d provisional)",
            gs['industries'], gs['themes'],
            gs['publishable_themes'], gs['provisional_themes'])
    except Exception:
        logger.exception("Group layer failed - groups.json not updated")

    # Nightly watchlist: zones -> panels -> tickers off the scored universe, so
    # the Watchlist page renders instead of filtering. Own failure domain.
    try:
        from pipeline.screeners.watchlist import build as build_watchlist, load_group_states, archive_leaders
        wl_rows = json.loads((OUTPUT_DIR / 'universe.json').read_text())['rows']
        gs_map = None
        try:
            gs_map = load_group_states(json.loads((OUTPUT_DIR / 'groups.json').read_text()))
        except Exception:
            logger.exception("groups.json unreadable - True Market Leaders panel will be unmeasured")
        wl_date = last_completed_session().isoformat()
        wl = build_watchlist(wl_rows, date=wl_date, group_states=gs_map)
        try:
            n_lead = archive_leaders(wl_rows, date=wl_date, group_states=gs_map)
            logger.info("leaders_log: +%d rows for %s", n_lead, wl_date)
        except Exception:
            logger.exception("leaders archive failed - watchlist.json unaffected")
        try:
            from pipeline.screeners.watchlist import archive_panel_hits, _with_groups
            n_hits = archive_panel_hits(wl, _with_groups(wl_rows, gs_map))
            logger.info("watchlist_hits: +%d rows for %s", n_hits, wl_date)
        except Exception:
            logger.exception("panel hits archive failed - watchlist.json unaffected")
        try:
            from pipeline.screeners.watchlist import archive_momentum97_shadow
            n_sh = archive_momentum97_shadow(wl_rows, date=wl_date)
            logger.info("momentum97_shadow: +%d rows for %s", n_sh, wl_date)
        except Exception:
            logger.exception("momentum97 shadow log failed - watchlist.json unaffected")
        (OUTPUT_DIR / 'watchlist.json').write_text(json.dumps(wl, indent=2, default=_json_serializer))
        logger.info("Saved watchlist.json - %d gated, cross-zone %d, panels %s",
                    wl['universe_gated'], len(wl['cross_zone']),
                    {p['key']: p['count'] for z in wl['zones'] for p in z['panels']})
    except Exception:
        logger.exception("Watchlist failed - watchlist.json not updated")

    # Style rotation: score the baskets fetched above. Own failure domain.
    try:
        from pipeline.rotation.build_rotation import build as build_rotation
        rotation_payload = build_rotation()
        (OUTPUT_DIR / 'rotation.json').write_text(
            json.dumps(rotation_payload, indent=2, default=_json_serializer))
        rv = rotation_payload['verdict']
        logger.info("Saved rotation.json - %s", rv['sentence'])
    except Exception:
        logger.exception("Rotation layer failed - rotation.json not updated")

    # Correction Risk base layer: two yfinance series (^GSPC, ^VIX to 1990),
    # a conditional base-rate table, today's cell. Network step, own failure
    # domain; the appendix (VIX3M/HYG/IEF logistic NULL) is not re-run nightly.
    try:
        from pipeline.risk.correction_risk import fetch_inputs, _main_from
        cr = _main_from(fetch_inputs(with_appendix=False), with_appendix=False)
        logger.info("Saved correction_risk.json - P(5%% dd/21d) %.3f vs base %.3f (VIX Q%d, %s 200dma)",
                    cr['prob'], cr['base_rate'], cr['today']['vix_quintile'],
                    'above' if cr['today']['above_200dma'] else 'below')
    except Exception:
        logger.exception("Correction risk failed - correction_risk.json not updated")

    # Site-wide quality: grade every file the frontend reads, write the
    # consolidated report beside them. Its own failure domain — a grading
    # crash must not cost the outputs it grades.
    try:
        from pipeline.quality import check_site
        site_report = check_site(OUTPUT_DIR, last_completed_session().isoformat())
        (OUTPUT_DIR / 'quality.json').write_text(
            json.dumps(site_report, indent=2, default=_json_serializer))
        logger.info("Site quality: %s (%s)", site_report['status'],
                    {k: v['status'] for k, v in site_report['sources'].items()})
    except Exception:  # noqa: BLE001
        logger.exception("Site quality check failed — outputs unaffected")

    # Summary
    total_tickers = sum(
        d.get('count', 0) for d in results.values() if isinstance(d, dict)
    )
    logger.info(f"Done. {len(results)} screeners completed. Universe: {len(universe)} stocks.")


if __name__ == '__main__':
    main()
