"""News & Events 候选池 -- three buckets for the Market State card.

**What it is.** A candidate pool, not the pick. Claire cross-checks it against
the daily recap and the X watch and chooses the five to eight that go on the
page (T-1003-84). This module only lists who was eligible and why.

Buckets (one row per ticker per bucket):

- ``leader``: RS 前段（``rs_rating >= 90``）且收在 50 日线上，按当天涨幅取前 10。
  Proxy, not the Leaders table: that table is already ten names, so ranking it
  by change would change nothing. ``rs_rating`` NaN is excluded, not ranked low.
- ``ep``: ``ep_stockbee`` 与 ``ep_qullamaggie`` 当天名单（两位作者各自的配方，
  不合并判断）。
- ``news_failure``: 利好（财报 EPS 实际高于预期）但当天反应弱（涨幅 <= +1%）。
  只做财报这一版：非财报利好标题判不了，不放（不用 AI 给标题打情绪分）。

**Headlines.** Finnhub ``company-news``，取前一交易日 16:00 ET 到当天 16:00 ET
之间最新一条；只存标题、链接、来源，不存正文（仓库是公开的）。
No ``FINNHUB_API_KEY`` → headline / earnings fields are ``null`` and listed in
``unmeasured``; the price-based buckets still ship.

**Session dating.** ``session`` = the completed session. An earnings event is a
reaction on that session when it is dated ``session`` (before the open / during
the day) or dated the prior session with ``hour == 'amc'`` (after the close).
"""

from __future__ import annotations

import datetime as dt
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
from zoneinfo import ZoneInfo

import requests

from pipeline.marketcal import last_completed_session, last_trading_day

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
FINNHUB = "https://finnhub.io/api/v1"

# Proxy thresholds, see module docstring and DATA_CONTRACTS §七 (2026-10-03).
LEADER_MIN_RS = 90
LEADER_N = 10
NEWS_FAILURE_MAX_CHANGE = 0.01  # decimal fraction, +1 %

BUCKETS = ("leader", "ep", "news_failure")
DEFINITION = (
    "leader = rs_rating>=90 & sma50_dist>0, top10 by change_pct (proxy for the Leaders table); "
    "ep = ep_stockbee + ep_qullamaggie; "
    "news_failure = Finnhub EPS actual>estimate on the reaction session & change_pct<=+1% "
    "(earnings-only; non-earnings good news is not judged)"
)
UNMEASURED_NO_KEY = [
    "headline/url/source/published_at (FINNHUB_API_KEY not set)",
    "earnings/eps_surprise_pct (FINNHUB_API_KEY not set)",
]


def _f(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if v != v else v  # NaN -> None


def leader_tickers(rows: Iterable[Mapping[str, Any]], n: int = LEADER_N) -> List[str]:
    """Top ``n`` by change among RS-leading names still above the 50 SMA."""
    pool = []
    for r in rows:
        rs, sma50, chg = _f(r.get("rs_rating")), _f(r.get("sma50_dist")), _f(r.get("change_pct"))
        if rs is None or sma50 is None or chg is None:
            continue
        if rs >= LEADER_MIN_RS and sma50 > 0:
            pool.append((-chg, str(r["ticker"]).upper()))
    return [t for _, t in sorted(pool)[:n]]


def ep_tickers(ep_stockbee: Mapping[str, Any], ep_qullamaggie: Mapping[str, Any]) -> List[str]:
    seen: Dict[str, None] = {}
    for src in (ep_stockbee, ep_qullamaggie):
        for r in (src or {}).get("tickers", []) or []:
            seen.setdefault(str(r["ticker"]).upper(), None)
    return list(seen)


class FinnhubClient:
    def __init__(self, key: str, timeout: int = 15):
        self.key = key
        self.timeout = timeout

    def _get(self, path: str, params: Dict[str, Any]) -> Any:
        r = requests.get(f"{FINNHUB}/{path}", params={**params, "token": self.key}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def earnings_calendar(self, start: dt.date, end: dt.date) -> List[Dict[str, Any]]:
        data = self._get("calendar/earnings", {"from": start.isoformat(), "to": end.isoformat()})
        return data.get("earningsCalendar") or []

    def company_news(self, symbol: str, start: dt.date, end: dt.date) -> List[Dict[str, Any]]:
        return self._get("company-news", {"symbol": symbol, "from": start.isoformat(), "to": end.isoformat()}) or []


def reaction_earnings(events: Iterable[Mapping[str, Any]], session: dt.date, prior: dt.date) -> Dict[str, Dict[str, Any]]:
    """Map ticker -> earnings event whose reaction lands on ``session``."""
    out: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        sym = ev.get("symbol")
        if not sym:
            continue
        d = str(ev.get("date") or "")
        hour = str(ev.get("hour") or "")
        if d == session.isoformat() or (d == prior.isoformat() and hour == "amc"):
            out.setdefault(str(sym).upper(), dict(ev))
    return out


def eps_surprise_pct(ev: Mapping[str, Any]) -> Optional[float]:
    actual, est = _f(ev.get("epsActual")), _f(ev.get("epsEstimate"))
    if actual is None or est is None or est == 0:
        return None
    return round((actual - est) / abs(est) * 100, 2)


def latest_headline(items: Iterable[Mapping[str, Any]], start_ts: float, end_ts: float) -> Optional[Dict[str, Any]]:
    """Newest item inside [start_ts, end_ts]; only title, link and source kept."""
    best = None
    for it in items:
        ts = _f(it.get("datetime"))
        if ts is None or not (start_ts <= ts <= end_ts):
            continue
        if best is None or ts > best[0]:
            best = (ts, it)
    if best is None:
        return None
    ts, it = best
    return {
        "headline": (it.get("headline") or "").strip() or None,
        "url": it.get("url") or None,
        "source": it.get("source") or None,
        "published_at": dt.datetime.fromtimestamp(ts, ET).isoformat(),
    }


def build(
    rows: List[Mapping[str, Any]],
    ep_stockbee: Mapping[str, Any],
    ep_qullamaggie: Mapping[str, Any],
    key: Optional[str] = None,
    session: Optional[dt.date] = None,
) -> Dict[str, Any]:
    session = session or last_completed_session()
    prior = last_trading_day(session - dt.timedelta(days=1))
    by_t = {str(r["ticker"]).upper(): r for r in rows}
    start_ts = dt.datetime.combine(prior, dt.time(16, 0), ET).timestamp()
    end_ts = dt.datetime.combine(session, dt.time(16, 0), ET).timestamp()

    client = FinnhubClient(key) if key else None
    earn: Dict[str, Dict[str, Any]] = {}
    earn_error = None
    if client:
        try:
            earn = reaction_earnings(client.earnings_calendar(prior, session), session, prior)
        except Exception as e:  # noqa: BLE001 — isolate; price buckets still ship
            earn_error = repr(e)
            logger.warning("news_pool: earnings calendar failed: %s", e)

    # (ticker, bucket) candidates, deduped per bucket.
    cands: List[Tuple[str, str]] = []
    cands += [(t, "leader") for t in leader_tickers(rows)]
    cands += [(t, "ep") for t in ep_tickers(ep_stockbee, ep_qullamaggie) if t in by_t]
    nf = []
    for sym, ev in earn.items():
        r = by_t.get(sym)
        chg = _f(r.get("change_pct")) if r else None
        surprise = eps_surprise_pct(ev)
        if chg is None or surprise is None or surprise <= 0 or chg > NEWS_FAILURE_MAX_CHANGE:
            continue
        nf.append(sym)
    cands += [(t, "news_failure") for t in sorted(nf)]

    def _enrich(tb: Tuple[str, str]) -> Dict[str, Any]:
        t, bucket = tb
        r = by_t[t]
        row = {
            "ticker": t,
            "bucket": bucket,
            "change_pct": _f(r.get("change_pct")),
            "rel_volume": _f(r.get("rel_volume")),
            "headline": None, "url": None, "source": None, "published_at": None,
            "earnings": None, "eps_surprise_pct": None,
        }
        if client is None:
            return row
        ev = earn.get(t)
        row["earnings"] = bool(ev) if earn_error is None else None
        row["eps_surprise_pct"] = eps_surprise_pct(ev) if ev else None
        try:
            hit = latest_headline(client.company_news(t, prior, session), start_ts, end_ts)
        except Exception as e:  # noqa: BLE001
            logger.warning("news_pool: company-news %s failed: %s", t, e)
            hit = None
        if hit:
            row.update(hit)
        return row

    with ThreadPoolExecutor(max_workers=4) as pool:
        tickers = list(pool.map(_enrich, cands))

    counts = {b: sum(1 for x in tickers if x["bucket"] == b) for b in BUCKETS}
    unmeasured = [] if client else list(UNMEASURED_NO_KEY)
    if earn_error:
        unmeasured.append(f"earnings/eps_surprise_pct (calendar call failed: {earn_error})")
    out: Dict[str, Any] = {
        "session": session.isoformat(),
        "prior_session": prior.isoformat(),
        "window_et": [f"{prior.isoformat()} 16:00", f"{session.isoformat()} 16:00"],
        "count": len(tickers),
        "bucket_counts": counts,
        "tickers": tickers,
        "definition": DEFINITION,
        "unmeasured": unmeasured,
    }
    if counts["news_failure"] == 0:
        out["news_failure_note"] = (
            "0: no eligible earnings beat with reaction <= +1%"
            if client and earn_error is None
            else "0: earnings calendar not measured this run"
        )
    return out
