"""Is vcp's edge the contraction, or the ADR it happens to pick?

Pre-registered in prereg_vcp_adr.md. Runs positive control first.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "per_event.csv", parse_dates=["date"])
df["vcp"] = df.screeners.fillna("").str.split("|").apply(lambda s: "vcp" in s)
# ADR quintile WITHIN each day
df["adrq"] = df.groupby("date").adr_pct.transform(
    lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))

def cells(frame, col):
    """One d per (day, ADR quintile) cell."""
    out = []
    for (d, q), g in frame.groupby(["date", "adrq"]):
        a, b = g[g.vcp][col].dropna(), g[~g.vcp][col].dropna()
        if len(a) >= 3 and len(b) >= 3:
            out.append({"date": d, "adrq": q, "d": float(a.median() - b.median()),
                        "n_vcp": len(a), "n_other": len(b)})
    return pd.DataFrame(out)

def test(frame, col):
    c = cells(frame, col)
    if len(c) < 10:
        return {"cells": len(c), "note": "too few cells"}
    st_c, p_c = wilcoxon(c.d.values)
    byday = c.groupby("date").d.median()            # primary: n = trading days
    st_d, p_d = wilcoxon(byday.values)
    return {"cells": int(len(c)), "cell_median_d": round(float(c.d.median()), 5),
            "cell_p": float(p_c),
            "n_days": int(len(byday)), "day_median_d": round(float(byday.median()), 5),
            "day_p": float(p_d), "day_share_positive": round(float((byday > 0).mean()), 4),
            "n_vcp_used": int(c.n_vcp.sum()), "n_other_used": int(c.n_other.sum())}

out = {"sample": {"vcp_events": int(df.vcp.sum()), "other_events": int((~df.vcp).sum()),
                  "days": int(df.date.nunique())}}

# --- positive control first ---
pc = {}
for pp in (0.01, 0.02, 0.03):
    f = df.copy(); f.loc[f.vcp, "excess_20"] = f.loc[f.vcp, "excess_20"] + pp
    r = test(f, "excess_20")
    pc[f"+{pp*100:.0f}pp"] = {"day_p": r.get("day_p"), "day_median_d": r.get("day_median_d")}
out["positive_control"] = pc

main = {"excess_20": test(df, "excess_20"), "excess_10": test(df, "excess_10")}
raw = sorted([(k, v["day_p"]) for k, v in main.items()], key=lambda x: x[1])
for rank, (k, p) in enumerate(raw):
    main[k]["day_p_holm"] = min(1.0, p * (len(raw) - rank))
out["main"] = main

# unconditional (no ADR matching) for contrast -- this is the shape 08-18 measured
uncond = []
for d, g in df.groupby("date"):
    a, b = g[g.vcp].excess_20.dropna(), g[~g.vcp].excess_20.dropna()
    if len(a) >= 3 and len(b) >= 3:
        uncond.append(a.median() - b.median())
st, p = wilcoxon(uncond)
out["unconditional_no_adr_matching"] = {
    "n_days": len(uncond), "day_median_d": round(float(np.median(uncond)), 5),
    "day_p": float(p), "day_share_positive": round(float(np.mean(np.array(uncond) > 0)), 4)}

out["adr_profile"] = {
    "vcp_median_adr": round(float(df[df.vcp].adr_pct.median()), 3),
    "other_median_adr": round(float(df[~df.vcp].adr_pct.median()), 3),
    "vcp_share_below_3.5": round(float((df[df.vcp].adr_pct < 3.5).mean()), 4),
    "other_share_below_3.5": round(float((df[~df.vcp].adr_pct < 3.5).mean()), 4)}

json.dump(out, open(HERE / "vcp_adr.json", "w"), indent=1)
print(json.dumps(out, indent=1))
