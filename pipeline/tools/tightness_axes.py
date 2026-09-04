"""Is compression a stock-picker or a clock? -- and does it stack with RS.

2026-08-23 (Andy: "我先理解哪个是选股,哪个是 timing... 这三个是否和我们其他
信号可以组成 timing/选股/排序的 edge").

`atr_pctl_252` beat every other tightness reading (tightness_grid.py), but a
reading can win for two very different reasons and the two have opposite uses:

  SELECTION (选股)  among the names available TODAY, it ranks which to take.
                   Test: rank within the day, so every comparison is between
                   two names on the same tape. Market conditions cancel.
  TIMING (timing)  for ONE name, it says when this name is ready. Test: rank
                   within the ticker (each reading against that name's own
                   distribution), so cross-name differences cancel.

Raw performance mixes both. This splits them, then asks whether the surviving
axis stacks with a signal from the other axis -- RS-line self-percentile, which
is our closest thing to a pure ranker.

    python -m pipeline.tools.tightness_axes --out data/research/tightness_2026-08/
"""
from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.tools.tightness_grid import grid, setup_mask, frame_outcome

BARS = Path("data/research/scanner_validation_2026-08/event_bars.pkl")


def bar_signals(df: pd.DataFrame, spy: pd.Series) -> pd.DataFrame:
    """The non-volatility signals we can rebuild from bars alone, so the
    combination test uses the same definitions the nightly universe uses
    (rs_line_pctl: see pipeline/adapters/yfinance_adapter.py)."""
    c, h, v = df["Close"], df["High"], df["Volume"]
    out = pd.DataFrame(index=df.index)
    a = pd.concat([c.rename("c"), spy.rename("b")], axis=1, join="inner").dropna()
    rs = (a["c"] / a["b"]).reindex(df.index)
    for n in (21, 63):
        out[f"rs_pctl_{n}"] = rs.rolling(n).apply(
            lambda w: (w <= w[-1]).mean() * 100, raw=True)
    out["hi20"] = (c >= c.rolling(20).max() - 1e-9)
    out["dist_52wh"] = (c / c.rolling(252, min_periods=130).max() - 1) * 100
    # pocket pivot (Morales): up day whose volume tops the largest down-day
    # volume of the prior 10 sessions. `where` leaves NaN on up days, and a
    # rolling max over a window that is all-NaN is NaN -- which compares False
    # against everything and silently zeroed this column on the first run.
    down_vol = v.where(c < c.shift())
    prior_down_max = down_vol.shift(1).rolling(10, min_periods=1).max()
    out["pp"] = (c > c.shift()) & (v > prior_down_max.fillna(0))
    out["pp_count_10d"] = out["pp"].rolling(10).sum()
    return out


def collect(bars_path: Path = BARS) -> pd.DataFrame:
    bars = pickle.load(open(bars_path, "rb"))
    spy = bars["SPY"]["Close"]
    rows = []
    for t, df in bars.items():
        if t == "SPY" or len(df) < 150:
            continue
        m = grid(df)
        sig = bar_signals(df, spy)
        mask = setup_mask(df, m).values
        c = df["Close"]
        for i in np.where(mask)[0]:
            if i < 130:
                continue
            res = frame_outcome(c, i, float(m["atr"].iloc[i]))
            if res is None:
                continue
            p0 = float(c.iloc[i])
            rows.append({
                "ticker": t, "date": c.index[i], "outcome": res,
                "fwd20": (float(c.iloc[i + 20]) / p0 - 1) * 100,
                "atr_pctl_252": float(m["atr14__pct252"].iloc[i]),
                "atr_pctl_63": float(m["atr14__pct63"].iloc[i]),
                # ATR%, not ADR% -- renamed 2026-09-04 with the pipeline column.
                # It holds atr14__abs; calling it adr_pct made a research frame
                # disagree with the production column of the same name.
                "atr_pct": float(m["atr14__abs"].iloc[i]),
                "rs_pctl_21": float(sig["rs_pctl_21"].iloc[i]),
                "rs_pctl_63": float(sig["rs_pctl_63"].iloc[i]),
                "dist_52wh": float(sig["dist_52wh"].iloc[i]),
                "pp_count_10d": float(sig["pp_count_10d"].iloc[i]),
            })
    d = pd.DataFrame(rows).sort_values(["ticker", "date"])
    d["gap"] = d.groupby("ticker")["date"].diff().dt.days
    d["first_day"] = d["gap"].isna() | (d["gap"] > 7)
    return d


def _win(x) -> float:
    return (x["outcome"] == "win").mean() * 100


def axis_table(d: pd.DataFrame, col: str) -> pd.DataFrame:
    """Raw vs within-day (selection) vs within-ticker (timing) tercile spread."""
    d = d.copy()
    d["raw"] = d[col]
    day_n = d.groupby("date")[col].transform("size")
    d["within_day"] = np.where(day_n >= 5, d.groupby("date")[col].rank(pct=True) * 100, np.nan)
    tk_n = d.groupby("ticker")[col].transform("size")
    d["within_ticker"] = np.where(tk_n >= 5, d.groupby("ticker")[col].rank(pct=True) * 100, np.nan)
    out = []
    for axis in ("raw", "within_day", "within_ticker"):
        x = d.dropna(subset=[axis])
        if len(x) < 150:
            continue
        q = pd.qcut(x[axis], 3, labels=["tight", "mid", "loose"], duplicates="drop")
        w = x.assign(q=q).groupby("q", observed=True).apply(_win, include_groups=False)
        out.append({"axis": axis, "n": len(x), "tight": round(w.get("tight", np.nan), 1),
                    "loose": round(w.get("loose", np.nan), 1),
                    "spread": round(w.get("tight", np.nan) - w.get("loose", np.nan), 1)})
    return pd.DataFrame(out)


def combo(d: pd.DataFrame, a: str, b: str, a_lo_is_good=True) -> pd.DataFrame:
    """2x2: does the tightness axis add anything on top of a ranking signal?"""
    x = d.dropna(subset=[a, b]).copy()
    am, bm = x[a].median(), x[b].median()
    x["A"] = np.where((x[a] <= am) == a_lo_is_good, f"{a}紧", f"{a}松")
    x["B"] = np.where(x[b] >= bm, f"{b}强", f"{b}弱")
    g = x.groupby(["A", "B"], observed=True).apply(
        lambda s: pd.Series({"n": len(s), "win": round(_win(s), 1),
                             "fwd20": round(s.fwd20.median(), 2)}), include_groups=False)
    return g.reset_index()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bars", type=Path, default=BARS)
    ap.add_argument("--out", type=Path, default=Path("data/research/tightness_2026-08"))
    args = ap.parse_args(argv)
    d = collect(args.bars)
    args.out.mkdir(parents=True, exist_ok=True)
    d.to_csv(args.out / "axes_sample.csv", index=False)
    fd = d[d.first_day]
    print(f"{len(d)} setup-days, {len(fd)} first-days, base win {_win(fd):.1f}%\n")
    for col in ("atr_pctl_252", "atr_pctl_63", "atr_pct"):
        print(f"== {col} ==")
        print(axis_table(fd, col).to_string(index=False), "\n")
    print("== 组合: 压缩(timing) x RS线63日自百分位(选股) ==")
    print(combo(fd, "atr_pctl_252", "rs_pctl_63").to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
