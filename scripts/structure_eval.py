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
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.options.structures import Leg, evaluate, crush_pnl


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
            tk = ib.reqMktData(o, "", False, False); ib.sleep(1.8)
            bid = tk.bid if (tk.bid and tk.bid > 0) else None
            ask = tk.ask if (tk.ask and tk.ask > 0) else None
            mid = (bid + ask) / 2 if (bid and ask) else tk.close
            g = tk.modelGreeks
            return bid, ask, mid, (g.impliedVol if g else None), \
                   (g.delta if g else None), (g.vega if g else None)

        legs = []
        for action, qty, strike, right in specs:
            bid, ask, mid, iv, delta, vega = quote(strike, right)
            if mid is None or (isinstance(mid, float) and math.isnan(mid)):
                sys.exit(f"no price for {strike}{right} — check strike/expiry")
            legs.append(Leg(action, qty, strike, right, mid=mid, bid=bid, ask=ask,
                            iv=iv, delta=delta, vega=vega))

        # Forward + implied move from the ATM straddle (for the sigma reading).
        atm = round(spot / 25) * 25
        _, _, cm, _, _, _ = quote(atm, "C")
        _, _, pm, _, _, _ = quote(atm, "P")
        forward = implied = None
        if cm and pm and not (math.isnan(cm) or math.isnan(pm)):
            implied = cm + pm
            forward = atm + (cm - pm)      # put-call parity, r≈0 over 1-2 days

        r = evaluate(legs, spot=spot, forward=forward, implied_move_pts=implied)
        if args.json:
            print(json.dumps({"legs": [l.__dict__ for l in legs], "metrics": r}, indent=2))
            return

        print("=" * 64)
        print(f"  SPX {args.expiry}   spot {spot:,.2f}"
              + (f"   forward {forward:,.2f}  implied ±{implied:,.1f}" if forward else ""))
        print("=" * 64)
        print(f"  {'leg':<12}{'strike':>8} {'mid':>8} {'bid/ask':>14} {'IV':>7} {'Δ':>7} {'vega':>7}")
        for l in legs:
            ba = f"{l.bid}×{l.ask}" if (l.bid and l.ask) else "—"
            iv = f"{l.iv:.2%}" if l.iv else "—"
            dl = f"{l.delta:+.3f}" if l.delta is not None else "—"
            vg = f"{l.vega:.3f}" if l.vega is not None else "—"
            print(f"  {l.action:<4}{l.qty:>3}   {l.right}{l.strike:>8,.0f} {l.mid:>8.2f} {ba:>14} {iv:>7} {dl:>7} {vg:>7}")
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
