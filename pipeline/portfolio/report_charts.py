"""Matplotlib charts for the shareable HTML performance report.

Every function returns a base64-encoded PNG string ready to drop into an
`<img src="data:image/png;base64,...">`. Charts render on white cards (the report
chrome is dark; white chart cards read like an institutional tearsheet and let us
reuse the existing white RR chart PNG unchanged).

Data comes straight from the performance_review engine (equity_by_date, monthly,
r_distribution) and the local OHLC store — no numbers are recomputed here, so the
charts always agree with the tables.
"""
from __future__ import annotations

import base64
import datetime as dt
import io
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import matplotlib.dates  # noqa: E402

GREEN = "#2e9e4f"
RED = "#d0362b"
BLUE = "#5AA9FF"          # readable on both light and dark
BLUE_L = "#3b6fa8"        # deeper blue for light backgrounds

plt.rcParams.update({"font.size": 10, "axes.linewidth": 0.8})


def _pal(dark: bool) -> dict:
    """Theme palette so charts match whichever report theme is active."""
    if dark:
        return {"face": "#111621", "ink": "#C7CDD8", "mut": "#79828F",
                "grid": "#232c3a", "edge": "#2b3543", "blue": BLUE, "zero": "#4b5563"}
    return {"face": "#ffffff", "ink": "#1a1f2b", "mut": "#5b6472",
            "grid": "#e9ecf1", "edge": "#c9cfd8", "blue": BLUE_L, "zero": "#b8bfc9"}


def _style(ax, p):
    ax.set_facecolor(p["face"])
    ax.tick_params(colors=p["mut"], labelsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(p["edge"])
    ax.yaxis.label.set_color(p["ink"])
    ax.xaxis.label.set_color(p["ink"])


def _b64(fig, face="#ffffff") -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=face, dpi=150)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _pct_axis(ax, p):
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(axis="y", color=p["grid"], lw=0.8)
    _style(ax, p)


def png_from_file(path: str) -> Optional[str]:
    """Base64 an existing PNG (e.g. the already-generated RR chart)."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return None


# --------------------------------------------------------------------------- #
def equity_curve(equity_by_date: dict, drawdown: Optional[dict], capital: float,
                 dark: bool = False, ylabel: str = "Return vs start") -> Optional[str]:
    """MTM equity as % return vs `capital` base, with the max-drawdown window shaded."""
    if not equity_by_date:
        return None
    p = _pal(dark)
    dates = sorted(equity_by_date)
    xs = [dt.date.fromisoformat(d) for d in dates]
    ys = [(equity_by_date[d] / capital - 1) * 100 for d in dates]

    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=150)
    ax.plot(xs, ys, color=p["blue"], lw=1.8)
    ax.fill_between(xs, ys, 0, where=[y >= 0 for y in ys], color=p["blue"], alpha=0.10)
    ax.axhline(0, color=p["zero"], lw=0.8)

    if drawdown and drawdown.get("peak_date") and drawdown.get("trough_date"):
        pk = dt.date.fromisoformat(drawdown["peak_date"][:10])
        tr = dt.date.fromisoformat(drawdown["trough_date"][:10])
        ax.axvspan(pk, tr, color=RED, alpha=0.12)
        ax.annotate(f"max DD {drawdown.get('pct'):.1f}%", xy=(tr, min(ys)), xytext=(0, 12),
                    textcoords="offset points", ha="center", color=RED, fontsize=9, fontweight="bold")
    _pct_axis(ax, p)
    ax.margins(x=0.01)
    ax.set_ylabel(ylabel)
    fig.autofmt_xdate(rotation=0, ha="center")
    return _b64(fig, p["face"])


def monthly_returns(monthly_stats: list, capital: float = None, dark: bool = False) -> Optional[str]:
    """Bar chart of compounded MTM return % per month (matches the dashboard).
    `monthly_stats` = performance_review.monthly_stats() rows."""
    if not monthly_stats:
        return None
    p = _pal(dark)
    months = [d["month"] for d in monthly_stats]
    vals = [d["ret_pct"] for d in monthly_stats]
    colors = [GREEN if v >= 0 else RED for v in vals]
    fig, ax = plt.subplots(figsize=(11, 3.4), dpi=150)
    bars = ax.bar(range(len(months)), vals, color=colors, width=0.66)
    ax.axhline(0, color=p["zero"], lw=0.8)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([m[2:] for m in months], fontsize=9)  # YY-MM
    _pct_axis(ax, p)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:+.1f}%", xy=(b.get_x() + b.get_width() / 2, v),
                    xytext=(0, 3 if v >= 0 else -12), textcoords="offset points",
                    ha="center", fontsize=8, color=p["ink"])
    return _b64(fig, p["face"])


def r_distribution(rdist: dict, dark: bool = False) -> Optional[str]:
    """Histogram of per-trade R buckets."""
    if not rdist or not sum(rdist.values()):
        return None
    p = _pal(dark)
    labels = list(rdist.keys())
    vals = [rdist[k] for k in labels]
    colors = [RED if ("-" in k and "R" in k.split("..")[0]) or k.startswith("<=") or k == "-2R..-1R" or k == "-1R..0"
              else GREEN for k in labels]
    fig, ax = plt.subplots(figsize=(8.5, 3.4), dpi=150)
    bars = ax.bar(range(len(labels)), vals, color=colors, width=0.72)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.5, rotation=0)
    ax.grid(axis="y", color=p["grid"], lw=0.8)
    _style(ax, p)
    for b, v in zip(bars, vals):
        if v:
            ax.annotate(str(v), xy=(b.get_x() + b.get_width() / 2, v), xytext=(0, 3),
                        textcoords="offset points", ha="center", fontsize=8.5, color=p["ink"])
    ax.set_ylabel("# trades")
    return _b64(fig, p["face"])


def _equity_at(equity_by_date, date, fallback):
    if not equity_by_date:
        return fallback
    prior = [d for d in equity_by_date if d <= date]
    return equity_by_date[max(prior)] if prior else fallback


def position_sizes(trades, equity_by_date: dict, capital: float, dark: bool = False):
    """Per-trade position size (notional at entry ÷ equity at entry, %), one bar
    per closed trade in the SAME order as the RR chart (by exit date) so the two
    align bar-for-bar. Green = the trade won, red = it lost. Returns (b64, stats)."""
    rr = sorted([t for t in trades if t.R is not None], key=lambda t: t.exit_date)
    if len(rr) < 3:
        return None, None
    p = _pal(dark)
    sizes, colors = [], []
    for t in rr:
        eq = _equity_at(equity_by_date, t.entry_date, capital) or capital
        notional = (t.orig_qty or 0) * (t.entry or 0)
        sizes.append(notional / eq * 100 if eq else 0)
        colors.append(GREEN if t.pnl > 0 else RED)

    import statistics as _st
    avg = _st.mean(sizes)
    # correlation between size and R (does betting big earn big?)
    Rs = [t.R for t in rr]
    corr = None
    if len(sizes) > 2 and _st.pstdev(sizes) > 0 and _st.pstdev(Rs) > 0:
        ms, mr = _st.mean(sizes), _st.mean(Rs)
        cov = sum((s - ms) * (r - mr) for s, r in zip(sizes, Rs)) / len(sizes)
        corr = cov / (_st.pstdev(sizes) * _st.pstdev(Rs))
    # share of gross losses coming from the biggest-quartile positions
    order = sorted(range(len(rr)), key=lambda i: -sizes[i])
    top_q = set(order[:max(1, len(rr) // 4)])
    gross_loss = sum(-t.pnl for t in rr if t.pnl < 0) or 1
    loss_top_q = sum(-rr[i].pnl for i in top_q if rr[i].pnl < 0)
    stats = {"avg": avg, "max": max(sizes), "corr": corr,
             "loss_share_top_quartile": loss_top_q / gross_loss * 100}

    fig, ax = plt.subplots(figsize=(13, 4.2), dpi=150)
    xs = list(range(len(sizes)))
    ax.bar(xs, sizes, color=colors, width=0.85, linewidth=0)
    ax.axhline(avg, color=p["mut"], lw=0.9, ls="--", alpha=0.7)
    ax.annotate(f"avg {avg:.1f}%", xy=(0, avg), xytext=(4, 3), textcoords="offset points",
                fontsize=8.5, color=p["mut"])
    # annotate the 4 biggest positions
    for i in order[:4]:
        ax.annotate(f"{rr[i].ticker} {sizes[i]:.0f}%", (i, sizes[i]), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color=(GREEN if rr[i].pnl > 0 else RED), fontweight="bold")
    ax.set_ylabel("Position size  (% of equity at entry)")
    ax.set_xlabel("Closed trades in sequence (same order as the RR chart)")
    ax.grid(axis="y", color=p["grid"], lw=0.7)
    ax.set_axisbelow(True)
    _style(ax, p)
    ax.set_xlim(-2, len(sizes) + 1)
    return _b64(fig, p["face"]), stats


def deployment_curve(trades, equity_by_date: dict, capital: float, dark: bool = False) -> Optional[str]:
    """% of capital deployed (cost basis of open positions ÷ equity) over time."""
    if not equity_by_date:
        return None
    p = _pal(dark)
    dates = sorted(equity_by_date)

    def deployed_cost(day: str) -> float:
        tot = 0.0
        for t in trades:
            if t.entry_date > day:
                continue
            sold = sum(lg.qty for lg in t.legs if lg.date <= day)
            rem = t.orig_qty - sold
            if rem > 1e-9:
                tot += rem * t.entry
        return tot

    xs = [dt.date.fromisoformat(d) for d in dates]
    dep = [deployed_cost(d) / equity_by_date[d] * 100 if equity_by_date[d] else 0 for d in dates]

    fig, ax = plt.subplots(figsize=(11, 3.4), dpi=150)
    ax.plot(xs, dep, color=p["blue"], lw=1.6)
    ax.fill_between(xs, dep, 0, color=p["blue"], alpha=0.10)
    ax.axhline(100, color=p["mut"], lw=0.8, ls="--")
    ax.annotate("100% (fully invested)", xy=(xs[0], 100), xytext=(2, 3),
                textcoords="offset points", fontsize=8, color=p["mut"])
    _pct_axis(ax, p)
    ax.margins(x=0.01)
    ax.set_ylabel("Capital deployed")
    fig.autofmt_xdate(rotation=0, ha="center")
    return _b64(fig, p["face"])


# --------------------------------------------------------------------------- #
def _ma(vals, n, kind="sma"):
    out = [None] * len(vals)
    if kind == "sma":
        for i in range(len(vals)):
            if i + 1 >= n:
                out[i] = sum(vals[i - n + 1:i + 1]) / n
    else:  # ema
        if len(vals) >= n:
            k = 2 / (n + 1)
            e = sum(vals[:n]) / n
            out[n - 1] = e
            for i in range(n, len(vals)):
                e = vals[i] * k + e * (1 - k)
                out[i] = e
    return out


def case_studies_grid(rows, load_ohlc, dark: bool = False) -> Optional[str]:
    """2×4 grid of mini price+MA charts for the 8 case-study trades.
    `rows` = analysis.trade_case_studies output; `load_ohlc(ticker)` → bars."""
    if not rows:
        return None
    p = _pal(dark)
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.4), dpi=150)
    fig.patch.set_facecolor(p["face"])
    axes = axes.ravel()
    for ax, row in zip(axes, rows):
        t = row["t"]
        bars = load_ohlc(t.ticker)
        if not bars:
            ax.set_axis_off()
            ax.set_title(f"{t.ticker} — no data", fontsize=9, color=p["mut"])
            continue
        entry = t.entry_date[:10]
        exit_ = t.exit_date[:10]
        closes = [b["close"] for b in bars]
        ema20 = _ma(closes, 20, "ema")
        sma50 = _ma(closes, 50, "sma")
        sma200 = _ma(closes, 200, "sma")
        # window: 40 bars before entry → 5 after exit
        ei = next((i for i, b in enumerate(bars) if b["date"] >= entry), len(bars) - 1)
        xi = next((i for i, b in enumerate(bars) if b["date"] >= exit_), len(bars) - 1)
        lo = max(0, ei - 40)
        hi = min(len(bars), xi + 6)
        idx = list(range(lo, hi))
        xd = [dt.date.fromisoformat(bars[i]["date"]) for i in idx]
        ax.plot(xd, [closes[i] for i in idx], color=p["ink"], lw=1.3, label="close")
        ax.plot(xd, [ema20[i] for i in idx], color="#e0932a", lw=1.0, label="20EMA")
        ax.plot(xd, [sma50[i] for i in idx], color=p["blue"], lw=1.0, label="50SMA")
        if any(sma200[i] is not None for i in idx):
            ax.plot(xd, [sma200[i] for i in idx], color="#b07cd4" if dark else "#9b59b6", lw=1.0, label="200SMA")
        # entry / exit markers
        ax.scatter([dt.date.fromisoformat(bars[ei]["date"])], [closes[ei]], marker="^",
                   color=GREEN if row["win"] else RED, s=55, zorder=5)
        if xi < len(bars):
            ax.scatter([dt.date.fromisoformat(bars[xi]["date"])], [closes[xi]], marker="x",
                       color=p["mut"], s=45, zorder=5)
        rr = f"{t.R:+.1f}R" if t.R is not None else "—"
        colr = GREEN if row["win"] else RED
        ax.set_title(f"{t.ticker}  {rr}", fontsize=10, fontweight="bold", color=colr, loc="left")
        ax.text(0.0, 1.14, row["cls"]["type"], transform=ax.transAxes, fontsize=7.5, color=p["mut"])
        ax.set_facecolor(p["face"])
        ax.tick_params(labelsize=7, colors=p["mut"])
        ax.grid(axis="y", color=p["grid"], lw=0.6)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(4))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b '%y"))
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(p["edge"])
        ax.margins(x=0.02)
        for lb in ax.get_xticklabels():
            lb.set_rotation(0)
    # single shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        leg = fig.legend(handles, labels, loc="upper center", ncol=4, fontsize=9,
                         frameon=False, bbox_to_anchor=(0.5, 1.03))
        for txt in leg.get_texts():
            txt.set_color(p["ink"])
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    return _b64(fig, p["face"])
