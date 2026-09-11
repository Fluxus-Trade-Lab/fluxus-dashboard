"""POST HOC (not pre-registered): is 'stacking thins both tails' just the
checklist selecting calmer stocks?  Pre-event vol = std of daily returns over
the 20 sessions ending t-5 (before the drop window, so the drop itself is not
in it).  Reports vol by k, then the H-M tail statistic within vol terciles.

    python3 data/research/reversal_checklist_2026-09/posthoc_vol.py --arm discovery
"""
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import study as S

ap = argparse.ArgumentParser(); ap.add_argument("--arm", default="discovery"); a = ap.parse_args()
px, spy = S.load_panel(); f = S.features(px, spy); ev = S.events(px, spy, f)
ev = ev[ev["holdout"] == (a.arm == "holdout")].copy()
vol = px.pct_change(fill_method=None).rolling(20).std().shift(5)
col = {c: i for i, c in enumerate(px.columns)}; row = {d: i for i, d in enumerate(px.index)}
V = vol.values
ev["prevol"] = [V[row[d], col[t]] for t, d in zip(ev["ticker"], ev["date"])]
print("pre-event vol (median daily std) by k:")
print(ev.groupby("k")["prevol"].median().map(lambda v: f"{v:.2%}").to_string())
ev = ev[ev["prevol"].notna()]
ev["vt"] = pd.qcut(ev["prevol"], 3, labels=["calm", "mid", "wild"])
print("\nH-M tail diff (k>=3 minus k<=1) and H-L median diff within vol tercile (depth-stratified, point only):")
for t, g in ev.groupby("vt", observed=True):
    for c in ("x5", "x5_v"):
        dm, dt = S.stratified(g, c)
        print(f"  {t:5s} {c:5s} n={len(g):6d}  median diff {dm[0]:+.2%}  tail diff {dt[0]:+.2%}")
print("\nk share by vol tercile:")
print(pd.crosstab(ev["vt"], ev["k"], normalize="index").map(lambda v: f"{v:.0%}").to_string())

# Matching, not normalising: dividing by vol favours calm names (gate_role
# 2026-08 section 2 measured log|x| ~ 0.823 log ADR), and high k IS the calm
# names.  So compare k>=3 vs k<=1 inside depth x vol-decile cells instead.
ev["vd"] = pd.qcut(ev["prevol"], 10, labels=False)
m = ev.copy()
m["stratum"] = m["stratum"] * 10 + m["vd"]
print("\nPOST HOC matched on depth stratum x pre-event vol decile (30 cells), week-cluster 95% CI:")
for c in ("x5", "x5_v"):
    dm, dt = S.stratified(m, c)
    cm, ct, nw = S.bootstrap(m, c, B=2000)
    print(f"  {c:5s} median diff {dm[0]:+.2%} [{cm[0]:+.2%}, {cm[1]:+.2%}]   tail diff {dt[0]:+.2%} [{ct[0]:+.2%}, {ct[1]:+.2%}]")
