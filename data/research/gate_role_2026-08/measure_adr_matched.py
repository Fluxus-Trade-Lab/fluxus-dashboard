"""Round 2: de-confound ADR by MATCHING, not by dividing.

Why this file exists. The first pass normalised with `|excess| / adr_pct` and
claimed the division was clean because `median |excess|/ADR` looked flat across
ADR deciles. It is not flat -- it runs 1.624 -> 1.033 monotonically, and the
log-log slope of median |excess| on ADR is 0.825, i.e. SUB-linear. Dividing by
ADR^1 therefore hands a systematic bonus to the quietest names, which is
exactly the artefact the first pass said it had ruled out. An independent
adversarial review caught it; this file replaces that step.

Two de-confounding methods, reported side by side:

  A  curve division   -- divide |excess| by E[|excess| | ADR], the empirical
                         median curve over 40 ADR quantiles. Removes any
                         monotone ADR effect, linear or not.
  B  decile matching  -- compare hit vs miss only INSIDE the same (day, ADR
                         decile) cell, then average the cell differences.
                         Makes no functional-form assumption at all.

A screener whose amplitude signal survives BOTH is saying something ADR does
not already say. One that survives neither was an ADR proxy.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
H, MIN_ARM, MIN_DAYS, MIN_CELL = 10, 5, 20, 3
TRAIN_FRAC, NQ, NDEC = 0.70, 40, 10

df = pd.read_csv(HERE / "../adr_floor_2026-08/per_event.csv.gz")
df = df[df[f"excess_{H}"].notna() & df.adr_pct.notna() & (df.adr_pct > 0)].copy()
df["date"] = pd.to_datetime(df["date"])
df["absx"] = df[f"excess_{H}"].abs()

days = np.sort(df.date.unique())
cut = int(len(days) * TRAIN_FRAC)
df["split"] = np.where(df.date.isin(set(days[:cut])), "train", "holdout")

# ---- the shape that broke round 1 --------------------------------------
q = pd.qcut(df.adr_pct, NQ, labels=False, duplicates="drop")
curve = df.assign(q=q).groupby("q").agg(adr=("adr_pct", "median"), absx=("absx", "median"))
slope = float(np.polyfit(np.log(curve.adr), np.log(curve.absx), 1)[0])

# A: divide by the expected |excess| at this name's ADR
exp_absx = df.assign(q=q).q.map(curve.absx)
df["adj"] = df.absx / exp_absx.values

# B: ADR decile, recomputed inside each split so the bins are not set by the
#    other half of the sample
df["dec"] = df.groupby("split", group_keys=False).adr_pct.transform(
    lambda s: pd.qcut(s, NDEC, labels=False, duplicates="drop"))

names = sorted({s for row in df.screeners for s in row.split("|")})
member = {s: df.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values
          for s in names}
included = [s for s in names
            if member[s].sum() >= 500 and df.date[member[s]].nunique() >= 40]


def paired(sub, mask, col):
    """A: median(hit) - median(miss), once per day."""
    d = []
    for _, idx in sub.groupby("date").indices.items():
        a, b = sub[col].values[idx][mask[idx]], sub[col].values[idx][~mask[idx]]
        if len(a) >= MIN_ARM and len(b) >= MIN_ARM:
            d.append(np.median(a) - np.median(b))
    return np.array(d)


def matched(sub, mask, col):
    """B: same comparison but only inside one (day, ADR-decile) cell, then the
    day's value is the mean of its cells' differences."""
    d = []
    dec = sub.dec.values
    vals = sub[col].values
    for _, idx in sub.groupby("date").indices.items():
        cells = []
        for k in np.unique(dec[idx]):
            j = idx[dec[idx] == k]
            a, b = vals[j][mask[j]], vals[j][~mask[j]]
            if len(a) >= MIN_CELL and len(b) >= MIN_CELL:
                cells.append(np.median(a) - np.median(b))
        if len(cells) >= 3:
            d.append(float(np.mean(cells)))
    return np.array(d)


def stat(d):
    if len(d) < MIN_DAYS:
        return {"n_days": int(len(d)), "delta": None, "p": None}
    _, p = wilcoxon(d)
    return {"n_days": int(len(d)), "delta": float(np.median(d)), "p": float(p),
            "share_positive": float(np.mean(d > 0))}


out = {"note": __doc__.strip().splitlines()[0],
       "adr_curve": {"n_quantiles": int(curve.shape[0]),
                     "median_abs_excess_first": round(float(curve.absx.iloc[0]), 5),
                     "median_abs_excess_last": round(float(curve.absx.iloc[-1]), 5),
                     "median_adr_first": round(float(curve.adr.iloc[0]), 3),
                     "median_adr_last": round(float(curve.adr.iloc[-1]), 3),
                     "loglog_slope": round(slope, 3),
                     "verdict": "sub-linear; dividing by ADR^1 favours quiet names"},
       "screeners": {}}

for split in ("train", "holdout"):
    sub = df[df.split == split].reset_index(drop=True)
    m = {s: sub.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values
         for s in included}
    raw = {"A": {}, "B": {}}
    for s in included:
        rA = stat(paired(sub, m[s], "adj"))
        rB = stat(matched(sub, m[s], "adj"))
        out["screeners"].setdefault(s, {})[split] = {"A_curve_divide": rA,
                                                     "B_decile_matched": rB}
        if rA["p"] is not None:
            raw["A"][s] = rA["p"]
        if rB["p"] is not None:
            raw["B"][s] = rB["p"]
    for key, tag in (("A", "A_curve_divide"), ("B", "B_decile_matched")):
        for rank, (s, p) in enumerate(sorted(raw[key].items(), key=lambda x: x[1])):
            out["screeners"][s][split][tag]["p_holm"] = min(1.0, p * (len(raw[key]) - rank))

json.dump(out, open(HERE / "results_adr_matched.json", "w"), indent=1)

print(f"log-log slope of median|excess| on ADR = {slope:.3f}  (1.0 = linear)")
print(f"{'screener':26s} | {'A train':>16s} {'A hold':>16s} | {'B train':>16s} {'B hold':>16s}")
for s in included:
    r = out["screeners"][s]
    def c(sp, tag):
        d = r[sp][tag]
        if d["p"] is None:
            return f"{'NA':>16s}"
        st = "*" if d.get("p_holm", 1) < 0.05 else " "
        return f"{d['delta']:+.4f} p={d['p']:.1g}{st}".rjust(16)
    print(f"{s:26s} | {c('train','A_curve_divide')} {c('holdout','A_curve_divide')} |"
          f" {c('train','B_decile_matched')} {c('holdout','B_decile_matched')}")
