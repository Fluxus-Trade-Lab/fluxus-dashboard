#!/usr/bin/env python3
"""
Daily ES (E-mini S&P) options-on-futures planner — for the 5DTE / July-6-expiry ES play.

Pulls the ES option chain for a target expiry (default the next Monday weekly, e.g. 20260706),
with per-strike IV, delta, gamma, open interest, then prints an actionable plan:
  spot, expected move, top-3 put/call OI walls (support/resistance), ~target-delta call.

Underlying = the front quarterly ES future (Sep in July). Uses reqSecDefOptParams to find the
chain/tradingClass that actually lists the target expiry (no hardcoded weekly class).

Prereq: TWS/Gateway running, API on, CME options-on-futures data subscription.
    .venv/bin/python scripts/ibkr_es_option_plan.py --expiry 20260706 --port 7496
    .venv/bin/python scripts/ibkr_es_option_plan.py --expiry 20260706 --width 60 --target-delta 0.60
"""
import argparse, math
import pandas as pd
from ib_async import IB, ContFuture, Future, FuturesOption

def first_num(*vals):
    for v in vals:
        if v is not None and isinstance(v,(int,float)) and not math.isnan(v): return float(v)
    return None
def spot_from(ib, c):
    t=ib.reqTickers(c)[0]; return first_num(t.last, t.close, t.marketPrice())

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--expiry", default="20260706", help="option expiry YYYYMMDD")
    p.add_argument("--fut-month", default="202609", help="underlying ES future YYYYMM (Sep in July)")
    p.add_argument("--width", type=float, default=60.0, help="strikes within +/- this many points of spot")
    p.add_argument("--target-delta", type=float, default=0.60)
    p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=7496)
    p.add_argument("--clientid", type=int, default=41); p.add_argument("--delayed", action="store_true")
    p.add_argument("--spot", type=float, default=None)
    args=p.parse_args()

    ib=IB(); ib.connect(args.host,args.port,clientId=args.clientid,timeout=20)
    if args.delayed: ib.reqMarketDataType(3)

    fut=Future("ES", args.fut_month, "CME")
    try: ib.qualifyContracts(fut)
    except Exception:
        fut=ContFuture("ES","CME"); ib.qualifyContracts(fut)
    spot=args.spot or spot_from(ib,fut)
    if spot is None:
        ib.reqMarketDataType(3); spot=spot_from(ib,fut); ib.reqMarketDataType(3 if args.delayed else 1)
    if spot is None: print("No ES spot; pass --spot."); ib.disconnect(); return
    print(f"\nES ({fut.localSymbol}) spot = {spot:.2f}   target expiry {args.expiry}")

    chains=ib.reqSecDefOptParams("ES","CME","FUT",fut.conId)
    chain=next((ch for ch in chains if args.expiry in ch.expirations), None)
    if chain is None:
        allexp=sorted({e for ch in chains for e in ch.expirations})
        print(f"Expiry {args.expiry} not listed. Nearby: {[e for e in allexp if e>=args.expiry][:6]}")
        ib.disconnect(); return
    print(f"Using tradingClass {chain.tradingClass} (mult {chain.multiplier})")
    strikes=sorted(s for s in chain.strikes if spot-args.width<=s<=spot+args.width)
    if not strikes: print("No strikes in range."); ib.disconnect(); return

    opts=[]
    for k in strikes:
        for right in ("C","P"):
            opts.append(FuturesOption("ES", args.expiry, k, right, "CME",
                        tradingClass=chain.tradingClass, multiplier=chain.multiplier))
    opts=[o for o in ib.qualifyContracts(*opts) if o.conId]
    tickers=ib.reqTickers(*opts)
    if all(t.modelGreeks is None for t in tickers) and not args.delayed:
        print("No live greeks — retrying DELAYED..."); ib.reqMarketDataType(3); tickers=ib.reqTickers(*opts)
    oi={o.conId: ib.reqMktData(o,"100,101",False,False) for o in opts}
    ib.sleep(4)
    rows=[]
    for o,t in zip(opts,tickers):
        mg=t.modelGreeks; tk=oi[o.conId]
        rows.append(dict(strike=o.strike,right=o.right,
                    iv=(mg.impliedVol if mg else None), delta=(mg.delta if mg else None),
                    gamma=(mg.gamma if mg else None), mid=t.marketPrice(),
                    oi=(tk.callOpenInterest if o.right=="C" else tk.putOpenInterest)))
    for o in opts: ib.cancelMktData(o)
    ib.disconnect()
    df=pd.DataFrame(rows)
    calls=df[df.right=="C"].set_index("strike").sort_index()
    puts =df[df.right=="P"].set_index("strike").sort_index()
    atmk=min(strikes,key=lambda k:abs(k-spot))
    em=None
    try: em=calls.loc[atmk,"mid"]+puts.loc[atmk,"mid"]
    except: pass
    def walls(side,n=3):
        s=side["oi"].dropna(); return list(s.sort_values(ascending=False).head(n).index) if len(s) else []
    cc=calls.dropna(subset=["delta"]); pick=None
    if len(cc): pick=cc.assign(dd=(cc["delta"]-args.target_delta).abs()).sort_values("dd").iloc[0]

    print("\n================= ES DAILY PLAN =================")
    print(f" Spot ....................... {spot:.2f}")
    if em: print(f" ATM straddle (exp move) .... ±{em:.2f} ({em/spot*100:.2f}%)  0.5% flush ≈ {spot*0.005:.0f} pts to {spot*0.995:.0f}")
    print(f" SUPPORT  (put walls) ........ {', '.join(str(int(x)) for x in walls(puts))}")
    print(f" RESISTANCE (call walls) ..... {', '.join(str(int(x)) for x in walls(calls))}")
    if pick is not None:
        iv=pick['iv']*100 if pick['iv'] else float('nan')
        print(f" Buy ~{args.target_delta:.2f}Δ call: strike {pick.name:.0f} | Δ {pick['delta']:.2f} | IV {iv:.1f}% | mid {pick['mid']:.2f}")
    print("================================================")
    out=f"esplan_{args.expiry}.csv"; df.sort_values(['strike','right']).to_csv(out,index=False)
    print(f"Full chain -> {out}")

if __name__=="__main__":
    main()
