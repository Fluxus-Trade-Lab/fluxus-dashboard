#!/usr/bin/env python3
"""Score both parties' views against what the session actually did.

This is the loop that makes the centaur a centaur. Without it `log.py` is a
diary and `blend.py` weights everyone at "unproven" forever — the layer looks
built and learns nothing.

Forward-only, like every other scorer here: a view is graded against the session
it was filed for, using that session's completed bar. A session still trading
has no outcome and is skipped rather than graded on a partial range.

Usage:
    .venv/bin/python scripts/score_views.py
    .venv/bin/python scripts/score_views.py --md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.centaur import blend as B
from pipeline.centaur import log as L
from pipeline.centaur import skill as S
from pipeline.marketcal import market_now, market_today

OUT = Path("data/centaur")
RTH_CLOSE = dt.time(16, 0)


def fetch_bars(symbol: str = "SPX", days: int = 90) -> dict[str, dict]:
    from ib_async import IB, Index, Stock
    ib = IB()
    for port in (7496, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=197, timeout=10)
            break
        except Exception:
            continue
    if not ib.isConnected():
        sys.exit("no IBKR endpoint — is TWS logged in?")
    try:
        c = Index(symbol, "CBOE") if symbol in ("SPX", "VIX") else Stock(symbol, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, endDateTime="", durationStr=f"{days} D",
                                    barSizeSetting="1 day", whatToShow="TRADES",
                                    useRTH=True, formatDate=1)
        out = {str(b.date): {"open": b.open, "high": b.high, "low": b.low,
                             "close": b.close} for b in bars}
    finally:
        ib.disconnect()
    # Same guard as the levels scorer: a session still trading has no outcome,
    # and IBKR hands back a partial bar without saying so.
    now = market_now()
    if now.time() < RTH_CLOSE:
        out.pop(str(market_today(now)), None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SPX")
    ap.add_argument("--horizon", default="intraday", choices=("intraday", "swing"))
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()

    rows = L.read()
    if not rows:
        sys.exit("no views on record — nothing to score. "
                 "Log one: scripts/log_view.py down 3 \"reason\"")

    bars = fetch_bars(args.symbol)
    outcomes = {d: S.outcome(b["open"], b["high"], b["low"], b["close"])
                for d, b in bars.items()}

    skills = {src: S.skill(rows, src, outcomes, args.horizon)
              for src in ("machine", "human")}
    weights = {src: B.weight_from_skill(s) for src, s in skills.items()}

    paired = L.paired(rows, args.horizon)
    disagree = L.disagreements(rows, args.horizon)
    # Where the two disagreed AND the session has settled: the only rows that
    # can ever answer "whose judgement was worth more".
    settled = [p for p in disagree if p["session"] in outcomes]
    scored_disagreements = [
        {"session": p["session"], "actual": outcomes[p["session"]],
         "machine": p["machine"]["direction"], "human": p["human"]["direction"],
         "winner": ("machine" if p["machine"]["direction"] == outcomes[p["session"]]
                    else "human" if p["human"]["direction"] == outcomes[p["session"]]
                    else "neither")}
        for p in settled]

    ledger = S.consultations(paired, outcomes)
    pressure = S.under_pressure([r for r in rows if r.get("horizon") == args.horizon])

    report = {
        "generated_at": market_now().isoformat(timespec="seconds"),
        "symbol": args.symbol, "horizon": args.horizon,
        "sessions_with_outcome": len(outcomes),
        "views_on_record": len(rows),
        "paired": len(paired), "disagreements": len(disagree),
        "skills": skills, "weights": weights,
        "scored_disagreements": scored_disagreements,
        "consultations": ledger,
        "pressure": pressure,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"skill_{args.symbol}.json").write_text(json.dumps(report, indent=2))

    if args.md:
        print(f"# Centaur skill — {args.symbol} ({args.horizon})\n")
        print("| party | scored | abstained | hits | hit rate | edge vs chance | weight |")
        print("|---|---|---|---|---|---|---|")
        for src, s in skills.items():
            hr = "—" if s["hit_rate"] is None else f"{s['hit_rate']:.1%}"
            ed = S.edge_over_chance(s)
            print(f"| {src} | {s['n_scored']} | {s['n_abstained']} | {s['hits']} | {hr} | "
                  f"{'—' if ed is None else f'{ed:+.1%}'} | {weights[src]['weight']:.2f} "
                  f"({weights[src]['basis']}) |")
        return

    print(f"views on record {len(rows)}   paired {len(paired)}   "
          f"disagreements {len(disagree)} ({len(settled)} settled)")
    print(f"{'party':<9}{'scored':>8}{'abstain':>9}{'hits':>6}{'hit rate':>10}"
          f"{'vs chance':>11}{'weight':>9}  basis")
    for src, s in skills.items():
        hr = "—" if s["hit_rate"] is None else f"{s['hit_rate']:.1%}"
        ed = S.edge_over_chance(s)
        w = weights[src]
        print(f"{src:<9}{s['n_scored']:>8}{s['n_abstained']:>9}{s['hits']:>6}{hr:>10}"
              f"{('—' if ed is None else f'{ed:+.1%}'):>11}{w['weight']:>9.2f}  {w['basis']}")
        if s["note"]:
            print(f"{'':9}{s['note']}")

    if scored_disagreements:
        print("\nsettled disagreements — the rows the merge learns from:")
        for d in scored_disagreements[-10:]:
            print(f"  {d['session']}  machine {d['machine']:<12} human {d['human']:<12} "
                  f"actual {d['actual']:<7} -> {d['winner']}")
    else:
        print("\nno settled disagreements yet — until the two differ on a finished "
              "session, nothing distinguishes them")
    ab = ledger["automation_bias_rate"]
    print(f"\nconsultation ledger — did the merge help when it overrode someone?")
    print(f"  scored pairs {ledger['n_scored_pairs']}   "
          f"positive {ledger['n_positive']} (saved a wrong human call)   "
          f"negative {ledger['n_negative']} (broke a right one)")
    print(f"  automation-bias rate: "
          f"{'—' if ab is None else f'{ab:.1%}'}"
          f"   net {ledger['net_consultations']:+d}")
    print(f"  reference: {ledger['reference']}")
    print(f"\nviews filed calm {pressure['calm']} / while trading {pressure['live']}")
    print(f"\nwrote {OUT / f'skill_{args.symbol}.json'}")


if __name__ == "__main__":
    main()
