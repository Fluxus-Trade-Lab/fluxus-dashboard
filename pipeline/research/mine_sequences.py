"""Rank screener sequences by measured edge over a random-entry baseline.

Testing ~49 pairs (and optionally hundreds of triples) against five months
of one market regime WILL produce impressive-looking results by chance.
Three guards push back, and all three appear in the report:

  1. every statistic is reported net of a random-entry baseline drawn from
     the same ticker/date universe — beating zero is not the bar;
  2. each sequence is scored independently in the first and second half of
     the window, and a sign flip flags it `unstable`;
  3. anything below `--min-n` is shown but excluded from the ranking.

"No sequence clears the bar" is a legitimate result, and the report says so
plainly when it happens.

    python3 -m pipeline.research.mine_sequences --window 10 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import itertools
import logging
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

from pipeline.research.outcomes import HORIZONS, measure_outcome
from pipeline.research.sequences import (
    MIN_N, find_pair_instances, find_triple_instances, is_unstable,
    random_instances, split_dates, summarize,
)
from pipeline.screeners.ticker_events import load_events
from pipeline.screeners.ticker_heat import WEIGHTS

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_EVENTS = _REPO / 'data' / 'history' / 'ticker_events.csv'
_DEFAULT_PANEL = _REPO / '.cache' / 'price_panel.pkl'
_OUT_DIR = _REPO / 'data' / 'research'

RANK_KEY_TEMPLATE = 'net_median_excess_{h}'
RANK_HORIZON = 10


def measure_instances(instances: List[Dict[str, Any]],
                      panel: Dict[str, pd.DataFrame],
                      spy: pd.DataFrame,
                      horizons: Sequence[int] = HORIZONS
                      ) -> Tuple[List[Dict[str, Any]], int]:
    """Measure each instance; return (outcomes, count lost to missing data)."""
    outcomes: List[Dict[str, Any]] = []
    lost = 0
    for inst in instances:
        bars = panel.get(inst['ticker'])
        if bars is None:
            lost += 1
            continue
        out = measure_outcome(bars, spy, inst['signal_date'], horizons=horizons)
        if out is None:
            lost += 1
            continue
        outcomes.append(out)
    return outcomes, lost


_NET_KEYS = ('median_excess_{h}', 'mean_excess_{h}', 'median_mfe_r_{h}',
             'median_mae_r_{h}', 'win_rate_{h}')


def net_of_baseline(seq: Dict[str, Any], base: Dict[str, Any],
                    horizons: Sequence[int] = HORIZONS) -> Dict[str, Any]:
    """Sequence statistics minus the baseline's, prefixed `net_`."""
    out: Dict[str, Any] = {}
    for h in horizons:
        for template in _NET_KEYS:
            key = template.format(h=h)
            a, b = seq.get(key), base.get(key)
            out[f'net_{key}'] = None if a is None or b is None else round(a - b, 6)
    return out


def render_markdown(rows: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    """The report: limits first, then the ranking, then what was excluded."""
    rank_key = RANK_KEY_TEMPLATE.format(h=RANK_HORIZON)
    lines: List[str] = []
    lines.append(f"# Sequence mining — as of {meta['as_of']}\n")
    lines.append("## Read this before the table\n")
    lines.append(
        f"- **One regime.** {meta['sessions']} archive sessions across a single "
        "market environment. A sequence that works here may only be describing "
        "that environment.\n"
        f"- **Multiple comparisons.** Many sequences were tested; some will look "
        "excellent by chance. Every number below is reported **net of a "
        "random-entry baseline** drawn from the same tickers and dates, and any "
        "sequence whose two half-samples disagree in sign is flagged unstable "
        "and excluded from the ranking.\n"
        f"- **Survivorship.** Prices were fetched today, so delisted and renamed "
        f"tickers are missing ({meta['coverage_missing']} of "
        f"{meta['tickers']} tickers). Those failures skew toward losers, so the "
        "surviving numbers are, if anything, flattering. Per-sequence "
        "instances lost to missing prices are in the `lost` column.\n"
        f"- **Window.** {meta['window']} archive sessions. The archive omits "
        "non-session and untrustworthy days, so an N-session gap spans more "
        "calendar time than N days.\n"
        f"- Ranked on `{rank_key}`; `--min-n {meta['min_n']}`, `--seed "
        f"{meta['seed']}`.\n"
    )

    ranked = [r for r in rows if not r['under_powered'] and not r['unstable']]
    ranked.sort(key=lambda r: (r.get(rank_key) is None, -(r.get(rank_key) or 0)))

    lines.append("## Ranked sequences\n")
    if not ranked:
        lines.append(
            "**No sequence cleared the bar.** Every candidate was either "
            "under-powered or unstable across the two half-samples. That is a "
            "real result, not a tooling failure — on this much data, in this one "
            "regime, nothing here is distinguishable from random entry.\n")
    else:
        lines.append(f"| Sequence | n | lost | net median excess ({RANK_HORIZON}d) "
                     f"| median MFE (R) | median MAE (R) | win rate |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for r in ranked:
            lines.append(
                f"| {r['sequence']} | {r['n']} | {r['lost']} "
                f"| {_fmt_pct(r.get(rank_key))} "
                f"| {_fmt_num(r.get(f'median_mfe_r_{RANK_HORIZON}'))} "
                f"| {_fmt_num(r.get(f'median_mae_r_{RANK_HORIZON}'))} "
                f"| {_fmt_pct(r.get(f'win_rate_{RANK_HORIZON}'), pct=True)} |")
        lines.append("")

    unstable = [r for r in rows if r['unstable'] and not r['under_powered']]
    lines.append("## Excluded — unstable across half-samples\n")
    lines.append(_simple_list(unstable, rank_key) or "_None._\n")

    weak = [r for r in rows if r['under_powered']]
    lines.append(f"## Excluded — fewer than {meta['min_n']} instances\n")
    lines.append(_simple_list(weak, rank_key) or "_None._\n")

    return "\n".join(lines)


def _fmt_num(v: Any) -> str:
    return '—' if v is None else f"{v:.2f}"


def _fmt_pct(v: Any, pct: bool = False) -> str:
    if v is None:
        return '—'
    return f"{v * 100:.1f}%" if not pct else f"{v * 100:.0f}%"


def _simple_list(rows: List[Dict[str, Any]], rank_key: str) -> str:
    if not rows:
        return ''
    out = ["| Sequence | n | net median excess |", "|---|---:|---:|"]
    for r in sorted(rows, key=lambda r: -(r.get(rank_key) or 0)):
        out.append(f"| {r['sequence']} | {r['n']} | {_fmt_pct(r.get(rank_key))} |")
    return "\n".join(out) + "\n"


# ── CLI (I/O; the pieces above are pure) ─────────────────────────────

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--window', type=int, default=10)
    parser.add_argument('--min-n', type=int, default=MIN_N)
    parser.add_argument('--horizons', default='5,10,21')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--triples', action='store_true')
    parser.add_argument('--events', default=str(_DEFAULT_EVENTS))
    parser.add_argument('--panel', default=str(_DEFAULT_PANEL))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    horizons = tuple(int(h) for h in args.horizons.split(','))
    panel_path = Path(args.panel)
    if not panel_path.exists():
        print(f"No price panel at {panel_path}. Run:\n"
              f"  python3 -m pipeline.tools.build_price_panel")
        return 1
    with open(panel_path, 'rb') as f:
        panel: Dict[str, pd.DataFrame] = pickle.load(f)
    spy = panel.get('SPY')
    if spy is None:
        print("Panel has no SPY — excess returns cannot be computed.")
        return 1

    events = load_events(args.events)
    if len(events) == 0:
        print("Event archive is empty.")
        return 1

    mid, last = split_dates(events)
    first_half = events[events['date'].astype(str) <= mid]
    second_half = events[events['date'].astype(str) > mid]
    screeners = sorted(WEIGHTS)

    candidates: List[Tuple[str, Tuple[str, ...]]] = [
        (f"{a} -> {b}", (a, b))
        for a, b in itertools.product(screeners, repeat=2) if a != b
    ]
    if args.triples:
        candidates += [
            (f"{a} -> {b} -> {c}", (a, b, c))
            for a, b, c in itertools.product(screeners, repeat=3)
            if a != b and b != c
        ]
    logger.info("Evaluating %d candidate sequences", len(candidates))

    def _find(frame: pd.DataFrame, legs: Tuple[str, ...]) -> List[Dict[str, Any]]:
        if len(legs) == 2:
            return find_pair_instances(frame, legs[0], legs[1], window=args.window)
        return find_triple_instances(frame, legs[0], legs[1], legs[2],
                                     window=args.window)

    rows: List[Dict[str, Any]] = []
    for label, legs in candidates:
        instances = _find(events, legs)
        outcomes, lost = measure_instances(instances, panel, spy, horizons)
        seq_stats = summarize(outcomes, horizons=horizons, lost=lost)
        if seq_stats['n'] == 0:
            continue

        base_inst = random_instances(events, n=seq_stats['n'], seed=args.seed)
        base_out, base_lost = measure_instances(base_inst, panel, spy, horizons)
        base_stats = summarize(base_out, horizons=horizons, lost=base_lost)

        half_stats = []
        for half in (first_half, second_half):
            h_out, h_lost = measure_instances(_find(half, legs), panel, spy, horizons)
            half_stats.append(summarize(h_out, horizons=horizons, lost=h_lost))

        row: Dict[str, Any] = {'sequence': label, **seq_stats}
        row.update(net_of_baseline(seq_stats, base_stats, horizons))
        row['under_powered'] = seq_stats['n'] < args.min_n
        row['unstable'] = is_unstable(half_stats[0], half_stats[1],
                                      f'median_excess_{RANK_HORIZON}')
        rows.append(row)

    coverage = len(set(events['ticker'].astype(str)) - set(panel))
    meta = {'as_of': last, 'window': args.window, 'seed': args.seed,
            'min_n': args.min_n, 'sessions': events['date'].nunique(),
            'tickers': events['ticker'].nunique(), 'coverage_missing': coverage}

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = _OUT_DIR / f"sequences_{last}.md"
    csv_path = _OUT_DIR / f"sequences_{last}.csv"
    md_path.write_text(render_markdown(rows, meta), encoding='utf-8')
    if rows:
        fieldnames = sorted({k for r in rows for k in r})
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    ranked = [r for r in rows if not r['under_powered'] and not r['unstable']]
    print(f"\n{len(rows)} sequences evaluated, {len(ranked)} cleared the bar")
    print(f"Report: {md_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
