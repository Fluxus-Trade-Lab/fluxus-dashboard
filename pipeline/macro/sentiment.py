"""Sentiment and cross-asset layer -- the free half of what TSF rents.

TSF's weekend macro pieces run on SentimenTrader and MenthorQ charts.  Most of
what those charts show is free at source; the inventory in
``Fluxus_Receipts/tsf/sentiment_cycle_data_inventory.md`` sorted his inputs
into what is buyable, what is computable, and what is simply published.

This module collects the published half:

``AAII``    weekly retail bull/bear survey -- free CSV from AAII
``NAAIM``   weekly active-manager exposure index -- free from NAAIM
``MOVE``    bond volatility; equities dislike it rising
``HYG``     high yield credit -- sometimes leads equities, as TSF himself notes
``XLP``     staples relative strength -- where defensive money is going
``USO``     oil, for the periods when the tape trades with it
``IPO``     recent-IPO behaviour -- the outermost edge of risk appetite

The two inputs deliberately *not* collected are CTA positioning and
vol-control exposure.  Both are bank model estimates resold by a vendor, get
revised after the fact, and are presented elsewhere as if they were
observations.  A number we cannot source or reproduce does not belong in a
letter that promises measurement.

    python -m pipeline.macro.sentiment
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.marketcal import market_today

logger = logging.getLogger(__name__)

OUT = Path("data/output/sentiment.json")

# Price-based series, fetched together. Ratios are computed against SPY so the
# reading is relative strength, not direction.
PRICE_SERIES: Dict[str, str] = {
    "MOVE": "^MOVE",
    "HYG": "HYG",
    "XLP": "XLP",
    "USO": "USO",
    "IPO": "IPO",
    "SPY": "SPY",
}
RATIO_VS_SPY = ("HYG", "XLP", "IPO")

# Both surveys resisted automated collection when this was built (2026-08-09):
# AAII answers 403 with NOINDEX/NOFOLLOW, which is an explicit statement that
# they do not want scrapers -- we honour it rather than route around it. NAAIM
# no longer publishes a direct CSV link; their numbers are open data on Nasdaq
# Data Link, which needs a free API key.
#
# So both arrive by hand until a licensed route exists. MANUAL_PATH is a small
# file you top up weekly; anything absent from it is reported as unavailable
# rather than quietly omitted.
MANUAL_PATH = Path("data/reference/sentiment_manual.json")

LOOKBACK_DAYS = 400
PCTILE_WINDOW = 252


@dataclass
class Reading:
    name: str
    value: Optional[float]
    pctile_1y: Optional[float]
    change_1w: Optional[float]
    source: str
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": _round(self.value),
            "pctile_1y": _round(self.pctile_1y, 1),
            "change_1w": _round(self.change_1w),
            "source": self.source,
            "note": self.note,
        }


def _round(v: Optional[float], digits: int = 4) -> Optional[float]:
    if v is None or pd.isna(v):
        return None
    return round(float(v), digits)


def _pctile(series: pd.Series, window: int = PCTILE_WINDOW) -> Optional[float]:
    tail = series.dropna().tail(window)
    if len(tail) < 30:
        return None
    return float((tail <= tail.iloc[-1]).mean() * 100)


def fetch_prices() -> pd.DataFrame:
    import yfinance as yf
    data = yf.download(list(PRICE_SERIES.values()), period="2y",
                       interval="1d", auto_adjust=True, progress=False)
    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
    close = close.rename(columns={v: k for k, v in PRICE_SERIES.items()})
    return close.ffill()


def price_readings(close: pd.DataFrame) -> List[Reading]:
    out: List[Reading] = []
    for name in PRICE_SERIES:
        if name == "SPY" or name not in close.columns:
            continue
        series = close[name].dropna()
        if series.empty:
            logger.warning("%s returned no data", name)
            continue

        if name in RATIO_VS_SPY and "SPY" in close.columns:
            series = (close[name] / close["SPY"]).dropna()
            label, note = f"{name}/SPY", "ratio vs SPY, not absolute price"
        else:
            label, note = name, ""

        wk = series.pct_change(5).iloc[-1] if len(series) > 5 else None
        out.append(Reading(label, float(series.iloc[-1]), _pctile(series),
                           float(wk) if wk is not None else None,
                           "yfinance", note))
    return out


# Weekly series entered by hand. Shape:
#   {"AAII bull-bear spread": {"history": [["2026-08-06", 4.2], ...],
#                              "note": "positive = more bulls than bears"}}
MANUAL_SERIES = ("AAII bull-bear spread", "NAAIM exposure")


def manual_readings() -> List[Reading]:
    """Read hand-entered weekly surveys, with the same percentile treatment."""
    if not MANUAL_PATH.exists():
        logger.warning("No manual survey file at %s", MANUAL_PATH)
        return []

    payload = json.loads(MANUAL_PATH.read_text())
    out: List[Reading] = []
    for name in MANUAL_SERIES:
        entry = payload.get(name)
        if not entry or not entry.get("history"):
            continue
        hist = sorted(entry["history"], key=lambda x: x[0])
        s = pd.Series([v for _, v in hist])
        if s.empty:
            continue
        wk = float(s.iloc[-1] - s.iloc[-2]) if len(s) > 1 else None
        stale = hist[-1][0]
        out.append(Reading(name, float(s.iloc[-1]), _pctile(s, 104), wk,
                           f"manual entry, last updated {stale}",
                           entry.get("note", "")))
    return out


def run() -> Dict[str, Any]:
    readings = price_readings(fetch_prices()) + manual_readings()

    missing = [n for n in (*PRICE_SERIES, *MANUAL_SERIES)
               if n != "SPY" and not any(x.name.startswith(n) for x in readings)]

    return {
        "date": market_today().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "readings": [r.to_dict() for r in readings],
        # Absence is reported, never silently dropped: a sentiment panel that
        # quietly loses AAII looks identical to one where AAII is neutral.
        "unavailable": missing,
        "deliberately_excluded": {
            "CTA positioning": "bank model estimate, revised after the fact",
            "vol-control exposure": "same -- an estimate presented as an observation",
        },
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    payload = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))

    for r in payload["readings"]:
        pct = f"{r['pctile_1y']:5.1f}%ile" if r["pctile_1y"] is not None else "   n/a"
        logger.info("  %-22s %12s  %s", r["name"], r["value"], pct)
    if payload["unavailable"]:
        logger.warning("unavailable: %s", ", ".join(payload["unavailable"]))
    logger.info("wrote %s", OUT)


if __name__ == "__main__":
    main()
