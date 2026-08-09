"""Stock-level backtest: does RS acceleration add anything to h_score?

The ETF study (``validate_accel.py``) established which *window scheme* is
stable.  It could not answer the question that matters here: the screener
already ranks names by ``h_score``, so does acceleration earn its place on
top of a score we already trust?

Every input is reconstructed from prices, not from stored snapshots, because
only today's universe row exists.  That is possible because each component is
a function of price history:

    perf_1m(t)  = close(t) / close(t-21) - 1
    rs_21d(t)   = cross-sectional percentile rank of perf_1m(t)
    i_score(t)  = industry mean of rs_63d(t)      (industry map is ~static)
    f_score      = 50 for every row -- the feed's fundamental columns are
                   entirely null, so it contributes nothing but a constant

Design follows the discipline the sequence-mining null result forced on us:
every arm draws from the **same pool on the same dates**, so a difference is
timing, not composition.

Result over 10 years / 112 periods: **null**. Acceleration on top of h_score
is a *negative* contribution (-0.18pp, consistent across half-samples), and
"Weakening" beat "Leading" by +0.37pp. RS-line arms were removed after both
tested negative. Nothing reached |t| > 2. See project memory.

    python -m pipeline.themes.backtest_accel --fetch    # download prices once
    python -m pipeline.themes.backtest_accel            # run the study
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

CACHE = Path(".cache/stock_panel.pkl")
PERIOD = "10y"   # 2y gave only 17 non-overlapping periods -- far too few
MIN_HISTORY = 378  # ~18 months; below this a correlation is not worth computing
META = Path(".cache/stock_panel_meta.json")
UNIVERSE = Path("data/output/universe.json")
BENCH = "SPY"

# Liquidity floor.  Microcaps dominate a 5,600-name universe by count and
# their prints are the ones that produce +31,192% artefacts.
MIN_CAP = 3e8
MIN_DOLLAR_VOL = 2e6

# Session offsets
M1, M3, M6 = 21, 63, 126
HORIZON = 21          # forward window
REBAL = 21            # non-overlapping cross-sections
TOP_N = 200           # how many names the screener would surface


def eligible_tickers() -> List[str]:
    rows = json.loads(UNIVERSE.read_text())["rows"]
    out = []
    for r in rows:
        cap = r.get("market_cap") or 0
        vol = (r.get("avg_volume") or 0) * (r.get("close") or 0)
        if cap >= MIN_CAP and vol >= MIN_DOLLAR_VOL and r.get("ticker"):
            out.append(str(r["ticker"]))
    logger.info("%d of %d names clear the liquidity floor", len(out), len(rows))
    return sorted(set(out))


def industry_map() -> Dict[str, str]:
    rows = json.loads(UNIVERSE.read_text())["rows"]
    return {str(r["ticker"]): r.get("industry") for r in rows if r.get("ticker")}


def fetch(tickers: List[str]) -> pd.DataFrame:
    import yfinance as yf
    frames = []
    batch = 400
    for i in range(0, len(tickers), batch):
        chunk = tickers[i:i + batch]
        logger.info("batch %d/%d (%d tickers)", i // batch + 1,
                    (len(tickers) - 1) // batch + 1, len(chunk))
        data = yf.download(chunk, period=PERIOD, interval="1d",
                           auto_adjust=True, progress=False, threads=True)
        close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
        frames.append(close)
    panel = pd.concat(frames, axis=1)
    panel = panel.loc[:, ~panel.columns.duplicated()]
    before = panel.shape[1]
    # Keep anything with MIN_HISTORY sessions rather than demanding 80% of the
    # full window. The strict filter silently deleted every company listed in
    # the last few years -- Crypto Equities lost CRWV, NBIS, CORZ, IREN and
    # BMNR, so the "theme" being validated was its oldest half wearing a 2026
    # name. Correlations are computed on overlapping days, so ragged starts
    # are fine as long as the overlap is long enough to mean anything.
    panel = panel.dropna(axis=1, thresh=MIN_HISTORY).ffill()
    logger.info("panel %d sessions x %d tickers (dropped %d with < %d sessions)",
                panel.shape[0], panel.shape[1], before - panel.shape[1],
                MIN_HISTORY)
    return panel


def load_panel(fetch_now: bool = False) -> pd.DataFrame:
    if CACHE.exists() and not fetch_now:
        return pd.read_pickle(CACHE)
    tickers = eligible_tickers()
    if BENCH not in tickers:
        tickers.append(BENCH)
    panel = fetch(tickers)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    panel.to_pickle(CACHE)
    META.write_text(json.dumps({
        "requested": len(tickers),
        "retained": int(panel.shape[1]),
        "coverage": round(panel.shape[1] / max(len(tickers), 1), 4),
        "sessions": int(panel.shape[0]),
        "note": "Names lost here are delisted/renamed and skew toward losers; "
                "coverage is reported so the bias is visible.",
    }, indent=2))
    return panel


def _ret(close: pd.DataFrame, back: int) -> pd.DataFrame:
    return close / close.shift(back) - 1.0


def build_features(close: pd.DataFrame, ind: Dict[str, str]) -> Dict[str, pd.DataFrame]:
    """Reconstruct the screener's scores plus acceleration, per session."""
    p1m, p3m, p6m = _ret(close, M1), _ret(close, M3), _ret(close, M6)

    rank = lambda df: df.rank(axis=1, pct=True) * 99  # noqa: E731
    rs21, rs63, rs126 = rank(p1m), rank(p3m), rank(p6m)

    # i_score: industry mean of rs_63d, then ranked. Median, not mean --
    # a single artefact print otherwise drags a whole industry's score.
    groups = pd.Series({t: ind.get(t) for t in close.columns}).dropna()
    ind_med = rs63[groups.index].T.groupby(groups).median().T
    i_raw = pd.DataFrame(
        {t: ind_med[groups[t]] for t in groups.index if groups[t] in ind_med.columns}
    )
    i_score = i_raw.rank(axis=1, pct=True) * 99

    # h_score with f_score held at its real value: a constant.
    h = (50 * 2 + i_score * 3 + rs21 * 1 + rs63 * 2 + rs126 * 2) / 10

    # Acceleration, V4 windows: last month's RS minus the two months before.
    bench = lambda df: df[BENCH]  # noqa: E731
    rs_near = p1m.sub(bench(p1m), axis=0)
    prior = (1 + p3m) / (1 + p1m) - 1
    bench_prior = (1 + p3m[BENCH]) / (1 + p1m[BENCH]) - 1
    rs_prior = prior.sub(bench_prior, axis=0)
    accel = rs_near - rs_prior
    level = p3m.sub(bench(p3m), axis=0)

    # Persistence: how many of five horizons the name is top-quartile on.
    pers = None
    windows = [5, M1, M3, M6, 252]
    counts = []
    for w in windows:
        r = _ret(close, w)
        q = r.rank(axis=1, pct=True)
        counts.append((q >= 0.75).astype(float))
    pers = sum(counts)

    fwd = close.shift(-HORIZON) / close - 1.0
    fwd = fwd.sub(fwd[BENCH], axis=0)

    return {"h": h, "accel": accel, "level": level, "fwd": fwd, "rs63": rs63,
            "pers": pers}


def run_study(f: Dict[str, pd.DataFrame]) -> List[Dict[str, object]]:
    """Pool-matched arms: same dates, same candidate pool, different filters."""
    h, accel, level, fwd = f["h"], f["accel"], f["level"], f["fwd"]
    dates = h.index[M6::REBAL]

    pers = f["pers"]
    arms: Dict[str, List[float]] = {
        "A  top-200 h_score (baseline)": [],
        "B  +accel > 0": [],
        "C  +state = Leading": [],
        "D  +accel <= 0 (Weakening)": [],
        "E  accel alone, no h_score": [],
        "H  +persistence >= 4 of 5": [],
        "I  +persistence >= 4 AND accel > 0": [],
    }
    sizes: Dict[str, List[int]] = {k: [] for k in arms}

    for dt in dates:
        if dt not in fwd.index:
            continue
        hr, ar, lr, fr = h.loc[dt], accel.loc[dt], level.loc[dt], fwd.loc[dt]
        pool = hr.dropna().drop(labels=[BENCH], errors="ignore")
        if len(pool) < TOP_N:
            continue
        top = pool.nlargest(TOP_N).index

        def collect(name: str, idx) -> None:
            vals = fr.reindex(idx).dropna()
            if len(vals) >= 10:
                arms[name].append(float(vals.mean()))
                sizes[name].append(len(vals))

        pr = pers.loc[dt]
        collect("A  top-200 h_score (baseline)", top)
        collect("B  +accel > 0", [t for t in top if ar.get(t, np.nan) > 0])
        collect("C  +state = Leading",
                [t for t in top if ar.get(t, np.nan) > 0 and lr.get(t, np.nan) > 0])
        collect("D  +accel <= 0 (Weakening)",
                [t for t in top if ar.get(t, np.nan) <= 0])
        collect("E  accel alone, no h_score", ar.dropna().nlargest(TOP_N).index)
        collect("H  +persistence >= 4 of 5", [t for t in top if pr.get(t, 0) >= 4])
        collect("I  +persistence >= 4 AND accel > 0",
                [t for t in top if pr.get(t, 0) >= 4 and ar.get(t, np.nan) > 0])

    rows = []
    for name, vals in arms.items():
        a = np.array(vals)
        if a.size == 0:
            continue
        se = a.std(ddof=1) / np.sqrt(a.size) if a.size > 1 else np.nan
        rows.append({
            "arm": name, "n_periods": a.size,
            "mean": a.mean(), "median": float(np.median(a)),
            "se": se, "t": a.mean() / se if se and se > 0 else np.nan,
            "hit": float((a > 0).mean()),
            "avg_names": float(np.mean(sizes[name])),
        })
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true")
    args = ap.parse_args()

    close = load_panel(fetch_now=args.fetch)
    ind = industry_map()
    f = build_features(close, ind)
    rows = run_study(f)

    print(f"\nPanel {close.shape[0]} sessions x {close.shape[1]} tickers "
          f"({close.index[0].date()} -> {close.index[-1].date()})")
    print(f"Non-overlapping cross-sections every {REBAL} sessions, "
          f"{HORIZON}-session forward excess vs {BENCH}\n")

    hdr = (f"{'arm':44s} {'per':>4s} {'names':>6s} {'mean%':>7s} "
           f"{'med%':>7s} {'t':>6s} {'hit%':>6s}")
    print(hdr); print("-" * len(hdr))
    for r in rows:
        print(f"{r['arm']:44s} {r['n_periods']:4d} {r['avg_names']:6.0f} "
              f"{100*r['mean']:+7.2f} {100*r['median']:+7.2f} "
              f"{r['t']:6.2f} {100*r['hit']:6.0f}")

    print("\nmean% = mean forward excess return vs SPY per rebalance")
    print("t     = mean / standard error across periods (|t| > 2 is the usual bar)")
    print("hit%  = share of periods with positive excess")
    print("\nArms draw from the same pool on the same dates, so B/C/D vs A is")
    print("a timing difference, not a composition difference.")


if __name__ == "__main__":
    main()
