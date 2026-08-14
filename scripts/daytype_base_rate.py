#!/usr/bin/env python3
"""Base rates for the auction's development stage, and the sweep behind the cuts.

A classifier without base rates is a relabelling. These are the numbers that say
whether the day types carve anything, how often each state appears, and — with
`power.years_to_decide` — how long any claim conditioned on a state would take
to settle.

The sweep is not optional decoration. The width cuts are ours, not Dalton's, and
publishing what they do to the distribution is the only thing standing between a
five-way classifier and a free-parameter farm.

Usage:
    .venv/bin/python scripts/daytype_base_rate.py --years 2
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
from pipeline.profile import daytype as D
from pipeline.profile import tpo as MP
from pipeline.reference import power as PW

OUT = Path("data/profile/daytype_base_rate.json")
MIN_BRACKETS = 8
INSTRUMENTS = {"SPX": 2.5, "SPY": 0.25}


def _sessions(bars) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for b in bars:
        out[str(b.date)[:10]].append({"low": b.low, "high": b.high,
                                      "open": b.open, "close": b.close})
    return {d: bs for d, bs in out.items() if len(bs) >= MIN_BRACKETS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    args = ap.parse_args()

    from ib_async import IB, Index, Stock
    # Shared connect: no startup account/order/position fetch.
    # That fetch hung the post-close chain twice; see pipeline/ibkr.py.
    try:
        ib = IBKR.connect(185, timeout=10)
    except ConnectionError as e:
        sys.exit(str(e))

    doc = {"generated_at": market_now().isoformat(timespec="seconds"),
           "years": args.years,
           "cuts": {"normal_ib_share": D.NORMAL_IB_SHARE,
                    "variation_ib_share": D.VARIATION_IB_SHARE,
                    "trend_close_in_extreme": D.TREND_CLOSE_IN_EXTREME,
                    "dd_trough_share": D.DD_TROUGH_SHARE},
           "instruments": {}}
    try:
        for name, tick in INSTRUMENTS.items():
            c = Index("SPX", "CBOE") if name == "SPX" else Stock(name, "SMART", "USD")
            ib.qualifyContracts(c)
            raw = ib.reqHistoricalData(c, endDateTime="",
                                       durationStr=f"{args.years} Y",
                                       barSizeSetting="30 mins",
                                       whatToShow="TRADES", useRTH=True,
                                       formatDate=1, timeout=300)
            S = _sessions(raw)
            days = sorted(S)

            # The prior session's value area is what makes "opened inside value"
            # answerable, so it is carried forward rather than left absent.
            prior_va, rows, pvs = None, [], {}
            day_c, open_c = collections.Counter(), collections.Counter()
            for d in days:
                pvs[d] = prior_va
                cl = D.classify(S[d], prior_value=prior_va, tick=tick)
                day_c[cl["day"]["type"]] += 1
                open_c[cl["open"]["type"]] += 1
                rows.append({"date": d, "day": cl["day"]["type"],
                             "open": cl["open"]["type"],
                             "ib_share": cl["day"]["measurements"].get("ib_share")})
                va = MP.value_area(MP.tpo_counts(MP.build_profile(S[d], tick)))
                prior_va = {"low": va["low"], "high": va["high"]} if va else None

            n = len(days)
            doc["instruments"][name] = {
                "tick": tick, "n_sessions": n,
                "first": days[0], "last": days[-1],
                "day_types": dict(day_c), "open_types": dict(open_c),
                "sweep": D.sweep_day_types(S),
                "sweep_open_window": D.sweep_open_window(S, pvs),
                "sessions": rows,
            }

            print(f"\n{'=' * 66}\n{name}  {n} sessions  {days[0]} .. {days[-1]}")
            print("  DAY TYPE                      n     share    per year   "
                  "years to settle a 65% edge")
            for t in D.DAY_TYPES:
                k = day_c.get(t, 0)
                if not k:
                    print(f"  {t:<26} {k:>4}     0.0%          —   —")
                    continue
                per_year = k / n * 252
                yrs = PW.years_to_decide(0.65, per_year)
                mark = "  settleable" if yrs["decidable_within_3y"] else ""
                print(f"  {t:<26} {k:>4}   {k / n:>6.1%}   {per_year:>8.0f}   "
                      f"{yrs['years']:>6.1f}{mark}")
            print("  OPEN TYPE")
            for t in D.OPEN_TYPES:
                k = open_c.get(t, 0)
                print(f"  {t:<26} {k:>4}   {k / n:>6.1%}")
    finally:
        ib.disconnect()

    print("\n" + "=" * 66)
    print("SWEEP — what the two width cuts do to the SPX distribution")
    sw = doc["instruments"]["SPX"]["sweep"]
    hdr = "  normal  var  " + "".join(f"{t[:10]:>12}" for t in D.DAY_TYPES)
    print(hdr)
    for r in sw:
        cells = "".join(f"{r[t]:>12}" for t in D.DAY_TYPES)
        star = "  <- shipped" if (r["normal_cut"] == D.NORMAL_IB_SHARE
                                  and r["variation_cut"] == D.VARIATION_IB_SHARE) else ""
        print(f"  {r['normal_cut']:>6.2f} {r['variation_cut']:>4.2f}{cells}{star}")

    print("\n" + "=" * 66)
    print("SWEEP — what counts as 'the open' (13 = the whole session, the bug)")
    print("  window" + "".join(f"{t[:12]:>14}" for t in D.OPEN_TYPES))
    for r in doc["instruments"]["SPX"]["sweep_open_window"]:
        star = "  <- shipped" if r["window"] == D.OPEN_WINDOW else ""
        print(f"  {r['window']:>6}" + "".join(f"{r[t]:>14}" for t in D.OPEN_TYPES) + star)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
