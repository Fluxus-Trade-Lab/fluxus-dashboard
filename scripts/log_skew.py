#!/usr/bin/env python3
"""Append one row per underlying per day to the skew store.

Two-pass by design. Asking for a whole chain to find two strikes exhausts
IBKR's market-data lines — the first attempt at this starved SPY and QQQ of
quotes entirely while DIA, which ran last, came back complete. So:

  pass 1  ~9 strikes around spot        -> ATM IV
  pass 2  ~7 strikes around the strike  -> the 25-delta wings
          that ATM IV says is 25-delta

which is ~30 lines per underlying instead of ~160.

IV is solved against the put-call parity forward, never spot: solving an index
option off spot ran about 1.1 vol points light the last time we tried it.

Usage:
    .venv/bin/python scripts/log_skew.py                    # SPY QQQ DIA, ~30 DTE
    .venv/bin/python scripts/log_skew.py --symbols SPY --dte 60
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.gex.blackscholes import bs_delta, implied_vol
from pipeline.marketcal import market_now, market_today
from pipeline.reference import skew_log as SK
from pipeline.reference.context import percentile_of

TARGET_DELTA = 0.25
# N^-1(0.75); the log-moneyness of a 25-delta strike is ~this many sigma out.
Z75 = 0.6745


def _mid(t):
    b, a = t.bid, t.ask
    if b is not None and a is not None and b > 0 and a > 0 and a >= b:
        return (a + b) / 2
    return None


def _quote(ib, contracts, wait: float):
    """Subscribe, wait, read mids, then release the lines before returning.

    Releasing matters more than it looks: the lines are the scarce resource and
    the next underlying cannot be measured until they come back.
    """
    from ib_async import Option
    tk = [ib.reqMktData(c, "", False, False) for c in contracts]
    ib.sleep(wait)
    out = {(c.right, c.strike): _mid(t) for c, t in zip(contracts, tk)
           if _mid(t) is not None}
    for t in tk:
        ib.cancelMktData(t.contract)
    ib.sleep(1.0)
    return out


def _forward(px: dict) -> float | None:
    """Put-call parity forward, read off the strike where |C-P| is smallest."""
    both = [k for (r, k) in px if r == "C" and ("P", k) in px]
    if not both:
        return None
    k0 = min(both, key=lambda k: abs(px[("C", k)] - px[("P", k)]))
    return k0 + (px[("C", k0)] - px[("P", k0)])


def measure(ib, symbol: str, target_dte: int, wait: float) -> dict | None:
    from ib_async import Option, Stock

    today = market_today()
    u = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(u)
    tu = ib.reqMktData(u, "", False, False)
    ib.sleep(3)
    spot = tu.last if tu.last == tu.last else tu.close
    ib.cancelMktData(u)
    if not spot:
        print(f"  {symbol}: no underlying quote")
        return None

    params = [c for c in ib.reqSecDefOptParams(u.symbol, "", u.secType, u.conId)
              if c.exchange == "SMART"]
    if not params:
        print(f"  {symbol}: no SMART option params")
        return None
    # SPY returns SEVERAL SMART chains and the first can be a special trading
    # class ("2SPY": three strikes, three expiries). Qualifying normal expiries
    # against it fails wholesale and read as "no quotes" — the correct chain is
    # the one that actually lists the strikes.
    ch = max(params, key=lambda c: len(c.strikes))
    exps = sorted(e for e in ch.expirations if e > today.strftime("%Y%m%d"))
    if not exps:
        return None
    expiry = min(exps, key=lambda e: abs(
        (dt.datetime.strptime(e, "%Y%m%d").date() - today).days - target_dte))
    dte = (dt.datetime.strptime(expiry, "%Y%m%d").date() - today).days
    T = dte / 365.0
    grid = sorted(ch.strikes)

    def near(price, n):
        """The n listed strikes closest to `price`, back in ascending order."""
        return sorted(sorted(grid, key=lambda s: abs(s - price))[:n])

    def opts(strikes):
        c = [Option(symbol, expiry, s, r, "SMART", tradingClass=ch.tradingClass)
             for s in strikes for r in ("C", "P")]
        return [o for o in ib.qualifyContracts(*c) if o is not None and o.conId]

    # ---- pass 1: the money ----
    px = _quote(ib, opts(near(spot, 9)), wait)
    fwd = _forward(px)
    if fwd is None:
        print(f"  {symbol}: no two-sided quotes at the money — not measurable")
        return None
    atm_ivs = [iv for (r, k), p in px.items()
               if abs(k - fwd) <= 0.02 * fwd
               and (iv := implied_vol(p, fwd, k, T, r)) and 0.01 < iv < 3.0]
    if not atm_ivs:
        print(f"  {symbol}: quotes but no solvable ATM IV")
        return None
    atm_iv = sum(atm_ivs) / len(atm_ivs)

    # ---- pass 2: where ATM vol says the 25-delta wings sit ----
    shift = Z75 * atm_iv * math.sqrt(T)
    wings = sorted(set(near(fwd * math.exp(shift), 4) + near(fwd * math.exp(-shift), 4)))
    px2 = _quote(ib, opts(wings), wait)

    rows = []
    for (r, k), p in {**px, **px2}.items():
        iv = implied_vol(p, fwd, k, T, r)
        if iv and 0.01 < iv < 3.0:
            rows.append({"right": r, "strike": k, "delta": bs_delta(fwd, k, T, iv, r),
                         "iv": iv})
    calls = [x for x in rows if x["right"] == "C" and 0.10 < x["delta"] < 0.45]
    puts = [x for x in rows if x["right"] == "P" and -0.45 < x["delta"] < -0.10]

    def pick(cands, target):
        if not cands:
            return None
        b = min(cands, key=lambda x: abs(abs(x["delta"]) - target))
        return {"strike": b["strike"], "delta": b["delta"], "iv": b["iv"]}

    return SK.entry(date=str(today), symbol=symbol, expiry=expiry, dte=dte,
                    spot=spot, forward=fwd, atm_iv=atm_iv, source="solved_mid",
                    measured_at=market_now().isoformat(timespec="seconds"),
                    call_25d=pick(calls, TARGET_DELTA),
                    put_25d=pick(puts, TARGET_DELTA), n_solved=len(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="SPY,QQQ,DIA")
    ap.add_argument("--dte", type=int, default=30)
    ap.add_argument("--wait", type=float, default=12.0, help="seconds per quote pass")
    ap.add_argument("--log", default=str(SK.DEFAULT_LOG))
    ap.add_argument("--force", action="store_true",
                    help="measure outside RTH anyway (the row will not be a session smile)")
    args = ap.parse_args()

    from ib_async import IB
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=161, timeout=10)
            break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")

    now = market_now()
    print(f"skew log @ {now:%Y-%m-%d %H:%M ET}  target {args.dte} DTE")
    if not (dt.time(9, 30) <= now.time() <= dt.time(16, 0) and now.weekday() < 5):
        print("  WARNING: outside RTH — option quotes are one-sided or absent, and a "
              "row measured now is not the day's smile. Nothing will be written.")
        if not args.force:
            ib.disconnect()
            sys.exit(2)
    written = 0
    try:
        for sym in [s.strip().upper() for s in args.symbols.split(",") if s.strip()]:
            try:
                row = measure(ib, sym, args.dte, args.wait)
            except Exception as e:                       # one bad symbol must not
                print(f"  {sym}: {type(e).__name__}: {e}")   # cost us the others
                continue
            if not row:
                continue
            fresh = SK.append(row, args.log)
            written += bool(fresh)
            hist = SK.series(SK.read(args.log), sym, "call_skew")
            cs, rr = row["call_skew"], row["risk_reversal"]
            line = (f"  {sym}  {row['expiry']} ({row['dte']}d)  spot {row['spot']:,.2f}  "
                    f"ATM {row['atm_iv']*100:.2f}%  callskew "
                    + (f"{cs*100:+.2f}" if cs is not None else "n/a"))
            if rr is not None:
                line += f"  RR {rr*100:+.2f}"
            if cs is not None and len(hist) >= 2:
                pc = percentile_of(cs, hist)
                line += (f"   -> {pc['pct']:.0f}th pct of n={pc['n']}"
                         + ("  [THIN]" if pc["thin"] else ""))
            print(line + ("" if fresh else "   (already logged today)"))
    finally:
        ib.disconnect()
    print(f"\n{written} new row(s) -> {args.log}")


if __name__ == "__main__":
    main()
