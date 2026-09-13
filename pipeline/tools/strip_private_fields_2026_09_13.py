"""One-off: strip share counts and dollar amounts from already-published output.

Andy 2026-09-13, verbatim: 「管线只做R 和%, 不写股数和美元」

The writers were fixed in the same branch; this rewrites what they had already
put on main, WITHOUT refetching anything (a refetch needs the Sheet
credentials and would also change every other field). Each file is loaded,
only the private fields are replaced, and it is written back with the exact
json.dumps settings that reproduce its original bytes -- so every other byte
is unchanged. A file whose original bytes cannot be reproduced is refused.

Replacements (same formulas as the fixed writers, which the checks below
compare against):
  trades/<id>.json   trade.original_qty/current_qty -> remaining_pct
                     trade.r_dollars                -> r_pct_of_entry
                     trade.realized_pl              -> dropped (realized_R exists)
                     trade.trims[].qty              -> pct_of_position
                     narrative "(qty N)" dropped, "= $7,713)" -> "= 7.7% of entry)"
  performance.json   monthly[].pnl -> pct (% of the review's starting capital;
                     needs the local, gitignored review file for the capital)
  h1_2026_stats.json h1_report.public_h1_stats
  portfolio_backtest.json  pyramid_campaigns[].layer_entries[].qty -> size_pct_of_first

Run:
    python -m pipeline.tools.strip_private_fields_2026_09_13 \
        --review /path/to/data/portfolio/reviews/h1_2026.json
Prints counts and percentages only, never the removed values.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from pipeline.portfolio import trade_postmortem as tp
from pipeline.portfolio.h1_report import public_h1_stats
from pipeline.portfolio.pyramid_analyzer import layer_size_pct_of_first
from pipeline.portfolio.trade_parser import Trade, TrimEvent

OUT = Path('data/output')


def _dump_like(raw: str, obj) -> str:
    """Serialise `obj` with whichever settings reproduce `raw` byte for byte."""
    original = json.loads(raw)
    for kw in (dict(indent=2), dict(indent=2, ensure_ascii=False)):
        for tail in ('', '\n'):
            if json.dumps(original, **kw) + tail == raw:
                return json.dumps(obj, **kw) + tail
    raise SystemExit('refusing: cannot reproduce original bytes')


_QTY = re.compile(r' \(qty \d+\)')
_R_DOLLARS = re.compile(r'\(1R = \$([0-9.]+)/sh = \$[0-9,]+\)\.')


def _trade_from_json(old: dict) -> Trade:
    return Trade(
        ticker=old['ticker'], direction=old['direction'], sector=old['sector'],
        entry_date=date.fromisoformat(old['entry_date']),
        entry_price=old['entry_price'], original_qty=old['original_qty'],
        current_qty=old['current_qty'], stop_price=old['stop_price'],
        initial_stop=old.get('initial_stop'), closed=old['closed'],
        trims=tuple(TrimEvent(date=date.fromisoformat(t['date']), price=t['price'],
                              qty=t['qty'], type=t['type']) for t in old['trims']),
    )


def clean_trades(stats: dict) -> None:
    for f in sorted((OUT / 'trades').glob('*.json')):
        if f.name == '_index.json':
            continue
        raw = f.read_text()
        rec = json.loads(raw)
        old = rec['trade']
        if 'original_qty' not in old:
            stats['trades_already_clean'] += 1
            continue
        trade = _trade_from_json(old)
        new = tp._trade_to_dict(trade)
        # Keep the STORED value for every field that survives: recomputing
        # could only ever change bytes this cleanup has no business changing.
        # `trims` is not a surviving field as a whole -- its qty is the thing
        # being removed -- so it is rebuilt from the stored entries instead.
        for k in new:
            if k == 'trims' or k not in old:
                continue
            if new[k] != old[k]:
                stats[f'kept_stored_{k}_differs_from_recompute'] += 1
                new[k] = old[k]
        new['trims'] = [
            {'date': t['date'], 'price': t['price'],
             'pct_of_position': tp.pct_of_position(t['qty'], old['original_qty']),
             'type': t['type']}
            for t in old['trims']
        ]
        if new['trims'] != tp._trade_to_dict(trade)['trims']:
            stats['trims_differ_from_fixed_writer'] += 1
        rec['trade'] = new

        narr = rec.get('narrative') or ''
        narr2 = _QTY.sub('', narr, count=1)
        if old.get('initial_stop') is not None:
            pct = tp.r_pct_of_entry(old['entry_price'], old['initial_stop'])
            narr2 = _R_DOLLARS.sub(lambda m: f'(1R = ${m.group(1)}/sh = {pct:.1f}% of entry).',
                                   narr2, count=1)
        rec['narrative'] = narr2
        # Positive check against the fixed writer: the regex edit and a fresh
        # render from the same inputs should agree.
        fresh = tp._generate_narrative(trade, rec['entry_snapshot'], rec['setup_type'],
                                       rec['path_analytics'], rec['lesson'])
        stats['narrative_matches_fixed_writer' if fresh == narr2
              else 'narrative_differs_from_fixed_writer'] += 1
        f.write_text(_dump_like(raw, rec))
        stats['trades_cleaned'] += 1


def clean_performance(review_path: Path, stats: dict) -> None:
    f = OUT / 'performance.json'
    raw = f.read_text()
    doc = json.loads(raw)
    review = json.loads(review_path.read_text())
    cap = review['overall']['capital']
    rows = []
    for m in doc['monthly']:
        if 'pnl' not in m:
            rows.append(m)
            continue
        rows.append({k if k != 'pnl' else 'pct': (v if k != 'pnl' else round(v / cap * 100, 2))
                     for k, v in m.items()})
    doc['monthly'] = rows
    total = round(sum(r['pct'] for r in rows), 2)
    stats['performance_monthly_pct_sum'] = total
    stats['review_return_pct'] = round(review['overall']['return_pct'], 2)
    f.write_text(_dump_like(raw, doc))


def clean_h1(stats: dict) -> None:
    f = OUT / 'h1_2026_stats.json'
    raw = f.read_text()
    doc = json.loads(raw)
    if 'starting_capital' not in doc.get('meta', {}):
        stats['h1_already_clean'] = True
        return
    f.write_text(_dump_like(raw, public_h1_stats(doc)))
    stats['h1_cleaned'] = True


def clean_backtest(stats: dict) -> None:
    f = OUT / 'portfolio_backtest.json'
    raw = f.read_text()
    doc = json.loads(raw)
    for c in doc.get('pyramid_campaigns', []):
        layers = c.get('layer_entries', [])
        if not layers or 'qty' not in layers[0]:
            continue
        first = layers[0]['qty']
        c['layer_entries'] = [
            {k if k != 'qty' else 'size_pct_of_first':
             (v if k != 'qty' else layer_size_pct_of_first(v, first))
             for k, v in l.items()}
            for l in layers
        ]
        stats['pyramid_campaigns_cleaned'] += 1
    f.write_text(_dump_like(raw, doc))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--review', type=Path, required=True,
                   help='data/portfolio/reviews/h1_2026.json (gitignored, local only)')
    args = p.parse_args(argv)
    from collections import Counter
    stats: Counter = Counter()
    clean_trades(stats)
    clean_performance(args.review, stats)
    clean_h1(stats)
    clean_backtest(stats)
    for k, v in sorted(stats.items()):
        print(f'{k}: {v}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
