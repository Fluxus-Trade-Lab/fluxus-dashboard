"""Export a per-theme membership sheet for manual sign-off.

The audit in ``build_groups`` proves every hand-written reference *resolves*.
It cannot prove a resolved name *belongs* -- that judgement is the curator's.
This writes the full member list of every theme, annotated with how each name
got there, so each list can be walked line by line and signed off.

    python -m pipeline.themes.export_review

Writes ``data/reference/theme_review.md``.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.marketcal import market_today
from pipeline.themes import taxonomy
from pipeline.themes.build_groups import (
    ETF_PATH,
    UNIVERSE_PATH,
    is_foreign_listing,
    load_universe,
)
from pipeline.themes.etf_holdings import load_holdings

logger = logging.getLogger(__name__)

OUT_PATH = Path("data/reference/theme_review.md")

# How a member arrived, in the order the resolver applies them.
ORIGIN_INDUSTRY = "industry"
ORIGIN_ETF = "etf-holding"
ORIGIN_EXTRA = "manual"
ORIGIN_RULE = "rule"


def member_origins(
    theme: taxonomy.Theme,
    universe: List[Dict[str, Any]],
    holdings: Mapping[str, Any],
) -> Dict[str, str]:
    """Map each resolved ticker to the reason it is in the theme."""
    by_ticker = {str(r["ticker"]): r for r in universe if r.get("ticker")}
    origins: Dict[str, str] = {}

    if theme.method == "rule" and theme.rule:
        for row in universe:
            if theme.rule(row) and row.get("ticker"):
                origins[str(row["ticker"])] = ORIGIN_RULE

    if theme.industries:
        wanted = set(theme.industries)
        for row in universe:
            if row.get("industry") in wanted and row.get("ticker"):
                origins.setdefault(str(row["ticker"]), ORIGIN_INDUSTRY)

    for etf in theme.etf:
        if theme.method == "proxy":
            continue
        for symbol in holdings.get(etf, ()):
            if is_foreign_listing(symbol) or symbol not in by_ticker:
                continue
            origins.setdefault(symbol, f"{ORIGIN_ETF}:{etf}")

    for ticker in theme.extra:
        if ticker in by_ticker:
            origins[ticker] = ORIGIN_EXTRA

    for ticker in theme.exclude:
        origins.pop(ticker, None)

    return origins


def render(universe: List[Dict[str, Any]], holdings: Mapping[str, Any],
           etf_rows: Mapping[str, Any]) -> str:
    by_ticker = {str(r["ticker"]): r for r in universe if r.get("ticker")}
    lines: List[str] = [
        "# Theme membership review",
        "",
        f"*Generated {market_today().isoformat()} from a {len(universe)}-row universe.*",
        "",
        "Every theme's resolved members, with how each name got in. "
        "`manual` entries are hand-written and carry no automatic justification "
        "-- those are the ones that most need a second look.",
        "",
        "Sign-off convention: strike a line to drop it, then add the ticker to "
        "that theme's `exclude` tuple in `taxonomy.py`.",
        "",
    ]

    for theme in taxonomy.THEMES:
        if theme.method == "proxy":
            fund = theme.etf[0] if theme.etf else "?"
            present = "present" if fund in etf_rows else "**MISSING from etf_data**"
            lines += [
                f"## {theme.name}",
                f"`proxy` · source: {theme.source} · fund: **{fund}** ({present})",
                "",
                "Tracks the fund's own price action; no constituents to review.",
                "",
            ]
            if theme.note:
                lines += [f"> {theme.note}", ""]
            continue

        origins = member_origins(theme, universe, holdings)
        header = f"## {theme.name}"
        meta = f"`{theme.method}` · source: {theme.source} · **{len(origins)} members**"
        lines += [header, meta, ""]

        if theme.note:
            lines += [f"> {theme.note}", ""]
        if theme.name in taxonomy.NEEDS_MANUAL:
            lines += ["> ⚠️ Flagged as needing a hand-built list.", ""]

        if not origins:
            lines += ["*No members resolved.*", ""]
            continue

        manual = sorted(t for t, o in origins.items() if o == ORIGIN_EXTRA)
        automatic = sorted(t for t, o in origins.items() if o != ORIGIN_EXTRA)

        if manual:
            lines += ["**Hand-written — verify each:**", ""]
            lines += ["| Ticker | Industry | Mkt cap ($B) |", "|---|---|---|"]
            for t in manual:
                row = by_ticker.get(t, {})
                cap = row.get("market_cap")
                cap_s = f"{cap/1e9:.1f}" if isinstance(cap, (int, float)) and cap else "-"
                lines.append(f"| {t} | {row.get('industry', '-')} | {cap_s} |")
            lines.append("")

        if automatic:
            lines += [
                f"**Resolved automatically ({len(automatic)}):**",
                "",
                "`" + "` · `".join(automatic) + "`",
                "",
            ]

    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    universe = load_universe(UNIVERSE_PATH)
    holdings = load_holdings()
    etf_rows = {r["ticker"]: r for r in json.loads(ETF_PATH.read_text())}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(render(universe, holdings, etf_rows))
    logger.info("Wrote %s", OUT_PATH)


if __name__ == "__main__":
    main()
