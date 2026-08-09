"""Fetch and store daily closes for every basket the rotation layer needs.

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
from typing import Dict

import yfinance as yf

from pipeline.rotation import baskets as B

log = logging.getLogger(__name__)
OUT_DIR = Path("data/output/baskets")


def fetch(period: str = "2y", out_dir: Path = OUT_DIR) -> Dict[str, int]:
    """Download and store closes for every required basket.

    A callable, not just a CLI: the daily pipeline runs this step itself, and a
    module whose only entry point is `main()` is a module the cron cannot use —
    which is exactly how the group snapshot ended up never running.
    """
    data = yf.download(B.REQUIRED, period=period, group_by="ticker",
                       auto_adjust=True, progress=False, threads=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    written, failed = 0, []
    for ticker in B.REQUIRED:
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
        (out_dir / f"{ticker}.json").write_text(
            json.dumps({"ticker": ticker, "bars": bars}))
        written += 1

    log.info("stored %d/%d baskets in %s", written, len(B.REQUIRED), out_dir)
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
