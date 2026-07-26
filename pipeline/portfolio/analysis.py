#!/usr/bin/env python3
"""Graded narrative analysis for the performance review.

Evaluates HOW the trader plays, not just the P&L — offense, defense, trimming
into strength, leverage/margin use, capital efficiency, and the stock
characteristics traded (sector / ATR% / beta). Renders a bilingual (EN + 中文)
narrative with a letter grade per dimension.

Consumes the `Trade` objects from performance_review.py. Stock characteristics
(ATR%, beta) need daily OHLC — fetched via yfinance and cached; degrades to
"n/a" if unavailable so a review never depends on the network.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

# Known leveraged / inverse / single-stock-leverage ETFs seen in this book.
LEVERAGED = {
    "SOXL", "SOXS", "TQQQ", "SQQQ", "TZA", "TNA", "NAIL", "NVDL", "FNGU", "FNGD",
    "AMZU", "METU", "CWEB", "AMDL", "TSLL", "NVDU", "SPXL", "SPXS", "UPRO", "SOLS",
    "OKLL", "NVDX", "MSFU", "GGLL", "AMUU", "SNXX", "NEBX", "AMDU", "TSLR", "CONL",
    "MSTX", "MSTU", "BITX", "ETHU", "USD", "SOXX",
}


def money(x) -> str:
    if x is None:
        return "—"
    return f"${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}"


def _grade(score: float) -> str:
    """0..1 → letter grade."""
    for cut, g in [(0.9, "A+"), (0.8, "A"), (0.7, "A-"), (0.6, "B+"),
                   (0.5, "B"), (0.4, "B-"), (0.3, "C+"), (0.2, "C"), (0.0, "C-")]:
        if score >= cut:
            return g
    return "C-"


# --------------------------------------------------------------------------- #
# Dimension computations
# --------------------------------------------------------------------------- #
def offense(trades) -> dict:
    wins = [t for t in trades if t.pnl > 0]
    gross_win = sum(t.pnl for t in wins) or 1
    st = sorted(trades, key=lambda t: -t.pnl)
    top5 = st[:5]
    top5_share = sum(t.pnl for t in top5) / gross_win
    ge3R = [t for t in trades if t.R is not None and t.R >= 3]
    ge5R = [t for t in trades if t.R is not None and t.R >= 5]
    win_holds = [t.hold_days for t in wins if t.hold_days is not None]
    loss_holds = [t.hold_days for t in trades if t.pnl < 0 and t.hold_days is not None]
    avg_win_hold = sum(win_holds) / len(win_holds) if win_holds else 0
    avg_loss_hold = sum(loss_holds) / len(loss_holds) if loss_holds else 0
    avg_win_R = sum(t.R for t in wins if t.R is not None) / max(1, len([t for t in wins if t.R is not None]))
    # Momentum: winners held LONGER than losers (letting winners run) + big right tail.
    run_ratio = avg_win_hold / avg_loss_hold if avg_loss_hold else 0
    score = min(1.0, 0.5 * min(run_ratio / 1.5, 1) + 0.5 * min(len(ge3R) / max(1, len(trades)) / 0.12, 1))
    return {
        "top5": top5, "top5_share": top5_share, "n_ge3R": len(ge3R), "n_ge5R": len(ge5R),
        "avg_win_hold": avg_win_hold, "avg_loss_hold": avg_loss_hold, "run_ratio": run_ratio,
        "avg_win_R": avg_win_R, "grade": _grade(score), "score": score,
    }


def defense(trades) -> dict:
    losers = [t for t in trades if t.pnl < 0]
    with_R = [t for t in losers if t.R is not None]
    # Respected stop = loss not worse than ~-1.2R (stops honored, no blow-through).
    respected = [t for t in with_R if t.R >= -1.2]
    respect_rate = len(respected) / len(with_R) if with_R else 1.0
    blown = [t for t in with_R if t.R < -2]  # blew well past stop
    avg_loss_R = sum(t.R for t in with_R) / len(with_R) if with_R else 0
    worst = sorted(losers, key=lambda t: t.pnl)[:5]
    loss_holds = [t.hold_days for t in losers if t.hold_days is not None]
    avg_loss_hold = sum(loss_holds) / len(loss_holds) if loss_holds else 0
    # Good defense = high respect-rate, few blow-throughs, losers cut fast.
    score = min(1.0, 0.6 * respect_rate + 0.4 * (1 - min(len(blown) / max(1, len(with_R)) / 0.1, 1)))
    return {
        "respect_rate": respect_rate, "n_blown": len(blown), "avg_loss_R": avg_loss_R,
        "worst": worst, "avg_loss_hold": avg_loss_hold, "grade": _grade(score), "score": score,
    }


def trimming(trades) -> dict:
    """Scaling out / trimming into strength."""
    scaled = [t for t in trades if len(t.legs) >= 2]  # multiple exit legs
    scale_rate = len(scaled) / len(trades) if trades else 0
    # For winners that scaled: did earlier trims occur at HIGHER prices than entry
    # AND was the position let run (later legs even higher)? Count "into strength".
    into_strength = 0
    winners_scaled = [t for t in scaled if t.pnl > 0]
    for t in winners_scaled:
        prices = [lg.price for lg in t.legs]
        if t.direction == "long" and prices[0] > t.entry:
            into_strength += 1
        elif t.direction == "short" and prices[0] < t.entry:
            into_strength += 1
    into_rate = into_strength / len(winners_scaled) if winners_scaled else 0
    avg_legs = sum(len(t.legs) for t in trades) / len(trades) if trades else 0
    score = min(1.0, 0.5 * min(scale_rate / 0.5, 1) + 0.5 * into_rate)
    return {"scale_rate": scale_rate, "into_rate": into_rate, "avg_legs": avg_legs,
            "n_scaled": len(scaled), "grade": _grade(score), "score": score}


def leverage(trades, capital) -> dict:
    lev = [t for t in trades if t.ticker in LEVERAGED]
    lev_pnl = sum(t.pnl for t in lev)
    lev_share = len(lev) / len(trades) if trades else 0
    # Peak concurrent gross exposure (entry-cost notional of open positions).
    events = []
    for t in trades:
        notional = (t.entry or 0) * (t.orig_qty or 0)
        events.append((t.entry_date, notional))
        # position closes at last leg date → exposure removed then (approx, full size)
        exitd = t.legs[-1].date if t.legs else t.entry_date
        events.append((exitd, -notional))
    events.sort()
    cur = 0.0
    peak = 0.0
    peak_date = None
    for d, delta in events:
        cur += delta
        if cur > peak:
            peak = cur
            peak_date = d
    peak_gross_x = peak / capital if capital else 0
    return {"n_lev": len(lev), "lev_share": lev_share, "lev_pnl": lev_pnl,
            "peak_gross": peak, "peak_gross_x": peak_gross_x, "peak_date": peak_date}


def capital_efficiency(trades, capital, total_pnl) -> dict:
    # Average concurrent open positions across trading days.
    day_open = defaultdict(int)
    for t in trades:
        exitd = t.legs[-1].date if t.legs else t.entry_date
        d = dt.date.fromisoformat(t.entry_date)
        end = dt.date.fromisoformat(exitd)
        while d <= end:
            if d.weekday() < 5:
                day_open[d.isoformat()] += 1
            d += dt.timedelta(days=1)
    avg_concurrent = sum(day_open.values()) / len(day_open) if day_open else 0
    holds = [t.hold_days for t in trades if t.hold_days is not None]
    avg_hold = sum(holds) / len(holds) if holds else 0
    days_in_market = len(day_open)
    return {"avg_concurrent": avg_concurrent, "avg_hold": avg_hold,
            "pnl_per_trade": total_pnl / len(trades) if trades else 0,
            "pnl_per_day": total_pnl / days_in_market if days_in_market else 0,
            "days_in_market": days_in_market}


# --------------------------------------------------------------------------- #
# Stock characteristics (ATR% / beta / sector) — needs OHLC
# --------------------------------------------------------------------------- #
def fetch_ohlc(tickers, start, end, cache_path=".cache/analysis_ohlc.json"):
    import json
    import os
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except (ValueError, OSError):
            cache = {}
    need = [t for t in list(tickers) + ["SPY"] if t not in cache]
    if need:
        try:
            import warnings
            warnings.filterwarnings("ignore")
            import yfinance as yf
        except ImportError:
            return cache
        try:
            df = yf.download(need, start=start, end=end, auto_adjust=True,
                             group_by="ticker", progress=False, threads=True)
        except Exception:  # noqa: BLE001
            return cache
        for t in need:
            try:
                sub = df[t] if len(need) > 1 else df
                sub = sub.dropna()
                cache[t] = {
                    "date": [str(d.date()) for d in sub.index],
                    "high": [float(x) for x in sub["High"]],
                    "low": [float(x) for x in sub["Low"]],
                    "close": [float(x) for x in sub["Close"]],
                }
            except Exception:  # noqa: BLE001
                cache[t] = {"date": [], "high": [], "low": [], "close": []}
        try:
            os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
            json.dump(cache, open(cache_path, "w"))
        except OSError:
            pass
    return cache


def _atr_pct(o):
    """Mean true-range % over the series (a volatility proxy)."""
    h, l, c = o.get("high", []), o.get("low", []), o.get("close", [])
    if len(c) < 5:
        return None
    trs = []
    for i in range(1, len(c)):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        if c[i]:
            trs.append(tr / c[i])
    return 100 * sum(trs) / len(trs) if trs else None


def _beta(o, spy):
    c, sc = o.get("close", []), spy.get("close", [])
    dmap = {d: v for d, v in zip(o.get("date", []), c)}
    smap = {d: v for d, v in zip(spy.get("date", []), sc)}
    common = sorted(set(dmap) & set(smap))
    if len(common) < 10:
        return None
    r = [dmap[common[i]] / dmap[common[i - 1]] - 1 for i in range(1, len(common))]
    s = [smap[common[i]] / smap[common[i - 1]] - 1 for i in range(1, len(common))]
    n = len(s)
    ms = sum(s) / n
    mr = sum(r) / n
    var = sum((x - ms) ** 2 for x in s)
    cov = sum((r[i] - mr) * (s[i] - ms) for i in range(n))
    return cov / var if var else None


def characteristics(trades) -> dict:
    tickers = {t.ticker for t in trades}
    dmin = min(t.entry_date for t in trades)
    dmax = max((lg.date for t in trades for lg in t.legs), default=dmin)
    ohlc = fetch_ohlc(tickers, (dt.date.fromisoformat(dmin) - dt.timedelta(days=40)).isoformat(),
                      (dt.date.fromisoformat(dmax) + dt.timedelta(days=3)).isoformat())
    spy = ohlc.get("SPY", {})
    atr = {tk: _atr_pct(ohlc.get(tk, {})) for tk in tickers}
    beta = {tk: _beta(ohlc.get(tk, {}), spy) for tk in tickers} if spy else {}
    # trade-weighted averages
    a_vals = [atr[t.ticker] for t in trades if atr.get(t.ticker) is not None]
    b_vals = [beta.get(t.ticker) for t in trades if beta.get(t.ticker) is not None]
    # sector mix (from CSV; many may be Unknown)
    sec = defaultdict(lambda: [0, 0.0])
    for t in trades:
        sec[t.sector][0] += 1
        sec[t.sector][1] += t.pnl
    long_n = sum(1 for t in trades if t.direction == "long")
    return {
        "avg_atr": sum(a_vals) / len(a_vals) if a_vals else None,
        "avg_beta": sum(b_vals) / len(b_vals) if b_vals else None,
        "atr_cov": len(a_vals) / len(trades) if trades else 0,
        "sectors": sorted(sec.items(), key=lambda kv: -kv[1][0]),
        "long_pct": long_n / len(trades) * 100 if trades else 0,
        "n_lev_note": None,
    }


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render_analysis(trades, capital, total_pnl, include_characteristics=True) -> str:
    off = offense(trades)
    dfn = defense(trades)
    trm = trimming(trades)
    lev = leverage(trades, capital)
    cef = capital_efficiency(trades, capital, total_pnl)
    ch = characteristics(trades) if include_characteristics else None

    L = []
    A = L.append
    A("## 交易评估 / Trader Evaluation\n")
    A("*系统评分——这半年你打得如何(不只是赚多少)。/ Graded read on HOW you played.*\n")
    A("| Dimension 维度 | Grade | Read |")
    A("|---|---|---|")
    A(f"| 进攻 Offense | **{off['grade']}** | 右尾:top-5 trades = {off['top5_share']*100:.0f}% of gross win; "
      f"{off['n_ge3R']}×≥3R, {off['n_ge5R']}×≥5R; winners held {off['avg_win_hold']:.1f}d vs losers {off['avg_loss_hold']:.1f}d ({off['run_ratio']:.1f}× — 让利润奔跑) |")
    A(f"| 防守 Defense | **{dfn['grade']}** | 止损纪律:{dfn['respect_rate']*100:.0f}% of losers ≤1.2R; "
      f"{dfn['n_blown']} blew past 2R; avg loss {dfn['avg_loss_R']:+.2f}R, cut in {dfn['avg_loss_hold']:.1f}d |")
    A(f"| 加码/减仓 Trim into strength | **{trm['grade']}** | {trm['scale_rate']*100:.0f}% of trades scaled out "
      f"(avg {trm['avg_legs']:.1f} legs); {trm['into_rate']*100:.0f}% of scaled winners trimmed into green |")
    A(f"| 杠杆/保证金 Leverage | — | peak gross exposure {money(lev['peak_gross'])} = {lev['peak_gross_x']:.2f}× capital "
      f"({'margin used' if lev['peak_gross_x']>1.02 else 'no margin'}); leveraged-ETF trades {lev['n_lev']} ({lev['lev_share']*100:.0f}%), P&L {money(lev['lev_pnl'])} |")
    A(f"| 资金效率 Capital efficiency | — | avg {cef['avg_concurrent']:.0f} concurrent positions, {cef['avg_hold']:.1f}d hold; "
      f"{money(cef['pnl_per_trade'])}/trade, {money(cef['pnl_per_day'])}/day in market |")
    A("")

    # Best / worst case studies
    A("### 最佳 & 最差 / Best & worst trades\n")
    A("**Best (offense working):**\n")
    A("| P&L | Ticker | Dir | R | Hold | Entry→Exit |")
    A("|---|---|---|---|---|---|")
    for t in off["top5"]:
        rr = f"{t.R:+.1f}R" if t.R is not None else "—"
        A(f"| {money(t.pnl)} | {t.ticker} | {t.direction} | {rr} | {t.hold_days}d | {t.entry_date}→{t.exit_date} |")
    A("\n**Worst (defense tested):**\n")
    A("| P&L | Ticker | Dir | R | Hold | Entry→Exit |")
    A("|---|---|---|---|---|---|")
    for t in dfn["worst"]:
        rr = f"{t.R:+.1f}R" if t.R is not None else "—"
        A(f"| {money(t.pnl)} | {t.ticker} | {t.direction} | {rr} | {t.hold_days}d | {t.entry_date}→{t.exit_date} |")
    A("")

    if ch:
        A("### 交易风格画像 / What you like to trade\n")
        A(f"- **Direction 方向:** {ch['long_pct']:.0f}% long / {100-ch['long_pct']:.0f}% short")
        if ch["avg_atr"] is not None:
            A(f"- **Volatility 波动 (ATR%):** avg {ch['avg_atr']:.1f}%/day across names traded "
              f"— {'high-octane movers' if ch['avg_atr']>4 else 'moderate volatility'} (coverage {ch['atr_cov']*100:.0f}%)")
        if ch["avg_beta"] is not None:
            A(f"- **Beta vs SPY:** avg {ch['avg_beta']:.2f} — {'high-beta / aggressive' if ch['avg_beta']>1.3 else 'market-like'}")
        secs = [f"{s} ({v[0]})" for s, v in ch["sectors"][:6] if s != "Unknown"]
        if secs:
            A(f"- **Sectors 板块 (by count):** {', '.join(secs)}")
        unknown = next((v[0] for s, v in ch["sectors"] if s == "Unknown"), 0)
        if unknown:
            A(f"- *(sector unlabeled on {unknown} trades — tag them in the log for a sharper read)*")
        A("")

    # One-paragraph synthesis
    A("### 一句话总结 / Synthesis\n")
    A(f"*进攻 {off['grade']} · 防守 {dfn['grade']} · 减仓 {trm['grade']}.* "
      f"你的钱几乎全靠右尾({off['top5_share']*100:.0f}% 来自 5 笔),靠的是让赢家跑({off['run_ratio']:.1f}× 持仓时长)+ 快砍亏损"
      f"({dfn['avg_loss_hold']:.1f}天,{dfn['respect_rate']*100:.0f}% 守住止损). "
      f"You win by letting a few winners run huge and cutting losers fast — a momentum/right-tail engine, "
      f"{'leaning on leveraged ETFs' if lev['lev_share']>0.1 else 'mostly in cash equities'}, "
      f"{'using margin at peak' if lev['peak_gross_x']>1.02 else 'staying within capital'}.")
    A("")
    return "\n".join(L)
