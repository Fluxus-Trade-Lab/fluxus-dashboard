"""LanceB reversal checklist: does stacking more variables move the median,
or only fatten the right tail?  Pre-registration: prereg.md (commit 530760a7).

    python3 data/research/reversal_checklist_2026-09/study.py --arm discovery
    python3 data/research/reversal_checklist_2026-09/study.py --arm discovery --placebo 100
    python3 data/research/reversal_checklist_2026-09/study.py --arm holdout
    python3 data/research/reversal_checklist_2026-09/study.py --arm discovery --sensitivity

Every number in results.md comes out of this file (tables are printed, not
typed).  Close-only panel, so four of LanceB's ten variables are testable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PANEL = next((c for c in (ROOT / ".cache/stock_panel.pkl",
                          Path.home() / "Documents/AI-Trading-System/.cache/stock_panel.pkl")
              if c.exists()), None)

BASE_DROP = -0.10       # r5 <= -10%   (self-made entry gate, prereg §2)
MIN_PRICE = 5.0
REFRACTORY = 10         # sessions
HORIZON = 5
ACCEL_SHARE = 0.6       # V1, self-made (prereg §3)
BB_N, BB_K = 20, 2.0    # V3, ChartSchool %B default
BREADTH_MA, BREADTH_OVERSOLD = 50, 0.30   # V8, ChartSchool percent-above-MA
DEPTH_EDGES = (-0.15, -0.25)              # strata: (-15,-10] (-25,-15] <=-25
SALT = "rev0912"
TAIL = 0.10
CRASH_WINDOWS = (("2020-02-20", "2020-04-30"), ("2025-03-26", "2025-05-15"))


def load_panel():
    s = pd.read_pickle(PANEL)
    spy = s["SPY"].astype(float)
    px = s.drop(columns=["SPY"]).astype(float)
    return px, spy


def features(px: pd.DataFrame, spy: pd.Series):
    """All features at t use closes up to and including t; outcomes use t+1.."""
    r5 = px / px.shift(5) - 1
    l3 = np.log(px / px.shift(3))
    l10 = np.log(px / px.shift(10))
    v1 = (l10 < 0) & ((l3 / l10) >= ACCEL_SHARE)
    v2 = (px < px.shift(1)) & (px.shift(1) < px.shift(2)) & (px.shift(2) < px.shift(3))
    sma = px.rolling(BB_N).mean()
    sd = px.rolling(BB_N).std(ddof=0)
    lower, upper = sma - BB_K * sd, sma + BB_K * sd
    pctb = (px - lower) / (upper - lower)
    v3 = pctb < 0
    ma50 = px.rolling(BREADTH_MA).mean()
    valid = ma50.notna() & px.notna()
    above = ((px > ma50) & valid).sum(axis=1) / valid.sum(axis=1).replace(0, np.nan)
    v8 = pd.DataFrame(np.repeat((above < BREADTH_OVERSOLD).values[:, None], px.shape[1], axis=1),
                      index=px.index, columns=px.columns)
    spy_fwd = spy.shift(-HORIZON) / spy - 1
    x5 = (px.shift(-HORIZON) / px - 1).sub(spy_fwd, axis=0)
    return dict(r5=r5, v1=v1, v2=v2, v3=v3, v8=v8, x5=x5, pctb=pctb, breadth=above)


def second_entry(pxa: np.ndarray, spya: np.ndarray, i: int, j: int):
    """'Right side of the V' daily proxy: enter on the first up close within
    t+1..t+3, exit HORIZON sessions later.  None = no entry."""
    n = pxa.shape[0]
    for e in range(i + 1, min(i + 4, n)):
        if pxa[e, j] > pxa[e - 1, j]:
            x = e + HORIZON
            if x >= n or np.isnan(pxa[x, j]):
                return np.nan
            return pxa[x, j] / pxa[e, j] - 1 - (spya[x] / spya[e] - 1)
    return None


def events(px, spy, f):
    base = (f["r5"] <= BASE_DROP) & (px >= MIN_PRICE)
    B = base.values
    pxa, spya = px.values, spy.values
    # .values on a DataFrame copies the whole frame; take each array once
    # (the first draft did it per event and never finished).
    X5, R5 = f["x5"].values, f["r5"].values
    V1, V2, V3, V8 = (f[v].values for v in ("v1", "v2", "v3", "v8"))
    rows = []
    dates = px.index
    for j, tk in enumerate(px.columns):
        last = -10 ** 9
        for i in np.flatnonzero(B[:, j]):
            if i - last < REFRACTORY:
                continue
            last = i
            x5 = X5[i, j]
            if np.isnan(x5):
                continue
            k = int(V1[i, j]) + int(V2[i, j]) + int(V3[i, j]) + int(V8[i, j])
            se = second_entry(pxa, spya, i, j)
            rows.append((tk, dates[i], float(R5[i, j]), k,
                         bool(V1[i, j]), bool(V2[i, j]), bool(V3[i, j]), bool(V8[i, j]),
                         float(x5), np.nan if se is None else float(se), se is None))
    ev = pd.DataFrame(rows, columns=["ticker", "date", "r5", "k", "v1", "v2", "v3", "v8",
                                     "x5", "x5_v", "no_entry"])
    ev["holdout"] = ev["ticker"].map(
        lambda t: int(hashlib.md5((t + SALT).encode()).hexdigest(), 16) % 10 < 3)
    ev["stratum"] = np.select([ev["r5"] > DEPTH_EDGES[0], ev["r5"] > DEPTH_EDGES[1]], [0, 1], 2)
    iso = ev["date"].dt.isocalendar()
    ev["week"] = (iso["year"].astype(int) * 100 + iso["week"].astype(int))
    return ev


# ---------- statistics -------------------------------------------------------

def _wmedian(sorted_vals, w):
    """Weighted median, w shaped (B, n) aligned with sorted_vals (n,)."""
    cw = np.cumsum(w, axis=1)
    tot = cw[:, -1]
    idx = (cw < (tot / 2.0)[:, None]).sum(axis=1)
    idx = np.minimum(idx, len(sorted_vals) - 1)
    out = sorted_vals[idx]
    out[tot == 0] = np.nan
    return out


def stratified(ev: pd.DataFrame, col: str, week_counts=None, week_ix=None):
    """Weighted-by-stratum-size difference (k>=3 minus k<=1) of the median and
    of P(x>=+10%).  With week_counts (B, W) it is evaluated per bootstrap draw."""
    lo, hi = ev["k"] <= 1, ev["k"] >= 3
    med_parts, tail_parts, weights = [], [], []
    for s in sorted(ev["stratum"].unique()):   # 0/1/2 in the pre-registered run
        cell = ev["stratum"] == s
        a, b = ev[cell & lo], ev[cell & hi]
        a, b = a[a[col].notna()], b[b[col].notna()]
        if len(a) == 0 or len(b) == 0:
            continue
        res = []
        for g in (b, a):
            order = np.argsort(g[col].values)
            v = g[col].values[order]
            if week_counts is None:
                w = np.ones((1, len(v)))
            else:
                w = week_counts[:, week_ix.loc[g.index].values[order]]
            med = _wmedian(v, w)
            tail = (w * (v >= TAIL)).sum(axis=1) / np.maximum(w.sum(axis=1), 1e-12)
            size = w.sum(axis=1)
            res.append((med, tail, size))
        (mb, tb, nb), (ma, ta, na) = res
        med_parts.append(mb - ma)
        tail_parts.append(tb - ta)
        weights.append(nb + na)
    W = np.vstack(weights)
    dm = (np.vstack(med_parts) * W).sum(axis=0) / W.sum(axis=0)
    dt = (np.vstack(tail_parts) * W).sum(axis=0) / W.sum(axis=0)
    return dm, dt


def bootstrap(ev, col, B=2000, seed=0):
    rng = np.random.default_rng(seed)
    weeks = np.sort(ev["week"].unique())
    week_ix = ev["week"].map({w: i for i, w in enumerate(weeks)})
    dms, dts = [], []
    for start in range(0, B, 100):
        b = min(100, B - start)
        draws = rng.integers(0, len(weeks), size=(b, len(weeks)))
        counts = np.zeros((b, len(weeks)))
        np.add.at(counts, (np.repeat(np.arange(b), len(weeks)), draws.ravel()), 1)
        dm, dt = stratified(ev, col, counts, week_ix)
        dms.append(dm)
        dts.append(dt)
    dm, dt = np.concatenate(dms), np.concatenate(dts)
    q = lambda a: [float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5))]
    return q(dm), q(dt), len(weeks)


def placebo(ev, col, n=100, B=300, seed=1, scope="stratum"):
    """Shuffle k, then report how often the week-cluster CI excludes 0.

    scope="stratum": shuffle within depth stratum across all dates -- k then
    carries no information at all, so ~5% is the calibration target.
    scope="week": shuffle within (week, stratum) -- this is NOT a null for the
    pre-registered statistic: it keeps which weeks the k>=3 events fall in,
    and V8 is a date-level variable.  The first calibration run used it by
    mistake (100% of tail CIs excluded 0); kept as the market-timing-only
    reference, labelled post hoc in results.md."""
    rng = np.random.default_rng(seed)
    hits_m = hits_t = 0
    pts, pts_t = [], []
    keys = ["stratum"] if scope == "stratum" else ["week", "stratum"]
    for p in range(n):
        e = ev.copy()
        e["k"] = e.groupby(keys)["k"].transform(
            lambda s: rng.permutation(s.values))
        dm, dt = stratified(e, col)
        pts.append(float(dm[0]))
        pts_t.append(float(dt[0]))
        cm, ct, _ = bootstrap(e, col, B=B, seed=seed + 100 + p)
        hits_m += (cm[0] > 0) or (cm[1] < 0)
        hits_t += (ct[0] > 0) or (ct[1] < 0)
    return dict(scope=scope, n=n, B=B, frac_ci_excludes0_median=hits_m / n,
                frac_ci_excludes0_tail=hits_t / n,
                point_q025=float(np.percentile(pts, 2.5)),
                point_q975=float(np.percentile(pts, 97.5)),
                point_mean=float(np.mean(pts)),
                tail_point_q025=float(np.percentile(pts_t, 2.5)),
                tail_point_q975=float(np.percentile(pts_t, 97.5)),
                tail_point_mean=float(np.mean(pts_t)))


def by_k(ev, col):
    out = []
    for k in range(5):
        g = ev.loc[ev["k"] == k, col].dropna()
        if len(g) == 0:
            continue
        out.append(dict(k=k, n=int(len(g)), median=float(g.median()), mean=float(g.mean()),
                        win=float((g > 0).mean()), p_up10=float((g >= TAIL).mean()),
                        p_dn10=float((g <= -TAIL).mean())))
    return out


def by_var(ev, col):
    out = []
    for v in ("v1", "v2", "v3", "v8"):
        for flag in (True, False):
            g = ev.loc[ev[v] == flag, col].dropna()
            out.append(dict(var=v, on=flag, n=int(len(g)), median=float(g.median()),
                            p_up10=float((g >= TAIL).mean()), p_dn10=float((g <= -TAIL).mean())))
    return out


def md_table(rows, cols):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    fmt = lambda v: (f"{v:+.2%}" if isinstance(v, float) and abs(v) < 5 else str(v))
    return head + "".join("| " + " | ".join(fmt(r[c]) for c in cols) + " |\n" for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["discovery", "holdout"], required=True)
    ap.add_argument("--placebo", type=int, default=0)
    ap.add_argument("--placebo-scope", choices=["stratum", "week"], default="stratum")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--B", type=int, default=2000)
    a = ap.parse_args()

    px, spy = load_panel()
    f = features(px, spy)
    ev_all = events(px, spy, f)
    ev = ev_all[ev_all["holdout"] == (a.arm == "holdout")].copy()
    rep = dict(arm=a.arm, panel=str(PANEL), n_events_all=int(len(ev_all)), n_events=int(len(ev)),
               n_tickers=int(ev["ticker"].nunique()),
               k_counts={int(k): int(v) for k, v in ev["k"].value_counts().sort_index().items()},
               strata_counts={int(k): int(v) for k, v in ev["stratum"].value_counts().sort_index().items()})

    if a.placebo:
        rep["placebo"] = placebo(ev, "x5", n=a.placebo, scope=a.placebo_scope)
        print(json.dumps(rep["placebo"], indent=1))
        (HERE / f"placebo_{a.arm}_{a.placebo_scope}.json").write_text(json.dumps(rep, indent=1))
        return

    cols = ["x5", "x5_v"]
    if a.sensitivity:
        m = pd.Series(False, index=ev.index)
        for s, e in CRASH_WINDOWS:
            m |= (ev["date"] >= s) & (ev["date"] <= e)
        rep["crash_excluded_n"] = int(m.sum())
        ev = ev[~m]
        rep["n_events"] = int(len(ev))   # header must show what was tested
        rep["n_tickers"] = int(ev["ticker"].nunique())
    for col in cols:
        dm, dt = stratified(ev, col)
        cm, ct, nw = bootstrap(ev, col, B=a.B)
        rep[col] = dict(HL_median_diff=float(dm[0]), HL_ci=cm, HM_tail_diff=float(dt[0]), HM_ci=ct,
                        weeks=nw, by_k=by_k(ev, col), by_var=by_var(ev, col))
    rep["no_entry_share"] = float(ev["no_entry"].mean())
    tag = a.arm + ("_ex_crash" if a.sensitivity else "")
    (HERE / f"results_{tag}.json").write_text(json.dumps(rep, indent=1, default=str))

    lines = [f"### {tag} · 事件 {rep['n_events']:,} · 票 {rep['n_tickers']:,}\n"]
    for col in cols:
        r = rep[col]
        lines.append(f"**{col}**（{'信号日收盘进' if col == 'x5' else '等第一个上涨收盘再进'}）· 周簇 {r['weeks']}\n")
        lines.append(md_table(r["by_k"], ["k", "n", "median", "mean", "win", "p_up10", "p_dn10"]))
        lines.append(f"\nH-L 分层中位差（k≥3 − k≤1）= {r['HL_median_diff']:+.2%}，95% 周簇区间 "
                     f"[{r['HL_ci'][0]:+.2%}, {r['HL_ci'][1]:+.2%}]\n")
        lines.append(f"H-M 分层右尾差 P(≥+10%) = {r['HM_tail_diff']:+.2%}，95% 周簇区间 "
                     f"[{r['HM_ci'][0]:+.2%}, {r['HM_ci'][1]:+.2%}]\n")
        lines.append("\n单变量开/关：\n\n" + md_table(r["by_var"], ["var", "on", "n", "median", "p_up10", "p_dn10"]) + "\n")
    lines.append(f"次结果 3 天内没有上涨收盘（不进场）占比 {rep['no_entry_share']:.1%}\n")
    (HERE / f"tables_{tag}.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
