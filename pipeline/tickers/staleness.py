"""Guard: fail loudly when the per-ticker OHLC store falls behind the market.

`data/output/tickers/<T>.json` is written by `pipeline.tickers.run_tickers`,
whose universe is a *rolling* set (open positions + trades closed in the last
90 days + the top-N Heating Up names). A ticker that leaves that set is never
written again, so its file freezes at whatever bars it last had — silently.
Nothing errors; consumers just keep reading months-old closes.

That is exactly what happened to 46 files in Aug 2026: they were fetched on
2026-05-24, dropped out of the universe, and sat at a 2026-05-22 last bar for
2.5 months while the rest of the store tracked the market.

This module measures the lag in *trading days* (so weekends and NYSE holidays
never register as staleness) and reports the share of files that are behind.
Run it as a CLI to gate or warn in the pipeline:

    python -m pipeline.tickers.staleness                    # warn, exit 0
    python -m pipeline.tickers.staleness --fail             # exit 1 if breached
    python -m pipeline.tickers.staleness --fail --max-stale-share 0.05

Thresholds are deliberately two-sided: a single delisted name going stale is
noise, a tenth of the store going stale is a broken refresh.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from pipeline.marketcal import is_trading_day, market_today

TICKERS_DIR = Path("data/output/tickers")

# Files that are not per-ticker OHLC payloads.
SKIP_STEMS = {"_benchmarks"}

# A file may lag the last completed session by this many trading days before it
# counts as stale. 2 absorbs a pipeline that runs pre-close and a one-day miss.
DEFAULT_MAX_LAG = 2

# Fail only when a *meaningful share* of the store is behind — one delisted
# ticker should not break the daily run.
DEFAULT_MAX_STALE_SHARE = 0.10


@dataclass
class StaleFile:
    ticker: str
    last_bar: Optional[str]  # None when the file carries no OHLC at all
    lag_trading_days: Optional[int]

    def __str__(self) -> str:
        if self.last_bar is None:
            return f"{self.ticker}: no OHLC array"
        return f"{self.ticker}: last bar {self.last_bar} ({self.lag_trading_days} trading days behind)"


@dataclass
class FreshnessReport:
    as_of: str                      # last completed session we expect bars through
    total: int = 0
    fresh: int = 0
    stale: list[StaleFile] = field(default_factory=list)

    @property
    def stale_count(self) -> int:
        return len(self.stale)

    @property
    def stale_share(self) -> float:
        return (self.stale_count / self.total) if self.total else 0.0

    def summary(self) -> str:
        return (
            f"{self.total} ticker files, expecting bars through {self.as_of}: "
            f"{self.fresh} fresh, {self.stale_count} stale "
            f"({self.stale_share:.1%})"
        )


def last_completed_session(as_of: Optional[dt.date] = None) -> dt.date:
    """The most recent trading day strictly before `as_of` (default: today, ET).

    Strictly before, because today's daily bar does not exist until the close —
    a pipeline running at 21:30 UTC (17:30 ET) would otherwise flag the whole
    store as one day stale on every run. The `--max-lag` tolerance covers the
    other direction.
    """
    d = (as_of or market_today()) - dt.timedelta(days=1)
    for _ in range(10):  # 10 back-steps clears any NYSE holiday run
        if is_trading_day(d):
            return d
        d -= dt.timedelta(days=1)
    return d


def trading_days_between(start: dt.date, end: dt.date) -> int:
    """Count of trading days in (start, end] — 0 when end <= start."""
    if end <= start:
        return 0
    n, d = 0, start + dt.timedelta(days=1)
    while d <= end:
        if is_trading_day(d):
            n += 1
        d += dt.timedelta(days=1)
    return n


def last_bar_date(path: Path) -> Optional[str]:
    """ISO date of the newest bar in a ticker file, or None if it has no usable
    OHLC. Unreadable/malformed files return None (they are a problem too)."""
    try:
        j = json.load(open(path))
    except (ValueError, OSError):
        return None
    if not isinstance(j, dict):
        return None
    bars = j.get("ohlc_2y") or j.get("ohlc_1y") or j.get("ohlc")
    if not isinstance(bars, list) or not bars:
        return None
    last = bars[-1]
    if not isinstance(last, dict):
        return None
    date = last.get("date")
    return date if isinstance(date, str) else None


def _ticker_files(tickers_dir: Path) -> Iterable[Path]:
    for p in sorted(tickers_dir.glob("*.json")):
        if p.stem in SKIP_STEMS:
            continue
        yield p


def audit_freshness(tickers_dir: Path = TICKERS_DIR,
                    as_of: Optional[dt.date] = None,
                    max_lag: int = DEFAULT_MAX_LAG) -> FreshnessReport:
    """Measure how far each ticker file lags the last completed session."""
    expected = last_completed_session(as_of)
    report = FreshnessReport(as_of=expected.isoformat())

    for path in _ticker_files(tickers_dir):
        report.total += 1
        raw = last_bar_date(path)
        if raw is None:
            report.stale.append(StaleFile(path.stem, None, None))
            continue
        try:
            last = dt.date.fromisoformat(raw)
        except ValueError:
            report.stale.append(StaleFile(path.stem, raw, None))
            continue
        lag = trading_days_between(last, expected)
        if lag > max_lag:
            report.stale.append(StaleFile(path.stem, raw, lag))
        else:
            report.fresh += 1

    report.stale.sort(key=lambda s: (-(s.lag_trading_days or 10**6), s.ticker))
    return report


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--tickers-dir", type=Path, default=TICKERS_DIR)
    p.add_argument("--max-lag", type=int, default=DEFAULT_MAX_LAG,
                   help=f"trading days a file may lag before it counts as stale "
                        f"(default {DEFAULT_MAX_LAG})")
    p.add_argument("--max-stale-share", type=float, default=DEFAULT_MAX_STALE_SHARE,
                   help=f"stale share that trips the guard, 0-1 "
                        f"(default {DEFAULT_MAX_STALE_SHARE})")
    p.add_argument("--as-of", type=dt.date.fromisoformat, default=None,
                   help="audit as of this date instead of today (ISO, for tests/backfills)")
    p.add_argument("--fail", action="store_true",
                   help="exit 1 when the threshold is breached (default: warn, exit 0)")
    p.add_argument("--list-all", action="store_true",
                   help="list every stale ticker (default: first 20)")
    args = p.parse_args(argv)

    if not args.tickers_dir.is_dir():
        print(f"staleness: {args.tickers_dir} does not exist", file=sys.stderr)
        return 1

    report = audit_freshness(args.tickers_dir, as_of=args.as_of, max_lag=args.max_lag)
    print(report.summary())

    if report.stale:
        shown = report.stale if args.list_all else report.stale[:20]
        for s in shown:
            print(f"  {s}")
        if len(shown) < report.stale_count:
            print(f"  … and {report.stale_count - len(shown)} more (--list-all)")

    breached = report.stale_share > args.max_stale_share
    if not breached:
        return 0

    level = "ERROR" if args.fail else "WARNING"
    print(
        f"{level}: {report.stale_share:.1%} of ticker files are stale "
        f"(threshold {args.max_stale_share:.0%}). These names left the "
        f"run_tickers universe and stopped being refreshed. Fix with:\n"
        f"  python -m pipeline.tickers.run_tickers --refresh-existing",
        file=sys.stderr,
    )
    return 1 if args.fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
