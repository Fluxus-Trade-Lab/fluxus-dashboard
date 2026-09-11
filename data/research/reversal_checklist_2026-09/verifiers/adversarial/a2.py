import sys, pandas as pd, numpy as np
sys.path.insert(0, "/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/wt-night/data/research/reversal_checklist_2026-09")
import study as S
OUT="/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bb656516-2546-4c8a-a682-52545aa25f71/scratchpad/verify_adversarial/"
ev0 = pd.read_pickle(OUT+"ev.pkl")

def strat(ev, col, wc=None, wix=None, strata=None, tailcol=None, thr=S.TAIL):
    lo, hi = ev["k"] <= 1, ev["k"] >= 3
    mp, tp, W = [], [], []
    for s in sorted(ev["S"].unique()):
        cell = ev["S"] == s
        a, b = ev[cell & lo], ev[cell & hi]
        a, b = a[a[col].notna()], b[b[col].notna()]
        if len(a) == 0 or len(b) == 0: continue
        res = []
        for g in (b, a):
            o = np.argsort(g[col].values); v = g[col].values[o]
            tv = (g[tailcol].values[o] if tailcol else v)
            w = np.ones((1, len(v))) if wc is None else wc[:, wix.loc[g.index].values[o]]
            res.append((S._wmedian(v, w), (w*(tv>=thr)).sum(1)/np.maximum(w.sum(1),1e-12), w.sum(1)))
        (mb,tb,nb),(ma,ta,na) = res
        mp.append(mb-ma); tp.append(tb-ta); W.append(nb+na)
    W = np.vstack(W)
    return (np.vstack(mp)*W).sum(0)/W.sum(0), (np.vstack(tp)*W).sum(0)/W.sum(0)

def boot(ev, col, clus, B=1000, seed=0, **kw):
    rng = np.random.default_rng(seed)
    cl = np.sort(ev[clus].unique()); wix = ev[clus].map({w:i for i,w in enumerate(cl)})
    dms, dts = [], []
    for st in range(0, B, 100):
        b = min(100, B-st)
        d = rng.integers(0, len(cl), size=(b, len(cl)))
        c = np.zeros((b, len(cl))); np.add.at(c, (np.repeat(np.arange(b), len(cl)), d.ravel()), 1)
        dm, dt = strat(ev, col, c, wix, **kw); dms.append(dm); dts.append(dt)
    dm, dt = np.concatenate(dms), np.concatenate(dts)
    q = lambda a: (np.nanpercentile(a,2.5), np.nanpercentile(a,97.5))
    return q(dm), q(dt), len(cl)

ev0["S"] = ev0["stratum"]
ev0["month"] = ev0.date.dt.year*100 + ev0.date.dt.month
ev0["blk4"] = (ev0.date - pd.Timestamp("2016-01-04")).dt.days // 28
ev0["qtr"] = ev0.date.dt.year*10 + ev0.date.dt.quarter
f = lambda x: f"{x:+.2%}"
for arm, h in (("disc", False), ("hold", True), ("pooled", None)):
    ev = ev0 if h is None else ev0[ev0.holdout==h]
    dm, dt = strat(ev, "x5")
    print(f"\n== {arm} n={len(ev)} x5 HL={f(dm[0])} HM={f(dt[0])}")
    for clus in ("week","blk4","month","qtr"):
        cm, ct, nc = boot(ev, "x5", clus)
        print(f"  clus={clus:5s} n_cl={nc:4d} HL CI [{f(cm[0])},{f(cm[1])}]  HM CI [{f(ct[0])},{f(ct[1])}]")
