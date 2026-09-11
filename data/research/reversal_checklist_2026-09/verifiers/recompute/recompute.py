import hashlib, json, sys
import numpy as np, pandas as pd

P = pd.read_pickle('/Users/taolezhu/Documents/AI-Trading-System/.cache/stock_panel.pkl')
C = P.values.astype(float)
dates = P.index
cols = list(P.columns)
spy = P['SPY'].values
stk_idx = [i for i, c in enumerate(cols) if c != 'SPY']
T, N = C.shape

def shift(a, k):  # value at t-k
    out = np.full_like(a, np.nan)
    if k > 0: out[k:] = a[:-k]
    else: out[:k] = a[-k:]
    return out

Cm1, Cm2, Cm3, Cm5, Cm10 = (shift(C, k) for k in (1, 2, 3, 5, 10))
Cp5 = shift(C, -5)
with np.errstate(all='ignore'):
    r5 = C / Cm5 - 1
    L3 = np.log(C / Cm3); L10 = np.log(C / Cm10)
    V1 = (L10 < 0) & (L3 / L10 >= 0.6)
    V2 = (C < Cm1) & (Cm1 < Cm2) & (Cm2 < Cm3)
    df = pd.DataFrame(C)
    sma20 = df.rolling(20, min_periods=20).mean().values
    sd20 = df.rolling(20, min_periods=20).std(ddof=0).values
    up, lo = sma20 + 2 * sd20, sma20 - 2 * sd20
    pb = (C - lo) / (up - lo)
    V3 = pb < 0
    sma50 = df.rolling(50, min_periods=50).mean().values
    S = C[:, stk_idx]; M = sma50[:, stk_idx]
    valid = ~np.isnan(S) & ~np.isnan(M)
    above = (S > M) & valid
    pct = above.sum(1) / np.where(valid.sum(1) > 0, valid.sum(1), np.nan)
    V8 = (pct < 0.30)
    spy5 = shift(spy[:, None], -5)[:, 0] / spy - 1
    x5 = Cp5 / C - 1 - spy5[:, None]
    ret = C / Cm1 - 1
    vol20 = pd.DataFrame(ret).rolling(20, min_periods=20).std().values  # ddof=1
    vol20_m5 = shift(vol20, 5)

base = (r5 <= -0.10) & (C >= 5)
rows = []
for j in stk_idx:
    tk = cols[j]
    idx = np.where(base[:, j])[0]
    last = -10**9
    for t in idx:
        if t - last >= 10:
            last = t
            rows.append((tk, j, t))
print('base after dedup (before outcome filter):', len(rows))
ev = pd.DataFrame(rows, columns=['tk', 'j', 't'])
j, t = ev.j.values, ev.t.values
ev['r5'] = r5[t, j]; ev['x5'] = x5[t, j]
ev['V1'] = V1[t, j]; ev['V2'] = V2[t, j]; ev['V3'] = V3[t, j]; ev['V8'] = V8[t]
ev['k'] = ev[['V1', 'V2', 'V3', 'V8']].sum(1)
ev['vol'] = vol20_m5[t, j]
ev['date'] = dates[t]
iso = pd.DatetimeIndex(ev.date).isocalendar()
ev['wk'] = (iso.year.astype(int) * 100 + iso.week.astype(int)).values
ev = ev[~np.isnan(ev.x5)].reset_index(drop=True)
ev['hold'] = [int(hashlib.md5((tk + 'rev0912').encode()).hexdigest(), 16) % 10 < 3 for tk in ev.tk]
ev['strat'] = np.where(ev.r5 > -0.15, 0, np.where(ev.r5 > -0.25, 1, 2))
print('total events:', len(ev), 'discovery:', (~ev.hold).sum(), 'holdout:', ev.hold.sum())
D = ev[~ev.hold].reset_index(drop=True)
print('discovery tickers:', D.tk.nunique(), 'holdout tickers:', ev[ev.hold].tk.nunique())

def lmed(v):
    v = np.sort(v); return v[int(np.ceil(len(v) / 2)) - 1]

print('\nk   n   median  P>=+10  P<=-10  mean  vol20med(t-5)  vol_ddof1')
for k in range(5):
    s = D[D.k == k]
    print(k, len(s), f'{np.median(s.x5):.4%}', f'{(s.x5>=0.10).mean():.4f}', f'{(s.x5<=-0.10).mean():.4f}', f'{s.x5.mean():.4%}', f'{np.nanmedian(s.vol):.4f}')
print('V prevalence:', D[['V1','V2','V3','V8']].mean().round(4).to_dict())
print('k by strat:\n', pd.crosstab(D.strat, D.k))

def stat(x, k, st, which):
    num = den = 0.0
    for s in (0, 1, 2):
        m = st == s
        hi = x[m & (k >= 3)]; loo = x[m & (k <= 1)]
        if len(hi) == 0 or len(loo) == 0: continue
        if which == 'med': d = lmed(hi) - lmed(loo)
        elif which == 'npmed': d = np.median(hi) - np.median(loo)
        else: d = (hi >= 0.10).mean() - (loo >= 0.10).mean()
        w = len(hi) + len(loo); num += w * d; den += w
    return num / den

x, k, st = D.x5.values, D.k.values, D.strat.values
print('\nH-L (lower median):', stat(x, k, st, 'med'))
print('H-L (numpy median):', stat(x, k, st, 'npmed'))
print('H-M tail:', stat(x, k, st, 'tail'))
for s in (0,1,2):
    m=st==s; hi=x[m&(k>=3)]; lo_=x[m&(k<=1)]
    print(' strat',s,'nhi',len(hi),'nlo',len(lo_),'dmed',lmed(hi)-lmed(lo_),'dtail',(hi>=.1).mean()-(lo_>=.1).mean())

# week-cluster bootstrap
rng = np.random.default_rng(912)
wks = D.wk.values; uw, inv = np.unique(wks, return_inverse=True)
groups = [np.where(inv == g)[0] for g in range(len(uw))]
B = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
bm, bt = [], []
for b in range(B):
    pick = rng.integers(0, len(uw), len(uw))
    ii = np.concatenate([groups[g] for g in pick])
    bm.append(stat(x[ii], k[ii], st[ii], 'med')); bt.append(stat(x[ii], k[ii], st[ii], 'tail'))
print('weeks:', len(uw))
print('H-L CI95:', np.percentile(bm, [2.5, 97.5]))
print('H-M CI95:', np.percentile(bt, [2.5, 97.5]))
