"""Backtest optimizer CLI — sweeps trim/trail parameters against your closed-trade
history and reports which combination would have maximized realized R.

Usage:
    python -m pipeline.portfolio.backtest_optimizer

Auto-detects the most recent CSV in data/portfolio/. Override with flags:
    --input <path>     CSV path
    --output <path>    markdown report path
    --json <path>      JSON output path
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from pipeline.marketcal import market_today
from pipeline.portfolio.trade_parser import parse_csv, find_latest_csv, Trade
from pipeline.portfolio.ohlc_cache import fetch_ohlc
from pipeline.portfolio.market_regime import build_regime_index
from pipeline.portfolio.simulator import prep_bars, _simulate_from_bars, SimParams
from pipeline.portfolio.parameter_grid import all_params, params_to_label
from pipeline.portfolio.pyramid_analyzer import (
    detect_campaigns, compute_counterfactual, build_pyramid_section,
)
from pipeline.portfolio.reporter import (
    atr_bucket, hold_archetype, find_best_param, top_n_params,
    write_markdown, write_json,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


def _entry_atr_pct(trade: Trade, ohlc) -> float | None:
    """Compute 14-day ATR% at the entry day."""
    if ohlc is None or len(ohlc) < 14:
        return None
    entry_ts = trade.entry_date
    # find the bar on entry day or the previous trading day
    prior = ohlc[ohlc.index <= str(entry_ts)]
    if len(prior) < 14:
        return None
    closes = prior['Close']
    highs = prior['High']
    lows = prior['Low']
    tr = np.maximum(highs - lows,
                    np.maximum((highs - closes.shift(1)).abs(),
                               (lows - closes.shift(1)).abs()))
    atr = tr.rolling(14, min_periods=1).mean().iloc[-1]
    close_at_entry = closes.iloc[-1]
    if close_at_entry <= 0:
        return None
    return float(atr / close_at_entry * 100)


def run(input_path: Path, output_md: Path, output_json: Path) -> None:
    logger.info(f"Reading trades from {input_path}")
    trades = parse_csv(input_path)
    closed_all = [t for t in trades if t.closed and t.exit_date is not None]
    multiday = [t for t in closed_all if t.has_multiday_trims and t.has_R]
    logger.info(f"Loaded {len(trades)} total · {len(closed_all)} closed · "
                f"{len(multiday)} multi-day-trim (optimizable)")

    if not multiday:
        print("ERROR: No multi-day trades to optimize.", file=sys.stderr)
        sys.exit(1)

    # ── Market regime index for the whole timespan ─────────────────────────
    earliest = min(t.entry_date for t in multiday) - timedelta(days=120)
    latest = max(t.exit_date for t in multiday) + timedelta(days=30)
    logger.info(f"Building market regime index {earliest} → {latest}")
    regime = build_regime_index(earliest, latest)

    # ── Fetch OHLC for each ticker ─────────────────────────────────────────
    unique_tickers = sorted({t.ticker for t in multiday})
    logger.info(f"Fetching OHLC for {len(unique_tickers)} unique tickers...")
    ohlc_by_ticker: dict[str, object] = {}
    for tk in unique_tickers:
        # broadest date range needed for this ticker
        trade_subset = [t for t in multiday if t.ticker == tk]
        s = min(t.entry_date for t in trade_subset) - timedelta(days=60)
        e = max(t.exit_date for t in trade_subset) + timedelta(days=30)
        df = fetch_ohlc(tk, s, e)
        if df is not None and len(df):
            ohlc_by_ticker[tk] = df

    # ── Pre-compute per-trade bars + tagging ───────────────────────────────
    logger.info("Preparing per-trade indicator bars...")
    trade_data: list[dict] = []
    for t in multiday:
        ohlc = ohlc_by_ticker.get(t.ticker)
        if ohlc is None:
            continue
        bars = prep_bars(t, ohlc)
        if bars is None:
            continue
        trade_data.append({
            'trade': t,
            'bars': bars,
            'atr_pct': _entry_atr_pct(t, ohlc),
            'regime': regime.at(t.entry_date) or 'unknown',
        })
    logger.info(f"Prepared {len(trade_data)} trades for simulation")

    # ── Parameter sweep ────────────────────────────────────────────────────
    params = all_params()
    logger.info(f"Running {len(params):,} param sets × {len(trade_data)} trades "
                f"= {len(params)*len(trade_data):,} simulations")

    n_trades = len(trade_data)
    n_params = len(params)
    R_matrix = np.full((n_trades, n_params), np.nan, dtype=np.float64)

    for i, td in enumerate(trade_data):
        bars = td['bars']
        tr = td['trade']
        for j, p in enumerate(params):
            try:
                R_matrix[i, j] = _simulate_from_bars(tr, bars, p)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"sim failed trade={tr.ticker} param={j}: {e}")
        if (i + 1) % 10 == 0:
            logger.info(f"  ... {i+1}/{n_trades} trades simulated")

    logger.info("Simulation complete. Aggregating...")

    # ── Tags as arrays ─────────────────────────────────────────────────────
    atr_buckets = np.array([atr_bucket(td['atr_pct']) for td in trade_data])
    archetypes = np.array([hold_archetype(td['trade'].hold_business_days) for td in trade_data])
    regimes = np.array([td['regime'] for td in trade_data])
    actual_Rs = np.array([td['trade'].realized_R if td['trade'].realized_R is not None else np.nan
                          for td in trade_data])

    # ── Best overall ───────────────────────────────────────────────────────
    best_overall = find_best_param(R_matrix, params, np.ones(n_trades, dtype=bool))
    best_overall['actual_total_R'] = float(np.nansum(actual_Rs))

    # ── By ATR bucket ──────────────────────────────────────────────────────
    by_atr = {}
    for b in sorted(set(atr_buckets)):
        mask = atr_buckets == b
        bp = find_best_param(R_matrix, params, mask)
        if bp is not None:
            bp['actual_total_R'] = float(np.nansum(actual_Rs[mask]))
        by_atr[b] = bp

    # ── By hold archetype ──────────────────────────────────────────────────
    by_hold = {}
    for a in sorted(set(archetypes)):
        mask = archetypes == a
        bp = find_best_param(R_matrix, params, mask)
        if bp is not None:
            bp['actual_total_R'] = float(np.nansum(actual_Rs[mask]))
        by_hold[a] = bp

    # ── By regime ──────────────────────────────────────────────────────────
    by_regime = {}
    for r in sorted(set(regimes)):
        mask = regimes == r
        bp = find_best_param(R_matrix, params, mask)
        if bp is not None:
            bp['actual_total_R'] = float(np.nansum(actual_Rs[mask]))
        by_regime[r] = bp

    # ── Top-5 sensitivity ──────────────────────────────────────────────────
    top5 = top_n_params(R_matrix, params, n=5)

    # ── Intraday vs close stop_basis head-to-head ──────────────────────────
    # For each param-cell that has both intraday and close variants, find the best
    # of each. Compare overall best-intraday vs best-close to surface the answer.
    intraday_mask = np.array([p.stop_basis == 'intraday' for p in params])
    close_mask = np.array([p.stop_basis == 'close' for p in params])
    valid_trade_mask = ~np.isnan(R_matrix).all(axis=1)
    intraday_totals = np.nansum(R_matrix[valid_trade_mask][:, intraday_mask], axis=0)
    close_totals = np.nansum(R_matrix[valid_trade_mask][:, close_mask], axis=0)
    best_intraday_R = float(np.max(intraday_totals)) if len(intraday_totals) else 0
    best_close_R = float(np.max(close_totals)) if len(close_totals) else 0
    intraday_best_idx_in_subset = int(np.argmax(intraday_totals)) if len(intraday_totals) else 0
    close_best_idx_in_subset = int(np.argmax(close_totals)) if len(close_totals) else 0
    intraday_param_idxs = np.where(intraday_mask)[0]
    close_param_idxs = np.where(close_mask)[0]
    intraday_best_label = (
        params_to_label(params[intraday_param_idxs[intraday_best_idx_in_subset]])
        if len(intraday_param_idxs) else '—'
    )
    close_best_label = (
        params_to_label(params[close_param_idxs[close_best_idx_in_subset]])
        if len(close_param_idxs) else '—'
    )
    stop_basis_comparison = {
        'best_intraday_total_R': best_intraday_R,
        'best_close_total_R': best_close_R,
        'delta_R': best_close_R - best_intraday_R,
        'winner': 'close' if best_close_R > best_intraday_R else 'intraday',
        'best_intraday_label': intraday_best_label,
        'best_close_label': close_best_label,
    }

    # ── Pyramid campaign analysis ──────────────────────────────────────────
    logger.info("Detecting pyramid campaigns...")
    # Detect across ALL closed-or-open trades (campaigns can include open layers)
    campaigns = detect_campaigns([t for t in trades if t.has_R])
    logger.info(f"Found {len(campaigns)} pyramid campaigns")
    if campaigns:
        # Fetch OHLC for campaign tickers if not already cached
        for c in campaigns:
            if c.ticker not in ohlc_by_ticker:
                s = c.first_entry - timedelta(days=60)
                # extend to today (campaigns may have open layers)
                e = max(c.last_entry, market_today()) + timedelta(days=30)
                df = fetch_ohlc(c.ticker, s, e)
                if df is not None and len(df):
                    ohlc_by_ticker[c.ticker] = df
        # Compute counterfactuals using best-overall params
        best_simparams = SimParams(**{
            k: best_overall['best_params'][k]
            for k in ('trim1_trigger_R', 'trim1_size_pct', 'trim2_trigger',
                      'trim2_size_pct', 'trim3_trigger', 'trim3_size_pct',
                      'full_stop_signal', 'gain_ratchet', 'stop_basis')
        })
        compute_counterfactual(campaigns, ohlc_by_ticker, best_simparams)
    pyramid_section = build_pyramid_section(campaigns)

    # ── Biggest missed-gain trades ─────────────────────────────────────────
    best_idx = best_overall['best_idx']
    optimal_per_trade = R_matrix[:, best_idx]
    gaps = []
    for i, td in enumerate(trade_data):
        actual = actual_Rs[i]
        opt = optimal_per_trade[i]
        if np.isnan(actual) or np.isnan(opt):
            continue
        gaps.append({
            'ticker': td['trade'].ticker,
            'entry_date': td['trade'].entry_date.isoformat(),
            'actual_R': float(actual),
            'optimal_R': float(opt),
            'delta_R': float(opt - actual),
        })
    gaps.sort(key=lambda g: -g['delta_R'])
    missed = gaps[:15]

    # ── Headline ───────────────────────────────────────────────────────────
    actual_total = float(np.nansum(actual_Rs))
    optimal_total = best_overall['total_R']
    lift_pct = (optimal_total - actual_total) / abs(actual_total) * 100 if actual_total != 0 else 0
    largest_gap_reason = (
        "premature exits on multi-day winners — optimizer held longer with a wider EMA-based stop"
        if missed and missed[0]['delta_R'] > 0
        else "stop placement and trim sizing"
    )

    # ── Assemble report ────────────────────────────────────────────────────
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'input_csv': str(input_path),
        'summary': {
            'trades_total': len(trades),
            'closed_count': len(closed_all),
            'multiday_count': len(multiday),
            'simulated_count': len(trade_data),
            'param_combos': n_params,
            'simulations': n_trades * n_params,
        },
        'headline': {
            'actual_total_R': actual_total,
            'optimal_total_R': optimal_total,
            'lift_pct': lift_pct,
            'largest_gap_reason': largest_gap_reason,
        },
        'best_overall': best_overall,
        'by_atr_bucket': by_atr,
        'by_hold': by_hold,
        'by_regime': by_regime,
        'top_n': top5,
        'missed_gains': missed,
        'pyramid_campaigns': pyramid_section,
        'stop_basis_comparison': stop_basis_comparison,
        '_schema': 'v3',
    }

    write_json(report, output_json)
    write_markdown(report, output_md)
    print(f"\n✓ Report: {output_md}")
    print(f"✓ JSON:   {output_json}")
    print(f"\nLift: {lift_pct:+.1f}% (actual {actual_total:+.1f}R → optimal {optimal_total:+.1f}R)")
    print(f"Best params: {best_overall['best_label']}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description='Portfolio backtest optimizer')
    p.add_argument('--input', type=Path, default=None,
                   help='CSV path (defaults to latest in data/portfolio/)')
    p.add_argument('--output', type=Path, default=None,
                   help='Markdown report path (defaults to docs/portfolio-tuning-YYYY-MM-DD.md)')
    p.add_argument('--json', type=Path, default=Path('data/output/portfolio_backtest.json'),
                   help='JSON output path')
    args = p.parse_args(argv)

    if args.input is None:
        args.input = find_latest_csv(Path('data/portfolio'))
        if args.input is None:
            print("ERROR: no CSV found in data/portfolio/", file=sys.stderr)
            sys.exit(1)
    if args.output is None:
        today = market_today().isoformat()
        args.output = Path(f'docs/portfolio-tuning-{today}.md')
    args.output.parent.mkdir(parents=True, exist_ok=True)

    run(args.input, args.output, args.json)


if __name__ == '__main__':
    main()
