"""Shared daily-OHLC store — **check here before fetching prices from the network.**

The pipeline already persists daily OHLC per ticker in `data/output/tickers/<T>.json`
(`ohlc_2y`, and a trailing `ohlc_1y` slice). Any code that needs historical bars —
technical context, backtests, MA/ATR at a date — should call `load_local_ohlc()`
FIRST and only hit yfinance when the local data is missing or too shallow. This
avoids redundant network calls and keeps every consumer on the same adjusted scale.

Also provides point-in-time technicals (20EMA / 50SMA / 200SMA / ATR14 + a setup
classifier) that mirror the frontend `tradeTechnicals.js`, so the H1 report and the
dashboard Diagnosis tab tell the same story.

**Staleness.** These files are only as fresh as the last pipeline run that touched
the name, and coverage is uneven — a name that drops out of the daily universe just
stops updating, silently. Two different questions therefore need two different calls:

* *"give me history"* — `load_local_ohlc(t)`. Unguarded by default; a backtest
  reading 2024 bars does not care that the file stops in May.
* *"give me the current price"* — `latest_close(t)`, which refuses (returns None)
  when the newest bar is stale, so the caller falls through to a fresh fetch exactly
  as it does for a missing file.

Never read `load_local_ohlc(t)[-1]["close"]` as a mark. That is what inverted the
sign on a live position on 2026-08-09: PLTR's file ended 2026-05-22 at 136.88, which
against a 155.37 entry and a 153.00 stop computes to -7.8R — while the real close of
172.01 made it +7.02R, the best position on the book.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

from pipeline.marketcal import market_today

TICKERS_DIR = Path("data/output/tickers")

# Calendar days of slack for `latest_close`. Big enough to absorb a normal
# weekend plus a holiday Monday (Fri bar read the following Wed = 5 days) and a
# pipeline run that has not landed yet; small enough that a name which quietly
# stopped updating is caught within the week.
DEFAULT_MAX_AGE_DAYS = 5


def _safe(sym: str) -> str:
    return sym.upper().replace("/", "_").replace("^", "_")


def load_local_ohlc(ticker: str, min_start: Optional[str] = None,
                    tickers_dir: Path = TICKERS_DIR,
                    through: Optional[str] = None,
                    max_age_days: Optional[int] = None) -> Optional[list[dict]]:
    """Return locally-stored daily bars for `ticker`, or None if absent/too shallow/stale.

    Prefers `ohlc_2y`, falls back to `ohlc_1y`. Bars are dicts:
    {date, open, high, low, close, volume}. Every rejection returns None so the
    caller falls through to a fresh fetch exactly as it does for a missing file.

    Freshness is **opt-in** — both guards default to off, because the established
    callers (H1 report technicals, conviction sizing, case-study charts) read
    point-in-time history for closed trades and a stale tail is irrelevant to them.
    Anything computing a *current* mark must opt in, or better, call `latest_close`.

    Args:
        min_start: ISO date. Reject if the history doesn't reach back this far.
        through: ISO date. Reject unless the newest bar is on/after it. Pure — no
            clock — so use it when you already know the session you need (e.g. the
            last trading day from `pipeline.marketcal`).
        max_age_days: Reject if the newest bar is more than this many calendar days
            before today's market date. Inclusive at the boundary.
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
    if (through or max_age_days is not None) and not _reaches(bars, through, max_age_days):
        return None
    return bars


def _reaches(bars: list[dict], through: Optional[str],
             max_age_days: Optional[int]) -> bool:
    """Is the newest bar recent enough for `through` / `max_age_days`?"""
    last = bars[-1].get("date")
    if not last:
        return False
    if through and last < through:
        return False
    if max_age_days is not None:
        try:
            last_date = dt.date.fromisoformat(last[:10])
        except ValueError:
            return False                       # unparseable date == unusable
        # market_today(), never date.today(): this box runs in JST, ~13h ahead
        # of ET, so the host clock reads "tomorrow" for most of the US session.
        if (market_today() - last_date).days > max_age_days:
            return False
    return True


def latest_close(ticker: str, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
                 tickers_dir: Path = TICKERS_DIR) -> Optional[dict]:
    """The newest locally-stored bar for `ticker`, or None if absent or stale.

    Use this — not `load_local_ohlc(t)[-1]` — for anything marking a position to
    market or computing an R-multiple. Returns the whole bar rather than a bare
    float so the caller can always report *as of when*:

        bar = latest_close("PLTR")
        if bar is None:
            bar = fetch_from_network("PLTR")   # same path as a missing file
        mark, as_of = bar["close"], bar["date"]

    Widen `max_age_days` deliberately (and say so at the call site) if you really
    do want an older mark.
    """
    bars = load_local_ohlc(ticker, tickers_dir=tickers_dir, max_age_days=max_age_days)
    return bars[-1] if bars else None


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
