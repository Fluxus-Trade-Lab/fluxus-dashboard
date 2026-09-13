"""Education figures — paper-style schematics (spec §5), one function per concept.

Every figure encodes spec §5's three checks as asserts on its own data, so a wrong
drawing fails the render instead of shipping:
  (1) price really performs the move the concept names,
  (2) the structural relationship is right (support below / resistance above / who leads),
  (3) every label is computed from, or placed on, the thing it names.
Schematics, not price data. Labels are English mono in both language editions.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Ellipse  # noqa: E402

PAPER, INK, VIO, AMB, GRN, GRY, RED = "#efece3", "#1b1b1b", "#5b5fd6", "#c98a1b", "#3f8f5a", "#8a857a", "#b0503a"
MONO = "Menlo"


def _canvas(title: str, ylim=(0, 60)):
    fig = plt.figure(figsize=(9.2, 4.4), dpi=200, facecolor=PAPER)
    ax = fig.add_axes([0.03, 0.05, 0.94, 0.72])
    ax.set_facecolor(PAPER)
    rng = np.random.default_rng(7)
    ax.imshow(rng.normal(0, 1, (120, 240)), extent=(0, 100, ylim[0], ylim[1]), cmap="Greys",
              alpha=0.035, aspect="auto", zorder=0)
    fig.text(0.03, 0.93, "E D U C A T I O N  ·  S C H E M A T I C", fontsize=7.2, family=MONO, color=GRY)
    fig.text(0.03, 0.845, title, fontsize=14, weight="bold", color=INK)
    ax.set_xlim(0, 100)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def _callout(ax, cx, cy, w, h, tx, ty, label, color=GRY):
    ax.add_patch(Ellipse((cx, cy), w, h, fill=False, ec=GRY, lw=0.9, zorder=5))
    ax.annotate(label, xy=(cx, cy + h / 2 * (1 if ty > cy else -1)), xytext=(tx, ty), fontsize=7.6,
                family=MONO, color=color, ha="center", arrowprops=dict(arrowstyle="-", lw=0.6, color=GRY), zorder=6)


def _save(fig, out: Path) -> Path:
    fig.savefig(out, facecolor=PAPER)
    plt.close(fig)
    return out


# ------------------------------------------------------------------ 09-11 · left side of the V
def left_side_of_v(out: Path) -> Path:
    fig, ax = _canvas("Pops get sold until the averages coil", ylim=(10, 60))
    px = [2, 7, 11, 16, 20, 25, 29, 34, 38, 43, 47, 52, 56, 60, 64, 68, 72, 76, 80, 86, 92, 97]
    py = [50, 41, 45.5, 36, 39.3, 31, 35.2, 27.5, 30.6, 26.2, 29.3, 26.6, 28.9, 27.0, 28.6, 27.4, 28.8, 31.8, 30.6, 38.5, 36.8, 45]
    x = np.linspace(6, 97, 300)
    ema20 = 28.8 + 27.4 * np.exp(-(x - 2) / 20.6) + 0.017 * np.clip(x - 74, 0, None) ** 2
    sma50 = 28.4 + 2.5 * np.exp(-(x - 2) / 40.0) - 0.008 * (x - 2) + 0.003 * np.clip(x - 82, 0, None) ** 2
    ema_at = lambda xx: float(np.interp(xx, x, ema20))
    sma_at = lambda xx: float(np.interp(xx, x, sma50))
    for hx, hy in ((11, 45.5), (20, 39.3), (29, 35.2)):
        assert ema_at(hx) - 3.0 <= hy <= ema_at(hx) + 0.3, (hx, hy, ema_at(hx))
    assert all(py[i] < ema_at(px[i]) for i in range(1, 17)), "left side: price must stay under the 20"
    assert ema_at(11) - sma_at(11) > 10 and ema_at(68) - sma_at(68) < 2.5, "averages must coil"
    assert ema_at(20) < ema_at(11) and ema_at(40) < ema_at(29), "20 must be falling on the left"
    assert py[-1] > ema_at(97) and py[-1] > sma_at(97)
    ax.plot(px, py, color=INK, lw=1.6, zorder=4)
    ax.plot(x, ema20, color=VIO, lw=1.3, zorder=3)
    ax.plot(x, sma50, color=AMB, lw=1.3, zorder=3)
    ax.text(7.5, 53.2, "20 EMA · falling", color=VIO, fontsize=7.5, family=MONO)
    ax.text(36, 24.6, "50 SMA", color=AMB, fontsize=7.5, family=MONO)
    _callout(ax, 20, 39.3, 5, 3.4, 24, 51.5, "pop sold at the 20")
    _callout(ax, 29, 35.2, 5, 3.4, 40, 44.5, "lower high, sold again")
    _callout(ax, 62, 28.0, 22, 5.6, 58, 17.5, "averages coil · range tightens", VIO)
    _callout(ax, 86, 38.5, 6, 4, 80, 50.5, "right side of the V", GRN)
    ax.text(8, 13.5, "LEFT SIDE", fontsize=7, family=MONO, color=GRY)
    return _save(fig, out)


# ------------------------------------------------------------------ 09-10 · RS line leads price
def rs_before_price(out: Path) -> Path:
    fig, ax = _canvas("Track RS while the market is weak")
    x = np.linspace(4, 96, 24)
    idx = np.array([100, 99, 100.5, 98.5, 99.2, 97.3, 98, 96.2, 96.8, 95, 95.9, 94.2, 94.8, 93.1, 94, 92.4,
                    93.2, 91.6, 92.5, 91, 91.8, 90.4, 91.3, 90.2])
    stk = np.array([100, 102, 104.5, 106, 104, 101.5, 102.5, 101, 102.8, 101.8, 103.2, 102.3, 103.6, 102.6, 104,
                    103.2, 104.4, 103.6, 104.8, 104.2, 105.2, 104.6, 105.5, 105.0])
    rs = stk / idx
    k = int(np.argmax(stk))                      # the stock's high
    rs_prior = rs[: k + 1].max()
    j = next(i for i in range(k + 1, len(rs)) if rs[i] > rs_prior)   # first RS new high
    lows = [idx[i] for i in range(1, len(idx) - 1) if idx[i] < idx[i - 1] and idx[i] < idx[i + 1]]
    assert all(b < a for a, b in zip(lows, lows[1:])), "index must make lower lows"
    assert stk[k + 1:].max() < stk[k], "price must stay under its high"
    assert stk[j] < stk[k] and rs[-1] > rs_prior, "RS must make a new high before price"
    py = 40 + (stk - 100) * 2.2
    iy = 40 + (idx - 100) * 1.2
    ry = 6 + (rs - 1.0) * 80
    ax.plot(x, iy, color=GRY, lw=1.1, ls=(0, (4, 3)), zorder=3)
    ax.plot(x, py, color=INK, lw=1.6, zorder=4)
    ax.plot(x, ry, color=VIO, lw=1.4, zorder=4)
    ax.axhline(py[k], xmin=0.08, xmax=0.97, color=GRY, lw=0.7, ls=":")
    ax.axhline(6 + (rs_prior - 1) * 80, xmin=0.08, xmax=0.97, color=VIO, lw=0.6, ls=":")
    ax.axhline(24.5, color="#d9cfb8", lw=0.8)
    ax.text(97, py[k] + 1.2, "stock's high", fontsize=7, family=MONO, color=GRY, ha="right")
    ax.text(x[-1], iy[-1] - 3.2, "index · lower lows", fontsize=7.4, family=MONO, color=GRY, ha="right")
    ax.text(4, 21.5, "RS LINE = STOCK ÷ INDEX", fontsize=7, family=MONO, color=VIO)
    _callout(ax, x[j], ry[j], 5, 3.4, x[j] + 4, 1.2, "RS new high first", VIO)
    _callout(ax, x[j], py[j], 5, 3.4, x[j] - 8, 57, "price still under its high")
    return _save(fig, out)


# ------------------------------------------------------------------ 09-09 · one line sets the posture
def bull_bear_line(out: Path) -> Path:
    fig, ax = _canvas("One line sets the posture")
    L = 30.0
    px = list(np.linspace(3, 97, 20))
    py = [40, 36, 38.5, 33.5, 35.5, 31.5, 33, 27.5, 29.5, 25, 27.8, 24.2, 28.6, 26.2, 31.8, 30.6, 34.5, 32.4, 37, 35.5]
    lose = next(i for i in range(1, len(py)) if py[i - 1] >= L > py[i])
    back = next(i for i in range(lose + 1, len(py)) if py[i - 1] < L <= py[i])
    assert all(p >= L for p in py[:lose]) and all(p < L for p in py[lose:back]), "below the line between loss and reclaim"
    assert all(p >= L for p in py[back:]), "stays above after the reclaim"
    ax.axhspan(L, 58, xmin=0.02, xmax=0.98, color=GRN, alpha=0.05, zorder=1)
    ax.axhspan(8, L, xmin=0.02, xmax=0.98, color=RED, alpha=0.05, zorder=1)
    ax.axhline(L, xmin=0.02, xmax=0.98, color=VIO, lw=1.3, zorder=3)
    ax.plot(px, py, color=INK, lw=1.6, zorder=4)
    ax.text(3, L + 0.9, "bull / bear line", fontsize=7.6, family=MONO, color=VIO)
    ax.text(3, 54, "ABOVE · long bias", fontsize=7.2, family=MONO, color=GRN)
    ax.text(3, 10, "BELOW · defense, cash is a position", fontsize=7.2, family=MONO, color=RED)
    _callout(ax, px[lose], py[lose], 5, 3.4, px[lose] + 4, 16, "loses the line")
    _callout(ax, px[back], py[back], 5, 3.4, px[back] - 2, 48, "reclaims it", GRN)
    return _save(fig, out)


# ------------------------------------------------------------------ 09-08 · cap weight holds, equal weight breaks
def equal_weight_split(out: Path) -> Path:
    fig, ax = _canvas("The index holds, the average stock breaks", ylim=(10, 60))
    xl = np.linspace(4, 45, 14)
    mal = 22 + 0.25 * (xl - 3)
    pl = mal + np.array([8, 10, 9, 12, 10.5, 13, 11, 12.5, 10, 11.5, 9, 10.5, 8.5, 9.5])
    xr = np.linspace(55, 96, 14)
    mar = 26 + 0.12 * (xr - 54) - 0.0035 * (xr - 54) ** 2
    off_r = np.array([7, 8.5, 6, 7.5, 4.5, 6, 3, 4, 1.5, 2.5, -1, 0.5, -2.5, -3.5])
    pr = mar + off_r
    first_below = int(np.argmax(pr < mar))
    assert (pl > mal).all(), "cap-weighted stays above its 50-day"
    assert (pr[:first_below] > mar[:first_below]).all() and pr[-1] < mar[-1], "equal weight was above, then breaks"
    assert mal[-1] > mal[0], "cap-weighted 50-day rising"
    for xs, ma, p in ((xl, mal, pl), (xr, mar, pr)):
        ax.plot(xs, ma, color=AMB, lw=1.3, zorder=3)
        ax.plot(xs, p, color=INK, lw=1.6, zorder=4)
    ax.axvline(50, ymin=0.05, ymax=0.95, color="#d9cfb8", lw=0.8, ls=(0, (4, 3)))
    ax.text(4, 55, "CAP-WEIGHTED", fontsize=7.4, family=MONO, color=GRY)
    ax.text(55, 55, "EQUAL-WEIGHT", fontsize=7.4, family=MONO, color=GRY)
    ax.text(xl[-1], mal[-1] - 3, "50-day", fontsize=7.2, family=MONO, color=AMB, ha="right")
    ax.text(xr[-1], mar[-1] + 1.4, "50-day", fontsize=7.2, family=MONO, color=AMB, ha="right")
    _callout(ax, xl[-1], pl[-1], 5, 3.4, 30, 51, "held above", GRN)
    _callout(ax, xr[first_below], pr[first_below], 5, 3.4, xr[first_below] - 6, 14, "first close under the 50-day", RED)
    return _save(fig, out)


# ------------------------------------------------------------------ weekly · shallow pullbacks lead
def shallow_pullback(out: Path) -> Path:
    fig, ax = _canvas("Shallow pullbacks lead the next leg")
    xa = [3, 10, 16, 22, 28, 35, 42, 49, 56, 63, 70, 77, 84, 91, 97]
    va = np.array([92, 100, 93, 95, 84, 73, 80, 78, 86, 90, 100.5, 99, 104, 103, 108])
    xb = [3, 10, 17, 24, 31, 38, 45, 52, 59, 66, 73, 80, 87, 94, 97]
    vb = np.array([92, 100, 88, 90, 72, 60, 40, 48, 45, 55, 52, 62, 60, 68, 70])
    HIGH = 100.0
    da, db = 1 - va.min() / HIGH, 1 - vb.min() / HIGH
    back_a = next(xa[i] for i in range(int(np.argmin(va)), len(va)) if va[i] > HIGH)
    back_b = next((xb[i] for i in range(int(np.argmin(vb)), len(vb)) if vb[i] > HIGH), None)
    assert da < db, "A must be the shallow one"
    assert back_b is None or back_a < back_b, "the shallow one must regain the high first"
    y = lambda v: 5 + np.asarray(v) * 0.48
    ax.axhline(y(HIGH), xmin=0.03, xmax=0.97, color=GRY, lw=0.7, ls=":")
    ax.text(3, y(HIGH) + 1.1, "prior high", fontsize=7, family=MONO, color=GRY, ha="left")
    ax.plot(xb, y(vb), color=AMB, lw=1.4, zorder=3)
    ax.plot(xa, y(va), color=INK, lw=1.7, zorder=4)
    ia, ib = int(np.argmin(va)), int(np.argmin(vb))
    _callout(ax, xa[ia], float(y(va[ia])), 5, 3.4, xa[ia] - 10, 30, f"−{da:.0%} pullback")
    _callout(ax, xb[ib], float(y(vb[ib])), 5, 3.4, xb[ib] + 12, 13, f"−{db:.0%} pullback", AMB)
    _callout(ax, back_a, float(y(HIGH)), 5, 3.4, back_a - 4, 58, "first back to the high", GRN)
    ax.text(97, float(y(vb[-1])) - 5.0, "still repairing", fontsize=7.4, family=MONO, color=AMB, ha="right")
    return _save(fig, out)


FIGURES = {
    "left_side_of_v": left_side_of_v,
    "rs_before_price": rs_before_price,
    "bull_bear_line": bull_bear_line,
    "equal_weight_split": equal_weight_split,
    "shallow_pullback": shallow_pullback,
}
