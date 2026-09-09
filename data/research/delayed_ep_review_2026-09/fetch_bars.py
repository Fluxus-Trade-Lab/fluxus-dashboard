"""Pull the ledger's tickers + SPY once and cache them next to this file.

Written 2026-09-09. Everything else in this directory reads bars.csv, so a
re-run -- mine or a verifier's -- costs zero vendor calls. We have hit Yahoo
into a 401 once by re-fetching data we already had
([[pitfall_refetched_data_we_already_had]]); one batched download, cached, is
the whole vendor budget of this study.

  PYTHONPATH=. python3 data/research/delayed_ep_review_2026-09/fetch_bars.py
"""
from __future__ import annotations
import csv
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).parent
LOG = Path("data/history/delayed_ep_log.csv")
OUT = HERE / "bars.csv"
BENCH = "SPY"


def main() -> int:
    tickers = sorted({r["ticker"] for r in csv.DictReader(LOG.open(newline=""))})
    raw = yf.download(tickers + [BENCH], period="120d", interval="1d",
                      group_by="ticker", auto_adjust=False, progress=False,
                      threads=True)
    rows = []
    for t in tickers + [BENCH]:
        try:
            s = raw[t]["Close"].dropna()
        except KeyError:
            continue
        rows += [(t, str(i.date()), float(v)) for i, v in s.items()]
    with OUT.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "date", "close"])
        w.writerows(sorted(rows))
    print(f"{len(rows)} bars, {len({r[0] for r in rows})} tickers -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
