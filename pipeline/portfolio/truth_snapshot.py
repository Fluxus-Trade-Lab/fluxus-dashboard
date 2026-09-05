#!/usr/bin/env python3
"""Emit the canonical, PUBLIC-SAFE performance truth snapshot.

Reads a deep-review JSON (default the H1 review) and writes aggregate-only numbers
to `performance_truth.json` at the repo root — the machine-readable companion to
PERFORMANCE_TRUTH.md that other projects (Squarespace Track Record, etc.) verify
against. Per-ticker / per-trade detail is intentionally dropped so the file is
safe to commit to the public repo.

Usage:
    python pipeline/portfolio/performance_review.py --period h1 --label h1_2026
    python pipeline/portfolio/truth_snapshot.py                        # Period 1 (H1_2026)
    python pipeline/portfolio/performance_review.py --period annual --label ytd_2026
    python pipeline/portfolio/truth_snapshot.py --review ytd_2026 \
        --key YTD_2026 --range 2025-12-31..2026-08-30                  # merge Period 2

Multi-period: the snapshot MERGES into an existing performance_truth.json, so
each period is regenerated independently and none is clobbered.
"""
from __future__ import annotations

import datetime as dt

from pipeline.marketcal import market_today
import argparse
import json
import os


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", default="h1_2026", help="review label (reviews/<label>.json)")
    ap.add_argument("--key", default="H1_2026", help="period key in performance_truth.json")
    ap.add_argument("--range", dest="range_", default="2025-12-31..2026-07-22")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    src = os.path.join(repo, "data", "portfolio", "reviews", f"{args.review}.json")
    if not os.path.exists(src):
        raise SystemExit(f"Review JSON not found: {src}. Run performance_review.py first.")

    d = json.load(open(src))
    o = d["overall"]
    m = d.get("mtm") or {}
    dd = m.get("drawdown", {})
    r = m.get("risk", {})
    ce = d.get("capital_efficiency") or {}

    period = {
                "range": args.range_,
                "starting_capital": o["capital"],
                "ending_equity": round(o["ending_equity"]),
                "return_pct": round(o["return_pct"], 4),
                "net_pnl": round(o["total_pnl"]),
                "trades": o["n"],
                "win_rate_pct": round(o["win_rate"], 2),
                "payoff": round(o["payoff"], 3),
                "profit_factor": round(o["profit_factor"], 3),
                "expectancy": round(o["expectancy"]),
                "avg_R": round(o["avg_R"], 3),
                "sum_R": round(o["sum_R"], 1),
                "avg_hold_days": round(o["avg_hold_days"], 1),
                "drawdown_mtm_pct_of_peak": round(dd.get("pct"), 2) if dd.get("pct") is not None else None,
                "drawdown_mtm_amount": round(dd["amount"]) if dd.get("amount") is not None else None,
                "drawdown_mtm_window": [dd.get("peak_date"), dd.get("trough_date")],
                "drawdown_realized_pct_of_peak": round(o["max_drawdown"].get("pct_of_peak"), 2)
                    if o["max_drawdown"].get("pct_of_peak") is not None else None,
                "peak_equity": round(r["peak_equity"]) if r.get("peak_equity") else None,
                "sharpe": round(r["sharpe"], 2) if r.get("sharpe") else None,
                "sortino": round(r["sortino"], 2) if r.get("sortino") else None,
                "vol_ann_pct": round(r["vol_ann"] * 100, 1) if r.get("vol_ann") is not None else None,
                "return_on_deployed_pct": round(ce["return_on_deployed"], 1) if ce.get("return_on_deployed") is not None else None,
                "avg_leverage_x": round(ce["avg_leverage_pct"] / 100, 2) if ce.get("avg_leverage_pct") is not None else None,
                "peak_leverage_x": round(ce["peak_leverage_pct"] / 100, 2) if ce.get("peak_leverage_pct") is not None else None,
                "avg_deployed_pct_of_start": round(ce["avg_deployed_pct_of_start"]) if ce.get("avg_deployed_pct_of_start") is not None else None,
                "monthly_pnl": {k: round(v["pnl"]) for k, v in d.get("monthly", {}).items()},
                "source_csv": d.get("source_csv"),
    }

    out = os.path.join(repo, "performance_truth.json")
    truth = {"_note": "Canonical source of truth. Aggregate-only (public-safe). See PERFORMANCE_TRUTH.md.",
             "periods": {}}
    if os.path.exists(out):
        try:
            truth = json.load(open(out))
        except ValueError:
            pass
    truth["generated"] = market_today().isoformat()
    truth.setdefault("periods", {})[args.key] = period
    with open(out, "w") as f:
        json.dump(truth, f, indent=2)
    print(f"✓ wrote {out} (period {args.key}; {len(truth['periods'])} period(s) total)")


if __name__ == "__main__":
    main()
