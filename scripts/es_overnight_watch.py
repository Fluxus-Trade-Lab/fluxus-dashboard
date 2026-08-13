#!/usr/bin/env python3
"""
Quick ES overnight watch — re-pull on demand to see where the overnight low is forming
vs your support/resistance. Fast (~2 day globex pull). Run it repeatedly through the night.

    .venv/bin/python scripts/es_overnight_watch.py --port 7496
    .venv/bin/python scripts/es_overnight_watch.py --support 7525 --resistance 7600

Prints: current ES, prior RTH close, overnight high/low (+ time of low), dip% from close,
distance to your levels, and the last 8 bars so you can read momentum.
"""
import argparse, datetime as dt
import pandas as pd
from ib_async import IB, ContFuture, util

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=7496)
    p.add_argument("--clientid", type=int, default=49)
    p.add_argument("--support", type=float, default=7525.0)
    p.add_argument("--resistance", type=float, default=7600.0)
    args=p.parse_args()

    ib=IB(); ib.connect(args.host,args.port,clientId=args.clientid,timeout=20)
    c=ContFuture("ES","CME"); ib.qualifyContracts(c)
    bars=ib.reqHistoricalData(c, endDateTime="", durationStr="2 D",
        barSizeSetting="5 mins", whatToShow="TRADES", useRTH=False,
        formatDate=1, keepUpToDate=False)
    ib.disconnect()
    if not bars: print("no data"); return
    df=util.df(bars); df['dt']=pd.to_datetime(df['date'])
    df=df.sort_values('dt').reset_index(drop=True)

    now=df.iloc[-1]; cur=now['close']
    # most recent RTH close (~16:00 ET) that is before the last bar
    closes=df[df['dt'].dt.time<=dt.time(16,0)]
    # find last bar on the most recent completed RTH day close
    df['d']=df['dt'].dt.date
    # reference = last 15:55/16:00 bar strictly before 'now' by at least a few bars
    ref=df[(df['dt'].dt.time>=dt.time(15,55))&(df['dt'].dt.time<=dt.time(16,5))&(df['dt']<now['dt'])]
    prior_close = ref.iloc[-1]['close'] if len(ref) else df.iloc[0]['close']
    ref_dt = ref.iloc[-1]['dt'] if len(ref) else df.iloc[0]['dt']
    on = df[df['dt']>ref_dt]   # overnight session since that RTH close
    if len(on)==0: on=df.tail(20)
    on_low=on['low'].min(); on_low_dt=on.loc[on['low'].idxmin(),'dt']
    on_high=on['high'].max()

    print(f"\n===== ES OVERNIGHT WATCH  ({now['dt']:%Y-%m-%d %H:%M} ET) =====")
    print(f" Current ES ............ {cur:.2f}")
    print(f" Prior RTH close ....... {prior_close:.2f}  ({(cur/prior_close-1)*100:+.2f}% since close)")
    print(f" Overnight HIGH ........ {on_high:.2f}")
    print(f" Overnight LOW ......... {on_low:.2f}   at {on_low_dt:%H:%M} ET   ({(on_low/prior_close-1)*100:+.2f}% vs close)")
    print(f" Your SUPPORT .......... {args.support:.0f}   ({(cur-args.support):+.0f} pts away)")
    print(f" Your RESISTANCE ....... {args.resistance:.0f}   ({(cur-args.resistance):+.0f} pts away)")
    zone = "*** IN/NEAR SUPPORT — watch for a hold ***" if cur<=args.support+8 else ""
    if zone: print(f" {zone}")
    print(f"\n last 8 bars (ET  O/H/L/C):")
    for _,b in df.tail(8).iterrows():
        print(f"   {b['dt']:%H:%M}  {b['open']:.2f} {b['high']:.2f} {b['low']:.2f} {b['close']:.2f}")
    print("="*46)

if __name__=="__main__":
    main()
