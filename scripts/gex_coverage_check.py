#!/usr/bin/env python3
"""Does our gamma profile match an outside one when the universe matches?

A correctness check, not a signal. The question is narrow and answerable: given
the same session, does our profile engine reproduce an independently computed
gamma profile once it is fed a comparable option universe? If yes, the engine is
sound and our production narrowness is a deliberate, priced choice. If no, we
have a defect or a different model, and either way we would want to know.

This is the `consistency.py` discipline applied to a whole curve rather than a
scalar: compute a published number by a second route and report the drift.

## What we measured on 2026-08-14 that prompted this

Our production pull holds 656 contracts -- 7 expiries, 49 strikes on a 25-point
step, +/-8% of spot. The chain lists 42 expiries and 720 strikes. **We see 1.1%
of what is listed.**

Against the reference profile for that session:

    ours     peak 7,900   trough 7,500   zero crossing 7,735
    theirs   peak ~7,720  trough ~8,300  zero crossing ~7,950
    correlation -0.016, and no dealer sign convention fixes it

The reference has THREE regions (negative low, positive middle, deeply negative
high). Our open interest has one hump, and a single global sign on one hump can
only ever produce two regions. Three needs either a wider OI distribution or a
dealer-position model inferred from trades. This script tests the first.

## The reference points are eyeballed and say so

`REFERENCE` below was read off a chart by eye to roughly +/-0.5bn. That is
precise enough to settle a question about SHAPE -- peak location, trough
location, where it crosses zero -- and nowhere near precise enough to grade
magnitude. Treat the correlation as the verdict and the levels as colour.

Usage:
    # measure the cost before committing to a full pull
    .venv/bin/python scripts/gex_coverage_check.py --sample 300

    # the real run, Monday, market open
    .venv/bin/python scripts/gex_coverage_check.py --width 0.103 --max-dte 400
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import ibkr as IBKR
from pipeline.gex.blackscholes import bs_gamma
from pipeline.marketcal import market_now

OUT = Path("data/gex/coverage_check.json")
MIN_T_YEARS = 0.5 / 365.0
CONTRACT_MULTIPLIER = 100
CALL_SIGN, PUT_SIGN = 1.0, -1.0

# Read off the 2026-08-14 reference chart by eye, +/-0.5bn. Shape is the claim;
# magnitude is not.
REFERENCE = {
    7000: -1.5, 7100: -1.4, 7200: -1.3, 7300: -1.2, 7400: -1.4, 7500: -1.3,
    7600: 0.5, 7700: 4.5, 7800: 3.0, 7900: 2.7, 8000: -1.0, 8100: -6.0,
    8200: -9.5, 8300: -11.0, 8400: -10.0, 8500: -7.0, 8600: -2.5,
}
REFERENCE_NOTE = ("digitised by eye from a chart for the 2026-08-14 session, "
                  "+/-0.5bn; good enough for shape, not for magnitude")


def corr(a: list[float], b: list[float]) -> float:
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else float("nan")


def profile(opts, grid) -> list[float]:
    out = []
    for S in grid:
        s2 = CONTRACT_MULTIPLIER * S * S * 0.01
        out.append(sum(sg * bs_gamma(S, k, t, iv) * oi * s2
                       for k, t, iv, oi, sg, _ in opts) / 1e9)
    return out


def shape(grid, ys) -> dict:
    zs = [grid[i - 1] + ys[i - 1] * (grid[i] - grid[i - 1]) / (ys[i - 1] - ys[i])
          for i in range(1, len(ys)) if ys[i - 1] * ys[i] < 0]
    return {"peak": grid[max(range(len(ys)), key=lambda i: ys[i])],
            "trough": grid[min(range(len(ys)), key=lambda i: ys[i])],
            "zero_crossings": [round(z) for z in zs],
            "max": round(max(ys), 2), "min": round(min(ys), 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=float, default=0.103,
                    help="Strike half-width as a fraction of spot. 0.103 is the "
                         "reference chart's own axis.")
    ap.add_argument("--step", type=float, default=25.0)
    ap.add_argument("--max-dte", type=int, default=400,
                    help="Include expiries out to this many days.")
    ap.add_argument("--sample", type=int, default=0,
                    help="Price the pull on this many contracts and stop. Run "
                         "this FIRST: the full universe has never been timed on "
                         "this path and a guess is not a measurement.")
    args = ap.parse_args()

    now = market_now()
    ib = IBKR.connect(245, timeout=15)
    try:
        from ib_async import Index, Option
        spx = Index("SPX", "CBOE")
        ib.qualifyContracts(spx)
        [t] = [ib.reqMktData(spx, "", False, False)]
        ib.sleep(3)
        spot = t.last if t.last == t.last else t.close
        ib.cancelMktData(spx)
        if not spot or spot != spot:
            sys.exit("no SPX spot — is the market open?")

        ch = max(ib.reqSecDefOptParams("SPX", "", spx.secType, spx.conId),
                 key=lambda c: len(c.strikes))
        strikes = [k for k in sorted(ch.strikes)
                   if abs(k - spot) / spot <= args.width
                   and abs(k % args.step) < 1e-6]
        expiries = sorted(e for e in ch.expirations
                          if 0 <= (dt.date(int(e[:4]), int(e[4:6]), int(e[6:]))
                                   - now.date()).days <= args.max_dte)
        todo = [(e, k, r) for e in expiries for k in strikes for r in ("C", "P")]
        print(f"SPX {spot:,.2f}  {len(expiries)} expiries x {len(strikes)} "
              f"strikes x 2 = {len(todo):,} contracts")
        if args.sample:
            todo = todo[:args.sample]
            print(f"  SAMPLE: pricing {len(todo)} of them")

        opts, t0, got = [], time.time(), 0
        for i, (e, k, r) in enumerate(todo, 1):
            o = Option("SPX", e, k, r, "SMART", tradingClass=ch.tradingClass)
            try:
                ib.qualifyContracts(o)
            except Exception:
                continue
            if not o.conId:
                continue
            tk = ib.reqMktData(o, "101", False, False)
            ib.sleep(0.35)
            oi = tk.callOpenInterest if r == "C" else tk.putOpenInterest
            iv = tk.modelGreeks.impliedVol if tk.modelGreeks else None
            ib.cancelMktData(o)
            if oi and oi == oi and iv and iv > 0:
                d = dt.datetime.strptime(e, "%Y%m%d").replace(
                    hour=16, tzinfo=now.tzinfo)
                T = max((d - now).total_seconds() / (365 * 24 * 3600), MIN_T_YEARS)
                opts.append((k, T, iv, float(oi),
                             CALL_SIGN if r == "C" else PUT_SIGN,
                             (d.date() - now.date()).days))
                got += 1
            if i % 100 == 0:
                el = time.time() - t0
                print(f"  {i:,}/{len(todo):,}  {got:,} with OI+IV  "
                      f"{el:.0f}s  ({el / i:.2f}s each, "
                      f"{el / i * len(todo) / 60:.0f} min projected)", flush=True)
    finally:
        ib.disconnect()

    elapsed = time.time() - t0
    print(f"\n{got:,} usable contracts in {elapsed:.0f}s "
          f"({elapsed / max(1, len(todo)):.2f}s each)")
    if args.sample:
        print("SAMPLE ONLY — no profile computed. Re-run without --sample "
              "once the projected time above is acceptable.")
        return
    if not opts:
        sys.exit("no contract returned both OI and IV — is the market open?")

    grid = sorted(REFERENCE)
    ours = profile(opts, grid)
    ref = [REFERENCE[g] for g in grid]
    c = corr(ours, ref)

    doc = {"generated_at": now.isoformat(timespec="seconds"), "spot": spot,
           "width": args.width, "max_dte": args.max_dte,
           "contracts_priced": len(todo), "contracts_usable": got,
           "seconds": round(elapsed), "grid": grid, "ours": ours,
           "reference": ref, "reference_note": REFERENCE_NOTE,
           "correlation": round(c, 4),
           "ours_shape": shape(grid, ours), "reference_shape": shape(grid, ref)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2))

    print(f"\n{'SPX':>7}{'ours $bn':>11}{'reference':>11}")
    for g, a, b in zip(grid, ours, ref):
        print(f"{g:>7}{a:>11.2f}{b:>11.1f}")
    print(f"\ncorrelation {c:+.3f}")
    print(f"  ours       {doc['ours_shape']}")
    print(f"  reference  {doc['reference_shape']}")
    print(f"\n  baseline at 1.1% coverage was -0.016. "
          f"{'COVERAGE explains it' if c > 0.5 else 'coverage does NOT explain it'}"
          f" — {'the engine reproduces the reference once fed a comparable universe'
               if c > 0.5 else
               'the difference is the model, not the universe: a dealer-position '
               'inference we do not have, not a wider chain'}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
