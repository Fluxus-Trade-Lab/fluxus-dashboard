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
import statistics
import sys
import zlib
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
                      horizons: Sequence[int] = HORIZONS,
                      cache: Dict[Tuple[str, str], Any] | None = None
                      ) -> Tuple[List[Dict[str, Any]], int]:
    """Measure each instance; return (outcomes, count lost to missing data).

    `cache` memoizes on (ticker, signal_date); the baseline redraws hit the
    same points many times, and the measurement is deterministic.
    """
    outcomes: List[Dict[str, Any]] = []
    lost = 0
    for inst in instances:
        key = (inst['ticker'], inst['signal_date'])
        if cache is not None and key in cache:
            out = cache[key]
        else:
            bars = panel.get(inst['ticker'])
            out = (None if bars is None else
                   measure_outcome(bars, spy, inst['signal_date'],
                                   horizons=horizons))
            if out is not None:
                out = {**out, 'ticker': inst['ticker'],
                       'signal_date': inst['signal_date']}
            if cache is not None:
                cache[key] = out
        if out is None:
            lost += 1
            continue
        outcomes.append(out)
    return outcomes, lost


def sequence_seed(base_seed: int, label: str) -> int:
    """A per-sequence seed, deterministic in (base_seed, label).

    Sharing one seed across sequences makes the n=110 baseline a strict
    prefix of the n=412 one: effectively a single sample whose sampling
    error is a common shift across the whole table.
    """
    return (base_seed ^ zlib.crc32(label.encode())) & 0xFFFFFFFF


def average_baselines(draws: List[Dict[str, Any]],
                      horizons: Sequence[int] = HORIZONS) -> Dict[str, Any]:
    """Mean of each baseline statistic across independent redraws.

    Also records `baseline_sd_median_excess_{h}` — the sample spread of the
    per-draw medians — so the reader can weigh the comparison's own noise
    against the net edge it is being asked to believe.
    """
    out: Dict[str, Any] = {}

    def _mean(key: str) -> Any:
        vals = [d[key] for d in draws
                if d.get(key) is not None and not pd.isna(d.get(key))]
        return round(statistics.fmean(vals), 6) if vals else None

    for key in ('n', 'lost'):
        out[key] = _mean(key)
    for h in horizons:
        for template in _NET_KEYS:
            key = template.format(h=h)
            out[key] = _mean(key)
        med = [d[f'median_excess_{h}'] for d in draws
               if d.get(f'median_excess_{h}') is not None]
        out[f'baseline_sd_median_excess_{h}'] = (
            None if not med else
            round(statistics.stdev(med), 6) if len(med) > 1 else 0.0)
    return out


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
        f"- **Multiple comparisons.** {meta.get('hypotheses', len(rows))} "
        "sequences were tested against this one sample; some will look "
        "excellent by chance. Every number in the ranking table is reported "
        "**net of a random-entry baseline** drawn from *the same sequence's "
        "tickers* and the same dates — so it measures timing, not which "
        f"companies keep clearing screeners. The baseline is the mean of "
        f"{meta.get('baseline_draws', '?')} independent redraws; its own "
        "spread is in `baseline_sd_median_excess` — where that is comparable "
        "to the net edge, the net edge is noise.\n"
        "- **The stability filter is weak.** Under pure noise two half-samples "
        "agree in sign about **50%** of the time. "
        + (f"Observed: **{meta['pass_rate'] * 100:.0f}%** of the "
           f"{meta['powered']} adequately-powered sequences passed "
           f"({meta['stable']} of {meta['powered']}). "
           if meta.get('pass_rate') is not None else "")
        + "A pass rate near 50% means the filter is not discriminating — it is "
        "removing coin flips, not identifying edge.\n"
        "- **Instances are not independent.** Sequences fire in clusters: many "
        "names confirm on the same session, and those outcomes share one day "
        "of market. The `distinct_signal_dates` column is a much better guide "
        "to effective sample size than `n`.\n"
        f"- **Survivorship.** Prices were fetched today, so delisted and renamed "
        f"tickers are missing ({meta['coverage_missing']} of "
        f"{meta['tickers']} tickers). Those failures skew toward losers, so the "
        "surviving numbers are, if anything, flattering. Per-sequence "
        "instances lost to missing prices are in the `lost` column.\n"
        + _recency_bullet(meta)
        + f"- **Window.** {meta['window']} archive sessions. The archive omits "
        "non-session and untrustworthy days, so an N-session gap spans more "
        "calendar time than N days.\n"
        f"- Ranked on `{rank_key}`; `--min-n {meta['min_n']}`, `--seed "
        f"{meta['seed']}`.\n"
    )

    ranked = [r for r in rows if not r['under_powered'] and not r['unstable']]
    ranked.sort(key=lambda r: (r.get(rank_key) is None, -(r.get(rank_key) or 0)))
    positive = [r for r in ranked if (r.get(rank_key) or 0) > 0]
    negative = [r for r in ranked if (r.get(rank_key) or 0) <= 0]

    lines.append("## Survived the guards (stability + power — NOT a "
                 "profitability test)\n")
    lines.append(
        "Passing here means a sequence had enough instances and did not flip "
        "sign between the two half-samples. It says nothing about whether the "
        "sequence made money. Sequences below are split by whether their net "
        "edge is actually positive.\n")
    if not ranked:
        lines.append(
            "**No sequence cleared the bar.** Every candidate was either "
            "under-powered or unstable across the two half-samples. That is a "
            "real result, not a tooling failure — on this much data, in this one "
            "regime, nothing here is distinguishable from random entry.\n")
    else:
        lines.append(f"### Positive net edge ({len(positive)})\n")
        lines.append(_ranked_table(positive, rank_key)
                     or "_None. Nothing that survived the guards beat its own "
                        "random-entry baseline._\n")
        lines.append(f"### Negative net edge ({len(negative)}) — stable losers\n")
        lines.append(_ranked_table(negative, rank_key)
                     or "_None._\n")

    unstable = [r for r in rows if r['unstable'] and not r['under_powered']]
    lines.append("## Excluded — unstable across half-samples\n")
    lines.append(_simple_list(unstable, rank_key) or "_None._\n")

    weak = [r for r in rows if r['under_powered']]
    lines.append(f"## Excluded — fewer than {meta['min_n']} instances\n")
    lines.append(_simple_list(weak, rank_key) or "_None._\n")

    return "\n".join(lines)


def _recency_bullet(meta: Dict[str, Any]) -> str:
    """Disclose the truncated tail and the asymmetry it puts in the split."""
    if not meta.get('measurable_last'):
        return ''
    h1m, h1 = meta['first_half_measurable'], meta['first_half_sessions']
    h2m, h2 = meta['second_half_measurable'], meta['second_half_sessions']
    tail = meta['sessions'] - meta['measurable_total']
    direction = (
        "the second half is the thinner one, so the stability check leans on "
        "less data exactly where the market is most recent"
        if h2m < h1m else
        "the first half is the thinner one")
    return (
        f"- **The tail is unmeasurable.** The price panel ends with the "
        f"archive, and the longest horizon needs "
        f"{max(meta.get('horizons', (21,)))} forward sessions, so the last "
        f"signal date that can be measured at all is "
        f"**{meta['measurable_last']}** — {tail} of {meta['sessions']} archive "
        f"sessions contribute zero instances. This makes the half-sample split "
        f"**asymmetric**: {h1m}/{h1} measurable sessions in the first half vs "
        f"{h2m}/{h2} in the second. That is not a 50/50 split, and "
        f"{direction}.\n")


def _ranked_table(rows: List[Dict[str, Any]], rank_key: str) -> str:
    """The ranking table. Every statistic here is NET of the baseline."""
    if not rows:
        return ''
    h = RANK_HORIZON
    out = [f"| Sequence | n | distinct dates | lost | net median excess ({h}d) "
           f"| baseline sd | net median MFE (R) | net median MAE (R) "
           f"| net win rate |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        out.append(
            f"| {r['sequence']} | {r['n']} "
            f"| {r.get('distinct_signal_dates', '—')} | {r['lost']} "
            f"| {_fmt_pct(r.get(rank_key))} "
            f"| {_fmt_pct(r.get(f'baseline_sd_median_excess_{h}'))} "
            f"| {_fmt_net(r.get(f'net_median_mfe_r_{h}'), r.get(f'median_mfe_r_{h}'))} "
            f"| {_fmt_net(r.get(f'net_median_mae_r_{h}'), r.get(f'median_mae_r_{h}'))} "
            f"| {_fmt_net_pct(r.get(f'net_win_rate_{h}'), r.get(f'win_rate_{h}'))} |")
    return "\n".join(out) + "\n"


def _fmt_net(net: Any, raw: Any) -> str:
    """Net value with the raw one in parentheses, so both claims are honest."""
    if net is None:
        return '—' if raw is None else f"— (raw {raw:.2f})"
    return f"{net:+.2f}" + ('' if raw is None else f" (raw {raw:.2f})")


def _fmt_net_pct(net: Any, raw: Any) -> str:
    if net is None:
        return '—' if raw is None else f"— (raw {raw * 100:.0f}%)"
    return (f"{net * 100:+.0f}pp"
            + ('' if raw is None else f" (raw {raw * 100:.0f}%)"))


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


def measurable_dates(archive_dates: Sequence[str], spy: pd.DataFrame,
                     max_horizon: int) -> List[str]:
    """Archive sessions with enough forward bars to be measurable at all.

    Entry is the session AFTER the signal, and the longest horizon needs
    `max_horizon` bars from there. The tail of the archive therefore
    contributes nothing, silently, unless it is disclosed.
    """
    cal = list(spy.index.strftime('%Y-%m-%d'))
    pos = {d: i for i, d in enumerate(cal)}
    limit = len(cal) - 1 - max_horizon
    return [d for d in sorted(set(archive_dates))
            if d in pos and pos[d] <= limit]


# ── CLI (I/O; the pieces above are pure) ─────────────────────────────

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--window', type=int, default=10)
    parser.add_argument('--min-n', type=int, default=MIN_N)
    parser.add_argument('--horizons', default='5,10,21')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--baseline-draws', type=int, default=20,
                        help='independent baseline redraws averaged per sequence')
    parser.add_argument('--triples', action='store_true')
    parser.add_argument('--events', default=str(_DEFAULT_EVENTS))
    parser.add_argument('--panel', default=str(_DEFAULT_PANEL))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    horizons = tuple(int(h) for h in args.horizons.split(','))
    if RANK_HORIZON not in horizons:
        parser.error(
            f"--horizons must include the ranking horizon {RANK_HORIZON} "
            f"(got {args.horizons}); every sequence would otherwise be "
            f"silently unranked.")
    if args.baseline_draws < 1:
        parser.error("--baseline-draws must be at least 1")
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

    cache: Dict[Tuple[str, str], Any] = {}
    rows: List[Dict[str, Any]] = []
    for label, legs in candidates:
        instances = _find(events, legs)
        outcomes, lost = measure_instances(instances, panel, spy, horizons, cache)
        seq_stats = summarize(outcomes, horizons=horizons, lost=lost)
        if seq_stats['n'] == 0:
            continue

        # F1: the baseline must be drawn from THIS sequence's tickers. Drawing
        # from all 3,872 archive names measures which companies keep clearing
        # screeners, not whether the timing signal is worth anything.
        seq_tickers = sorted({str(i['ticker']) for i in instances})
        seed = sequence_seed(args.seed, label)
        draws = []
        for k in range(args.baseline_draws):
            base_inst = random_instances(events, n=seq_stats['n'],
                                         seed=(seed + k * 7919) & 0xFFFFFFFF,
                                         rng_tickers=seq_tickers)
            base_out, base_lost = measure_instances(base_inst, panel, spy,
                                                    horizons, cache)
            draws.append(summarize(base_out, horizons=horizons, lost=base_lost))
        base_stats = average_baselines(draws, horizons=horizons)

        half_stats = []
        for half in (first_half, second_half):
            h_out, h_lost = measure_instances(_find(half, legs), panel, spy,
                                              horizons, cache)
            half_stats.append(summarize(h_out, horizons=horizons, lost=h_lost))

        measured = sorted(o['signal_date'] for o in outcomes)
        row: Dict[str, Any] = {'sequence': label, **seq_stats}
        row.update(net_of_baseline(seq_stats, base_stats, horizons))
        for h in horizons:
            key = f'baseline_sd_median_excess_{h}'
            row[key] = base_stats.get(key)
        row['distinct_signal_dates'] = len({o['signal_date'] for o in outcomes})
        row['measured_first'] = measured[0] if measured else None
        row['measured_last'] = measured[-1] if measured else None
        row['under_powered'] = seq_stats['n'] < args.min_n
        row['unstable'] = is_unstable(half_stats[0], half_stats[1],
                                      f'median_excess_{RANK_HORIZON}')
        rows.append(row)

    coverage = len(set(events['ticker'].astype(str)) - set(panel))
    archive_dates = sorted(set(events['date'].astype(str)))
    meas = measurable_dates(archive_dates, spy, max(horizons))
    meas_set = set(meas)
    first_dates = [d for d in archive_dates if d <= mid]
    second_dates = [d for d in archive_dates if d > mid]
    powered = [r for r in rows if not r['under_powered']]
    stable = [r for r in powered if not r['unstable']]
    meta = {'as_of': last, 'window': args.window, 'seed': args.seed,
            'min_n': args.min_n, 'sessions': events['date'].nunique(),
            'tickers': events['ticker'].nunique(), 'coverage_missing': coverage,
            'horizons': horizons, 'baseline_draws': args.baseline_draws,
            'hypotheses': len(rows), 'candidates': len(candidates),
            'powered': len(powered), 'stable': len(stable),
            'pass_rate': (len(stable) / len(powered)) if powered else None,
            'measurable_last': meas[-1] if meas else None,
            'measurable_total': len(meas),
            'first_half_sessions': len(first_dates),
            'first_half_measurable': sum(1 for d in first_dates if d in meas_set),
            'second_half_sessions': len(second_dates),
            'second_half_measurable': sum(1 for d in second_dates if d in meas_set)}

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

    rank_key = RANK_KEY_TEMPLATE.format(h=RANK_HORIZON)
    n_pos = sum(1 for r in stable if (r.get(rank_key) or 0) > 0)
    print(f"\n{len(rows)} sequences evaluated; {len(stable)} passed the "
          f"stability and power filters; {n_pos} of those have positive net edge")
    print(f"Last measurable signal date: {meta['measurable_last']} "
          f"({meta['measurable_total']}/{meta['sessions']} archive sessions "
          f"measurable)")
    print(f"Report: {md_path}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
