#!/usr/bin/env python3
"""
Daily option-chain planner for the July dip-buy playbook.

Pulls the option chain for a given expiry (0DTE = today, 1DTE = next session),
with per-strike IV, delta, gamma and open interest, then prints an actionable plan:
  - spot + expected move (from the ATM straddle)
  - SUPPORT  = put wall  (strike with max put open interest)
  - RESISTANCE= call wall (strike with max call open interest)
  - a rough gamma-flip estimate from OI-weighted gamma
  - the call strike closest to your target delta (default 0.60, slightly ITM)

Prereq: TWS / IB Gateway running, API enabled. Option greeks/OI need an options
market-data subscription (OPRA); the script falls back to DELAYED data if live is
unavailable (set with --delayed or automatically when greeks come back empty).

Usage:
    .venv/bin/python scripts/ibkr_daily_option_plan.py --symbol SPX --dte 0 --port 7496
    .venv/bin/python scripts/ibkr_daily_option_plan.py --symbol SPX --dte 1        # tomorrow
    .venv/bin/python scripts/ibkr_daily_option_plan.py --symbol XSP --dte 0 --width 0.03
    .venv/bin/python scripts/ibkr_daily_option_plan.py --symbol SPY --dte 0 --target-delta 0.60

Symbols:  SPX (index, SPXW dailies) | XSP (mini-SPX) | SPY (ETF)
"""
import argparse, datetime as dt, math, os, sys
import pandas as pd
from ib_async import IB, Index, Stock, Option

# scripts/ is on sys.path when run directly, not the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.marketcal import market_today  # trading dates: ET, never host JST

def first_num(*vals):
    """First finite number among vals (handles nan/None from IB tickers)."""
    for v in vals:
        if v is not None and isinstance(v,(int,float)) and not math.isnan(v):
            return float(v)
    return None

def spot_from(ib, contract):
    t = ib.reqTickers(contract)[0]
    return first_num(t.last, t.close, t.marketPrice())

CFG = {  # (secType, exchange, tradingClass for daily expiries)
    "SPX": dict(sec="IND", exch="CBOE", tclass="SPXW"),
    "XSP": dict(sec="IND", exch="CBOE", tclass="XSP"),
    "SPY": dict(sec="STK", exch="SMART", tclass="SPY"),
    "QQQ": dict(sec="STK", exch="SMART", tclass="QQQ"),
}

def underlier(symbol):
    c = CFG[symbol]
    return Index(symbol, c["exch"], "USD") if c["sec"] == "IND" else Stock(symbol, "SMART", "USD")

def next_business_day(d, n):
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5: n -= 1
    return d

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="SPX", choices=["SPX","XSP","SPY","QQQ"])
    p.add_argument("--dte", type=int, default=0, help="0 = today, 1 = next session, ...")
    p.add_argument("--width", type=float, default=0.025, help="strikes within +/- this frac of spot")
    p.add_argument("--target-delta", type=float, default=0.60)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7496)
    p.add_argument("--clientid", type=int, default=31)
    p.add_argument("--delayed", action="store_true")
    p.add_argument("--spot", type=float, default=None, help="manual spot override (skips index quote)")
    args = p.parse_args()

    ib = IB(); ib.connect(args.host, args.port, clientId=args.clientid, timeout=20)
    if args.delayed: ib.reqMarketDataType(3)

    u = underlier(args.symbol); ib.qualifyContracts(u)
    # --- robust spot resolution ---
    spot = args.spot
    src = "manual" if spot else None
    if spot is None:
        spot = spot_from(ib, u); src = "index-live" if spot else None
    if spot is None:  # index quote missing (no CBOE index subscription) -> delayed
        ib.reqMarketDataType(3); spot = spot_from(ib, u)
        if spot: src = "index-delayed"
        ib.reqMarketDataType(3 if args.delayed else 1)
    if spot is None:  # final fallback: SPY proxy (SPX≈SPY*10, XSP≈SPY)
        spy = Stock("SPY","SMART","USD"); ib.qualifyContracts(spy)
        s = spot_from(ib, spy)
        if s: spot = s*(10 if args.symbol=="SPX" else 1); src = "SPY-proxy"
    if spot is None:
        print("Could not resolve spot. Pass --spot <price> (e.g. --spot 7499)."); ib.disconnect(); return
    print(f"\n{args.symbol} spot = {spot:.2f}  [{src}]  (target expiry offset: {args.dte} session)")

    # option chain params
    c = CFG[args.symbol]
    chains = ib.reqSecDefOptParams(u.symbol, "", c["sec"], u.conId)
    chain = next((ch for ch in chains if ch.tradingClass == c["tclass"]
                  and ch.exchange in ("SMART","CBOE")), None) or chains[0]
    target_date = next_business_day(market_today(), args.dte) if args.dte>0 else market_today()
    tds = target_date.strftime("%Y%m%d")
    exps = sorted(chain.expirations)
    expiry = tds if tds in exps else next((e for e in exps if e >= tds), exps[0])
    print(f"Using expiry {expiry}  (tradingClass {chain.tradingClass})")

    lo, hi = spot*(1-args.width), spot*(1+args.width)
    strikes = sorted(s for s in chain.strikes if lo <= s <= hi)
    if not strikes: print("No strikes in range."); ib.disconnect(); return

    # build + qualify option contracts
    opts=[]
    for k in strikes:
        for right in ("C","P"):
            opts.append(Option(args.symbol, expiry, k, right, "SMART",
                               tradingClass=chain.tradingClass, multiplier="100"))
    opts = [o for o in ib.qualifyContracts(*opts) if o.conId]

    # greeks via snapshot tickers
    tickers = ib.reqTickers(*opts)
    if all(t.modelGreeks is None for t in tickers) and not args.delayed:
        print("No live greeks — retrying with DELAYED data..."); ib.reqMarketDataType(3)
        tickers = ib.reqTickers(*opts)

    # open interest via a short streaming pass (generic tick 101)
    oi={}
    for o in opts:
        tk = ib.reqMktData(o, "100,101", False, False)
        oi[o.conId]=tk
    ib.sleep(4)
    rows=[]
    for o,t in zip(opts, tickers):
        mg=t.modelGreeks
        tk=oi[o.conId]
        openint = (tk.callOpenInterest if o.right=="C" else tk.putOpenInterest)
        rows.append(dict(strike=o.strike, right=o.right,
                         iv=(mg.impliedVol if mg else None),
                         delta=(mg.delta if mg else None),
                         gamma=(mg.gamma if mg else None),
                         mid=t.marketPrice(), oi=openint))
    for o in opts: ib.cancelMktData(o)
    df=pd.DataFrame(rows)
    ib.disconnect()

    calls=df[df.right=="C"].set_index("strike"); puts=df[df.right=="P"].set_index("strike")

    # ATM straddle -> expected move
    atmk=min(strikes, key=lambda k: abs(k-spot))
    em=None
    try: em=calls.loc[atmk,"mid"]+puts.loc[atmk,"mid"]
    except: pass

    # walls — top-3 OI strikes per side (nearest big one is the actionable level)
    def walls(side, n=3):
        s = side["oi"].dropna()
        return list(s.sort_values(ascending=False).head(n).index) if len(s) else []
    pw = walls(puts); cw = walls(calls)

    # rough gamma flip: OI-weighted gamma, calls +, puts - ; cumulative sign change near spot
    flip=None
    try:
        g=(calls["gamma"].fillna(0)*calls["oi"].fillna(0)
           - puts["gamma"].fillna(0)*puts["oi"].fillna(0))
        cum=g.sort_index().cumsum()
        sign=cum.apply(lambda x: 1 if x>0 else -1)
        chg=sign.ne(sign.shift())
        flips=[k for k,ch in zip(cum.index[1:], chg.iloc[1:]) if ch]
        flip=min(flips, key=lambda k: abs(k-spot)) if flips else None
    except: pass

    # target-delta call (slightly ITM)
    cc=calls.dropna(subset=["delta"]).copy()
    pick=None
    if len(cc):
        pick=cc.assign(dd=(cc["delta"]-args.target_delta).abs()).sort_values("dd").iloc[0]

    print("\n================= DAILY PLAN =================")
    print(f" Spot ....................... {spot:.2f}")
    if em: print(f" ATM straddle (exp. move) ... ±{em:.2f}  ({em/spot*100:.2f}%)  -> 0.5% flush ≈ {spot*0.005:.1f} pts to {spot*0.995:.1f}")
    print(f" SUPPORT  (put walls, top OI) . {', '.join(str(int(x)) for x in pw)}")
    print(f" RESISTANCE (call walls) ...... {', '.join(str(int(x)) for x in cw)}")
    if flip: print(f" ~Gamma flip (rough) ......... {flip}")
    if pick is not None:
        print(f" Buy this call (~{args.target_delta:.2f}Δ, slightly ITM):")
        print(f"     strike {pick.name:.0f}  |  delta {pick['delta']:.2f}  |  IV {pick['iv']*100 if pick['iv'] else float('nan'):.1f}%  |  mid {pick['mid']:.2f}")
    print("=============================================")

    out=f"optionplan_{args.symbol}_{expiry}.csv"; df.sort_values(['strike','right']).to_csv(out,index=False)
    print(f"\nFull chain saved -> {out}")
    print("Read: enter on a 0.5%+ morning dip toward SUPPORT; buy the ~0.6Δ call above; exit ~3:30pm.")

if __name__ == "__main__":
    main()
