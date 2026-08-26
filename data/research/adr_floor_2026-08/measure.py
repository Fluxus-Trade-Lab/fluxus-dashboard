"""ADR>=3.5 universe floor: what did the names it cuts do next?

Runs in the pre-registered order: build -> positive control -> false-positive
rate -> main tests. See prereg_adr_floor.md; nothing here deviates from it.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(20260827)
FLOOR, LAST, HS = 3.5, pd.Timestamp("2026-08-25"), (5, 10, 20)

close = pd.read_csv(HERE / "close.csv", index_col=0, parse_dates=True).loc[:LAST]
adr = pd.read_csv(HERE / "adr_pct_recon.csv", index_col=0, parse_dates=True).loc[:LAST]
ev = pd.read_csv(HERE / "../../history/ticker_events.csv")
ev["date"] = pd.to_datetime(ev["date"])

sessions = close.index
pos = {d: i for i, d in enumerate(sessions)}
spy = close["SPY"]

rows, dropped = [], {"no_bar": 0, "no_adr": 0, "no_forward": {h: 0 for h in HS}}
for (d, t), grp in ev.groupby(["date", "ticker"], sort=False):
    if d not in pos or t not in close.columns:
        dropped["no_bar"] += 1; continue
    i = pos[d]
    a = adr[t].iloc[i]
    if pd.isna(a):
        dropped["no_adr"] += 1; continue
    c0, s0 = close[t].iloc[i], spy.iloc[i]
    if pd.isna(c0) or c0 <= 0:
        dropped["no_bar"] += 1; continue
    r = {"date": d, "ticker": t, "adr_pct": float(a),
         "screeners": "|".join(sorted(grp.screener.unique()))}
    for h in HS:
        j = i + h
        if j >= len(sessions) or pd.isna(close[t].iloc[j]):
            r[f"excess_{h}"] = np.nan; dropped["no_forward"][h] += 1
        else:
            r[f"excess_{h}"] = float((close[t].iloc[j] / c0 - 1) - (spy.iloc[j] / s0 - 1))
    rows.append(r)

df = pd.DataFrame(rows)
df["cut"] = df.adr_pct < FLOOR
df.to_csv(HERE / "per_event.csv", index=False)


def paired(frame, col, stat):
    """One observation per trading day: stat(CUT) - stat(KEEP). Same-day
    subtraction removes the market, so n is trading days, not rows."""
    ds = []
    for d, g in frame.groupby("date"):
        a, b = g[g.cut][col].dropna(), g[~g.cut][col].dropna()
        if len(a) >= 5 and len(b) >= 5:
            ds.append(stat(a) - stat(b))
    ds = np.array(ds)
    if len(ds) < 10:
        return {"n_days": len(ds), "median_d": None, "p": None}
    st, p = wilcoxon(ds)
    return {"n_days": int(len(ds)), "median_d": float(np.median(ds)),
            "mean_d": float(np.mean(ds)), "p": float(p),
            "share_positive": float(np.mean(ds > 0))}


med = lambda x: float(np.median(x))
absmed = lambda x: float(np.median(np.abs(x)))
rtail = lambda x: float(np.mean(x >= 0.10))

out = {"calibration": json.load(open(HERE / "calibration.json")),
       "sample": {"events": int(len(df)), "days": int(df.date.nunique()),
                  "tickers": int(df.ticker.nunique()),
                  "cut": int(df.cut.sum()), "keep": int((~df.cut).sum()),
                  "dropped": {k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()})
                              for k, v in dropped.items()},
                  "first": str(df.date.min().date()), "last": str(df.date.max().date())}}

# ---- 3.1 positive control: inject a known edge into CUT, must be caught ----
inj = {}
for pp in (0.005, 0.010, 0.020):
    f = df.copy()
    f.loc[f.cut, "excess_10"] = f.loc[f.cut, "excess_10"] + pp
    inj[f"+{pp*100:.1f}pp"] = paired(f, "excess_10", med)
out["positive_control_injection"] = inj

# ---- 3.2 false-positive rate: shuffle CUT/KEEP within each day ----
ps = []
for _ in range(200):
    f = df.copy()
    f["cut"] = f.groupby("date")["cut"].transform(lambda s: RNG.permutation(s.values))
    r = paired(f, "excess_10", med)
    if r["p"] is not None:
        ps.append(r["p"])
out["false_positive_rate"] = {"trials": len(ps),
                              "share_p_lt_.05": round(float(np.mean(np.array(ps) < 0.05)), 4)}

# ---- 4 main tests ----
main = {"H1H2_median_excess_10": paired(df, "excess_10", med),
        "H3a_median_abs_excess_10": paired(df, "excess_10", absmed),
        "H3b_right_tail_ge_10pct": paired(df, "excess_10", rtail)}
raw = [(k, v["p"]) for k, v in main.items() if v["p"] is not None]
for rank, (k, p) in enumerate(sorted(raw, key=lambda x: x[1])):
    main[k]["p_holm"] = min(1.0, p * (len(raw) - rank))
out["main"] = main

out["secondary_horizons"] = {f"excess_{h}": paired(df, f"excess_{h}", med) for h in HS}
out["descriptive"] = {
    g: {f"median_excess_{h}": round(float(df[df.cut == c][f"excess_{h}"].median()), 5) for h in HS}
       | {"median_abs_excess_10": round(float(df[df.cut == c].excess_10.abs().median()), 5),
          "right_tail_ge_10pct": round(float((df[df.cut == c].excess_10 >= 0.10).mean()), 5),
          "left_tail_le_-10pct": round(float((df[df.cut == c].excess_10 <= -0.10).mean()), 5),
          "n": int((df.cut == c).sum())}
    for g, c in (("CUT_adr_lt_3.5", True), ("KEEP_adr_ge_3.5", False))}

json.dump(out, open(HERE / "results.json", "w"), indent=1)
print(json.dumps(out, indent=1))
