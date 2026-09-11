import sys, numpy as np, pandas as pd
sys.path.insert(0, "/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/wt-night/data/research/reversal_checklist_2026-09")
import study as S
OUT="/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/verify_adversarial/"
px, spy = S.load_panel()
print(px.shape, px.index[0], px.index[-1])
f = S.features(px, spy)
ev = S.events(px, spy, f)
print(len(ev), ev.holdout.value_counts().to_dict())
col = {c: i for i, c in enumerate(px.columns)}; row = {d: i for i, d in enumerate(px.index)}
ri = np.array([row[d] for d in ev.date]); ci = np.array([col[t] for t in ev.ticker])
P = px.values
ret = px.pct_change(fill_method=None).values
# zero-return days in t+1..t+5 and t-4..t
zf = np.zeros(len(ev), int); zb = np.zeros(len(ev), int)
for o in range(1,6):
    zf += (ret[ri+o, ci] == 0)
for o in range(0,5):
    zb += (ret[ri-o, ci] == 0)
ev["zero_fwd"] = zf; ev["zero_back"] = zb
vol = px.pct_change(fill_method=None).rolling(20).std().shift(5).values
ev["prevol"] = vol[ri, ci]
ev["spy5"] = (spy.shift(-5)/spy - 1).values[ri]
ev["raw5"] = P[ri+5, ci]/P[ri, ci]-1
ev["breadth"] = f["breadth"].values[ri]
ev["ri"]=ri; ev["ci"]=ci
ev.to_pickle(OUT+"ev.pkl")
# panel level zero-return stats: trailing flat stretch at end
last_change = {}
flat_tail = (px.diff().iloc[::-1] == 0).cumprod().sum()
print("tickers with >=20 flat trailing days:", int((flat_tail>=20).sum()))
# fraction of zero-return days overall
r = px.pct_change(fill_method=None)
print("share zero-return ticker-days (non-nan):", float((r==0).sum().sum()/r.notna().sum().sum()))
