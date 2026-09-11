import sys, pandas as pd, numpy as np
sys.path.insert(0, "/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/verify_adversarial")
from a2 import strat, boot, ev0, f, S
for arm, h in (("disc", False), ("hold", True)):
    ev = ev0[(ev0.holdout==h) & ev0.prevol.notna()].copy()
    # vol terciles computed within arm (like posthoc)
    ev["vt"] = pd.qcut(ev.prevol, 3, labels=False)
    ev["vt5"] = pd.qcut(ev.prevol, 5, labels=False)
    ev["S"] = ev.stratum*10 + ev.vt
    for col in ("x5","x5_v"):
        dm, dt = strat(ev, col); cm, ct, _ = boot(ev, col, "week")
        print(f"{arm} {col} depth×vol3  HL {f(dm[0])} [{f(cm[0])},{f(cm[1])}]  HM {f(dt[0])} [{f(ct[0])},{f(ct[1])}]")
    ev["S"] = ev.stratum*10 + ev.vt5
    dm, dt = strat(ev, "x5"); cm, ct, _ = boot(ev, "x5", "week")
    print(f"{arm} x5 depth×vol5  HL {f(dm[0])} [{f(cm[0])},{f(cm[1])}]  HM {f(dt[0])} [{f(ct[0])},{f(ct[1])}]")
    # vol-normalized tail: z = x5/(prevol*sqrt5); threshold chosen so pooled rate ~= 10%
    ev["z5"] = ev.x5/(ev.prevol*np.sqrt(5))
    thr = ev.z5.quantile(0.90)
    ev["S"] = ev.stratum
    dm, dt = strat(ev, "x5", tailcol="z5", thr=thr); cm, ct, _ = boot(ev, "x5", "week", tailcol="z5", thr=thr)
    print(f"{arm} vol-normalized right tail (z>={thr:.2f}, 10% overall) HM {f(dt[0])} [{f(ct[0])},{f(ct[1])}]")
    # left tail normalized
    ev["nz5"] = -ev.z5; thrl = ev.nz5.quantile(0.90)
    dm, dt = strat(ev, "x5", tailcol="nz5", thr=thrl)
    print(f"{arm} vol-normalized LEFT tail HM-analog {f(dt[0])}")
    # date-demeaned x5 (cross-sectional within week): removes market-timing component
    ev["x5d"] = ev.x5 - ev.groupby("week").x5.transform("median")
    ev["S"] = ev.stratum
    dm, dt = strat(ev, "x5d"); cm, ct, _ = boot(ev, "x5d", "week")
    print(f"{arm} x5 minus week-median  HL {f(dm[0])} [{f(cm[0])},{f(cm[1])}]")
    # prevol by v3 status within depth stratum 0
    print(arm, "median prevol, stratum0, v3 on/off:", ev[ev.stratum==0].groupby("v3").prevol.median().round(4).to_dict())
    print(arm, "v3 share by vol tercile:", ev.groupby("vt").v3.mean().round(3).to_dict(), " v1:", ev.groupby("vt").v1.mean().round(3).to_dict(), " v8:", ev.groupby("vt").v8.mean().round(3).to_dict())
