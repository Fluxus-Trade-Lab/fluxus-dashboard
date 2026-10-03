"""T-1002-03: does rs_rating / rs_1m·3m·6m / RS line pick out the names that
go on to beat SPY, and by how much does each differ from the others?

Reconstructs each metric from price history alone (today's universe.json only
has today's row, so every window is rebuilt from closes), then at each
non-overlapping rebalance date takes the top-quintile names under each metric
and measures forward 20- and 63-session excess return vs SPY plus hit rate.

Universe: today's `tradeable` flag in data/output/universe.json (2,499 names
on 2026-09-30) projected backward over 5 years of price history. This is a
SURVIVORSHIP-BIASED sample: anything that delisted, got acquired, or dropped
out of the tradeable set between the backtest window and today is invisible
here, and such names skew toward losers -- any edge measured below is an
upper bound, not a replicated finding.

    python3 data/research/rs_unify/rs_compare.py --fetch   # download once (~2-3 min)
    python3 data/research/rs_unify/rs_compare.py            # run the study
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

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

logger = logging.getLogger(__name__)

CACHE = Path(".cache/rs_unify_panel.pkl")
META = Path("data/research/rs_unify/panel_meta.json")
UNIVERSE = Path("data/output/universe.json")
BENCH = "SPY"
PERIOD = "5y"

M1, M3, M6, M9, M12 = 21, 63, 126, 189, 252
HORIZONS = (20, 63)
REBAL = 21
QUINTILE = 0.20


def eligible_tickers() -> List[str]:
    rows = json.loads(UNIVERSE.read_text())["rows"]
    out = sorted({str(r["ticker"]) for r in rows if r.get("tradeable") and r.get("ticker")})
    logger.info("%d tradeable tickers in universe.json", len(out))
    return out


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
    panel = panel.dropna(axis=1, thresh=M12 + REBAL).ffill()
    logger.info("panel %d sessions x %d tickers (dropped %d with < %d sessions)",
                panel.shape[0], panel.shape[1], before - panel.shape[1], M12 + REBAL)
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
        "date_range": [str(panel.index[0].date()), str(panel.index[-1].date())],
        "note": "tickers dropped here are names with < 273 sessions of yfinance "
                "history inside the 5y window (recent IPOs/relistings) -- this "
                "trims the sample further, on top of the survivorship bias from "
                "using today's tradeable set.",
    }, indent=2))
    return panel


def _ret(close: pd.DataFrame, back: int) -> pd.DataFrame:
    return close / close.shift(back) - 1.0


def build_features(close: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    bench = close[BENCH]
    p1m, p3m, p6m, p12m = _ret(close, M1), _ret(close, M3), _ret(close, M6), _ret(close, M12)
    rankpct = lambda df: df.rank(axis=1, pct=True) * 99  # noqa: E731

    rs_1m = rankpct(p1m)
    rs_3m = rankpct(p3m)
    rs_6m = rankpct(p6m)

    # rs_rating reconstruction: run_all.py:565-567 -- 0.4*q1(3m) + 0.2*q2(6m)
    # + 0.2*q3(interpolated 6m/1y at 9m) + 0.2*q4(1y), then ranked.  _quarter_
    # excess in the real pipeline returns RAW perf (not SPY-subtracted) because
    # ranking is invariant to a constant offset across the cross-section --
    # replicated the same way here, so q9m interpolates p6m/p12m at the
    # midpoint exactly like production.
    q9m = p6m + (p12m - p6m) * 0.5
    rs_raw = 0.4 * p3m + 0.2 * p6m + 0.2 * q9m + 0.2 * p12m
    rs_rating = rankpct(rs_raw)

    # RS line self-percentile (oratnek RS 1M/3M): adapters/yfinance_adapter.py
    # rs_line_pctl -- today's close/bench ratio's percentile among its own
    # trailing n sessions. Computed per-ticker with a rolling window.
    ratio = close.div(bench, axis=0)

    def self_pctl(r: pd.DataFrame, n: int) -> pd.DataFrame:
        def _one(col: pd.Series) -> pd.Series:
            return col.rolling(n).apply(lambda w: (w <= w[-1]).mean() * 100.0, raw=True)
        return r.apply(_one, axis=0)

    rs_line_21 = self_pctl(ratio, 21)
    rs_line_63 = self_pctl(ratio, 63)

    # Academic cross-sectional benchmark: Jegadeesh-Titman 12-1 momentum
    # (12-month return skipping the most recent month, to dodge short-term
    # reversal) -- the standard momentum-factor construction, not ours.
    p12_1 = close.shift(M1) / close.shift(M12) - 1.0
    mom_12_1 = rankpct(p12_1)

    fwd = {}
    for h in HORIZONS:
        f = close.shift(-h) / close - 1.0
        fwd[h] = f.sub(f[BENCH], axis=0)

    return {
        "rs_1m": rs_1m, "rs_3m": rs_3m, "rs_6m": rs_6m, "rs_rating": rs_rating,
        "rs_line_21": rs_line_21, "rs_line_63": rs_line_63, "mom_12_1": mom_12_1,
        "fwd": fwd,
    }


ARMS = ["rs_rating", "rs_3m", "rs_6m", "rs_1m", "rs_line_21", "rs_line_63", "mom_12_1"]
ARM_LABEL = {
    "rs_rating": "rs_rating (IBD-recon 0.4/0.2/0.2/0.2)",
    "rs_3m": "rs_3m (single-window 3m, cross-sect.)",
    "rs_6m": "rs_6m (single-window 6m, cross-sect.)",
    "rs_1m": "rs_1m (single-window 1m, cross-sect.)",
    "rs_line_21": "RS line self-pctl, 21d (oratnek RS 1M)",
    "rs_line_63": "RS line self-pctl, 63d (oratnek RS 3M)",
    "mom_12_1": "academic 12-1 momentum (benchmark, not ours)",
}


def run_study(f: Dict[str, pd.DataFrame], warmup: int) -> Dict[int, List[Dict[str, object]]]:
    dates = f["rs_rating"].index[warmup::REBAL]
    results: Dict[int, List[Dict[str, object]]] = {h: [] for h in HORIZONS}

    for h in HORIZONS:
        fwd = f["fwd"][h]
        arms_vals: Dict[str, List[float]] = {a: [] for a in ARMS}
        sizes: Dict[str, List[int]] = {a: [] for a in ARMS}
        for dt in dates:
            if dt not in fwd.index:
                continue
            fr = fwd.loc[dt]
            for a in ARMS:
                sr = f[a].loc[dt].dropna().drop(labels=[BENCH], errors="ignore")
                if len(sr) < 50:
                    continue
                cut = sr.quantile(1 - QUINTILE)
                top = sr[sr >= cut].index
                vals = fr.reindex(top).dropna()
                if len(vals) >= 10:
                    arms_vals[a].append(float(vals.mean()))
                    sizes[a].append(len(vals))

        for a in ARMS:
            vals = np.array(arms_vals[a])
            if vals.size == 0:
                continue
            se = vals.std(ddof=1) / np.sqrt(vals.size) if vals.size > 1 else np.nan
            results[h].append({
                "arm": a, "label": ARM_LABEL[a], "n_periods": int(vals.size),
                "mean": float(vals.mean()), "median": float(np.median(vals)),
                "se": float(se) if se == se else None,
                "t": float(vals.mean() / se) if se and se > 0 else None,
                "hit": float((vals > 0).mean()),
                "avg_names": float(np.mean(sizes[a])),
            })
    return results


def pairwise_overlap(f: Dict[str, pd.DataFrame], asof_date) -> Dict[str, float]:
    """Top-quintile membership overlap on the most recent available date --
    cross-checks the already-published correlation numbers (claire 10-02:
    rs_rating-rs_6m 0.84, rs_rating-rs_3m 0.65, rs_3m-rs_6m 0.53) against an
    independently reconstructed panel."""
    out = {}
    pairs = [("rs_rating", "rs_6m"), ("rs_rating", "rs_3m"), ("rs_3m", "rs_6m"),
             ("rs_rating", "rs_line_21"), ("rs_line_21", "rs_line_63")]
    for a, b in pairs:
        sa = f[a].loc[asof_date].dropna().drop(labels=[BENCH], errors="ignore")
        sb = f[b].loc[asof_date].dropna().drop(labels=[BENCH], errors="ignore")
        common = sa.index.intersection(sb.index)
        if len(common) < 50:
            continue
        corr = sa.loc[common].corr(sb.loc[common], method="spearman")
        cut_a = sa.loc[common].quantile(0.80)
        cut_b = sb.loc[common].quantile(0.80)
        top_a = set(sa.loc[common][sa.loc[common] >= cut_a].index)
        top_b = set(sb.loc[common][sb.loc[common] >= cut_b].index)
        jacc = len(top_a & top_b) / len(top_a | top_b) if (top_a | top_b) else None
        out[f"{a}~{b}"] = {
            "spearman": round(float(corr), 3) if corr == corr else None,
            "top20pct_jaccard": round(jacc, 3) if jacc is not None else None,
            "n": len(common),
        }
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--out", default="data/research/rs_unify/backtest_results.json")
    args = ap.parse_args()

    close = load_panel(fetch_now=args.fetch)
    f = build_features(close)
    warmup = M12 + M1  # need 252d history for rs_rating/mom_12_1 plus 21d for rs_line warmup
    results = run_study(f, warmup)
    overlap = pairwise_overlap(f, close.index[-1])

    out = {
        "panel": {
            "sessions": int(close.shape[0]), "tickers": int(close.shape[1]) - 1,
            "date_range": [str(close.index[0].date()), str(close.index[-1].date())],
        },
        "survivorship_bias": "tickers = today's tradeable set (2026-09-30) "
            "projected backward; delisted/acquired/dropped names over the 5y "
            "window are absent and skew toward losers -- edges below are an "
            "upper bound.",
        "forward_horizons": {str(h): results[h] for h in HORIZONS},
        "asof_overlap_check": overlap,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))

    print(f"\nPanel {close.shape[0]} sessions x {close.shape[1]-1} tickers "
          f"({close.index[0].date()} -> {close.index[-1].date()})")
    for h in HORIZONS:
        print(f"\n=== forward {h}-session excess vs SPY, top-quintile by each metric ===")
        hdr = (f"{'arm':45s} {'per':>4s} {'names':>6s} {'mean%':>7s} "
               f"{'med%':>7s} {'t':>6s} {'hit%':>6s}")
        print(hdr); print("-" * len(hdr))
        for r in results[h]:
            t = r['t']
            print(f"{r['label']:45s} {r['n_periods']:4d} {r['avg_names']:6.0f} "
                  f"{100*r['mean']:+7.2f} {100*r['median']:+7.2f} "
                  f"{t if t is None else round(t,2):>6} {100*r['hit']:6.0f}")
    print("\nas-of overlap (most recent session):")
    for k, v in overlap.items():
        print(f"  {k}: spearman={v['spearman']} top20%-jaccard={v['top20pct_jaccard']} n={v['n']}")


if __name__ == "__main__":
    main()
