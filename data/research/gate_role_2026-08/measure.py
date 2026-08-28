"""Is each screener a stock-picking gate or a position-sizing gate?

Pre-registered in prereg.md; nothing here deviates from it. Runs in the
declared order: build -> positive control -> false-positive rate -> main
tests -> holdout replication.

Reads the event panel built by ../adr_floor_2026-08/ (zero new fetching).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(20260829)
H = 10                      # primary horizon, pre-declared
MIN_EVENTS, MIN_DAYS = 500, 40
MIN_ARM, MIN_PAIRED_DAYS = 5, 20
TRAIN_FRAC = 0.70
PERM_TRIALS = 200

df = pd.read_csv(HERE / "../adr_floor_2026-08/per_event.csv.gz")
df = df[df[f"excess_{H}"].notna() & df.adr_pct.notna() & (df.adr_pct > 0)].copy()
df["date"] = pd.to_datetime(df["date"])
# R-like units: excess is a fraction, adr_pct is a percent.
df["r10"] = df[f"excess_{H}"] * 100.0 / df.adr_pct

days = np.sort(df.date.unique())
cut_i = int(len(days) * TRAIN_FRAC)
TRAIN, HOLD = set(days[:cut_i]), set(days[cut_i:])
df["split"] = np.where(df.date.isin(TRAIN), "train", "holdout")

names = sorted({s for row in df.screeners for s in row.split("|")})
member = {s: df.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values
          for s in names}

included, excluded = [], {}
for s in names:
    m = member[s]
    n, d = int(m.sum()), int(df.date[m].nunique())
    if n >= MIN_EVENTS and d >= MIN_DAYS:
        included.append(s)
    else:
        excluded[s] = {"events": n, "days": d}

# ---------------------------------------------------------------- statistics
med = lambda x: float(np.median(x))
absmed = lambda x: float(np.median(np.abs(x)))
rtail = lambda x: float(np.mean(x >= 0.10))
rtail_r = lambda x: float(np.mean(x >= 2.0))

METRICS = [
    ("M1_median_excess",   f"excess_{H}", med,     "stock-picking"),
    ("M2_median_abs",      f"excess_{H}", absmed,  "amplitude (raw)"),
    ("M3_right_tail_10pct",f"excess_{H}", rtail,   "right tail (raw)"),
    ("M2r_median_abs_R",   "r10",         absmed,  "amplitude (ADR-normalised)"),
    ("M3r_right_tail_2R",  "r10",         rtail_r, "right tail (ADR-normalised)"),
]


def day_deltas(frame, mask, col, stat):
    """stat(HIT) - stat(MISS) once per trading day. Same-day subtraction
    removes the market, so n is trading days, not rows."""
    out = []
    dates = frame.date.values
    vals = frame[col].values
    for d in np.unique(dates):
        sel = dates == d
        a, b = vals[sel & mask], vals[sel & ~mask]
        if len(a) >= MIN_ARM and len(b) >= MIN_ARM:
            out.append(stat(a) - stat(b))
    return np.asarray(out)


def test(frame, mask, col, stat):
    ds = day_deltas(frame, mask, col, stat)
    if len(ds) < MIN_PAIRED_DAYS:
        return {"n_days": int(len(ds)), "delta": None, "p": None}
    _, p = wilcoxon(ds)
    return {"n_days": int(len(ds)), "delta": float(np.median(ds)),
            "mean_delta": float(np.mean(ds)), "p": float(p),
            "share_positive": float(np.mean(ds > 0))}


tr = df[df.split == "train"].reset_index(drop=True)
ho = df[df.split == "holdout"].reset_index(drop=True)
tr_mask = {s: tr.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values for s in included}
ho_mask = {s: ho.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values for s in included}

out = {"sample": {"events": int(len(df)), "days": int(df.date.nunique()),
                  "tickers": int(df.ticker.nunique()),
                  "first": str(pd.Timestamp(days[0]).date()), "last": str(pd.Timestamp(days[-1]).date()),
                  "train_days": len(TRAIN), "holdout_days": len(HOLD),
                  "train_split_at": str(pd.Timestamp(days[cut_i]).date()),
                  "train_events": int((df.split == "train").sum()),
                  "holdout_events": int((df.split == "holdout").sum())},
       "included": included, "excluded": excluded,
       "calibration": json.load(open(HERE / "../adr_floor_2026-08/calibration.json"))}

# ---- 7.1 positive control: inject a known edge into HIT, M1 must catch it --
print("positive control ...")
pc = {}
for s in included:
    m = tr_mask[s]
    row = {}
    for pp in (0.005, 0.010, 0.020):
        f = tr.copy()
        f.loc[m, f"excess_{H}"] = f.loc[m, f"excess_{H}"] + pp
        r = test(f, m, f"excess_{H}", med)
        row[f"+{pp*100:.1f}pp"] = {"delta": r["delta"], "p": r["p"]}
    pc[s] = row
out["positive_control"] = pc

# ---- 7.2 false-positive rate: shuffle membership inside each day ----------
print("false-positive rate ...")
fpr = {}
dates_tr = tr.date.values
uniq = np.unique(dates_tr)
day_idx = {d: np.where(dates_tr == d)[0] for d in uniq}
for s in included:
    m0 = tr_mask[s]
    ps = []
    for _ in range(PERM_TRIALS):
        m = np.zeros(len(tr), bool)
        for d, idx in day_idx.items():
            k = int(m0[idx].sum())
            if k:
                m[RNG.choice(idx, size=k, replace=False)] = True
        r = test(tr, m, f"excess_{H}", med)
        if r["p"] is not None:
            ps.append(r["p"])
    fpr[s] = {"trials": len(ps),
              "share_p_lt_.05": (round(float(np.mean(np.array(ps) < 0.05)), 4) if ps else None)}
out["false_positive_rate"] = fpr

# ---- main tests on train, Holm within each metric across screeners --------
print("main tests ...")
main = {s: {} for s in included}
for key, col, stat, _lab in METRICS:
    raw = {}
    for s in included:
        r = test(tr, tr_mask[s], col, stat)
        main[s][key] = r
        if r["p"] is not None:
            raw[s] = r["p"]
    for rank, (s, p) in enumerate(sorted(raw.items(), key=lambda x: x[1])):
        main[s][key]["p_holm"] = min(1.0, p * (len(raw) - rank))
out["train"] = main

# ---- holdout: same statistics, direction check only ----------------------
print("holdout ...")
hold = {s: {} for s in included}
for key, col, stat, _lab in METRICS:
    for s in included:
        hold[s][key] = test(ho, ho_mask[s], col, stat)
out["holdout"] = hold

# ---- classification (rules pre-declared in prereg §6) --------------------
def sig(r):  # significant after Holm
    return r.get("p_holm") is not None and r["p_holm"] < 0.05

verdict = {}
for s in included:
    t = main[s]
    m1 = t["M1_median_excess"]
    if m1["p"] is None:                       # prereg §4: < 20 paired days
        verdict[s] = {"verdict": "unmeasurable", "negatives": [],
                      "holdout_direction_agrees": {}, "replicated": False,
                      "why": f"only {m1['n_days']} paired days (need {MIN_PAIRED_DAYS})"}
        continue
    pick = sig(m1) and m1["delta"] > 0
    amp_raw = (sig(t["M2_median_abs"]) and t["M2_median_abs"]["delta"] > 0) or \
              (sig(t["M3_right_tail_10pct"]) and t["M3_right_tail_10pct"]["delta"] > 0)
    amp_r = (sig(t["M2r_median_abs_R"]) and t["M2r_median_abs_R"]["delta"] > 0) or \
            (sig(t["M3r_right_tail_2R"]) and t["M3r_right_tail_2R"]["delta"] > 0)
    neg = [k for k, _c, _s, _l in METRICS if sig(t[k]) and t[k]["delta"] < 0]
    flat_m1 = (not sig(m1)) and m1["delta"] is not None and abs(m1["delta"]) < 0.01

    if pick and amp_r:
        v = "both"
    elif pick:
        v = "stock-picking gate"
    elif flat_m1 and amp_r:
        v = "position-sizing gate"
    elif amp_raw and not amp_r:
        v = "shadow of ADR"
    elif not (pick or amp_raw or amp_r) and not neg:
        v = "dumb gate"
    else:
        v = "mixed / see negatives"

    # holdout direction agreement on whichever metric carried the verdict
    keys = [k for k, _c, _s, _l in METRICS if sig(t[k])]
    agree = {k: bool(hold[s][k]["delta"] is not None and t[k]["delta"] is not None
                     and np.sign(hold[s][k]["delta"]) == np.sign(t[k]["delta"])) for k in keys}
    if all(hold[s][k]["p"] is None for k, _c, _st, _l in METRICS):
        v += " (train only; holdout unmeasurable)"
    verdict[s] = {"verdict": v, "negatives": neg,
                  "holdout_direction_agrees": agree,
                  "replicated": bool(agree) and all(agree.values())}
out["verdict"] = verdict

# ---- post-hoc diagnostic (declared as post-hoc): is M2 just ADR? --------
# If |excess| were sub-linear in ADR, dividing by ADR would mechanically
# favour quiet names and M2r would be an *inverse* shadow. Check both ends.
dec = pd.qcut(df.adr_pct, 10, labels=False)
by_dec = df.assign(dec=dec).groupby("dec").apply(
    lambda g: pd.Series({"median_adr": g.adr_pct.median(),
                         "median_abs_excess": g[f"excess_{H}"].abs().median(),
                         "median_abs_R": g.r10.abs().median(), "n": len(g)}),
    include_groups=False)
comp = []
for s_ in included:
    m = member[s_][df.index.isin(df.index)] if False else df.screeners.str.contains(
        rf"(?:^|\|){s_}(?:\||$)", regex=True).values
    if main[s_]["M2r_median_abs_R"]["delta"] is None:
        continue
    comp.append({"screener": s_,
                 "d_median_adr": float(df.adr_pct[m].median() - df.adr_pct[~m].median()),
                 "M2_raw": main[s_]["M2_median_abs"]["delta"],
                 "M2r_norm": main[s_]["M2r_median_abs_R"]["delta"]})
c = pd.DataFrame(comp)
out["posthoc_adr_shadow"] = {
    "note": "POST-HOC, not pre-registered. Across screeners: does the raw "
            "amplitude difference track how much higher-ADR the screener's "
            "names are? And does normalising remove it?",
    "by_adr_decile": {str(k): {kk: round(float(vv), 4) for kk, vv in v.items()}
                      for k, v in by_dec.to_dict("index").items()},
    "per_screener": comp,
    "spearman_dAdr_vs_M2_raw": round(float(c.d_median_adr.corr(c.M2_raw, method="spearman")), 3),
    "spearman_dAdr_vs_M2r_norm": round(float(c.d_median_adr.corr(c.M2r_norm, method="spearman")), 3)}

json.dump(out, open(HERE / "results.json", "w"), indent=1)
print(json.dumps({"sample": out["sample"], "verdict": verdict}, indent=1))
