"""Asset-layer signals -- the same knives, pointed at ETFs.

2026-08-20 (Andy: "要的!"): IBIT and GLD came up in a six-name check and the
system had nothing -- ETFs never enter the stock universe, and etf_data.json
carries raw performance only. This module gives ~26 core asset ETFs (indexes,
bonds, metals, energy, crypto, dollar, international, REITs) the exact same
signal fields a stock row carries: RS-line self-percentiles, MA-reclaim
crosses, the ATR Matrix position, 20-day closing highs.

Writes `data/output/asset_signals.json` (rows keyed like universe rows) and
appends one row per asset per session to `data/history/asset_signals.csv`
(registered in audit_archives) so forward studies need no rebuild.

Pure compute on supplied bars; the one yf.download lives in fetch()."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import pandas as pd

from pipeline.adapters.yfinance_adapter import (
    _crossed_up, calculate_atr, rs_line_pctl,
)

logger = logging.getLogger(__name__)

OUT = Path("data/output/asset_signals.json")
LOG = Path("data/history/asset_signals.csv")

# ticker -> (label, category). The asset layer, not the industry layer --
# sectors/industries/countries already live in etf_data.json.
ASSETS: Dict[str, tuple] = {
    "SPY": ("S&P 500", "index"), "QQQ": ("Nasdaq 100", "index"),
    "IWM": ("Russell 2000", "index"), "DIA": ("Dow", "index"), "RSP": ("S&P Equal Weight", "index"),
    "TLT": ("20y Treasuries", "bonds"), "IEF": ("7-10y Treasuries", "bonds"),
    "SHY": ("1-3y Treasuries", "bonds"), "HYG": ("High Yield", "bonds"),
    "LQD": ("IG Credit", "bonds"), "TIP": ("TIPS", "bonds"),
    "GLD": ("Gold", "metals"), "SLV": ("Silver", "metals"),
    "GDX": ("Gold Miners", "metals"), "SIL": ("Silver Miners", "metals"),
    "USO": ("Oil", "energy"), "UNG": ("Nat Gas", "energy"), "DBA": ("Agriculture", "commodities"),
    "IBIT": ("Bitcoin", "crypto"), "ETHA": ("Ethereum", "crypto"),
    "UUP": ("US Dollar", "fx"),
    "EEM": ("Emerging Mkts", "intl"), "EFA": ("Developed ex-US", "intl"),
    "FXI": ("China Large Cap", "intl"), "EWJ": ("Japan", "intl"),
    "VNQ": ("US REITs", "real_assets"),
}


def compute_row(ticker: str, hist: pd.DataFrame, spy_close: Optional[pd.Series]) -> Optional[Dict[str, Any]]:
    """One asset's signal row from its daily bars. Same definitions as the
    stock enrichment (rs_line_pctl / _crossed_up are the same functions)."""
    hist = hist.dropna(subset=["Close"]) if "Close" in hist else hist.dropna()
    n = len(hist)
    if n < 25:
        return None
    c = hist["Close"]
    close = float(c.iloc[-1])
    ema21_s = c.ewm(span=21, adjust=False).mean()
    sma50_s = c.rolling(50).mean()
    sma200 = float(c.rolling(200).mean().iloc[-1]) if n >= 200 else None
    atr = calculate_atr(hist)
    vol = float(hist["Volume"].iloc[-1]) if "Volume" in hist else None
    av = float(hist["Volume"].rolling(50).mean().iloc[-1]) if "Volume" in hist and n >= 50 else None
    ema21 = float(ema21_s.iloc[-1])
    sma50 = float(sma50_s.iloc[-1]) if n >= 50 else None
    label, category = ASSETS.get(ticker, (ticker, "other"))
    bench = spy_close if ticker != "SPY" else None
    row = {
        "ticker": ticker, "label": label, "category": category,
        "close": round(close, 2),
        "change_pct": round(float(c.iloc[-1] / c.iloc[-2] - 1), 4) if n >= 2 else None,
        "rel_volume": round(vol / av, 2) if vol and av else None,
        "perf_1w": round(float(close / c.iloc[-6] - 1), 4) if n >= 6 else None,
        "perf_1m": round(float(close / c.iloc[-22] - 1), 4) if n >= 22 else None,
        "perf_3m": round(float(close / c.iloc[-64] - 1), 4) if n >= 64 else None,
        "perf_6m": round(float(close / c.iloc[-127] - 1), 4) if n >= 127 else None,
        "rs_line_pctl_21": rs_line_pctl(c, bench) if bench is not None else None,
        "rs_line_pctl_63": rs_line_pctl(c, bench, 63) if bench is not None else None,
        "cross_ema21_up": _crossed_up(c, ema21_s),
        "cross_sma50_up": _crossed_up(c, sma50_s) if n >= 51 else None,
        "ema21_dist": round(close / ema21 - 1, 4) if ema21 else None,
        "sma50_dist": round(close / sma50 - 1, 4) if sma50 else None,
        "sma200_dist": round(close / sma200 - 1, 4) if sma200 else None,
        "atr_from_sma50": round((close - sma50) / atr, 2) if atr and sma50 else None,
        "hi20": bool(close >= float(c.iloc[-20:].max())),
        "high_52w_dist": round(close / float(c.max()) - 1, 4),
        "bar_date": str(hist.index[-1].date()),
    }
    for k in ("rs_line_pctl_21", "rs_line_pctl_63"):
        if row[k] is not None:
            row[k] = round(row[k], 1)
    return row


def build(hists: Mapping[str, pd.DataFrame], date: str) -> Dict[str, Any]:
    spy = hists.get("SPY")
    spy_close = spy["Close"].dropna() if spy is not None and "Close" in spy else None
    rows = []
    for t in ASSETS:
        h = hists.get(t)
        if h is None or not len(h):
            continue
        try:
            r = compute_row(t, h, spy_close)
        except Exception:  # noqa: BLE001 -- one bad fund never costs the file
            logger.exception("asset_signals: %s failed", t)
            continue
        if r:
            rows.append(r)
    return {"date": date, "count": len(rows),
            "note": "same definitions as universe rows: rs_line_pctl_* are RS-line SELF percentiles vs SPY; cross_* are close-crossed-up events; atr_from_sma50 is the ATR Matrix position",
            "rows": rows}


def fetch(tickers: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """One batch download, one retry -- 26 tickers is small."""
    import time
    import yfinance as yf
    tickers = tickers or list(ASSETS)
    if "SPY" not in tickers:
        tickers = ["SPY", *tickers]
    out: Dict[str, pd.DataFrame] = {}
    for attempt in range(3):
        missing = [t for t in tickers if t not in out]
        if not missing:
            break
        if attempt:
            time.sleep(20 * attempt)
        data = yf.download(missing, period="1y", group_by="ticker",
                           auto_adjust=True, progress=False, threads=True)
        for t in missing:
            try:
                h = data[t].dropna(subset=["Close"]) if len(missing) > 1 else data.dropna(subset=["Close"])
            except KeyError:
                continue
            if len(h):
                out[t] = h
    return out


def archive(payload: Mapping[str, Any], path: Path = LOG) -> int:
    """One row per (date, ticker), idempotent per date."""
    import csv
    fields = ["date", "ticker", "category", "close", "change_pct", "rel_volume",
              "rs_line_pctl_21", "rs_line_pctl_63", "cross_ema21_up", "cross_sma50_up",
              "atr_from_sma50", "ema21_dist", "sma50_dist", "hi20", "perf_1m", "perf_3m"]
    date = payload["date"]
    old = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != date]
    new = [{"date": date, **{k: r.get(k) for k in fields if k != "date"}} for r in payload["rows"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in [*old, *new]:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
    return len(new)
