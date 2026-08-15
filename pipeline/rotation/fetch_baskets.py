"""Fetch and store daily closes for every fund the bar store carries.

Small and separate from `build_rotation` on purpose: eleven ETFs plus the
benchmark is a single yfinance call, and keeping the network out of the build
means the rotation object can be rebuilt offline and replayed over a truncated
history without touching a socket.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

import yfinance as yf

from pipeline.rotation import baskets as B
from pipeline.themes import taxonomy

log = logging.getLogger(__name__)
OUT_DIR = Path("data/output/baskets")


def required_tickers() -> List[str]:
    """Every fund whose bars this store has to carry.

    Two consumers, one store. Rotation needs its style baskets; the theme layer
    needs the funds behind its `proxy` themes — both to fill the 3m..6m bucket
    etf_data cannot reach, and to draw ten weeks of state from price today
    rather than waiting on the archive. Fetching the union once removes the
    failure mode where a fund is present for one consumer and missing for the
    other.
    """
    proxies = {t.etf[0] for t in taxonomy.THEMES
               if t.method == "proxy" and t.etf}
    return sorted(set(B.REQUIRED) | proxies)


def fetch(period: str = "2y", out_dir: Path = OUT_DIR) -> Dict[str, int]:
    """Download and store closes for every fund the store carries.

    A callable, not just a CLI: the daily pipeline runs this step itself, and a
    module whose only entry point is `main()` is a module the cron cannot use —
    which is exactly how the group snapshot ended up never running.
    """
    tickers = required_tickers()
    data = yf.download(tickers, period=period, group_by="ticker",
                       auto_adjust=True, progress=False, threads=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    written, failed = 0, []
    for ticker in tickers:
        try:
            sub = data[ticker].dropna(subset=["Close"])
        except KeyError:
            failed.append(ticker)
            continue
        if sub.empty:
            failed.append(ticker)
            continue
        bars = [{"date": idx.strftime("%Y-%m-%d"), "close": round(float(row.Close), 4)}
                for idx, row in sub.iterrows()]

        # Never replace a series with a sparser one. A throttled batch can
        # return a PARTIAL series — SPLV came back missing three mid-July
        # sessions Yahoo actually has — and overwriting meant a good file on
        # disk became a holey one, which align then (correctly) refused,
        # which silently cost the volatility cut its vote. Fresh-but-holey
        # loses to stale-but-complete; the next clean fetch still wins
        # because it has at least as many bars plus the new session.
        path = out_dir / f"{ticker}.json"
        if path.exists():
            try:
                old_bars = json.loads(path.read_text()).get("bars") or []
            except (ValueError, OSError):
                old_bars = []
            if len(bars) < len(old_bars):
                log.error("%s: fetched %d bars but the stored file has %d — "
                          "keeping the stored file (partial response)",
                          ticker, len(bars), len(old_bars))
                failed.append(ticker)
                continue
        path.write_text(json.dumps({"ticker": ticker, "bars": bars}))
        written += 1

    log.info("stored %d/%d baskets in %s", written, len(tickers), out_dir)
    if failed:
        # Loud, not silent: a basket that vanishes changes which cuts can vote,
        # and a cut voting on one leg would read as agreement.
        log.error("no data for: %s", ", ".join(failed))
    return {"written": written, "failed": len(failed)}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--period", default="2y")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    fetch(args.period, args.out)


if __name__ == "__main__":
    main()
