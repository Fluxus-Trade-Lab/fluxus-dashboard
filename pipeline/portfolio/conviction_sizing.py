#!/usr/bin/env python3
"""Conviction → position-size evaluator (Tharp + LordFed grounded).

The audit found corr(position size, R) ≈ 0 — sizing adds no edge. This asks the
follow-up: if we sized by a conviction score built ONLY from signals observable
AT ENTRY (trend/MA alignment, ATR extension, breakout proximity, is-it-a-re-attack),
would the money have gone to the better trades?

Design choices, from the two references:
  * Van Tharp — size by RISK (percent-risk model; R-multiples; percent-volatility
    for an equal-vol variant) and anti-martingale (press strength, cut weakness).
  * LordFed — Test / Core / Press tiers; "never average down unless pre-planned"
    (re-attacks get the Test floor); half-Kelly humility.

Crucially the backtest is RISK-NEUTRAL: every scheme deploys the SAME total risk
budget as the actual book, only REALLOCATED. So it isolates *steering* (did the
risk go to the right trades?) from *leverage* (did betting more help?). The
conviction rule is PRE-SPECIFIED, not fit to these 331 trades (overfit guard).

Run:  python -m pipeline.portfolio.conviction_sizing
"""
from __future__ import annotations

import statistics as st

from pipeline.tickers.ohlc_store import load_local_ohlc, trade_technicals


def _corr(xs, ys):
    if len(xs) < 3 or st.pstdev(xs) == 0 or st.pstdev(ys) == 0:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
    return cov / (st.pstdev(xs) * st.pstdev(ys))


def conviction_score(tech, direction, is_reattack):
    """0..1 from entry-observable signals. Pre-specified weights (not fitted)."""
    if not tech:
        return None
    long = direction != "short"
    stack = tech.get("stack") or ""
    ext = tech.get("ext_atr")
    slope = tech.get("sma50_slope") or 0
    dist_hi = tech.get("dist_hi20_pct")
    s = 0.5
    # trend / MA alignment with direction
    if long:
        s += {"bull": 0.20, "bull*": 0.10, "mixed": -0.05, "bear": -0.20, "bear*": -0.15}.get(stack, 0)
        if tech.get("above_sma50") and slope > 0:
            s += 0.10
        if dist_hi is not None and dist_hi > -5:   # near the 20d high = breakout
            s += 0.10
    else:
        s += {"bear": 0.20, "bear*": 0.10, "mixed": -0.05, "bull": -0.20, "bull*": -0.15}.get(stack, 0)
        if tech.get("above_sma50") is False and slope < 0:
            s += 0.10
    # ATR extension: a little push-off is fine; chasing (>2.5 ATR) is punished
    if ext is not None:
        if long and ext > 2.5:
            s -= 0.15
        elif long and 0 <= ext <= 1.5:
            s += 0.05
    # LordFed: never average down — re-attacks get pushed toward the Test floor
    if is_reattack:
        s -= 0.30
    return max(0.0, min(1.0, s))


def tier_mult(score):
    """Test / Core / Press multiplier (LordFed)."""
    if score < 0.40:
        return 0.5, "Test"
    if score < 0.70:
        return 1.0, "Core"
    return 1.6, "Press"


def evaluate(trades):
    # per-trade entry technicals + conviction
    by_tk = {}
    for t in sorted(trades, key=lambda x: x.entry_date):
        by_tk.setdefault(t.ticker, []).append(t)

    def is_reattack(t):
        priors = [x for x in by_tk[t.ticker] if x.entry_date < t.entry_date]
        return any(x.pnl < 0 for x in priors)

    rows = []
    for t in trades:
        if t.R is None or not t.risk:
            continue
        bars = load_local_ohlc(t.ticker)
        tech = trade_technicals(bars, t.entry_date, t.direction) if bars else None
        sc = conviction_score(tech, t.direction, is_reattack(t))
        if sc is None:
            continue
        mult, tier = tier_mult(sc)
        atr_pct = (tech.get("atr_pct") or None)
        rows.append({"t": t, "R": t.R, "risk": t.risk, "score": sc, "mult": mult,
                     "tier": tier, "atr_pct": atr_pct, "reattack": is_reattack(t)})
    if not rows:
        return None

    total_risk = sum(r["risk"] for r in rows)

    def alloc_pnl(weights):
        scale = total_risk / sum(weights)
        return sum(w * scale * r["R"] for w, r in zip(weights, rows)), \
            [w * scale for w in weights]

    # 1) actual: risk as traded
    actual_pnl = sum(r["risk"] * r["R"] for r in rows)
    # 2) conviction-weighted (risk-neutral reallocation)
    conv_pnl, conv_w = alloc_pnl([r["mult"] for r in rows])
    # 3) equal-vol (Tharp percent-volatility): weight ∝ 1/ATR%
    vol_rows = [r for r in rows if r["atr_pct"]]
    eqvol_pnl = None
    if len(vol_rows) > len(rows) * 0.8:
        w = [(1 / r["atr_pct"]) if r["atr_pct"] else 0 for r in rows]
        eqvol_pnl, _ = alloc_pnl(w)
    # 4) conviction × equal-vol (both levers)
    combo_pnl, _ = alloc_pnl([r["mult"] * (1 / r["atr_pct"] if r["atr_pct"] else 1) for r in rows])

    Rs = [r["R"] for r in rows]
    return {
        "n": len(rows),
        "corr_actualrisk_R": _corr([r["risk"] for r in rows], Rs),
        "corr_score_R": _corr([r["score"] for r in rows], Rs),
        "corr_conv_R": _corr(conv_w, Rs),
        "actual_pnl": actual_pnl, "conv_pnl": conv_pnl,
        "eqvol_pnl": eqvol_pnl, "combo_pnl": combo_pnl,
        "tier_counts": {tt: sum(1 for r in rows if r["tier"] == tt) for tt in ("Test", "Core", "Press")},
        "tier_meanR": {tt: (st.mean([r["R"] for r in rows if r["tier"] == tt])
                            if any(r["tier"] == tt for r in rows) else None)
                       for tt in ("Test", "Core", "Press")},
        "rows": rows,
    }


if __name__ == "__main__":
    from pipeline.portfolio import performance_review as pr
    t, _ = pr.parse_csv(pr.latest_csv("data/portfolio"))
    e = evaluate(t)
    print(f"n = {e['n']} trades with entry technicals + R\n")
    print("── DOES ENTRY-CONVICTION PREDICT OUTCOME? (the crux) ──")
    print(f"  corr(actual risk, R)      = {e['corr_actualrisk_R']:+.3f}   (baseline: sizing ~ uncorrelated)")
    print(f"  corr(conviction score, R) = {e['corr_score_R']:+.3f}   (do entry signals predict R?)")
    print(f"  corr(conviction size, R)  = {e['corr_conv_R']:+.3f}\n")
    print("── SAME TOTAL RISK, REALLOCATED — total P&L ──")
    print(f"  actual (as traded)     ${e['actual_pnl']:,.0f}")
    print(f"  conviction-weighted    ${e['conv_pnl']:,.0f}   ({(e['conv_pnl']/e['actual_pnl']-1)*100:+.1f}%)")
    if e["eqvol_pnl"]:
        print(f"  equal-vol (Tharp)      ${e['eqvol_pnl']:,.0f}   ({(e['eqvol_pnl']/e['actual_pnl']-1)*100:+.1f}%)")
    print(f"  conviction × equal-vol ${e['combo_pnl']:,.0f}   ({(e['combo_pnl']/e['actual_pnl']-1)*100:+.1f}%)\n")
    print("── TIER PROFILE (Test/Core/Press) ──")
    for tt in ("Test", "Core", "Press"):
        mr = e["tier_meanR"][tt]
        print(f"  {tt:6s} n={e['tier_counts'][tt]:3d}  mean R {mr:+.2f}" if mr is not None else f"  {tt}: n=0")
