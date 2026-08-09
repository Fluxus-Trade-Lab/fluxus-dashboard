"""Repair one archive day whose change_pct-derived counts are missing.

Rebuilds up_4pct / down_4pct / advances / declines for a single date when the
live run captured everything else correctly but lost the source's Change
column. Every other field on the row is left exactly as measured.

This is NOT the survivorship-biased reconstruction that backfill_breadth does.
The roster comes from the universe.json committed by that day's own run, so
membership is point-in-time correct, and the counts are rebuilt from prices for
that specific pair of sessions. The row is still stamped source='backfill',
because part of it is reconstructed rather than measured and downstream
consumers are entitled to know that.

Two independent price sources are computed and reconciled, because the failure
this repairs was itself a silent bad input:

  A  close(date) / close(prev_date) - 1, from the two committed universe.json
     snapshots. No survivorship loss — both rosters are point-in-time — but
     raw quotes, so a split between the two sessions reads as a huge move.
  B  the same ratio from yfinance split-adjusted closes. Immune to splits, but
     names delisted since then are missing.

A is the base: it is exactly what the live pipeline would have recorded that
day. B is a validator, not an authority — on the 2026-08-07 repair its handful
of disagreements with A were four names where B carried a stale flat bar
against a plainly real move in A (CHEC 11.21 -> 10.20, B said 0.00%) and four
sub-dollar names where A's two-decimal quotes quantize into fake percentage
moves. Neither source dominates, so B only overrides A at --split-threshold,
where the gap is far too large to be anything but a corporate action.

The run aborts if A and B disagree by more than --report-threshold on more
than --max-disagree of the overlap, since widespread disagreement means one of
them is wrong in a way this cannot resolve.

Not part of the daily cron. Run manually:

    python3 -m pipeline.tools.repair_change_pct_day \\
        --date 2026-08-07 \\
        --universe /tmp/universe-2026-08-07.json \\
        --prev-universe /tmp/universe-2026-08-06.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

from pipeline.screeners.breadth_store import (
    derive, load_archive, upsert_row, write_archive,
)

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_CSV = _REPO / 'data' / 'history' / 'breadth_archive.csv'

# Thresholds for the A-vs-B reconciliation described in the module docstring.
_REPORT_THRESHOLD = 0.03   # per-name |A - B| above this: worth listing
_SPLIT_THRESHOLD = 0.40    # per-name |A - B| above this: a corporate action, take B
_MAX_DISAGREE_RATE = 0.02  # fraction of overlap allowed past _REPORT_THRESHOLD
# Columns this tool is allowed to rewrite. Everything else on the row was
# measured correctly and must survive untouched.
_REPAIRED_COLUMNS = ('up_4pct', 'down_4pct', 'advances', 'declines')


def load_closes(path: str) -> pd.Series:
    """ticker -> close from a committed universe.json snapshot."""
    payload = json.loads(Path(path).read_text())
    rows = payload.get('rows', [])
    closes = {
        r['ticker']: float(r['close'])
        for r in rows
        if r.get('ticker') and r.get('close') is not None
    }
    logger.info("%s: %d rows, %d with a close (ts=%s)",
                path, len(rows), len(closes), payload.get('timestamp'))
    return pd.Series(closes, dtype=float)


def fetch_adjusted_changes(tickers: list[str], date: str, prev_date: str) -> pd.Series:
    """ticker -> split-adjusted change over (prev_date, date], via yfinance."""
    import yfinance as yf

    end = (pd.Timestamp(date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    out: dict[str, float] = {}
    batch_size = 400
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        logger.info("  yfinance batch %d: %d tickers", i // batch_size + 1, len(batch))
        try:
            data = yf.download(batch, start=prev_date, end=end, group_by='ticker',
                               auto_adjust=True, progress=False, threads=True)
        except Exception as exc:  # noqa: BLE001 — a dead batch is not fatal
            logger.warning("  batch download failed: %s", exc)
            continue
        if data is None or data.empty:
            continue
        for t in batch:
            try:
                hist = data[t]['Close'].dropna() if len(batch) > 1 else data['Close'].dropna()
                # Require both sessions present; a single bar cannot give a change.
                hist = hist[hist.index.strftime('%Y-%m-%d') <= date]
                if len(hist) < 2:
                    continue
                if hist.index[-1].strftime('%Y-%m-%d') != date:
                    continue
                prev, cur = float(hist.iloc[-2]), float(hist.iloc[-1])
                if prev > 0:
                    out[t] = cur / prev - 1
            except Exception:  # noqa: BLE001 — per-ticker gaps are expected
                continue
    return pd.Series(out, dtype=float)


def reconcile(snap: pd.Series, adj: pd.Series,
              report_threshold: float = _REPORT_THRESHOLD,
              split_threshold: float = _SPLIT_THRESHOLD) -> tuple[pd.Series, dict]:
    """Validate A against B, overriding only on corporate actions.

    Returns (change_pct, stats). See the module docstring for why B does not
    win the ordinary disagreements.
    """
    overlap = snap.index.intersection(adj.index)
    diff = (snap[overlap] - adj[overlap]).abs()
    flagged = diff[diff > report_threshold]
    splits = diff[diff > split_threshold]

    merged = snap.copy()
    merged.loc[splits.index] = adj.loc[splits.index]
    # Names yfinance knows and the snapshot pair does not add nothing here:
    # the roster is defined by the snapshot, so they are deliberately dropped.
    stats = {
        'snapshot_names': int(len(snap)),
        'adjusted_names': int(len(adj)),
        'overlap': int(len(overlap)),
        'flagged': int(len(flagged)),
        'flagged_rate': float(len(flagged) / len(overlap)) if len(overlap) else 1.0,
        'split_overrides': sorted(splits.index),
        'unverified': int(len(snap) - len(overlap)),
        'max_abs_diff': float(diff.max()) if len(diff) else 0.0,
        'median_abs_diff': float(diff.median()) if len(diff) else 0.0,
        'flagged_names': {t: {'snapshot': round(float(snap[t]), 4),
                              'adjusted': round(float(adj[t]), 4)}
                          for t in flagged.sort_values(ascending=False).index},
    }
    return merged, stats


def counts_from_changes(chg: pd.Series) -> dict:
    """Apply breadth_metrics.compute_snapshot's predicates, verbatim."""
    return {
        'up_4pct': int((chg >= 0.04).sum()),
        'down_4pct': int((chg <= -0.04).sum()),
        'advances': int((chg > 0).sum()),
        'declines': int((chg < 0).sum()),
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--date', required=True, help='market date (ET) to repair')
    ap.add_argument('--universe', required=True, help='universe.json committed for --date')
    ap.add_argument('--prev-universe', required=True,
                    help='universe.json committed for the prior session')
    ap.add_argument('--csv', default=str(_DEFAULT_CSV))
    ap.add_argument('--report-threshold', type=float, default=_REPORT_THRESHOLD)
    ap.add_argument('--split-threshold', type=float, default=_SPLIT_THRESHOLD)
    ap.add_argument('--max-disagree', type=float, default=_MAX_DISAGREE_RATE)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args(argv)

    frame = load_archive(args.csv)
    match = frame[frame['date'] == args.date]
    if match.empty:
        logger.error("No row for %s in %s — this tool repairs, it does not create",
                     args.date, args.csv)
        return 2
    existing = match.iloc[0].to_dict()

    cur = load_closes(args.universe)
    prev = load_closes(args.prev_universe)
    common = cur.index.intersection(prev.index)
    snap_chg = (cur[common] / prev[common] - 1).dropna()
    logger.info("Snapshot pair: %d names in both rosters", len(snap_chg))

    prev_date = str(frame[frame['date'] < args.date]['date'].iloc[-1])
    logger.info("Prior session in archive: %s", prev_date)
    adj_chg = fetch_adjusted_changes(sorted(snap_chg.index), args.date, prev_date)

    merged, stats = reconcile(snap_chg, adj_chg,
                              args.report_threshold, args.split_threshold)
    logger.info("Reconciliation: %s", json.dumps(stats, indent=2))
    if stats['flagged_rate'] > args.max_disagree:
        logger.error(
            "Sources disagree on %.1f%% of the overlap (> %.1f%%) — refusing to "
            "write. One of them is wrong in a way this tool cannot resolve.",
            stats['flagged_rate'] * 100, args.max_disagree * 100)
        return 3

    repaired = counts_from_changes(merged)
    logger.info("Repaired counts for %s:", args.date)
    for col in _REPAIRED_COLUMNS:
        logger.info("  %-10s %8s -> %s", col, existing.get(col), repaired[col])

    if args.dry_run:
        logger.info("Dry run — archive untouched")
        return 0

    row = {**existing, **repaired, 'source': 'backfill'}
    frame = derive(upsert_row(frame, row))
    write_archive(frame, args.csv)
    logger.info("Repaired %s (source=backfill); derived series recomputed", args.date)
    return 0


if __name__ == '__main__':
    sys.exit(main())
