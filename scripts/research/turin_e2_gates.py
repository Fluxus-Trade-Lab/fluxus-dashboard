"""E2 -- turin's RULES tested as gates (not table cuts), matched-baseline style.

Pre-registered NULL criteria (plan 3.2): gated vs un-gated distributions differ
with p > 0.05, or the direction contradicts his claim.

R1  washout-buy confirmation gate (his 2022-03-10 rule):
    "Every buyable low saw the NYSE cumulative AD line's 21d z-score cross
     above 0; buying dips while it is < 0 = bagholder."
    Test: dip days (SPX >= 3% below its 60d high, NYSE breadth 2007+),
    split by gate state z21>0 (allowed) vs z21<=0 (forbidden).
    Outcomes: fwd 21d / 63d return, fwd 63d max further drawdown (bagholder
    depth), P(further -5%).  Significance: Mann-Whitney on ONE observation per
    dip episode (first day of each episode; episodes = dip runs separated by
    >5 sessions) -- day-level rows overlap and would fake precision.
    His direction: forbidden days have worse fwd returns and deeper fwd min.

R3  VIX term-structure states as a VOL claim (his 2022-03-28 rule):
    VIX/VIX3M 3EMA: <0.8 complacency (hedges cheap & needed),
    0.8-1.0 neutral, >1.0 backwardation (fear/capitulation; short-vol zone,
    take off hedges).
    Test per state: fwd 21d vol expansion (fwd RV / trailing RV), fwd 21d
    %change in VIX, tail P(VIX +50% in 21d), fwd 21d SPX return.
    His directions: complacency -> vol expands (ratio > neutral state's);
    backwardation -> VIX falls over the next month (mean reversion) while
    left-tail risk stays elevated (we quantify, he implies).

Usage:  python3 scripts/research/turin_e2_gates.py
Inputs: .cache/risk/e1_inputs.pkl (from turin_e1_cuts.py) + data/reference/breadth_tv/
Output: data/research/turin_e2_results.json + printed summary
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache/risk/e1_inputs.pkl"
TVDIR = ROOT / "data/reference/breadth_tv"
OUT = ROOT / "data/research/turin_e2_results.json"

H1, H2 = 21, 63


def tv_series(name: str) -> pd.Series:
    s = pd.read_csv(TVDIR / f"{name}.csv", parse_dates=["date"]).set_index("date")["close"]
    return s[~s.index.duplicated(keep="last")]


def dist(x: pd.Series) -> dict:
    x = x.dropna()
    return {"n": int(len(x)), "mean": round(float(x.mean()), 4),
            "median": round(float(x.median()), 4),
            "p10": round(float(x.quantile(0.1)), 4), "p90": round(float(x.quantile(0.9)), 4)}


def main() -> None:
    raw = pd.read_pickle(CACHE)
    px = raw["^GSPC"].dropna()
    vix = raw["^VIX"].dropna()

    fwd21 = px.shift(-H1) / px - 1.0
    fwd63 = px.shift(-H2) / px - 1.0
    fmin63 = pd.concat([px.shift(-k) for k in range(1, H2 + 1)], axis=1).min(axis=1) / px - 1.0

    results = {}

    # ------------------------------------------------------------- R1 ----
    net = (tv_series("INDEX_ADVN") - tv_series("INDEX_DECN")).dropna()
    adl = net.cumsum()
    z21 = (adl - adl.rolling(21).mean()) / adl.rolling(21).std()

    d = pd.DataFrame({"px": px, "z": z21, "fwd21": fwd21, "fwd63": fwd63,
                      "fmin63": fmin63}).dropna(subset=["px", "z"])
    d["dip"] = d["px"] <= d["px"].rolling(60).max() * 0.97
    dips = d[d["dip"]].copy()
    # episode id: runs of dip days separated by >5 sessions
    pos = pd.Series(range(len(d)), index=d.index)
    gap = pos.loc[dips.index].diff().fillna(99)
    dips["ep"] = (gap > 5).cumsum()
    dips["allowed"] = dips["z"] > 0

    day_a, day_f = dips[dips["allowed"]], dips[~dips["allowed"]]
    # one obs per (episode x gate-state): the FIRST day in that state
    ep_first = dips.groupby(["ep", "allowed"]).head(1)
    ep_a = ep_first[ep_first["allowed"]]
    ep_f = ep_first[~ep_first["allowed"]]

    tests = {}
    for col, better_high in (("fwd21", True), ("fwd63", True), ("fmin63", True)):
        a, f = ep_a[col].dropna(), ep_f[col].dropna()
        u, p = mannwhitneyu(a, f, alternative="two-sided")
        # his direction: allowed better (higher return / shallower fwd min)
        direction_ok = bool(a.median() > f.median()) if better_high else bool(a.median() < f.median())
        tests[col] = {"p_mannwhitney_episode_level": round(float(p), 4),
                      "direction_matches_claim": direction_ok,
                      "allowed_median": round(float(a.median()), 4),
                      "forbidden_median": round(float(f.median()), 4),
                      "n_allowed": int(len(a)), "n_forbidden": int(len(f))}

    r1_pass = all(t["direction_matches_claim"] for t in tests.values()) and \
        any(t["p_mannwhitney_episode_level"] <= 0.05 for t in tests.values())
    results["R1_washout_gate"] = {
        "rule": "dip days (>=3% off 60d high) gated by NYSE cumAD 21d z > 0",
        "sample": {"from": str(d.index[0].date()), "to": str(d.index[-1].date()),
                   "dip_days": int(len(dips)), "episodes": int(dips["ep"].nunique()),
                   "allowed_days": int(len(day_a)), "forbidden_days": int(len(day_f))},
        "day_level_distributions": {
            "allowed": {c: dist(day_a[c]) for c in ("fwd21", "fwd63", "fmin63")},
            "forbidden": {c: dist(day_f[c]) for c in ("fwd21", "fwd63", "fmin63")},
            "P_further_5pct_dd_63d": {
                "allowed": round(float((day_a["fmin63"] <= -0.05).mean()), 4),
                "forbidden": round(float((day_f["fmin63"] <= -0.05).mean()), 4)},
        },
        "episode_level_tests": tests,
        "verdict": "PASS" if r1_pass else "NULL",
    }

    # ------------------------------------------------------------- R3 ----
    ts = (raw["^VIX"] / raw["^VIX3M"]).dropna().ewm(span=3).mean()
    lr = np.log(px).diff()
    rv_trail = lr.rolling(21).std() * np.sqrt(252) * 100
    rv_fwd = rv_trail.shift(-H1)
    dvix = vix.shift(-H1) / vix - 1.0
    vmax21 = pd.concat([vix.shift(-k) for k in range(1, H1 + 1)], axis=1).max(axis=1) / vix - 1.0

    r = pd.DataFrame({"ts": ts, "exp": rv_fwd / rv_trail, "dvix": dvix,
                      "vtail": vmax21, "fwd21": fwd21}).dropna(subset=["ts"])
    r["state"] = pd.cut(r["ts"], [-np.inf, 0.8, 1.0, np.inf], labels=["complacency", "neutral", "backwardation"])

    by_state = {}
    for s in ("complacency", "neutral", "backwardation"):
        g = r[r["state"] == s]
        by_state[s] = {
            "n": int(len(g)),
            "vol_expansion_ratio": dist(g["exp"]),
            "fwd21_vix_change": dist(g["dvix"]),
            "P_vix_spikes_50pct_21d": round(float((g["vtail"] >= 0.5).mean()), 4),
            "fwd21_spx_return": dist(g["fwd21"]),
        }

    comp, neut, back = (r[r["state"] == s] for s in ("complacency", "neutral", "backwardation"))
    u1, p1 = mannwhitneyu(comp["exp"].dropna(), neut["exp"].dropna(), alternative="two-sided")
    claim_a = {"claim": "complacency -> vol expansion ahead (vs neutral)",
               "direction_matches": bool(comp["exp"].median() > neut["exp"].median()),
               "p": round(float(p1), 4),
               "complacency_median": round(float(comp["exp"].median()), 3),
               "neutral_median": round(float(neut["exp"].median()), 3)}
    u2, p2 = mannwhitneyu(back["dvix"].dropna(), neut["dvix"].dropna(), alternative="two-sided")
    claim_b = {"claim": "backwardation -> VIX falls over next 21d (mean reversion, vs neutral)",
               "direction_matches": bool(back["dvix"].median() < neut["dvix"].median()),
               "p": round(float(p2), 4),
               "backwardation_median": round(float(back["dvix"].median()), 3),
               "neutral_median": round(float(neut["dvix"].median()), 3)}

    r3_pass = all(c["direction_matches"] and c["p"] <= 0.05 for c in (claim_a, claim_b))
    results["R3_vixts_vol_states"] = {
        "rule": "VIX/VIX3M 3EMA states 0.8 / 1.0 (turin thresholds verbatim)",
        "sample": {"from": str(r.index[0].date()), "to": str(r.index[-1].date()),
                   "sessions": int(len(r))},
        "by_state": by_state,
        "claims": {"a_complacency_vol_expands": claim_a, "b_backwardation_vix_reverts": claim_b},
        "verdict": "PASS" if r3_pass else "NULL",
        "note": "day-level Mann-Whitney; overlapping horizons inflate precision -- "
                "treat p as descriptive, directions + effect sizes as primary",
    }

    OUT.write_text(json.dumps(results, indent=2))

    # ------------------------------------------------------------ print --
    r1 = results["R1_washout_gate"]
    print(f"\n=== R1 washout gate  [{r1['verdict']}]  {r1['sample']['from']}->{r1['sample']['to']}")
    s = r1["sample"]
    print(f"    dip days {s['dip_days']} in {s['episodes']} episodes; allowed {s['allowed_days']} / forbidden {s['forbidden_days']}")
    dl = r1["day_level_distributions"]
    print(f"    day-level fwd21 median: allowed {dl['allowed']['fwd21']['median']:+.4f} vs forbidden {dl['forbidden']['fwd21']['median']:+.4f}")
    print(f"    day-level fmin63 median: allowed {dl['allowed']['fmin63']['median']:+.4f} vs forbidden {dl['forbidden']['fmin63']['median']:+.4f}")
    print(f"    P(further -5% within 63d): allowed {dl['P_further_5pct_dd_63d']['allowed']:.3f} vs forbidden {dl['P_further_5pct_dd_63d']['forbidden']:.3f}")
    for k, t in r1["episode_level_tests"].items():
        print(f"    episode-level {k}: allowed {t['allowed_median']:+.4f} vs forbidden {t['forbidden_median']:+.4f}  p={t['p_mannwhitney_episode_level']}  dir_ok={t['direction_matches_claim']}  (n={t['n_allowed']}/{t['n_forbidden']})")

    r3 = results["R3_vixts_vol_states"]
    print(f"\n=== R3 VIX-TS vol states  [{r3['verdict']}]  {r3['sample']['from']}->{r3['sample']['to']}  n={r3['sample']['sessions']}")
    for st, g in r3["by_state"].items():
        print(f"    {st:14s} n={g['n']:5d}  vol_exp med {g['vol_expansion_ratio']['median']:.3f}  dVIX med {g['fwd21_vix_change']['median']:+.3f}  P(VIX+50%) {g['P_vix_spikes_50pct_21d']:.3f}  fwd21 spx med {g['fwd21_spx_return']['median']:+.4f}")
    for _, c in r3["claims"].items():
        print(f"    claim: {c['claim']}  -> dir_ok={c['direction_matches']}  p={c['p']}")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
