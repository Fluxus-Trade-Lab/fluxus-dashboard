"""News & Events candidate pool -> data/output/news_pool.json (T-1003-83).

Three buckets, one row per (ticker, bucket). This file only lists candidates;
the pick of 5-8 names happens on the local machine (T-1003-84), not here.

  leader        Liquid Leaders: universe `liquid_leader` (ADV >= 2M, above
                SMA50, rs_3m >= 80 -- the watchlist panel's own predicate),
                top 10 by change_pct.
  ep            Episodic Pivots: union of ep_stockbee + ep_qullamaggie.
  news_failure  Good news, weak tape. Earnings beat (Finnhub earnings calendar:
                epsActual > epsEstimate) while the stock closed flat or down
                (change_pct <= +1%). Only the machine-checkable version; a
                non-earnings headline is never classed as "good news" here.

Units: change_pct is the fraction c/c1 - 1, as in universe.json and the EP
files (0.01 = +1%).

Headline and link come from Finnhub company-news: the latest item between the
previous session's 16:00 ET and the session's 16:00 ET. Titles and links only,
never article bodies -- the repository is public.
"""

from __future__ import annotations

import datetime as dt
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

import requests

from pipeline.marketcal import MARKET_CLOSE, last_trading_day
from pipeline.screeners.universe_gate import MIN_MARKET_CAP

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
FINNHUB = "https://finnhub.io/api/v1"
TOP_N = 10
NEWS_FAILURE_MAX_CHANGE = 0.01   # "当天涨幅不大，甚至跌": c/c1 - 1 <= +1%

DEFINITIONS = {
    "leader": "Liquid Leaders (ADV>=2M, >SMA50, rs_3m>=80; course M2_L09), top 10 by change_pct",
    "ep": "Episodic Pivots: Stockbee c/c1>1.04 & v>3*avgv50.1 & v>=300k; Qullamaggie gap>=10% & vol>=1 ADV",
    "news_failure": ("自造口径（机器可判的一版）：Finnhub 财报日历 epsActual > epsEstimate，"
                     "且当天 change_pct <= +1%。非财报的利好标题不判、不入池。"),
}
UNMEASURED = ("news_failure 只覆盖财报 beat；非财报利好（合同、评级、并购）判不了，不入池。"
              "headline 为窗口内 Finnhub 最新一条，可能不是最相关的一条。")


def _f(v: Any) -> Optional[float]:
    if v is None or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


def _round(x: Optional[float], nd: int) -> Optional[float]:
    return None if x is None else round(x, nd)


def _row(base: Mapping[str, Any], bucket: str) -> Dict[str, Any]:
    return {
        "ticker": str(base["ticker"]).upper(),
        "bucket": bucket,
        "change_pct": _round(_f(base.get("change_pct")), 6),
        "rel_volume": _round(_f(base.get("rel_volume")), 4),
        "headline": None,
        "url": None,
        "source": None,
        "published_at": None,
        "earnings": False,
        "eps_surprise_pct": None,
    }


def leaders(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    pool = [r for r in rows
            if r.get("liquid_leader") is True and _f(r.get("change_pct")) is not None]
    pool.sort(key=lambda r: (-_f(r["change_pct"]), r["ticker"]))
    return [_row(r, "leader") for r in pool[:TOP_N]]


def episodic(stockbee: Optional[Mapping[str, Any]],
             qullamaggie: Optional[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """One row per ticker; `ep_by` says which author(s) flagged it."""
    seen: Dict[str, Dict[str, Any]] = {}
    for name, doc in (("stockbee", stockbee), ("qullamaggie", qullamaggie)):
        for r in (doc or {}).get("tickers") or []:
            t = str(r["ticker"]).upper()
            if t not in seen:
                seen[t] = {**_row(r, "ep"), "ep_by": []}
            seen[t]["ep_by"].append(name)
    out = list(seen.values())
    out.sort(key=lambda r: (-(r["change_pct"] or float("-inf")), r["ticker"]))
    return out


def earnings_beats(events: Sequence[Mapping[str, Any]],
                   rows_by_t: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """news_failure candidates from the Finnhub earnings calendar events."""
    out = []
    for ev in events:
        t = str(ev.get("symbol") or "").upper()
        base = rows_by_t.get(t)
        actual, est = _f(ev.get("epsActual")), _f(ev.get("epsEstimate"))
        if not base or actual is None or est is None or actual <= est:
            continue
        cap = _f(base.get("market_cap"))
        change = _f(base.get("change_pct"))
        if cap is None or cap < MIN_MARKET_CAP or change is None or change > NEWS_FAILURE_MAX_CHANGE:
            continue
        surprise = (actual - est) / abs(est) * 100 if est else None
        out.append({**_row(base, "news_failure"), "earnings": True,
                    "eps_surprise_pct": None if surprise is None else round(surprise, 2)})
    out.sort(key=lambda r: (r["change_pct"], r["ticker"]))
    return out


def earnings_calendar(start: dt.date, end: dt.date, key: str) -> List[Dict[str, Any]]:
    """Finnhub earnings calendar, start..end inclusive. Raises on transport error."""
    r = requests.get(f"{FINNHUB}/calendar/earnings",
                     params={"from": start.isoformat(), "to": end.isoformat(), "token": key},
                     timeout=15)
    r.raise_for_status()
    return list((r.json() or {}).get("earningsCalendar") or [])


def latest_news(ticker: str, start: dt.datetime, end: dt.datetime,
                key: str) -> Optional[Dict[str, Any]]:
    """Latest company-news item whose timestamp falls inside [start, end]."""
    r = requests.get(f"{FINNHUB}/company-news",
                     params={"symbol": ticker, "from": start.date().isoformat(),
                             "to": end.date().isoformat(), "token": key},
                     timeout=10)
    if not r.ok:
        return None
    lo, hi = start.timestamp(), end.timestamp()
    items = [i for i in (r.json() or [])
             if i.get("headline") and i.get("url") and lo <= (i.get("datetime") or 0) <= hi]
    if not items:
        return None
    best = max(items, key=lambda i: i["datetime"])
    return {"headline": best["headline"], "url": best["url"], "source": best.get("source"),
            "published_at": dt.datetime.fromtimestamp(best["datetime"], dt.timezone.utc).isoformat()}


def build(session: dt.date,
          universe_rows: Optional[Sequence[Mapping[str, Any]]],
          ep_stockbee: Optional[Mapping[str, Any]],
          ep_qullamaggie: Optional[Mapping[str, Any]],
          *,
          key: Optional[str] = None,
          fetch_calendar: Callable[..., List[Dict[str, Any]]] = earnings_calendar,
          fetch_news: Callable[..., Optional[Dict[str, Any]]] = latest_news,
          timestamp: Optional[str] = None) -> Dict[str, Any]:
    prev = last_trading_day(session - dt.timedelta(days=1))
    start = dt.datetime.combine(prev, MARKET_CLOSE, tzinfo=ET)
    end = dt.datetime.combine(session, MARKET_CLOSE, tzinfo=ET)
    rows = [r for r in universe_rows or [] if r.get("ticker")]
    rows_by_t = {str(r["ticker"]).upper(): r for r in rows}

    finnhub, events = "no_key", []
    if key:
        finnhub = "ok"
        try:
            events = fetch_calendar(prev, session, key)
        except Exception:  # noqa: BLE001 -- the pool still ships leader + ep
            logger.exception("Finnhub earnings calendar failed; news_failure bucket empty")
            finnhub = "failed"

    # One calendar event per symbol (the first one returned).
    cal: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        s = str(ev.get("symbol") or "").upper()
        if s and s not in cal:
            cal[s] = ev

    beats = earnings_beats(list(cal.values()), rows_by_t)
    out = leaders(rows) + episodic(ep_stockbee, ep_qullamaggie) + beats

    # Earnings flag and surprise ride on every row whose ticker reported.
    for r in out:
        ev = cal.get(r["ticker"])
        if ev is not None:
            r["earnings"] = True
            if r["eps_surprise_pct"] is None:
                a, e = _f(ev.get("epsActual")), _f(ev.get("epsEstimate"))
                if a is not None and e:
                    r["eps_surprise_pct"] = round((a - e) / abs(e) * 100, 2)

    # Headline and link for every candidate, one lookup per ticker.
    if key and out:
        tickers = sorted({r["ticker"] for r in out})

        def _safe(t: str) -> Optional[Dict[str, Any]]:
            try:
                return fetch_news(t, start, end, key)
            except Exception:  # noqa: BLE001
                logger.warning("company-news failed for %s", t)
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            news = dict(zip(tickers, pool.map(_safe, tickers)))
        for r in out:
            n = news.get(r["ticker"])
            if n:
                r.update(n)

    counts = {b: sum(1 for r in out if r["bucket"] == b) for b in ("leader", "ep", "news_failure")}
    zero_reason = None
    if counts["news_failure"] == 0:
        if finnhub == "no_key":
            zero_reason = "未设 FINNHUB_API_KEY，财报读数不可得"
        elif finnhub == "failed":
            zero_reason = "Finnhub 财报日历调用失败，本班无财报读数"
        elif not cal:
            zero_reason = f"{prev}–{session} 财报日历为空"
        else:
            zero_reason = (f"{prev}–{session} 日历内 {len(cal)} 只有财报，"
                           "无一只同时满足 EPS 超预期且当天涨幅 ≤ +1%")

    return {
        "timestamp": timestamp or dt.datetime.now(dt.timezone.utc).isoformat(),
        "as_of": session.isoformat(),
        "window": {"from": start.isoformat(), "to": end.isoformat()},
        "finnhub": finnhub,
        "counts": counts,
        "news_failure_zero_reason": zero_reason,
        "definitions": DEFINITIONS,
        "unmeasured": UNMEASURED,
        "tickers": out,
    }
