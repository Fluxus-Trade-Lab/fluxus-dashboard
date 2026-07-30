#!/usr/bin/env python3
"""Performance Review engine — 交易复盘引擎.

Parses a portfolio CSV export (the "Fluxus Portfolio" Stock-Trades format with
Trim1/2/3 legs) of CLOSED trades and produces a bilingual (EN metrics + 中文
commentary) review as Markdown + JSON.

Cadence 节奏:
    * monthly  每月  — light: one month's realized P&L + that month's trades
    * h1 / annual  半年 / 全年 — deep: full breakdowns, R-distribution, leaks

Usage:
    # Full deep review of the whole file (auto date range in the title)
    python pipeline/portfolio/performance_review.py --csv data/portfolio/portfolio_2026-07-26.csv --period h1

    # A single month (re-export the cumulative CSV each month, then:)
    python pipeline/portfolio/performance_review.py --csv <latest.csv> --period monthly --month 2026-08

    # Everything (monthly sections + deep review) in one file
    python pipeline/portfolio/performance_review.py --csv <latest.csv> --period all

Design notes:
    * Realized P&L is attributed at the LEG level to the trim/exit date, so a
      trade trimmed across two months splits its P&L into the right months.
    * Per-trade R uses the Initial Stop: risk = |entry - initial_stop| * qty.
    * Longs: pnl = (exit - entry) * qty.  Shorts: pnl = (entry - exit) * qty.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt

from pipeline.marketcal import market_today
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field, asdict

DEFAULT_CAPITAL = 1_000_000


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
@dataclass
class Leg:
    date: str          # YYYY-MM-DD
    price: float
    qty: float
    kind: str          # trim_1_3 / trim_1_5 / trim_1_2 / sell_rest


@dataclass
class Trade:
    ticker: str
    direction: str     # long / short
    sector: str
    entry_date: str    # YYYY-MM-DD
    entry: float
    orig_qty: float
    initial_stop: float | None
    legs: list[Leg] = field(default_factory=list)

    # computed
    pnl: float = 0.0
    risk: float | None = None
    R: float | None = None
    exit_date: str = ""
    hold_days: int | None = None
    avg_exit: float | None = None

    def compute(self) -> None:
        pnl = 0.0
        exit_qty = 0.0
        exit_val = 0.0
        for lg in self.legs:
            if self.direction == "long":
                pnl += (lg.price - self.entry) * lg.qty
            else:
                pnl += (self.entry - lg.price) * lg.qty
            exit_qty += lg.qty
            exit_val += lg.price * lg.qty
        self.pnl = pnl
        self.avg_exit = (exit_val / exit_qty) if exit_qty else None
        if self.initial_stop is not None and self.entry is not None:
            rps = abs(self.entry - self.initial_stop)
            self.risk = rps * self.orig_qty if self.orig_qty else None
            self.R = (self.pnl / self.risk) if (self.risk and self.risk > 0) else None
        self.exit_date = self.legs[-1].date if self.legs else self.entry_date
        try:
            self.hold_days = (
                dt.date.fromisoformat(self.exit_date) - dt.date.fromisoformat(self.entry_date)
            ).days
        except ValueError:
            self.hold_days = None

    def leg_pnl(self, lg: Leg) -> float:
        if self.direction == "long":
            return (lg.price - self.entry) * lg.qty
        return (self.entry - lg.price) * lg.qty


def _num(x: str | None) -> float | None:
    if x is None:
        return None
    x = x.strip()
    if not x:
        return None
    try:
        return float(x)
    except ValueError:
        return None


def parse_csv(path: str) -> tuple[list[Trade], dict]:
    meta = {"startingCapital": DEFAULT_CAPITAL, "exportDate": None}
    trades: list[Trade] = []
    header: list[str] | None = None
    with open(path, newline="") as f:
        for row in csv.reader(f):
            if not row:
                continue
            if row[0] == "_meta":
                key, val = row[1], row[2]
                if key == "startingCapital":
                    meta["startingCapital"] = float(val)
                else:
                    meta[key] = val
                continue
            if row[0] == "Ticker":
                header = row
                continue
            if header is None:
                continue
            d = dict(zip(header, row))
            legs: list[Leg] = []
            for i in (1, 2, 3):
                dd = (d.get(f"Trim{i} Date", "") or "")[:10]
                pp = _num(d.get(f"Trim{i} Price"))
                qq = _num(d.get(f"Trim{i} Qty"))
                if pp is not None and qq:
                    legs.append(Leg(dd, pp, qq, d.get(f"Trim{i} Type", "")))
            t = Trade(
                ticker=d["Ticker"],
                direction=d["Direction"],
                sector=d.get("Sector", "Unknown") or "Unknown",
                entry_date=(d["Entry Date"] or "")[:10],
                entry=_num(d["Entry Price"]),
                orig_qty=_num(d["Original Qty"]) or 0.0,
                initial_stop=_num(d.get("Initial Stop")),
                legs=legs,
            )
            t.compute()
            trades.append(t)
    return trades, meta


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def overall_stats(trades: list[Trade], capital: float) -> dict:
    total = sum(t.pnl for t in trades)
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    flat = [t for t in trades if t.pnl == 0]
    gw = sum(t.pnl for t in wins)
    gl = sum(t.pnl for t in losses)
    Rs = [t.R for t in trades if t.R is not None]
    hds = [t.hold_days for t in trades if t.hold_days is not None]
    return {
        "capital": capital,
        "n": len(trades),
        "total_pnl": total,
        "return_pct": total / capital * 100 if capital else None,
        "ending_equity": capital + total,
        "wins": len(wins),
        "losses": len(losses),
        "flat": len(flat),
        "win_rate": len(wins) / len(trades) * 100 if trades else None,
        "gross_win": gw,
        "gross_loss": gl,
        "profit_factor": gw / abs(gl) if gl else None,
        "avg_win": gw / len(wins) if wins else None,
        "avg_loss": gl / len(losses) if losses else None,
        "payoff": (gw / len(wins)) / abs(gl / len(losses)) if wins and losses else None,
        "expectancy": total / len(trades) if trades else None,
        "avg_R": sum(Rs) / len(Rs) if Rs else None,
        "sum_R": sum(Rs) if Rs else None,
        "avg_hold_days": sum(hds) / len(hds) if hds else None,
        "max_drawdown": max_drawdown(trades, capital),
    }


def max_drawdown(trades: list[Trade], capital: float) -> dict:
    """Max drawdown on the REALIZED equity curve, marked END-OF-DAY.

    Realized-only understates the true (mark-to-market) drawdown — it steps only
    when a trade closes. Aggregating per day (not per leg) removes the arbitrary
    within-day leg-ordering dependence the old version had. See mtm.py for the
    reporting-standard mark-to-market drawdown.
    """
    daily: dict[str, float] = defaultdict(float)
    for t in trades:
        for lg in t.legs:
            daily[lg.date] += t.leg_pnl(lg)
    eq = capital
    peak = capital
    peak_date = None
    mdd = 0.0
    mdd_pct = 0.0
    trough_date = None
    for d in sorted(daily):
        eq += daily[d]
        if eq > peak:
            peak = eq
            peak_date = d
        dd = eq - peak
        if dd < mdd:
            mdd = dd
            mdd_pct = dd / peak * 100 if peak else 0.0
            trough_date = d
    return {"amount": mdd, "pct": mdd / capital * 100 if capital else None,
            "pct_of_peak": mdd_pct, "date": trough_date, "peak_date": peak_date,
            "basis": "realized EOD"}


def monthly_pnl(trades: list[Trade]) -> dict[str, dict]:
    """Realized P&L per calendar month (leg-level attribution)."""
    pnl = defaultdict(float)
    closes = defaultdict(int)
    for t in trades:
        for lg in t.legs:
            pnl[lg.date[:7]] += t.leg_pnl(lg)
        closes[t.exit_date[:7]] += 1
    out = {}
    for m in sorted(set(pnl) | set(closes)):
        out[m] = {"pnl": pnl.get(m, 0.0), "closes": closes.get(m, 0)}
    return out


def by_key(trades: list[Trade], key) -> list[tuple]:
    agg = defaultdict(lambda: {"pnl": 0.0, "n": 0, "wins": 0})
    for t in trades:
        k = key(t)
        agg[k]["pnl"] += t.pnl
        agg[k]["n"] += 1
        if t.pnl > 0:
            agg[k]["wins"] += 1
    return sorted(agg.items(), key=lambda kv: -kv[1]["pnl"])


def r_distribution(trades: list[Trade]) -> dict[str, int]:
    buckets = {"<= -2R": 0, "-2R..-1R": 0, "-1R..0": 0, "0..1R": 0, "1R..2R": 0, "2R..3R": 0, ">= 3R": 0}
    for t in trades:
        if t.R is None:
            continue
        r = t.R
        if r <= -2:
            buckets["<= -2R"] += 1
        elif r <= -1:
            buckets["-2R..-1R"] += 1
        elif r < 0:
            buckets["-1R..0"] += 1
        elif r < 1:
            buckets["0..1R"] += 1
        elif r < 2:
            buckets["1R..2R"] += 1
        elif r < 3:
            buckets["2R..3R"] += 1
        else:
            buckets[">= 3R"] += 1
    return buckets


def rule_break_watch(trades: list[Trade], avg_hold: float) -> list[Trade]:
    """Losing trades held far beyond the average hold — likely cut-rule breaks."""
    flags = [t for t in trades if t.pnl < 0 and t.hold_days is not None
             and t.hold_days > max(3 * avg_hold, 30) and (t.R is None or t.R <= -1.5)]
    return sorted(flags, key=lambda t: t.pnl)[:8]


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def money(x) -> str:
    if x is None:
        return "—"
    return f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}"


def pct(x) -> str:
    return "—" if x is None else f"{x:+.1f}%"


def render_deep(trades: list[Trade], meta: dict, title: str, mtm: dict | None = None) -> str:
    cap = meta["startingCapital"]
    s = overall_stats(trades, cap)
    mo = monthly_pnl(trades)
    L: list[str] = []
    A = L.append

    A(f"# {title}\n")
    A(f"*Generated {market_today().isoformat()} · source `{os.path.basename(meta.get('_csv',''))}` "
      f"· {s['n']} closed trades*\n")

    # Headline
    A("## 概览 / Headline\n")
    A(f"**${cap:,.0f} → {money(s['ending_equity'])} · {pct(s['return_pct'])}**\n")
    A("| Metric | Value | 解读 |")
    A("|---|---|---|")
    A(f"| Net realized P&L 净已实现盈亏 | **{money(s['total_pnl'])}** | {pct(s['return_pct'])} |")
    A(f"| Closed trades 已平仓 | {s['n']} | 均持仓 {s['avg_hold_days']:.1f} 天 |")
    A(f"| Win rate 胜率 | **{s['win_rate']:.1f}%** | {'低胜率' if s['win_rate'] < 50 else '高胜率'} |")
    A(f"| Payoff 盈亏比 | **{s['payoff']:.2f}×** | 均盈 / 均亏 |")
    A(f"| Profit factor 利润因子 | **{s['profit_factor']:.2f}** | 每亏 $1 赚 ${s['profit_factor']:.2f} |")
    A(f"| Expectancy 期望值 | **{money(s['expectancy'])}/trade** | {s['avg_R']:+.2f}R 均 |")
    A(f"| Total R 累计 R | **{s['sum_R']:+.1f}R** | |")
    A(f"| Avg win / loss 均盈/均亏 | {money(s['avg_win'])} / {money(s['avg_loss'])} | |")
    dd = s["max_drawdown"]
    if mtm and mtm.get("drawdown", {}).get("amount"):
        md = mtm["drawdown"]
        A(f"| **Max drawdown 最大回撤 (MTM 标准)** | **{money(md['amount'])} "
          f"({md['pct']:.1f}% of peak)** | mark-to-market 逐日盯市；峰 {md['peak_date']}→谷 {md['trough_date']} |")
        A(f"| Max drawdown (realized floor 已实现) | {money(dd['amount'])} ({dd['pct_of_peak']:.1f}% of peak) | 仅平仓口径,偏乐观 |")
    else:
        A(f"| Max drawdown 最大回撤 (realized EOD 已实现) | **{money(dd['amount'])} "
          f"({dd['pct_of_peak']:.1f}% of peak)** | 至 {dd['date']} · MTM 见下 / needs prices |")
    A("")

    # Mark-to-market drawdown & risk ratios (the reporting standard)
    if mtm and mtm.get("risk"):
        r = mtm["risk"]
        md = mtm["drawdown"]
        A("## 盯市回撤与风险比率 / Mark-to-market drawdown & risk\n")
        A("*逐日盯市权益曲线(现金+持仓按当日收盘价,split 用成交价锚定校正)—— 这是对外/机构口径的回撤标准。*\n")
        A("| Metric | Value |")
        A("|---|---|")
        A(f"| Peak equity 峰值权益 | {money(r.get('peak_equity'))} (+{r.get('peak_return_pct', 0):.0f}%) |")
        A(f"| **Max drawdown 最大回撤** | **{money(md['amount'])} ({md['pct']:.1f}% of peak)** |")
        A(f"| Drawdown window 回撤区间 | {md['peak_date']} → {md['trough_date']} |")
        A(f"| Sharpe | {r['sharpe']:.2f} |" if r.get('sharpe') else "| Sharpe | — |")
        A(f"| Sortino | {r['sortino']:.2f} |" if r.get('sortino') else "| Sortino | — |")
        A(f"| Calmar | {r['calmar']:.2f} |" if r.get('calmar') else "| Calmar | — |")
        A(f"| Ann. return (CAGR) 年化 | {r['cagr']*100:.1f}% |" if r.get('cagr') is not None else "| CAGR | — |")
        A(f"| Ann. volatility 年化波动 | {r['vol_ann']*100:.1f}% |" if r.get('vol_ann') is not None else "")
        A("")

    # Monthly
    A("## 月度曲线 / Monthly curve\n")
    A("| Month | P&L | Return | Closes | Equity |")
    A("|---|---|---|---|---|")
    eq = cap
    for m, d in mo.items():
        eq += d["pnl"]
        A(f"| {m} | {money(d['pnl'])} | {d['pnl']/cap*100:+.1f}% | {d['closes']} | ${eq:,.0f} |")
    A("")

    # Direction
    A("## 方向 / By direction\n")
    A("| Dir | n | P&L | Win% |")
    A("|---|---|---|---|")
    for k, v in by_key(trades, lambda t: t.direction):
        A(f"| {k} | {v['n']} | {money(v['pnl'])} | {v['wins']/v['n']*100:.0f}% |")
    A("")

    # R distribution
    A("## R 分布 / R-multiple distribution\n")
    rd = r_distribution(trades)
    A("| Bucket | Count |")
    A("|---|---|")
    for b, c in rd.items():
        A(f"| {b} | {c} |")
    A("")

    # Best / worst tickers
    A("## 标的贡献 / By ticker\n")
    bt = by_key(trades, lambda t: t.ticker)
    A("**Top 10 winners**\n")
    A("| Ticker | P&L | Trades | Win% |")
    A("|---|---|---|---|")
    for k, v in bt[:10]:
        A(f"| {k} | {money(v['pnl'])} | {v['n']} | {v['wins']/v['n']*100:.0f}% |")
    A("\n**Bottom 10 (leaks 漏点)**\n")
    A("| Ticker | P&L | Trades | Win% |")
    A("|---|---|---|---|")
    for k, v in bt[-10:]:
        A(f"| {k} | {money(v['pnl'])} | {v['n']} | {v['wins']/v['n']*100:.0f}% |")
    A("")

    # Best / worst single trades
    st = sorted(trades, key=lambda t: -t.pnl)
    A("## 单笔极值 / Best & worst trades\n")
    A("| P&L | Ticker | Dir | Entry→Exit | R | Hold |")
    A("|---|---|---|---|---|---|")
    for t in st[:6]:
        A(f"| {money(t.pnl)} | {t.ticker} | {t.direction} | {t.entry_date}→{t.exit_date} "
          f"| {t.R:+.1f}R | {t.hold_days}d |")
    A("| … | | | | | |")
    for t in st[-6:]:
        rr = f"{t.R:+.1f}R" if t.R is not None else "—"
        A(f"| {money(t.pnl)} | {t.ticker} | {t.direction} | {t.entry_date}→{t.exit_date} "
          f"| {rr} | {t.hold_days}d |")
    A("")

    # Rule-break watch
    flags = rule_break_watch(trades, s["avg_hold_days"] or 7)
    A("## 纪律预警 / Rule-break watch\n")
    if flags:
        A(f"*亏损单里持仓远超均值({s['avg_hold_days']:.0f}天)且 ≤ -1.5R 的——多半是没砍在止损上。*\n")
        A("| Ticker | P&L | R | Hold | Entry→Exit |")
        A("|---|---|---|---|---|")
        for t in flags:
            rr = f"{t.R:+.1f}R" if t.R is not None else "—"
            A(f"| {t.ticker} | {money(t.pnl)} | {rr} | {t.hold_days}d | {t.entry_date}→{t.exit_date} |")
    else:
        A("*无明显纪律破坏。/ No obvious cut-rule breaks.*")
    A("")

    # Graded narrative (offense / defense / trim / leverage / capital efficiency / style)
    try:
        try:
            from . import analysis as _an
        except ImportError:
            import analysis as _an  # type: ignore
        A(_an.render_analysis(trades, cap, s["total_pnl"],
                              equity_by_date=(mtm or {}).get("equity_by_date")))
    except Exception as e:  # noqa: BLE001 — narrative must never break the review
        A(f"*（评估段落生成失败 / analysis section unavailable: {type(e).__name__}）*\n")

    return "\n".join(L)


def render_monthly(trades: list[Trade], meta: dict, month: str) -> str:
    """Light single-month review. `month` = 'YYYY-MM'."""
    cap = meta["startingCapital"]
    # month P&L via leg attribution
    mp = 0.0
    for t in trades:
        for lg in t.legs:
            if lg.date[:7] == month:
                mp += t.leg_pnl(lg)
    closed = [t for t in trades if t.exit_date[:7] == month]
    opened = [t for t in trades if t.entry_date[:7] == month]
    wins = [t for t in closed if t.pnl > 0]
    losses = [t for t in closed if t.pnl < 0]

    L: list[str] = []
    A = L.append
    A(f"# 月度复盘 {month} / Monthly Review\n")
    A(f"*Generated {market_today().isoformat()} · leg-attributed realized P&L*\n")
    A(f"**Realized this month 本月已实现:** {money(mp)}  ({mp/cap*100:+.2f}% on ${cap:,.0f})\n")
    A(f"- Trades closed 平仓: {len(closed)}  ·  opened 开仓: {len(opened)}")
    if closed:
        wr = len(wins) / len(closed) * 100
        A(f"- Win rate 胜率: {wr:.0f}%  ·  wins {len(wins)} / losses {len(losses)}")
    A("")

    if closed:
        st = sorted(closed, key=lambda t: -t.pnl)
        A("## 本月平仓单 / Trades closed this month\n")
        A("| P&L | Ticker | Dir | Entry→Exit | R | Hold |")
        A("|---|---|---|---|---|---|")
        for t in st:
            rr = f"{t.R:+.1f}R" if t.R is not None else "—"
            A(f"| {money(t.pnl)} | {t.ticker} | {t.direction} | {t.entry_date}→{t.exit_date} "
              f"| {rr} | {t.hold_days}d |")
        A("")
        # quick leaks
        worst = st[-3:]
        A("## 复盘要点 / Notes\n")
        A(f"- 最大贡献 Top winner: **{st[0].ticker}** {money(st[0].pnl)}"
          + (f" ({st[0].R:+.1f}R)" if st[0].R is not None else ""))
        if worst and worst[0].pnl < 0:
            A(f"- 最大漏点 Worst: **{worst[0].ticker}** {money(worst[0].pnl)}"
              + (f" ({worst[0].R:+.1f}R)" if worst[0].R is not None else ""))
        A("- 填空 / fill in: 触发信号对不对?止损执行没?有没有该拿住却砍早 / 该砍却拖?")
        A("")
        # Light graded narrative on this month's closed trades (no network fetch).
        try:
            try:
                from . import analysis as _an
            except ImportError:
                import analysis as _an  # type: ignore
            A(_an.render_analysis(closed, cap, sum(t.pnl for t in closed),
                                  include_characteristics=False))
        except Exception:  # noqa: BLE001
            pass
    A("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def latest_csv(portfolio_dir: str) -> str | None:
    files = [f for f in os.listdir(portfolio_dir) if f.startswith("portfolio_") and f.endswith(".csv")]
    if not files:
        return None
    return os.path.join(portfolio_dir, sorted(files)[-1])


def compute_mtm(trades: list[Trade], meta: dict) -> dict | None:
    """Fetch prices + build the mark-to-market curve, drawdown, risk ratios.

    Returns None if the mtm module / prices are unavailable (review still renders
    with the realized figure). Never raises — a review must not depend on network.
    """
    try:
        from . import mtm as _mtm
    except ImportError:  # run as a script, not a package
        import mtm as _mtm  # type: ignore
    try:
        cap = meta["startingCapital"]
        tickers = sorted({t.ticker for t in trades})
        dmin = min(t.entry_date for t in trades)
        dmax = max((lg.date for t in trades for lg in t.legs), default=dmin)
        # pad the window a few days each side for weekend/holiday lookups
        start = (dt.date.fromisoformat(dmin) - dt.timedelta(days=10)).isoformat()
        end = (dt.date.fromisoformat(dmax) + dt.timedelta(days=3)).isoformat()
        prices = _mtm.fetch_prices(tickers, start, end)
        curve = _mtm.build_mtm_curve(trades, prices, cap)
        if not curve:
            return None
        return {
            "drawdown": _mtm.drawdown(curve),
            "risk": _mtm.risk_ratios(curve, cap),
            "final_equity": curve[-1][1],
            "points": len(curve),
            "equity_by_date": {d: v for d, v in curve},
        }
    except Exception:  # noqa: BLE001 — degrade gracefully to realized-only
        return None


def _capital_efficiency_json(trades: list[Trade], cap: float, mtm: dict | None = None) -> dict | None:
    """Capital-efficiency block for the JSON output (return on deployed, etc.)."""
    try:
        try:
            from . import analysis as _an
        except ImportError:
            import analysis as _an  # type: ignore
        total = sum(t.pnl for t in trades)
        return _an.capital_efficiency(trades, cap, total, (mtm or {}).get("equity_by_date"))
    except Exception:  # noqa: BLE001
        return None


def build_json(trades: list[Trade], meta: dict, mtm: dict | None = None) -> dict:
    cap = meta["startingCapital"]
    return {
        "export_date": meta.get("exportDate"),
        "source_csv": os.path.basename(meta.get("_csv", "")),
        "generated": market_today().isoformat(),
        "overall": overall_stats(trades, cap),
        "capital_efficiency": _capital_efficiency_json(trades, cap, mtm),
        "mtm": mtm,
        "monthly": monthly_pnl(trades),
        "by_direction": {k: v for k, v in by_key(trades, lambda t: t.direction)},
        "by_ticker": {k: v for k, v in by_key(trades, lambda t: t.ticker)},
        "r_distribution": r_distribution(trades),
    }


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    portfolio_dir = os.path.join(repo, "data", "portfolio")

    ap = argparse.ArgumentParser(description="Trading performance review engine")
    ap.add_argument("--csv", default=None, help="portfolio CSV export (default: latest in data/portfolio)")
    ap.add_argument("--period", choices=["monthly", "h1", "annual", "all"], default="h1")
    ap.add_argument("--month", default=None, help="YYYY-MM for --period monthly")
    ap.add_argument("--out", default=os.path.join(portfolio_dir, "reviews"))
    ap.add_argument("--label", default=None, help="output file stem")
    ap.add_argument("--no-mtm", action="store_true", help="skip mark-to-market (no network fetch)")
    args = ap.parse_args()

    csv_path = args.csv or latest_csv(portfolio_dir)
    if not csv_path or not os.path.exists(csv_path):
        raise SystemExit(f"No CSV found (looked in {portfolio_dir}). Pass --csv.")

    trades, meta = parse_csv(csv_path)
    meta["_csv"] = csv_path
    os.makedirs(args.out, exist_ok=True)

    # date range for titles / labels
    dates = [t.entry_date for t in trades] + [t.exit_date for t in trades]
    dmin, dmax = min(dates), max(dates)

    # Mark-to-market (network fetch) — only for deep reviews, unless disabled.
    mtm = None
    if not args.no_mtm and args.period != "monthly":
        print("· fetching prices for mark-to-market drawdown …")
        mtm = compute_mtm(trades, meta)
        print("  MTM " + ("ready" if mtm else "unavailable → realized-only"))

    if args.period == "monthly":
        month = args.month or dmax[:7]
        md = render_monthly(trades, meta, month)
        stem = args.label or f"monthly_{month}"
        title_period = month
    else:
        period_name = {"h1": "H1", "annual": "Annual", "all": "Full"}[args.period]
        title = f"{period_name} Review · 交易复盘 ({dmin} → {dmax})"
        md = render_deep(trades, meta, title, mtm)
        stem = args.label or f"{args.period}_{dmin}_{dmax}"
        title_period = f"{dmin}→{dmax}"
        if args.period == "all":
            # append monthly sections
            months = sorted({lg.date[:7] for t in trades for lg in t.legs})
            md += "\n\n---\n\n# 逐月明细 / Month-by-month\n"
            for m in months:
                md += "\n" + render_monthly(trades, meta, m) + "\n---\n"

    md_path = os.path.join(args.out, f"{stem}.md")
    json_path = os.path.join(args.out, f"{stem}.json")
    with open(md_path, "w") as f:
        f.write(md)
    with open(json_path, "w") as f:
        json.dump(build_json(trades, meta, mtm), f, indent=2, default=str)

    print(f"✓ Review ({args.period}, {title_period}) written:")
    print(f"  {md_path}")
    print(f"  {json_path}")


if __name__ == "__main__":
    main()
