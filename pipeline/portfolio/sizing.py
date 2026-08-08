#!/usr/bin/env python3
"""Sizing optimization — (half) Kelly + progressive exposure, on the real log.

Two lenses on "how big should the bets be":

1. KELLY — the growth-optimal bet size.
   * per-trade: the fraction f of equity to risk as 1R that maximizes
     Σ log(1 + f·R_i) over the empirical R-multiple distribution (log-optimal).
   * portfolio: the leverage λ*=μ/σ² on the actual daily MTM return stream.
   Full Kelly on a fat right tail + a bull run is degenerate (says "lever up
   hugely") — so half-Kelly and heavy caveats. The usable number is the RATIO to
   what you actually did, plus the reminder that Kelly assumes the edge is real
   and stationary.

2. PROGRESSIVE EXPOSURE — scale the book with regime instead of a static size.
   Backtests two pre-specified, theory-motivated overlays on the daily equity
   curve (no per-rule tuning): an equity-vs-20d-MA gate and a drawdown ladder.
   Reports CAGR / MaxDD / Sharpe / Calmar vs the un-overlaid baseline.

Run:  python -m pipeline.portfolio.sizing
"""
from __future__ import annotations

import math
import random
import statistics as st

PPY = 252
RF = 0.04


# --------------------------------------------------------------------------- #
# Position-sizing-to-OBJECTIVES (Van Tharp) — Monte-Carlo over the R-distribution
# --------------------------------------------------------------------------- #
def _sim(Rs, f, n_trades, n_sims, seed):
    """Bootstrap-resample R and compound equity by (1 + f·R) each trade.
    Returns (final_multiples, max_drawdowns) across n_sims paths."""
    rng = random.Random(seed)
    m = len(Rs)
    finals, mdds = [], []
    for _ in range(n_sims):
        eq = peak = 1.0
        mdd = 0.0
        for _ in range(n_trades):
            eq *= (1 + f * Rs[rng.randrange(m)])
            if eq <= 0:
                eq = 1e-12
            if eq > peak:
                peak = eq
            d = eq / peak - 1
            if d < mdd:
                mdd = d
        finals.append(eq)
        mdds.append(mdd)
    return finals, mdds


def sizing_objective_curves(Rs, years, risk_grid=None, n_sims=800, seed=7):
    """For each risk-per-trade %, the MC-median CAGR, median max-DD, and P(ruin).
    Ruin = drawdown worse than 50%. Also risk-of-ruin under Base / Pessimistic
    (edge haircut −0.3R) / Zero-edge (demeaned) R-distributions."""
    Rs = [r for r in Rs if r is not None]
    if len(Rs) < 20:
        return None
    n = len(Rs)
    tpy = n / years if years > 0 else n
    if risk_grid is None:
        risk_grid = [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015,
                     0.02, 0.025, 0.03, 0.04, 0.05]
    mean = st.mean(Rs)
    variants = {"Base (historical)": Rs,
                "Pessimistic (−0.3R)": [r - 0.3 for r in Rs],
                "Zero edge": [r - mean for r in Rs]}
    curve, ruin = [], {k: [] for k in variants}
    for f in risk_grid:
        finals, mdds = _sim(Rs, f, n, n_sims, seed)
        med_final = st.median(finals)
        cagr = (med_final ** (tpy / n) - 1) * 100 if med_final > 0 else -99.9
        curve.append({"risk": f * 100, "cagr": cagr,
                      "dd": st.median(mdds) * 100,
                      "ruin": sum(1 for d in mdds if d < -0.5) / n_sims * 100})
        for name, rr in variants.items():
            _, md = _sim(rr, f, n, n_sims, seed)
            ruin[name].append({"risk": f * 100,
                               "ruin": sum(1 for d in md if d < -0.5) / n_sims * 100})
    return {"curve": curve, "ruin": ruin, "n_trades": n, "tpy": tpy}


# --------------------------------------------------------------------------- #
# Kelly
# --------------------------------------------------------------------------- #
def kelly_per_trade(Rs, f_grid=None):
    """Log-optimal 1R fraction over the empirical R-multiple distribution."""
    Rs = [r for r in Rs if r is not None]
    if len(Rs) < 10:
        return None
    worst = min(Rs)
    f_cap = (0.98 / abs(worst)) if worst < 0 else 0.95   # keep 1+f·R > 0
    if f_grid is None:
        f_grid = [i / 2000 for i in range(1, int(f_cap * 2000))]

    def growth(f):
        s = 0.0
        for r in Rs:
            v = 1 + f * r
            if v <= 0:
                return -1e9
            s += math.log(v)
        return s / len(Rs)

    best_f = max(f_grid, key=growth)
    return {
        "f_star": best_f, "half": best_f / 2,
        "g_at_star": growth(best_f), "g_at_half": growth(best_f / 2),
        "n": len(Rs), "worst_R": worst,
        "expectancy_R": st.mean(Rs),
    }


def daily_returns(equity_by_date):
    ds = sorted(equity_by_date)
    out = []
    for i in range(1, len(ds)):
        p, c = equity_by_date[ds[i - 1]], equity_by_date[ds[i]]
        if p > 0:
            out.append((ds[i], c / p - 1))
    return out


def kelly_portfolio(equity_by_date):
    """Growth-optimal LEVERAGE multiplier λ*=μ/σ² on the actual daily returns."""
    rets = [r for _, r in daily_returns(equity_by_date)]
    if len(rets) < 20:
        return None
    mu, var = st.mean(rets), st.variance(rets)
    rf_d = RF / PPY
    lam = (mu - rf_d) / var if var > 0 else None
    sharpe = (mu - rf_d) / (var ** 0.5) * (PPY ** 0.5) if var > 0 else None
    return {"lambda_star": lam, "half": lam / 2 if lam else None,
            "mu_daily": mu, "sigma_daily": var ** 0.5, "sharpe_ann": sharpe}


# --------------------------------------------------------------------------- #
# Progressive exposure — backtest overlays on the daily equity curve
# --------------------------------------------------------------------------- #
def _metrics(dates, rets, cap=1.0):
    """CAGR / MaxDD / Sharpe / Calmar from a daily return series."""
    eq = cap
    peak = cap
    mdd = 0.0
    curve = [cap]
    for r in rets:
        eq *= (1 + r)
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
        curve.append(eq)
    n = len(rets)
    years = n / PPY
    cagr = (curve[-1] / curve[0]) ** (1 / years) - 1 if years > 0 and curve[0] > 0 else None
    mu, var = st.mean(rets), (st.variance(rets) if n > 1 else 0)
    rf_d = RF / PPY
    sharpe = (mu - rf_d) / (var ** 0.5) * (PPY ** 0.5) if var > 0 else None
    calmar = (cagr / abs(mdd)) if (cagr is not None and mdd < 0) else None
    return {"cagr": cagr, "maxdd": mdd, "sharpe": sharpe, "calmar": calmar,
            "final": curve[-1]}


def _sma(vals, n, i):
    if i + 1 < n:
        return None
    return sum(vals[i - n + 1:i + 1]) / n


def progressive_backtest(equity_by_date, low_exposure=0.5):
    """Apply exposure overlays using only info available at t-1 (no lookahead).
    Exposure e_t scales that day's book return: ruled_r = e_t · r_t."""
    dr = daily_returns(equity_by_date)
    if len(dr) < 30:
        return None
    dates = [d for d, _ in dr]
    rets = [r for _, r in dr]

    # reconstruct the ruled equity index to read state (equity, its 20d MA, DD)
    base_eq = [1.0]
    for r in rets:
        base_eq.append(base_eq[-1] * (1 + r))
    # state series aligned so day t uses eq[t] (close of t-1 → start of t)
    ma20 = [_sma(base_eq, 20, i) for i in range(len(base_eq))]
    peak = []
    pk = base_eq[0]
    for v in base_eq:
        pk = max(pk, v)
        peak.append((v - pk) / pk)   # drawdown at each point

    def run(exposure_fn):
        rr = []
        for i, r in enumerate(rets):
            e = exposure_fn(i)          # uses base_eq[i], ma20[i], peak[i] (info at t-1)
            rr.append(e * r)
        return _metrics(dates, rr)

    base = _metrics(dates, rets)
    # 1) equity > 20d MA gate: full exposure above its own trend, de-risk below
    gate = run(lambda i: 1.0 if (ma20[i] is None or base_eq[i] >= ma20[i]) else low_exposure)
    # 2) drawdown ladder: 1.0 at peak → 0.5 at −5% → 0.25 beyond −10%
    def dd_ladder(i):
        d = peak[i]
        if d <= -0.10:
            return 0.25
        if d <= -0.05:
            return 0.50
        return 1.0
    ladder = run(dd_ladder)
    # 3) combine (min of both overlays)
    combo = run(lambda i: min(1.0 if (ma20[i] is None or base_eq[i] >= ma20[i]) else low_exposure,
                              dd_ladder(i)))
    return {"baseline": base, "ma_gate": gate, "dd_ladder": ladder, "combined": combo}


# --------------------------------------------------------------------------- #
def summarize(trades, equity_by_date, capital):
    Rs = [t.R for t in trades if t.R is not None]
    risks = [t.risk for t in trades if t.risk]
    actual_1R_pct = (st.mean(risks) / capital * 100) if risks else None
    return {
        "actual_1R_pct": actual_1R_pct,
        "kelly_trade": kelly_per_trade(Rs),
        "kelly_pf": kelly_portfolio(equity_by_date) if equity_by_date else None,
        "progressive": progressive_backtest(equity_by_date) if equity_by_date else None,
    }


if __name__ == "__main__":
    from pipeline.portfolio import performance_review as pr
    t, m = pr.parse_csv(pr.latest_csv("data/portfolio"))
    m["_csv"] = "x"
    mtm = pr.compute_mtm(t, m)
    s = summarize(t, mtm["equity_by_date"], m["startingCapital"])
    kt, kp, prog = s["kelly_trade"], s["kelly_pf"], s["progressive"]
    print(f"actual 1R = {s['actual_1R_pct']:.2f}% of capital (target 0.25%)\n")
    print("── KELLY (per-trade, log-optimal on R) ──")
    print(f"  f* = {kt['f_star']*100:.2f}% of equity per 1R   half-Kelly = {kt['half']*100:.2f}%   "
          f"(n={kt['n']}, worst {kt['worst_R']:.1f}R, E[R]={kt['expectancy_R']:+.2f})")
    print(f"  → vs your actual {s['actual_1R_pct']:.2f}%: ratio {kt['half']*100/s['actual_1R_pct']:.1f}× (half-Kelly)\n")
    print("── KELLY (portfolio leverage, μ/σ² on daily returns) ──")
    print(f"  λ* = {kp['lambda_star']:.1f}×   half = {kp['half']:.1f}×   "
          f"(daily μ {kp['mu_daily']*100:.2f}%, σ {kp['sigma_daily']*100:.2f}%, Sharpe {kp['sharpe_ann']:.2f})")
    print("  ⚠ degenerate on a +90%/6-mo bull sample — do NOT lever to this.\n")
    print("── PROGRESSIVE EXPOSURE (overlays on daily equity) ──")
    def row(name, mm):
        print(f"  {name:16s} CAGR {mm['cagr']*100:6.1f}%  MaxDD {mm['maxdd']*100:6.1f}%  "
              f"Sharpe {mm['sharpe']:.2f}  Calmar {mm['calmar']:.2f}")
    row("baseline", prog["baseline"])
    row("equity>20dMA", prog["ma_gate"])
    row("DD ladder", prog["dd_ladder"])
    row("combined", prog["combined"])
