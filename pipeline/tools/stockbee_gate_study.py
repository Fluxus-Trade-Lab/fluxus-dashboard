"""Do Stockbee's own setup qualifiers separate a 4% breakout?

Pre-registration: data/research/stockbee_2026-08/prereg_setup_gates.md
(written and committed BEFORE this file computed anything).

He publishes nine qualifiers for picking which rows of the 4% scan to buy.
Three of them can be mechanised from OHLC alone:

    B3  not up 3 days in a row prior to the breakout day   <- his only hard number
    B2  prior day is a narrow range day or a negative bar
    B1  the breakout day closes at or near its high

The other six need float, a definition of "start of the move", or an eye.
His two VOLUME conditions (v > v1, v > 100000) are NOT tested here: the
price panel carries OHLC only. Said plainly rather than quietly skipped.

Metric is excess over SPY on purpose. The 2026-08-19 b4_gates study found
gates that separated cleanly (p=0.0022) yet whose survivors still trailed
SPY -- separation is not an edge, so absolute medians are not the question.

Run:  python -m pipeline.tools.stockbee_gate_study            # discovery only
      python -m pipeline.tools.stockbee_gate_study --holdout  # burns the holdout
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd  # noqa: E402

PANEL = Path.home() / "Documents/AI-Trading-System/.cache/price_panel.pkl"
EVENTS = Path("data/history/ticker_events.csv")
SCREENER = "gainers_4pct"
MIN_GAP_SESSIONS = 10          # de-overlap: same ticker inside 10 sessions -> keep first
NEAR_HIGH = 0.70               # B1 threshold, fixed in the prereg
NARROW_LOOKBACK = 9            # B2: prior day vs median range of t-10..t-2


def arm(ticker: str) -> str:
    """discovery / holdout, decided by the ticker alone so it is reproducible."""
    h = int(hashlib.md5(ticker.encode()).hexdigest()[:2], 16)
    return "discovery" if h % 10 < 7 else "holdout"


def gates(df: pd.DataFrame, i: int) -> dict | None:
    """B1/B2/B3 for the event at positional index i. None if not enough bars."""
    if i < 10 or i >= len(df):
        return None
    c, h, l = df["Close"], df["High"], df["Low"]
    b3 = not (c.iloc[i - 1] > c.iloc[i - 2] > c.iloc[i - 3] > c.iloc[i - 4])
    prior_rng = (h.iloc[i - 1] - l.iloc[i - 1]) / c.iloc[i - 1]
    hist = ((h - l) / c).iloc[i - 10:i - 1]
    b2 = bool(prior_rng < hist.median()) or bool(c.iloc[i - 1] < c.iloc[i - 2])
    rng = h.iloc[i] - l.iloc[i]
    b1 = True if rng <= 0 else bool((c.iloc[i] - l.iloc[i]) / rng >= NEAR_HIGH)
    return {"B3": b3, "B2": b2, "B1": b1, "Ball": b3 and b2 and b1}


def build(panel: dict) -> pd.DataFrame:
    spy = panel["SPY"]["Close"]
    by_ticker: dict[str, list[str]] = {}
    with EVENTS.open() as fh:
        for r in csv.DictReader(fh):
            if r["screener"] == SCREENER:
                by_ticker.setdefault(r["ticker"], []).append(r["date"])

    rows = []
    for t, dates in by_ticker.items():
        df = panel.get(t)
        if df is None or len(df) < 20:
            continue
        idx = df.index
        last_i = -10 ** 9
        for d in sorted(set(dates)):
            ts = pd.Timestamp(d)
            pos = idx.searchsorted(ts)
            if pos >= len(idx) or idx[pos] != ts:
                continue                                  # event day not a bar we hold
            if pos - last_i < MIN_GAP_SESSIONS:
                continue                                  # de-overlap
            g = gates(df, pos)
            if g is None:
                continue
            row = {"ticker": t, "date": d, "arm": arm(t), **g}
            ok = False
            for hz in (3, 5):
                if pos + hz >= len(idx):
                    row[f"excess_{hz}"] = None
                    continue
                sp0 = spy.reindex([idx[pos]]).iloc[0]
                sp1 = spy.reindex([idx[pos + hz]]).iloc[0]
                if pd.isna(sp0) or pd.isna(sp1):
                    row[f"excess_{hz}"] = None
                    continue
                stock = df["Close"].iloc[pos + hz] / df["Close"].iloc[pos] - 1
                row[f"excess_{hz}"] = float(stock - (sp1 / sp0 - 1))
                ok = True
            if ok:
                last_i = pos
                rows.append(row)
    return pd.DataFrame(rows)


def placebo(d: pd.DataFrame, col: str = "excess_5", n: int = 20) -> None:
    """How often does a MEANINGLESS split of the same tickers look significant?

    Added after the discovery run: the pre-registered control (first letter
    A-M) came back at p<0.0001, which is not something a ticker's spelling
    should do. Twenty hash splits say ~3/20 clear p<0.05 where 1/20 is
    expected -- so p in this design runs about 3x optimistic. Reported rather
    than corrected: the honest reading is to treat p<0.05 here as p<0.15.
    """
    from scipy.stats import mannwhitneyu
    sub = d[d[col].notna()]
    sig = 0
    for k in range(n):
        flag = sub["ticker"].map(
            lambda t: int(hashlib.md5((t + f"salt{k}").encode()).hexdigest()[:8], 16) % 100 < 67)
        a, b = sub.loc[flag, col], sub.loc[~flag, col]
        if mannwhitneyu(a, b, alternative="two-sided").pvalue < 0.05:
            sig += 1
    print(f"\n  placebo: {sig}/{n} meaningless ticker splits reach p<0.05 on {col} "
          f"(1/{n} expected) -- p here is roughly {max(sig,1)}x optimistic")


def bad_bars(d: pd.DataFrame, col: str = "excess_5", cut: float = 1.0) -> None:
    """Name the rows whose forward return is not credible.

    Medians are robust so these do not move any number reported here, but a
    +4598% row is a split or a bad bar, not a trade, and a silently-kept one
    would wreck any mean-based follow-up.
    """
    bad = d[d[col].notna() & (d[col].abs() > cut)]
    if len(bad):
        print(f"\n  implausible rows (|{col}| > {cut*100:.0f}%): {len(bad)} of {d[col].notna().sum()}"
              f" -- {', '.join(f'{r.ticker} {r.date} {r._asdict()[col]*100:+.0f}%' for r in list(bad.itertuples())[:4])}"
              f"{' ...' if len(bad) > 4 else ''}")


def report(d: pd.DataFrame, label: str) -> None:
    from scipy.stats import mannwhitneyu
    print(f"\n===== {label}  (n={len(d)}, {d['ticker'].nunique()} tickers, "
          f"{d['date'].min()} .. {d['date'].max()}) =====")
    for hz in (3, 5):
        col = f"excess_{hz}"
        sub = d[d[col].notna()]
        if sub.empty:
            continue
        base = sub[col].median()
        print(f"\n  --- excess vs SPY, +{hz}d --- (all rows median {base*100:+.2f}%, "
              f">0: {(sub[col] > 0).mean()*100:.1f}%, n={len(sub)})")
        print(f"  {'gate':<7}{'pass n':>7}{'pass med':>10}{'fail n':>7}{'fail med':>10}"
              f"{'diff pp':>9}{'p':>9}{'pass>0':>8}")
        for g in ("B3", "B2", "B1", "Ball", "ctrl"):
            flag = (sub["ticker"].str[0] <= "M") if g == "ctrl" else sub[g]
            a, b = sub.loc[flag, col], sub.loc[~flag, col]
            if len(a) < 20 or len(b) < 20:
                print(f"  {g:<7}{len(a):>7}{'--':>10}{len(b):>7}{'--':>10}  (too few)")
                continue
            p = mannwhitneyu(a, b, alternative="two-sided").pvalue
            print(f"  {g:<7}{len(a):>7}{a.median()*100:>9.2f}%{len(b):>7}"
                  f"{b.median()*100:>9.2f}%{(a.median()-b.median())*100:>8.2f}"
                  f"{p:>9.4f}{(a > 0).mean()*100:>7.1f}%")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--holdout", action="store_true",
                    help="also run the holdout arm -- ONE TIME ONLY, see the prereg")
    a = ap.parse_args()
    panel = pickle.load(open(PANEL, "rb"))
    df = build(panel)
    print(f"events kept after de-overlap: {len(df)}  "
          f"(discovery {(df['arm'] == 'discovery').sum()} / holdout {(df['arm'] == 'holdout').sum()})")
    disc = df[df["arm"] == "discovery"]
    report(disc, "DISCOVERY")
    bad_bars(disc)
    placebo(disc)
    if a.holdout:
        hold = df[df["arm"] == "holdout"]
        report(hold, "HOLDOUT  (burned)")
        bad_bars(hold)
        placebo(hold)
    else:
        print("\nholdout NOT run. Re-run with --holdout once the discovery read is final.")


if __name__ == "__main__":
    main()
