"""Daily closes for research pulls, with the alignment check that was missing.

2026-09-23: a theme experiment pulled bars while yfinance was still returning
`Close = NaN` for SPY's 2026-09-22 row. The script dropped that row and carried
on, so every window was one session stale -- and the four-state agreement it
measured read 49% instead of 68%. The data source was not the defect; the
missing check was. Andy same day: 「需不需要备用的数据源比如finviz」 -> the
nightly pipeline already had 09-22 (5,437 of 5,604 rows), so production needs
no new source; research pulls need (a) a hard check and (b) a fallback.

Two layers, on purpose:
  * pure functions (`align_report`, `merge_series`) -- tested, no network;
  * fetchers (`yfinance_closes`, `stooq_closes`) -- thin, network, untested.

Production (`pipeline/screeners/run_all.py`) does NOT use this module. It keeps
Finviz for the universe snapshot and yfinance for bars; adding a source there
would need its own week of comparison first (Andy 2026-09-23 agreed to keep it
out of production for now).
"""
from __future__ import annotations

import io
import logging
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import pandas as pd

logger = logging.getLogger(__name__)

STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"


def align_report(series: Mapping[str, pd.Series], through: str) -> Dict[str, List[str]]:
    """Which symbols end on `through`, which end early, which are empty.

    `through` is a trading date (YYYY-MM-DD), normally the session the study is
    about. A symbol whose last bar is AFTER it is 'ahead' -- that happens when a
    feed publishes an unfinished session, and it is just as wrong as a stale one.
    """
    ok, stale, ahead, empty = [], [], [], []
    for sym, s in series.items():
        if s is None or len(s) == 0:
            empty.append(sym)
            continue
        last = str(pd.Timestamp(s.index[-1]).date())
        (ok if last == through else stale if last < through else ahead).append(sym)
    return {"ok": sorted(ok), "stale": sorted(stale), "ahead": sorted(ahead),
            "empty": sorted(empty)}


def require_through(series: Mapping[str, pd.Series], through: str,
                    must: Sequence[str] = ()) -> Dict[str, List[str]]:
    """Raise unless every symbol in `must` ends exactly on `through`.

    `must` is for the symbols a study cannot be honest without -- the benchmark
    above all: a stale SPY shifts every excess in the study, not one row of it.
    """
    report = align_report(series, through)
    bad = [s for s in must if s not in report["ok"]]
    if bad:
        raise ValueError(
            f"bars are not aligned to {through}: {bad} "
            f"(stale={[s for s in bad if s in report['stale']]}, "
            f"ahead={[s for s in bad if s in report['ahead']]}, "
            f"empty={[s for s in bad if s in report['empty']]}). "
            "Fix the pull before computing anything -- a one-session shift is "
            "worth ~19 points of agreement on the 2026-09-22 theme study.")
    return report


def merge_series(primary: Mapping[str, pd.Series],
                 fallback: Mapping[str, pd.Series],
                 through: str) -> Dict[str, pd.Series]:
    """Take the fallback's series for any symbol the primary left short of `through`."""
    out = dict(primary)
    report = align_report(primary, through)
    for sym in report["stale"] + report["empty"]:
        alt = fallback.get(sym)
        if alt is None or len(alt) == 0:
            continue
        if str(pd.Timestamp(alt.index[-1]).date()) >= through:
            out[sym] = alt[alt.index <= pd.Timestamp(through)]
    return out


# ── fetchers (network; kept thin so the logic above stays testable) ──────────

def yfinance_closes(tickers: Iterable[str], period: str = "6mo") -> Dict[str, pd.Series]:
    import yfinance as yf
    tickers = list(tickers)
    out: Dict[str, pd.Series] = {}
    for i in range(0, len(tickers), 100):
        batch = tickers[i:i + 100]
        data = yf.download(batch, period=period, group_by="ticker",
                           progress=False, threads=True)
        for t in batch:
            try:
                frame = data[t] if len(batch) > 1 else data
                close = frame["Close"].dropna()
            except Exception:
                continue
            if len(close):
                out[t] = close
    return out


def stooq_closes(tickers: Iterable[str], suffix: str = ".us") -> Dict[str, pd.Series]:
    """Stooq's free daily CSV -- the fallback. US tickers take a `.us` suffix."""
    import requests
    out: Dict[str, pd.Series] = {}
    for t in tickers:
        sym = f"{t.lower().replace('.', '-')}{suffix}"
        try:
            text = requests.get(STOOQ_URL.format(symbol=sym), timeout=20).text
            frame = pd.read_csv(io.StringIO(text), parse_dates=["Date"])
            if "Close" not in frame:
                continue
            out[t] = frame.set_index("Date")["Close"].dropna()
        except Exception as exc:
            logger.debug("stooq %s failed: %s", t, exc)
    return out


def daily_closes(tickers: Sequence[str], through: str, must: Sequence[str] = (),
                 period: str = "6mo") -> Dict[str, pd.Series]:
    """yfinance first, Stooq for whatever it left stale, then the hard check."""
    primary = yfinance_closes(tickers, period=period)
    report = align_report(primary, through)
    short = report["stale"] + report["empty"]
    if short:
        logger.info("%d/%d symbols short of %s -- asking stooq",
                    len(short), len(tickers), through)
        primary = merge_series(primary, stooq_closes(short), through)
    require_through(primary, through, must=must or ())
    return primary
