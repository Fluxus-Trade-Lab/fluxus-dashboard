"""Did tonight's run produce True Market Leaders under the new definition?

TML moved to Richard Moglen's 2020 definition on 2026-09-18 (Moglen / Weinstein,
see METRIC_SOURCES.md). This reads the published outputs and answers, in one
command, three questions the first nights raise:

  * live   -- has a nightly run under the NEW definition landed? (the bar-derived
              field `weinstein_stage` only exists once it has)
  * count  -- how many TMLs today, and which tickers
  * agree  -- does the watchlist panel match leaders_log (one rule, two writers)

profit_margin / roe coverage is printed because they fill in over ~8 nights of
fundamentals rotation, and a missing fundamental fails the "3 of 5" test -- so a
low share is exactly why the first nights under-report (est. ~2 vs ~6 at full
coverage, 2026-09-17 data).

    python -m pipeline.tools.audit_tml

Exit 0 = live and consistent; 1 = panel disagrees with leaders_log; 2 = the new
definition has not run yet (nothing to check).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

OUTPUT = Path("data/output")
HISTORY = Path("data/history")

COVERAGE_FIELDS = ("weinstein_stage", "ud_vol_ratio_50", "sb_avg_dollar_vol_20",
                   "profit_margin", "roe", "industry_rank")


def _present(v: Any) -> bool:
    return v is not None and v != ""


def _coverage(rows: List[dict], field: str) -> Tuple[int, int]:
    return sum(1 for r in rows if _present(r.get(field))), len(rows)


def _tml_panel(wl: dict) -> dict:
    for z in wl.get("zones", []):
        for p in z.get("panels", []):
            if p.get("key") == "true_market_leaders":
                return p
    return {}


def _log_tml(history: Path, date: str) -> List[str]:
    path = history / "leaders_log.csv"
    if not path.exists() or not date:
        return []
    with path.open(newline="") as fh:
        return sorted(r["ticker"] for r in csv.DictReader(fh)
                      if r.get("date") == date and str(r.get("tml")).lower() == "true")


def audit(output: Path = OUTPUT, history: Path = HISTORY) -> Dict[str, Any]:
    universe = json.loads((output / "universe.json").read_text())
    rows = universe.get("rows", [])
    wl = json.loads((output / "watchlist.json").read_text())

    coverage = {f: _coverage(rows, f) for f in COVERAGE_FIELDS}
    live = coverage["weinstein_stage"][0] > 0

    panel = _tml_panel(wl)
    count = int(panel.get("count") or 0)
    panel_tickers = sorted(t.get("ticker") for t in (panel.get("tickers") or []) if t.get("ticker"))
    truncated = int(panel.get("truncated") or 0)

    date = str(wl.get("date") or "")[:10]
    log_tickers = _log_tml(history, date)

    # One rule, two writers (watchlist panel and leaders_log.tml since d154052b):
    # the counts must match; the ticker sets must match when the panel is not
    # truncated (it shows at most the top 25).
    count_match = count == len(log_tickers)
    ticker_match = truncated > 0 or set(panel_tickers) == set(log_tickers)
    consistent = count_match and ticker_match

    exit_code = 2 if not live else (0 if consistent else 1)
    return {"date": date, "live": live, "count": count, "tickers": panel_tickers,
            "truncated": truncated, "log_count": len(log_tickers),
            "log_tickers": log_tickers, "consistent": consistent,
            "coverage": coverage, "exit": exit_code}


def _fmt(r: Dict[str, Any]) -> str:
    L = [f"TML check -- {r['date'] or '(no date)'}"]
    if not r["live"]:
        L.append("  ⏳ NOT LIVE: universe.json has no weinstein_stage -- the new "
                 "definition has not run yet. Re-run after tonight's 正班 lands.")
        L.append("  coverage: " + ", ".join(f"{f} {n}/{d}" for f, (n, d) in r["coverage"].items()))
        return "\n".join(L)
    L.append(f"  TML today: {r['count']}"
             + (f" — {', '.join(r['tickers'])}" if r["tickers"] else "")
             + (f" (+{r['truncated']} beyond the panel's top 25)" if r["truncated"] else ""))
    L.append(f"  panel vs leaders_log: {'✅ match' if r['consistent'] else '❌ MISMATCH'}"
             f" (panel {r['count']}, log {r['log_count']})")
    if not r["consistent"]:
        only_panel = sorted(set(r["tickers"]) - set(r["log_tickers"]))
        only_log = sorted(set(r["log_tickers"]) - set(r["tickers"]))
        if only_panel:
            L.append(f"    only on panel: {', '.join(only_panel)}")
        if only_log:
            L.append(f"    only in log:   {', '.join(only_log)}")
    L.append("  field coverage (a low profit_margin/roe share is why counts start small):")
    for f, (n, d) in r["coverage"].items():
        pct = f"{n / d * 100:.0f}%" if d else "—"
        L.append(f"    {f:<22} {n}/{d} ({pct})")
    return "\n".join(L)


def main(argv: List[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0]) if argv else OUTPUT
    hist = Path(argv[1]) if len(argv) > 1 else HISTORY
    if not (out / "watchlist.json").exists():
        print(f"no outputs at {out} -- run from the repo root", file=sys.stderr)
        return 2
    r = audit(out, hist)
    print(_fmt(r))
    return r["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
