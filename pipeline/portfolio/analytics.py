"""
Trading Performance Analytics
==============================

Drop-in module for computing performance metrics, drawdown, exit-style
classification, and portfolio heat for swing/momentum trading strategies.

Designed around a trade model with:
  - Single entry (date, price, qty)
  - Optional stop loss
  - 0-3 partial-exit "trims" (date, price, qty, type)
  - 'closed' flag (False if still holding remaining shares)

All math is intentionally written without external dependencies (pure
stdlib) so it ports cleanly to JavaScript/TypeScript for the React tracker.
Every metric carries its formula in the docstring.

Usage:
    from analytics import parse_csv, compute_report, portfolio_heat

    trades, start_cap = parse_csv("portfolio.csv")
    report, curve = compute_report(trades, start_cap,
                                    date(2026, 1, 2), date(2026, 5, 21))
    print(f"Return: {report.return_pct * 100:.2f}%")

    heat = portfolio_heat(open_trades, current_prices, account_equity)
    print(f"Heat: {heat.open_heat_pct * 100:.1f}% ({heat.status})")
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from statistics import mean, median, stdev
from typing import Literal, Optional


# =============================================================================
# DATA MODEL
# =============================================================================

Direction = Literal["long", "short"]
ExitStyle = Literal["strength", "weakness", "mixed", "stop_only"]


@dataclass
class Trim:
    """A partial or full exit. 'type' is informational only (e.g. 'trim_1_3')."""
    date: date
    price: float
    qty: int
    type: str = ""


@dataclass
class Trade:
    """
    A single trade. Invariants:
      - orig_qty > 0
      - sum(trim.qty for trim in trims) <= orig_qty
      - if closed: sum(trim.qty) == orig_qty, curr_qty == 0
      - if not closed: curr_qty == orig_qty - sum(trim.qty)
    """
    ticker: str
    direction: Direction
    entry_date: date
    entry_price: float
    orig_qty: int
    curr_qty: int                             # remaining shares; 0 if closed
    stop: Optional[float] = None
    closed: bool = False
    sector: str = ""
    trims: list[Trim] = field(default_factory=list)


# =============================================================================
# TRADE-LEVEL METRICS
# =============================================================================

def realized_pnl(t: Trade) -> float:
    """
    Sum of P&L across all completed trims (does NOT mark-to-market remaining qty).

        Long:   sum( (trim_price - entry_price) * trim_qty )
        Short:  sum( (entry_price - trim_price) * trim_qty )

    For an open position with partial trims, this returns the realized portion
    only. To get total trade P&L including unrealized, add:
        sign * (current_price - entry_price) * curr_qty
    """
    sign = 1 if t.direction == "long" else -1
    return sum(sign * (tr.price - t.entry_price) * tr.qty for tr in t.trims)


def total_pnl(t: Trade, current_price: Optional[float] = None) -> float:
    """Realized + unrealized P&L. current_price required for open positions."""
    pnl = realized_pnl(t)
    if not t.closed and current_price is not None and t.curr_qty > 0:
        sign = 1 if t.direction == "long" else -1
        pnl += sign * (current_price - t.entry_price) * t.curr_qty
    return pnl


def r_risk(t: Trade) -> Optional[float]:
    """
    1R = dollar risk if the stop fires from entry on the ORIGINAL position.

        risk_1R = |entry_price - stop_price| * orig_qty

    Returns None if no stop is set. Use the original quantity (not current)
    so that R-multiples are comparable across the trade's life.
    """
    if t.stop is None or t.stop <= 0:
        return None
    return abs(t.entry_price - t.stop) * t.orig_qty


def r_multiple(t: Trade) -> Optional[float]:
    """
    R-multiple = realized_pnl / r_risk

    Standardizes P&L across position sizes:
      +2R: trade made 2x what was risked
      -1R: clean stop-out
      +5R: significant winner
    """
    risk = r_risk(t)
    if risk is None or risk == 0:
        return None
    return realized_pnl(t) / risk


def classify_exit_style(t: Trade) -> ExitStyle:
    """
    Bucket a trade by HOW the exits were sequenced. Direction-adjusted so
    that "better" always means "more profitable" regardless of long/short.

      strength  : trim prices monotonically improving
                  (long: ascending; short: descending)
                  -> clean trim ladder, sold into rising strength
      weakness  : trim prices monotonically deteriorating
                  -> trimmed into pullbacks, often capping winners
      mixed     : non-monotonic — went up, pulled back, went up again
                  -> "let it breathe" — usually your biggest winners
      stop_only : single losing exit with no profit-taking trims first
                  -> stop hit before any partials

    Single-trim profitable exits are classified as 'strength'.
    """
    if not t.trims:
        return "stop_only"

    pnl = realized_pnl(t)
    # Flip prices for shorts so higher is always "better"
    p = [tr.price if t.direction == "long" else -tr.price for tr in t.trims]

    if len(p) == 1:
        return "strength" if pnl > 0 else "stop_only"

    ascending = all(p[i] <= p[i + 1] for i in range(len(p) - 1))
    descending = all(p[i] >= p[i + 1] for i in range(len(p) - 1))

    if ascending and not descending:
        return "strength"
    if descending and not ascending:
        return "weakness"
    if ascending and descending:        # all prices equal
        return "strength"
    return "mixed"


def hold_days(t: Trade) -> Optional[int]:
    """Calendar days from entry to the LAST trim. None if no trims."""
    if not t.trims:
        return None
    last = max(tr.date for tr in t.trims)
    return (last - t.entry_date).days


def panic_trim_leak(t: Trade) -> Optional[float]:
    """
    For winning trades where you trimmed INTO weakness (descending trim
    sequence for a long), compute how much more you'd have made if every
    trim had executed at the BEST-priced trim instead.

    This is your "panic-trim tax." Sum it across all winners monthly —
    that's the cost of selling into weakness when the trade was already
    green. Should trend toward zero as discipline improves.

    Returns None for:
      - losers
      - single-trim trades
      - trades where exits didn't deteriorate
    """
    if not t.trims or len(t.trims) < 2:
        return None
    pnl = realized_pnl(t)
    if pnl <= 0:
        return None

    prices = [tr.price for tr in t.trims]
    if t.direction == "long":
        deteriorating = all(prices[i] >= prices[i + 1] for i in range(len(prices) - 1))
        if not deteriorating or prices[0] == prices[-1]:
            return None
        best_price = max(prices)
    else:
        deteriorating = all(prices[i] <= prices[i + 1] for i in range(len(prices) - 1))
        if not deteriorating or prices[0] == prices[-1]:
            return None
        best_price = min(prices)

    total_qty = sum(tr.qty for tr in t.trims)
    sign = 1 if t.direction == "long" else -1
    best_pnl = sign * (best_price - t.entry_price) * total_qty
    return best_pnl - pnl


# =============================================================================
# EQUITY CURVE + DRAWDOWN
# =============================================================================

@dataclass
class EquityPoint:
    """One row in the equity curve."""
    date: date
    equity: float
    peak: float              # running max equity to date
    drawdown: float          # (peak - equity) / peak; 0 means at new high
    daily_pnl: float


def build_equity_curve(
    trades: list[Trade],
    starting_capital: float,
    start_date: date,
    end_date: date,
) -> list[EquityPoint]:
    """
    Construct a daily equity curve over [start_date, end_date] using
    weekdays only (Mon-Fri). Each trim's P&L is credited on the trim's
    date. Days with no activity carry forward the previous equity.

    NOTE: This uses TRADE-ACTIVITY-DAY accounting, not calendar-day
    mark-to-market. If you want true MTM (using daily close prices on
    open positions), you need an additional price-history source and
    a different builder.
    """
    daily_pnl: dict[date, float] = defaultdict(float)
    for t in trades:
        sign = 1 if t.direction == "long" else -1
        for tr in t.trims:
            daily_pnl[tr.date] += sign * (tr.price - t.entry_price) * tr.qty

    points: list[EquityPoint] = []
    equity = starting_capital
    peak = starting_capital

    d = start_date
    while d <= end_date:
        if d.weekday() < 5:                 # 0=Mon .. 4=Fri
            pnl = daily_pnl.get(d, 0.0)
            equity += pnl
            peak = max(peak, equity)
            dd = (peak - equity) / peak if peak > 0 else 0.0
            points.append(EquityPoint(d, equity, peak, dd, pnl))
        d += timedelta(days=1)
    return points


def sma(values: list[float], n: int) -> list[Optional[float]]:
    """
    Simple moving average. First (n-1) entries are None.

        sma[i] = mean(values[i-n+1 : i+1])
    """
    out: list[Optional[float]] = []
    for i in range(len(values)):
        if i < n - 1:
            out.append(None)
        else:
            out.append(sum(values[i - n + 1:i + 1]) / n)
    return out


@dataclass
class DrawdownWindow:
    """One drawdown event: peak -> trough -> (optional) recovery."""
    peak_idx: int
    trough_idx: int
    recovery_idx: Optional[int]              # None if not yet recovered
    peak_equity: float
    trough_equity: float
    drawdown_pct: float                      # 0..1
    duration_days: int                       # trading days peak -> trough
    recovery_days: Optional[int]             # trading days trough -> new peak


def max_drawdown(curve: list[EquityPoint]) -> DrawdownWindow:
    """
    Find the worst peak-to-trough decline in the curve.

    Algorithm:
      1. Walk forward tracking running peak.
      2. At each point, dd = (peak - equity) / peak.
      3. The trough is the point with the highest dd.
      4. The peak is the most recent prior point where equity == peak.
      5. Recovery is the first point after the trough where equity >= peak.
    """
    if not curve:
        raise ValueError("Empty curve")

    max_dd = 0.0
    trough_idx = 0
    for i, p in enumerate(curve):
        if p.drawdown > max_dd:
            max_dd = p.drawdown
            trough_idx = i

    # Walk back to find the peak that defined this drawdown
    target_peak = curve[trough_idx].peak
    peak_idx = trough_idx
    for i in range(trough_idx, -1, -1):
        if curve[i].equity >= target_peak:
            peak_idx = i
            break

    # Walk forward to find recovery
    recovery_idx: Optional[int] = None
    for i in range(trough_idx + 1, len(curve)):
        if curve[i].equity >= target_peak:
            recovery_idx = i
            break

    return DrawdownWindow(
        peak_idx=peak_idx,
        trough_idx=trough_idx,
        recovery_idx=recovery_idx,
        peak_equity=curve[peak_idx].equity,
        trough_equity=curve[trough_idx].equity,
        drawdown_pct=max_dd,
        duration_days=trough_idx - peak_idx,
        recovery_days=(recovery_idx - trough_idx) if recovery_idx else None,
    )


def find_drawdown_windows(
    curve: list[EquityPoint],
    min_dd: float = 0.02,
) -> list[DrawdownWindow]:
    """
    Find ALL drawdowns deeper than min_dd (default 2%). Useful for
    detecting recurring stall periods, not just the worst one.
    """
    windows: list[DrawdownWindow] = []
    in_dd = False
    start_idx = 0
    peak_eq = curve[0].equity if curve else 0
    worst_in_window = 0
    worst_idx = 0

    for i, p in enumerate(curve):
        if not in_dd and p.drawdown >= min_dd:
            in_dd = True
            start_idx = i
            peak_eq = p.peak
            worst_in_window = p.drawdown
            worst_idx = i
        elif in_dd:
            if p.drawdown > worst_in_window:
                worst_in_window = p.drawdown
                worst_idx = i
            if p.equity >= peak_eq:
                # Recovered
                # Find true peak idx
                peak_idx = start_idx
                for j in range(start_idx, -1, -1):
                    if curve[j].equity >= peak_eq:
                        peak_idx = j
                        break
                windows.append(DrawdownWindow(
                    peak_idx=peak_idx,
                    trough_idx=worst_idx,
                    recovery_idx=i,
                    peak_equity=peak_eq,
                    trough_equity=curve[worst_idx].equity,
                    drawdown_pct=worst_in_window,
                    duration_days=worst_idx - peak_idx,
                    recovery_days=i - worst_idx,
                ))
                in_dd = False

    # Trailing unrecovered drawdown
    if in_dd:
        peak_idx = start_idx
        for j in range(start_idx, -1, -1):
            if curve[j].equity >= peak_eq:
                peak_idx = j
                break
        windows.append(DrawdownWindow(
            peak_idx=peak_idx,
            trough_idx=worst_idx,
            recovery_idx=None,
            peak_equity=peak_eq,
            trough_equity=curve[worst_idx].equity,
            drawdown_pct=worst_in_window,
            duration_days=worst_idx - peak_idx,
            recovery_days=None,
        ))
    return windows


# =============================================================================
# MARK-TO-MARKET EQUITY CURVE (real daily prices)
# =============================================================================
#
# build_equity_curve() above credits only REALIZED trim P&L on trim dates and
# never marks open positions to market. That is fine for behavioral attribution
# but it does NOT match the live Fluxus dashboard, whose equity curve marks every
# open position at its real daily close. Use the MTM builder below when you want
# numbers that reconcile with the dashboard header (return, drawdown, Sharpe).

from typing import Callable


PriceField = Literal["close", "low", "high"]
# price_fn(ticker, day, field) -> price or None when no bar exists for that day.
# The caller (e.g. a yfinance/ohlc_cache adapter) owns walk-back-to-last-known-bar.
PriceFn = Callable[[str, date, str], Optional[float]]


@dataclass
class MTMEquityPoint:
    """One row in the mark-to-market equity curve."""
    date: date
    equity: float            # close book value: cash + Σ remaining_qty·close·dir
    peak: float              # running max of close equity
    drawdown: float          # (peak - equity)/peak on a CLOSE basis
    daily_pnl: float         # close-to-close change
    intraday_low: float      # worst-case book value (longs@low, shorts@high)
    intraday_high: float     # best-case book value (longs@high, shorts@low)


def build_mtm_equity_curve(
    trades: list[Trade],
    starting_capital: float,
    start_date: date,
    end_date: date,
    price_fn: PriceFn,
) -> list[MTMEquityPoint]:
    """
    Daily mark-to-market equity curve over weekdays in [start_date, end_date],
    mirroring the Fluxus dashboard's buildEquityCurve (equityCurve.js):

        equity(d) = cash(d) + Σ_open remaining_qty · close(ticker, d) · dir

    where cash(d) folds in each trade's entry cost and every trim on/before d.
    Closed positions contribute purely through realized cash; open positions add
    their remaining quantity marked at the real daily close.

    price_fn(ticker, day, field) returns the price for that bar or None when no
    bar exists; on None we fall back to the trade's entry price for that day
    (identical to the dashboard's lookupPrice fallback). Walk-back to the last
    known bar is the price_fn's responsibility.

    intraday_low/high mark longs at the daily low/high (and shorts inverted) so
    that max_intraday_drawdown() can bound the worst peak-to-trough the book
    could have printed intraday. That envelope is conservative: it assumes every
    position hits its adverse extreme at the same instant.
    """
    points: list[MTMEquityPoint] = []
    peak = starting_capital
    prev_equity = starting_capital

    d = start_date
    while d <= end_date:
        if d.weekday() >= 5:                       # skip weekends
            d += timedelta(days=1)
            continue

        cash = starting_capital
        mv_close = mv_low = mv_high = 0.0

        for t in trades:
            if t.entry_date > d:
                continue
            sign = 1 if t.direction == "long" else -1
            cash -= t.orig_qty * t.entry_price * sign

            sold = 0
            for tr in t.trims:
                if tr.date <= d:
                    cash += tr.qty * tr.price * sign
                    sold += tr.qty

            qty = t.orig_qty - sold
            if qty <= 0:
                continue

            close = price_fn(t.ticker, d, "close")
            if close is None:
                close = low = high = t.entry_price
            else:
                low = price_fn(t.ticker, d, "low") or close
                high = price_fn(t.ticker, d, "high") or close

            mv_close += qty * close * sign
            # worst case: long marked at its low, short marked at its high
            worst = low if sign == 1 else high
            best = high if sign == 1 else low
            mv_low += qty * worst * sign
            mv_high += qty * best * sign

        equity = cash + mv_close
        peak = max(peak, equity)
        dd = (peak - equity) / peak if peak > 0 else 0.0
        points.append(MTMEquityPoint(
            date=d,
            equity=equity,
            peak=peak,
            drawdown=dd,
            daily_pnl=equity - prev_equity,
            intraday_low=cash + mv_low,
            intraday_high=cash + mv_high,
        ))
        prev_equity = equity
        d += timedelta(days=1)

    return points


def max_intraday_drawdown(curve: list[MTMEquityPoint]) -> DrawdownWindow:
    """
    Worst peak-to-trough using intraday extremes: the running peak is taken from
    intraday_high, the trough from intraday_low. Deeper than the close-to-close
    figure because it captures adverse excursions that recovered by the close.

    CONSERVATIVE: assumes all positions hit their adverse extreme simultaneously,
    so treat it as an upper bound on the intraday pain, not a realized number.
    """
    if not curve:
        raise ValueError("Empty curve")

    running_peak = curve[0].intraday_high
    peak_idx = 0
    cur_peak_idx = 0
    max_dd = 0.0
    trough_idx = 0
    for i, p in enumerate(curve):
        if p.intraday_high > running_peak:
            running_peak = p.intraday_high
            cur_peak_idx = i
        dd = (running_peak - p.intraday_low) / running_peak if running_peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
            trough_idx = i
            peak_idx = cur_peak_idx

    recovery_idx: Optional[int] = None
    target = curve[peak_idx].intraday_high
    for i in range(trough_idx + 1, len(curve)):
        if curve[i].intraday_high >= target:
            recovery_idx = i
            break

    return DrawdownWindow(
        peak_idx=peak_idx,
        trough_idx=trough_idx,
        recovery_idx=recovery_idx,
        peak_equity=curve[peak_idx].intraday_high,
        trough_equity=curve[trough_idx].intraday_low,
        drawdown_pct=max_dd,
        duration_days=trough_idx - peak_idx,
        recovery_days=(recovery_idx - trough_idx) if recovery_idx else None,
    )


# =============================================================================
# RISK-ADJUSTED RETURNS (Sharpe / Sortino)
# =============================================================================

def daily_returns(curve: list[EquityPoint]) -> list[float]:
    """Period-over-period returns from the equity curve."""
    out = []
    for i in range(1, len(curve)):
        prev = curve[i - 1].equity
        if prev > 0:
            out.append((curve[i].equity - prev) / prev)
    return out


def sharpe_ratio(returns: list[float], rf: float = 0.0, periods: int = 252) -> float:
    """
    Annualized Sharpe ratio.

        Sharpe = (mean(returns) - rf_per_period) / stdev(returns) * sqrt(periods)

    rf is the ANNUAL risk-free rate (e.g. 0.05 for 5%).
    periods = 252 for daily, 52 for weekly, 12 for monthly.

    CAVEAT: If returns come from a trade-activity-day series (skipping
    idle days), Sharpe is inflated vs a calendar-day series. For a
    publishable Sharpe, fill idle calendar days with 0% return first.
    """
    if len(returns) < 2:
        return 0.0
    sd = stdev(returns)
    if sd == 0:
        return 0.0
    rf_per_period = rf / periods
    return (mean(returns) - rf_per_period) / sd * math.sqrt(periods)


def sortino_ratio(returns: list[float], rf: float = 0.0, periods: int = 252) -> float:
    """
    Annualized Sortino ratio. Like Sharpe but only penalizes DOWNSIDE
    volatility (negative returns). More appropriate for strategies with
    asymmetric return distributions like momentum trading.

        downside_dev = sqrt( sum(r^2 for r in negative_returns) / N_negative )
        Sortino = (mean(returns) - rf_per_period) / downside_dev * sqrt(periods)
    """
    if len(returns) < 2:
        return 0.0
    neg = [r for r in returns if r < 0]
    if not neg:
        return float("inf")                  # no losses = undefined upper bound
    downside = math.sqrt(sum(r * r for r in neg) / len(neg))
    if downside == 0:
        return 0.0
    rf_per_period = rf / periods
    return (mean(returns) - rf_per_period) / downside * math.sqrt(periods)


def calmar_ratio(annual_return: float, max_dd_pct: float) -> float:
    """
    Calmar = annualized return / max drawdown.
    Quick gut-check ratio. >3 is exceptional for active trading.
    """
    return annual_return / max_dd_pct if max_dd_pct > 0 else 0


# =============================================================================
# PORTFOLIO HEAT
# =============================================================================

def position_heat(direction: Direction, current_price: float,
                  stop: float, qty: int) -> float:
    """
    Heat = the dollar amount the market can take if the stop fires NOW.

        Long:  max(0, current - stop) * qty
        Short: max(0, stop - current) * qty

    For a winning long where current > entry > stop, heat is the
    "give-back-to-stop" amount — what unrealized profit you'd surrender.
    For a losing long where current < entry but still > stop, heat is
    the additional loss you'd take from here to the stop.
    """
    if direction == "long":
        return max(0.0, current_price - stop) * qty
    return max(0.0, stop - current_price) * qty


def position_initial_heat(t: Trade) -> Optional[float]:
    """
    Initial heat = entry-to-stop risk on the remaining open quantity.

        |entry - stop| * curr_qty

    Used to measure "fresh risk" — how much you'd lose if a still-red
    position stopped out. Returns None if no stop or trade is closed.
    """
    if t.stop is None or t.closed:
        return None
    return abs(t.entry_price - t.stop) * t.curr_qty


@dataclass
class HeatReport:
    """Aggregate portfolio-level risk snapshot."""
    open_heat_usd: float
    open_heat_pct: float                     # / account_equity
    initial_heat_usd: float                  # fresh risk on losing positions only
    initial_heat_pct: float
    by_position: list[tuple[str, float]]     # [(ticker, heat_usd)] sorted desc
    n_positions: int

    @property
    def status(self) -> Literal["cool", "warm", "hot", "overheated"]:
        """Zone classification based on open_heat_pct."""
        h = self.open_heat_pct
        if h < 0.05:
            return "cool"
        if h < 0.08:
            return "warm"
        if h < 0.12:
            return "hot"
        return "overheated"


def portfolio_heat(
    open_trades: list[Trade],
    current_prices: dict[str, float],
    account_equity: float,
) -> HeatReport:
    """
    Compute aggregate heat across all open positions.

    Args:
        open_trades:     list of Trade where closed=False
        current_prices:  {ticker: last_price} for every open position
        account_equity:  total account value (cash + positions, MTM)

    Returns a HeatReport with status zones suggesting action:
        cool       (<5%):  room to add new positions
        warm       (5-8%): healthy, monitor
        hot        (8-12%): trim before adding new exposure
        overheated (>12%): no new entries; consider de-risking

    Suggested ceiling for momentum swing trading: 8% open heat.

    Companion rules to enforce alongside this:
      - Per-ticker heat capped at ~4% (single-name concentration limit)
      - Per-sector heat capped at ~6% (sector concentration limit)
      - Initial heat (red positions only) capped at ~3%
    """
    total_heat = 0.0
    initial = 0.0
    by_pos: dict[str, float] = defaultdict(float)
    n_counted = 0

    for t in open_trades:
        if t.stop is None:
            continue
        last = current_prices.get(t.ticker)
        if last is None:
            continue                          # skip positions without current price
        n_counted += 1

        h = position_heat(t.direction, last, t.stop, t.curr_qty)
        total_heat += h
        by_pos[t.ticker] += h

        # Initial heat counts only positions currently in the red
        in_red = (
            (t.direction == "long" and last < t.entry_price) or
            (t.direction == "short" and last > t.entry_price)
        )
        if in_red:
            ih = position_initial_heat(t)
            if ih:
                initial += ih

    sorted_pos = sorted(by_pos.items(), key=lambda x: x[1], reverse=True)
    return HeatReport(
        open_heat_usd=total_heat,
        open_heat_pct=total_heat / account_equity if account_equity > 0 else 0,
        initial_heat_usd=initial,
        initial_heat_pct=initial / account_equity if account_equity > 0 else 0,
        by_position=sorted_pos,
        n_positions=n_counted,
    )


def can_open_new_position(
    heat_report: HeatReport,
    proposed_risk_usd: float,
    account_equity: float,
    heat_ceiling_pct: float = 0.08,
) -> tuple[bool, str]:
    """
    Pre-trade check: can we add this position without breaching heat limits?

    Args:
        heat_report:        current portfolio heat
        proposed_risk_usd:  1R risk for the proposed trade (|entry-stop|*qty)
        account_equity:     current account value
        heat_ceiling_pct:   max acceptable open heat (default 8%)

    Returns (allowed, reason).
    """
    projected_heat = heat_report.open_heat_usd + proposed_risk_usd
    projected_pct = projected_heat / account_equity if account_equity > 0 else 1.0
    if projected_pct > heat_ceiling_pct:
        return False, (
            f"Would push heat from {heat_report.open_heat_pct*100:.1f}% to "
            f"{projected_pct*100:.1f}% (ceiling {heat_ceiling_pct*100:.0f}%). "
            f"Trim existing positions or skip this trade."
        )
    return True, f"OK. Projected heat: {projected_pct*100:.1f}%."


# =============================================================================
# AGGREGATE PERFORMANCE REPORT
# =============================================================================

@dataclass
class PerformanceReport:
    """Single-shot summary of a trading period."""
    # Capital
    starting_capital: float
    ending_equity: float
    total_realized_pnl: float
    return_pct: float                        # total_realized_pnl / starting_capital

    # Trade counts
    n_trades: int
    n_closed: int
    n_open: int
    n_wins: int
    n_losses: int
    n_scratch: int

    # Win/loss stats (closed trades only)
    win_rate: float                          # wins / (wins + losses), excl scratch
    avg_winner: float
    avg_loser: float
    win_loss_ratio: float                    # |avg_winner / avg_loser|
    gross_profit: float
    gross_loss: float
    profit_factor: float                     # |gross_profit / gross_loss|
    expectancy: float                        # avg $ per trade

    # R-multiple stats
    avg_r: float
    median_r: float
    avg_winning_r: float
    avg_losing_r: float

    # Risk
    max_dd: DrawdownWindow
    sharpe: float
    sortino: float

    # Behavioral breakdown
    exit_styles: dict[str, dict]             # {style: {count, total_pnl, avg_pnl, wins, losses}}


def compute_report(
    trades: list[Trade],
    starting_capital: float,
    start_date: date,
    end_date: date,
) -> tuple[PerformanceReport, list[EquityPoint]]:
    """
    Build a complete performance report.

    Convention used here:
      - 'Wins' and 'losses' count CLOSED trades only.
      - 'total_realized_pnl' includes partial trims on still-open positions
        (these don't get classified as win/loss until the trade fully closes).
      - 'return_pct' is on the starting capital, not the peak.
    """
    closed = [t for t in trades if t.closed]
    open_t = [t for t in trades if not t.closed]

    pnls_closed = [(t, realized_pnl(t)) for t in closed]
    wins = [t for t, p in pnls_closed if p > 0]
    losses = [t for t, p in pnls_closed if p < 0]
    scratch = [t for t, p in pnls_closed if p == 0]

    total_realized = sum(realized_pnl(t) for t in trades)
    gp = sum(realized_pnl(t) for t in wins)
    gl = sum(realized_pnl(t) for t in losses)

    avg_w = mean([realized_pnl(t) for t in wins]) if wins else 0.0
    avg_l = mean([realized_pnl(t) for t in losses]) if losses else 0.0
    n_wl = len(wins) + len(losses)
    win_rate = len(wins) / n_wl if n_wl else 0.0

    rms = [r_multiple(t) for t in closed]
    rms = [r for r in rms if r is not None]
    r_wins = [r for r in rms if r > 0]
    r_losses = [r for r in rms if r < 0]

    curve = build_equity_curve(trades, starting_capital, start_date, end_date)
    rets = daily_returns(curve)

    # Exit style breakdown
    style_buckets: dict[str, list[Trade]] = defaultdict(list)
    for t in closed:
        style_buckets[classify_exit_style(t)].append(t)

    exit_styles: dict[str, dict] = {}
    for style, ts in style_buckets.items():
        pnls = [realized_pnl(t) for t in ts]
        exit_styles[style] = {
            "count": len(ts),
            "total_pnl": sum(pnls),
            "avg_pnl": sum(pnls) / len(ts) if ts else 0.0,
            "wins": sum(1 for p in pnls if p > 0),
            "losses": sum(1 for p in pnls if p < 0),
        }

    report = PerformanceReport(
        starting_capital=starting_capital,
        ending_equity=curve[-1].equity if curve else starting_capital,
        total_realized_pnl=total_realized,
        return_pct=total_realized / starting_capital if starting_capital else 0.0,
        n_trades=len(trades),
        n_closed=len(closed),
        n_open=len(open_t),
        n_wins=len(wins),
        n_losses=len(losses),
        n_scratch=len(scratch),
        win_rate=win_rate,
        avg_winner=avg_w,
        avg_loser=avg_l,
        win_loss_ratio=abs(avg_w / avg_l) if avg_l else 0.0,
        gross_profit=gp,
        gross_loss=gl,
        profit_factor=abs(gp / gl) if gl else 0.0,
        expectancy=(len(wins) * avg_w + len(losses) * avg_l) / n_wl if n_wl else 0.0,
        avg_r=mean(rms) if rms else 0.0,
        median_r=median(rms) if rms else 0.0,
        avg_winning_r=mean(r_wins) if r_wins else 0.0,
        avg_losing_r=mean(r_losses) if r_losses else 0.0,
        max_dd=max_drawdown(curve),
        sharpe=sharpe_ratio(rets),
        sortino=sortino_ratio(rets),
        exit_styles=exit_styles,
    )
    return report, curve


# =============================================================================
# DIAGNOSTICS
# =============================================================================

def top_n_winners(trades: list[Trade], n: int = 10) -> list[tuple[Trade, float]]:
    """Top n winning closed trades by realized P&L."""
    closed = [t for t in trades if t.closed]
    ranked = sorted(closed, key=lambda t: realized_pnl(t), reverse=True)
    return [(t, realized_pnl(t)) for t in ranked[:n]]


def top_n_losers(trades: list[Trade], n: int = 10) -> list[tuple[Trade, float]]:
    """Worst n losing closed trades by realized P&L."""
    closed = [t for t in trades if t.closed]
    ranked = sorted(closed, key=lambda t: realized_pnl(t))
    return [(t, realized_pnl(t)) for t in ranked[:n]]


def revenge_trade_clusters(
    trades: list[Trade],
    window_days: int = 30,
    min_stops: int = 2,
) -> list[tuple[str, list[Trade]]]:
    """
    Detect 'revenge trading': repeated entries on the same ticker within
    a rolling window after recent stop-outs. These are usually losing
    patterns where you're re-attacking a thesis that already failed.

    Returns [(ticker, [trades_in_cluster])] for clusters of >= min_stops
    stop-outs within window_days.
    """
    by_ticker: dict[str, list[Trade]] = defaultdict(list)
    for t in trades:
        if t.closed and realized_pnl(t) < 0:
            by_ticker[t.ticker].append(t)

    clusters = []
    for ticker, ts in by_ticker.items():
        ts.sort(key=lambda x: x.entry_date)
        cluster: list[Trade] = []
        for t in ts:
            if not cluster:
                cluster = [t]
            elif (t.entry_date - cluster[0].entry_date).days <= window_days:
                cluster.append(t)
            else:
                if len(cluster) >= min_stops:
                    clusters.append((ticker, list(cluster)))
                cluster = [t]
        if len(cluster) >= min_stops:
            clusters.append((ticker, cluster))
    return clusters


def aggregate_by_ticker(trades: list[Trade]) -> list[tuple[str, int, float]]:
    """Returns [(ticker, n_trades, total_realized_pnl)] sorted by pnl desc."""
    agg: dict[str, list[float]] = defaultdict(list)
    for t in trades:
        if t.closed:
            agg[t.ticker].append(realized_pnl(t))
    out = [(tk, len(pls), sum(pls)) for tk, pls in agg.items()]
    return sorted(out, key=lambda x: x[2], reverse=True)


def panic_trim_summary(trades: list[Trade]) -> tuple[int, float, list[tuple[Trade, float]]]:
    """
    Quantify the 'panic-trim tax' across all winners.

    Returns (count, total_leak_usd, [(trade, leak)...] sorted desc).
    """
    leaks = []
    for t in trades:
        leak = panic_trim_leak(t)
        if leak is not None and leak > 0:
            leaks.append((t, leak))
    leaks.sort(key=lambda x: x[1], reverse=True)
    return len(leaks), sum(l for _, l in leaks), leaks


# =============================================================================
# CSV PARSER (matches the Fluxus portfolio tracker schema)
# =============================================================================

def _parse_date(s: str) -> Optional[date]:
    """Accept ISO-8601 with timezone, or YYYY-MM-DD."""
    if not s:
        return None
    s = s.strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_csv(path: str) -> tuple[list[Trade], float]:
    """
    Parse the portfolio tracker CSV. Returns (trades, starting_capital).

    Expected format:
        Line 1-2: _meta rows with startingCapital and exportDate
        Line 3:   header row starting with 'Ticker,Direction,...'
        Line 4+:  trade rows

    Trade row columns:
        0: Ticker            10: Trim1 Price       18: Trim3 Date
        1: Direction         11: Trim1 Qty         19: Trim3 Price
        2: Sector            12: Trim1 Type        20: Trim3 Qty
        3: Entry Date        13: Trim2 Date        21: Trim3 Type
        4: Entry Price       14: Trim2 Price
        5: Original Qty      15: Trim2 Qty
        6: Current Qty       16: Trim2 Type
        7: Stop Price        17: Trim3 Date
        8: Closed (YES/NO)
        9: Trim1 Date

    Skips malformed rows silently. For production, log them instead.
    """
    trades: list[Trade] = []
    starting_capital = 0.0

    with open(path) as f:
        for row in csv.reader(f):
            if not row:
                continue
            if row[0] == "_meta" and len(row) > 2 and row[1] == "startingCapital":
                starting_capital = float(row[2])
                continue
            if row[0].startswith("_meta") or row[0] == "Ticker":
                continue
            try:
                t = Trade(
                    ticker=row[0],
                    direction=row[1],                    # type: ignore
                    sector=row[2],
                    entry_date=_parse_date(row[3]),       # type: ignore
                    entry_price=float(row[4]),
                    orig_qty=int(row[5]),
                    curr_qty=int(row[6]),
                    stop=float(row[7]) if row[7] else None,
                    closed=(row[8] == "YES"),
                )
                # Up to 3 trims
                for i in range(3):
                    b = 9 + i * 4
                    if b + 1 >= len(row):
                        break
                    d = _parse_date(row[b])
                    if d and row[b + 1]:
                        t.trims.append(Trim(
                            date=d,
                            price=float(row[b + 1]),
                            qty=int(row[b + 2]) if row[b + 2] else 0,
                            type=row[b + 3] if len(row) > b + 3 else "",
                        ))
                trades.append(t)
            except (ValueError, IndexError):
                continue

    return trades, starting_capital


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # 1. Load trades from CSV
    trades, start_cap = parse_csv("portfolio_2026-05-21.csv")
    print(f"Loaded {len(trades)} trades, starting capital ${start_cap:,.0f}")

    # 2. Compute full report
    report, curve = compute_report(
        trades,
        starting_capital=start_cap,
        start_date=date(2026, 1, 2),
        end_date=date(2026, 5, 21),
    )

    print(f"\n--- Headline ---")
    print(f"Return:        {report.return_pct * 100:+.2f}%")
    print(f"Win rate:      {report.win_rate * 100:.1f}%")
    print(f"Profit factor: {report.profit_factor:.2f}")
    print(f"Expectancy:    ${report.expectancy:,.0f}/trade")
    print(f"Max DD:        {report.max_dd.drawdown_pct * 100:.2f}% "
          f"({curve[report.max_dd.peak_idx].date} → {curve[report.max_dd.trough_idx].date})")
    print(f"Sharpe:        {report.sharpe:.2f}")
    print(f"Sortino:       {report.sortino:.2f}")

    print(f"\n--- Exit Styles ---")
    for style, stats in sorted(report.exit_styles.items(),
                                key=lambda x: x[1]["avg_pnl"], reverse=True):
        print(f"  {style:<10} n={stats['count']:>3}  "
              f"avg=${stats['avg_pnl']:>8,.0f}/trade  "
              f"total=${stats['total_pnl']:>10,.0f}")

    # 3. Portfolio heat (requires open positions + current market prices)
    open_trades = [t for t in trades if not t.closed]
    current_prices = {
        "ALAB": 287.48, "NBIS": 193.00, "BE": 284.65, "HD": 310.58,
        "DOCN": 150.02, "DDOG": 208.82, "CGNX": 63.37, "ACMR": 65.00,
        "GLW": 180.66, "PL": 40.98, "NOWL": 5.16, "CLSK": 14.69,
    }
    heat = portfolio_heat(open_trades, current_prices, report.ending_equity)

    print(f"\n--- Portfolio Heat ---")
    print(f"Open heat:     ${heat.open_heat_usd:>10,.0f}  "
          f"({heat.open_heat_pct * 100:.2f}%, {heat.status})")
    print(f"Initial heat:  ${heat.initial_heat_usd:>10,.0f}  "
          f"({heat.initial_heat_pct * 100:.2f}%)")
    print(f"Top contributors:")
    for ticker, h in heat.by_position[:5]:
        print(f"  {ticker:<6} ${h:>10,.0f}")

    # 4. Pre-trade check
    ok, reason = can_open_new_position(
        heat, proposed_risk_usd=4500, account_equity=report.ending_equity
    )
    print(f"\n--- Pre-trade check (proposed $4,500 risk) ---")
    print(f"Allowed: {ok}\nReason: {reason}")

    # 5. Diagnostic: revenge trade clusters
    clusters = revenge_trade_clusters(trades, window_days=30, min_stops=2)
    print(f"\n--- Revenge trade clusters (>= 2 stop-outs in 30 days) ---")
    for ticker, cluster in clusters[:5]:
        total = sum(realized_pnl(t) for t in cluster)
        print(f"  {ticker}: {len(cluster)} stops, total ${total:,.0f}")

    # 6. Diagnostic: panic trim leak
    n, total_leak, top_leaks = panic_trim_summary(trades)
    print(f"\n--- Panic-trim leak ---")
    print(f"{n} winning trades trimmed into weakness, total leak ${total_leak:,.0f}")
    for t, leak in top_leaks[:5]:
        print(f"  {t.ticker} {t.direction} {t.entry_date}: "
              f"realized ${realized_pnl(t):,.0f}, left ${leak:,.0f} on table")
