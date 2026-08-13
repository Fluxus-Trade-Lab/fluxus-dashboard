#!/usr/bin/env python3
"""
Download intraday bars from IBKR for the July 1-17 seasonal / 0DTE dip-buy backtest.

Pulls ~June 18 -> July 18 each year (covers the July 1-17 window + lead-in) as
5-minute RTH bars, as far back as IBKR serves. Saves one tidy CSV.

For ES it requests the SEPTEMBER contract of each year (the liquid front month during
early-mid July, since the June contract expires ~the 20th). Continuous futures cannot
take a historical endDateTime, so we use the specific expired contract per year with
includeExpired=True.

Prereq: TWS or IB Gateway running with API enabled.
    pip install ib_async pandas

Usage:
    .venv/bin/python scripts/ibkr_intraday_download.py --port 7496          # ES, TWS live
    .venv/bin/python scripts/ibkr_intraday_download.py --symbol SPY --port 7496
    .venv/bin/python scripts/ibkr_intraday_download.py --barsize "1 min"    # finer, less depth
    .venv/bin/python scripts/ibkr_intraday_download.py --iv                 # also pull ATM IV

Instruments:
    ES  -> S&P 500 e-mini future, September expiry per year (best 0DTE-SPX proxy, default)
    SPY -> SPDR S&P 500 ETF (1/10 SPX, RTH only)
    SPX -> S&P 500 cash index
"""
import argparse, time, sys
import pandas as pd
from ib_async import IB, Future, Stock, Index, util


def year_contract(symbol: str, yr: int):
    """Contract to use for that year's July window."""
    if symbol == "ES":
        # September expiry = liquid front month during early/mid July
        return Future("ES", f"{yr}09", "CME", includeExpired=True)
    if symbol == "SPY":
        return Stock("SPY", "SMART", "USD")
    if symbol == "SPX":
        return Index("SPX", "CBOE", "USD")
    raise ValueError(f"unknown symbol {symbol}")


def ensure_connected(ib, args):
    if not ib.isConnected():
        ib.connect(args.host, args.port, clientId=args.clientid, timeout=20)


def pull(ib, contract, end, args, what):
    return ib.reqHistoricalData(
        contract, endDateTime=end, durationStr=args.duration,
        barSizeSetting=args.barsize, whatToShow=what,
        useRTH=bool(args.rth), formatDate=1, keepUpToDate=False,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="ES", choices=["ES", "SPY", "SPX"])
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7497,
                   help="TWS live 7496 / TWS paper 7497 / GW live 4001 / GW paper 4002")
    p.add_argument("--clientid", type=int, default=17)
    p.add_argument("--start-year", type=int, default=2005)
    p.add_argument("--end-year", type=int, default=2025)
    p.add_argument("--barsize", default="5 mins")
    p.add_argument("--duration", default="30 D")
    p.add_argument("--rth", type=int, default=1, help="1=regular hours only, 0=full session incl. overnight (ES globex)")
    p.add_argument("--iv", action="store_true")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    ib = IB()
    print(f"Connecting to {args.host}:{args.port} (clientId={args.clientid}) ...")
    ib.connect(args.host, args.port, clientId=args.clientid, timeout=20)
    print("Connected.")

    frames = []
    for yr in range(args.start_year, args.end_year + 1):
        end = f"{yr}0718 20:00:00 US/Eastern"
        contract = year_contract(args.symbol, yr)
        # qualify (best effort; expired contracts sometimes won't qualify but still return data)
        try:
            ensure_connected(ib, args)
            q = ib.qualifyContracts(contract)
            label = (q[0].localSymbol if q else contract.symbol)
        except Exception as e:
            label = contract.symbol
            print(f"  {yr}: qualify note: {e}")

        bars = []
        for attempt in range(3):
            try:
                ensure_connected(ib, args)
                bars = pull(ib, contract, end, args, "TRADES")
                break
            except Exception as e:
                print(f"  {yr} ({label}) attempt {attempt+1} error: {e}")
                bars = []
                ib.sleep(4)  # let socket settle / reconnect next loop

        if not bars:
            print(f"  {yr} ({label}): no data (IBKR depth may not reach this year)")
            ib.sleep(2)
            continue

        df = util.df(bars)
        df["year"] = yr
        df["contract"] = label
        df["field"] = "price"
        frames.append(df)
        print(f"  {yr} ({label}): {len(df)} bars  {df['date'].min()} -> {df['date'].max()}")
        ib.sleep(11)  # respect IBKR pacing (~60 requests / 10 min)

        if args.iv and args.symbol != "SPX":
            try:
                ensure_connected(ib, args)
                ivb = pull(ib, contract, end, args, "OPTION_IMPLIED_VOLATILITY")
                if ivb:
                    ivdf = util.df(ivb); ivdf["year"] = yr
                    ivdf["contract"] = label; ivdf["field"] = "iv"
                    frames.append(ivdf)
                    print(f"       + {len(ivdf)} IV bars")
                ib.sleep(11)
            except Exception as e:
                print(f"       IV pull failed: {e}")

    ib.disconnect()
    if not frames:
        print("\nNo data retrieved. If you saw 'Not connected', the socket dropped — "
              "rerun; if you saw permission/security-definition errors for every year, "
              "your account may lack CME historical data for expired ES contracts.")
        sys.exit(1)

    rthtag = "rth" if args.rth else "overnight"
    out = args.out or f"ibkr_{args.symbol}_{args.barsize.replace(' ','')}_{rthtag}_julywindows.csv"
    full = pd.concat(frames, ignore_index=True)
    full.to_csv(out, index=False)
    print(f"\nSaved {len(full)} rows -> {out}")
    print("Hand this CSV back to Claude for the intraday 0DTE dip-buy backtest.")


if __name__ == "__main__":
    main()
