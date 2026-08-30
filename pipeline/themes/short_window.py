"""Three windows on the same four-state board -- 2w / 1m / 3m.

2026-08-28 (Andy, after Clement_Ang17's 2-week board read 31 Lagging while
ours read 8): "我们需要短窗口的敏感度！是在找 canary in the mines... 比如
lagging 的开始更加多，这个是最重要的特征" and "以后还要有 1m 的窗口".

Why this does not contradict the month-scale choice in `rs_engine`: that
validation rejected short windows for **which theme will outperform** -- the
Leading-minus-Lagging spread flipped sign between half-samples. This module
asks a different question -- **how many themes are deteriorating** -- and a
window can be too noisy to rank names while still being the right length to
count them. The two live side by side and answer different questions; the
月度 board stays the one that sizes positions.

Axes (identical shape at all three lengths, only the constants move):
    level    = cumulative excess vs the benchmark over L sessions
    momentum = excess over M sessions (the RS line's slope; RRG RS-Momentum)
    state    = Leading / Weakening / Improving / Lagging by the two signs

Theme aggregates are EQUAL-WEIGHTED constituent baskets, so a cap-weighted
benchmark can beat most themes at once -- that is a real reading (breadth),
not an artefact, but it means the absolute Lagging count is not comparable
across dashboards that weight differently. **The comparable quantity is the
CHANGE in the Lagging share**, which is what the canary reads.
"""
from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

# (level lookback, momentum lookback) in trading sessions -- BOTH are plain
# lookbacks now; momentum is the recent excess, not a difference of two.
# 2W..10W is the ladder Clement_Ang17's board plots as an x-axis -- his chart
# is a TRAJECTORY across these five, not a point, which is why a single state
# never reproduced it. Andy 2026-08-28: "他有 2W 4W 6W 8W 10W... 以后我们都需要".
# 1m/3m stay as named aliases of the two the Themes page already reads.
WINDOWS: Dict[str, tuple] = {
    "2w": (10, 5),
    "4w": (20, 10),
    "6w": (30, 15),
    "8w": (40, 20),
    "10w": (50, 25),
    "1m": (21, 10),      # alias-ish of 4w; kept because the page names months
    "3m": (63, 21),      # the validated, position-sizing board (rs_engine)
}
LADDER = ("2w", "4w", "6w", "8w", "10w")   # the trajectory, near -> far
STATES = ("Leading", "Weakening", "Improving", "Lagging")


def basket_nav(bars: Mapping[str, pd.DataFrame], tickers: Sequence[str],
               min_names: int = 3) -> Optional[pd.Series]:
    """Equal-weighted daily-rebalanced NAV of the constituents we have bars for.

    Equal-weighted on purpose: a theme is a claim about its members, not about
    its largest member. Returns None when too few constituents are available --
    a two-name 'theme' is a pair trade, not a breadth reading.
    """
    cols = [bars[t]["Close"].rename(t) for t in tickers if t in bars]
    if len(cols) < min_names:
        return None
    df = pd.concat(cols, axis=1, sort=True).dropna(how="all")
    ret = df.pct_change().mean(axis=1, skipna=True)
    return (1.0 + ret.fillna(0.0)).cumprod()


def classify(level: float, momentum: float) -> Optional[str]:
    """Quadrant from the two axes. A tie goes to the WEAKER state: exactly
    flat momentum is not improvement, and a steady pace with equal windows
    sits at ~0 by construction, so the sign there is float noise rather than
    a reading -- letting it fall to Leading would manufacture a signal out of
    rounding. (rs_engine's month-scale gate uses unequal windows on purpose,
    where a steady outperformer scores negative; here the windows are equal
    and the same steadiness lands on zero.)"""
    if not (np.isfinite(level) and np.isfinite(momentum)):
        return None
    if level > 0:
        return "Leading" if momentum > 0 else "Weakening"
    return "Improving" if momentum > 0 else "Lagging"


def _excess(nav: pd.Series, bench: pd.Series, i: int, n: int) -> float:
    if i - n < 0:
        return np.nan
    return (nav.iloc[i] / nav.iloc[i - n] - 1.0) - (bench.iloc[i] / bench.iloc[i - n] - 1.0)


def state_series(nav: pd.Series, bench: pd.Series, window: str) -> pd.Series:
    """The four-state at every session, for one theme and one window.

    MOMENTUM IS FIRST ORDER -- the recent excess itself, i.e. the slope of the
    RS line, which is what an RRG's RS-Momentum axis measures. The first
    version of this module used `near excess - prior excess` (an
    ACCELERATION, second order), copied out of habit from rs_engine, whose
    month-scale gate deliberately uses unequal windows for a different job.
    That was simply the wrong axis: on 2026-08-28 it produced 10/21/14/11
    against Clement_Ang17's 17/10/6/31, while first order gives 21/10/8/17 --
    Weakening matches exactly, Improving within 2, Leading within 4. Andy
    caught the wrong attribution ("我们的成分基本一样。所以是计算的内容不同?").

    The two axes MUST use different lookbacks: with L == M both are the same
    number and the board collapses to Leading/Lagging with nothing in the
    transition quadrants (measured: 31/0/0/25).
    """
    L, M = WINDOWS[window]
    idx = nav.index.intersection(bench.index)
    nav, bench = nav.reindex(idx), bench.reindex(idx)
    out: List[Optional[str]] = []
    for i in range(len(idx)):
        if i < L + M:
            out.append(None)
            continue
        out.append(classify(_excess(nav, bench, i, L), _excess(nav, bench, i, M)))
    return pd.Series(out, index=idx, name=window)


def board(themes: Mapping[str, Sequence[str]], bars: Mapping[str, pd.DataFrame],
          benchmark: str = "SPY", window: str = "2w") -> pd.DataFrame:
    """One column per theme, one row per session, values = state (or None)."""
    bench = bars[benchmark]["Close"]
    cols = {}
    for name, tickers in themes.items():
        nav = basket_nav(bars, tickers)
        if nav is None:
            continue
        cols[name] = state_series(nav, bench, window)
    return pd.DataFrame(cols)


def shares(board_df: pd.DataFrame) -> pd.DataFrame:
    """Per-session counts and shares of each state.

    `measurable` is carried so a change in the denominator can never be read
    as a change in the market -- the count alone lies when the theme list
    grows (see DATA_RELIABILITY: a reading without its denominator).
    """
    rows = []
    for date, row in board_df.iterrows():
        vals = [v for v in row.tolist() if v]
        n = len(vals)
        rec = {"date": date, "measurable": n}
        for s in STATES:
            c = sum(1 for v in vals if v == s)
            rec[s] = c
            rec[f"{s}_share"] = (c / n) if n else np.nan
        rows.append(rec)
    return pd.DataFrame(rows).set_index("date")


TREND_DAYS = 90            # sessions of state history shipped for the page
LADDER_JSON = "data/output/theme_ladder.json"
LADDER_LOG = "data/history/theme_ladder.csv"


def build(themes: Mapping[str, Sequence[str]], bars: Mapping[str, pd.DataFrame],
          benchmark: str = "SPY") -> dict:
    """The five-rung board for today, plus the state of every theme on each rung.

    Shipped as a READING, not a signal. The canary claim it was built to test
    ("a rising Lagging share precedes drawdown") measured 20% vs a 12% baseline
    in-sample and 17% vs 12% on the holdout -- direction consistent, neither
    significant, and with 10 and 6 de-clustered triggers the test CANNOT reach
    p<0.05 below a 40% hit rate. That NULL is a property of the sample size,
    not of the market (claims.jsonl: canary-lagging-share). Forward evidence
    accumulates in LADDER_LOG; revisit when the ledger has ~60 triggers.

    On comparability: after the momentum axis was corrected to first order
    (see `state_series`), our 2w board reads 21/10/8/17 against
    Clement_Ang17's 17/10/6/31 the same day -- Weakening exact, Improving
    within 2, Leading within 4. The one residual is Lagging (17 vs 31), and a
    15-cell (L, M) grid could not close it: no window combination reaches 31.
    That residual is composition -- our theme constituents come from a
    momentum-screened universe, so the baskets are genuinely stronger against
    SPY. Counts still travel poorly across dashboards; the CHANGE travels.
    """
    bench = bars[benchmark]["Close"]
    rungs, per_theme = {}, {}
    for w in LADDER:
        b = board(themes, bars, benchmark=benchmark, window=w)
        if b.empty:
            continue
        sh = shares(b)
        last = sh.iloc[-1]
        rungs[w] = {s: int(last[s]) for s in STATES}
        rungs[w]["measurable"] = int(last["measurable"])
        rungs[w]["lagging_share"] = None if not last["measurable"] else round(float(last["Lagging_share"]), 4)
        # 5-session change in the Lagging share -- the canary's own reading
        d5 = sh["Lagging_share"].diff(5).iloc[-1]
        rungs[w]["lagging_share_d5"] = None if pd.isna(d5) else round(float(d5), 4)
        for name, st in b.iloc[-1].items():
            per_theme.setdefault(name, {})[w] = st
    # The counts OVER TIME, not just today's snapshot -- Andy 2026-08-28:
    # "我不需要你给我金丝雀这样的结论，但是我要能看到 4 态的数量变化 aka
    # leading theme 减少，lagging 开始变多". A single day's board cannot show
    # that; the deltas and the series can.
    hist = {}
    for w in LADDER:
        b = board(themes, bars, benchmark=benchmark, window=w)
        if b.empty:
            continue
        sh = shares(b).dropna(subset=["Lagging_share"])
        sh = sh[sh["measurable"] >= 1]
        if sh.empty:
            continue
        tail = sh.tail(TREND_DAYS)
        hist[w] = {
            "dates": [str(d.date()) for d in tail.index],
            **{s: [int(v) for v in tail[s]] for s in STATES},
            "measurable": [int(v) for v in tail["measurable"]],
            "delta": {s: {f"d{n}": (int(sh[s].iloc[-1] - sh[s].iloc[-1 - n])
                                    if len(sh) > n else None)
                          for n in (5, 10, 21)} for s in STATES},
        }

    return {
        "as_of": str(bench.index[-1].date()),
        "history": hist,
        "benchmark": benchmark,
        "ladder": list(LADDER),
        "rungs": rungs,
        "themes": per_theme,
        "note": ("readings only -- the canary claim is unproven and underpowered; "
                 "absolute counts are not comparable across dashboards that weight "
                 "themes differently, only the change in share is"),
    }


def fetch_bars(tickers: Sequence[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
    """Daily bars for the constituents. The one network call in this module."""
    import yfinance as yf
    data = yf.download(list(tickers), period=period, interval="1d",
                       auto_adjust=True, progress=False, group_by="ticker", threads=True)
    out: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        try:
            df = data[t].dropna(how="all")
        except (KeyError, TypeError):
            continue
        if len(df) > 60:
            out[t] = df
    return out


def archive_ladder(payload: Mapping, path=None) -> int:
    """Append tonight's rung counts. One row per (date, rung).

    This is the forward ledger the canary claim needs: the retrospective test
    had 10 in-sample and 6 holdout triggers, below the 40% hit rate the sample
    would need to reach p<0.05 at all. Only accumulated forward evidence can
    settle it, and only if it is recorded from the start.
    """
    import csv
    from pathlib import Path
    path = Path(path or LADDER_LOG)
    fields = ["date", "rung", "measurable", *STATES, "lagging_share", "lagging_share_d5"]
    date = payload["as_of"]
    old = []
    if path.exists():
        with path.open(newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != date]
    new = [{"date": date, "rung": w, "measurable": r["measurable"],
            **{s: r[s] for s in STATES},
            "lagging_share": r["lagging_share"], "lagging_share_d5": r["lagging_share_d5"]}
           for w, r in payload["rungs"].items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w_ = csv.DictWriter(fh, fieldnames=fields)
        w_.writeheader()
        for r in old + new:
            w_.writerow({k: r.get(k) for k in fields})
    return len(old) + len(new)
