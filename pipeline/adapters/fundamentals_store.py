"""Fundamentals store -- the F score's source, refreshed on a rolling basis.

Why this exists (2026-08-17): `f_score` (weight 2 of 10 in `h_score`) reads
`eps_growth_next_y` and `revenue_growth`, two Finviz columns that the free
Overview page does not carry -- they had been 100% null since the HTML
scraper became the path, so the F score was a constant 50 for every row and
a dead weight in the composite. Andy: "换源,容纳后 finviz 当 backup".

Design:
  * yfinance `Ticker.info` is the PRIMARY source. It is ~0.9 s per ticker,
    so the whole universe cannot be re-read nightly; fundamentals are
    quarterly data, so they do not need to be. Each night refreshes the
    BUDGET tickers whose reading is oldest (or missing) -- the universe turns
    over in ~8 nights, after which every name is re-read about weekly.
  * The store is one JSON file, committed with the rest of `data/`, so a
    cron run inherits the previous nights' readings.
  * Finviz is the BACKUP: when a Finviz row carries a value (Elite CSV
    export), it fills only where yfinance has none. `fund_source` on the
    row says which one spoke.

Field mapping (names kept so `compute_universe_scores` is untouched):
  eps_growth_next_y  <- forwardEps / trailingEps - 1, only when trailingEps > 0
                        (Finviz's "EPS next Y" is the analyst-estimate growth;
                        a loss-making name has no meaningful growth rate and
                        Finviz prints blank/odd there too -> None)
  revenue_growth     <- revenueGrowth (yoy, latest quarter). NOTE: Finviz's
                        column was "Sales past 5Y" (5-year CAGR); this is a
                        one-year quarterly figure. Same job in the F score --
                        top-line growth -- different window; documented in
                        DATA_CONTRACTS.
  eps_growth_this_y  <- earningsGrowth (yoy)
"""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

log = logging.getLogger(__name__)

STORE = Path("data/reference/fundamentals.json")
FIELDS = ("eps_growth_next_y", "revenue_growth", "eps_growth_this_y")
import os
BUDGET = int(os.environ.get('FUNDAMENTALS_BUDGET', '700'))   # tickers refreshed per run; CI sets 400
WORKERS = 6
MAX_CONSECUTIVE_FAILURES = 40   # a throttle wall, not a run of dead symbols
# A wall is a rate limit, not a verdict: 2026-08-27 the nightly run hit one and
# gave up with partial coverage; a manual rerun 40 minutes later got 400/400.
# So the wall is TRANSIENT and worth one cooldown before conceding the night.
# One retry, not a loop: if the second pass walls too, the limit is real and
# tomorrow's queue (the victims are un-stamped, see below) is the right answer.
WALL_COOLDOWN_S = int(os.environ.get('FUNDAMENTALS_COOLDOWN', '90'))
WALL_RETRIES = 1
RETRY_WORKERS = 2               # gentler on the way back in


def map_info(info: Mapping) -> Dict[str, Optional[float]]:
    """yfinance `info` dict -> our three fields (None where undefined)."""
    def num(k):
        v = info.get(k)
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return None if f != f else f

    fwd, trail = num("forwardEps"), num("trailingEps")
    eps_next = (fwd / trail - 1.0) if (fwd is not None and trail is not None and trail > 0) else None
    return {
        "eps_growth_next_y": eps_next,
        "revenue_growth": num("revenueGrowth"),
        "eps_growth_this_y": num("earningsGrowth"),
    }


def _fetch_one(ticker: str) -> Optional[Dict[str, Optional[float]]]:
    import yfinance as yf
    info = yf.Ticker(ticker).info
    if not isinstance(info, dict) or not info:
        return None
    return map_info(info)


def load(path: Path = STORE) -> Dict[str, Dict]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        log.exception("fundamentals store unreadable -- starting empty")
        return {}


def save(store: Mapping[str, Dict], path: Path = STORE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(store.items())), indent=0, sort_keys=True))


def pick_due(store: Mapping[str, Dict], tickers: Iterable[str], budget: int = BUDGET) -> List[str]:
    """Oldest readings first, never-tried first of all; at most `budget`.
    A failed attempt counts as 'tried' so a dead symbol drifts to the back of
    the queue instead of eating the budget every night."""
    tickers = list(dict.fromkeys(t for t in tickers if isinstance(t, str) and t))

    def key(t):
        rec = store.get(t) or {}
        return max(rec.get("asof") or "", rec.get("last_attempt") or "")
    return sorted(tickers, key=key)[:budget]


def refresh(store: Dict[str, Dict], tickers: Iterable[str], *, budget: int = BUDGET,
            fetch: Callable[[str], Optional[Dict]] = _fetch_one, workers: int = WORKERS,
            asof: Optional[str] = None) -> Dict[str, int]:
    """Refresh the due tickers in place. Returns counts. Never raises for a
    single ticker; stops early on a wall of consecutive failures (throttle)."""
    asof = asof or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    due = pick_due(store, tickers, budget)
    ok = fail = 0
    walled = False
    retries_used = 0
    failed_this_run: List[str] = []
    t0 = time.time()

    def _pass(names: Sequence[str], n_workers: int) -> tuple[int, int, bool, List[str]]:
        """One sweep. Returns (ok, fail, walled, names not attempted)."""
        p_ok = p_fail = 0
        consecutive = 0
        hit_wall = False
        remaining: List[str] = []
        done_ok: set = set()
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futs = {ex.submit(fetch, t): t for t in names}
            for fut in as_completed(futs):
                t = futs[fut]
                try:
                    res = fut.result()
                except CancelledError:
                    remaining.append(t)
                    continue
                except Exception as e:  # noqa: BLE001
                    res = None
                    log.debug("fundamentals %s: %s", t, e)
                if res is None:
                    p_fail += 1
                    consecutive += 1
                    failed_this_run.append(t)
                    # keep the old reading if there is one; note the attempt
                    store.setdefault(t, {})["last_attempt"] = asof
                    if consecutive >= MAX_CONSECUTIVE_FAILURES:
                        hit_wall = True
                        log.warning("fundamentals: %d consecutive failures (rate limit wall)",
                                    consecutive)
                        # Everything not yet SUCCESSFUL is the wall's victim --
                        # both the queued names we can cancel and the ones that
                        # already came back empty because the limit was already
                        # on. Cancelling only tells us who never ran; the
                        # failures are exactly who to try again after cooling.
                        for f, ft in futs.items():
                            f.cancel()
                            if ft not in done_ok:
                                remaining.append(ft)
                        break
                    continue
                consecutive = 0
                p_ok += 1
                done_ok.add(t)
                store[t] = {**res, "asof": asof, "source": "yfinance"}
        seen: set = set()
        uniq = [t for t in remaining if not (t in seen or seen.add(t))]
        return p_ok, p_fail, hit_wall, uniq

    todo = list(due)
    workers_now = workers
    while todo:
        p_ok, p_fail, hit_wall, remaining = _pass(todo, workers_now)
        ok += p_ok
        fail += p_fail
        if not hit_wall:
            walled = False
            break
        walled = True
        if retries_used >= WALL_RETRIES or not remaining:
            break
        retries_used += 1
        log.warning("fundamentals: cooling down %ds before retry %d/%d (%d names left)",
                    WALL_COOLDOWN_S, retries_used, WALL_RETRIES, len(remaining))
        time.sleep(WALL_COOLDOWN_S)
        todo = remaining
        workers_now = RETRY_WORKERS

    if walled:
        # The failures were the wall's victims, not dead symbols: un-stamp
        # them so they stay at the front of tomorrow's queue.
        for t in failed_this_run:
            rec = store.get(t)
            if rec is None:
                continue
            rec.pop("last_attempt", None)
            if not rec:
                del store[t]
    log.info("fundamentals: refreshed %d/%d due (%d failed%s%s) in %.0fs; store %d tickers",
             ok, len(due), fail, ", rate-limited" if walled else "",
             f", {retries_used} retry" if retries_used else "", time.time() - t0, len(store))
    return {"due": len(due), "ok": ok, "failed": fail, "walled": walled,
            "retries": retries_used, "store": len(store)}


def apply(universe: pd.DataFrame, store: Mapping[str, Dict]) -> pd.DataFrame:
    """yfinance first, Finviz's own column as backup. Adds `fund_source`
    ('yfinance' | 'finviz' | None) and `fund_asof`."""
    df = universe.copy()
    for f in FIELDS:
        if f not in df.columns:
            df[f] = pd.NA
        df[f] = pd.to_numeric(df[f], errors="coerce")
    finviz_has = df[list(FIELDS)].notna().any(axis=1)

    yf_vals = {f: [] for f in FIELDS}
    asof, src = [], []
    for t, fv in zip(df["ticker"], finviz_has):
        rec = store.get(t) if isinstance(t, str) else None
        has_yf = bool(rec) and any(rec.get(f) is not None for f in FIELDS)
        for f in FIELDS:
            yf_vals[f].append(rec.get(f) if rec else None)
        asof.append(rec.get("asof") if rec else None)
        src.append("yfinance" if has_yf else ("finviz" if fv else None))
    for f in FIELDS:
        yf_col = pd.Series(yf_vals[f], index=df.index, dtype="float64")
        df[f] = yf_col.where(yf_col.notna(), df[f])
    df["fund_source"] = pd.Series(src, index=df.index, dtype=object)
    df["fund_asof"] = pd.Series(asof, index=df.index, dtype=object)
    return df
