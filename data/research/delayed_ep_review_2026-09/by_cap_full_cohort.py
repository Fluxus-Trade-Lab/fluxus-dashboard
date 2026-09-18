"""Excess vs the FULL clean same-day cohort, reported by market-cap group (2026-09-19).

Why this exists: cohort_read_2026-09-19.py re-centres the cohort INSIDE each cap
group. An adversarial verifier showed that splitting the benchmark moves the
numbers by itself: breaking +5d on >=$1B reads -0.05% against a >=$1B-only
cohort but +1.25% against the full cohort -- the small caps had lifted the
group mean, not depressed the big names. Reading "is the edge in the small
caps?" needs ONE benchmark, split only at report time. This is that read.

  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/by_cap_full_cohort.py
"""
import csv, datetime as dt, sys
import numpy as np
from pipeline.marketcal import is_trading_day, last_completed_session
sys.path.insert(0, 'data/research/breadth_universe_break_2026-09-18')
from population_reach import snapshots

H = 'data/research/delayed_ep_review_2026-09/'
bars = {}
for r in csv.DictReader(open(H + 'bars_2026-09-19.csv')):
    bars.setdefault(r['ticker'], {})[r['date']] = float(r['close'])
full = list(csv.DictReader(open('data/history/delayed_ep_log.csv')))
clean = [r for r in full if r['ep_date'] >= '2026-08-11' and r['as_of'] != '2026-09-02']
sn = snapshots(since='2026-08-01'); sd = sorted(sn)
for r in clean:
    e = [d for d in sd if d <= r['as_of']]
    r['cap'] = sn[e[-1]].get(r['ticker'])
g, d = [], dt.date(2026, 8, 13)
while d <= last_completed_session():
    if is_trading_day(d):
        g.append(str(d))
    d += dt.timedelta(1)
pos = {x: i for i, x in enumerate(g)}


def fwd(t, day, h):
    i = pos.get(day)
    if i is None or i + h >= len(g):
        return None
    s = bars.get(t, {})
    return s[g[i + h]] / s[day] - 1 if day in s and g[i + h] in s else None


for h in (3, 5, 10):
    raw = {}
    for r in clean:
        v = fwd(r['ticker'], r['as_of'], h)
        if v is not None:
            raw.setdefault(r['as_of'], []).append((r, v))
    coh = {d: np.mean([v for _, v in x]) for d, x in raw.items()}
    for st in ('breaking', 'basing', 'drifting', 'failed'):
        for nm, f in (('all', lambda c: True), ('>=1B', lambda c: c >= 1e9), ('<1B', lambda c: c < 1e9)):
            sel = [(r, v - coh[d]) for d, x in raw.items() for r, v in x if r['stage'] == st and f(r['cap'])]
            if not sel:
                continue
            print(f"+{h:<2} {st:>9} {nm:>5}  med {np.median([x for _, x in sel])*100:+6.2f}%  "
                  f"n={len(sel):<4} tickers={len({r['ticker'] for r, _ in sel})}")
