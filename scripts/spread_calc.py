#!/usr/bin/env python3
"""Objective option-spread calculator — you pick the strikes, it reports numbers.

Pulls live SPX(W) quotes+greeks for the legs you specify and prints credit,
max loss, breakevens, short-strike deltas (≈ implied breach probability), and
each short strike's distance to the current GEX landmarks + expected move.
It does NOT choose strikes, size, or judge the trade — it is a calculator.

Usage (short strikes only = strangle; add wings for a defined-risk condor):
    .venv/bin/python scripts/spread_calc.py --expiry 20260731 \
        --short-call 7500 --short-put 7350 \
        [--long-call 7520 --long-put 7330]
"""
import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _latest_gex():
    files = sorted(glob.glob("data/gex/gex_SPX_2*.json"))
    return json.loads(open(files[-1]).read()) if files else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expiry", required=True, help="YYYYMMDD")
    ap.add_argument("--short-call", type=float, required=True)
    ap.add_argument("--short-put", type=float, required=True)
    ap.add_argument("--long-call", type=float)
    ap.add_argument("--long-put", type=float)
    args = ap.parse_args()

    from ib_async import IB, Index, Option
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=99, timeout=10); break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")
    try:
        ib.reqMarketDataType(1)
        spx = Index("SPX", "CBOE"); ib.qualifyContracts(spx)
        t = ib.reqMktData(spx, "", False, False); ib.sleep(2.5)
        g = _latest_gex()
        spot = t.last if (t.last and not math.isnan(t.last)) else (t.close if (t.close and not math.isnan(t.close)) else g.get("spot"))

        params = ib.reqSecDefOptParams("SPX", "", "IND", spx.conId)
        tc = next((p.tradingClass for p in params if args.expiry in p.expirations), "SPXW")

        def leg(strike, right):
            o = Option("SPX", args.expiry, strike, right, "CBOE", tradingClass=tc)
            ib.qualifyContracts(o)
            tk = ib.reqMktData(o, "", False, False); ib.sleep(1.8)
            mid = (tk.bid + tk.ask) / 2 if (tk.bid and tk.ask and tk.bid > 0 and tk.ask > 0) else tk.close
            d = tk.modelGreeks.delta if tk.modelGreeks else None
            return {"strike": strike, "right": right, "bid": tk.bid, "ask": tk.ask,
                    "mid": mid, "delta": d}

        sc = leg(args.short_call, "C")
        sp = leg(args.short_put, "P")
        lc = leg(args.long_call, "C") if args.long_call else None
        lp = leg(args.long_put, "P") if args.long_put else None

        # credit = sold − bought
        credit = (sc["mid"] or 0) + (sp["mid"] or 0)
        if lc: credit -= (lc["mid"] or 0)
        if lp: credit -= (lp["mid"] or 0)

        defined = bool(lc and lp)
        print("=" * 58)
        print(f"  SPX {args.expiry}  spot {spot:,.2f}   (calc only — not advice)")
        print("=" * 58)
        for name, l in (("short call", sc), ("long call ", lc), ("short put ", sp), ("long put  ", lp)):
            if not l: continue
            dd = f"Δ {l['delta']:+.3f}" if l["delta"] is not None else "Δ n/a"
            print(f"  {name} {l['strike']:>6,.0f}  bid {l['bid']}  ask {l['ask']}  mid {l['mid']}  {dd}")
        print("-" * 58)
        print(f"  NET CREDIT           {credit:>8.2f}  (x100 = ${credit*100:,.0f}/contract)")
        if defined:
            wc = args.long_call - args.short_call
            wp = args.short_put - args.long_put
            width = max(wc, wp)
            maxloss = width - credit
            print(f"  wing width  call {wc:.0f} / put {wp:.0f}   widest {width:.0f}")
            print(f"  MAX LOSS             {maxloss:>8.2f}  (${maxloss*100:,.0f})   "
                  f"R/R {credit/maxloss:.2f} : 1" if maxloss > 0 else "  MAX LOSS n/a")
        else:
            print("  MAX LOSS             UNBOUNDED  (naked strangle — no wings)")
        be_lo = args.short_put - credit
        be_hi = args.short_call + credit
        print(f"  BREAKEVENS           {be_lo:,.0f}  ↔  {be_hi:,.0f}   (width {be_hi-be_lo:,.0f})")
        if sc["delta"] is not None and sp["delta"] is not None:
            pin = (1 - abs(sc["delta"]) - abs(sp["delta"])) * 100
            print(f"  short deltas: call {abs(sc['delta']):.2f}  put {abs(sp['delta']):.2f}  "
                  f"→ ~{pin:.0f}% stay-inside (rough, delta≈breach prob)")
        # landmarks
        print("-" * 58)
        print("  short strikes vs GEX landmarks:")
        marks = {"put_wall": g.get("put_wall"), "flip": g.get("zero_gamma_flip"),
                 "call_wall": g.get("call_wall")}
        print(f"    put_wall {marks['put_wall']}  flip {marks['flip']}  call_wall {marks['call_wall']}")
        print(f"    short put {args.short_put:.0f}: {args.short_put-spot:+.0f} vs spot; "
              f"{'above' if args.short_put>marks['put_wall'] else 'below'} put_wall")
        print(f"    short call {args.short_call:.0f}: {args.short_call-spot:+.0f} vs spot; "
              f"{'at/above' if args.short_call>=marks['call_wall'] else 'below'} call_wall")
        print("=" * 58)
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
