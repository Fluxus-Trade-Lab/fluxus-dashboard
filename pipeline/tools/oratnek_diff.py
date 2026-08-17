"""Rebuild our watchlist AS OF a past session and diff it against oratnek's page.

Why: one day's screenshot (29 names) is not enough to reverse-engineer the
filters he does not publish; several days are. Each day he posts is a new set
of constraints. This tool makes a day cheap: point it at the session his page
was built on, it re-runs OUR pipeline on bars truncated to that session, and
prints, panel by panel, his list vs ours with every field of the names that
differ, then archives both under data/research/oratnek_diff/.

    python -m pipeline.tools.oratnek_diff --asof 2026-08-12 --his his_2026-08-13.json
    python -m pipeline.tools.oratnek_diff --asof 2026-08-12 --his ... --commit dbc7676

`--his` is a JSON mapping of OUR panel keys to his lists, each entry either a
ticker or [ticker, his_rs_1m]:
    {"ll_hl_1st": [["OUST", 100]], "pp_2plus_10d": [["NTSK", 95], ...], "vcs": [], ...}
Panel keys: ll_hl_1st ll_hl_2nd ll_hl_trend_break pp_today pp_2plus_10d vcs
            weekly_momentum_97 bullish_4pct weekly_20_gainers

How the as-of rebuild works: the universe snapshot (market cap, Finviz perf
columns, sector...) comes from git -- the nightly commit closest AFTER the
session (`--commit` to pin one). yfinance bars are downloaded once and sliced
to `--asof` before every derived field is computed, by patching yf.download
inside the enrichment. So sp_*, vcs, pocket pivots, perf_5d, rs_line_pctl_21
are what the pipeline would have printed that night had those columns existed.
Percentile columns and scores are recomputed on that day's universe. Finviz
columns that are themselves windows (perf_1w, change_pct, rel_volume) are the
snapshot's own -- as of that session -- which is what we want.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import subprocess
import sys
from pathlib import Path

import pandas as pd

log = logging.getLogger("oratnek_diff")
OUT_DIR = Path("data/research/oratnek_diff")
PANEL_KEYS = ["ll_hl_1st", "ll_hl_2nd", "ll_hl_trend_break", "pp_today", "pp_2plus_10d",
              "vcs", "weekly_momentum_97", "bullish_4pct", "weekly_20_gainers"]
SHOW = ["market_cap", "avg_volume", "close", "adr_pct", "rs_1m", "rs_3m", "rs_line_pctl_21",
        "perf_1w", "perf_5d", "perf_1w_pctile", "perf_3m_pctile", "change_pct", "rel_volume",
        "trend_base", "sma50_dist", "vcs", "pp_count_10d", "vol10_green", "vol10_green_count_10d",
        "sp_signal", "sp_setup", "sp_days", "atr_from_sma50"]


def snapshot_commit(asof: str) -> str:
    """The nightly universe.json commit closest after `asof` (the run that
    carried that session's Finviz page)."""
    # the cron runs 21:30 UTC after the close, so the snapshot that carries
    # `asof`'s bars is the first commit after asof 21:00Z -- not the first
    # commit on that calendar day (that one is the previous session's)
    out = subprocess.run(
        ["git", "log", "--format=%h %cI", f"--since={asof}T21:00:00Z", "--", "data/output/universe.json"],
        capture_output=True, text=True, check=True).stdout.strip().splitlines()
    cands = [(pd.Timestamp(l.split()[1]).tz_convert("UTC").isoformat(), l.split()[0]) for l in out if l.strip()]
    cands = [c for c in cands if c[0] >= f"{asof}T21:00:00+00:00"]
    if not cands:
        raise SystemExit(f"no universe.json commit on/after {asof}")
    return sorted(cands)[0][1]


def load_snapshot(commit: str) -> pd.DataFrame:
    raw = subprocess.run(["git", "show", f"{commit}:data/output/universe.json"],
                         capture_output=True, text=True, check=True).stdout
    payload = json.loads(raw)
    rows = payload["rows"] if isinstance(payload, dict) else payload
    return pd.DataFrame(rows)


def rebuild_asof(universe: pd.DataFrame, asof: str, extra: set | None = None) -> pd.DataFrame:
    """Run enrich_universe + compute_universe_scores + screener flags with
    every yfinance download sliced to `asof`."""
    import yfinance as yf
    from pipeline.adapters import yfinance_adapter as YA
    from pipeline.screeners.run_all import compute_universe_scores
    from pipeline.themes import is_tradeable  # noqa: F401

    real_download = yf.download

    def sliced(*a, **k):
        df = real_download(*a, **k)
        try:
            return df.loc[:asof]
        except Exception:
            return df
    YA.yf.download = sliced
    try:
        base_cols = ["ticker", "close", "change_pct", "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_1y",
                     "perf_ytd", "sma20_dist", "sma50_dist", "sma200_dist", "atr", "rel_volume", "avg_volume",
                     "volume", "market_cap", "sector", "industry", "high_52w", "low_52w",
                     "eps_growth_next_y", "revenue_growth", "eps_growth_this_y"]
        u = universe[[c for c in base_cols if c in universe.columns]].copy()
        for c in ("market_cap", "avg_volume", "close"):
            u[c] = pd.to_numeric(u[c], errors="coerce")
        # bars only for the names the watchlist can show (its gate); the rest
        # stay in the frame so the cross-sectional scores keep their field
        gated = (u["market_cap"] >= 1e9) & (u["avg_volume"] * u["close"] >= 2e7)
        if extra:
            gated = gated | u["ticker"].isin(extra)      # his names get bars even outside our gate
        log.info("enriching %d gated of %d rows as of %s", int(gated.sum()), len(u), asof)
        part = YA.YfinanceAdapter().enrich_universe(u[gated].copy(), expected_session=pd.Timestamp(asof).date())
        enriched = pd.concat([part, u[~gated]], ignore_index=True)
    finally:
        YA.yf.download = real_download
    scored = compute_universe_scores(enriched)
    # the pctile columns + momentum flag live in run_all after scoring; redo the two we need
    scored["perf_1w_pctile"] = pd.to_numeric(scored["perf_1w"], errors="coerce").rank(pct=True, na_option="top").round(4)
    scored["perf_3m_pctile"] = pd.to_numeric(scored["perf_3m"], errors="coerce").rank(pct=True, na_option="top").round(4)
    return scored


def build_watchlist(scored: pd.DataFrame, asof: str) -> dict:
    from pipeline.screeners.watchlist import build
    rows = json.loads(scored.to_json(orient="records", date_format="iso"))
    return build(rows, date=asof, group_states=None)


def full_membership(scored: pd.DataFrame) -> dict:
    from pipeline.screeners.watchlist import PANELS, passes_gate
    rows = json.loads(scored.to_json(orient="records"))
    out = {}
    for k in PANEL_KEYS:
        p = PANELS[k]
        out[k] = [r["ticker"] for r in rows if passes_gate(r) and p.test(r)]
    return out


def diff(scored: pd.DataFrame, ours: dict, his: dict) -> str:
    by = {r["ticker"]: r for r in json.loads(scored.to_json(orient="records"))}
    buf = io.StringIO()
    w = buf.write
    w(f"{'panel':20s} {'his':>4s} {'ours':>5s} {'both':>5s} {'ours_rs_high':>12s}\n")
    for k in PANEL_KEYS:
        h = [x[0] if isinstance(x, list) else x for x in his.get(k, [])]
        o = ours.get(k, [])
        both = [t for t in h if t in o]
        rsh = sum(1 for t in o if (by.get(t, {}).get("rs_line_pctl_21") or 0) >= 100)
        w(f"{k:20s} {len(h):4d} {len(o):5d} {len(both):5d} {rsh:12d}\n")
    w("\n-- his RS 1M vs our rs_line_pctl_21 --\n")
    for k in PANEL_KEYS:
        for x in his.get(k, []):
            if isinstance(x, list) and len(x) == 2:
                t, v = x
                ours_v = by.get(t, {}).get("rs_line_pctl_21")
                flag = "" if ours_v is not None and round(ours_v) == v else "   <-- MISMATCH"
                shown = "-" if ours_v is None else str(round(ours_v))
                w(f"  {t:6s} his {v:4d}  ours {shown:>4}{flag}\n")
    w("\n-- his-only names, with our reading --\n")
    for k in PANEL_KEYS:
        h = [x[0] if isinstance(x, list) else x for x in his.get(k, [])]
        for t in h:
            if t in ours.get(k, []):
                continue
            r = by.get(t)
            if r is None:
                w(f"  {k:18s} {t:6s} NOT IN UNIVERSE\n"); continue
            w(f"  {k:18s} {t:6s} " + " ".join(f"{c}={_fmt(r.get(c))}" for c in SHOW) + "\n")
    w("\n-- ours-only names (first 15 per panel) --\n")
    for k in PANEL_KEYS:
        h = [x[0] if isinstance(x, list) else x for x in his.get(k, [])]
        extra = [t for t in ours.get(k, []) if t not in h]
        w(f"  {k:18s} +{len(extra)}: {' '.join(extra[:15])}\n")
    return buf.getvalue()


def _fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.3g}" if abs(v) < 1000 else f"{v:.3g}"
    return str(v)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", required=True, help="session the page was built on, YYYY-MM-DD")
    ap.add_argument("--his", required=True, help="JSON: our panel key -> [ticker | [ticker, his_rs]]")
    ap.add_argument("--commit", help="pin the universe.json snapshot commit")
    ap.add_argument("--reuse", action="store_true", help="reuse a cached rebuild for --asof if present")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache = OUT_DIR / f"universe_asof_{args.asof}.json"
    if args.reuse and cache.exists():
        scored = pd.DataFrame(json.loads(cache.read_text()))
        log.info("reusing %s", cache)
    else:
        commit = args.commit or snapshot_commit(args.asof)
        log.info("snapshot commit %s", commit)
        universe = load_snapshot(commit)
        log.info("snapshot rows %d", len(universe))
        his_names = {x[0] if isinstance(x, list) else x
                     for v in json.loads(Path(args.his).read_text()).values() for x in v}
        scored = rebuild_asof(universe, args.asof, extra=his_names)
        cache.write_text(scored.to_json(orient="records", date_format="iso"))
        log.info("cached %s", cache)

    his = json.loads(Path(args.his).read_text())
    ours = full_membership(scored)
    report = diff(scored, ours, his)
    print(report)
    (OUT_DIR / f"diff_{args.asof}.txt").write_text(report)
    (OUT_DIR / f"his_{args.asof}.json").write_text(json.dumps(his, indent=1))
    (OUT_DIR / f"ours_{args.asof}.json").write_text(json.dumps(ours, indent=1))
    log.info("archived under %s", OUT_DIR)


if __name__ == "__main__":
    sys.exit(main())
