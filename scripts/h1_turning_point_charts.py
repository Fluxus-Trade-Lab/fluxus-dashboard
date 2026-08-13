#!/usr/bin/env python3
"""Turning-point charts for the H1 flagship letter.

Deliberately two charts, not eight. A letter with a chart per beat reads as a
slideshow; the argument is stronger when the whole March-April sequence sits on
ONE annotated panel and the reader can see the gap between "I saw it" (3/20) and
"I bought" (4/9) without scrolling.

    python scripts/h1_turning_point_charts.py

  spy_turning_points.png  -- SPY daily, 10/20/50 MA, four dated annotations
  be_the_trade.png        -- BE daily with the actual 4/9 order drawn on it

Prices from IBKR (house rule: never TradingView), cached to JSON so re-runs work
without TWS.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

OUT = Path("Fluxus_Substack/assets")
CACHE = OUT / "ohlc_turning_points.json"

INK = "#111418"
MUTED = "#8b9199"
GRID = "#e6e8ec"
UP = "#3f7d5a"
DOWN = "#c0523f"
MA10 = "#5b8fd0"
MA20 = "#c8804a"
MA50 = "#8b9199"
MARK = "#111418"


def fetch(specs):
    """specs: {ticker: (durationStr, endDate)} -> {ticker: [bar dicts]}"""
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    from ib_async import IB, Stock
    ib, last = IB(), None
    for port in (7496, 7497, 4001, 4002):
        for cid in (16, 17, 18, 19):
            try:
                ib.connect("127.0.0.1", port, clientId=cid, timeout=8)
                last = None
                break
            except Exception as exc:  # noqa: BLE001
                last = exc
                if "refused" in str(exc).lower():
                    break
        if last is None:
            break
    if last is not None:
        raise SystemExit(f"no IBKR connection (needed once to seed {CACHE}): {last}")
    out = {}
    for tk, (duration, end) in specs.items():
        c = Stock(tk, "SMART", "USD")
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(
            c, endDateTime=f"{end} 23:59:59 US/Eastern", durationStr=duration,
            barSizeSetting="1 day", whatToShow="TRADES", useRTH=True,
            formatDate=1, timeout=90)
        out[tk] = [{"d": str(b.date), "o": b.open, "h": b.high,
                    "l": b.low, "c": b.close} for b in bars]
        print(f"# {tk}: {len(out[tk])} bars {out[tk][0]['d']}..{out[tk][-1]['d']}",
              file=sys.stderr)
        ib.sleep(3)
    ib.disconnect()
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out))
    return out


def sma(vals, n):
    out, run = [], []
    for v in vals:
        run.append(v)
        if len(run) > n:
            run.pop(0)
        out.append(sum(run) / len(run) if len(run) == n else None)
    return out


def style(ax):
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def candles(ax, bars, xs):
    for i, b in enumerate(bars):
        col = UP if b["c"] >= b["o"] else DOWN
        ax.vlines(xs[i], b["l"], b["h"], color=col, lw=0.8, alpha=0.85)
        ax.vlines(xs[i], min(b["o"], b["c"]), max(b["o"], b["c"]),
                  color=col, lw=3.0, alpha=0.95)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT / name}")


def chart_spy(bars):
    closes = [b["c"] for b in bars]
    m10, m20, m50 = sma(closes, 10), sma(closes, 20), sma(closes, 50)
    lo, hi = "2026-02-10", "2026-05-08"
    keep = [i for i, b in enumerate(bars) if lo <= b["d"] <= hi]
    view = [bars[i] for i in keep]
    xs = list(range(len(view)))
    idx = {b["d"]: i for i, b in enumerate(view)}

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    style(ax)
    candles(ax, view, xs)
    for series, col, lab in ((m10, MA10, "10 MA"), (m20, MA20, "20 MA"), (m50, MA50, "50 MA")):
        ax.plot(xs, [series[i] for i in keep], color=col, lw=1.4, label=lab, alpha=0.9)

    def near(day):
        c = [d for d in idx if d <= day]
        return idx[max(c)] if c else 0

    lows = [b["l"] for b in view]
    highs = [b["h"] for b in view]
    ymin, ymax = min(lows), max(highs)
    span = ymax - ymin
    # Label positions are hand-placed in data coords: the four beats sit close
    # together on the x-axis, so auto-placement stacks them on top of each other.
    # 4/8 and 4/9 are adjacent bars; separate labels put their leader lines through
    # each other. They are one beat anyway -- the news, then the trigger.
    beats = [
        ("2026-03-20", "3/20 — the confluence post\n“I'm not calling the bottom”",
         -13.0, ymin + span * 0.78, "left"),
        ("2026-03-30", "3/30 — the actual low.\nI bought nothing.",
         -13.5, ymin + span * 0.30, "right"),
        ("2026-04-09", "4/8 — ceasefire prints. “No FTD.” Still nothing.\n"
                       "4/9 — in. 10–14%, stop 136. ≈0.5% of the account.",
         5.0, ymin + span * 0.10, "left"),
    ]
    for day, text, dx, ty, ha in beats:
        i = near(day)
        anchor = view[i]["l"] if ty < view[i]["l"] else view[i]["h"]
        ax.annotate(
            text, xy=(i, anchor), xytext=(i + dx, ty),
            color=INK, fontsize=9.5, ha=ha, va="center",
            arrowprops=dict(arrowstyle="-", color=MARK, lw=1.0,
                            shrinkA=2, shrinkB=4, alpha=0.55,
                            connectionstyle="arc3,rad=0"),
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID, lw=0.9),
            zorder=6)
        ax.scatter([i], [anchor], s=26, color=MARK, zorder=7)

    step = max(1, len(view) // 9)
    ax.set_xticks(xs[::step])
    ax.set_xticklabels([dt.date.fromisoformat(view[i]["d"]).strftime("%b %d")
                        for i in xs[::step]])
    ax.set_xlim(-16, len(view) + 14)
    ax.set_ylim(ymin - span * 0.06, ymax + span * 0.08)
    ax.legend(frameon=False, loc="upper left", fontsize=9, labelcolor=INK, ncol=3)
    ax.set_title("SPY — twenty days between seeing it and buying it",
                 color=INK, fontsize=13, loc="left", pad=14)
    save(fig, "spy_turning_points.png")


def chart_be(bars):
    lo, hi = "2026-03-16", "2026-04-24"
    view = [b for b in bars if lo <= b["d"] <= hi]
    if not view:
        print("BE: no bars in window, skipping")
        return
    xs = list(range(len(view)))
    idx = {b["d"]: i for i, b in enumerate(view)}

    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    style(ax)
    candles(ax, view, xs)

    def near(day):
        c = [d for d in idx if d <= day]
        return idx[max(c)] if c else 0

    entry_i, exit_i = near("2026-04-09"), near("2026-04-14")
    ax.axhspan(140, 144, color="#dbe6f2", alpha=0.75, lw=0, zorder=0)
    ax.axhline(136, color=DOWN, lw=1.3, ls="--")
    ax.axhline(200, color=UP, lw=1.3, ls="--")
    # Labels parked in the right margin so they never sit on top of a candle.
    rx = len(view) + 0.8
    ax.annotate("entry 140–144", xy=(rx, 142), color="#3b6ea8", fontsize=9.5, va="center")
    ax.annotate("stop 136\n−4.2% of the trade\n≈0.5% of the account",
                xy=(rx, 126), color=DOWN, fontsize=9.5, va="center")
    ax.annotate("200 — trimmed 4/14,\nfive days later", xy=(rx, 209),
                color=UP, fontsize=9.5, va="center")
    ax.scatter([entry_i], [142], marker="^", s=110, color=MARK, zorder=5)
    ax.scatter([exit_i], [200], marker="v", s=110, color=MARK, zorder=5)
    ax.annotate("4/9 in", xy=(entry_i, 142), xytext=(entry_i - 5.0, 126),
                color=INK, fontsize=9,
                arrowprops=dict(arrowstyle="-", color=MARK, lw=1, alpha=0.6))
    ax.annotate("4/14 out", xy=(exit_i, 200), xytext=(exit_i - 4.0, 188),
                color=INK, fontsize=9,
                arrowprops=dict(arrowstyle="-", color=MARK, lw=1, alpha=0.6))

    step = max(1, len(view) // 8)
    ax.set_xticks(xs[::step])
    ax.set_xticklabels([dt.date.fromisoformat(view[i]["d"]).strftime("%b %d")
                        for i in xs[::step]])
    ax.set_xlim(-1, len(view) + 11)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    ax.set_title("BE — the whole order, posted before the open",
                 color=INK, fontsize=13, loc="left", pad=14)
    save(fig, "be_the_trade.png")


def main():
    data = fetch({"SPY": ("8 M", "20260510"), "BE": ("6 M", "20260501")})
    chart_spy(data["SPY"])
    chart_be(data["BE"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
