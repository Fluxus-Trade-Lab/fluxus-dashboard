import pandas as pd, numpy as np
OUT="/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/verify_adversarial/"
ev = pd.read_pickle(OUT+"ev.pkl")
print("zero_fwd>=1 share:", (ev.zero_fwd>=1).mean(), " >=2:", (ev.zero_fwd>=2).mean(), " ==5:", (ev.zero_fwd==5).mean())
print("zero_back>=1:", (ev.zero_back>=1).mean())
print(ev.groupby("k").apply(lambda g: pd.Series(dict(zf1=(g.zero_fwd>=1).mean(), zf2=(g.zero_fwd>=2).mean(), zb1=(g.zero_back>=1).mean()))))
# does removing zero-fwd>=2 change medians?
for h in (False, True):
    e = ev[ev.holdout==h]
    print("arm holdout" if h else "arm disc", "raw5==0 share", (e.raw5==0).mean())
# check x5 recompute
print("x5 recompute err", np.nanmax(np.abs(ev.raw5-ev.spy5-ev.x5)))
# refractory: events per ticker, and cross-ticker same-week clustering
wk = ev.groupby("week").size()
print("events/week: median", wk.median(), "max", wk.max(), "top5 weeks", wk.sort_values().tail(5).to_dict())
print("share of events in top 20 weeks", wk.sort_values().tail(20).sum()/len(ev))
