import sys, pandas as pd, numpy as np
sys.path.insert(0, "/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/verify_adversarial")
from a2 import strat, boot, ev0, f, S
m = pd.Series(False, index=ev0.index)
for s, e in S.CRASH_WINDOWS: m |= (ev0.date >= s) & (ev0.date <= e)
ev0["crash"] = m
for h in (False, True):
    e = ev0[(ev0.holdout==h) & ev0.crash]
    print("holdout" if h else "disc", "IN crash n=", len(e), e.groupby("k").x5.agg(["size","median"]).round(4).to_dict("index"))
    ev = ev0[(ev0.holdout==h) & ev0.crash]; ev["S"]=ev.stratum
    dm, dt = strat(ev,"x5"); print("   in-crash HL", f(dm[0]), " v8 share", round(ev.v8.mean(),3), " k>=3 share", round((ev.k>=3).mean(),3))
    ev = ev0[(ev0.holdout==h) & ~ev0.crash]
    for clus in ("week","month"):
        cm, ct, _ = boot(ev, "x5", clus); print("   ex-crash", clus, f"[{f(cm[0])},{f(cm[1])}]")
# share of k>=3 events in crash windows vs k<=1
print("crash share by k:", ev0.groupby("k").crash.mean().round(3).to_dict())
# ffill: drop events with zero-return days in fwd or back
for h in (False, True):
    ev = ev0[(ev0.holdout==h) & (ev0.zero_fwd==0) & (ev0.zero_back==0)]
    dm, dt = strat(ev,"x5"); cm, ct, _ = boot(ev,"x5","week")
    print("no-flat-days", "hold" if h else "disc", len(ev), "HL", f(dm[0]), f"[{f(cm[0])},{f(cm[1])}]", "HM", f(dt[0]), f"[{f(ct[0])},{f(ct[1])}]")
# no-entry by k
print("no_entry by k:", ev0.groupby("k").no_entry.mean().round(3).to_dict())
# lower median vs pandas median, point stat
ev = ev0[~ev0.holdout]
lo, hi = ev.k<=1, ev.k>=3
parts=[];W=[]
for s in (0,1,2):
    a=ev[(ev.stratum==s)&lo].x5; b=ev[(ev.stratum==s)&hi].x5
    parts.append(b.median()-a.median()); W.append(len(a)+len(b))
print("HL with pandas median:", f(np.average(parts, weights=W)), " per-stratum:", [f(p) for p in parts], W)
# weekly correlation between arms of (mean x5 k>=3 - mean x5 k<=1)
g = ev0.groupby(["holdout","week"]).apply(lambda d: d[d.k>=3].x5.median()-d[d.k<=1].x5.median()).unstack(0).dropna()
print("weekly HL corr disc vs hold:", round(g.corr().iloc[0,1],3), "n weeks", len(g))
g2 = ev0.groupby(["holdout","week"]).apply(lambda d: (d[d.k>=3].x5>=.1).mean()-(d[d.k<=1].x5>=.1).mean()).unstack(0).dropna()
print("weekly HM corr:", round(g2.corr().iloc[0,1],3))
# base-rate: same week, share of week-level variation: k>=3 share by week vs week median x5
wk = ev0.groupby("week").agg(k3=("k", lambda k:(k>=3).mean()), med=("x5","median"), n=("x5","size"))
print("corr(week k>=3 share, week median x5):", round(wk[["k3","med"]].corr().iloc[0,1],3))
