"""Shared daily-OHLC store — **check here before fetching prices from the network.**

The pipeline already persists daily OHLC per ticker in `data/output/tickers/<T>.json`
(`ohlc_2y`, and a trailing `ohlc_1y` slice). Any code that needs historical bars —
technical context, backtests, MA/ATR at a date — should call `load_local_ohlc()`
FIRST and only hit yfinance when the local data is missing or too shallow. This
avoids redundant network calls and keeps every consumer on the same adjusted scale.

Also provides point-in-time technicals (20EMA / 50SMA / 200SMA / ATR14 + a setup
classifier) that mirror the frontend `tradeTechnicals.js`, so the H1 report and the
dashboard Diagnosis tab tell the same story.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

TICKERS_DIR = Path("data/output/tickers")


def _safe(sym: str) -> str:
    return sym.upper().replace("/", "_").replace("^", "_")


def load_local_ohlc(ticker: str, min_start: Optional[str] = None,
                    tickers_dir: Path = TICKERS_DIR) -> Optional[list[dict]]:
    """Return locally-stored daily bars for `ticker`, or None if absent/too shallow.

    Prefers `ohlc_2y`, falls back to `ohlc_1y`. If `min_start` (ISO date) is given,
    returns None when the stored history doesn't reach back that far — the caller
    should then fetch fresh. Bars are dicts: {date, open, high, low, close, volume}.
    """
    path = tickers_dir / f"{_safe(ticker)}.json"
    if not path.exists():
        return None
    try:
        j = json.load(open(path))
    except (ValueError, OSError):
        return None
    bars = j.get("ohlc_2y") or j.get("ohlc_1y") or j.get("ohlc")
    if not bars:
        return None
    if min_start and bars[0]["date"] > min_start:
        return None
    return bars


# --------------------------------------------------------------------------- #
# Point-in-time technicals (mirror of frontend tradeTechnicals.js)
# --------------------------------------------------------------------------- #
def _sma(closes, n, end):
    if end + 1 < n:
        return None
    return sum(closes[end - n + 1:end + 1]) / n


def _ema(closes, n, end):
    if end + 1 < n:
        return None
    k = 2 / (n + 1)
    e = sum(closes[:n]) / n
    for i in range(n, end + 1):
        e = closes[i] * k + e * (1 - k)
    return e


def _atr14(bars, end, period=14):
    if end < period:
        return None
    trs = []
    for i in range(end - period + 1, end + 1):
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / period


def _index_as_of(bars, date_str):
    idx = -1
    for i, b in enumerate(bars):
        if b["date"] <= date_str:
            idx = i
        else:
            break
    return idx


def trade_technicals(bars, entry_date: str, direction: str) -> Optional[dict]:
    """Technicals as of `entry_date` (bars up to & including it). Reference price
    is the entry-day ADJUSTED close, matching the OHLC scale (never the raw fill)."""
    if not bars or len(bars) < 20:
        return None
    entry_date = entry_date[:10]
    idx = _index_as_of(bars, entry_date)
    if idx < 20:
        return None
    closes = [b["close"] for b in bars]
    px = closes[idx]
    ema20 = _ema(closes, 20, idx)
    sma50 = _sma(closes, 50, idx)
    sma200 = _sma(closes, 200, idx)
    sma50_prior = _sma(closes, 50, max(0, idx - 20))
    atr = _atr14(bars, idx)
    prev_close = bars[idx - 1]["close"] if idx >= 1 else None
    hi20 = max((bars[i]["high"] for i in range(max(0, idx - 20), idx)), default=None)

    if ema20 is not None and sma50 is not None:
        if sma200 is not None:
            stack = "bull" if ema20 > sma50 > sma200 else "bear" if ema20 < sma50 < sma200 else "mixed"
        else:
            stack = "bull*" if ema20 > sma50 else "bear*"
    else:
        stack = None

    return {
        "as_of": bars[idx]["date"],
        "ref_price": px,
        "ema20": ema20, "sma50": sma50, "sma200": sma200, "atr": atr,
        "atr_pct": (atr / px * 100) if (atr and px) else None,
        "ext_atr": ((px - ema20) / atr) if (atr and ema20 is not None) else None,
        "above_ema20": (px > ema20) if ema20 is not None else None,
        "above_sma50": (px > sma50) if sma50 is not None else None,
        "above_sma200": (px > sma200) if sma200 is not None else None,
        "stack": stack,
        "sma50_slope": ((sma50 - sma50_prior) / sma50_prior * 100)
                       if (sma50 is not None and sma50_prior) else None,
        "dist_hi20_pct": ((px - hi20) / hi20 * 100) if hi20 else None,
        "gap_pct": ((px - prev_close) / prev_close * 100) if prev_close else None,
    }


def classify_trade(pnl: float, direction: str, tech: Optional[dict],
                   is_reattack: bool, R: Optional[float] = None) -> dict:
    """Winning-type (pnl>0) or mistake-type (pnl<=0) label. Mirrors the JS classifier."""
    long = direction != "short"
    ext = tech.get("ext_atr") if tech else None
    stack = tech.get("stack") if tech else None
    notes = []
    if tech and tech.get("atr_pct") and tech["atr_pct"] > 6:
        notes.append("high-vol name")

    if pnl > 0:
        if not long:
            typ = "Trend short" if (stack or "").startswith("bear") else "Counter-trend short"
        elif ext is not None and ext > 3:
            typ = "Extended momentum (chased & worked)"
        elif (stack or "").startswith("bull") and tech.get("above_ema20") and ext is not None and ext >= 0.3:
            typ = "Momentum breakout"
        elif tech and tech.get("above_sma50") and ext is not None and ext < 0.5 and (tech.get("sma50_slope") or 0) > 0:
            typ = "Pullback continuation"
        elif (stack or "").startswith("bull"):
            typ = "Trend continuation"
        else:
            typ = "Momentum long"
        return {"type": typ, "win": True, "notes": notes}

    # losers
    typ = "Failed momentum"
    if is_reattack:
        typ = "Re-attack (avg down into red)"
    elif long and ext is not None and ext > 2:
        typ = f"Chased extended (+{ext:.1f} ATR over 20EMA)"
    elif long and tech and tech.get("above_sma50") is False and (tech.get("sma50_slope") or 0) < -1:
        typ = "Knife-catch (below a falling 50SMA)"
    elif long and stack == "bear":
        typ = "Bought a downtrend (bear MA stack)"
    if R is not None and R < -1.5:
        notes.append(f"blew through stop ({R:.1f}R)")
    return {"type": typ, "win": False, "notes": notes}
