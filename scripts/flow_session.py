#!/usr/bin/env python3
"""Pull the settled option tape after the close and produce the flow read.

The second opinion, and the only phase of the plan with a real data cost. It
runs LAST in the daily chain and its failure is never fatal: a brief without a
flow read says so, and a brief that waited for one would be no brief at all.

## Why post-close and not live

Prints settle. A read assembled during the session is a read of a partial book,
and the question it answers — "was the belt bid today" — is not answerable until
today is over. The live engine in the OptionsFlow repo is the intraday tool;
this is the record.

## The classification is OFF by default, and the reason is measured

Aggressor classification needs the contemporaneous NBBO. Measured on SPX 7750C,
2026-08-12:

    TRADES     3,514 ticks    4 pages     1.9s
    BID_ASK   60,648 ticks   60 pages     142s   and still not finished

Eighty contracts of quote ticks is about three hours. That does not fit a daily
chain, and the cheap substitute does not work: 1-minute BID/ASK bars agreed with
the tick NBBO on only 56.7% of 769 overlapping prints, against a 50% coin, with
symmetric disagreements. Noise, not a cheaper measurement.

So the default pull is TRADES only -- about 1.9s a contract -- and every
side-dependent reading comes back `unknown` rather than guessed. `--with-quotes`
does it properly and takes hours; it exists for a single session worth studying,
not for the chain.

Usage:
    .venv/bin/python scripts/flow_session.py --symbol SPX
    .venv/bin/python scripts/flow_session.py --symbol SPX --with-quotes   # hours
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd

from pipeline.flow import atm_core, enrich, quote_rule
from pipeline.flow import session as FS
from pipeline import ibkr as IBKR
from pipeline.marketcal import MARKET_TZ, market_now, market_today

OUT_DIR = Path("data/flow")
LOG = OUT_DIR / "session_reads.jsonl"
TICK_PAGE = 1000            # IBKR's per-request cap for reqHistoricalTicks
MAX_PAGES = 40              # per contract per side; 40k ticks is far past real
# strikes*2. Measured: ~2s a contract for TRADES, so 100 contracts is about
# five minutes -- inside the chain's 900s ceiling. It was 40, and 40 covered only
# +/-0.6% of spot, which put every strike in the belt and made the belt/wings
# split vacuous. The wings are half the question and have to be sampled.
BUDGET_CONTRACTS = 100


def _et(day: str, h: int, m: int) -> dt.datetime:
    return dt.datetime.strptime(day, "%Y%m%d").replace(
        hour=h, minute=m, tzinfo=MARKET_TZ)


def _ticks(ib, contract, day: str, what: str) -> list:
    """One contract's ticks for one RTH session, paged forward from the open.

    Paging FORWARD from 09:30 rather than backward from the close: a backward
    walk that hits MAX_PAGES loses the morning, and the morning is where the
    positioning gets put on. A forward walk that hits the cap loses the
    afternoon and says so.
    """
    out, cursor = [], _et(day, 9, 30)
    end = _et(day, 16, 15)
    for _ in range(MAX_PAGES):
        batch = ib.reqHistoricalTicks(
            contract, startDateTime=cursor, endDateTime="",
            numberOfTicks=TICK_PAGE, whatToShow=what, useRth=True,
            ignoreSize=False)
        if not batch:
            break
        out.extend(batch)
        last = batch[-1].time
        if last >= end or len(batch) < TICK_PAGE:
            break
        cursor = last + dt.timedelta(microseconds=1)
    return out


def _frame(ticks, kind: str) -> pd.DataFrame:
    if not ticks:
        cols = (["time", "price", "size"] if kind == "trades"
                else ["time", "bid", "ask"])
        return pd.DataFrame({c: pd.Series(dtype="float64") for c in cols})
    if kind == "trades":
        rows = [{"time": t.time, "price": float(t.price), "size": float(t.size)}
                for t in ticks if getattr(t, "price", 0)]
    else:
        rows = [{"time": t.time, "bid": float(t.priceBid),
                 "ask": float(t.priceAsk)} for t in ticks]
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--date", help="YYYYMMDD (ET). Default: last complete session.")
    ap.add_argument("--budget", type=int, default=BUDGET_CONTRACTS)
    ap.add_argument("--with-quotes", action="store_true",
                    help="Also pull BID_ASK ticks so prints can be classified. "
                         "~142s PER CONTRACT — hours for a full chain. Without "
                         "it every side-dependent reading is reported unknown.")
    ap.add_argument("--sigma", type=float, default=2.5,
                    help="How many daily sigma of strikes to cover. Wider than "
                         "the 0DTE core because the WINGS are half the question.")
    args = ap.parse_args()

    now = market_now()
    if args.date:
        day = args.date
    else:
        d = market_today(now)
        if now.time() < dt.time(16, 0):
            d -= dt.timedelta(days=1)
        while d.weekday() > 4:
            d -= dt.timedelta(days=1)
        day = d.strftime("%Y%m%d")
    pretty = f"{day[:4]}-{day[4:6]}-{day[6:]}"

    from ib_async import IB, Index, Option, Stock
    # Shared connect: no startup account/order/position fetch.
    # That fetch hung the post-close chain twice; see pipeline/ibkr.py.
    try:
        ib = IBKR.connect(187, timeout=10)
    except ConnectionError as e:
        sys.exit(str(e))

    try:
        under = (Index("SPX", "CBOE") if args.symbol == "SPX"
                 else Stock(args.symbol, "SMART", "USD"))
        ib.qualifyContracts(under)
        bars = ib.reqHistoricalData(under, endDateTime=_et(day, 16, 0),
                                    durationStr="1 D", barSizeSetting="1 day",
                                    whatToShow="TRADES", useRTH=True,
                                    formatDate=1, timeout=60)
        if not bars:
            sys.exit(f"no {args.symbol} bar for {pretty} — is it a trading day?")
        spot = bars[-1].close

        params = ib.reqSecDefOptParams(under.symbol, "", under.secType,
                                       under.conId)
        # SPY/QQQ list a stub chain ("2SPY", 3 strikes) first; taking [0] made
        # every qualify fail once already. Take the richest.
        chains = [c for c in params if c.exchange == "SMART"] or params
        chain = max(chains, key=lambda c: len(c.strikes))
        expiries = sorted(e for e in chain.expirations if e >= day)
        if not expiries:
            sys.exit(f"no expiry at or after {pretty} in the chain")
        expiry = expiries[0]

        strikes = atm_core.select_core(spot, sorted(chain.strikes),
                                       budget_contracts=args.budget,
                                       max_sigma=args.sigma,
                                       daily_sigma_pct=0.01)
        print(f"{args.symbol} {pretty}  spot {spot:,.2f}  expiry {expiry}  "
              f"{len(strikes)} strikes {min(strikes):,.0f}-{max(strikes):,.0f}")

        prints, missing, done = [], 0, 0
        for k in strikes:
            for right in ("C", "P"):
                opt = Option(under.symbol, expiry, k, right,
                             "SMART", tradingClass=chain.tradingClass)
                try:
                    ib.qualifyContracts(opt)
                except Exception:
                    missing += 1
                    continue
                if not opt.conId:
                    missing += 1
                    continue
                trades = _frame(_ticks(ib, opt, day, "TRADES"), "trades")
                if trades.empty:
                    continue
                if args.with_quotes:
                    quotes = _frame(_ticks(ib, opt, day, "BID_ASK"), "quotes")
                    merged = enrich.enrich_trades(trades, quotes)
                    for row in merged.itertuples():
                        prints.append({
                            "strike": float(k), "right": right,
                            "price": float(row.price), "size": float(row.size),
                            "side": quote_rule.classify(
                                row.price,
                                None if pd.isna(row.bid) else float(row.bid),
                                None if pd.isna(row.ask) else float(row.ask),
                                None if pd.isna(row.prev_price) else float(row.prev_price)),
                        })
                else:
                    # No quotes pulled, so no print gets a side. UNKNOWN is the
                    # honest label and session.py turns it into an explicit
                    # "unknown" reading rather than a balanced one.
                    for row in trades.itertuples():
                        prints.append({"strike": float(k), "right": right,
                                       "price": float(row.price),
                                       "size": float(row.size),
                                       "side": "UNKNOWN"})
                done += 1
                if done % 10 == 0:
                    print(f"    ... {done} contracts, {len(prints):,} prints",
                          flush=True)
    finally:
        ib.disconnect()

    if not prints:
        sys.exit(f"no prints for {pretty} — nothing to read")

    read = FS.session_read(prints, spot, pretty)
    read["symbol"] = args.symbol
    read["expiry"] = expiry
    read["generated_at"] = now.isoformat(timespec="seconds")
    read["contracts_unavailable"] = missing
    read["quotes_pulled"] = bool(args.with_quotes)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"flow_{args.symbol}_{day}.json").write_text(json.dumps(read, indent=2))
    # Append-only history is what makes "does it repeat" answerable at all.
    with LOG.open("a") as f:
        f.write(json.dumps({k: read[k] for k in
                            ("session", "symbol", "spot", "n_prints",
                             "total_premium", "belt_bid", "generated_at")}) + "\n")

    bs = read["block_summary"]
    print(f"  {read['n_prints']:,} prints   "
          f"${read['total_premium'] / 1e6:,.1f}M premium   "
          f"blocks {bs['block_share']:.1%} (lot rule would say "
          f"{bs['large_lot_share']:.1%}, they agree on {bs['agreement']:.0%})")
    for z, b in read["zones"].items():
        if not b["premium"]:
            print(f"  {z:<11} —")
            continue
        lift = f"{b['net_lift']:+.0%}" if b["net_lift"] is not None else "  ?  "
        print(f"  {z:<11} {b['share_of_session']:>6.1%} of premium   "
              f"net lift {lift}   classified {b['classified_share']:.0%}   "
              f"blocks {b['block_share']:.0%}")
    if not read["zones_covered"]:
        print(f"\n  !! {read['coverage_note']}")
    bb = read["belt_bid"]
    print(f"\n  BELT: {bb['state'].upper()} — {bb['note']}")

    hist = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
    hist = [h for h in hist if h.get("symbol") == args.symbol]
    r = FS.repeats(hist, bb["state"]) if bb["state"] != "unknown" else None
    if r:
        print(f"  RUN:  {r['consecutive']} consecutive '{r['state']}' "
              f"through {r['through']} — {r['reading']}")
    print("\n  belt width sweep:")
    for row in read["belt_sweep"]:
        star = "  <- shipped" if row["belt_pct"] == FS.BELT_PCT else ""
        lift = f"{row['net_lift']:+.0%}" if row["net_lift"] is not None else "   ?"
        print(f"    {row['belt_pct']:>6.3%}  {row['belt_strikes']:>2} strikes  "
              f"{row['belt_share']:>6.1%} of premium  {row['belt_state']:<9} "
              f"{lift}{star}")
    print(f"\nwrote {OUT_DIR}/flow_{args.symbol}_{day}.json")


if __name__ == "__main__":
    main()
