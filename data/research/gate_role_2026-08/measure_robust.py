"""Round 3: what survives once the days are allowed to be dependent?

Rounds 1-2 tested each screener with a Wilcoxon over daily deltas, i.e. one
observation per trading day treated as independent. Three independent reviews
converged on the same objection and it is right: the days are not independent.

  * a name that hits a screener tends to keep hitting it for several sessions
  * the 10-day forward window of day t overlaps day t+1's by 90%

Measured here: the lag-1 autocorrelation of each screener's daily delta series,
and the resulting effective sample size n_eff = n (1-r)/(1+r).

Two dependence-robust replacements, both keeping whole blocks intact:
  * BLOCK SIGN-FLIP  -- randomise the sign of entire length-10 blocks; the
    null is "no shift", the blocks keep whatever within-block structure exists
  * HAC t-test       -- Newey-West standard error at lag 10

Also reports the ADR dirt found by review: adr_pct values above 100.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(20260829)
H, BLOCK, TRIALS, MIN_ARM, MIN_DAYS = 10, 10, 5000, 5, 20

df = pd.read_csv(HERE / "../adr_floor_2026-08/per_event.csv.gz")
dirty = df[(df.adr_pct > 100) | (df.adr_pct <= 0)]
df = df[df[f"excess_{H}"].notna() & df.adr_pct.notna() & (df.adr_pct > 0)].copy()
df["date"] = pd.to_datetime(df["date"])
df["absx"] = df[f"excess_{H}"].abs()

days = np.sort(df.date.unique())
cut = int(len(days) * 0.70)
df["split"] = np.where(df.date.isin(set(days[:cut])), "train", "holdout")

# ADR-adjusted amplitude (round 2 method A: divide by E[|excess| | ADR])
q = pd.qcut(df.adr_pct, 40, labels=False, duplicates="drop")
curve = df.assign(q=q).groupby("q").absx.median()
df["adj"] = df.absx / df.assign(q=q).q.map(curve).values

names = sorted({s for row in df.screeners for s in row.split("|")})
inc = [s for s in names
       if df.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).sum() >= 500]


def deltas(sub, mask, col, stat):
    out, ds = [], []
    vals = sub[col].values
    for d, idx in sub.groupby("date").indices.items():
        a, b = vals[idx][mask[idx]], vals[idx][~mask[idx]]
        if len(a) >= MIN_ARM and len(b) >= MIN_ARM:
            out.append(stat(a) - stat(b))
            ds.append(d)
    return np.array(out)


def acf1(x):
    x = x - x.mean()
    return float(np.dot(x[:-1], x[1:]) / np.dot(x, x)) if len(x) > 2 and np.dot(x, x) else 0.0


def block_signflip(x):
    """p for H0: the series is symmetric about zero, blocks kept intact."""
    n = len(x)
    obs = abs(x.mean())
    blocks = [np.arange(i, min(i + BLOCK, n)) for i in range(0, n, BLOCK)]
    hits = 0
    for _ in range(TRIALS):
        y = x.copy()
        for b in blocks:
            if RNG.random() < 0.5:
                y[b] = -y[b]
        hits += abs(y.mean()) >= obs
    return (hits + 1) / (TRIALS + 1)


def hac_p(x, lag=BLOCK):
    """Newey-West t on the mean."""
    n = len(x)
    e = x - x.mean()
    g0 = np.dot(e, e) / n
    s = g0
    for k in range(1, min(lag, n - 1) + 1):
        gk = np.dot(e[:-k], e[k:]) / n
        s += 2 * (1 - k / (lag + 1)) * gk
    s = max(s, 1e-18)
    from scipy.stats import norm
    t = x.mean() / np.sqrt(s / n)
    return float(2 * (1 - norm.cdf(abs(t)))), float(t)


med = lambda v: float(np.median(v))
METRICS = [("M1_median_excess", f"excess_{H}", med),
           ("AMP_adr_adjusted", "adj", med)]

out = {"note": __doc__.strip().splitlines()[0],
       "block_len": BLOCK, "trials": TRIALS,
       "adr_dirt": {"rows_adr_gt_100_or_le_0": int(len(dirty)),
                    "max_adr_pct": float(df.adr_pct.max()),
                    "max_in_raw_panel": float(dirty.adr_pct.max()) if len(dirty) else None,
                    "note": "excluded from every test here; flagged for the panel builder"},
       "screeners": {}}

for split in ("train", "holdout"):
    sub = df[df.split == split].reset_index(drop=True)
    masks = {s: sub.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values for s in inc}
    raw = {k: {} for k, _c, _s in METRICS}
    for s in inc:
        for key, col, stat in METRICS:
            d = deltas(sub, masks[s], col, stat)
            rec = {"n_days": int(len(d))}
            if len(d) >= MIN_DAYS:
                r = acf1(d)
                p_hac, t = hac_p(d)
                rec |= {"median": med(d), "mean": float(d.mean()), "acf1": round(r, 3),
                        "n_eff": round(len(d) * (1 - r) / (1 + r), 1),
                        "p_blockflip": round(block_signflip(d), 4),
                        "p_hac": round(p_hac, 4), "t_hac": round(t, 2)}
                raw[key][s] = rec["p_blockflip"]
            out["screeners"].setdefault(s, {}).setdefault(split, {})[key] = rec
    for key, _c, _s in METRICS:
        run = 0.0
        for rank, (s, p) in enumerate(sorted(raw[key].items(), key=lambda x: x[1])):
            run = max(run, min(1.0, p * (len(raw[key]) - rank)))
            out["screeners"][s][split][key]["p_blockflip_holm"] = round(run, 4)
        # HAC is the test that turns out to have usable resolution here (see
        # the positive control at the bottom), so it gets a Holm column too.
        hp = {s: out["screeners"][s][split][key]["p_hac"]
              for s in raw[key] if "p_hac" in out["screeners"][s][split][key]}
        run = 0.0
        for rank, (s, p) in enumerate(sorted(hp.items(), key=lambda x: x[1])):
            run = max(run, min(1.0, p * (len(hp) - rank)))
            out["screeners"][s][split][key]["p_hac_holm"] = round(run, 5)

json.dump(out, open(HERE / "results_robust.json", "w"), indent=1)

print(f"adr dirt rows (>100 or <=0): {len(dirty)}   max in raw panel: "
      f"{dirty.adr_pct.max() if len(dirty) else 'n/a'}")
print(f"\n{'screener':26s} {'metric':18s} {'n':>3s} {'acf1':>6s} {'n_eff':>6s} "
      f"{'median':>9s} {'p_flip':>8s} {'p_holm':>8s} {'p_hac':>8s}")
survivors = []
for s in inc:
    for key, _c, _s2 in METRICS:
        r = out["screeners"][s]["train"][key]
        if "median" not in r:
            continue
        ph = r["p_blockflip_holm"]
        if ph < 0.05:
            survivors.append((s, key, ph))
        print(f"{s:26s} {key:18s} {r['n_days']:3d} {r['acf1']:6.2f} {r['n_eff']:6.1f} "
              f"{r['median']:+9.4f} {r['p_blockflip']:8.4f} {ph:8.4f} {r['p_hac']:8.4f}")
print("\nSURVIVING Holm after block sign-flip (train):", survivors or "NONE")


# ---------------------------------------------------------------------------
# Positive control FOR THE ROBUST TESTS THEMSELVES.
#
# "No survivors" is only informative if the test could have reported one. With
# n=67 days and blocks of 10 there are 7 blocks, so the sign-flip null has 2^7
# = 128 arrangements and the smallest two-sided p it can return is ~1/128; a
# Holm factor of 14 pushes that above .05 before any data is seen. Measure it
# rather than argue about it: inject a known shift and find where each test
# fires.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from scipy.stats import norm

    print("\n" + "=" * 74)
    print("positive control on the robust tests (train, AMP metric)")
    sub = df[df.split == "train"].reset_index(drop=True)
    ctrl = {}
    for s in ("momentum_97", "vcp", "preset:4_bullish"):
        m = sub.screeners.str.contains(rf"(?:^|\|){s}(?:\||$)", regex=True).values
        base = deltas(sub, m, "adj", med)
        row = {}
        for shift in (0.05, 0.10, 0.20, 0.40, 0.80):
            d = base + shift - np.median(base)      # known shift, baseline removed
            pf = block_signflip(d)
            ph, _t = hac_p(d)
            row[f"+{shift:.2f}R"] = {"p_blockflip": round(pf, 4),
                                     "p_blockflip_x14": round(min(1, pf * 14), 4),
                                     "p_hac": round(ph, 5),
                                     "p_hac_x14": round(min(1, ph * 14), 5)}
        ctrl[s] = row
        print(f"  {s}")
        for k, v in row.items():
            print(f"    {k}  flip p={v['p_blockflip']:.4f} (x14 {v['p_blockflip_x14']:.3f})"
                  f"   HAC p={v['p_hac']:.5f} (x14 {v['p_hac_x14']:.5f})")
    n_blocks = int(np.ceil(67 / BLOCK))
    floor = 2.0 / (2 ** n_blocks)
    print(f"\n  sign-flip resolution floor: {n_blocks} blocks -> smallest two-sided p "
          f"~{floor:.4f}; x14 = {min(1, floor*14):.4f}")
    out["robust_positive_control"] = ctrl
    out["signflip_resolution"] = {"blocks": n_blocks, "min_two_sided_p": round(floor, 5),
                                  "min_after_holm14": round(min(1, floor * 14), 5)}
    json.dump(out, open(HERE / "results_robust.json", "w"), indent=1)
