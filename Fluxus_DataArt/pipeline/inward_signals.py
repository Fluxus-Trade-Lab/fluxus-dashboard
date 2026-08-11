#!/usr/bin/env python3
"""向内层信号:节奏(爆发/沉默)、连败后的手、sizing 纪律随时间的波动。"""
import csv, datetime as dt, statistics
from pathlib import Path
from collections import defaultdict

SRC = Path(__file__).parents[1] / 'sources/portfolio_2026-07-26.csv'
lines = list(csv.reader(open(SRC)))
for i, l in enumerate(lines):
    if l and l[0] == 'Ticker':
        header, start = l, i + 1
        break
recs = [dict(zip(header, l)) for l in lines[start:] if l and l[0]]

def dd(s):
    if not s:
        return None
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).date() if 'T' in s else dt.date.fromisoformat(s)

trades = []
for x in recs:
    if x['Closed'] != 'YES':
        continue
    e = float(x['Entry Price']); q = float(x['Original Qty'])
    stop = float(x['Initial Stop'] or x['Stop Price'])
    sgn = 1 if x['Direction'] == 'long' else -1
    pnl, last = 0.0, None
    for i in (1, 2, 3):
        if x.get(f'Trim{i} Date'):
            pnl += sgn * (float(x[f'Trim{i} Price']) - e) * float(x[f'Trim{i} Qty'])
            last = dd(x[f'Trim{i} Date'])
    trades.append(dict(t=x['Ticker'], entry=dd(x['Entry Date']), exit=last,
                       pnl=pnl, risk=abs(e - stop) * q))

# ---- equity at each entry (realized, by exit date) ----
by_exit = sorted(trades, key=lambda z: z['exit'])
for t in trades:
    t['equity_at_entry'] = 1_000_000 + sum(x['pnl'] for x in by_exit if x['exit'] < t['entry'])
    t['risk_pct'] = t['risk'] / t['equity_at_entry'] * 100

# 1) sizing discipline over time: monthly median & CV of risk%
bym = defaultdict(list)
for t in trades:
    bym[t['entry'].strftime('%Y-%m')].append(t['risk_pct'])
print('sizing 纪律 (risk % of equity at entry):')
print(f"{'month':9}{'n':>4}{'median%':>9}{'p90%':>7}{'CV':>6}")
for m in sorted(bym):
    v = sorted(bym[m])
    cv = statistics.stdev(v) / statistics.mean(v) if len(v) > 2 else 0
    print(f"{m:9}{len(v):>4}{statistics.median(v):>9.2f}{v[int(len(v)*0.9)]:>7.2f}{cv:>6.2f}")

# 2) rhythm: bursts and silences (entry dates)
by_day = defaultdict(int)
for t in trades:
    by_day[t['entry']] += 1
days = sorted(by_day)
bursts = [(d, n) for d, n in sorted(by_day.items()) if n >= 5]
print('\n爆发日 (>=5 entries):', [(d.isoformat(), n) for d, n in bursts])
# silences: gaps between consecutive entry dates >= 4 calendar days
sil = []
for a, b in zip(days, days[1:]):
    gap = (b - a).days
    if gap >= 4:
        sil.append((a.isoformat(), b.isoformat(), gap))
print('沉默期 (>=4 天无开仓):', sil)

# 3) the hand after losing: after each day with >=2 net losing closes,
#    compare next-entry-day size & count vs overall baseline
day_pnl = defaultdict(float)
day_losses = defaultdict(int)
for t in trades:
    day_pnl[t['exit']] += t['pnl']
    if t['pnl'] < 0:
        day_losses[t['exit']] += 1
bad_days = {d for d in day_pnl if day_pnl[d] < 0 and day_losses[d] >= 2}
base_risk = statistics.median(t['risk_pct'] for t in trades)
after, notafter = [], []
for t in trades:
    prev = [d for d in bad_days if 0 < (t['entry'] - d).days <= 2]
    (after if prev else notafter).append(t)
def stat(ts, label):
    wins = [x['pnl'] for x in ts if x['pnl'] > 0]
    print(f"{label}: n={len(ts)}, 种子中位={statistics.median(x['risk_pct'] for x in ts):.2f}%, "
          f"win%={100*len(wins)/len(ts):.0f}, netP&L=${sum(x['pnl'] for x in ts):,.0f}, "
          f"expR={statistics.mean([x['pnl']/x['risk'] for x in ts if x['risk']>0]):.2f}")
print('\n坏日子之后 48h 内种下的 vs 其他:')
stat(after, '  连亏日后 48h')
stat(notafter, '  平常')
