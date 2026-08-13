"""Damage, measured with error bars.

His objective function, stated 2026-08-12:

    "The goal isn't more return — it's less damage. −4.9% max drawdown against
     SPY's −8.9% since inception."

That sentence is why this module exists, and it also contains the trap. **A max
drawdown is a path statistic: one number from one history, n=1.** Two of them
side by side look like a comparison and are not one. "−4.9% versus −8.9%" could
be a real difference in how a book handles damage, or it could be that the one
worst week of a single sample happened to fall where the overlay was on.

I said yesterday that drawdown is cheaper to measure than a directional hit
rate. That is true and it is not free: what makes it cheap is that both series
are observed on the SAME days, so the comparison can be paired and resampled.
Without the resampling it is the weakest possible claim, not the strongest.

So every comparison here comes back with an interval, from a **paired circular
block bootstrap**:

  * **paired** — book and control are resampled on the same drawn dates, so the
    market's own path is not what varies between them. Only the overlay is.
  * **block** — daily returns are not independent. Volatility clusters, and a
    drawdown is precisely a run of bad days. An i.i.d. bootstrap destroys the
    clustering that creates drawdowns and would report a flatteringly tight
    interval around a number it has broken.
  * **circular** — blocks wrap, so every observation has equal weight instead of
    the ends being under-sampled.

The block length is a free parameter and is therefore swept, reported, and never
chosen quietly. See `bootstrap_sensitivity`.
"""
from __future__ import annotations

import math
import random
import statistics as st

# Roughly a trading month. Long enough to carry a volatility cluster, short
# enough that a two-year sample still contains many independent blocks. Swept
# in `bootstrap_sensitivity` rather than trusted.
DEFAULT_BLOCK = 21
DEFAULT_DRAWS = 2000


def equity(returns: list[float], start: float = 1.0) -> list[float]:
    """Compound a daily return series into an equity curve, INCLUDING day zero.

    The curve is one longer than the returns because inception is itself a peak.
    Omitting it was a real bug: a book that opened by losing 10% and never
    recovered reported a max drawdown of zero, because the running peak was
    seeded at the value AFTER the first loss. Money you were down from the day
    you started is money you were down.
    """
    out, v = [start], start
    for r in returns:
        v *= (1.0 + r)
        out.append(v)
    return out


def underwater(curve: list[float]) -> list[float]:
    """Fraction below the running peak, at every point. Never positive."""
    out, peak = [], -math.inf
    for v in curve:
        peak = max(peak, v)
        out.append(v / peak - 1.0 if peak > 0 else 0.0)
    return out


def max_drawdown(returns: list[float]) -> dict:
    """The deepest peak-to-trough, with where it happened.

    Returned as a dict rather than a float because the index is what makes a
    drawdown checkable: a book and a control whose worst runs are in different
    places are failing differently, and a bare number hides that.
    """
    if not returns:
        return {"max_drawdown": 0.0, "trough_index": None, "peak_index": None,
                "n": 0}
    # Indices are into the equity curve, where 0 is inception and 1 is after the
    # first return.
    curve = equity(returns)
    uw = underwater(curve)
    trough = min(range(len(uw)), key=lambda i: uw[i])
    peak = max(range(trough + 1), key=lambda i: curve[i])
    return {"max_drawdown": round(uw[trough], 6), "trough_index": trough,
            "peak_index": peak, "n": len(returns)}


def summary(returns: list[float]) -> dict:
    """Damage first, return second — deliberately in that order."""
    if not returns:
        return {"n": 0, "max_drawdown": 0.0, "total_return": 0.0,
                "time_underwater": 0.0, "ann_vol": 0.0}
    curve = equity(returns)
    uw = underwater(curve)
    sd = st.pstdev(returns) if len(returns) > 1 else 0.0
    return {
        "n": len(returns),
        "max_drawdown": max_drawdown(returns)["max_drawdown"],
        "total_return": round(curve[-1] - 1.0, 6),
        # How much of the life was spent below a prior peak. A book with the
        # same max drawdown but half the time underwater is a different animal,
        # and a single worst-case number cannot tell them apart.
        "time_underwater": round(sum(1 for x in uw if x < -1e-12) / len(uw), 4),
        "ann_vol": round(sd * math.sqrt(252), 6),
    }


def _blocks(n: int, block: int, rng: random.Random) -> list[int]:
    """Indices for one circular block-bootstrap draw of length n."""
    idx = []
    while len(idx) < n:
        s = rng.randrange(n)
        idx.extend((s + k) % n for k in range(min(block, n - len(idx))))
    return idx


def drawdown_advantage(book: list[float], control: list[float],
                       block: int = DEFAULT_BLOCK, draws: int = DEFAULT_DRAWS,
                       seed: int = 7, conf: float = 0.90) -> dict:
    """How much less damage the book took, with an interval. Never a bare number.

    `advantage` is positive when the book's drawdown is SHALLOWER than the
    control's, so a positive interval that excludes zero is the claim "this
    reduced damage" actually being supported.

    Both series must be the same length and aligned day-for-day; that pairing is
    the entire source of the method's power, and a caller that pads or truncates
    one side has silently compared two different markets.
    """
    if len(book) != len(control):
        raise ValueError(
            f"book has {len(book)} days and control {len(control)}; the "
            "comparison is paired and cannot be made across different windows")
    if not book:
        raise ValueError("no observations")
    if block < 1:
        raise ValueError("block must be at least 1 day")

    # Drawdowns are NEGATIVE, so the shallower book has the LARGER value and the
    # difference runs book minus control. Writing it the other way round -- which
    # is how it shipped for an hour -- makes every genuine improvement report as
    # a kill, and the test fixture for "a hedge that fires in the bad stretch"
    # is what caught it. Class: sign convention, the oldest error in this repo.
    book_dd = max_drawdown(book)["max_drawdown"]
    control_dd = max_drawdown(control)["max_drawdown"]
    obs = book_dd - control_dd

    rng = random.Random(seed)
    diffs = []
    n = len(book)
    for _ in range(draws):
        idx = _blocks(n, block, rng)
        b = [book[i] for i in idx]
        c = [control[i] for i in idx]
        diffs.append(max_drawdown(b)["max_drawdown"]
                     - max_drawdown(c)["max_drawdown"])
    diffs.sort()
    lo_i = int((1 - conf) / 2 * draws)
    hi_i = min(draws - 1, int((1 + conf) / 2 * draws))
    lo, hi = diffs[lo_i], diffs[hi_i]
    # Strictly worse, and exactly-equal, counted apart. Folding ties into
    # "worse" inflates the failure rate on any series with calm stretches, where
    # a resample that draws no drawdown at all gives both sides a flat zero --
    # that is the two being indistinguishable, not the book losing.
    worse = sum(1 for d in diffs if d < 0) / draws
    tied = sum(1 for d in diffs if d == 0) / draws
    return {
        "book_max_drawdown": book_dd,
        "control_max_drawdown": control_dd,
        "advantage": round(obs, 6),
        "ci_low": round(lo, 6), "ci_high": round(hi, 6), "conf": conf,
        "p_book_worse": round(worse, 4), "p_tied": round(tied, 4),
        "excludes_zero": bool(lo > 0 or hi < 0),
        "block": block, "draws": draws, "n_days": n,
        "note": _explain(obs, lo, hi, worse, n),
    }


def _explain(obs: float, lo: float, hi: float, worse: float, n: int) -> str:
    """One whole sentence per branch — the shared-prefix shape has bitten here
    three times."""
    head = (f"observed advantage {obs * 100:+.1f} points of drawdown over "
            f"{n} days")
    if lo > 0:
        return (f"{head}; the interval [{lo * 100:+.1f}, {hi * 100:+.1f}] "
                f"excludes zero — the book took less damage")
    if hi < 0:
        return (f"{head}; the interval [{lo * 100:+.1f}, {hi * 100:+.1f}] "
                f"excludes zero on the wrong side — the book took MORE damage")
    return (f"{head}; the interval [{lo * 100:+.1f}, {hi * 100:+.1f}] straddles "
            f"zero and the book is worse in {worse:.0%} of resamples — this "
            f"sample cannot tell the two apart")


def bootstrap_sensitivity(book: list[float], control: list[float],
                          blocks=(1, 5, 10, 21, 42), draws: int = 500,
                          seed: int = 7) -> list[dict]:
    """The block length, swept — because it is a free parameter.

    Block 1 is the i.i.d. case and is included ON PURPOSE. The textbook reason
    to reject it is that destroying volatility clustering destroys the runs that
    MAKE drawdowns. Whether that shows up as a narrower interval depends on the
    series -- on a synthetic fixture the two came out within a thousandth of
    each other -- so the sweep is here to be read on real data rather than to
    confirm something asserted in advance.
    """
    return [{"block": b,
             **{k: v for k, v in
                drawdown_advantage(book, control, block=b, draws=draws,
                                   seed=seed).items()
                if k in ("advantage", "ci_low", "ci_high", "p_book_worse",
                         "excludes_zero")}}
            for b in blocks]
