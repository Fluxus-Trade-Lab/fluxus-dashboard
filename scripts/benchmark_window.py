#!/usr/bin/env python3
"""Benchmark return over an arbitrary window, straight from IBKR.

Exists so every published performance comparison ("the account did X, SPY did Y")
has a reproducible source. Per house rule, index/benchmark data comes from IBKR
only -- never TradingView.

    python scripts/benchmark_window.py 2025-12-31 2026-07-22
    python scripts/benchmark_window.py 2025-12-31 2026-07-22 --tickers SPY QQQ IWM

Price return, not total return: IBKR's ADJUSTED_LAST times out for these ETFs, and
price return is the correct comparison anyway -- the account figure it sits next to
is realized trading P&L, which also excludes dividends. Both sides consistent.
"""
import argparse
import datetime as dt
import sys

from ib_async import IB, Stock

PORTS = (7496, 7497, 4001, 4002)   # TWS live/paper, then Gateway live/paper
CLIENT_IDS = (12, 13, 14, 15)      # low ids: high ids hang TWS across sessions.
# Several are tried because a previous run that died mid-request leaves its id
# held by TWS for a while ("Error 326: client id is already in use").


def connect() -> IB:
    ib, last = IB(), None
    for port in PORTS:
        for client_id in CLIENT_IDS:
            try:
                ib.connect("127.0.0.1", port, clientId=client_id, timeout=8)
                print(f"# connected on port {port} (clientId {client_id})", file=sys.stderr)
                return ib
            except Exception as exc:        # noqa: BLE001 - try next id, then next port
                last = exc
                if "refused" in str(exc).lower():
                    break                   # nothing listening here; skip other ids
    raise SystemExit(f"no IBKR connection on {PORTS}: {last}")


def months_span(start: dt.date, end: dt.date) -> str:
    """IBKR durationStr covering the window with a month of slack on each side."""
    return f"{max(1, (end.year - start.year) * 12 + end.month - start.month + 2)} M"


def series(ib: IB, ticker: str, end: dt.date, duration: str) -> dict[str, float]:
    contract = Stock(ticker, "SMART", "USD")
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=f"{end:%Y%m%d} 23:59:59 US/Eastern",
        durationStr=duration,
        barSizeSetting="1 day",
        whatToShow="TRADES",
        useRTH=True,
        formatDate=1,
        timeout=90,
    )
    return {str(b.date): b.close for b in bars}


def close_on_or_before(closes: dt.date, day: str):
    prior = [d for d in sorted(closes) if d <= day]
    return (prior[-1], closes[prior[-1]]) if prior else (None, None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("start")
    ap.add_argument("end")
    ap.add_argument("--tickers", nargs="+", default=["SPY", "QQQ"])
    args = ap.parse_args()

    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    duration = months_span(start, end)

    ib = connect()
    try:
        print(f"{'':6s} {'from':>12s} {'close':>9s}   {'to':>12s} {'close':>9s}   {'return':>8s}")
        for ticker in args.tickers:
            closes = series(ib, ticker, end + dt.timedelta(days=1), duration)
            if not closes:
                print(f"{ticker:6s} NO DATA")
                continue
            d0, p0 = close_on_or_before(closes, args.start)
            d1, p1 = close_on_or_before(closes, args.end)
            if p0 is None or p1 is None:
                print(f"{ticker:6s} window not covered (have {min(closes)}..{max(closes)})")
                continue
            print(f"{ticker:6s} {d0:>12s} {p0:>9.2f} -> {d1:>12s} {p1:>9.2f}   "
                  f"{(p1 / p0 - 1) * 100:>+7.2f}%")
            ib.sleep(3)                     # stay inside IBKR historical pacing
    finally:
        ib.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
