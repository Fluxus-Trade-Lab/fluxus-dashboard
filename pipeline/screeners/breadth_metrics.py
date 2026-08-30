"""Self-calculated market breadth metrics.

Combines Stockbee Market Monitor scans with classic breadth indicators.
Consumes the Finviz universe DataFrame (with sma40_dist from yfinance
enrichment) and computes today's snapshot; persistence and derived series
(A/D line, McClellan, rolling ratios) live in the canonical archive CSV
managed by ``pipeline.screeners.breadth_store``.

Metrics computed:
- Stockbee MM: 4% up/down, 5d/10d ratios, 25% qtr/month, 50% month, 13%/34d
- Classic: % above 20/40/50/200 SMA, A/D line, McClellan Oscillator, NH/NL
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import pandas as pd

from pipeline.marketcal import last_completed_session
from pipeline.screeners.breadth_store import (
    load_archive,
    upsert_row,
    derive,
    write_archive,
    check_quality,
)

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────
_NEW_HIGH_THRESHOLD = -0.001  # true 52w high (0.1% float/quote tolerance)
_NEW_LOW_THRESHOLD = 0.001    # true 52w low
# Liquidity gate for the *_liq new-high/new-low counts. $5M/day and $5 a share
# is where the SPAC trust band ($9.50-11 on ~16k shares) and the sub-$2 shells
# both fall out; it is a floor for "a name a human could actually trade", not
# a tuned parameter, and it was never searched over alternatives.
_MIN_PRICE = 5.0
_MIN_DOLLAR_VOL = 5_000_000.0


def compute_snapshot(universe: pd.DataFrame) -> Dict[str, Any]:
    """Compute a single day's breadth snapshot from the universe.

    Parameters
    ----------
    universe : pd.DataFrame
        Finviz universe with columns: change_pct, perf_1m, perf_3m,
        sma20_dist, sma40_dist, sma50_dist, sma200_dist, high_52w, low_52w.

    Returns
    -------
    dict
        All daily breadth counts and percentages.
    """
    n = len(universe)
    if n == 0:
        return {
            'universe_size': 0,
            'up_4pct': 0, 'down_4pct': 0,
            'up_25pct_qtr': 0, 'down_25pct_qtr': 0,
            'up_25pct_month': 0, 'down_25pct_month': 0,
            'up_50pct_month': 0, 'down_50pct_month': 0,
            'up_13pct_34d': 0, 'down_13pct_34d': 0,
            't2108': 0.0,
            'pct_above_200sma': 0.0, 'pct_above_50sma': 0.0,
            'pct_above_20sma': 0.0,
            'advances': 0, 'declines': 0,
            'new_highs': 0, 'new_lows': 0,
            'net_advances': 0,
        }

    chg = pd.to_numeric(universe['change_pct'], errors='coerce')
    perf_1m = pd.to_numeric(universe.get('perf_1m', pd.Series(dtype=float)), errors='coerce')
    perf_3m = pd.to_numeric(universe.get('perf_3m', pd.Series(dtype=float)), errors='coerce')
    perf_34d = pd.to_numeric(universe.get('perf_34d', pd.Series(dtype=float)), errors='coerce')

    # Stockbee MM scans
    up_4pct = int((chg >= 0.04).sum())
    down_4pct = int((chg <= -0.04).sum())
    up_25pct_qtr = int((perf_3m >= 0.25).sum())
    down_25pct_qtr = int((perf_3m <= -0.25).sum())
    up_25pct_month = int((perf_1m >= 0.25).sum())
    down_25pct_month = int((perf_1m <= -0.25).sum())
    up_50pct_month = int((perf_1m >= 0.50).sum())
    down_50pct_month = int((perf_1m <= -0.50).sum())
    up_13pct_34d = int((perf_34d >= 0.13).sum())
    down_13pct_34d = int((perf_34d <= -0.13).sum())

    # Classic breadth: % above MAs
    sma20 = pd.to_numeric(universe.get('sma20_dist', pd.Series(dtype=float)), errors='coerce')
    sma40 = pd.to_numeric(universe.get('sma40_dist', pd.Series(dtype=float)), errors='coerce')
    sma50 = pd.to_numeric(universe.get('sma50_dist', pd.Series(dtype=float)), errors='coerce')
    sma200 = pd.to_numeric(universe.get('sma200_dist', pd.Series(dtype=float)), errors='coerce')

    pct_above_20 = round(float((sma20 > 0).sum()) / n * 100, 2)
    t2108 = round(float((sma40 > 0).sum()) / n * 100, 2)
    pct_above_50 = round(float((sma50 > 0).sum()) / n * 100, 2)
    pct_above_200 = round(float((sma200 > 0).sum()) / n * 100, 2)

    # Advances / Declines
    advances = int((chg > 0).sum())
    declines = int((chg < 0).sum())

    # New 52w highs / lows
    high_52w = pd.to_numeric(universe.get('high_52w', pd.Series(dtype=float)), errors='coerce')
    low_52w = pd.to_numeric(universe.get('low_52w', pd.Series(dtype=float)), errors='coerce')
    new_highs = int((high_52w >= _NEW_HIGH_THRESHOLD).sum())
    new_lows = int((low_52w <= _NEW_LOW_THRESHOLD).sum())

    # New 4-week (20-session) highs / lows -- the matched-horizon version.
    # Added 2026-08-31. The 252d pair above needs a name to undercut a whole
    # year before it counts, so it is structurally blind to a four-week
    # deterioration: on 2026-08-28 it was the ONE reading in the breadth panel
    # that stayed benign while %above-50sma, 10d net advances and McClellan
    # all fell. Same threshold and tolerance as the 52w pair, so the two are
    # directly comparable; NULL (not 0) when the column is absent, because a
    # missing input must not read as "no new lows today".
    high_20d = pd.to_numeric(universe.get('high_20d', pd.Series(dtype=float)), errors='coerce')
    low_20d = pd.to_numeric(universe.get('low_20d', pd.Series(dtype=float)), errors='coerce')
    have_20d = int(high_20d.notna().sum()), int(low_20d.notna().sum())
    new_highs_4w = int((high_20d >= _NEW_HIGH_THRESHOLD).sum()) if have_20d[0] else None
    new_lows_4w = int((low_20d <= _NEW_LOW_THRESHOLD).sum()) if have_20d[1] else None

    # --- Liquidity gate (2026-08-31) -------------------------------------
    # On 2026-08-28, 88% of the 66 names counted as 52-week new highs sat in
    # the $9.50-11 SPAC trust band, 89% traded under 100k shares/day, and the
    # median dollar volume was $166k against $8.0M for the universe. A SPAC
    # trust accretes with interest, so it prints a "new 52-week high" almost
    # every session regardless of the market -- which is why this reading sat
    # still on 08-28 while three other breadth readings fell. Names newly
    # listed inside the window make it worse: several had 20-48 bars of
    # history in total, so their entire life IS the lookback.
    #
    # The gate is emitted ALONGSIDE the ungated counts, never instead of
    # them, for two reasons. (1) Continuity: `new_highs`/`new_lows` have 574
    # rows of archive behind them and silently redefining them would put a
    # second level break into a series that already has one (universe went
    # 3000 -> 5614 on 2026-08-14). (2) Identification: with 4 counts on a
    # 2x2 of {20d, 252d} x {gated, ungated}, the window effect and the
    # pollution effect can be read separately. Collapsing to one gated
    # number would confound them -- any change could be either cause.
    #
    # NULL, not 0, when the inputs to the gate are missing: a count of zero
    # reads as "nothing made a new low today", the most reassuring possible
    # rendering of a data outage.
    px = pd.to_numeric(universe.get('close', pd.Series(dtype=float)), errors='coerce')
    avol = pd.to_numeric(universe.get('avg_volume', pd.Series(dtype=float)), errors='coerce')
    liquid = (px >= _MIN_PRICE) & (px * avol >= _MIN_DOLLAR_VOL)
    n_liquid = int(liquid.sum())
    gate_usable = int((px.notna() & avol.notna()).sum()) > 0

    def _gated(series, cmp_ok, have):
        if not (gate_usable and have):
            return None
        return int((cmp_ok(series) & liquid).sum())

    hi_ok = lambda x: x >= _NEW_HIGH_THRESHOLD
    lo_ok = lambda x: x <= _NEW_LOW_THRESHOLD
    new_highs_liq = _gated(high_52w, hi_ok, int(high_52w.notna().sum()))
    new_lows_liq = _gated(low_52w, lo_ok, int(low_52w.notna().sum()))
    new_highs_4w_liq = _gated(high_20d, hi_ok, have_20d[0])
    new_lows_4w_liq = _gated(low_20d, lo_ok, have_20d[1])

    return {
        'universe_size': n,
        'up_4pct': up_4pct,
        'down_4pct': down_4pct,
        'up_25pct_qtr': up_25pct_qtr,
        'down_25pct_qtr': down_25pct_qtr,
        'up_25pct_month': up_25pct_month,
        'down_25pct_month': down_25pct_month,
        'up_50pct_month': up_50pct_month,
        'down_50pct_month': down_50pct_month,
        'up_13pct_34d': up_13pct_34d,
        'down_13pct_34d': down_13pct_34d,
        't2108': t2108,
        'pct_above_200sma': pct_above_200,
        'pct_above_50sma': pct_above_50,
        'pct_above_20sma': pct_above_20,
        'advances': advances,
        'declines': declines,
        'new_highs': new_highs,
        'new_lows': new_lows,
        'new_highs_4w': new_highs_4w,
        'new_lows_4w': new_lows_4w,
        'new_highs_liq': new_highs_liq,
        'new_lows_liq': new_lows_liq,
        'new_highs_4w_liq': new_highs_4w_liq,
        'new_lows_4w_liq': new_lows_4w_liq,
        'liquid_universe': n_liquid if gate_usable else None,
        'net_advances': advances - declines,
    }


def run(
    universe: pd.DataFrame,
    csv_path: str,
    spx_close: Optional[float] = None,
) -> Dict[str, Any]:
    """Compute today's breadth snapshot, update the canonical archive, emit breadth.json.

    The archive CSV is the single source of truth (see breadth_store). On quality
    rejection the archive is untouched and the output is served stale from its tail.
    """
    snapshot = compute_snapshot(universe)
    frame = load_archive(csv_path)

    if len(universe) > 0:
        null_rate = float(
            pd.to_numeric(universe.get('sma200_dist', pd.Series(dtype=float)),
                          errors='coerce').isna().mean()
        )
    else:
        null_rate = 1.0

    # The archive is keyed by SESSION, not by wall date: a Sunday cron run must
    # file its numbers under Friday or it invents a trading day -- and a
    # premarket run must file under YESTERDAY, not today (2026-08-19: a 05:18
    # ET dispatch filed 123/125 under a session that had not traded). Same
    # label every other writer in run_all uses: last_completed_session.
    today_iso = last_completed_session().isoformat()
    ok, reason = check_quality(frame, snapshot, null_rate, today_iso, spx_close)
    if ok:
        row = {
            'date': today_iso,
            'source': 'live',
            'spx_close': spx_close,
            **snapshot,
        }
        frame = derive(upsert_row(frame, row))
        write_archive(frame, csv_path)
        quality: Dict[str, Any] = {'stale': False}
    else:
        logger.error("Breadth quality guard rejected today's row: %s", reason)
        frame = derive(frame)
        quality = {'stale': True, 'reason': reason}
        if len(frame) > 0:
            quality['as_of'] = str(frame['date'].iloc[-1])

    return _build_output(frame, quality, snapshot, spx_close)


def _build_output(
    frame: pd.DataFrame,
    quality: Dict[str, Any],
    snapshot: Dict[str, Any],
    spx_close: Optional[float],
) -> Dict[str, Any]:
    """Derive the breadth.json payload from the archive tail (last 100 rows)."""
    tail = frame.tail(100)
    rows = [
        {k: (None if pd.isna(v) else v) for k, v in r.items()}
        for r in tail.to_dict(orient='records')
    ]
    last = rows[-1] if rows else {}

    def _col(name: str) -> list:
        return [r.get(name) for r in rows]

    return {
        'universe_size': last.get('universe_size', snapshot['universe_size']),
        'spx_close': last.get('spx_close', spx_close),
        'mm': {
            'up_4pct': last.get('up_4pct'),
            'down_4pct': last.get('down_4pct'),
            'ratio_5d': last.get('ratio_5d'),
            'ratio_10d': last.get('ratio_10d'),
            'up_25pct_qtr': last.get('up_25pct_qtr'),
            'down_25pct_qtr': last.get('down_25pct_qtr'),
            'up_25pct_month': last.get('up_25pct_month'),
            'down_25pct_month': last.get('down_25pct_month'),
            'up_50pct_month': last.get('up_50pct_month'),
            'down_50pct_month': last.get('down_50pct_month'),
            'up_13pct_34d': last.get('up_13pct_34d'),
            'down_13pct_34d': last.get('down_13pct_34d'),
        },
        'breadth': {
            't2108': last.get('t2108'),
            'pct_above_200sma': last.get('pct_above_200sma'),
            'pct_above_50sma': last.get('pct_above_50sma'),
            'pct_above_20sma': last.get('pct_above_20sma'),
            'advances': last.get('advances'),
            'declines': last.get('declines'),
            'new_highs': last.get('new_highs'),
            'new_lows': last.get('new_lows'),
            'ad_line': last.get('ad_line'),
            'mcclellan_osc': last.get('mcclellan_osc'),
        },
        'history': {
            'dates': _col('date'),
            'pct_above_200sma': _col('pct_above_200sma'),
            'pct_above_50sma': _col('pct_above_50sma'),
            'pct_above_20sma': _col('pct_above_20sma'),
            'mcclellan_osc': _col('mcclellan_osc'),
            'rows': rows,
        },
        'data_quality': quality,
    }
