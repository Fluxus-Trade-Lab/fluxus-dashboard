"""ETF holdings cache -- seeds for the cross-cutting theme layer.

A theme like "Uranium & Nuclear Energy" has no Finviz industry.  Rather than
hand-maintaining member lists (the approach that costs a competitor a year of
curation), we seed each theme from a proxy ETF's holdings and intersect that
with our own universe.

Holdings move slowly, so they live in a committed cache and are refreshed on
demand rather than on every pipeline run::

    python -m pipeline.themes.etf_holdings --refresh

If the cache is missing the build degrades gracefully: ETF-seeded themes are
reported as skipped with a reason instead of silently coming out empty.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Sequence

logger = logging.getLogger(__name__)

CACHE_PATH = Path("data/reference/etf_holdings.json")


def load_holdings(path: Path = CACHE_PATH) -> Dict[str, List[str]]:
    """Load the holdings cache. Missing cache is not an error."""
    if not path.exists():
        logger.warning("No ETF holdings cache at %s - ETF themes will be skipped", path)
        return {}
    payload = json.loads(path.read_text())
    holdings = payload.get("holdings", payload)
    return {k: list(v) for k, v in holdings.items()}


def fetch_holdings(tickers: Sequence[str]) -> Dict[str, List[str]]:
    """Fetch top holdings per ETF via yfinance.

    yfinance exposes only the top ~10 holdings for most funds, which is
    enough to seed a theme's leadership but is *not* the full basket.  The
    count is recorded so a thin seed is visible rather than assumed complete.
    """
    try:
        import yfinance as yf
    except ImportError:  # pragma: no cover - depends on env
        logger.error("yfinance not installed; cannot refresh holdings")
        return {}

    out: Dict[str, List[str]] = {}
    for ticker in tickers:
        try:
            fd = yf.Ticker(ticker).funds_data
            top = fd.top_holdings
            symbols = [str(s).upper() for s in top.index.tolist()]
            if symbols:
                out[ticker] = symbols
                logger.info("%s -> %d holdings", ticker, len(symbols))
            else:
                logger.warning("%s returned no holdings", ticker)
        except Exception as exc:  # noqa: BLE001 - third-party surface is broad
            logger.warning("%s holdings unavailable: %s", ticker, exc)
    return out


def theme_etfs() -> List[str]:
    """Every proxy ETF referenced by the taxonomy."""
    from pipeline.themes import taxonomy

    seen: list[str] = []
    for theme in taxonomy.THEMES:
        for etf in theme.etf:
            if etf not in seen:
                seen.append(etf)
    return seen


def refresh(path: Path = CACHE_PATH) -> Dict[str, List[str]]:
    tickers = theme_etfs()
    logger.info("Refreshing holdings for %d ETFs", len(tickers))
    holdings = fetch_holdings(tickers)

    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_holdings(path) if path.exists() else {}
    existing.update(holdings)  # keep anything this run failed to fetch

    path.write_text(json.dumps({
        "source": "yfinance funds_data.top_holdings",
        "note": "Top holdings only, not full baskets. Seeds for theme membership.",
        "holdings": existing,
    }, indent=2))
    logger.info("Wrote %d ETFs to %s", len(existing), path)
    return existing


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="re-fetch from yfinance")
    args = parser.parse_args()

    if args.refresh:
        refresh()
    else:
        holdings = load_holdings()
        print(f"{len(holdings)} ETFs cached")
        for k, v in sorted(holdings.items()):
            print(f"  {k:6s} {len(v):3d} holdings")


if __name__ == "__main__":
    main()
