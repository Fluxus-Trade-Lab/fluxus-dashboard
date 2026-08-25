"""Delayed EP: which day do you enter? -- measurement per prereg_window.md.

Every number in results.md comes from this file. No thresholds are chosen here;
D grid, hold length, excess definition and the holdout salt are all fixed in
the pre-registration written before any forward return was computed.
"""
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SALT = "dep-window-20260826"   # prereg §3
DS = range(1, 16)              # entry offsets
HOLD = 5                       # sessions held

close = pd.read_csv(HERE / "bars.csv", index_col=0, parse_dates=True)
sess = close.index                                  # trading calendar from the bars
spy = close["SPY"]

events = [r for r in csv.DictReader(open(ROOT / "data/history/ticker_events.csv"))
          if r["screener"] == "episodic_pivot"]

def half(t):
    return "discovery" if int(hashlib.sha1((SALT + t).encode()).hexdigest(), 16) % 2 == 0 else "holdout"

recs, dropped = [], {"no_col": 0, "ep_not_in_cal": 0, "short_tail": 0}
for e in events:
    t, d0 = e["ticker"], pd.Timestamp(e["date"])
    if t not in close.columns:
        dropped["no_col"] += 1; continue
    px = close[t]
    idx = sess.searchsorted(d0)
    if idx >= len(sess) or sess[idx] != d0:
        dropped["ep_not_in_cal"] += 1; continue
    if idx + max(DS) + HOLD >= len(sess):
        dropped["short_tail"] += 1; continue
    row = {"ticker": t, "ep_date": e["date"], "half": half(t)}
    ok = True
    for D in DS:
        a, b = px.iloc[idx + D], px.iloc[idx + D + HOLD]
        sa, sb = spy.iloc[idx + D], spy.iloc[idx + D + HOLD]
        if not np.isfinite([a, b, sa, sb]).all() or a <= 0 or sa <= 0:
            ok = False; break
        row[f"D{D}"] = (b / a - 1) - (sb / sa - 1)
    if ok:
        recs.append(row)

df = pd.DataFrame(recs)
print(f"events in archive: {len(events)}  usable: {len(df)}  dropped: {dropped}")
print(f"  discovery {(df.half=='discovery').sum()}  holdout {(df.half=='holdout').sum()}")
print(f"  distinct EP dates {df.ep_date.nunique()}  distinct tickers {df.ticker.nunique()}")

cols = [f"D{D}" for D in DS]

def curve(sub, label):
    print(f"\n--- {label} (n={len(sub)}) ---")
    print(f"{'D':>3} {'median excess':>14} {'>0':>7} {'mean':>9}")
    out = {}
    for D in DS:
        v = sub[f"D{D}"]
        out[D] = dict(median=float(v.median()), win=float((v > 0).mean()), mean=float(v.mean()), n=int(v.notna().sum()))
        print(f"{D:>3} {v.median()*100:>13.2f}% {(v>0).mean()*100:>6.1f}% {v.mean()*100:>8.2f}%")
    return out

def paired(sub, left, right, name):
    """Wilcoxon signed-rank on the within-event difference of two D-blocks."""
    L = sub[[f"D{d}" for d in left]].mean(axis=1)
    R = sub[[f"D{d}" for d in right]].mean(axis=1)
    d = (L - R).dropna()
    stat, p = wilcoxon(d, alternative="two-sided")
    return dict(name=name, left=list(left), right=list(right), n=int(len(d)),
                median_diff=float(d.median()), mean_diff=float(d.mean()),
                share_positive=float((d > 0).mean()), p=float(p))

TESTS = [((1, 2), (3,), "P1  D1,2 vs D3            (H2 our --min-days cost)"),
         (tuple(range(1, 5)), tuple(range(5, 16)), "P2  D1-4 vs D5-15         (H3 his window vs our tail)"),
         ((1, 2), tuple(range(3, 16)), "P3  D1,2 vs D3-15         (H1 early is better)")]

res = {"n_events": len(df), "dropped": dropped,
       "distinct_ep_dates": int(df.ep_date.nunique()), "distinct_tickers": int(df.ticker.nunique())}
for label, sub in (("all", df), ("discovery", df[df.half == "discovery"]), ("holdout", df[df.half == "holdout"])):
    res[f"curve_{label}"] = curve(sub, label)

for label in ("discovery", "holdout", "all"):
    sub = df[df.half == label] if label != "all" else df
    print(f"\n=== paired tests :: {label} (n={len(sub)}) ===")
    ts = [paired(sub, l, r, n) for l, r, n in TESTS]
    ps = sorted(range(len(ts)), key=lambda i: ts[i]["p"])
    for rank, i in enumerate(ps):                       # Holm, family = 3
        ts[i]["p_holm"] = min(1.0, ts[i]["p"] * (len(ts) - rank))
    for t in ts:
        print(f"{t['name']}  n={t['n']:>3}  median_diff={t['median_diff']*100:>+6.2f}%  "
              f"share+={t['share_positive']*100:>5.1f}%  p={t['p']:.4f}  p_holm={t['p_holm']:.4f}")
    res[f"tests_{label}"] = ts

json.dump(res, open(HERE / "results.json", "w"), indent=1)
df.to_csv(HERE / "per_event.csv", index=False)
print("\nwrote results.json, per_event.csv")
