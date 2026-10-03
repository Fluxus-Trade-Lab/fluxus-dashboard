"""Backfill news_pool for past sessions (T-1003-83 follow-up).

Andy 2026-10-04: asked whether past sessions could be filled in; chose 「选A」 --
a one-off GitHub job that uses the FINNHUB_API_KEY already stored there, so the
key never leaves GitHub (.github/workflows/news-pool-backfill.yml).

For each session in [--start, --end]:
  1. Find the last commit on the current branch whose data/output/universe.json
     was produced for that session (its `timestamp`, read through
     marketcal.last_completed_session, names the session).
  2. Read universe.json, ep_stockbee.json, ep_qullamaggie.json AT THAT COMMIT --
     the lists exactly as the page showed them that night.
  3. Run news_pool.build() for that session with the Finnhub key: the earnings
     calendar and company-news endpoints take past dates.
  4. Write data/history/news_pool/<session>.json.

Sessions with no matching commit are skipped and listed. Sessions before the
EP files existed (2026-09-18), or whose EP files came from another run, keep
leader + news_failure and carry `backfill.ep_unmeasured` -- an empty ep bucket
there means "not measured", never "no EP that day".

Finnhub's free tier allows 60 calls/minute; every request goes through a
throttle (>= 1.1 s apart) and a 429 is retried, because news_pool.latest_news
treats any non-OK reply as "no headline" and a rate limit would otherwise read
as a quiet news day.

Only headline, link, source and time are stored (the repo is public).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from pipeline.marketcal import is_trading_day, last_completed_session
from pipeline.screeners import news_pool as NP

OUT_DIR = Path("data/history/news_pool")
UNIVERSE = "data/output/universe.json"
EP_FILES = ("data/output/ep_stockbee.json", "data/output/ep_qullamaggie.json")


class _Throttled:
    """Stand-in for the `requests` module inside news_pool: one call per
    MIN_GAP seconds across threads, 429 retried."""
    MIN_GAP = 1.1

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last = 0.0
        self.calls = 0
        self.rate_limited = 0

    def get(self, url, **kw):
        for attempt in range(5):
            with self._lock:
                wait = self._last + self.MIN_GAP - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                self._last = time.monotonic()
                self.calls += 1
            r = requests.get(url, **kw)
            if r.status_code != 429:
                return r
            self.rate_limited += 1
            time.sleep(10 * (attempt + 1))
        return r


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def _show(sha: str, path: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(_git("show", f"{sha}:{path}"))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def _session_of(ts: Optional[str]) -> Optional[dt.date]:
    if not ts:
        return None
    try:
        return last_completed_session(dt.datetime.fromisoformat(ts))
    except ValueError:
        return None


def commits_by_session(since: dt.date) -> Dict[dt.date, str]:
    """session -> newest commit whose universe.json is that session's."""
    log = _git("log", "--format=%H", f"--since={(since - dt.timedelta(days=3)).isoformat()}",
               "--", UNIVERSE).split()
    out: Dict[dt.date, str] = {}
    for sha in log:                                   # newest first
        u = _show(sha, UNIVERSE)
        s = _session_of((u or {}).get("timestamp"))
        if s and s not in out:
            out[s] = sha
    return out


def sessions(start: dt.date, end: dt.date) -> List[dt.date]:
    d, out = start, []
    while d <= end:
        if is_trading_day(d):
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--key", default=None, help="defaults to $FINNHUB_API_KEY")
    a = ap.parse_args(argv)
    import os
    key = a.key or os.environ.get("FINNHUB_API_KEY")
    if not key:
        print("FINNHUB_API_KEY not set -- nothing to backfill", file=sys.stderr)
        return 2

    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    shim = _Throttled()
    NP.requests = shim                                # news_pool's calls go through the throttle
    by_session = commits_by_session(start)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done, skipped = [], []
    for s in sessions(start, end):
        sha = by_session.get(s)
        if not sha:
            skipped.append((s, "no universe.json commit for this session"))
            continue
        u = _show(sha, UNIVERSE)
        eps = [_show(sha, p) for p in EP_FILES]
        ep_note = None
        if all(e is None for e in eps):
            ep_note = "EP 名单当时还没有发布（ep_stockbee/ep_qullamaggie 自 2026-09-18 起），本日 ep 类空缺，不是零"
        elif any(e is None or _session_of(e.get("timestamp")) != s for e in eps):
            ep_note = f"{sha[:9]} 上的 EP 文件不是本场次的，本日 ep 类空缺，不是零"
        if ep_note:
            eps = [None, None]
        pool = NP.build(s, u.get("rows"), eps[0], eps[1], key=key)
        pool["backfill"] = {"source_commit": sha, "ep_unmeasured": ep_note,
                            "built_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        (OUT_DIR / f"{s.isoformat()}.json").write_text(json.dumps(pool, indent=1, ensure_ascii=False))
        heads = sum(1 for r in pool["tickers"] if r.get("headline"))
        done.append(s)
        print(f"{s} {sha[:9]} {pool['counts']} headlines {heads}/{len(pool['tickers'])} finnhub={pool['finnhub']}")
    print(f"\nwritten {len(done)} sessions · Finnhub calls {shim.calls} · 429s retried {shim.rate_limited}")
    for s, why in skipped:
        print(f"skipped {s}: {why}")
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
