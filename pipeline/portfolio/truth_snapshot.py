#!/usr/bin/env python3
"""Emit the canonical, PUBLIC-SAFE performance truth snapshot.

Reads a deep-review JSON (default the H1 review) and writes aggregate-only numbers
to `performance_truth.json` at the repo root — the machine-readable companion to
PERFORMANCE_TRUTH.md that other projects (Squarespace Track Record, etc.) verify
against. Per-ticker / per-trade detail is intentionally dropped so the file is
safe to commit to the public repo.

Usage:
    python pipeline/portfolio/performance_review.py --period h1 --label h1_2026
    python pipeline/portfolio/truth_snapshot.py            # -> performance_truth.json
"""
from __future__ import annotations

import datetime as dt
import json
import os


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    src = os.path.join(repo, "data", "portfolio", "reviews", "h1_2026.json")
    if not os.path.exists(src):
        raise SystemExit(f"Review JSON not found: {src}. Run performance_review.py first.")

    d = json.load(open(src))
    o = d["overall"]
    m = d.get("mtm") or {}
    dd = m.get("drawdown", {})
    r = m.get("risk", {})

    truth = {
        "_note": "Canonical source of truth. Aggregate-only (public-safe). See PERFORMANCE_TRUTH.md.",
        "generated": dt.date.today().isoformat(),
        "source_csv": d.get("source_csv"),
        "periods": {
            "H1_2026": {
                "range": "2025-12-31..2026-07-22",
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
                "monthly_pnl": {k: round(v["pnl"]) for k, v in d.get("monthly", {}).items()},
            }
        },
    }

    out = os.path.join(repo, "performance_truth.json")
    with open(out, "w") as f:
        json.dump(truth, f, indent=2)
    print(f"✓ wrote {out}")


if __name__ == "__main__":
    main()
