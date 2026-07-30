"""One-time breadth history backfill from raw OHLC.

Reconstructs ~2.2 years of daily breadth rows (source='backfill') by applying
TODAY'S universe membership to a 3-year adjusted-close download. This is
survivorship-biased and point-in-time-wrong by construction — reconstructed
days read slightly stronger than reality. The 'source' flag exists so downstream
consumers can tell reconstruction from measurement.

Dates come from the yfinance session index (US exchange dates) — never the host
clock. Not part of the daily cron; run manually:

    python3 -m pipeline.tools.backfill_breadth --dry-run
    python3 -m pipeline.tools.backfill_breadth
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.screeners.breadth_store import (
    BREADTH_COLUMNS, derive, load_archive, write_archive,
)

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_CSV = _REPO / 'data' / 'history' / 'breadth_archive.csv'
_UNIVERSE_JSON = _REPO / 'data' / 'output' / 'universe.json'
_MIN_PRIOR_SESSIONS = 200
# Live rows with pct_above_200sma below this are enrichment failures (e.g. the
# Jul 15-24 2026 poison, ~0.2-0.8%) — backfill may replace them on merge.
_IMPLAUSIBLE_PCT200 = 5.0
# Live rows with universe_size below this are partial-universe failures (e.g.
# the Jun 8 2026 200-name Finviz day) — same replacement policy.
_IMPLAUSIBLE_MIN_UNIVERSE = 1500
# Columns a surviving LIVE row inherits from its same-date reconstruction:
# NH/NL because pre-v2 live rows used a ±2% band instead of true extremes, and
# the 13%/34d pair because the live pipeline did not compute it at all.
_HYDRATED_COLUMNS = ('new_highs', 'new_lows', 'up_13pct_34d', 'down_13pct_34d')


def compute_backfill_rows(
    closes: pd.DataFrame,
    spx: pd.Series,
    highs: pd.DataFrame | None = None,
    lows: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Pure reconstruction: one archive row per date with >=200 prior sessions.

    closes: DatetimeIndex (ascending) x tickers, adjusted close.
    spx: date-indexed S&P 500 close (may be missing dates -> NaN spx_close).
    highs/lows: same shape as closes, adjusted intraday High/Low. When given,
    NH/NL are measured close-vs-1y-extreme-of-intraday, matching the live
    pipeline exactly (yfinance_adapter: close/max(High)-1 >= -0.001). When
    omitted they fall back to close-based extremes — a different, looser rule
    that reads several times more new highs. Always pass them in production.

    Perf lookbacks mirror the live iloc offsets: perf_1m = iloc[-21] = 20
    sessions back, perf_3m = iloc[-63] = 62 back, perf_34d = iloc[-35] = 34 back.
    Derived columns are left NA; breadth_store.derive() fills them post-merge.
    """
    chg = closes / closes.shift(1) - 1
    p1m = closes / closes.shift(20) - 1
    p34 = closes / closes.shift(34) - 1
    p3m = closes / closes.shift(62) - 1
    sma20 = closes.rolling(20).mean()
    sma40 = closes.rolling(40).mean()
    sma50 = closes.rolling(50).mean()
    sma200 = closes.rolling(200).mean()
    hi_src = closes if highs is None else highs.reindex(index=closes.index, columns=closes.columns)
    lo_src = closes if lows is None else lows.reindex(index=closes.index, columns=closes.columns)
    hi252 = hi_src.rolling(252, min_periods=_MIN_PRIOR_SESSIONS).max()
    lo252 = lo_src.rolling(252, min_periods=_MIN_PRIOR_SESSIONS).min()

    rows = []
    for i in range(_MIN_PRIOR_SESSIONS, len(closes)):
        date = closes.index[i]
        c = closes.iloc[i]
        n = int(c.notna().sum())
        if n == 0:
            continue
        d_chg, d_1m, d_34, d_3m = chg.iloc[i], p1m.iloc[i], p34.iloc[i], p3m.iloc[i]
        adv = int((d_chg > 0).sum())
        dec = int((d_chg < 0).sum())
        spx_val = spx.get(date)
        rows.append({
            'date': date.strftime('%Y-%m-%d'),
            'source': 'backfill',
            'universe_size': n,
            'spx_close': float(spx_val) if pd.notna(spx_val) else None,
            'up_4pct': int((d_chg >= 0.04).sum()),
            'down_4pct': int((d_chg <= -0.04).sum()),
            'up_25pct_qtr': int((d_3m >= 0.25).sum()),
            'down_25pct_qtr': int((d_3m <= -0.25).sum()),
            'up_25pct_month': int((d_1m >= 0.25).sum()),
            'down_25pct_month': int((d_1m <= -0.25).sum()),
            'up_50pct_month': int((d_1m >= 0.50).sum()),
            'down_50pct_month': int((d_1m <= -0.50).sum()),
            'up_13pct_34d': int((d_34 >= 0.13).sum()),
            'down_13pct_34d': int((d_34 <= -0.13).sum()),
            't2108': round(float((c > sma40.iloc[i]).sum()) / n * 100, 2),
            'pct_above_200sma': round(float((c > sma200.iloc[i]).sum()) / n * 100, 2),
            'pct_above_50sma': round(float((c > sma50.iloc[i]).sum()) / n * 100, 2),
            'pct_above_20sma': round(float((c > sma20.iloc[i]).sum()) / n * 100, 2),
            'advances': adv,
            'declines': dec,
            'new_highs': int((c >= hi252.iloc[i] * (1 - 0.001)).sum()),
            'new_lows': int((c <= lo252.iloc[i] * (1 + 0.001)).sum()),
        })
    out = pd.DataFrame(rows)
    for col in BREADTH_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    return out[BREADTH_COLUMNS]


def merge_backfill(existing: pd.DataFrame, backfill: pd.DataFrame) -> pd.DataFrame:
    """Merge backfill under existing rows.

    Existing (live) rows win on date collision — unless the live row is
    implausible (pct_above_200sma < _IMPLAUSIBLE_PCT200, an enrichment
    failure, OR universe_size < _IMPLAUSIBLE_MIN_UNIVERSE, a partial-universe
    failure), in which case a backfill row for the same date replaces it.
    An implausible live row with no backfill replacement stays: better
    garbage than a hole — downstream dry-run gates surface it.
    NaN/absent in either column is NOT implausible.

    Non-session artifacts are dropped outright. The backfill frame has a row
    for EVERY real session in its date range, so an existing row whose date
    falls inside [backfill.min, backfill.max] but is absent from the backfill
    dates was never a trading day (legacy naive-clock re-runs stamped rows on
    e.g. Sunday 2026-05-24 and Memorial Day 2026-05-25). Existing rows outside
    the backfill range are kept regardless — we cannot judge them.

    Finally, surviving live rows are HYDRATED from their same-date
    reconstruction on _HYDRATED_COLUMNS only. Those live rows predate the v2
    semantics: NH/NL used a ±2% band (yielding e.g. 327 new highs next to 29
    under the true-extreme rule) and the 13%/34d columns did not exist at all.
    The reconstruction is the same universe on the same day under the current
    rules, so it is the right source for exactly those columns — every other
    column stays as measured.
    """
    implausible = pd.Series(False, index=existing.index)
    pct = existing.get('pct_above_200sma')
    if pct is not None:
        implausible |= pd.to_numeric(pct, errors='coerce') < _IMPLAUSIBLE_PCT200
    uni = existing.get('universe_size')
    if uni is not None:
        implausible |= pd.to_numeric(uni, errors='coerce') < _IMPLAUSIBLE_MIN_UNIVERSE
    backfill_dates = set(backfill['date'])
    replaceable_dates = set(existing.loc[implausible, 'date']) & backfill_dates

    non_session = pd.Series(False, index=existing.index)
    if len(backfill) and len(existing):
        lo, hi = min(backfill_dates), max(backfill_dates)
        dates = existing['date'].astype(str)
        non_session = dates.between(lo, hi) & ~dates.isin(backfill_dates)

    keep = existing[~existing['date'].isin(replaceable_dates) & ~non_session].copy()
    keep = _hydrate_live_rows(keep, backfill)
    add = backfill[~backfill['date'].isin(set(keep['date']))]
    merged = pd.concat([keep, add], ignore_index=True)
    return merged.sort_values('date').reset_index(drop=True)


def _hydrate_live_rows(keep: pd.DataFrame, backfill: pd.DataFrame) -> pd.DataFrame:
    """Overwrite _HYDRATED_COLUMNS on surviving live rows from same-date backfill."""
    cols = [c for c in _HYDRATED_COLUMNS if c in backfill.columns]
    if not cols or 'date' not in keep.columns or not len(keep):
        return keep
    lookup = backfill.set_index('date')
    is_live = keep.get('source', pd.Series('live', index=keep.index)).eq('live')
    targets = keep.index[is_live & keep['date'].isin(lookup.index)]
    for col in cols:
        if col not in keep.columns:
            keep[col] = pd.NA
        keep.loc[targets, col] = lookup.loc[keep.loc[targets, 'date'], col].to_numpy()
    return keep


# ── Network + CLI (not unit-tested; exercised by --dry-run) ──────────

def _load_tickers() -> list[str]:
    data = json.loads(_UNIVERSE_JSON.read_text(encoding='utf-8'))
    return sorted({r['ticker'] for r in data['rows'] if r.get('ticker')})


def _download_ohlc(tickers: list[str], years: int,
                   cache: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Download adjusted Close/High/Low as three aligned wide frames.

    High and Low are required: NH/NL must be measured against intraday extremes
    to match the live pipeline. All three share ONE cache file (a dict) so a
    closes-only cache can never be mistaken for a complete one.
    """
    if cache.exists():
        logger.info("Using cached OHLC: %s", cache)
        cached = pd.read_pickle(cache)
        if not isinstance(cached, dict) or not {'close', 'high', 'low'} <= set(cached):
            raise RuntimeError(
                f"Cache {cache} is not a close/high/low dict — delete it and re-run")
        return cached['close'], cached['high'], cached['low']
    import yfinance as yf
    parts: dict[str, list[pd.Series]] = {'Close': [], 'High': [], 'Low': []}
    batch_size = 200
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        logger.info("Downloading batch %d-%d of %d", i, i + len(batch), len(tickers))
        data = yf.download(batch, period=f'{years}y', group_by='ticker',
                           auto_adjust=True, progress=False, threads=True)
        for t in batch:
            try:
                cols = {f: data[t][f] for f in parts}
            except KeyError:
                logger.warning("No data for %s", t)
                continue
            for field, series in cols.items():
                parts[field].append(series.rename(t))

    def _wide(field: str) -> pd.DataFrame:
        frame = pd.concat(parts[field], axis=1).sort_index()
        frame.index = pd.DatetimeIndex(frame.index).tz_localize(None)
        return frame

    closes, highs, lows = _wide('Close'), _wide('High'), _wide('Low')
    highs = highs.reindex(index=closes.index, columns=closes.columns)
    lows = lows.reindex(index=closes.index, columns=closes.columns)
    cache.parent.mkdir(parents=True, exist_ok=True)
    # pickle, not parquet: host has no pyarrow/fastparquet
    pd.to_pickle({'close': closes, 'high': highs, 'low': lows}, cache)
    return closes, highs, lows


def _download_spx(years: int) -> pd.Series:
    import yfinance as yf
    spx = yf.download('^GSPC', period=f'{years}y', auto_adjust=True, progress=False)
    close = spx['Close']
    if isinstance(close, pd.DataFrame):  # yfinance MultiIndex quirk
        close = close.iloc[:, 0]
    close.index = pd.DatetimeIndex(close.index).tz_localize(None)
    return close


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--years', type=int, default=3)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--csv', default=str(_DEFAULT_CSV))
    parser.add_argument('--cache', default=str(_REPO / 'data' / 'history' / 'backfill_ohlc.pkl'))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    tickers = _load_tickers()
    logger.info("Universe: %d tickers", len(tickers))
    closes, highs, lows = _download_ohlc(tickers, args.years, Path(args.cache))
    spx = _download_spx(args.years)

    backfill = compute_backfill_rows(closes, spx, highs=highs, lows=lows)
    existing = load_archive(args.csv)
    merged = derive(merge_backfill(existing, backfill))

    n_back = int((merged['source'] == 'backfill').sum())
    n_live = int((merged['source'] == 'live').sum())
    print(f"\nMerged archive: {len(merged)} rows "
          f"({n_back} backfill, {n_live} live), "
          f"{merged['date'].iloc[0]} .. {merged['date'].iloc[-1]}")
    print("\nNull rates:")
    print((merged.isna().mean().round(3)).to_string())
    print("\nMetric ranges (min..max):")
    for col in ['universe_size', 'up_4pct', 'down_4pct', 'pct_above_200sma',
                't2108', 'new_highs', 'new_lows', 'mcclellan_osc', 'ad_line']:
        vals = pd.to_numeric(merged[col], errors='coerce')
        print(f"  {col}: {vals.min():.1f} .. {vals.max():.1f}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0
    write_archive(merged, args.csv)
    print(f"\nWrote {args.csv}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
