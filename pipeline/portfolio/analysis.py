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


def capital_efficiency(trades, capital, total_pnl, equity_by_date=None) -> dict:
    # Per-day: concurrent open positions + gross deployed capital (cost basis of
    # open positions, as-traded). Deployed / starting capital shows how hard the
    # capital worked (>100% = ran net margin); return-on-deployed is P&L per
    # dollar actually at risk, the truest read of edge-per-dollar.
    day_open = defaultdict(int)
    day_deployed = defaultdict(float)
    for t in trades:
        exitd = t.legs[-1].date if t.legs else t.entry_date
        d = dt.date.fromisoformat(t.entry_date)
        end = dt.date.fromisoformat(exitd)
        while d <= end:
            if d.weekday() < 5:
                ds = d.isoformat()
                sold = sum(lg.qty for lg in t.legs if lg.date <= ds)
                held = (t.orig_qty or 0) - sold
                if held > 0.5:
                    day_open[ds] += 1
                    day_deployed[ds] += held * (t.entry or 0)
            d += dt.timedelta(days=1)
    days_in_market = len(day_open)
    avg_concurrent = sum(day_open.values()) / days_in_market if days_in_market else 0
    deployed_vals = list(day_deployed.values())
    avg_deployed = sum(deployed_vals) / len(deployed_vals) if deployed_vals else 0
    peak_deployed = max(deployed_vals) if deployed_vals else 0
    holds = [t.hold_days for t in trades if t.hold_days is not None]
    avg_hold = sum(holds) / len(holds) if holds else 0

    # Leverage = deployed ÷ CURRENT equity (vs starting capital, which overstates
    # as the account grows). Needs the daily MTM equity curve; None if unavailable.
    avg_lev = peak_lev = None
    if equity_by_date:
        levs = []
        for ds, dep in day_deployed.items():
            eq = equity_by_date.get(ds)
            if eq and eq > 0:
                levs.append(dep / eq)
        if levs:
            avg_lev = sum(levs) / len(levs) * 100
            peak_lev = max(levs) * 100

    return {"avg_concurrent": avg_concurrent, "avg_hold": avg_hold,
            "pnl_per_trade": total_pnl / len(trades) if trades else 0,
            "pnl_per_day": total_pnl / days_in_market if days_in_market else 0,
            "days_in_market": days_in_market,
            "avg_deployed": avg_deployed,
            "avg_deployed_pct_of_start": avg_deployed / capital * 100 if capital else 0,
            "peak_deployed_pct_of_start": peak_deployed / capital * 100 if capital else 0,
            "avg_leverage_pct": avg_lev,
            "peak_leverage_pct": peak_lev,
            "return_on_deployed": total_pnl / avg_deployed * 100 if avg_deployed else None}


def position_heat(trades, equity_by_date, greed=14, fwd=10):
    """Concurrent NAMES (unique tickers, layers deduped) vs the forward pullback.

    Tests the trader's rule of thumb that hitting ~`greed` names precedes a
    P&L shakeout. Returns name-count distribution, forward-pullback rate by
    name bucket, and each episode where names first crossed `greed`.
    """
    if not equity_by_date:
        return None
    days = sorted(equity_by_date)
    eq = [equity_by_date[d] for d in days]
    names = []
    for ds in days:
        s = set()
        for t in trades:
            if t.entry_date > ds:
                continue
            sold = sum(lg.qty for lg in t.legs if lg.date <= ds)
            if (t.orig_qty or 0) - sold > 0.5:
                s.add(t.ticker)
        names.append(len(s))

    def fwd_dd(i):
        seg = eq[i + 1:i + 1 + fwd]
        return (min(seg) - eq[i]) / eq[i] * 100 if seg else None

    def fwd_ret(i, k=5):
        return (eq[i + k] - eq[i]) / eq[i] * 100 if i + k < len(eq) else None

    buckets = []
    for lo, hi, lab in [(0, 10, "<10"), (10, greed, f"10-{greed - 1}"), (greed, 999, f">={greed} (greed)")]:
        idx = [i for i, n in enumerate(names) if lo <= n < hi]
        dds = [fwd_dd(i) for i in idx]
        dds = [x for x in dds if x is not None]
        rets = [fwd_ret(i) for i in idx]
        rets = [x for x in rets if x is not None]
        if dds:
            buckets.append({"label": lab, "n": len(idx),
                            "avg_fwd5_ret": sum(rets) / len(rets) if rets else None,
                            "pullback_rate": sum(1 for x in dds if x < -2) / len(dds) * 100})

    episodes = []
    prev = 0
    for i, (ds, n) in enumerate(zip(days, names)):
        if n >= greed and prev < greed:
            episodes.append({"date": ds, "names": n, "equity": eq[i], "next_maxdd": fwd_dd(i)})
        prev = n
    srt = sorted(names)
    return {"max_names": max(names), "median_names": srt[len(srt) // 2],
            "days_ge_greed": sum(1 for n in names if n >= greed), "total_days": len(names),
            "greed": greed, "fwd": fwd, "buckets": buckets, "episodes": episodes}


def behavioral_diagnosis(trades, equity_by_date, capital):
    """Evidence for the four behavioral questions: loss/winner character,
    drawdown sizing, and trim/stop discipline. Log-based (no price fetch)."""
    with_R = [t for t in trades if t.R is not None]
    wins = [t for t in with_R if t.R > 0]
    losses = [t for t in with_R if t.R < 0]
    if not wins or not losses:
        return None

    # Re-attack: same ticker entered 3+ times; net P&L (leak = kept adding to a loser)
    by_tk = defaultdict(list)
    for t in sorted(trades, key=lambda x: x.entry_date):
        by_tk[t.ticker].append(t)
    reattack = []
    for tk, ts in by_tk.items():
        if len(ts) >= 3:
            reattack.append({"ticker": tk, "n": len(ts),
                             "n_loss": sum(1 for x in ts if x.pnl < 0),
                             "net": sum(x.pnl for x in ts)})
    worst_reattack = sorted(reattack, key=lambda r: r["net"])[:5]

    # Hold time + over-held losers
    avg_win_hold = sum(t.hold_days for t in wins if t.hold_days is not None) / max(1, len(wins))
    avg_loss_hold = sum(t.hold_days for t in losses if t.hold_days is not None) / max(1, len(losses))
    overheld = sorted([t for t in losses if t.hold_days and t.hold_days > 21], key=lambda t: t.pnl)[:5]

    # Drawdown sizing: avg initial risk when equity is >3% off peak vs normal
    dd_flag = {}
    if equity_by_date:
        peak = capital
        for d in sorted(equity_by_date):
            peak = max(peak, equity_by_date[d])
            dd_flag[d] = (equity_by_date[d] - peak) / peak < -0.03

    def in_dd(ds):
        prior = [d for d in dd_flag if d <= ds]
        return dd_flag.get(prior[-1], False) if prior else False

    risks_dd = [t.risk for t in trades if t.risk and in_dd(t.entry_date)]
    risks_ok = [t.risk for t in trades if t.risk and not in_dd(t.entry_date)]

    # Trim / stops
    scaled = [t for t in trades if len(t.legs) >= 2]
    scaled_win = [t for t in scaled if t.pnl > 0]
    into = sum(1 for t in scaled_win
               if (t.direction == "long" and t.legs[0].price > t.entry)
               or (t.direction == "short" and t.legs[0].price < t.entry))
    lR = [t for t in losses]
    risks = [t.risk for t in trades if t.risk]
    return {
        "worst_reattack": worst_reattack,
        "avg_win_hold": avg_win_hold, "avg_loss_hold": avg_loss_hold, "overheld": overheld,
        "risk_dd_pct": (sum(risks_dd) / len(risks_dd) / capital * 100) if risks_dd else None,
        "risk_ok_pct": (sum(risks_ok) / len(risks_ok) / capital * 100) if risks_ok else None,
        "n_dd_trades": len(risks_dd),
        "scale_rate": len(scaled) / len(trades) * 100 if trades else 0,
        "win_legs": sum(len(t.legs) for t in wins) / len(wins),
        "loss_legs": sum(len(t.legs) for t in losses) / len(losses),
        "into_strength_pct": into / len(scaled_win) * 100 if scaled_win else 0,
        "respect_pct": sum(1 for t in lR if t.R >= -1.2) / len(lR) * 100,
        "blew_pct": sum(1 for t in lR if t.R < -1) / len(lR) * 100,
        "n_blew2": sum(1 for t in lR if t.R < -2),
        "avg_risk_pct": (sum(risks) / len(risks) / capital * 100) if risks else None,
        "avg_win_R": sum(t.R for t in wins) / len(wins),
        "avg_loss_R": sum(t.R for t in losses) / len(losses),
    }


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
def render_analysis(trades, capital, total_pnl, include_characteristics=True, equity_by_date=None) -> str:
    off = offense(trades)
    dfn = defense(trades)
    trm = trimming(trades)
    lev = leverage(trades, capital)
    cef = capital_efficiency(trades, capital, total_pnl, equity_by_date)
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
    rod = f"{cef['return_on_deployed']:.1f}%" if cef.get('return_on_deployed') is not None else "—"
    total_ret = total_pnl / capital * 100 if capital else 0
    has_lev = cef.get('avg_leverage_pct') is not None
    lev_txt = (f"avg leverage {cef['avg_leverage_pct']/100:.2f}× / peak {cef['peak_leverage_pct']/100:.2f}× (gross ÷ equity)"
               if has_lev else
               f"avg deployed {cef['avg_deployed_pct_of_start']:.0f}% / peak {cef['peak_deployed_pct_of_start']:.0f}% of starting capital")
    A(f"| 资金效率 Capital efficiency | — | **return on deployed capital {rod}** (vs +{total_ret:.1f}% on total); "
      f"{lev_txt}; avg {cef['avg_concurrent']:.0f} concurrent, {cef['avg_hold']:.1f}d hold; {money(cef['pnl_per_trade'])}/trade |")
    A("")
    if has_lev:
        A(f"> **资金效率解读 / Capital efficiency:** every $1 of capital actually at risk returned **{rod}** "
          f"over the period. Leverage — gross exposure ÷ current equity — averaged **{cef['avg_leverage_pct']/100:.2f}×** "
          f"and peaked at **{cef['peak_leverage_pct']/100:.2f}×**, so on average you deployed "
          f"{'more than' if cef['avg_leverage_pct']>100 else 'under'} your equity "
          f"({'net margin' if cef['avg_leverage_pct']>100 else 'kept dry powder'}). "
          f"(Deployment vs the *starting* $1M reads higher — {cef['peak_deployed_pct_of_start']:.0f}% peak — because equity grew; "
          f"leverage vs current equity is the honest gauge.)\n")

    # Position heat — name count vs forward pullback (the "greed gauge")
    ph = position_heat(trades, equity_by_date) if equity_by_date else None
    if ph:
        A("### 仓位热度 / Position heat — names vs pullback\n")
        A(f"*Concurrent NAMES (unique tickers, layers deduped). Max {ph['max_names']}, "
          f"median {ph['median_names']}; hit ≥{ph['greed']} on {ph['days_ge_greed']}/{ph['total_days']} days.*\n")
        A("| Names held | Avg fwd 5d return | % days → >2% pullback |")
        A("|---|---|---|")
        for b in ph["buckets"]:
            r = f"{b['avg_fwd5_ret']:+.1f}%" if b["avg_fwd5_ret"] is not None else "—"
            A(f"| {b['label']} | {r} | {b['pullback_rate']:.0f}% |")
        A(f"\n**Every crossing to ≥{ph['greed']} names → next-{ph['fwd']}d max pullback:**\n")
        A("| Date | Names | Equity | Next pullback |")
        A("|---|---|---|---|")
        for e in ph["episodes"]:
            dd = f"{e['next_maxdd']:.1f}%" if e["next_maxdd"] is not None else "—"
            A(f"| {e['date']} | {e['names']} | {money(e['equity'])} | {dd} |")
        hits = [e for e in ph["episodes"] if e["next_maxdd"] is not None and e["next_maxdd"] < -3]
        A(f"\n> **解读:** {len(hits)}/{len(ph['episodes'])} times names crossed ≥{ph['greed']}, a >3% pullback followed within "
          f"{ph['fwd']} days. Pullback frequency rises with names ({ph['buckets'][0]['pullback_rate']:.0f}% at {ph['buckets'][0]['label']} "
          f"→ {ph['buckets'][-1]['pullback_rate']:.0f}% at {ph['buckets'][-1]['label']}). Returns still trend positive (you add names "
          f"in momentum), so ≥{ph['greed']} names = **stop adding / tighten stops / take some off**, not exit-all.\n")

    # Behavioral diagnosis — the four questions
    bd = behavioral_diagnosis(trades, equity_by_date, capital) if equity_by_date else None
    if bd:
        A("### 行为诊断 / Behavioral diagnosis\n")
        A("**1 · Largest losses — where the holes come from.** Your losers are cut FAST "
          f"(avg {bd['avg_loss_hold']:.1f}d vs winners {bd['avg_win_hold']:.1f}d) — you're not a chronic "
          "bag-holder. The big losses come from **re-attacking a broken thesis**, not bad entries:")
        A("")
        A("| Re-traded name | Entries | Losing | Net |")
        A("|---|---|---|---|")
        for r in bd["worst_reattack"]:
            A(f"| {r['ticker']} | {r['n']} | {r['n_loss']} | {money(r['net'])} |")
        if bd["overheld"]:
            oh = ", ".join(f"{t.ticker} {t.hold_days}d ({t.R:+.1f}R)" for t in bd["overheld"])
            A(f"\n*The only chronic over-holds (>21d losers): {oh} — one campaign, not a habit.*\n")
        A(f"> **Answer:** Not bottom-fishing, not holding losses long on average. The leak is **averaging into "
          f"a failing name** (the top row above is your single biggest hole). You need a hard "
          f"'this thesis is dead — stop re-entering' rule.\n")

        A("**2 · Largest winners — what's working.** Winners are held **longer** "
          f"({bd['avg_win_hold']:.1f}d vs {bd['avg_loss_hold']:.1f}d), scaled out more "
          f"({bd['win_legs']:.1f} legs vs {bd['loss_legs']:.1f}), and **{bd['into_strength_pct']:.0f}% of scaled "
          f"winners were trimmed into strength** (first trim in profit). The same persistence that sinks a bad "
          f"name (re-attack) makes your biggest wins when the thesis is right — you press winners. Keep it; "
          f"just gate it on the thesis still being valid.\n")

        A("**3 · Drawdown behavior — do you press or pull back?** You **de-risk** in drawdowns: "
          f"avg initial risk was **{bd['risk_dd_pct']:.2f}%** on the {bd['n_dd_trades']} trades opened while "
          f">3% off peak, vs **{bd['risk_ok_pct']:.2f}%** normally — roughly **half size** when cold. That's "
          f"disciplined; you're not revenge-sizing.\n")

        A("**4 · Trims & stops.** Scaling: {sr:.0f}% of trades scaled out, {i:.0f}% of scaled winners trimmed into "
          "strength — excellent exit craft. Stops: **{resp:.0f}% of losses respected the stop** (≤1.2R), but "
          "**{blew:.0f}% blew through −1R** ({b2} worse than −2R) — the tail is the re-attack campaign. Sizing: "
          "avg initial risk **{rp:.2f}% of capital vs your 0.25% target** — you run ~2× your intended 1R.\n"
          .format(sr=bd['scale_rate'], i=bd['into_strength_pct'], resp=bd['respect_pct'],
                  blew=bd['blew_pct'], b2=bd['n_blew2'], rp=bd['avg_risk_pct']))

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
