#!/usr/bin/env python3
"""SMH vs SOXX: internal breadth of each ETF's own holdings (T-1004-10).

Same rulers as T-1002-80 (`data/research/semi_breadth_2026-10-02/build_series.py`),
which restates them from ``pipeline/screeners/breadth_metrics.py``. Only the pool
changes: instead of the union of three taxonomy theme groups, each series is built
from one ETF's published holdings file.

Two arms per ETF:
  * equal-weight  -- "how many of the names are above the line", i.e. the
    breadth of the basket, which is what the publicly reported breadth numbers
    measure for the whole market;
  * weight-weighted -- the same question answered with each name counted at its
    index weight, which is what the ETF's own price actually tracks.

The gap between the two arms is the point of the exercise.

Usage:
    python3 data/research/semi_etf_breadth_2026-10-04/build_series.py [--outdir DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))

# ── Rulers, restated from pipeline/screeners/breadth_metrics.py ───────────
NEW_HIGH_THRESHOLD = -0.001      # breadth_metrics.py:33
NEW_LOW_THRESHOLD = 0.001        # breadth_metrics.py:34
EXCLUDED_INDUSTRIES = frozenset({'Shell Companies'})   # breadth_metrics.py:51
MIN_BARS_52W = 200               # breadth_metrics.py:59
MIN_BARS_4W = 20                 # breadth_metrics.py:60
WIN_52W, WIN_4W = 252, 20

WINDOW_START = "2026-08-03"
# 252-bar lookback + 200d SMA warmup must both be satisfied at WINDOW_START.
DOWNLOAD_START = "2024-09-01"
ETFS = ("SMH", "SOXX")

HOLDINGS = {
    "SMH": HERE / "holdings_smh_2026-10-01.csv",
    "SOXX": HERE / "holdings_soxx_2026-10-01.csv",
}


def load_holdings() -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    """ticker -> index weight (%) per ETF, from the issuer files in this dir.

    Only the iShares file carries a `Location` column. The 23 names the two
    funds share are the same securities (same ADR line), so SOXX's Location
    column is what labels domicile for both -- stated here rather than in the
    write-up because it is an inference, not a field VanEck publishes.
    """
    out, loc = {}, {}
    for etf, path in HOLDINGS.items():
        with path.open() as f:
            rows = list(csv.DictReader(f))
        out[etf] = {r["ticker"]: float(r["weight_pct"]) for r in rows}
        for r in rows:
            if r.get("location"):
                loc[r["ticker"]] = r["location"]
        if not 95.0 < sum(out[etf].values()) < 101.0:
            raise SystemExit(f"{etf}: equity weights sum to "
                             f"{sum(out[etf].values()):.2f}, expected ~100")
    return out, loc


def load_industries(pool: list[str]) -> dict[str, str | None]:
    """Finviz industry per name, for the common-stock type gate."""
    u = json.loads((REPO / "data/output/universe.json").read_text())
    rows = {r["ticker"]: r for r in u["rows"]}
    absent = [t for t in pool if t not in rows]
    if absent:
        print(f"  warn: not in published universe, type gate unknown: {absent}")
    return {t: rows.get(t, {}).get("industry") for t in pool}


def download(tickers: list[str], end: str) -> dict[str, pd.DataFrame]:
    import yfinance as yf
    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(tickers), 20):
        chunk = tickers[i:i + 20]
        df = yf.download(chunk, start=DOWNLOAD_START, end=end, auto_adjust=True,
                         progress=False, group_by="ticker", threads=True, actions=False)
        for t in chunk:
            try:
                sub = df[t].dropna(how="all")
            except KeyError:
                print(f"  warn: no bars for {t}")
                continue
            if len(sub):
                out[t] = sub[["High", "Low", "Close"]].copy()
        time.sleep(1)
    return out


def panels(bars: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Per-name daily panel. min_periods is the bar floor, not the window
    length -- see the long comment in the T-1002-80 script: leaving it at the
    pandas default silently imposes a 252-bar floor instead of 200."""
    out = {}
    for t, h in bars.items():
        c = h["Close"]
        out[t] = pd.DataFrame({
            "close": c,
            "sma50": c.rolling(50).mean(),
            "sma200": c.rolling(200).mean(),
            "max_h_252": h["High"].rolling(WIN_52W, min_periods=MIN_BARS_52W).max(),
            "min_l_252": h["Low"].rolling(WIN_52W, min_periods=MIN_BARS_52W).min(),
            "max_h_20": h["High"].rolling(WIN_4W, min_periods=MIN_BARS_4W).max(),
            "min_l_20": h["Low"].rolling(WIN_4W, min_periods=MIN_BARS_4W).min(),
            "bars_n": np.arange(1, len(c) + 1),
        })
    return out


def verify_control(panel: dict, asof: str) -> None:
    """Positive control: reproduce the published per-name readings on `asof`.

    Finviz's 52-week range is built on INTRADAY highs/lows, not closes. The
    close-based variant is the negative arm -- if it ever stops being visibly
    worse, this control has stopped discriminating and the series is unverified.
    """
    u = json.loads((REPO / "data/output/universe.json").read_text())
    rows = {r["ticker"]: r for r in u["rows"]}
    D = pd.Timestamp(asof)
    sma_sign_dis = hi_flag_dis = 0
    d_hi_high, d_hi_close, d_sma = [], [], []
    mine_above = pub_above = 0
    for t, p in panel.items():
        if D not in p.index or t not in rows:
            continue
        r, pub = p.loc[D], rows[t]
        if pd.notna(r["sma50"]) and pub.get("sma50_dist") is not None:
            mine = r["close"] / r["sma50"] - 1
            d_sma.append(abs(mine - pub["sma50_dist"]))
            mine_above += mine > 0
            pub_above += pub["sma50_dist"] > 0
            sma_sign_dis += (mine > 0) != (pub["sma50_dist"] > 0)
        if pd.notna(r["max_h_252"]) and pub.get("high_52w") is not None:
            mine_h = r["close"] / r["max_h_252"] - 1
            d_hi_high.append(abs(mine_h - pub["high_52w"]))
            d_hi_close.append(abs(r["close"] / p.loc[:D, "close"].tail(WIN_52W).max() - 1
                                  - pub["high_52w"]))
            hi_flag_dis += ((mine_h >= NEW_HIGH_THRESHOLD)
                            != (pub["high_52w"] >= NEW_HIGH_THRESHOLD))

    med_high, med_close = float(np.median(d_hi_high)), float(np.median(d_hi_close))
    print(f"  control on {asof}: n={len(d_sma)}")
    print(f"    sma50 dist   median |diff| {np.median(d_sma):.5f}  max {max(d_sma):.4f}")
    print(f"    sma50 sign disagreements   {sma_sign_dis} / {len(d_sma)}")
    print(f"    above-50sma count  mine {mine_above}  published {pub_above}")
    print(f"    52w high (intraday arm)  median |diff| {med_high:.5f}  max {max(d_hi_high):.4f}")
    print(f"    52w high (close arm)     median |diff| {med_close:.5f}   <- negative arm")
    print(f"    new-high flag disagreements {hi_flag_dis} / {len(d_hi_high)}")
    assert sma_sign_dis == 0, f"50dma sign disagrees on {sma_sign_dis} names"
    assert hi_flag_dis == 0, f"52w-high flag disagrees on {hi_flag_dis} names"
    assert mine_above == pub_above, f"above-50sma count {mine_above} != {pub_above}"
    # The negative arm must stay visibly worse, or the control proves nothing.
    assert med_close > 5 * max(med_high, 1e-6), (
        f"close-based 52w arm ({med_close:.5f}) is no longer clearly worse than "
        f"the intraday arm ({med_high:.5f}); this control no longer discriminates")


def pct(numer: float, denom: float) -> float | None:
    """Null, not zero, on an empty denominator: a day with nothing to measure
    is not a day with nothing above the line."""
    return round(100.0 * numer / denom, 2) if denom else None


def count_day(panel: dict, weights: dict[str, float], industries: dict,
              D: pd.Timestamp) -> dict:
    """One session, one ETF: both breadth arms plus the gated extreme counts.

    The equal-weight arm counts names; the weighted arm counts index weight.
    Both renormalize over the names that actually have the reading that day,
    so the two arms share a denominator population and the gap between them
    is entirely about concentration, not about coverage.
    """
    above50, above200 = [], []
    present = 0
    nh = nl = nh4 = nl4 = 0
    n_gate52 = n_gate4 = 0
    hi_dist = []
    for t in sorted(weights):
        p = panel.get(t)
        if p is None or D not in p.index:
            continue
        r = p.loc[D]
        if pd.isna(r["close"]):
            continue
        present += 1
        if pd.notna(r["sma50"]):
            above50.append((t, bool(r["close"] > r["sma50"])))
        if pd.notna(r["sma200"]):
            above200.append((t, bool(r["close"] > r["sma200"])))
        # common-stock gate, breadth_metrics.py:51 / 59-60
        typed = industries.get(t) not in EXCLUDED_INDUSTRIES
        if typed and r["bars_n"] >= MIN_BARS_52W and pd.notna(r["max_h_252"]):
            n_gate52 += 1
            d_hi = r["close"] / r["max_h_252"] - 1
            hi_dist.append(d_hi)
            nh += d_hi >= NEW_HIGH_THRESHOLD
            nl += r["close"] / r["min_l_252"] - 1 <= NEW_LOW_THRESHOLD
        if typed and r["bars_n"] >= MIN_BARS_4W and pd.notna(r["max_h_20"]):
            n_gate4 += 1
            nh4 += r["close"] / r["max_h_20"] - 1 >= NEW_HIGH_THRESHOLD
            nl4 += r["close"] / r["min_l_20"] - 1 <= NEW_LOW_THRESHOLD

    def eq(flags):
        return pct(sum(v for _, v in flags), len(flags))

    def wt(flags):
        return pct(sum(weights[t] for t, v in flags if v),
                   sum(weights[t] for t, _ in flags))

    return {
        "n_present": present,
        "n_with_sma50": len(above50),
        "eq_pct_above_50sma": eq(above50),
        "wt_pct_above_50sma": wt(above50),
        "eq_pct_above_200sma": eq(above200),
        "wt_pct_above_200sma": wt(above200),
        "n_gate_52w": n_gate52,
        "new_highs_52w": int(nh),
        "new_lows_52w": int(nl),
        "n_gate_4w": n_gate4,
        "new_highs_4w": int(nh4),
        "new_lows_4w": int(nl4),
        "median_dist_52w_high": round(float(np.median(hi_dist)), 4) if hi_dist else None,
    }


def series(panel: dict, weights: dict[str, float], industries: dict,
           dates: pd.DatetimeIndex, etf_panel: pd.DataFrame) -> list[dict]:
    """One ETF's daily internal-breadth row set."""
    etf_close = etf_panel["close"]
    base = etf_close.loc[etf_close.index >= dates[0]].iloc[0]
    rows = []
    for D in dates:
        row = {"date": D.date().isoformat()}
        row.update(count_day(panel, weights, industries, D))
        row["etf_close_ret_from_start"] = round(100.0 * (etf_close.loc[D] / base - 1), 2)
        row["etf_dist_52w_high"] = round(
            float(etf_close.loc[D] / etf_panel["max_h_252"].loc[D] - 1), 4)
        rows.append(row)
    return rows


def summarize(rows: dict[str, list[dict]], weights: dict[str, dict[str, float]],
              holdings_loc: dict[str, str], asof: str) -> dict:
    """Every number the README quotes, computed here so it can be re-derived."""
    import statistics as st
    out: dict = {"etfs": {}}
    smh_t, soxx_t = set(weights["SMH"]), set(weights["SOXX"])
    non_us = {t for t, loc in holdings_loc.items() if loc != "United States"}
    out["overlap"] = {
        "n": len(smh_t & soxx_t),
        "tickers": sorted(smh_t & soxx_t),
        "smh_only": sorted(smh_t - soxx_t),
        "soxx_only": sorted(soxx_t - smh_t),
        "share_of_smh_weight": round(sum(weights["SMH"][t] for t in smh_t & soxx_t), 2),
        "share_of_soxx_weight": round(sum(weights["SOXX"][t] for t in smh_t & soxx_t), 2),
    }
    for etf in ETFS:
        r = rows[etf]
        held = set(weights[etf])
        gaps = [x["wt_pct_above_50sma"] - x["eq_pct_above_50sma"] for x in r]
        foreign = sorted(held & non_us)
        out["etfs"][etf] = {
            "n_equity_holdings": len(held),
            "max_weight_pct": round(max(weights[etf].values()), 2),
            "top5_weight_pct": round(sum(sorted(weights[etf].values(), reverse=True)[:5]), 2),
            "top5_names": [t for t, _ in sorted(weights[etf].items(), key=lambda x: -x[1])[:5]],
            "non_us_names": foreign,
            "non_us_weight_pct": round(sum(weights[etf][t] for t in foreign), 2),
            "eq_50sma_first": r[0]["eq_pct_above_50sma"],
            "eq_50sma_last": r[-1]["eq_pct_above_50sma"],
            "wt_50sma_first": r[0]["wt_pct_above_50sma"],
            "wt_50sma_last": r[-1]["wt_pct_above_50sma"],
            "eq_200sma_first": r[0]["eq_pct_above_200sma"],
            "eq_200sma_last": r[-1]["eq_pct_above_200sma"],
            "wt_minus_eq_mean": round(st.mean(gaps), 2),
            "wt_minus_eq_max": round(max(gaps), 2),
            "wt_minus_eq_max_date": r[gaps.index(max(gaps))]["date"],
            "wt_minus_eq_min": round(min(gaps), 2),
            "wt_minus_eq_min_date": r[gaps.index(min(gaps))]["date"],
            "days_wt_above_eq": sum(g > 0 for g in gaps),
            "sessions": len(r),
            "new_highs_52w_total": sum(x["new_highs_52w"] for x in r),
            "new_lows_52w_total": sum(x["new_lows_52w"] for x in r),
            "new_highs_4w_total": sum(x["new_highs_4w"] for x in r),
            "new_highs_4w_best_day": max(x["new_highs_4w"] for x in r),
            "new_lows_4w_total": sum(x["new_lows_4w"] for x in r),
            "median_dist_52w_high_last": r[-1]["median_dist_52w_high"],
            "etf_ret_window_pct": r[-1]["etf_close_ret_from_start"],
            "etf_dist_52w_high_first": r[0]["etf_dist_52w_high"],
            "etf_dist_52w_high_last": r[-1]["etf_dist_52w_high"],
        }
        on_0922 = [x for x in r if x["date"] == "2026-09-22"]
        if on_0922:
            out["etfs"][etf]["etf_dist_52w_high_2026_09_22"] = on_0922[0]["etf_dist_52w_high"]
            out["etfs"][etf]["eq_50sma_2026_09_22"] = on_0922[0]["eq_pct_above_50sma"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(HERE))
    args = ap.parse_args()
    outdir = Path(args.outdir)

    from pipeline.marketcal import last_completed_session
    asof = last_completed_session().isoformat()
    print(f"window {WINDOW_START} -> {asof}")

    weights, holdings_loc = load_holdings()
    pool = sorted(set().union(*(w.keys() for w in weights.values())))
    print(f"pool: {len(pool)} names "
          f"(SMH {len(weights['SMH'])}, SOXX {len(weights['SOXX'])}, "
          f"overlap {len(set(weights['SMH']) & set(weights['SOXX']))})")

    industries = load_industries(pool)
    end = (pd.Timestamp(asof) + pd.Timedelta(days=1)).date().isoformat()
    bars = download(pool + list(ETFS), end)
    missing = [t for t in pool + list(ETFS) if t not in bars]
    if missing:
        raise SystemExit(f"no bars for {missing}; cannot build the series")
    panel = panels(bars)

    verify_control({t: p for t, p in panel.items() if t in pool}, asof)

    dates = panel[ETFS[0]].loc[WINDOW_START:asof].index
    print(f"  {len(dates)} sessions")

    out = {etf: series(panel, weights[etf], industries, dates,
                       panel[etf]) for etf in ETFS}

    # Name-level diagnostics: which holdings the gates drop, and when.
    print("  gate diagnostics on", asof)
    for etf in ETFS:
        held = [t for t in weights[etf] if t in panel]
        no50 = [t for t in held if pd.isna(panel[t]["sma50"].loc[dates[0]])]
        no52 = [t for t in held if panel[t]["bars_n"].loc[asof] < MIN_BARS_52W]
        shell = [t for t in held if industries.get(t) in EXCLUDED_INDUSTRIES]
        print(f"    {etf}: no 50d SMA at window start {no50} | "
              f"<{MIN_BARS_52W} bars (out of the 52w counts) {no52} | "
              f"excluded industry {shell}")

    cols = ["date"]
    for etf in ETFS:
        cols += [f"{etf.lower()}_{k}" for k in out[etf][0] if k != "date"]
    path = outdir / "semi_etf_breadth_series.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, D in enumerate(dates):
            row = {"date": D.date().isoformat()}
            for etf in ETFS:
                for k, v in out[etf][i].items():
                    if k != "date":
                        row[f"{etf.lower()}_{k}"] = v
            w.writerow(row)
    print(f"wrote {path} ({len(dates)} rows)")

    # ETF-level facts the write-up quotes.
    facts = {"window": [dates[0].date().isoformat(), asof],
             "holdings_as_of": "2026-10-01", "etfs": {}}
    for etf in ETFS:
        p = panel[etf]
        c0, c1 = p["close"].loc[dates[0]], p["close"].loc[asof]
        highs = bars[etf]["High"].loc[:asof].tail(WIN_52W)
        facts["etfs"][etf] = {
            "ret_window_pct": round(100.0 * (c1 / c0 - 1), 2),
            "dist_52w_high_pct": round(100.0 * (c1 / p["max_h_252"].loc[asof] - 1), 2),
            "date_of_52w_high": highs.idxmax().date().isoformat(),
            "n_equity_holdings": len(weights[etf]),
            "max_weight_pct": round(max(weights[etf].values()), 2),
            "top5_weight_pct": round(sum(sorted(weights[etf].values(), reverse=True)[:5]), 2),
        }
    facts["summary"] = summarize(out, weights, holdings_loc, asof)
    (outdir / "etf_facts.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(json.dumps(facts, indent=2))


if __name__ == "__main__":
    main()
