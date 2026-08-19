"""Delayed Reaction EP -- Stockbee's second entry, from our own EP archive.

Pradeep's idea: the day a stock gaps on a real catalyst is not the entry --
day 1 tends to reverse, and by day 3-4 the market assumes the news is priced
in and the stock often drifts a little more. If it then holds inside the
EP-day range, contracts, and breaks out a SECOND time, that breakout is a
better trade than day 1: the news is digested, supply (secondaries, day-1
sellers) is cleared, and the stop sits under a tight base instead of under
the EP day's huge bar. He says the mirror works on the short side.

He gives no numeric thresholds in the sources we can read (his scan is
published as images). The rules below are ours, tunable by flag, and every
row prints the raw facts so the thresholds can be judged:

    candidate     episodic_pivot fired in data/history/ticker_events.csv
                  3..15 sessions ago (--min-days / --max-days)
    held          lowest low since the EP day >= EP-day low  (gap not filled)
    near          close within +-10% of the EP-day close (--near)
    contracting   mean (H-L)/close of the last 5 bars <= 60% of the EP-day
                  range/close (--contract)
    breakout      today's close > highest high of the post-EP bars before
                  today, close > open, rel volume >= 1  -> the second entry

    stage = 'failed'   if not held
            'breaking' if held and breakout today
            'basing'   if held and contracting (watch: entry not yet)
            'drifting' otherwise

Bars: yfinance daily (auto_adjust=False), only for the candidate set (~dozens),
so this is cheap. Nothing here is written to universe.json yet -- this is the
"let's see the list first" version.

Run:  python -m pipeline.tools.delayed_ep_scan [--as-of 2026-08-14] [--stage breaking]
      python -m pipeline.tools.delayed_ep_scan --archive          # append to the daily log
      python -m pipeline.tools.delayed_ep_scan --review           # what became of past stages

Monitoring (Andy, 2026-08-17: "design the watch, report back in a few days"):
--archive appends one row per (as-of, ticker) to data/history/delayed_ep_log.csv,
idempotent per as-of date; the cron runs it nightly. --review joins the log to
current prices and answers the questions that decide the thresholds:
  * of the names logged 'basing', how many later logged 'breaking' / 'failed'?
  * forward return from the first 'breaking' day, 5 and 10 sessions on;
  * forward return from the first 'basing' day, ditto;
  * how often 'failed' names (EP-low undercut) went on to make new highs anyway
    -- the AXTI/LIFE question: is 'held' too strict?
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd  # noqa: E402

warnings.filterwarnings("ignore")
EVENTS = Path("data/history/ticker_events.csv")
UNIVERSE = Path("data/output/universe.json")
LOG = Path("data/history/delayed_ep_log.csv")
LOG_FIELDS = ["as_of", "ticker", "ep_date", "days_since", "stage", "held", "near", "contracting",
              "breakout", "close", "vs_ep_close_pct", "ep_range_pct", "recent_range_pct",
              "base_high", "today_change_pct", "today_relvol", "ep_change", "ep_relvol"]


@dataclass
class DelayedEp:
    ticker: str
    ep_date: str
    days_since: int
    ep_change: Optional[float]
    ep_relvol: Optional[float]
    held: bool
    near: bool
    contracting: bool
    breakout: bool
    stage: str
    close: float
    vs_ep_close_pct: float
    ep_range_pct: float
    recent_range_pct: float
    base_high: float
    today_change_pct: float
    today_relvol: Optional[float]


def classify(bars: pd.DataFrame, ep_date: str, *, near: float = 0.10,
             contract: float = 0.60, ep_change=None, ep_relvol=None,
             ticker: str = "") -> Optional[DelayedEp]:
    """Pure classification over daily bars (Open/High/Low/Close/Volume,
    DatetimeIndex, oldest first). ep_date must be a bar in `bars`."""
    b = bars
    if ep_date not in set(b.index.strftime("%Y-%m-%d")):
        return None
    i_ep = list(b.index.strftime("%Y-%m-%d")).index(ep_date)
    if i_ep >= len(b) - 1:
        return None
    ep = b.iloc[i_ep]
    post = b.iloc[i_ep + 1:]            # EP+1 .. today
    today = b.iloc[-1]
    before_today = post.iloc[:-1]       # EP+1 .. yesterday
    days_since = len(post)

    held = bool(post["Low"].min() >= ep["Low"])
    vs_ep = float(today["Close"] / ep["Close"] - 1.0)
    near_ok = abs(vs_ep) <= near
    ep_range = float((ep["High"] - ep["Low"]) / ep["Close"])
    tail = b.iloc[-5:]
    recent_range = float(((tail["High"] - tail["Low"]) / tail["Close"]).mean())
    contracting = ep_range > 0 and recent_range <= contract * ep_range
    base_high = float(before_today["High"].max()) if len(before_today) else float(ep["High"])
    vol_avg = float(b["Volume"].iloc[-51:-1].mean()) if len(b) > 20 else None
    today_relvol = float(today["Volume"] / vol_avg) if vol_avg else None
    breakout = bool(today["Close"] > base_high and today["Close"] > today["Open"]
                    and (today_relvol is None or today_relvol >= 1.0))
    if not held:
        stage = "failed"
    elif breakout:
        stage = "breaking"
    elif contracting:
        stage = "basing"
    else:
        stage = "drifting"
    prev_close = float(b["Close"].iloc[-2])
    return DelayedEp(ticker, ep_date, days_since, ep_change, ep_relvol, held, near_ok,
                     contracting, breakout, stage, float(today["Close"]), vs_ep, ep_range,
                     recent_range, base_high, float(today["Close"] / prev_close - 1.0), today_relvol)


def load_candidates(as_of: str, min_days: int, max_days: int) -> dict:
    """ticker -> latest EP row within the window (trading-day distance is
    settled later on real bars; here a calendar pre-filter of 3x the window)."""
    out = {}
    lo = (pd.Timestamp(as_of) - pd.Timedelta(days=max_days * 3)).strftime("%Y-%m-%d")
    for r in csv.DictReader(EVENTS.open()):
        if r["screener"] != "episodic_pivot" or not (lo <= r["date"] <= as_of):
            continue
        t = r["ticker"]
        if t not in out or r["date"] > out[t]["date"]:
            out[t] = r
    return out


def archive(rows, as_of: str, path: Path = LOG) -> int:
    """Append today's rows; replace any existing rows for the same as-of."""
    import csv as _csv
    old = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in _csv.DictReader(fh) if r.get("as_of") != as_of]
    new = [{"as_of": as_of, **{k: getattr(d, k) for k in LOG_FIELDS if k != "as_of"}} for d in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        w.writeheader()
        for r in [*old, *new]:
            w.writerow({k: r.get(k, "") for k in LOG_FIELDS})
    return len(new)


def review(path: Path = LOG, horizons=(5, 10)) -> None:
    """What became of past stages. Reads the log, pulls current bars for the
    tickers in it, prints transition counts and forward returns."""
    import csv as _csv
    import yfinance as yf
    if not path.exists():
        print("no log yet"); return
    with path.open(newline="") as fh:
        log = list(_csv.DictReader(fh))
    if not log:
        print("empty log"); return
    dates = sorted({r["as_of"] for r in log})
    print(f"log: {len(log)} rows, {len(dates)} sessions ({dates[0]} .. {dates[-1]}), "
          f"{len({r['ticker'] for r in log})} tickers")
    # stage transitions per ticker
    by_t = {}
    for r in sorted(log, key=lambda r: (r["ticker"], r["as_of"])):
        by_t.setdefault(r["ticker"], []).append(r)
    trans = {}
    first_stage_day = {}
    for t, rs in by_t.items():
        seq = [r["stage"] for r in rs]
        for a, b in zip(seq, seq[1:]):
            if a != b:
                trans[(a, b)] = trans.get((a, b), 0) + 1
        for r in rs:
            first_stage_day.setdefault((t, r["stage"]), r)
    print("\nstage transitions (from -> to: count):")
    for (a, b), n in sorted(trans.items(), key=lambda x: -x[1]):
        print(f"  {a:>9} -> {b:<9} {n}")
    # forward returns from first 'breaking' / 'basing' / 'failed' day
    tickers = sorted(by_t)
    data = yf.download(tickers, period="90d", interval="1d", group_by="ticker",
                       auto_adjust=False, progress=False, threads=True)
    def close_on_or_after(t, d, k):
        try:
            s = (data[t]["Close"] if len(tickers) > 1 else data["Close"]).dropna()
        except KeyError:
            return None
        s = s[s.index >= pd.Timestamp(d)]
        return float(s.iloc[k]) if len(s) > k else None
    print("\nforward return from the FIRST day a name was logged in a stage "
          "(median / n; needs that many later sessions):")
    for stage in ("breaking", "basing", "failed"):
        for h in horizons:
            rets = []
            for (t, st), r in first_stage_day.items():
                if st != stage:
                    continue
                c0 = float(r["close"]); ck = close_on_or_after(t, r["as_of"], h)
                if ck:
                    rets.append(ck / c0 - 1)
            if rets:
                rets.sort()
                print(f"  {stage:>9} +{h:>2}d: median {rets[len(rets)//2]*100:+.1f}%  "
                      f"n={len(rets)}  >0: {sum(1 for x in rets if x > 0)/len(rets)*100:.0f}%")
            else:
                print(f"  {stage:>9} +{h:>2}d: (not enough sessions yet)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", action="store_true", help="append today's rows to the log")
    ap.add_argument("--review", action="store_true", help="what became of past stages")
    ap.add_argument("--quiet-print", action="store_true", help="only the summary line")
    ap.add_argument("--as-of", default=None, help="last session (default: newest bar)")
    ap.add_argument("--min-days", type=int, default=3)
    ap.add_argument("--max-days", type=int, default=15)
    ap.add_argument("--near", type=float, default=0.10)
    ap.add_argument("--contract", type=float, default=0.60)
    ap.add_argument("--stage", default=None, help="only print this stage")
    a = ap.parse_args()
    if a.review:
        review(); return
    import yfinance as yf
    from pipeline.marketcal import last_completed_session
    as_of = a.as_of or last_completed_session().strftime("%Y-%m-%d")
    cands = load_candidates(as_of, a.min_days, a.max_days)
    tickers = sorted(cands)
    print(f"EP firings in window: {len(tickers)} tickers (as of {as_of})")
    if not tickers:
        return
    # 2026-08-18: the cron step printed "77 tickers ... 0 in the window" and
    # archived nothing -- Yahoo throttled the one batch download at 22:00 UTC
    # and every frame came back empty. Retry with a pause, like the universe
    # sweep does, and say loudly when the night is lost rather than filing
    # silence as "no candidates".
    import time
    frames = {}
    for attempt in range(4):
        missing = [t for t in tickers if t not in frames]
        if not missing:
            break
        if attempt:
            time.sleep(20 * attempt)
        data = yf.download(missing, period="120d", interval="1d", group_by="ticker",
                           auto_adjust=False, progress=False, threads=True)
        for t in missing:
            try:
                df = data[t].dropna(subset=["Close"]) if len(missing) > 1 else data.dropna(subset=["Close"])
            except KeyError:
                continue
            if len(df):
                frames[t] = df
    got = len(frames)
    if got < 0.5 * len(tickers):
        print(f"ERROR delayed_ep: bars for only {got}/{len(tickers)} candidates after 4 rounds "
              f"(Yahoo throttle?) -- not archiving a half-empty session", file=sys.stderr)
        if a.archive:
            return
    uni = {r["ticker"]: r for r in json.loads(UNIVERSE.read_text())["rows"]}
    rows = []
    for t in tickers:
        df = frames.get(t)
        if df is None:
            continue
        df = df[df.index <= pd.Timestamp(as_of)]
        if len(df) < 25:
            continue
        r = cands[t]
        d = classify(df, r["date"], near=a.near, contract=a.contract,
                     ep_change=float(r["change_pct"]) if r.get("change_pct") else None,
                     ep_relvol=float(r["rel_volume"]) if r.get("rel_volume") else None, ticker=t)
        if d is None or not (a.min_days <= d.days_since <= a.max_days):
            continue
        rows.append(d)

    order = {"breaking": 0, "basing": 1, "drifting": 2, "failed": 3}
    rows.sort(key=lambda d: (order[d.stage], d.days_since))
    if a.stage:
        rows = [d for d in rows if d.stage == a.stage]
    print(f"{len(rows)} in the {a.min_days}-{a.max_days} session window\n")
    if a.archive:
        n = archive(rows, as_of)
        print(f"archived {n} rows for {as_of} -> {LOG}")
    if a.quiet_print:
        return
    print(f"{'stage':<9}{'tk':<6}{'EP date':<11}{'d':>3}{'EPchg':>7}{'EPrv':>6}{'vsEP%':>7}"
          f"{'EPrng%':>7}{'5drng%':>7}{'held':>5}{'todaychg':>9}{'rv':>5}{'vcs':>5}{'rs21':>5}{'mcap':>6}")
    for d in rows:
        u = uni.get(d.ticker, {})
        print(f"{d.stage:<9}{d.ticker:<6}{d.ep_date:<11}{d.days_since:>3}"
              f"{(d.ep_change or 0)*100:>7.1f}{(d.ep_relvol or 0):>6.1f}{d.vs_ep_close_pct*100:>7.1f}"
              f"{d.ep_range_pct*100:>7.1f}{d.recent_range_pct*100:>7.1f}{'y' if d.held else 'n':>5}"
              f"{d.today_change_pct*100:>9.1f}{(d.today_relvol or 0):>5.1f}"
              f"{(u.get('vcs') if u.get('vcs') is not None else float('nan')):>5.0f}"
              f"{(u.get('rs_21d') if u.get('rs_21d') is not None else float('nan')):>5.0f}"
              f"{(u.get('market_cap') or 0)/1e9:>6.1f}")


if __name__ == "__main__":
    main()
