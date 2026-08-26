"""POST-HOC, NOT PRE-REGISTERED. Read as a question, not a result.

The floor's stated rationale (watchlist.py:52) is "R = ATR, so a 1% ADR name
needs 3x the size for the same risk unit". That sentence is about % space. In R
space the same move is worth excess/ADR. So: do the cut names give up edge per
unit of risk, or only per unit of price?
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "per_event.csv", parse_dates=["date"])
df["excess_10_R"] = df.excess_10 / (df.adr_pct / 100.0)

def paired(col, stat):
    ds = []
    for d, g in df.groupby("date"):
        a, b = g[g.cut][col].dropna(), g[~g.cut][col].dropna()
        if len(a) >= 5 and len(b) >= 5:
            ds.append(stat(a) - stat(b))
    ds = np.array(ds)
    st, p = wilcoxon(ds)
    return {"n_days": len(ds), "median_d": round(float(np.median(ds)), 4),
            "p": float(p), "share_positive": round(float(np.mean(ds > 0)), 4)}

med = lambda x: float(np.median(x))
absmed = lambda x: float(np.median(np.abs(x)))
out = {
 "_warning": "POST-HOC. Not in prereg_adr_floor.md. Hypothesis-generating only.",
 "median_excess_10_in_R": paired("excess_10_R", med),
 "median_abs_excess_10_in_R": paired("excess_10_R", absmed),
 "descriptive": {g: {"median_excess_10_R": round(float(df[df.cut == c].excess_10_R.median()), 4),
                     "median_abs_excess_10_R": round(float(df[df.cut == c].excess_10_R.abs().median()), 4),
                     "n": int((df.cut == c).sum())}
                 for g, c in (("CUT_adr_lt_3.5", True), ("KEEP_adr_ge_3.5", False))}}
json.dump(out, open(HERE / "posthoc_r_units.json", "w"), indent=1)
print(json.dumps(out, indent=1))
