#!/usr/bin/env python3
"""RR chart — every closed trade plotted by its R-multiple.

Green = win, red = loss, from a zero baseline. The signature "fintwit RR chart":
a floor of small losses with a few towering right-tail winners. Reusable across
review periods (monthly / quarterly / H1 / annual).

R = realized P&L ÷ initial risk (|entry − initial_stop| × original_qty).
Needs matplotlib; returns None (no file) if it's unavailable so a review never
hard-fails on the chart.
"""
from __future__ import annotations

from statistics import mean, median


def generate_rr_chart(trades, capital, out_path,
                      period_label="Jan 2026 to Jul 2026",
                      handle="@Fluxus_Z",
                      title="Every trade by R-multiple",
                      headline=None):
    """Render the RR bar chart to `out_path` (PNG). Returns out_path or None."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MultipleLocator
    except ImportError:
        return None

    rr = [t for t in trades if t.R is not None]
    if len(rr) < 3:
        return None
    rr = sorted(rr, key=lambda t: t.exit_date)
    Rs = [t.R for t in rr]
    xs = list(range(len(Rs)))
    colors = ["#2e9e4f" if r > 0 else "#d0362b" for r in Rs]

    wins = [r for r in Rs if r > 0]
    losses = [r for r in Rs if r < 0]
    avg_win = mean(wins) if wins else 0
    avg_loss = mean(losses) if losses else 0
    win_rate = len(wins) / len(Rs) * 100
    sum_r = sum(Rs)
    # 1R as % of capital = average initial risk / capital
    risks = [t.risk for t in rr if t.risk]
    avg_risk_pct = (mean(risks) / capital * 100) if (risks and capital) else None
    total_pnl = sum(t.pnl for t in rr)
    ret_pct = total_pnl / capital * 100 if capital else 0

    fig, ax = plt.subplots(figsize=(13, 6.4), dpi=170)
    ax.bar(xs, Rs, color=colors, width=0.85, linewidth=0)
    ax.axhline(0, color="#888", lw=0.8)
    # reference lines for avg win / loss (unlabeled — numbers are in the subtitle)
    ax.axhline(avg_win, color="#2e9e4f", lw=0.9, ls="--", alpha=0.5)
    ax.axhline(avg_loss, color="#d0362b", lw=0.9, ls="--", alpha=0.5)
    hi = max(Rs)
    ax.set_ylim(min(min(Rs) - 1, -3), hi + 2.5)
    ax.set_ylabel("R multiple  (profit ÷ initial risk)", fontsize=11, color="#333")
    ax.set_xlabel(f"Closed trades in sequence  ({period_label})", fontsize=11, color="#333")
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.grid(axis="y", color="#eee", lw=0.7)
    ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color("#ccc")
    ax.tick_params(colors="#666", labelsize=9)
    ax.set_xlim(-2, len(Rs) + 1)

    # annotate the biggest winners
    for t in sorted(rr, key=lambda t: -t.R)[:4]:
        i = rr.index(t)
        ax.annotate(f"{t.ticker} +{t.R:.0f}R", (i, t.R), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color="#1e7e34", fontweight="bold")

    head = headline or (f"{ret_pct:+.1f}%  ·  {len(Rs)} trades  ·  {win_rate:.0f}% win rate  ·  "
                        f"+{sum_r:.0f}R total  ·  avg win {avg_win:.1f}R / avg loss {avg_loss:.1f}R")
    ax.set_title(f"{title}", fontsize=16, fontweight="bold", color="#111", loc="left", pad=30)
    fig.text(0.125, 0.905, head, fontsize=11, color="#555")
    risk_note = (f"1R ≈ {avg_risk_pct:.2f}% of capital"
                 if avg_risk_pct is not None else "")
    if risk_note:
        fig.text(0.125, 0.876, risk_note, fontsize=9.5, color="#999")
    fig.text(0.9, 0.02, handle, fontsize=10, color="#bbb", ha="right")

    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    plt.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path
