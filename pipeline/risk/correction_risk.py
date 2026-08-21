"""Correction Risk -- P(S&P 500 draws down >= 5% within the next 21 sessions).

The Correction Risk slot on the Market page was published EMPTY with its
standard written on it: a probability WITH the base rate it is measured
against; a tail reading, not a direction call; two layers validated apart --
a base layer on inputs with decades of history, then breadth/gamma as an
overlay only on the window where they exist, never averaged in. This module
is the base layer.

What it is (2026-08-17 research, .cache/risk + this file):

    A CONDITIONAL BASE-RATE TABLE, not a fitted model.

    cell = (VIX quintile, above/below the 200-day SMA)
    value = historical frequency of a >= 5% drawdown inside the next 21
            sessions, 1990 -> today, ~199 distinct drawdown episodes.

    VIX quintile alone:  5.5% / 8.1% / 13.8% / 26.0% / 29.7%  (base 16.6%),
    monotone in BOTH half-samples (Spearman 0.9 / 1.0). Below the 200-day the
    upper quintiles roughly double (Q4: 39% vs 19% above).

Why a table and not a model: a 9-feature L2 logistic (VIX, term structure,
realised vol, 200/50-day distance, 21-day return, drawdown state, HYG/IEF
credit proxy), walk-forward by year 2013-2026, came out WORSE than the base
rate out of sample (Brier 0.133 vs 0.121, AUC 0.52) and its reliability
deciles were not monotone; the only components with out-of-sample skill were
VIX level and 200-day side, and only weakly (best AUC 0.63, Brier 1.3% better
than base). The table keeps exactly that skill, transparently, and adds no
parameters to overfit. The logistic remains here as `logistic_appendix()`
so the NULL is reproducible.

Inputs: ^GSPC and ^VIX from yfinance -- two series, both with history to
1990, both refreshable nightly. VIX3M / credit are NOT needed for the table
(they were only in the appendix model).

Not here: breadth and dealer gamma (2.2 years of history). regime.py's
validated read -- 5% drawdown frequency 27% in Damaged vs 6% in Extended
across 2024-2026 -- is the overlay, and it is reported beside this number
with its own window, not blended.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

HORIZON = 21
DD_THRESHOLD = -0.05
QUINTILES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
INPUTS = Path(".cache/risk/inputs.pkl")
OUTPUT = Path("data/output/correction_risk.json")
ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------ features --

def build_frame(inputs: pd.DataFrame) -> pd.DataFrame:
    """Feature matrix + label. Needs ^GSPC and ^VIX; the other columns
    (^VIX3M, HYG, IEF) are optional and only feed the logistic appendix."""
    px = inputs["^GSPC"].astype(float)
    f = pd.DataFrame(index=inputs.index)
    f["px"] = px
    f["vix"] = inputs["^VIX"].astype(float)
    f["d200"] = px / px.rolling(200).mean() - 1.0
    f["d50"] = px / px.rolling(50).mean() - 1.0
    lr = np.log(px).diff()
    f["rv20"] = lr.rolling(21).std() * np.sqrt(252) * 100
    f["rv_ratio"] = f["rv20"] / (lr.rolling(63).std() * np.sqrt(252) * 100)
    f["ret21"] = px / px.shift(21) - 1.0
    f["dd63"] = px / px.rolling(63).max() - 1.0
    if "^VIX3M" in inputs:
        f["term"] = inputs["^VIX"] / inputs["^VIX3M"] - 1.0
        # E1 2026-08-21: 3-day EMA of VIX/VIX3M, states <0.8 / 0.8-1.0 / >1.0
        # (turin thresholds verbatim) -- the only tested cut that beat the VIX
        # quintile spread on its own sample. Third table dimension since 08-21.
        f["ts_ema"] = (inputs["^VIX"] / inputs["^VIX3M"]).ewm(span=3).mean()
    if "HYG" in inputs and "IEF" in inputs:
        cr = np.log(inputs["HYG"] / inputs["IEF"])
        f["credit20"] = cr - cr.shift(20)
    fwd_min = pd.concat([px.shift(-k) for k in range(1, HORIZON + 1)], axis=1).min(axis=1) / px - 1.0
    f["fwd_min21"] = fwd_min
    f["y"] = (fwd_min <= DD_THRESHOLD).astype(float)
    f.loc[fwd_min.isna(), "y"] = np.nan
    return f


def episodes(y: pd.Series) -> int:
    """Distinct drawdown events: runs of y==1 separated by at least one 0."""
    v = y.fillna(0).astype(int).values
    if len(v) == 0:
        return 0
    return int(((v[1:] == 1) & (v[:-1] == 0)).sum() + (1 if v[0] == 1 else 0))


# --------------------------------------------------- the base-rate table --

def vix_edges(vix: pd.Series) -> List[float]:
    e = vix.quantile(QUINTILES).values.astype(float).copy()
    e[0] -= 1.0
    e[-1] += 1.0
    return [float(x) for x in e]


def quintile_of(v: float, edges: Sequence[float]) -> int:
    for q in range(1, 6):
        if edges[q - 1] < v <= edges[q]:
            return q
    return 5 if v > edges[-1] else 1


def conditional_table(f: pd.DataFrame) -> Dict:
    """Frequency of a 5% drawdown in the next 21 sessions by (VIX quintile,
    200-day side), with the half-sample check that is our house standard."""
    d = f.dropna(subset=["vix", "d200", "y"]).copy()
    edges = vix_edges(d["vix"])
    d["vq"] = [quintile_of(v, edges) for v in d["vix"]]
    d["above200"] = d["d200"] > 0
    mid = d.index[len(d) // 2]
    halves = {"first": d[d.index < mid], "second": d[d.index >= mid]}

    def by_q(g):
        t = g.groupby("vq")["y"].agg(["mean", "count"])
        return {int(q): {"rate": round(float(t.loc[q, "mean"]), 4), "n": int(t.loc[q, "count"])}
                for q in t.index}

    def mono(g):
        t = g.groupby("vq")["y"].mean()
        return round(float(t.corr(pd.Series(range(len(t)), index=t.index), method="spearman")), 2)

    t2 = d.groupby(["vq", "above200"])["y"].agg(["mean", "count"])
    cells = {}
    for (q, ab), r in t2.iterrows():
        cells[f"Q{q}_{'above' if ab else 'below'}200"] = {"rate": round(float(r["mean"]), 4), "n": int(r["count"])}
    return {
        "sample": {"from": str(d.index[0].date()), "to": str(d.index[-1].date()),
                   "sessions": int(len(d)), "episodes": episodes(d["y"]),
                   "half_split": str(mid.date())},
        "base_rate": round(float(d["y"].mean()), 4),
        "vix_edges": [round(x, 2) for x in edges],
        "by_vix_quintile": {"full": by_q(d), "first_half": by_q(halves["first"]),
                            "second_half": by_q(halves["second"])},
        "monotone_spearman": {"full": mono(d), "first_half": mono(halves["first"]),
                              "second_half": mono(halves["second"])},
        "by_vix_quintile_x_200dma": cells,
    }


def ts_state_of(v: float) -> int:
    return 1 if v < 0.8 else (2 if v <= 1.0 else 3)


TS_LABELS = {1: "complacency(<0.8)", 2: "neutral(0.8-1.0)", 3: "backwardation(>1.0)"}


def ts_table(f: pd.DataFrame) -> Optional[Dict]:
    """Third dimension (2026-08-21, Andy-approved): VIX quintile x 200-day side
    x VIX/VIX3M-3EMA state. Sample is shorter (VIX3M history); the classic
    two-dim table above stays the headline. House checks re-run on this sample."""
    if "ts_ema" not in f.columns:
        return None
    d = f.dropna(subset=["vix", "d200", "ts_ema", "y"]).copy()
    if len(d) < 1000:
        return None
    edges = vix_edges(d["vix"])
    d["vq"] = [quintile_of(v, edges) for v in d["vix"]]
    d["above200"] = d["d200"] > 0
    d["ts"] = [ts_state_of(v) for v in d["ts_ema"]]
    mid = d.index[len(d) // 2]
    halves = {"first": d[d.index < mid], "second": d[d.index >= mid]}

    def ts_rates(g):
        t = g.groupby("ts")["y"].agg(["mean", "count"])
        return {int(s): {"rate": round(float(t.loc[s, "mean"]), 4), "n": int(t.loc[s, "count"])}
                for s in t.index}

    def mono(g):
        t = g.groupby("ts")["y"].mean()
        return round(float(t.corr(pd.Series(range(len(t)), index=t.index), method="spearman")), 2)

    cells = {}
    for (q, ab, s), r in d.groupby(["vq", "above200", "ts"])["y"].agg(["mean", "count"]).iterrows():
        cells[f"Q{q}_{'above' if ab else 'below'}200_ts{s}"] = {
            "rate": round(float(r["mean"]), 4), "n": int(r["count"])}
    return {
        "sample": {"from": str(d.index[0].date()), "to": str(d.index[-1].date()),
                   "sessions": int(len(d)), "episodes": episodes(d["y"]),
                   "base_rate": round(float(d["y"].mean()), 4)},
        "vix_edges_this_sample": [round(x, 2) for x in edges],
        "ts_state_labels": TS_LABELS,
        "by_ts_state": {"full": ts_rates(d), "first_half": ts_rates(halves["first"]),
                        "second_half": ts_rates(halves["second"])},
        "ts_monotone_spearman": {"full": mono(d), "first_half": mono(halves["first"]),
                                 "second_half": mono(halves["second"])},
        "by_vix_quintile_x_200dma_x_ts": cells,
    }


def ts_today(f: pd.DataFrame, t3: Dict) -> Optional[Dict]:
    if t3 is None or "ts_ema" not in f.columns:
        return None
    d = f.dropna(subset=["vix", "d200", "ts_ema"])
    if d.empty:
        return None
    last = d.iloc[-1]
    stale_days = int((f.index[-1] - d.index[-1]).days)
    q = quintile_of(float(last["vix"]), [e for e in t3["vix_edges_this_sample"]])
    s = ts_state_of(float(last["ts_ema"]))
    key = f"Q{q}_{'above' if last['d200'] > 0 else 'below'}200_ts{s}"
    cell = t3["by_vix_quintile_x_200dma_x_ts"].get(key) or {"rate": None, "n": 0}
    return {"date": str(d.index[-1].date()), "ts_ema": round(float(last["ts_ema"]), 3),
            "ts_state": s, "ts_label": TS_LABELS[s],
            "prob_3d": cell["rate"], "n_cell_3d": cell["n"],
            "prob_ts_only": t3["by_ts_state"]["full"].get(s, {}).get("rate"),
            "input_staleness_days": stale_days,
            "stale_warning": stale_days > 7}


# ------------------------------------------------- side readings (旁注) --

def side_readings(root: Path) -> Dict:
    """NHNL and GEX states beside the table -- never averaged into `prob`.
    E1 2026-08-21: nhnl3 (KY thresholds) beat the VIX spread; GEX rolling-252
    percentile passed monotone within every VIX tercile. Both read from local
    files maintained by other jobs; absent or stale files degrade gracefully."""
    out = {"note": "annotations only; not part of prob. Historical rates from "
                   "scripts/research/turin_e1_cuts.py (data/research/turin_e1_results.json)"}
    try:  # NHNL (TV export, scripts/research/fetch_tv_breadth.py)
        hi = pd.read_csv(root / "data/reference/breadth_tv/INDEX_HIGN.csv",
                         parse_dates=["date"]).set_index("date")["close"]
        lo = pd.read_csv(root / "data/reference/breadth_tv/INDEX_LOWN.csv",
                         parse_dates=["date"]).set_index("date")["close"]
        r = (hi / (hi + lo)).dropna().ewm(span=10).mean()
        v = float(r.iloc[-1])
        state = "oversold(<0.30)" if v < 0.30 else ("overbought(>0.85)" if v > 0.85 else "mid")
        hist = {"oversold(<0.30)": 0.372, "mid": 0.194, "overbought(>0.85)": 0.091}
        out["nhnl"] = {"date": str(r.index[-1].date()), "ratio_10ema": round(v, 3),
                       "state": state, "hist_rate_e1": hist[state]}
    except Exception as e:
        out["nhnl"] = {"unavailable": str(e)[:80]}
    try:  # GEX (SqueezeMetrics DIX.csv, refresh via curl -- see reference memory)
        sm = pd.read_csv(root / "SqueezeMetrics/DIX.csv", parse_dates=["date"]).set_index("date")
        gexn = (sm["gex"] / (sm["price"] ** 2)).dropna()
        w = gexn.tail(252)
        pr = float((w <= gexn.iloc[-1]).mean())
        quint = min(int(pr * 5) + 1, 5)
        hist = {1: 0.212, 2: 0.158, 3: 0.114, 4: 0.105, 5: 0.089}
        out["gex"] = {"date": str(sm.index[-1].date()), "pct_rank_252d": round(pr, 3),
                      "quintile": quint, "hist_rate_e1": hist[quint]}
    except Exception as e:
        out["gex"] = {"unavailable": str(e)[:80]}
    return out


def today_reading(f: pd.DataFrame, table: Dict) -> Dict:
    """Today's cell and its historical frequency -- the number the page shows."""
    last = f.dropna(subset=["vix", "d200"]).iloc[-1]
    q = quintile_of(float(last["vix"]), table["vix_edges"])
    ab = bool(last["d200"] > 0)
    key = f"Q{q}_{'above' if ab else 'below'}200"
    cell = table["by_vix_quintile_x_200dma"].get(key) or {"rate": None, "n": 0}
    qcell = table["by_vix_quintile"]["full"][q]
    return {
        "date": str(f.dropna(subset=["vix", "d200"]).index[-1].date()),
        "spx_close": round(float(f["px"].dropna().iloc[-1]), 2) if "px" in f.columns else None,
        "vix": round(float(last["vix"]), 2), "vix_quintile": q,
        "above_200dma": ab, "d200": round(float(last["d200"]), 4),
        "prob": cell["rate"], "n_cell": cell["n"],
        "prob_vix_only": qcell["rate"], "n_vix_only": qcell["n"],
        "base_rate": table["base_rate"],
    }


# ---------------------------------------------- logistic appendix (NULL) --

def _fit_logit(X: np.ndarray, y: np.ndarray, l2: float = 1.0) -> np.ndarray:
    from scipy.optimize import minimize
    n, k = X.shape
    Xb = np.c_[np.ones(n), X]
    def nll(w):
        z = Xb @ w
        return np.sum(np.logaddexp(0, -z) * y + np.logaddexp(0, z) * (1 - y)) + 0.5 * l2 * np.sum(w[1:] ** 2)
    def grad(w):
        p = 1.0 / (1.0 + np.exp(-(Xb @ w)))
        g = Xb.T @ (p - y); g[1:] += l2 * w[1:]
        return g
    return minimize(nll, np.zeros(k + 1), jac=grad, method="L-BFGS-B").x


def _auc(y: np.ndarray, p: np.ndarray) -> Optional[float]:
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    order = np.argsort(np.r_[pos, neg]); ranks = np.empty(len(order)); ranks[order] = np.arange(1, len(order) + 1)
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def walk_forward(f: pd.DataFrame, features: Sequence[str], first_test_year: int, l2: float = 1.0):
    d = f.dropna(subset=list(features) + ["y"])
    probs = pd.Series(np.nan, index=d.index)
    for yr in sorted({y for y in d.index.year if y >= first_test_year}):
        tr, te = d[d.index.year < yr], d[d.index.year == yr]
        if len(tr) < 250 or len(te) == 0:
            continue
        mu, sd = tr[list(features)].mean(), tr[list(features)].std().replace(0, 1)
        w = _fit_logit(((tr[list(features)] - mu) / sd).values, tr["y"].values, l2)
        probs.loc[te.index] = 1.0 / (1.0 + np.exp(-(np.c_[np.ones(len(te)), ((te[list(features)] - mu) / sd).values] @ w)))
    return probs


def logistic_appendix(f: pd.DataFrame, first_test_year: int = 2013) -> Dict:
    """The model we did NOT ship, kept reproducible: out-of-sample Brier/AUC
    for the 9-feature logistic and for VIX alone."""
    out = {}
    for name, feats, l2 in (("full_9", ["vix", "term", "rv20", "rv_ratio", "d200", "d50", "ret21", "dd63", "credit20"], 1.0),
                            ("vix_d200", ["vix", "d200"], 5.0), ("vix_only", ["vix"], 5.0)):
        if not all(c in f.columns for c in feats):
            continue
        p = walk_forward(f, feats, first_test_year, l2).dropna()
        y = f.loc[p.index, "y"].values
        out[name] = {"auc": round(_auc(y, p.values), 3), "brier": round(float(np.mean((p.values - y) ** 2)), 4),
                     "brier_base_rate": round(float(np.mean((y.mean() - y) ** 2)), 4), "n_oos": int(len(p))}
    return out


# -------------------------------------------------------------- report --

def run(inputs: pd.DataFrame, with_appendix: bool = True) -> Dict:
    f = build_frame(inputs)
    table = conditional_table(f)
    today = today_reading(f, table)
    rep = {
        "date": today["date"],
        "question": "P(S&P 500 closes >= 5% below today's close at some point in the next 21 sessions)",
        "method": "conditional base rate: (VIX quintile, above/below 200-day SMA) -> historical frequency; no fitted parameters",
        "prob": today["prob"],
        "base_rate": today["base_rate"],
        "today": today,
        "table": table,
        "overlay": {
            "note": "breadth/gamma layer is NOT in `prob`; regime.py's validated read is reported here with its own window and never averaged in",
            "regime_bands_2024_2026": {"damaged": 0.272, "extended": 0.058,
                                       "source": "pipeline/screeners/regime.py docstring, 558 sessions, ~10 independent episodes"},
        },
        "predicts_return": False,
        "separates_tail": True,
        "caveats": [
            "Tail reading, not a direction call: it answers how often a 5% drawdown followed this state, never which way to lean.",
            "A table, not a model: VIX quintile x 200-day side. A 9-feature logistic was worse than the base rate out of sample (see appendix) -- the honest skill lives in these two variables and is modest.",
            "Cells are unequal: Q1/Q2 below the 200-day are rare (n < 130); read n_cell beside prob.",
            "Quintile edges are set on the full 1990-> sample; the half-sample check shows the ordering holds in both halves.",
            "Overlapping 21-day windows: sessions are not independent -- the episode count is the sample size that matters.",
        ],
    }
    # 2026-08-21 expansion (Andy-approved; page still NOT wired -- parked):
    # third dimension VIX-TS, plus NHNL/GEX side readings. Classic two-dim
    # table and `prob` above are unchanged.
    t3 = ts_table(f)
    if t3 is not None:
        rep["ts_dimension"] = {"table": t3, "today": ts_today(f, t3),
                               "provenance": "E1 2026-08-21 (turin study): only cut that beat "
                                             "the VIX-quintile spread on its own sample; "
                                             "interacts with VIX level -- read the 3d cell, not ts alone"}
    rep["side_readings"] = side_readings(ROOT)
    if with_appendix:
        rep["appendix_logistic_oos"] = logistic_appendix(f)
    return rep


def fetch_inputs(with_appendix: bool = False) -> pd.DataFrame:
    """^GSPC and ^VIX from yfinance (history to 1990); optional VIX3M (CBOE)
    and HYG/IEF for the appendix. The nightly run uses the two-series form."""
    import yfinance as yf
    def yfc(sym, start):
        d = yf.download(sym, start=start, progress=False, auto_adjust=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = [c[0] for c in d.columns]
        return d["Close"].dropna().rename(sym)
    parts = [yfc("^GSPC", "1985-01-01"), yfc("^VIX", "1990-01-01")]
    # ^VIX3M feeds the TS dimension (2026-08-21) so it is fetched on every run:
    # yfinance gives 2006+ but its tail has gone stale (observed stuck at
    # 2026-07-17); the CBOE CSV is 2009+ and current. Merge, CBOE wins overlaps.
    v3_parts = []
    try:
        v3_parts.append(yfc("^VIX3M", "2006-01-01"))
    except Exception:
        pass
    try:
        import io, requests
        c = requests.get("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv", timeout=30).text
        v3_parts.append(pd.read_csv(io.StringIO(c), parse_dates=["DATE"], index_col="DATE")["CLOSE"].rename("^VIX3M"))
    except Exception:
        pass
    if v3_parts:
        v3 = v3_parts[-1] if len(v3_parts) == 1 else v3_parts[1].combine_first(v3_parts[0])
        parts.append(v3.rename("^VIX3M"))
    if with_appendix:
        for sym in ("HYG", "IEF"):
            try:
                d = yf.download(sym, start="2007-01-01", progress=False, auto_adjust=True)
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = [c[0] for c in d.columns]
                parts.append(d["Close"].dropna().rename(sym))
            except Exception:
                pass
    return pd.concat(parts, axis=1).sort_index().dropna(subset=["^GSPC"])


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="download inputs instead of reading the cache")
    ap.add_argument("--no-appendix", action="store_true")
    a = ap.parse_args()
    inputs = fetch_inputs(with_appendix=not a.no_appendix) if a.fetch or not INPUTS.exists() else pd.read_pickle(INPUTS)
    _main_from(inputs, with_appendix=not a.no_appendix)


def _main_from(inputs: pd.DataFrame, with_appendix: bool = True) -> Dict:
    rep = run(inputs, with_appendix=with_appendix)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(rep, indent=2))
    return rep


def _legacy_main() -> None:
    inputs = pd.read_pickle(INPUTS)
    rep = _main_from(inputs)
    t = rep["today"]; tb = rep["table"]
    print(f"{rep['date']}  VIX {t['vix']} (Q{t['vix_quintile']}), {'above' if t['above_200dma'] else 'below'} 200dma "
          f"-> P(5% dd/21d) = {t['prob']:.3f} (n={t['n_cell']})   vix-only {t['prob_vix_only']:.3f}   base {t['base_rate']:.3f}")
    print(f"  sample {tb['sample']['from']}..{tb['sample']['to']}, episodes {tb['sample']['episodes']}, "
          f"monotone ρ full/first/second {tb['monotone_spearman']}")
    print("  by quintile:", {q: v['rate'] for q, v in tb['by_vix_quintile']['full'].items()})
    if "appendix_logistic_oos" in rep:
        print("  appendix (oos):", rep["appendix_logistic_oos"])


if __name__ == "__main__":
    main()
