"""Per-trade post-mortem generator.

For each trade in the portfolio CSV, produces a JSON record at
`data/output/trades/<trade_id>.json` with:

  - Entry-day technical snapshot (price, MA20/50/200, RSI(14), ATR(14),
    52W position, setup classification) — computed from per-ticker
    1y OHLC already stored in data/output/tickers/<SYM>.json
  - Execution chain (entry, trims, current state, realized R, days held)
  - Post-entry path analytics (max favorable excursion, max adverse,
    optimal exit price + date, R captured vs R available)
  - Auto-tagged lesson (Good execution / Premature trim / Stopped too
    tight / Failed setup / Choppy / In progress)
  - Deterministic technical-only AI narrative (no current web context —
    honest as-of-trade-date)

Run:
    python -m pipeline.portfolio.trade_postmortem
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone

from pipeline.marketcal import market_today
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from pipeline.portfolio.trade_parser import parse_csv, find_latest_csv, Trade

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path('data/output/trades')
TICKERS_DIR = Path('data/output/tickers')
FIXED_R_DOLLARS = 2500.0

# capture_pct is realized_R / optimal_R, so it is only meaningful once the trade
# actually offered something to capture. Below this the percentage is withheld
# and `missed_R` carries the reading instead.
MIN_OPTIMAL_R_FOR_RATIO = 0.25


# ── helpers ────────────────────────────────────────────────────────────────

def _safe_float(v):
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _load_ohlc_df(ticker: str) -> Optional[pd.DataFrame]:
    """Load 1y OHLC from per-ticker JSON into a DataFrame keyed by date."""
    p = TICKERS_DIR / f'{ticker.upper()}.json'
    if not p.exists():
        return None
    try:
        data = json.load(open(p))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"failed to load {p}: {e}")
        return None
    bars = data.get('ohlc_1y') or []
    if not bars:
        return None
    df = pd.DataFrame(bars)
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df.set_index('date').sort_index()
    # ensure numerics
    for col in ('open', 'high', 'low', 'close', 'volume'):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _compute_entry_snapshot(df: pd.DataFrame, entry_date: date) -> dict:
    """Return technical snapshot computed using bars up to and including entry."""
    # Use entry date as the cut-off — exclude future data
    prior = df[df.index <= entry_date]
    if len(prior) < 1:
        return {}
    last = prior.iloc[-1]
    closes = prior['close']
    highs = prior['high']
    lows = prior['low']
    n = len(prior)

    ma20 = float(closes.rolling(20).mean().iloc[-1]) if n >= 20 else None
    ma50 = float(closes.rolling(50).mean().iloc[-1]) if n >= 50 else None
    ma200 = float(closes.rolling(200).mean().iloc[-1]) if n >= 200 else None

    # RSI(14) Wilder's
    rsi = None
    if n >= 15:
        delta = closes.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, float('nan'))
        rsi_series = 100 - 100 / (1 + rs)
        rsi = _safe_float(rsi_series.iloc[-1])

    # ATR(14) TR-based
    atr = None
    atr_pct = None
    if n >= 2:
        tr = pd.concat([
            (highs - lows),
            (highs - closes.shift(1)).abs(),
            (lows - closes.shift(1)).abs(),
        ], axis=1).max(axis=1)
        atr = _safe_float(tr.rolling(14, min_periods=1).mean().iloc[-1])
        if atr and float(last['close']) > 0:
            atr_pct = atr / float(last['close']) * 100

    # 52W extents using bars in the year before entry
    one_yr_ago = entry_date - timedelta(days=365)
    yearly = prior[prior.index > one_yr_ago] if (prior.index > one_yr_ago).any() else prior
    high_52w = _safe_float(yearly['high'].max())
    low_52w = _safe_float(yearly['low'].min())
    last_close = _safe_float(last['close'])
    position_pct = None
    if last_close is not None and high_52w and low_52w and high_52w > low_52w:
        position_pct = (last_close - low_52w) / (high_52w - low_52w) * 100

    # Recent levels
    high_20d = _safe_float(highs.iloc[-20:].max()) if n >= 20 else _safe_float(highs.max())
    low_10d = _safe_float(lows.iloc[-10:].min()) if n >= 10 else _safe_float(lows.min())
    low_5d = _safe_float(lows.iloc[-5:].min()) if n >= 5 else _safe_float(lows.min())

    return {
        'close': last_close,
        'open': _safe_float(last['open']),
        'high': _safe_float(last['high']),
        'low': _safe_float(last['low']),
        'volume': _safe_float(last['volume']),
        'ma20': ma20, 'ma50': ma50, 'ma200': ma200,
        'rsi14': rsi,
        'atr14': atr, 'atr14_pct': atr_pct,
        'high_52w': high_52w, 'low_52w': low_52w,
        'position_in_52w_range_pct': position_pct,
        'high_20d': high_20d, 'low_10d': low_10d, 'low_5d': low_5d,
    }


def _classify_setup(snap: dict, direction: str) -> str:
    """Classify the technical setup at entry."""
    px = snap.get('close')
    ma20 = snap.get('ma20'); ma50 = snap.get('ma50'); ma200 = snap.get('ma200')
    high_52w = snap.get('high_52w')
    rsi = snap.get('rsi14')

    if px is None:
        return 'unknown'

    if direction == 'long':
        stacked_bull = ma20 and ma50 and ma200 and ma20 > ma50 > ma200 and px > ma20
        near_high = high_52w and px >= high_52w * 0.95
        pullback = ma20 and ma50 and px > ma50 and abs(px - ma20) / px < 0.04
        if stacked_bull and near_high:
            return 'Breakout / near 52W high'
        if stacked_bull and pullback:
            return 'Pullback in uptrend'
        if ma200 and px > ma200 and ma50 and px < ma50:
            return 'Pullback below MA50 — risk-on but stretched'
        if ma200 and px < ma200:
            return 'Long below MA200 — counter-trend'
        if rsi and rsi >= 70:
            return 'Extended long — RSI overbought'
        return 'Long in mixed structure'
    else:  # short
        stacked_bear = ma20 and ma50 and ma200 and ma20 < ma50 < ma200 and px < ma20
        if stacked_bear:
            return 'Trend short — stacked bearish'
        if ma200 and px > ma200:
            return 'Short into uptrend — fade attempt'
        if rsi and rsi <= 30:
            return 'Short with RSI oversold — risky'
        return 'Short in mixed structure'


def _compute_path_analytics(df: pd.DataFrame, trade: Trade) -> dict:
    """Walk OHLC from entry → exit, compute MFE/MAE/optimal, and separately what
    the name did for ten days after the exit.

    The two windows are kept apart on purpose. Until 2026-08-09 the excursion
    window ran to exit + 10 days, so `optimal_R` could sit on a high printed
    after the position was already closed — on this book that was true for
    101 of 198 closed trades, a bare majority. `capture_pct` then answered two
    questions at once ("did you hold your winner to its peak" and "did you sell
    too early") and you could not tell from the number which one it was
    reporting. Holding to a peak you have already sold past is not a thing a
    trader can do, so it does not belong in a metric called capture.
    """
    entry_d = trade.entry_date
    exit_d = trade.exit_date or market_today()
    # The capturable window: only bars you were actually holding through.
    window = df[(df.index >= entry_d) & (df.index <= exit_d)]
    # What it did next, reported separately as "left on the table".
    after = df[(df.index > exit_d) & (df.index <= exit_d + timedelta(days=10))]
    if len(window) < 1:
        return {}

    entry_price = trade.entry_price
    sign = 1 if trade.direction == 'long' else -1
    # R-multiples are anchored to the locked-at-entry stop so trailing the live
    # stop after the fact never rewrites historical excursion math.
    r_per_share = abs(trade.entry_price - trade.initial_stop)
    if r_per_share <= 0:
        return {}

    # Per-bar unrealized R (using each bar's high for max favorable, low for max adverse)
    if trade.direction == 'long':
        favorable_per_share = (window['high'] - entry_price)
        adverse_per_share = (entry_price - window['low'])
    else:
        favorable_per_share = (entry_price - window['low'])
        adverse_per_share = (window['high'] - entry_price)

    fav_R = favorable_per_share / r_per_share
    adv_R = adverse_per_share / r_per_share

    mfe_R = _safe_float(fav_R.max())
    mfe_date = fav_R.idxmax() if mfe_R is not None else None
    mae_R = _safe_float(adv_R.max())
    mae_date = adv_R.idxmax() if mae_R is not None else None

    # Optimal exit = the bar with the highest favorable R achieved (the actual peak)
    optimal_R = mfe_R
    optimal_date = mfe_date
    optimal_price = (
        float(window.loc[optimal_date, 'high'])
        if optimal_date is not None and optimal_date in window.index
        else None
    )

    # Realized R captured / R available while holding.
    realized_R = trade.realized_R if trade.closed else None

    # The ratio is unstable as optimal_R approaches zero: a name that never got
    # meaningfully above entry gives a denominator near nothing, so an ordinary
    # loss divides into hundreds of percent. LLY on this book read −947% off an
    # optimal_R of 0.084. Below the floor the percentage is withheld and the
    # additive gap is the number to read instead — it never blows up.
    capture_pct = None
    if (realized_R is not None and optimal_R is not None
            and optimal_R >= MIN_OPTIMAL_R_FOR_RATIO):
        capture_pct = realized_R / optimal_R * 100
    missed_R = (
        optimal_R - realized_R
        if realized_R is not None and optimal_R is not None else None
    )

    # Left on the table: the best it printed in the ten days after the exit,
    # measured in the same R. This is the "did I sell too early" question, kept
    # as its own field so it can never be mistaken for capture.
    post_exit_R = None
    if len(after) >= 1:
        if trade.direction == 'long':
            post_fav = (after['high'] - entry_price) / r_per_share
        else:
            post_fav = (entry_price - after['low']) / r_per_share
        post_exit_R = _safe_float(post_fav.max())

    days_to_optimal = (
        (optimal_date - entry_d).days if optimal_date is not None else None
    )
    hold_days = (exit_d - entry_d).days

    return {
        'mfe_R': mfe_R,
        'mfe_date': optimal_date.isoformat() if optimal_date is not None else None,
        'mae_R': mae_R,
        'mae_date': mae_date.isoformat() if mae_date is not None else None,
        'optimal_exit_price': optimal_price,
        'optimal_exit_date': optimal_date.isoformat() if optimal_date is not None else None,
        'optimal_R': optimal_R,
        'days_to_optimal': days_to_optimal,
        'realized_R': realized_R,
        'capture_pct': capture_pct,
        'missed_R': missed_R,
        'post_exit_R': post_exit_R,
        'hold_calendar_days': hold_days,
    }


def _classify_lesson(trade: Trade, analytics: dict) -> str:
    """Auto-tag the lesson — only for closed trades."""
    if not trade.closed:
        return 'In progress'

    realized = analytics.get('realized_R')
    optimal = analytics.get('optimal_R')
    mae = analytics.get('mae_R')

    if realized is None:
        return 'Insufficient data'

    # Stopped too tight: went red, but had a real winner peak
    if realized < -0.5 and optimal is not None and optimal > 2:
        return 'Stopped too tight'

    # Failed setup: went red, no meaningful winner peak
    if realized < -0.5:
        return 'Failed setup'

    # Choppy: small realized, no edge captured
    if -0.5 <= realized <= 0.5:
        return 'Choppy / no edge'

    # Premature trim: solid realized but optimal was 2x+ larger
    if realized > 0.5 and optimal is not None and optimal >= 2 * realized:
        return 'Premature trim'

    # Good execution: captured ≥50% of the available move
    if realized > 0.5:
        return 'Good execution'

    return 'Unclassified'


def _generate_narrative(trade: Trade, snap: dict, setup: str, analytics: dict, lesson: str) -> str:
    """Deterministic technical-only narrative — no current web context."""
    direction = 'long' if trade.direction == 'long' else 'short'
    entry_date_str = trade.entry_date.isoformat()
    entry_price = trade.entry_price
    initial_stop = trade.initial_stop
    current_stop = trade.stop_price
    r_per_share = abs(entry_price - initial_stop)
    R_dollars = r_per_share * trade.original_qty
    trailed = abs(current_stop - initial_stop) > 0.01

    px = snap.get('close')
    ma20 = snap.get('ma20'); ma50 = snap.get('ma50'); ma200 = snap.get('ma200')
    rsi = snap.get('rsi14')
    pos = snap.get('position_in_52w_range_pct')
    atr_pct = snap.get('atr14_pct')

    # Sentence 1: entry context
    stop_phrase = f"with stop ${initial_stop:.2f}"
    if trailed:
        stop_phrase += f" (currently trailed to ${current_stop:.2f})"
    sent1_parts = [
        f"Entered **{trade.ticker}** {direction} on {entry_date_str} at "
        f"${entry_price:.2f} (qty {trade.original_qty}) {stop_phrase}",
        f"(1R = ${r_per_share:.2f}/sh = ${R_dollars:,.0f}).",
    ]

    # Sentence 2: technical setup
    setup_bits = []
    if px and ma20:
        if px > ma20:
            setup_bits.append(f"price above MA20 (${ma20:.2f})")
        else:
            setup_bits.append(f"price below MA20 (${ma20:.2f})")
    if ma20 and ma50 and ma200:
        if ma20 > ma50 > ma200:
            setup_bits.append("MA20 > MA50 > MA200 (golden alignment)")
        elif ma20 < ma50 < ma200:
            setup_bits.append("MA20 < MA50 < MA200 (death alignment)")
        else:
            setup_bits.append("MA stack mixed")
    if rsi is not None:
        setup_bits.append(f"RSI {rsi:.0f}")
    if pos is not None:
        setup_bits.append(f"{pos:.0f}% through 52W range")
    if atr_pct is not None:
        setup_bits.append(f"ATR {atr_pct:.1f}% of price")
    sent2 = f"Setup: **{setup}** — {', '.join(setup_bits)}." if setup_bits else f"Setup: **{setup}**."

    # Sentence 3: execution / outcome
    if trade.closed:
        realized = analytics.get('realized_R')
        optimal = analytics.get('optimal_R')
        capture = analytics.get('capture_pct')
        optimal_date = analytics.get('optimal_exit_date')
        days_to_opt = analytics.get('days_to_optimal')
        outcome = ""
        if realized is not None:
            outcome = f"Realized **{realized:+.2f}R**"
            if optimal is not None and optimal > 0:
                outcome += f", peak was **+{optimal:.2f}R** on {optimal_date}"
                if days_to_opt is not None:
                    outcome += f" (day +{days_to_opt})"
                if capture is not None:
                    outcome += f" — captured **{capture:.0f}%** of the move"
            outcome += "."
        # Lesson
        sent3 = f"{outcome} **Lesson: {lesson}.**"
    else:
        # Open trade — show current state
        mfe = analytics.get('mfe_R')
        mae = analytics.get('mae_R')
        sent3 = f"**In progress.** Peak so far +{mfe:.2f}R; worst drawdown -{mae:.2f}R." \
                if mfe is not None and mae is not None else "**In progress.**"

    return f"{' '.join(sent1_parts)} {sent2} {sent3}"


def _trade_id(trade: Trade, idx: int) -> str:
    """Stable id: ticker + entry date + index (to disambiguate same-day re-entries)."""
    return f"{trade.ticker}_{trade.entry_date.isoformat()}_{idx:03d}"


def _trade_to_dict(trade: Trade) -> dict:
    return {
        'ticker': trade.ticker,
        'direction': trade.direction,
        'sector': trade.sector,
        'entry_date': trade.entry_date.isoformat(),
        'entry_price': trade.entry_price,
        'original_qty': trade.original_qty,
        'current_qty': trade.current_qty,
        'stop_price': trade.stop_price,        # current / trailing
        'initial_stop': trade.initial_stop,    # locked at entry — R denominator
        'closed': trade.closed,
        'exit_date': trade.exit_date.isoformat() if trade.exit_date else None,
        'hold_business_days': trade.hold_business_days,
        'r_dollars': trade.R_dollars,
        'realized_pl': trade.realized_pl,
        'realized_R': trade.realized_R,
        'trims': [
            {'date': t.date.isoformat(), 'price': t.price, 'qty': t.qty, 'type': t.type}
            for t in trade.trims
        ],
    }


# ── main entry ─────────────────────────────────────────────────────────────

def generate_postmortems(trades: list[Trade], output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    # Pre-load OHLC per unique ticker
    ohlc_cache: dict[str, Optional[pd.DataFrame]] = {}
    succeeded = 0
    skipped: list[str] = []

    # Group trades by ticker to give same-day re-entries stable indices
    by_ticker_date: dict[tuple, int] = {}

    for trade in sorted(trades, key=lambda t: (t.entry_date, t.ticker)):
        key = (trade.ticker, trade.entry_date)
        idx = by_ticker_date.get(key, 0)
        by_ticker_date[key] = idx + 1

        tid = _trade_id(trade, idx)

        if trade.ticker not in ohlc_cache:
            ohlc_cache[trade.ticker] = _load_ohlc_df(trade.ticker)
        df = ohlc_cache[trade.ticker]

        if df is None or df.empty:
            skipped.append(f"{tid} (no OHLC for {trade.ticker})")
            continue
        if trade.entry_date < df.index.min() - timedelta(days=2):
            # Trade is older than our OHLC window — can't reconstruct
            skipped.append(f"{tid} (entry {trade.entry_date} predates 1y OHLC window {df.index.min()})")
            continue

        snap = _compute_entry_snapshot(df, trade.entry_date)
        setup = _classify_setup(snap, trade.direction)
        analytics = _compute_path_analytics(df, trade)
        lesson = _classify_lesson(trade, analytics)
        narrative = _generate_narrative(trade, snap, setup, analytics, lesson)

        record = {
            'trade_id': tid,
            'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            '_schema': 'v1',
            'trade': _trade_to_dict(trade),
            'entry_snapshot': snap,
            'setup_type': setup,
            'path_analytics': analytics,
            'lesson': lesson,
            'narrative': narrative,
            # Slice of OHLC for the per-trade chart annotations: entry-30d to exit+10d
            'ohlc_window': _slice_ohlc(df, trade),
        }

        with open(output_dir / f'{tid}.json', 'w') as f:
            json.dump(record, f, indent=2, default=str)
        succeeded += 1

    return {'succeeded': succeeded, 'skipped': skipped, 'total': len(trades)}


def _slice_ohlc(df: pd.DataFrame, trade: Trade) -> list[dict]:
    """Return OHLC bars for entry-30d to exit+10d (or today+10d if open)."""
    start = trade.entry_date - timedelta(days=30)
    end = (trade.exit_date or market_today()) + timedelta(days=10)
    window = df[(df.index >= start) & (df.index <= end)]
    return [
        {
            'date': d.isoformat(),
            'open': _safe_float(r.get('open')),
            'high': _safe_float(r.get('high')),
            'low': _safe_float(r.get('low')),
            'close': _safe_float(r.get('close')),
            'volume': _safe_float(r.get('volume')),
        }
        for d, r in window.iterrows()
    ]


def _build_index(output_dir: Path) -> None:
    """Write _index.json listing all trade ids + summary for the journal page."""
    files = sorted(output_dir.glob('*.json'))
    index = []
    for p in files:
        if p.name == '_index.json':
            continue
        try:
            d = json.load(open(p))
        except Exception:  # noqa: BLE001
            continue
        index.append({
            'trade_id': d['trade_id'],
            'ticker': d['trade']['ticker'],
            'direction': d['trade']['direction'],
            'entry_date': d['trade']['entry_date'],
            'exit_date': d['trade'].get('exit_date'),
            'closed': d['trade']['closed'],
            'realized_R': d['trade'].get('realized_R'),
            'optimal_R': d['path_analytics'].get('optimal_R'),
            'capture_pct': d['path_analytics'].get('capture_pct'),
            'setup_type': d['setup_type'],
            'lesson': d['lesson'],
            'hold_days': d['path_analytics'].get('hold_calendar_days'),
        })
    # Sort by entry date descending (most recent first)
    index.sort(key=lambda r: (r.get('entry_date') or '', r['trade_id']), reverse=True)
    with open(output_dir / '_index.json', 'w') as f:
        json.dump({'generated_at': datetime.now(timezone.utc).isoformat(), 'trades': index}, f, indent=2)
    logger.info(f"Wrote index of {len(index)} trades to {output_dir / '_index.json'}")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    p = argparse.ArgumentParser(description='Per-trade post-mortem generator')
    p.add_argument('--input', type=Path, default=None,
                   help='Portfolio CSV (defaults to latest in data/portfolio/)')
    p.add_argument('--output', type=Path, default=OUTPUT_DIR)
    args = p.parse_args(argv)

    csv = args.input or find_latest_csv(Path('data/portfolio'))
    if not csv or not csv.exists():
        raise SystemExit("ERROR: no portfolio CSV found")

    logger.info(f"Reading trades from {csv}")
    trades = parse_csv(csv)
    logger.info(f"Loaded {len(trades)} trades")

    summary = generate_postmortems(trades, args.output)
    _build_index(args.output)

    print(f"\n✓ Generated {summary['succeeded']}/{summary['total']} post-mortems → {args.output}")
    if summary['skipped']:
        print(f"✗ Skipped {len(summary['skipped'])}:")
        for s in summary['skipped'][:10]:
            print(f"    {s}")
        if len(summary['skipped']) > 10:
            print(f"    ... and {len(summary['skipped']) - 10} more")


if __name__ == '__main__':
    main()
