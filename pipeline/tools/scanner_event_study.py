"""Forward-return event study for the scanner presets.

For every (screener, date, ticker) hit, measure the close-to-close return
5/10/20 sessions later, the max favourable / adverse excursion inside 20
sessions, and compare against (a) a same-day random draw of equal size from
the pool of names with bars, repeated, and (b) SPY. Prints per-screener
aggregates and writes a per-hit table for the case studies.

    python -m pipeline.tools.scanner_event_study --events data/history/ticker_events.csv \
        --bars data/research/scanner_validation_2026-08/event_bars.pkl \
        --out data/research/scanner_validation_2026-08/study_old7.csv

Or with `--panels-dir` pointing at the as-of panel membership files
(panels_asof_<date>.json) for the newer watchlist panels.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HORIZONS = (5, 10, 20)


def load_events(path: Path):
    rows = list(csv.DictReader(path.open()))
    ev = defaultdict(list)
    for r in rows:
        ev[r["screener"]].append((r["date"], r["ticker"]))
    return ev


def load_panel_events(panels_dir: Path):
    ev = defaultdict(list)
    for f in sorted(panels_dir.glob("panels_asof_*.json")):
        d = f.stem.replace("panels_asof_", "")
        m = json.loads(f.read_text())
        for k, tks in m.items():
            for t in tks:
                ev[k].append((d, t))
    return ev


def fwd_stats(close: pd.Series, high: pd.Series, low: pd.Series, d0: pd.Timestamp):
    """Returns dict of fwd5/10/20, mfe20, mae20 relative to the close on d0."""
    if d0 not in close.index:
        # use the last bar on/before d0
        idx = close.index.searchsorted(d0, side="right") - 1
        if idx < 0:
            return None
    else:
        idx = close.index.get_loc(d0)
    c0 = float(close.iloc[idx])
    if not c0 or np.isnan(c0):
        return None
    out = {}
    for h in HORIZONS:
        j = idx + h
        out[f"fwd{h}"] = float(close.iloc[j] / c0 - 1.0) if j < len(close) else np.nan
    win = slice(idx + 1, min(idx + 21, len(close)))
    if win.stop > win.start:
        out["mfe20"] = float(high.iloc[win].max() / c0 - 1.0)
        out["mae20"] = float(low.iloc[win].min() / c0 - 1.0)
    else:
        out["mfe20"] = out["mae20"] = np.nan
    return out


def run(events, bars, out_csv: Path, n_boot: int = 200, seed: int = 7):
    rng = np.random.default_rng(seed)
    spy = bars.get("SPY")
    tickers_with_bars = [t for t in bars if t != "SPY"]
    rows = []
    summary = []
    for scr, hits in sorted(events.items()):
        vals = defaultdict(list)
        n_ok = 0
        for d, t in hits:
            b = bars.get(t)
            if b is None:
                continue
            d0 = pd.Timestamp(d)
            st = fwd_stats(b["Close"], b["High"], b["Low"], d0)
            if st is None:
                continue
            n_ok += 1
            for k, v in st.items():
                vals[k].append(v)
            sp = fwd_stats(spy["Close"], spy["High"], spy["Low"], d0) if spy is not None else None
            rows.append({"screener": scr, "date": d, "ticker": t, **st,
                         **({f"spy_{k}": v for k, v in sp.items()} if sp else {})})
        if n_ok == 0:
            continue
        # baseline: same dates, random tickers, same count per date
        by_date = defaultdict(int)
        for d, t in hits:
            by_date[d] += 1
        base = {h: [] for h in HORIZONS}
        for _ in range(max(1, n_boot // 10)):
            for d, n in by_date.items():
                d0 = pd.Timestamp(d)
                pick = rng.choice(tickers_with_bars, size=min(n, len(tickers_with_bars)), replace=False)
                for t in pick:
                    b = bars[t]
                    st = fwd_stats(b["Close"], b["High"], b["Low"], d0)
                    if st is None:
                        continue
                    for h in HORIZONS:
                        if not np.isnan(st[f"fwd{h}"]):
                            base[h].append(st[f"fwd{h}"])
        rec = {"screener": scr, "hits": len(hits), "measured": n_ok}
        for h in HORIZONS:
            a = np.array([v for v in vals[f"fwd{h}"] if not np.isnan(v)])
            bb = np.array(base[h])
            sp_a = np.array([r[f"spy_fwd{h}"] for r in rows if r["screener"] == scr and not np.isnan(r.get(f"spy_fwd{h}", np.nan))])
            rec[f"fwd{h}_med"] = float(np.median(a)) if len(a) else np.nan
            rec[f"fwd{h}_mean"] = float(a.mean()) if len(a) else np.nan
            rec[f"fwd{h}_win"] = float((a > 0).mean()) if len(a) else np.nan
            rec[f"base{h}_med"] = float(np.median(bb)) if len(bb) else np.nan
            rec[f"spy{h}_med"] = float(np.median(sp_a)) if len(sp_a) else np.nan
        mfe = np.array([v for v in vals["mfe20"] if not np.isnan(v)])
        mae = np.array([v for v in vals["mae20"] if not np.isnan(v)])
        rec["mfe20_med"] = float(np.median(mfe)) if len(mfe) else np.nan
        rec["mae20_med"] = float(np.median(mae)) if len(mae) else np.nan
        rec["mfe20_ge10"] = float((mfe >= 0.10).mean()) if len(mfe) else np.nan
        rec["mae20_le_m10"] = float((mae <= -0.10).mean()) if len(mae) else np.nan
        summary.append(rec)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    s = pd.DataFrame(summary)
    s.to_csv(out_csv.with_name(out_csv.stem + "_summary.csv"), index=False)
    return s


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--events")
    ap.add_argument("--panels-dir")
    ap.add_argument("--bars", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    bars = pickle.load(open(a.bars, "rb"))
    events = load_events(Path(a.events)) if a.events else load_panel_events(Path(a.panels_dir))
    s = run(events, bars, Path(a.out))
    pd.set_option("display.width", 220)
    cols = ["screener", "hits", "measured", "fwd5_med", "base5_med", "fwd10_med", "base10_med", "fwd20_med", "base20_med", "spy20_med", "fwd20_win", "mfe20_med", "mae20_med", "mfe20_ge10", "mae20_le_m10"]
    print(s[cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    sys.exit(main())
