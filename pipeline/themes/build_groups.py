"""Build the group layer: industries + themes, scored and classified.

Produces ``data/output/groups.json`` with three sections:

``industries``  ~145 Finviz industries, mechanical, zero maintenance
``themes``      the curated cross-cutting layer (see taxonomy.py)
``stocks``      per-ticker RS payload + rank inside its industry

Run standalone::

    python -m pipeline.themes.build_groups
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.marketcal import market_today
from pipeline.themes import is_tradeable, rs_engine, taxonomy
from pipeline.themes.etf_holdings import load_holdings

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/output")
UNIVERSE_PATH = OUTPUT_DIR / "universe.json"
ETF_PATH = OUTPUT_DIR / "etf_data.json"
VERDICTS_PATH = Path("data/reference/taxonomy_verdicts.json")

# How old a verdict may be before it stops being trusted. Themes drift as
# constituents list and delist; a verdict from last spring describes a group
# that no longer exists.
VERDICT_MAX_AGE_DAYS = 120
BENCHMARK = "SPY"

MIN_INDUSTRY_MEMBERS = 5
MIN_THEME_MEMBERS = 2      # below this there is no group, only a ticker
MEASURABLE_MEMBERS = 5     # below this a co-movement reading is not credible


def is_foreign_listing(symbol: str) -> bool:
    """True for non-US listings that can never match a US universe.

    ETF holdings come back with exchange suffixes (0700.HK, CCO.TO, PLS.AX,
    600111.SS, HDFCBANK.NS).  KWEB and INDA are made almost entirely of these,
    which is why their seeds resolved to zero members before this filter.
    """
    return "." in symbol or symbol.isdigit()


def load_universe(path: Path = UNIVERSE_PATH,
                  tradeable_only: bool = True) -> List[Dict[str, Any]]:
    """Universe rows, filtered to the tradeable set by default.

    Themes are aggregated over names you could actually take a position in.
    Before this filter existed the shipped themes were built on all 5,615 rows
    while validation ran on the 3,025 liquid ones -- so the object being
    validated was not the object being published. Pass tradeable_only=False
    for screener-style work that wants every name.
    """
    payload = json.loads(path.read_text())
    rows = payload.get("rows", payload if isinstance(payload, list) else [])
    total = len(rows)
    if tradeable_only:
        rows = [r for r in rows if is_tradeable(r)]
    logger.info("Loaded %d universe rows (%d tradeable of %d)",
                len(rows), len(rows), total)
    return rows


def load_benchmark(path: Path = ETF_PATH, ticker: str = BENCHMARK) -> Dict[str, Any]:
    """Benchmark perf_* row.

    etf_data carries perf_1w/1m/3m but not perf_6m, so the 3m..6m bucket
    degrades to NaN for the benchmark and therefore for everything measured
    against it.  That is correct behaviour -- better a missing far bucket
    than one silently benchmarked against zero.
    """
    rows = json.loads(path.read_text())
    for row in rows:
        if row.get("ticker") == ticker:
            return row
    raise ValueError(f"Benchmark {ticker} not found in {path}")


def build_industries(
    universe: Sequence[Mapping[str, Any]],
    benchmark: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    return rs_engine.score_groups(
        universe,
        group_key="industry",
        benchmark=benchmark,
        min_members=MIN_INDUSTRY_MEMBERS,
    )


def resolve_theme_members(
    theme: taxonomy.Theme,
    universe: Sequence[Mapping[str, Any]],
    holdings: Mapping[str, Sequence[str]],
) -> List[Mapping[str, Any]]:
    """Resolve a theme's constituent rows by its declared method."""
    by_ticker = {str(r.get("ticker")): r for r in universe if r.get("ticker")}

    if theme.method == "proxy":
        # The fund itself is the instrument; there are no constituents to
        # resolve.  build_themes scores these off etf_data directly.
        members = []

    elif theme.method == "rule":
        members = [r for r in universe if theme.rule and theme.rule(r)]

    elif theme.method in ("industry", "etf"):
        # Both methods can carry an industry backbone; ETF seeds add the
        # cross-cutting names no industry contains.
        wanted = set(theme.industries)
        picked: dict[str, Mapping[str, Any]] = {
            str(r["ticker"]): r for r in universe
            if r.get("industry") in wanted and r.get("ticker")
        }
        for etf in theme.etf:
            for symbol in holdings.get(etf, ()):
                if is_foreign_listing(symbol):
                    continue
                row = by_ticker.get(symbol)
                if row is not None:
                    picked[symbol] = row
        members = list(picked.values())

    else:
        raise ValueError(f"Unknown method {theme.method!r} for {theme.name}")

    for ticker in theme.extra:
        row = by_ticker.get(ticker)
        if row is not None and row not in members:
            members.append(row)

    if theme.exclude:
        drop = set(theme.exclude)
        members = [r for r in members if str(r.get("ticker")) not in drop]

    return members


def build_themes(
    universe: Sequence[Mapping[str, Any]],
    benchmark: Mapping[str, Any],
    holdings: Mapping[str, Sequence[str]],
    etf_rows: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Score every theme.  Returns (scored, skipped-with-reason)."""
    scored: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []
    etf_rows = etf_rows or {}

    for theme in taxonomy.THEMES:
        if theme.method == "proxy":
            row = etf_rows.get(theme.etf[0]) if theme.etf else None
            if row is None:
                skipped.append({
                    "theme": theme.name, "method": "proxy", "members": "0",
                    "reason": f"proxy ETF {theme.etf[:1]} not in etf_data",
                })
                continue
            payload = rs_engine.score_row(row, benchmark)
            if payload["state"] is None:
                skipped.append({
                    "theme": theme.name, "method": "proxy", "members": "0",
                    "reason": "unusable RS inputs",
                })
                continue
            payload.update({
                "group": theme.name, "method": "proxy", "source": theme.source,
                "members": 1, "tickers": [theme.etf[0]], "needs_manual": False,
                # n=1 by design. The fund *is* the instrument, so its RS
                # reading is exact -- not the same situation as a constituent
                # theme that only managed to find two members.
                "measurable": True,
            })
            for col in rs_engine.PERSISTENCE_COLS:
                payload[col] = rs_engine.safe_round(row.get(col))
            scored.append(payload)
            continue

        members = resolve_theme_members(theme, universe, holdings)

        if len(members) < MIN_THEME_MEMBERS:
            skipped.append({
                "theme": theme.name,
                "method": theme.method,
                "members": str(len(members)),
                "reason": "too few members",
            })
            continue

        synthetic = rs_engine.aggregate_rows(members)
        payload = rs_engine.score_row(synthetic, benchmark)
        if payload["state"] is None:
            skipped.append({
                "theme": theme.name,
                "method": theme.method,
                "members": str(len(members)),
                "reason": "unusable RS inputs",
            })
            continue

        payload.update({
            "group": theme.name,
            "method": theme.method,
            "source": theme.source,
            "members": len(members),
            # A two-name "theme" still has a median return, but calling that a
            # group reading implies a cohesion that cannot be tested at n=2.
            # Surfaced as a watchlist instead of silently scored or silently
            # dropped -- the tradeable GLP-1 universe really is this small.
            "measurable": len(members) >= MEASURABLE_MEMBERS,
            "tickers": sorted(str(m.get("ticker")) for m in members if m.get("ticker")),
            "needs_manual": theme.name in taxonomy.NEEDS_MANUAL,
        })
        for col in synthetic:
            payload[col] = rs_engine.safe_round(synthetic.get(col))
        scored.append(payload)

    # Cohort mode, matching score_groups. Scoring themes against the benchmark
    # while industries are scored against their peers would put two different
    # denominators (3 vs 5) in one column -- the exact thing persistence_of
    # exists to prevent.
    for payload in scored:
        p = rs_engine.persistence(
            {c: payload.get(c) for c in rs_engine.PERSISTENCE_COLS},
            benchmark, cohort=scored,
        )
        payload["persistence"] = p[0] if p else None
        payload["persistence_of"] = p[1] if p else None

    scored.sort(key=lambda r: (r["excess_3m"] is None, -(r["excess_3m"] or 0)))
    return scored, skipped


def audit_taxonomy(
    universe: Sequence[Mapping[str, Any]],
    holdings: Mapping[str, Sequence[str]],
    etf_rows: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """Check every hand-written reference in the taxonomy against real data.

    A curated list is only worth having if every line in it is verified.  A
    ticker that silently fails to resolve does not raise an error -- it just
    makes the theme quietly smaller and its reading quietly wrong.  This
    surfaces all four ways that can happen so each one gets signed off.
    """
    known_tickers = {str(r["ticker"]) for r in universe if r.get("ticker")}
    known_industries = {r.get("industry") for r in universe if r.get("industry")}

    unknown_extra: List[Dict[str, str]] = []
    unknown_industry: List[Dict[str, str]] = []
    unknown_etf: List[Dict[str, str]] = []
    missing_holdings: List[Dict[str, str]] = []

    for theme in taxonomy.THEMES:
        for ticker in theme.extra:
            if ticker not in known_tickers:
                unknown_extra.append({"theme": theme.name, "ticker": ticker})
        for industry in theme.industries:
            if industry not in known_industries:
                unknown_industry.append({"theme": theme.name, "industry": industry})
        for etf in theme.etf:
            if theme.method == "proxy":
                if etf not in etf_rows:
                    unknown_etf.append({"theme": theme.name, "etf": etf})
            elif etf not in holdings:
                missing_holdings.append({"theme": theme.name, "etf": etf})

    return {
        "unknown_extra_tickers": unknown_extra,
        "unknown_industries": unknown_industry,
        "proxy_etf_not_in_etf_data": unknown_etf,
        "etf_without_cached_holdings": missing_holdings,
        "clean": not (unknown_extra or unknown_industry
                      or unknown_etf or missing_holdings),
    }


def load_verdicts(path: Path = VERDICTS_PATH) -> Dict[str, Any]:
    """Stored co-movement verdicts from validate_taxonomy.

    Absent or stale verdicts leave every theme unvalidated rather than
    silently publishable -- an unproven theme should look unproven, not
    look like one that quietly passed.
    """
    if not path.exists():
        logger.warning("No verdicts at %s - themes ship unvalidated", path)
        return {}
    payload = json.loads(path.read_text())
    try:
        age = (datetime.now(timezone.utc)
               - datetime.fromisoformat(payload["generated_at"])).days
    except (KeyError, ValueError):
        age = None
    if age is not None and age > VERDICT_MAX_AGE_DAYS:
        logger.warning("Verdicts are %d days old (limit %d) - treating as absent",
                       age, VERDICT_MAX_AGE_DAYS)
        return {}
    return payload.get("themes", {})


def state_counts(groups: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    counts = {s: 0 for s in rs_engine.STATES}
    for g in groups:
        state = g.get("state")
        if state in counts:
            counts[state] += 1
    return counts


def run() -> Dict[str, Any]:
    universe = load_universe()
    benchmark = load_benchmark()
    holdings = load_holdings()
    etf_rows = {r["ticker"]: r for r in json.loads(ETF_PATH.read_text())}

    verdicts = load_verdicts()
    industries = build_industries(universe, benchmark)
    themes, skipped = build_themes(universe, benchmark, holdings, etf_rows)

    for t in themes:
        v = verdicts.get(t["group"], {})
        t["validation"] = v.get("verdict")
        t["validation_excess"] = v.get("excess")
        # Publishable = the market agrees these names move together, or the
        # theme is a single fund whose reading is exact by construction, or it
        # is a factor grouping that never claimed co-movement. Everything else
        # is provisional and stays out of the frontend.
        # Three ways to be publishable, and they are different claims:
        #   proxy  -- one fund; its reading is exact by construction
        #   rule   -- a factor grouping, which never claimed co-movement, so
        #             a co-movement verdict is not the bar it has to clear
        #   other  -- the market agrees these names move together
        # IPOs was briefly blocked here for failing a test it does not sit:
        # its members are recent listings, so they are thin in a 10y panel by
        # definition, which says nothing about whether the rule works.
        t["publish"] = bool(
            t.get("measurable", True)
            and (t["method"] in ("proxy", "rule")
                 or v.get("verdict") in ("real", "weak"))
        )
    stocks = rs_engine.rank_within_group(universe, "industry", benchmark)
    audit = audit_taxonomy(universe, holdings, etf_rows)

    payload = {
        "date": market_today().isoformat(),
        "benchmark": BENCHMARK,
        "universe_size": len(universe),
        "industries": industries,
        "themes": themes,
        "themes_skipped": skipped,
        "audit": audit,
        "stocks": stocks,
        "summary": {
            "publishable_themes": sum(1 for t in themes if t.get("publish")),
            "provisional_themes": sum(1 for t in themes if not t.get("publish")),
            "industries": len(industries),
            "industry_states": state_counts(industries),
            "themes": len(themes),
            "theme_states": state_counts(themes),
            "themes_skipped": len(skipped),
            "taxonomy": taxonomy.summary(),
        },
    }
    return payload


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    payload = run()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "groups.json"
    out.write_text(json.dumps(payload, indent=2, default=str))

    s = payload["summary"]
    logger.info("industries=%d %s", s["industries"], s["industry_states"])
    logger.info("themes=%d %s", s["themes"], s["theme_states"])
    logger.info("skipped=%d", s["themes_skipped"])
    a = payload["audit"]
    if a["clean"]:
        logger.info("taxonomy audit: CLEAN")
    else:
        logger.warning(
            "taxonomy audit: %d unknown tickers, %d unknown industries, "
            "%d missing proxy ETFs, %d ETFs without holdings",
            len(a["unknown_extra_tickers"]), len(a["unknown_industries"]),
            len(a["proxy_etf_not_in_etf_data"]), len(a["etf_without_cached_holdings"]),
        )
    logger.info("wrote %s", out)


if __name__ == "__main__":
    main()
