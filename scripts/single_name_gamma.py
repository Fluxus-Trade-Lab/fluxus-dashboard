#!/usr/bin/env python3
"""Single-name option gamma / earnings structure from IBKR.

Reuses the Fluxus GEX engine's math (pipeline.gex.compute) and connection
(pipeline.gex.ibkr) but is otherwise self-contained, so it can be lifted into a
standalone options-flow project later.

WHAT IT REPORTS, per expiry:
  - ATM straddle  = the market's implied move (the headline number for earnings)
  - ATM IV        = pre-event inflated; crushes after the print
  - OI walls      = top call/put open-interest strikes (where dealers hedge a gap)
  - net GEX / pin / flip  (SHOWN WITH A CAVEAT — see below)

CAVEAT ON SINGLE-NAME GEX SIGN:
  net GEX assumes dealers are long calls / short puts. That is an *index*-flow
  heuristic. In a single stock much of the OI is customer hedges and covered
  calls, so the net-GEX SIGN and pin are low-confidence. Trust the straddle
  (implied move) and the OI walls — those are assumption-free.

Prereq: TWS / IB Gateway running with API enabled. Works during RTH (live
greeks) and pre-market (falls back to the prior settle via frozen data), which
matters when you run it the morning of an earnings gap.

Usage:
    .venv/bin/python scripts/single_name_gamma.py TSM
    .venv/bin/python scripts/single_name_gamma.py NVDA --width 0.12 --expiries 3
    .venv/bin/python scripts/single_name_gamma.py AVGO --client-id 25
"""
import argparse
import math
import sys
from pathlib import Path

import pandas as pd
from ib_async import Stock, Option

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root for `pipeline`
from pipeline.gex import ibkr, compute

MDT_LIVE, MDT_FROZEN = 1, 2
OI_SETTLE_SECONDS = 12          # LIVE OI ticks
GREEKS_SETTLE_SECONDS = 5       # FROZEN greeks snapshot


def _num(x):
    try:
        x = float(x)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def resolve_stock(ib, symbol):
    u = Stock(symbol, "SMART", "USD")
    if not ib.qualifyContracts(u):
        raise SystemExit(f"Could not qualify {symbol} as a US-listed stock.")
    t = ib.reqTickers(u)[0]
    spot = _num(t.last) or _num(t.marketPrice()) or _num(t.close)
    if spot is None:
        raise SystemExit(f"No spot for {symbol}. Is TWS connected with data?")
    chains = ib.reqSecDefOptParams(u.symbol, "", "STK", u.conId)
    ch = next((c for c in chains if c.exchange == "SMART"), chains[0])
    return spot, ch


def infer_step(strikes):
    """Smallest positive spacing between adjacent strikes (handles $1/$2.5/$5)."""
    s = sorted(set(strikes))
    diffs = [round(b - a, 4) for a, b in zip(s, s[1:]) if b > a]
    return min(diffs) if diffs else 1.0


def pull_expiry(ib, symbol, ch, expiry, spot, width):
    lo, hi = spot * (1 - width), spot * (1 + width)
    strikes = sorted(k for k in ch.strikes if lo <= k <= hi)
    opts = [Option(symbol, expiry, k, r, "SMART", tradingClass=ch.tradingClass)
            for k in strikes for r in ("C", "P")]
    opts = [o for o in ib.qualifyContracts(*opts) if getattr(o, "conId", None)]
    if not opts:
        return None
    # Two-phase (same trick as the index engine): LIVE delivers OI (static
    # clearing data, arrives even pre-open), then FROZEN fills greeks/IV/price
    # from the last settle when live quotes are dark.
    ib.reqMarketDataType(MDT_LIVE)
    handles = [ib.reqMktData(o, "100,101", False, False) for o in opts]
    try:
        ib.sleep(OI_SETTLE_SECONDS)
        ib.reqMarketDataType(MDT_FROZEN)
        ib.sleep(GREEKS_SETTLE_SECONDS)
        rows = []
        for o, h in zip(opts, handles):
            mg = h.modelGreeks
            rows.append(dict(
                strike=float(o.strike), right=o.right,
                gamma=_num(mg.gamma) if mg else None,
                iv=_num(mg.impliedVol) if mg else None,
                mid=_num(h.marketPrice()) or _num(h.close),
                oi=_num(h.callOpenInterest if o.right == "C" else h.putOpenInterest),
            ))
    finally:
        for o in opts:
            ib.cancelMktData(o)
    return pd.DataFrame(rows)


def fmt_walls(walls, n=4):
    return "  ".join(f"{int(w['strike'])}({int(w['oi'])})" for w in walls[:n]) or "—"


def report(symbol, spot, results):
    print(f"\n{'='*66}")
    print(f" {symbol}  spot ${spot:.2f}   single-name option gamma")
    print(f"{'='*66}")
    print(" NOTE: net-GEX sign/pin are LOW-confidence for single names "
          "(dealer-\n       side assumption is index-flow). Trust the straddle "
          "+ OI walls.\n")
    for label, expiry, m in results:
        print(f" --- {label}  ({expiry}) ---")
        if m is None:
            print("   (no qualifying contracts in band)\n")
            continue
        print(f"   quality={m['quality']}  greekCov={m['greeks_coverage']:.0%}  "
              f"oiCov={m['oi_coverage']:.0%}")
        if m["straddle"]:
            mv = m["straddle"] / spot * 100
            iv = f"{m['atm_iv']:.0%}" if m["atm_iv"] else "n/a"
            print(f"   IMPLIED MOVE  ±{mv:.1f}%  (±${m['straddle']:.2f} straddle)"
                  f"   ATM IV {iv}")
            print(f"     → range: ${spot - m['straddle']:.0f}  ..  "
                  f"${spot + m['straddle']:.0f}")
        gex = f"{m['net_gex_mm']:+,.1f}" if m["net_gex_mm"] is not None else "n/a"
        print(f"   call wall {m['call_wall']}   put wall {m['put_wall']}   "
              f"pin {m['pin']}   [net GEX {gex} $mm — low-conf sign]")
        print(f"   top call OI:  {fmt_walls(m['walls_top_calls'])}")
        print(f"   top put OI:   {fmt_walls(m['walls_top_puts'])}\n")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("symbol", help="ticker, e.g. TSM NVDA AVGO")
    p.add_argument("--width", type=float, default=0.10,
                   help="strike band +/- fraction of spot (default 0.10; single "
                        "names gap far more than indices)")
    p.add_argument("--expiries", type=int, default=2,
                   help="how many nearest expiries to pull (default 2)")
    p.add_argument("--client-id", type=int, default=22)
    args = p.parse_args()
    symbol = args.symbol.upper()

    ib = ibkr.connect(client_id=args.client_id, market_data_type=MDT_LIVE)
    try:
        spot, ch = resolve_stock(ib, symbol)
        exps = sorted(ch.expirations)[:args.expiries]
        if not exps:
            raise SystemExit(f"No listed option expiries for {symbol}.")
        results = []
        for i, e in enumerate(exps):
            label = "FRONT (nearest — captures the next event)" if i == 0 \
                else f"expiry +{i}"
            df = pull_expiry(ib, symbol, ch, e, spot, args.width)
            m = compute.compute_tenor(df, spot=spot, multiplier=100) if df is not None else None
            results.append((label, e, m))
    finally:
        ib.disconnect()
    report(symbol, spot, results)


if __name__ == "__main__":
    main()
