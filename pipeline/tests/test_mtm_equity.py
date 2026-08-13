"""Unit tests for the mark-to-market equity curve (pure math, no network)."""
from datetime import date

from pipeline.portfolio.analytics import (
    Trade, Trim,
    build_mtm_equity_curve, max_drawdown, max_intraday_drawdown,
)


def _price_fn(table):
    """table: {(ticker, iso_date): (close, low, high)}; None when absent."""
    def fn(ticker, day, field):
        hit = table.get((ticker, day.isoformat()))
        if hit is None:
            return None
        return hit[{"close": 0, "low": 1, "high": 2}[field]]
    return fn


def test_single_long_mtm_marks_to_close():
    # Buy 100 @ $10 on day 1 ($1,000 cost), mark at close each day.
    t = Trade(ticker="AAA", direction="long", entry_date=date(2026, 1, 1),
              entry_price=10.0, orig_qty=100, curr_qty=100, stop=9.0, closed=False)
    prices = {
        ("AAA", "2026-01-01"): (10.0, 9.5, 10.5),
        ("AAA", "2026-01-02"): (12.0, 11.0, 13.0),  # +$200 close, low marks +$100
    }
    curve = build_mtm_equity_curve(
        [t], 1000.0, date(2026, 1, 1), date(2026, 1, 2), _price_fn(prices))
    assert len(curve) == 2
    # Day 1: cash 1000 - 1000 + 100*10 = 1000
    assert curve[0].equity == 1000.0
    # Day 2: cash 0 + 100*12 = 1200
    assert curve[1].equity == 1200.0
    assert curve[1].daily_pnl == 200.0
    # intraday envelope on day 2: low mark = 100*11 = 1100, high = 100*13 = 1300
    assert curve[1].intraday_low == 1100.0
    assert curve[1].intraday_high == 1300.0


def test_trim_realizes_into_cash():
    t = Trade(ticker="BBB", direction="long", entry_date=date(2026, 1, 1),
              entry_price=10.0, orig_qty=100, curr_qty=50, stop=9.0, closed=False,
              trims=[Trim(date=date(2026, 1, 2), price=11.0, qty=50, type="trim_1_2")])
    prices = {
        ("BBB", "2026-01-01"): (10.0, 10.0, 10.0),
        ("BBB", "2026-01-02"): (11.0, 11.0, 11.0),
    }
    curve = build_mtm_equity_curve(
        [t], 1000.0, date(2026, 1, 1), date(2026, 1, 2), _price_fn(prices))
    # Day 2: cash = 1000 - 1000 + 50*11 (trim) = 550; remaining 50 @ 11 = 550 → 1100
    assert curve[1].equity == 1100.0


def test_short_marks_inverted():
    t = Trade(ticker="CCC", direction="short", entry_date=date(2026, 1, 1),
              entry_price=20.0, orig_qty=100, curr_qty=100, stop=22.0, closed=False)
    prices = {
        ("CCC", "2026-01-01"): (20.0, 19.0, 21.0),
        ("CCC", "2026-01-02"): (18.0, 17.0, 19.0),  # price down = short profit
    }
    curve = build_mtm_equity_curve(
        [t], 1000.0, date(2026, 1, 1), date(2026, 1, 2), _price_fn(prices))
    # Short: cash = 1000 + 100*20 = 3000; mv = 100*18*(-1) = -1800 → 1200 (+$200)
    assert curve[1].equity == 1200.0
    # Worst case for a short is price UP → mark at the high (19): mv = -1900
    assert curve[1].intraday_low == 3000.0 - 1900.0  # 1100
    assert curve[1].intraday_high == 3000.0 - 1700.0  # 1300


def test_missing_price_falls_back_to_entry():
    t = Trade(ticker="DDD", direction="long", entry_date=date(2026, 1, 1),
              entry_price=10.0, orig_qty=100, curr_qty=100, stop=9.0, closed=False)
    curve = build_mtm_equity_curve(
        [t], 1000.0, date(2026, 1, 1), date(2026, 1, 2), _price_fn({}))
    # No prices at all → marked flat at entry → equity stays at starting capital
    assert curve[0].equity == 1000.0
    assert curve[1].equity == 1000.0
    assert curve[1].intraday_low == 1000.0


def test_intraday_drawdown_deeper_than_close():
    t = Trade(ticker="EEE", direction="long", entry_date=date(2026, 1, 1),
              entry_price=10.0, orig_qty=100, curr_qty=100, stop=8.0, closed=False)
    prices = {
        ("EEE", "2026-01-01"): (10.0, 10.0, 10.0),
        # Close recovers to 10, but intraday low was 7 (a -30% spike on the position)
        ("EEE", "2026-01-02"): (10.0, 7.0, 10.0),
    }
    curve = build_mtm_equity_curve(
        [t], 1000.0, date(2026, 1, 1), date(2026, 1, 2), _price_fn(prices))
    close_dd = max_drawdown(curve)
    intra_dd = max_intraday_drawdown(curve)
    assert close_dd.drawdown_pct == 0.0          # flat on a close basis
    assert round(intra_dd.drawdown_pct, 4) == 0.30  # -30% intraday envelope


def test_weekends_skipped():
    t = Trade(ticker="FFF", direction="long", entry_date=date(2026, 1, 2),  # Friday
              entry_price=10.0, orig_qty=10, curr_qty=10, stop=9.0, closed=False)
    # Jan 3-4 2026 is Sat/Sun; only Fri Jan 2 and Mon Jan 5 should appear
    curve = build_mtm_equity_curve(
        [t], 1000.0, date(2026, 1, 2), date(2026, 1, 5), _price_fn({}))
    assert [p.date for p in curve] == [date(2026, 1, 2), date(2026, 1, 5)]
