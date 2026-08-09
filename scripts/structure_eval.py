#!/usr/bin/env python3
"""Evaluate any multi-leg SPX option structure against the live chain.

You specify the legs; this pulls live quotes/greeks from IBKR and prints the
full objective metric table (debit, max profit/loss, R/R, breakevens, net
greeks, skew capture, worst-case slippage, payoff peak in sigmas of the priced
move, and IV-crush sensitivity). It selects nothing and judges nothing.

Usage:
  # explicit legs: ACTION:QTY:STRIKE:RIGHT
  .venv/bin/python scripts/structure_eval.py --expiry 20260730 \
      --leg BUY:1:7425:P --leg SELL:2:7350:P --leg BUY:1:7275:P

  # shorthands
  .venv/bin/python scripts/structure_eval.py --expiry 20260730 --fly 7425/7350/7275 --right P
  .venv/bin/python scripts/structure_eval.py --expiry 20260731 --condor 7330/7350/7500/7520
"""
import argparse
import datetime as dt
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.options.structures import Leg, evaluate, crush_pnl
from pipeline.gex.blackscholes import bs_delta, bs_gamma, bs_vega, implied_vol
from pipeline.marketcal import MARKET_TZ, market_now

MIN_T_YEARS = 1.0 / (365.0 * 24.0)      # floor so an expiring option still prices


def _years_to_expiry(expiry: str) -> float:
    """Year fraction to the 16:00 ET settlement of `expiry` (YYYYMMDD)."""
    d = dt.datetime.strptime(expiry, "%Y%m%d").date()
    settle = dt.datetime.combine(d, dt.time(16, 0), tzinfo=MARKET_TZ)
    return max((settle - market_now()).total_seconds() / (365.0 * 24 * 3600), MIN_T_YEARS)


def _load_dealer_gex() -> dict[float, float] | None:
    """Per-strike dealer $GEX from the newest gex_levels run, if there is one.

    Lets the evaluator answer "is the payoff peak on a strike where dealers are
    long gamma" instead of leaving that criterion as a vibe.
    """
    files = sorted(glob.glob("data/gex/gex_SPX_2*.json"))
    if not files:
        return None
    try:
        d = json.loads(open(files[-1]).read())
        return {float(k): float(v) for k, v in (d.get("per_strike_gex") or {}).items()}
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _parse_legs(args) -> list[tuple]:
    """-> [(action, qty, strike, right)]"""
    if args.fly:
        a, b, c = (float(x) for x in args.fly.split("/"))
        r = args.right.upper()
        return [("BUY", 1, a, r), ("SELL", 2, b, r), ("BUY", 1, c, r)]
    if args.condor:
        lp, sp, sc, lc = (float(x) for x in args.condor.split("/"))
        return [("BUY", 1, lp, "P"), ("SELL", 1, sp, "P"),
                ("SELL", 1, sc, "C"), ("BUY", 1, lc, "C")]
    out = []
    for spec in args.leg:
        action, qty, strike, right = spec.split(":")
        out.append((action.upper(), int(qty), float(strike), right.upper()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expiry", required=True, help="YYYYMMDD")
    ap.add_argument("--leg", action="append", default=[],
                    help="ACTION:QTY:STRIKE:RIGHT, repeatable")
    ap.add_argument("--fly", help="A/B/C -> BUY 1 A, SELL 2 B, BUY 1 C")
    ap.add_argument("--right", default="P", help="right for --fly (default P)")
    ap.add_argument("--condor", help="longPut/shortPut/shortCall/longCall")
    ap.add_argument("--crush", type=float, default=8.0,
                    help="IV crush in vol points for the sensitivity line")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args()
    specs = _parse_legs(args)
    if not specs:
        sys.exit("no legs — use --leg / --fly / --condor")

    from ib_async import IB, Index, Option
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=107, timeout=10); break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")
    try:
        ib.reqMarketDataType(1)
        spx = Index("SPX", "CBOE"); ib.qualifyContracts(spx)
        t = ib.reqMktData(spx, "", False, False); ib.sleep(2.5)
        spot = t.last if (t.last and not math.isnan(t.last)) else t.close

        params = ib.reqSecDefOptParams("SPX", "", "IND", spx.conId)
        tc = next((p.tradingClass for p in params if args.expiry in p.expirations), "SPXW")

        def quote(strike, right):
            o = Option("SPX", args.expiry, strike, right, "CBOE", tradingClass=tc)
            ib.qualifyContracts(o)
            # 101 = open interest, 100 = option volume; both are needed to judge
            # "liquidity in the wings" and neither arrives on the default tick set.
            tk = ib.reqMktData(o, "100,101", False, False); ib.sleep(2.0)
            bid = tk.bid if (tk.bid and tk.bid > 0) else None
            ask = tk.ask if (tk.ask and tk.ask > 0) else None
            mid = (bid + ask) / 2 if (bid and ask) else tk.close
            g = tk.modelGreeks
            oi = tk.putOpenInterest if right == "P" else tk.callOpenInterest
            oi = int(oi) if (oi and not math.isnan(oi)) else None
            vol = int(tk.volume) if (tk.volume and not math.isnan(tk.volume)) else None
            return (bid, ask, mid, (g.impliedVol if g else None),
                    (g.delta if g else None), (g.vega if g else None),
                    (g.gamma if g else None), oi, vol)

        T = _years_to_expiry(args.expiry)
        # Forward first: index options price off the forward, not spot. Solving
        # IV against raw spot biased it ~1.1 vol points low vs IBKR's own model;
        # against the parity forward the gap drops to ~0.1.
        atm = round(spot / 25) * 25
        cm = quote(atm, "C")[2]
        pm = quote(atm, "P")[2]
        forward = implied = None
        if cm and pm and not (math.isnan(cm) or math.isnan(pm)):
            implied = cm + pm
            forward = atm + (cm - pm)      # put-call parity, r≈0 over 1-2 days
        underlying = forward or spot

        legs = []
        for action, qty, strike, right in specs:
            bid, ask, mid, iv, delta, vega, gamma, oi, vol = quote(strike, right)
            if mid is None or (isinstance(mid, float) and math.isnan(mid)):
                sys.exit(f"no price for {strike}{right} — check strike/expiry")
            src = "feed"
            # IBKR's model greeks arrive intermittently; a single missing leg
            # would otherwise blank out the net greeks for the whole package.
            # Back IV out of the mid and compute the greeks ourselves instead.
            if delta is None or vega is None or gamma is None or iv is None:
                iv_bs = iv if iv else implied_vol(mid, underlying, strike, T, right)
                if iv_bs:
                    iv = iv or iv_bs
                    delta = delta if delta is not None else bs_delta(underlying, strike, T, iv_bs, right)
                    vega = vega if vega is not None else bs_vega(underlying, strike, T, iv_bs)
                    gamma = gamma if gamma is not None else bs_gamma(underlying, strike, T, iv_bs)
                    src = "bs"
            legs.append(Leg(action, qty, strike, right, mid=mid, bid=bid, ask=ask,
                            iv=iv, delta=delta, vega=vega, gamma=gamma,
                            oi=oi, volume=vol, greeks_src=src))

        dealer_gex = _load_dealer_gex()
        r = evaluate(legs, spot=spot, forward=forward, implied_move_pts=implied,
                     dealer_gex=dealer_gex)
        if args.json:
            print(json.dumps({"legs": [l.__dict__ for l in legs], "metrics": r}, indent=2))
            return

        print("=" * 64)
        print(f"  SPX {args.expiry}   spot {spot:,.2f}"
              + (f"   forward {forward:,.2f}  implied ±{implied:,.1f}" if forward else ""))
        print("=" * 64)
        print(f"  {'leg':<12}{'strike':>8} {'mid':>8} {'bid/ask':>14} {'IV':>7} {'Δ':>7} {'vega':>7} {'OI':>7} {'vol':>6}  src")
        for l in legs:
            ba = f"{l.bid}×{l.ask}" if (l.bid and l.ask) else "—"
            iv = f"{l.iv:.2%}" if l.iv else "—"
            dl = f"{l.delta:+.3f}" if l.delta is not None else "—"
            vg = f"{l.vega:.3f}" if l.vega is not None else "—"
            oi = f"{l.oi:,}" if l.oi is not None else "—"
            vl = f"{l.volume:,}" if l.volume is not None else "—"
            print(f"  {l.action:<4}{l.qty:>3}   {l.right}{l.strike:>8,.0f} {l.mid:>8.2f} {ba:>14} {iv:>7} {dl:>7} {vg:>7} {oi:>7} {vl:>6}  {l.greeks_src}")
        if any(l.greeks_src == "bs" for l in legs):
            print(f"  (src=bs: IBKR greeks were missing; IV backed out of the mid, "
                  f"delta/vega from Black-Scholes at T={T*365:.2f}d)")
        print("-" * 64)
        kind = "DEBIT" if r["is_debit"] else "CREDIT"
        print(f"  net {kind:<8}      {abs(r['net_debit']):>9.2f}   (${abs(r['net_debit'])*100:,.0f} / contract)")
        if r["natural_debit"] is not None:
            print(f"  worst fill          {abs(r['natural_debit']):>9.2f}   slippage {r['slippage']:+.2f}"
                  f" ({r['slippage_pct_of_debit']:+.1f}% of premium)")
        mp = f"{r['max_profit']:>9.2f} @ {r['max_profit_at']:,.0f}" if r["max_profit"] is not None else "UNBOUNDED"
        ml = f"{r['max_loss']:>9.2f}" if r["max_loss"] is not None else "UNBOUNDED"
        print(f"  max profit          {mp}")
        print(f"  max loss            {ml}")
        if r["rr"]:
            print(f"  R/R                 1 : {r['rr']:.2f}")
        if r["breakevens"]:
            bes = "  ↔  ".join(f"{b:,.2f}" for b in r["breakevens"])
            print(f"  breakevens          {bes}"
                  + (f"   (zone {r['profit_zone_width']:,.1f} wide)" if r["profit_zone_width"] else ""))
        print(f"  net delta           {r['net_delta']:+.4f}" if r["net_delta"] is not None else "")
        if r["net_vega"] is not None:
            print(f"  net vega            {r['net_vega']:+.4f}"
                  f"   → {args.crush:.0f}pt IV crush = {crush_pnl(r['net_vega'], args.crush):+.2f}")
        if r["net_gamma"] is not None:
            conv = "LONG convexity" if r["long_convexity"] else "SHORT convexity"
            print(f"  net gamma           {r['net_gamma']:+.6f}   ({conv})")
        if r["min_leg_oi"] is not None:
            thin = f"  thinnest {'/'.join(r['thinnest_legs'])}" if r["thinnest_legs"] else ""
            print(f"  liquidity           min OI {r['min_leg_oi']:,}  min vol "
                  f"{r['min_leg_volume'] if r['min_leg_volume'] is not None else '—'}"
                  f"  worst spread {r['worst_leg_spread_pct']:.1f}%{thin}")
        if "peak_dealer_gex" in r:
            side = "dealers LONG gamma here (they pin toward it)" if r["peak_dealer_long_gamma"] \
                   else "dealers SHORT gamma here (they amplify away from it)"
            print(f"  dealer @ peak       {r['peak_dealer_gex']/1e9:+.2f}B   {side}")
        if r["skew_capture"] is not None:
            print(f"  skew                sold {r['iv_sold']:.2%} vs bought {r['iv_bought']:.2%}"
                  f"  → {r['skew_capture']:+.2%}")
        if "peak_sigma" in r:
            print(f"  payoff peak         {r['peak_sigma']:+.2f}σ  ({r['peak_vs_forward_pct']:+.2f}% from forward)")
        risk = "DEFINED" if r["risk_defined"] else "UNDEFINED TAIL"
        tails = [n for n, k in (("up", "unbounded_loss_up"), ("down", "unbounded_loss_down")) if r[k]]
        print(f"  risk                {risk}" + (f"  — unbounded loss {'/'.join(tails)}" if tails else ""))
        print("=" * 64)
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
