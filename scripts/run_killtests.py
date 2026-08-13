#!/usr/bin/env python3
"""Put our own candidate rules through his kill test and publish the death count.

The point is not to find a winner. It is to build the denominator: he reports
17 dead volatility signals, a dead leverage overlay, and 8 base assets that lost
to plain SPY, and that count is what makes his survivors mean anything.

## The overlay is a PROXY and is labelled as one

He runs defined-risk option structures on dislocations. We have no historical
option chains, so the overlay here is modelled as **de-risking**: on an active
day the book holds `1 - HEDGE` of the base exposure.

This understates a real defined-risk overlay in one direction and overstates it
in the other, and both should be stated:

  * it has **no convexity** — a put pays accelerating amounts in a crash, a
    linear de-risk does not, so a genuine structure would look BETTER here
  * it has **no premium cost** — a de-risk is free, a structure is not, so a
    genuine structure would look WORSE here

A rule that cannot survive as a free linear hedge will not survive as a paid
convex one. That makes this a permissive first screen, and a survivor here is a
candidate for real testing, never a result.

## Lookahead

Every signal is computed from the PRIOR session's completed bars and applied to
the NEXT session's return. The kill test cannot detect lookahead, so the offset
is done in one place, `_lag`, and stated in the kill log for every rule.

Usage:
    .venv/bin/python scripts/run_killtests.py --years 2
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.book import killlog as KL
from pipeline.book import killtest as K
from pipeline.book import metrics as M
from pipeline.marketcal import market_now
from pipeline.profile import facilitation as F
from pipeline.profile import tff as T
from pipeline.profile import tpo as MP

HEDGE = 0.50            # how much exposure comes off on an active day
TICK = 0.25             # SPY price bucket, ~ SPX 2.5 at a 10:1 index ratio
MIN_BRACKETS = 8
OUT = Path("data/book/killtest_run.json")


def _lag(flags: dict[str, bool], days: list[str]) -> list[bool]:
    """Yesterday's signal, applied to today. The ONLY place the offset happens.

    `days[i]`'s return is acted on with the flag computed from `days[i-1]`, whose
    session had already closed. Day zero has no prior session and is inactive.
    """
    return [False] + [flags.get(days[i - 1], False) for i in range(1, len(days))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    ap.add_argument("--draws", type=int, default=1500)
    args = ap.parse_args()

    from ib_async import IB, Stock
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=183, timeout=10)
            break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")
    try:
        spy = Stock("SPY", "SMART", "USD")
        ib.qualifyContracts(spy)
        daily = ib.reqHistoricalData(spy, endDateTime="",
                                     durationStr=f"{args.years} Y",
                                     barSizeSetting="1 day", whatToShow="TRADES",
                                     useRTH=True, formatDate=1, timeout=180)
        half = ib.reqHistoricalData(spy, endDateTime="",
                                    durationStr=f"{args.years} Y",
                                    barSizeSetting="30 mins", whatToShow="TRADES",
                                    useRTH=True, formatDate=1, timeout=300)
    finally:
        ib.disconnect()

    closes = {str(b.date)[:10]: b.close for b in daily}
    sess: dict[str, list[dict]] = collections.defaultdict(list)
    for b in half:
        sess[str(b.date)[:10]].append({"low": b.low, "high": b.high,
                                       "close": b.close})
    sess = {d: bs for d, bs in sess.items() if len(bs) >= MIN_BRACKETS}

    days = sorted(set(closes) & set(sess))
    base = [0.0] + [closes[days[i]] / closes[days[i - 1]] - 1.0
                    for i in range(1, len(days))]
    print(f"{len(days)} sessions  {days[0]} .. {days[-1]}")
    print(f"buy-and-hold SPY: {json.dumps(M.summary(base))}")

    # --- the candidate signals, each computed from that session's own bars ---
    fac = {d: F.facilitation(bs, MP.initial_balance(bs)) for d, bs in sess.items()}
    tables = {m: T.build_table(sess, TICK, measure=m) for m in T.MEASURES}
    tffs = {}
    for d, bs in sess.items():
        r = T.read(bs, TICK, tables)
        tffs[d] = r["measures"]["tpo"]["tff"] if r and r.get("measurable") else None

    candidates = {
        "gate shut (rejected or no extension)":
            ({d: (f or {}).get("state") in ("rejected", "no_extension")
              for d, f in fac.items()},
             "a session that extended and never built, or never left the initial "
             "balance, is followed by damage worth de-risking into"),
        "gate shut, rejected only":
            ({d: (f or {}).get("state") == "rejected" for d, f in fac.items()},
             "the market went to look and declined — the 18% case the base rate "
             "says the rule exists for"),
        "two-sided extension":
            ({d: (f or {}).get("state") == "two_sided" for d, f in fac.items()},
             "both sides extended: an unresolved auction, so de-risk"),
        "TFF non-facilitating (bottom quartile)":
            ({d: (v is not None and v <= 0.25) for d, v in tffs.items()},
             "Jones' cardinal rule — avoid markets that are not facilitating "
             "trade; a quiet tape warns of range expansion"),
        "TFF dead (bottom 5%)":
            ({d: (v is not None and v <= 0.05) for d, v in tffs.items()},
             "the strict reading of the cardinal rule"),
        "TFF expansive (top decile)":
            ({d: (v is not None and v >= 0.90) for d, v in tffs.items()},
             "the opposite hypothesis: it is the BUSY tape that precedes damage. "
             "Tested so the quiet-tape rules have a mirror to lose to"),
    }

    now = market_now()
    results, rows = [], []
    for name, (flags, hypothesis) in candidates.items():
        active = _lag(flags, days)
        overlay = [-HEDGE * b for b in base]
        r = K.kill_test(name, base, overlay, active, draws=args.draws)
        sh = K.shuffled_control(name, base, overlay, active, draws=args.draws)
        results.append({"rule": r, "shuffled": sh})
        for res in (r, sh):
            row = KL.entry(res, hypothesis=hypothesis,
                           computed_from="prior session's completed 30-min bars",
                           date=now.strftime("%Y-%m-%d"))
            KL.append(row)
            rows.append(row)
        print(f"\n[{r['verdict']:<9}] {name}")
        print(f"     {r['note']}")
        print(f"     timing-shuffled control -> {sh['verdict']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"generated_at": now.isoformat(timespec="seconds"),
         "sessions": len(days), "first": days[0], "last": days[-1],
         "hedge": HEDGE, "overlay_model": "linear de-risk proxy, no convexity, "
                                          "no premium cost",
         "buy_and_hold": M.summary(base),
         "results": results}, indent=2))
    print("\n" + "=" * 66)
    print(KL.report())
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
