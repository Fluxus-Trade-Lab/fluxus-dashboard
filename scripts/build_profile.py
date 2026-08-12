#!/usr/bin/env python3
"""Build the Market Profile for a session and write it next to the GEX levels.

Two instruments on purpose:

  * **TPO on SPX.** Time at price needs no volume, and the cash index is the
    thing our gamma levels are denominated in. Using it keeps the auction levels
    and the options levels on one scale with no conversion.
  * **Volume-at-price on ES.** The cash index prints no volume at all, so a VPOC
    from it would be fiction. ES has real volume, and its levels are reported in
    ES terms — never silently converted. An ES-to-SPX basis measured at a
    different moment than the profile is exactly the non-simultaneous comparison
    that has bitten this project twice.

Usage:
    .venv/bin/python scripts/build_profile.py                 # today, ET
    .venv/bin/python scripts/build_profile.py --date 20260804
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.marketcal import MARKET_TZ, market_now, market_today
from pipeline.profile import tpo as MP

OUT = Path("data/profile")
RTH_CLOSE = dt.time(16, 0)


def _close_utc(day: str) -> str:
    """That ET session's 16:00 close, as IBKR's UTC dash form.

    The named-timezone form ("20260805 16:00:00 US/Eastern") is rejected with
    error 10314 — the same failure the ES chunked pull hit. UTC with a dash is
    the form that works, and doing the conversion here means the DST offset is
    never hand-typed.
    """
    local = dt.datetime.strptime(day, "%Y%m%d").replace(
        hour=16, tzinfo=MARKET_TZ)
    return local.astimezone(dt.timezone.utc).strftime("%Y%m%d-%H:%M:%S")


def _bars(ib, contract, size: str, day: str, rth: bool = True):
    """One session of bars ending at that day's close, in ET."""
    end = _close_utc(day)
    b = ib.reqHistoricalData(contract, endDateTime=end, durationStr="1 D",
                             barSizeSetting=size, whatToShow="TRADES",
                             useRTH=rth, formatDate=1, timeout=120)
    return [{"time": str(x.date), "open": x.open, "high": x.high, "low": x.low,
             "close": x.close, "volume": float(x.volume or 0)} for x in b]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYYMMDD (ET). Default: the last complete session.")
    ap.add_argument("--tick", type=float, default=2.5,
                    help="SPX price bucket. 2.5 gives ~30 rows on a typical "
                         "75pt range; 5.0 halves that and erases single prints.")
    ap.add_argument("--es-tick", type=float, default=1.0)
    ap.add_argument("--method", default="pair", choices=MP.VALUE_AREA_METHODS)
    args = ap.parse_args()

    now = market_now()
    if args.date:
        day = args.date
    else:
        d = market_today(now)
        # A session still trading has no profile; use the prior one.
        if now.time() < RTH_CLOSE:
            d -= dt.timedelta(days=1)
        while d.weekday() > 4:
            d -= dt.timedelta(days=1)
        day = d.strftime("%Y%m%d")
    pretty = f"{day[:4]}-{day[4:6]}-{day[6:]}"

    from ib_async import IB, ContFuture, Future, Index
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=171, timeout=10)
            break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")

    try:
        spx = Index("SPX", "CBOE")
        ib.qualifyContracts(spx)
        half = _bars(ib, spx, "30 mins", day)
        if not half:
            sys.exit(f"no SPX 30-min bars for {pretty} — is it a trading day?")

        # A ContFuture cannot carry an endDateTime (error 10339). Qualify it to
        # learn WHICH contract is front month, then ask the dated one. Same fix
        # the chunked ES history pull needed.
        cf = ContFuture("ES", "CME")
        ib.qualifyContracts(cf)
        es = Future(conId=cf.conId, exchange="CME")
        ib.qualifyContracts(es)
        fine = _bars(ib, es, "1 min", day)
    finally:
        ib.disconnect()

    # Which bracket printed the extreme. "Poor high made late, periods 7-8" is
    # a statement about WHEN, and a profile that only stores the price cannot
    # answer it.
    hi_i = max(range(len(half)), key=lambda i: half[i]["high"])
    lo_i = min(range(len(half)), key=lambda i: half[i]["low"])

    prof = MP.build_profile(half, args.tick)
    counts = MP.tpo_counts(prof)
    va = MP.value_area(counts, method=args.method)
    out = {
        "date": pretty,
        "generated_at": now.isoformat(timespec="seconds"),
        "tpo": {
            "instrument": "SPX", "bar": "30 mins", "tick": args.tick,
            "periods": len(half),
            "high": max(counts), "low": min(counts),
            # Open and close were never stored; four of the pattern's conditions
            # are about where the session closed relative to its own structure.
            "open": half[0]["open"], "close": half[-1]["close"],
            "high_period": hi_i + 1, "low_period": lo_i + 1,
            "tpoc": MP.poc(counts),
            "value_area": va,
            # Jones defines value as 1 sigma of the distribution, not as a 70%
            # window grown from the POC. Both are stored because they disagree
            # by up to 6 SPX points on a skewed session, and a pattern phrased
            # as "the close travels from below value to above value" can come
            # out either way on that gap.
            "value_area_sigma": MP.value_area(counts, method="sigma"),
            "value_area_disagreement": MP.value_area_disagreement(counts),
            "moments": MP.moments(counts),
            "single_prints": MP.single_prints(prof),
            "tails": MP.tails(prof),
            "poor_extremes": MP.poor_extremes(prof),
            "initial_balance": MP.initial_balance(half),
            "counts": {str(k): v for k, v in sorted(counts.items())},
        },
        "volume": None,
    }
    if fine:
        vap = MP.volume_at_price(fine, args.es_tick)
        # TPO counts for ES on the same grid, so "volume without time" compares
        # like with like rather than crossing instruments.
        es_half = MP.build_profile(
            [{"low": b["low"], "high": b["high"]} for b in fine], args.es_tick)
        lvn = MP.low_volume_nodes(vap)
        gaps = [g for g in MP.profile_gaps(vap) if g["interior"]]
        es_counts = MP.tpo_counts(es_half)
        out["volume"] = {
            "instrument": "ES", "bar": "1 min", "tick": args.es_tick,
            # TPOC on the SAME instrument as the VPOC. Our headline TPOC is SPX
            # and the VPOC is ES, deliberately never converted -- which makes
            # "VPOC and TPOC coincide" unanswerable across them. Computing both
            # on ES answers it without inventing a basis.
            "tpoc": MP.poc(es_counts),
            "coincide": (abs((MP.poc(es_counts) or 0) - (MP.vpoc(vap) or 0))
                         <= 2 * args.es_tick) if (es_counts and vap) else None,
            "at_price": {str(k): round(v, 1) for k, v in sorted(vap.items())},
            "low_volume_nodes": lvn,
            "interior_dips": gaps,
            "provenance": "approximated — each bar's volume spread evenly across "
                          "the prices it spans; not tape-derived volume-at-price",
            "vpoc": MP.vpoc(vap),
            "volume_without_time": MP.volume_without_time(
                vap, MP.tpo_counts(es_half)),
            "total": sum(vap.values()),
        }

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"profile_{day}.json"
    p.write_text(json.dumps(out, indent=2))

    t = out["tpo"]
    print(f"Market Profile  {pretty}   SPX {t['low']:,.0f} - {t['high']:,.0f}  "
          f"({t['periods']} brackets, {args.tick:g}pt buckets)")
    print(f"  TPOC ................ {t['tpoc']:,.0f}   "
          f"open {t['open']:,.0f} close {t['close']:,.0f}   "
          f"high in period {t['high_period']}, low in period {t['low_period']}")
    print(f"  Value area .......... {va['low']:,.0f} - {va['high']:,.0f}  "
          f"({va['covered']*100:.0f}% of TPOs, method={va['method']})")
    d, mo = out["tpo"]["value_area_disagreement"], out["tpo"]["moments"]
    if d:
        s = d["sigma"]
        print(f"  Jones 1-sigma ....... {s['low']:,.1f} - {s['high']:,.1f}  "
              f"({s['covered']*100:.0f}% held)   "
              f"low {d['low_delta']:+.1f}, high {d['high_delta']:+.1f} vs above")
    if mo and mo["skew"] is not None:
        print(f"  Shape ............... skew {mo['skew']:+.2f}   "
              f"excess kurtosis {mo['excess_kurtosis']:+.2f}"
              + ("   FLAT — the POC is an argmax over near-ties"
                 if mo["excess_kurtosis"] < -1.0 else ""))
    ib_ = t["initial_balance"]
    print(f"  Initial balance ..... {ib_['low']:,.0f} - {ib_['high']:,.0f}")
    for side in ("buying", "selling"):
        tl = t["tails"][side]
        if tl:
            print(f"  {side.capitalize():8} tail ...... {tl['low']:,.0f} - {tl['high']:,.0f}"
                  f"  ({tl['length']} ticks, "
                  f"{'significant' if tl['significant'] else 'NOT significant'})")
    pe = t["poor_extremes"]
    print(f"  Poor high / low ..... {pe['poor_high']} ({pe['high_tpos']} TPOs) / "
          f"{pe['poor_low']} ({pe['low_tpos']} TPOs)")
    sp = t["single_prints"]
    print(f"  Single prints ....... {len(sp)}" +
          (f"   {sp[0]:,.0f} .. {sp[-1]:,.0f}" if sp else ""))
    if out["volume"]:
        v = out["volume"]
        print(f"  ES VPOC ............. {v['vpoc']:,.2f}   (ES units, approximated)"
              + (f"   TPOC {v['tpoc']:,.2f}"
                 f"   {'COINCIDE' if v.get('coincide') else 'apart'}"
                 if v.get("tpoc") else ""))
        vw = v["volume_without_time"]
        print(f"  Volume w/o time ..... {len(vw)} price(s)" +
              (f"   {vw[0]:,.2f} .. {vw[-1]:,.2f}" if vw else ""))
        ln = v["low_volume_nodes"]
        ln, gp = v["low_volume_nodes"], v["interior_dips"]
        if ln:
            print(f"  Low-volume nodes .... {len(ln)}   " +
                  ", ".join(f"{r['price']:,.0f} ({r['share_of_peak']:.0%})" for r in ln[:4]))
        else:
            near = ", ".join(f"{r['price']:,.0f} ({r['share_of_peak']:.0%})" for r in gp[:3])
            print(f"  Low-volume nodes .... 0 below the {MP.LVN_FRAC:.0%} cut" +
                  (f"; deepest interior dips {near}" if near else "; no interior dip at all"))
    print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
