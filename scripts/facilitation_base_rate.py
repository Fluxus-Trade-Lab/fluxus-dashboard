#!/usr/bin/env python3
"""How often does the market actually facilitate trade? The base rate.

This is the number that was missing. We can say whether a pattern matched a
given session; until we know how OFTEN it fires we cannot place any claim about
it on the decidability frontier, because the wait is set by the effect size and
the occurrence rate together (`pipeline.reference.power.years_to_decide`).

Two instruments on purpose. He models the auction on **SPY's 30-minute RTH
profile**; ours is built on SPX. If the two disagree about whether a session was
facilitated, that is a fact about our instrument choice and not about the market,
and it should be measured rather than argued about.

Usage:
    .venv/bin/python scripts/facilitation_base_rate.py --months 6
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import ibkr as IBKR
from pipeline.marketcal import market_now
from pipeline.profile import facilitation as F
from pipeline.profile import tpo as MP
from pipeline.reference import power as PW

OUT = Path("data/profile/facilitation_base_rate.json")
# A session needs enough brackets to have an initial balance AND something after
# it. Half days print fewer and would drag the rate toward "no extension" for a
# reason that has nothing to do with the auction.
MIN_BRACKETS = 8


def by_session(bars) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for b in bars:
        day = str(b.date)[:10]
        out[day].append({"low": b.low, "high": b.high, "close": b.close,
                         "volume": float(b.volume or 0)})
    return out


def run(ib, contract, months: int) -> dict:
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr=f"{months} M",
        barSizeSetting="30 mins", whatToShow="TRADES", useRTH=True,
        formatDate=1, timeout=180)
    sessions = by_session(bars)
    # The last session may still be trading; a partial day would be scored as a
    # non-extension purely because its afternoon has not happened yet.
    today = market_now().strftime("%Y-%m-%d")
    sessions.pop(today, None)

    states, rows, skipped = collections.Counter(), [], 0
    for day, bs in sorted(sessions.items()):
        if len(bs) < MIN_BRACKETS:
            skipped += 1
            continue
        f = F.facilitation(bs, MP.initial_balance(bs))
        if not f:
            skipped += 1
            continue
        states[f["state"]] += 1
        rows.append({"date": day, "state": f["state"],
                     "tradeable": f["tradeable"],
                     "up_built": f["up"]["n_periods_built"],
                     "down_built": f["down"]["n_periods_built"]})
    n = len(rows)
    tradeable = sum(1 for r in rows if r["tradeable"])
    return {"n_sessions": n, "skipped_short_sessions": skipped,
            "states": dict(states),
            "tradeable": tradeable,
            "tradeable_rate": (tradeable / n) if n else None,
            "sessions": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=6)
    args = ap.parse_args()

    from ib_async import IB, Index, Stock
    # Shared connect: no startup account/order/position fetch.
    # That fetch hung the post-close chain twice; see pipeline/ibkr.py.
    try:
        ib = IBKR.connect(173, timeout=10)
    except ConnectionError as e:
        sys.exit(str(e))

    results = {}
    try:
        for name, c in (("SPX", Index("SPX", "CBOE")),
                        ("SPY", Stock("SPY", "SMART", "USD"))):
            ib.qualifyContracts(c)
            results[name] = run(ib, c, args.months)
    finally:
        ib.disconnect()

    doc = {"generated_at": market_now().isoformat(timespec="seconds"),
           "months": args.months, "min_brackets": MIN_BRACKETS,
           "thresholds": {"min_build_share": F.MIN_BUILD_SHARE,
                          "min_built_periods": F.MIN_BUILT_PERIODS},
           "instruments": results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2))

    for name, r in results.items():
        n = r["n_sessions"]
        print(f"\n{name}  —  {n} complete sessions "
              f"({r['skipped_short_sessions']} short sessions skipped)")
        for state in ("no_extension", "rejected", "facilitated", "two_sided"):
            c = r["states"].get(state, 0)
            print(f"  {state:<14} {c:>4}   {c/n:>6.1%}" if n else f"  {state:<14} —")
        if n:
            rate = r["tradeable_rate"]
            per_year = rate * 252
            print(f"  ---")
            print(f"  gate opens on {rate:.1%} of sessions  ≈ {per_year:.0f}/year")
            for edge in (0.60, 0.65, 0.70):
                d = PW.years_to_decide(edge, per_year)
                mark = "settleable" if d["decidable_within_3y"] else "out of reach"
                print(f"    to prove a {edge:.0%} edge on this gate: "
                      f"{d['occurrences_needed']:>4} occurrences = "
                      f"{d['years']:>4.1f} years   {mark}")

    a, b = results.get("SPX"), results.get("SPY")
    if a and b:
        sa = {r["date"]: r["state"] for r in a["sessions"]}
        sb = {r["date"]: r["state"] for r in b["sessions"]}
        both = sorted(set(sa) & set(sb))
        agree = sum(1 for d in both if sa[d] == sb[d])
        print(f"\nSPX vs SPY on the same {len(both)} sessions: "
              f"{agree} agree ({agree/len(both):.1%})" if both else "")
        diff = [d for d in both if sa[d] != sb[d]][:6]
        if diff:
            print("  disagreements (instrument choice, not market):")
            for d in diff:
                print(f"    {d}   SPX {sa[d]:<13} SPY {sb[d]}")

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
