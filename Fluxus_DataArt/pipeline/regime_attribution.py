#!/usr/bin/env python3
"""逐日重放 regime score (Time Machine),把 331 笔按入场日市场状态分桶。
两套 band 都算:DISPLAY(仓位语言)与 ANALYSIS(统计口径,per regime.py 的警告)。
"""
import sys, csv, datetime as dt, statistics
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]  # worktree root
sys.path.insert(0, str(ROOT))
import pandas as pd
from pipeline.screeners.state_board import state_board
from pipeline.screeners.regime import score as regime_score, band_for

arch = pd.read_csv(ROOT / 'data/history/breadth_archive.csv', parse_dates=['date'])
arch = arch.sort_values('date').reset_index(drop=True)

scores = {}
for i in range(len(arch)):
    d = arch.loc[i, 'date'].date()
    if d < dt.date(2025, 12, 1) or d > dt.date(2026, 7, 25):
        continue
    s = regime_score(state_board(arch.iloc[:i + 1]))
    if s and s['score'] is not None:
        scores[d] = s['score']
days = sorted(scores)
print('replayed sessions:', len(days), days[0], '->', days[-1])

def disp_band(p):
    return 'Defence' if p < 12 else 'Caution' if p < 34 else 'Neutral' if p < 56 else 'Constructive' if p < 78 else 'Full'

def ana_band(p):
    return band_for(p)['label']

def latest_session(d):
    c = [x for x in days if x <= d]
    return c[-1] if c else None

lines = list(csv.reader(open(Path(__file__).parents[1] / 'sources/portfolio_2026-07-26.csv')))
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
    risk = abs(e - stop) * q
    trades.append(dict(t=x['Ticker'], entry=dd(x['Entry Date']), exit=last,
                       pnl=pnl, risk=risk, r=pnl / risk if risk > 0 else 0))

for scheme, fn in [('DISPLAY (Defence/Caution/Neutral/Constructive/Full)', disp_band),
                   ('ANALYSIS (Damaged/Mixed/Healthy/Extended)', ana_band)]:
    agg = defaultdict(list)
    for t in trades:
        s = latest_session(t['entry'])
        if s is not None:
            agg[fn(scores[s])].append(t)
    sess = defaultdict(int)
    for d in days:
        sess[fn(scores[d])] += 1
    print('\n==', scheme)
    print(f"{'band':13}{'sessions':>9}{'entries':>8}{'/day':>6}{'medRisk$':>10}{'totRisk$':>11}{'win%':>6}{'payoff':>8}{'expR':>7}{'netP&L':>11}")
    for b in ['Defence', 'Caution', 'Neutral', 'Constructive', 'Full',
              'Damaged', 'Mixed', 'Healthy', 'Extended']:
        if b not in agg and b not in sess:
            continue
        ts = agg.get(b, [])
        n = len(ts)
        if n == 0:
            print(f"{b:13}{sess.get(b,0):>9}{0:>8}")
            continue
        wins = [t['pnl'] for t in ts if t['pnl'] > 0]
        losses = [t['pnl'] for t in ts if t['pnl'] < 0]
        payoff = (statistics.mean(wins) / abs(statistics.mean(losses))) if wins and losses else float('nan')
        print(f"{b:13}{sess.get(b,0):>9}{n:>8}{n/max(sess.get(b,1),1):>6.1f}"
              f"{statistics.median([t['risk'] for t in ts]):>10,.0f}"
              f"{sum(t['risk'] for t in ts):>11,.0f}"
              f"{100*len(wins)/n:>6.0f}{payoff:>8.2f}"
              f"{statistics.mean([t['r'] for t in ts]):>7.2f}"
              f"{sum(t['pnl'] for t in ts):>11,.0f}")

bym = defaultdict(list)
for d in days:
    bym[d.strftime('%Y-%m')].append(scores[d])
print('\nmonthly score mean/min/max:')
for m in sorted(bym):
    print(m, f"{statistics.mean(bym[m]):5.1f}", min(bym[m]), max(bym[m]))

# daily series for the art pipeline
out = Path(__file__).parents[1] / 'sources/regime_daily.csv'
with open(out, 'w') as f:
    f.write('date,score,display_band,analysis_band\n')
    for d in days:
        f.write(f"{d},{scores[d]},{disp_band(scores[d])},{ana_band(scores[d])}\n")
print('wrote', out)
