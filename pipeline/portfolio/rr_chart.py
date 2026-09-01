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
                      headline=None, dark=False, equity_by_date=None):
    """Render the RR bar chart to `out_path` (PNG). Returns out_path or None."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MultipleLocator
    except ImportError:
        return None

    # theme palette
    if dark:
        C = dict(face="#111621", title="#E8ECF2", head="#9aa4b2", sub="#79828F",
                 hand="#4b5563", axis="#232c3a", spine="#2b3543", tick="#79828F",
                 grid="#232c3a", zero="#4b5563", winlbl="#5fd08a", losslbl="#f4838c")
    else:
        C = dict(face="white", title="#111", head="#555", sub="#999",
                 hand="#bbb", axis="#333", spine="#ccc", tick="#666",
                 grid="#eee", zero="#888", winlbl="#1e7e34", losslbl="#b3241b")

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
    # 1R %: HOUSE RULE (2026-09-01) — ÷ equity on the ENTRY DAY when the curve is
    # available; ÷ starting capital only as a labeled fallback.
    def _eq_at(ds):
        if not equity_by_date:
            return capital
        prior = [d for d in equity_by_date if d <= ds]
        return equity_by_date[max(prior)] if prior else capital
    risks = [t.risk / _eq_at(t.entry_date) * 100 for t in rr if t.risk]
    avg_risk_pct = median(risks) if risks else None
    risk_denom = "entry-day equity (median)" if equity_by_date else "starting capital (median)" 
    total_pnl = sum(t.pnl for t in rr)
    ret_pct = total_pnl / capital * 100 if capital else 0

    fig, ax = plt.subplots(figsize=(13, 6.4), dpi=170)
    ax.set_facecolor(C["face"])
    ax.bar(xs, Rs, color=colors, width=0.85, linewidth=0)
    ax.axhline(0, color=C["zero"], lw=0.8)
    # reference lines for avg win / loss (unlabeled — numbers are in the subtitle)
    ax.axhline(avg_win, color="#2e9e4f", lw=0.9, ls="--", alpha=0.5)
    ax.axhline(avg_loss, color="#d0362b", lw=0.9, ls="--", alpha=0.5)
    hi = max(Rs)
    ax.set_ylim(min(min(Rs) - 1, -3), hi + 2.5)
    ax.set_ylabel("R multiple  (profit ÷ initial risk)", fontsize=11, color=C["axis"])
    ax.set_xlabel(f"Closed trades in sequence  ({period_label})", fontsize=11, color=C["axis"])
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.grid(axis="y", color=C["grid"], lw=0.7)
    ax.set_axisbelow(True)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(C["spine"])
    ax.tick_params(colors=C["tick"], labelsize=9)
    ax.set_xlim(-2, len(Rs) + 1)

    # annotate the biggest winners
    for t in sorted(rr, key=lambda t: -t.R)[:4]:
        i = rr.index(t)
        ax.annotate(f"{t.ticker} +{t.R:.0f}R", (i, t.R), xytext=(0, 6),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color=C["winlbl"], fontweight="bold")
    # annotate the biggest loss
    worst = min(rr, key=lambda t: t.R)
    if worst.R < -1.5:
        ax.set_ylim(min(min(Rs) - 1.6, -3), hi + 2.5)
        i = rr.index(worst)
        ax.annotate(f"{worst.ticker} {worst.R:.1f}R", (i, worst.R), xytext=(0, -6),
                    textcoords="offset points", ha="center", va="top", fontsize=8.5,
                    color=C["losslbl"], fontweight="bold")

    head = headline or (f"{ret_pct:+.1f}%  ·  {len(Rs)} trades  ·  {win_rate:.0f}% win rate  ·  "
                        f"+{sum_r:.0f}R total  ·  avg win {avg_win:.1f}R / avg loss {avg_loss:.1f}R")
    ax.set_title(f"{title}", fontsize=16, fontweight="bold", color=C["title"], loc="left", pad=30)
    fig.text(0.125, 0.905, head, fontsize=11, color=C["head"])
    risk_note = (f"1R ≈ {avg_risk_pct:.2f}% of {risk_denom}"
                 if avg_risk_pct is not None else "")
    if risk_note:
        fig.text(0.125, 0.876, risk_note, fontsize=9.5, color=C["sub"])
    fig.text(0.9, 0.02, handle, fontsize=10, color=C["hand"], ha="right")

    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    plt.savefig(out_path, bbox_inches="tight", facecolor=C["face"])
    plt.close(fig)
    return out_path
