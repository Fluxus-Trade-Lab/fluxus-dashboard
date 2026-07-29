"""Objective evaluation of multi-leg option structures — pure math, no IO.

Given legs with live quotes, returns every number needed to judge a structure
on its own terms: net debit/credit, max profit/loss, breakevens, profit zone,
net greeks, skew captured across the legs, worst-case fill slippage, where the
payoff peak sits relative to the market's own priced move, and the P&L impact
of an IV crush.

Deliberately contains no judgement and no strike selection — it scores what it
is handed. Payoff is piecewise-linear in the underlying, so extremes and
breakevens are computed exactly at the kinks rather than by grid search.
"""
from __future__ import annotations

from dataclasses import dataclass

BUY, SELL = "BUY", "SELL"


@dataclass
class Leg:
    action: str          # BUY | SELL
    qty: int             # positive
    strike: float
    right: str           # "C" | "P"
    mid: float
    bid: float | None = None
    ask: float | None = None
    iv: float | None = None      # decimal, e.g. 0.2285
    delta: float | None = None
    vega: float | None = None
    oi: int | None = None
    volume: int | None = None
    greeks_src: str = "feed"     # "feed" | "bs" — computed greeks must be visible

    @property
    def signed(self) -> int:
        """+qty when long, -qty when short."""
        return self.qty if self.action.upper() == BUY else -self.qty


def _intrinsic(spot: float, leg: Leg) -> float:
    if leg.right.upper() == "C":
        return max(spot - leg.strike, 0.0)
    return max(leg.strike - spot, 0.0)


def payoff_at(spot: float, legs: list[Leg]) -> float:
    """Expiry payoff of the package (before premium paid/received)."""
    return sum(l.signed * _intrinsic(spot, l) for l in legs)


def net_debit(legs: list[Leg]) -> float:
    """Positive = net debit paid; negative = net credit received."""
    return sum(l.signed * l.mid for l in legs)


def natural_debit(legs: list[Leg]) -> float | None:
    """Worst-case fill: pay the ask on buys, receive the bid on sells."""
    if any(l.ask is None or l.bid is None for l in legs):
        return None
    return sum((l.qty * l.ask) if l.signed > 0 else (-l.qty * l.bid) for l in legs)


def _pnl(spot: float, legs: list[Leg], debit: float) -> float:
    return payoff_at(spot, legs) - debit


def evaluate(legs: list[Leg],
             spot: float | None = None,
             forward: float | None = None,
             implied_move_pts: float | None = None) -> dict:
    """Full objective metric set for the structure.

    `forward` + `implied_move_pts` are optional; when supplied, the payoff peak
    is also reported in sigmas of the market's own priced move.
    """
    debit = net_debit(legs)
    strikes = sorted({l.strike for l in legs})

    # P&L is piecewise-linear with kinks only at strikes. Evaluate there, plus
    # the true floor (S=0) and a point far above the top strike.
    lo, hi = 0.0, strikes[-1] * 2.0
    pts = [lo] + strikes + [hi]
    pnl = [(s, _pnl(s, legs, debit)) for s in pts]

    # Unbounded-ness comes from the slope outside the outermost strikes.
    slope_above = sum(l.signed for l in legs if l.right.upper() == "C")
    slope_below = -sum(l.signed for l in legs if l.right.upper() == "P")

    kink_pnl = [(s, p) for s, p in pnl if s in strikes]
    best_s, best_p = max(kink_pnl, key=lambda sp: sp[1])
    worst_s, worst_p = min(pnl, key=lambda sp: sp[1])

    max_profit = None if (slope_above > 0 or slope_below < 0) else best_p
    max_loss = None if (slope_above < 0 or slope_below > 0) else worst_p

    # Breakevens: linear interpolation across sign changes between kinks.
    bes = []
    for (s0, p0), (s1, p1) in zip(pnl, pnl[1:]):
        if p0 == 0:
            bes.append(s0)
        elif (p0 < 0 < p1) or (p1 < 0 < p0):
            bes.append(s0 + (s1 - s0) * (-p0) / (p1 - p0))
    bes = sorted(set(round(b, 4) for b in bes))

    def _net(attr):
        vals = [getattr(l, attr) for l in legs]
        if any(v is None for v in vals):
            return None
        return sum(l.signed * getattr(l, attr) for l in legs)

    net_delta, net_vega = _net("delta"), _net("vega")

    # Skew captured: average IV sold vs average IV bought (qty-weighted).
    sold = [(l.qty, l.iv) for l in legs if l.signed < 0 and l.iv is not None]
    bought = [(l.qty, l.iv) for l in legs if l.signed > 0 and l.iv is not None]
    iv_sold = sum(q * v for q, v in sold) / sum(q for q, _ in sold) if sold else None
    iv_bought = sum(q * v for q, v in bought) / sum(q for q, _ in bought) if bought else None
    skew_capture = (iv_sold - iv_bought) if (iv_sold is not None and iv_bought is not None) else None

    nat = natural_debit(legs)
    slip = (nat - debit) if nat is not None else None
    slip_pct = (slip / abs(debit) * 100.0) if (slip is not None and debit) else None

    out = {
        "net_debit": round(debit, 4),
        "is_debit": debit > 0,
        "natural_debit": round(nat, 4) if nat is not None else None,
        "slippage": round(slip, 4) if slip is not None else None,
        "slippage_pct_of_debit": round(slip_pct, 2) if slip_pct is not None else None,
        "max_profit": round(max_profit, 4) if max_profit is not None else None,
        "max_profit_at": best_s if max_profit is not None else None,
        "max_loss": round(max_loss, 4) if max_loss is not None else None,
        "rr": round(abs(max_profit / max_loss), 3) if (max_profit and max_loss) else None,
        "breakevens": bes,
        "profit_zone_width": round(bes[-1] - bes[0], 4) if len(bes) >= 2 else None,
        "net_delta": round(net_delta, 4) if net_delta is not None else None,
        "net_vega": round(net_vega, 4) if net_vega is not None else None,
        "iv_sold": round(iv_sold, 4) if iv_sold is not None else None,
        "iv_bought": round(iv_bought, 4) if iv_bought is not None else None,
        "skew_capture": round(skew_capture, 4) if skew_capture is not None else None,
        # Named profit/loss explicitly: "unbounded upside" alone is ambiguous
        # about which way the tail runs, and that ambiguity is exactly what a
        # risk check must not have.
        "unbounded_profit_up": slope_above > 0,
        "unbounded_profit_down": slope_below < 0,
        "unbounded_loss_up": slope_above < 0,
        "unbounded_loss_down": slope_below > 0,
        "risk_defined": slope_above >= 0 and slope_below <= 0,
    }
    if forward and implied_move_pts and max_profit is not None:
        out["peak_vs_forward_pct"] = round((best_s - forward) / forward * 100.0, 3)
        out["peak_sigma"] = round((best_s - forward) / implied_move_pts, 3)
    if spot:
        out["spot"] = spot
    return out


def crush_pnl(net_vega: float, iv_drop_pts: float) -> float:
    """P&L from an IV collapse. `iv_drop_pts` in vol points (8 = 24% -> 16%).

    vega is dP/dσ per vol point, so a drop of X points moves P by vega * (-X).
    A short-vega package therefore gains on a crush.
    """
    return net_vega * (-iv_drop_pts)
