"""Forward test for RS unify option B: log the old and the new reading of every
switched RS leg, every session, side by side.

Andy 2026-10-04: 「选B，而且务必要做forward testing，至少5天。」

One row per (date, panel, ticker) that is in EITHER list; `old` / `new` say
which. close/change_pct are logged so forward returns can be measured from
later sessions plus a price fetch for names that left both lists.
`industry_top20` logs industries (ticker column = industry name).

Each list is produced by the same code that makes the published one:
  liquid_leader / industry_top20 -- run_all.compute_universe_scores, on the
      UNROUNDED scores, handed over in EXACT. Re-deriving them from
      universe.json misplaces names at the 80 edge: the exported rs columns are
      rounded (2026-10-02: 4 of 181 -- GME/JCI/PK/SONY at rs_3m 79.5-79.99,
      exported as 80).
  vcs / 4pct_bullish -- watchlist.panel_pool + watchlist.PANELS["vcs" |
      "bullish_4pct"] (the latter is the pipeline twin of the frontend preset,
      pinned to it by test_watchlist), with rs_leg.UNIFIED flipped for the old
      reading. Both run on the exported rows, as the published panels do.

Evaluate with `python3 -m pipeline.tools.rs_switch_shadow --report` once
>= rs_leg.FORWARD_MIN_SESSIONS sessions are logged.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from pipeline.constants import rs_leg

SHADOW_LOG = Path("data/history/rs_switch_shadow.csv")
FIELDS = ["date", "panel", "ticker", "old", "new", "close", "change_pct",
          "rs_1m", "rs_3m", "rs_rating"]

# Filled by run_all.compute_universe_scores:
#   "liquid_leader": {ticker: (old_flag, new_flag)}
#   "industry_top20": (old_industries, new_industries)
EXACT: Dict[str, Any] = {}


def _f(r: Mapping[str, Any], k: str) -> Optional[float]:
    v = r.get(k)
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _ge(r, k, x):
    v = _f(r, k)
    return v is not None and v >= x


def _between(r, k, lo, hi):
    v = _f(r, k)
    return v is not None and lo <= v <= hi


def _panel(rows, key: str, unified: bool) -> set:
    """The watchlist's own panel (same pool, same predicate) under either reading."""
    from pipeline.screeners import watchlist as W
    zone = next(z["key"] for z in W.ZONES if key in z["panels"])
    saved = rs_leg.UNIFIED
    rs_leg.UNIFIED = unified
    try:
        return {r["ticker"] for r in W.panel_pool(rows, zone) if W.PANELS[key].test(r)}
    finally:
        rs_leg.UNIFIED = saved


def shadow_rows(rows: List[Mapping[str, Any]], *, date: str,
                exact: Optional[Mapping[str, Any]] = None) -> List[Dict[str, Any]]:
    exact = EXACT if exact is None else exact
    by = {r["ticker"]: r for r in rows if r.get("ticker")}
    sets: Dict[str, tuple] = {}
    if "liquid_leader" in exact:
        ll = exact["liquid_leader"]
        sets["liquid_leader"] = ({t for t, (o, _) in ll.items() if o},
                                 {t for t, (_, n) in ll.items() if n})
    sets["vcs"] = (_panel(rows, "vcs", False), _panel(rows, "vcs", True))
    sets["4pct_bullish"] = (_panel(rows, "bullish_4pct", False), _panel(rows, "bullish_4pct", True))
    out: List[Dict[str, Any]] = []
    for panel, (old, new) in sets.items():
        for t in sorted(old | new):
            r = by.get(t, {})
            out.append({"date": date, "panel": panel, "ticker": t,
                        "old": int(t in old), "new": int(t in new), "close": _f(r, "close"),
                        "change_pct": _f(r, "change_pct"), "rs_1m": _f(r, "rs_1m"),
                        "rs_3m": _f(r, "rs_3m"), "rs_rating": _f(r, "rs_rating")})
    if "industry_top20" in exact:
        old_i, new_i = exact["industry_top20"]
        for ind in sorted(set(old_i) | set(new_i)):
            out.append({"date": date, "panel": "industry_top20", "ticker": ind,
                        "old": int(ind in old_i), "new": int(ind in new_i)})
    return out


def archive(rows: List[Mapping[str, Any]], *, date: str, path: Path = SHADOW_LOG,
            exact: Optional[Mapping[str, Any]] = None) -> int:
    """Rewrite `date`'s rows (idempotent re-runs), keep every other date."""
    old: List[Dict[str, Any]] = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != date]
    new = shadow_rows(rows, date=date, exact=exact)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in [*old, *new]:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in FIELDS})
    return len(new)


def report(path: Path = SHADOW_LOG) -> Dict[str, Any]:
    """Per panel: mean list sizes and mean daily keep rate (share of the old
    list still in the new one); days under 50% = the backtest's 'huge change'."""
    with path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    out: Dict[str, Any] = {"sessions": sorted({r["date"] for r in rows})}
    for panel in sorted({r["panel"] for r in rows}):
        days: Dict[str, List[int]] = {}
        for r in rows:
            if r["panel"] == panel:
                d = days.setdefault(r["date"], [0, 0, 0])
                d[0] += r["old"] == "1"
                d[1] += r["new"] == "1"
                d[2] += r["old"] == "1" and r["new"] == "1"
        keep = [b / o for o, n, b in days.values() if o]
        out[panel] = {"old_mean": round(sum(v[0] for v in days.values()) / len(days), 1),
                      "new_mean": round(sum(v[1] for v in days.values()) / len(days), 1),
                      "keep_mean": round(sum(keep) / len(keep), 3) if keep else None,
                      "days_keep_below_50pct": sum(k < 0.5 for k in keep)}
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(report(), indent=1, ensure_ascii=False))
