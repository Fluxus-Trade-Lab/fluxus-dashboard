"""Do the two proposed 4% Bullish gates pay?

`data/research/scanner_validation_2026-08/summary.md` §三.2 proposes two gates
on the 4% Bullish panel and a "first wave" sub-cell:

    atr_from_sma50 <= 4   and   change_pct <= 8%     (>= 15% -> chase warning)

The panel's own recipe is unchanged; the question is only whether a hit that
clears both gates does better afterwards than one that does not. This splits
every archived `preset:4_bullish` hit into cohorts and runs each cohort
through the SAME forward-return machinery the parent study used
(`scanner_event_study.run`), including its same-day random-ticker baseline.

Two sources, deliberately:

* `change_pct` comes from the archive row -- the number the screen actually
  saw that evening, not a value re-derived here.
* `atr_from_sma50` is not in the archive (the column was added 2026-08-17 and
  every backfilled row has it empty), so it is computed as-of from bars with
  the one implementation the rest of the repo uses --
  `research.outcomes.atr` (Wilder) and
  `screeners.atr_enrichment.atr_multiple_from_levels`. No new spelling of a
  quantity that already has a name.

    python -m pipeline.tools.bullish4_gate_study \
        --events data/history/ticker_events.csv \
        --bars data/research/scanner_validation_2026-08/event_bars.pkl \
        --out data/research/scanner_validation_2026-08/study_b4_gates.csv
"""

from __future__ import annotations

import argparse
import csv
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.research.outcomes import atr as wilder_atr
from pipeline.screeners.atr_enrichment import atr_multiple_from_levels
from pipeline.tools.scanner_event_study import run

SCREENER = "preset:4_bullish"

# The two gate values under test, and the chase line, from summary.md §三.2.
ATR_GATE = 4.0
CHG_GATE = 0.08
CHASE = 0.15


def load_hits(path: Path, screener: str = SCREENER):
    """[(date, ticker, change_pct)] for one screener, deduped on (date, ticker)."""
    seen = set()
    out = []
    for r in csv.DictReader(path.open()):
        if r.get("screener") != screener:
            continue
        key = (r["date"], r["ticker"])
        if key in seen:
            continue
        seen.add(key)
        try:
            chg = float(r["change_pct"])
        except (TypeError, ValueError, KeyError):
            chg = float("nan")
        out.append((r["date"], r["ticker"], chg))
    return out


def asof_features(bars: pd.DataFrame, d0: pd.Timestamp,
                  spy_close: pd.Series | None = None) -> dict:
    """as-of readings on the last bar at or before d0.

    Returns atr_from_sma50 (the repo's signed ATR Matrix multiple),
    bar_change (close/prev close - 1, for cross-checking the archived value),
    high_20d (close is the highest close of the last 20 sessions) and
    rs_high_21 (the RS line close/SPY at a 21-session high -- the same
    definition as the universe's ``rs_line_pctl_21 == 100``).
    """
    close = bars["Close"]
    idx = close.index.searchsorted(d0, side="right") - 1
    if idx < 50:                      # need a full SMA50 window
        return {}
    c = float(close.iloc[idx])
    sma50 = float(close.iloc[idx - 49:idx + 1].mean())
    a = wilder_atr(bars.iloc[:idx + 1])
    a = float(a.iloc[-1]) if len(a) and np.isfinite(a.iloc[-1]) else float("nan")
    prev = float(close.iloc[idx - 1])
    win = close.iloc[max(0, idx - 19):idx + 1]
    out = {
        "atr_from_sma50": atr_multiple_from_levels(c, a, sma50),
        "bar_change": (c / prev - 1.0) if prev else float("nan"),
        "high_20d": bool(c >= win.max() - 1e-9),
        "rs_high_21": None,
    }
    if spy_close is not None:
        rs = (close.iloc[:idx + 1] / spy_close.reindex(close.index[:idx + 1]).ffill()).dropna()
        if len(rs) >= 21:
            out["rs_high_21"] = bool(rs.iloc[-1] >= rs.iloc[-21:].max() - 1e-12)
    return out


def cohorts(hits, bars) -> tuple[dict, list]:
    """hits -> {cohort_name: [(date, ticker)]} plus a per-hit detail table."""
    ev = defaultdict(list)
    detail = []
    spy = bars.get("SPY")
    spy_close = spy["Close"] if spy is not None else None
    for d, t, chg in hits:
        b = bars.get(t)
        if b is None:
            continue
        f = asof_features(b, pd.Timestamp(d), spy_close)
        if not f:
            continue
        ext = f["atr_from_sma50"]
        row = {"date": d, "ticker": t, "change_pct": chg, **f}
        detail.append(row)

        ev["all"].append((d, t))
        if np.isfinite(chg):
            if chg <= CHG_GATE:
                ev["chg_le8"].append((d, t))
            elif chg < CHASE:
                ev["chg_8_15"].append((d, t))
            else:
                ev["chg_ge15"].append((d, t))
        if ext is not None:
            ev["atr_le4" if ext <= ATR_GATE else "atr_gt4"].append((d, t))
        # the proposal, and everything it would drop
        if ext is not None and np.isfinite(chg):
            if ext <= ATR_GATE and chg <= CHG_GATE:
                ev["gated"].append((d, t))
                if f["high_20d"]:
                    ev["gated_20dhigh"].append((d, t))
                if f["rs_high_21"]:
                    ev["gated_rshigh"].append((d, t))
                # the proposed "first wave" cell: both overlays on the gate
                if f["high_20d"] and f["rs_high_21"]:
                    ev["gated_firstwave"].append((d, t))
            else:
                ev["dropped"].append((d, t))
    return ev, detail


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="data/history/ticker_events.csv")
    ap.add_argument("--bars", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--screener", default=SCREENER)
    a = ap.parse_args(argv)

    hits = load_hits(Path(a.events), a.screener)
    with open(a.bars, "rb") as fh:
        bars = pickle.load(fh)
    ev, detail = cohorts(hits, bars)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(detail).to_csv(out.with_name(out.stem + "_hits.csv"), index=False)

    dd = pd.DataFrame(detail)
    if len(dd):
        both = dd.dropna(subset=["change_pct", "bar_change"])
        if len(both):
            gap = (both["change_pct"] - both["bar_change"]).abs()
            print(f"archive change_pct vs bar-derived: n={len(both)} "
                  f"median |gap| {gap.median():.4f}, 95th {gap.quantile(0.95):.4f}")

    s = run(ev, bars, out)
    cols = ["screener", "hits", "measured", "fwd5_med", "base5_med", "fwd10_med",
            "base10_med", "fwd20_med", "base20_med", "fwd20_win", "mfe20_med",
            "mae20_med", "mae20_le_m10"]
    with pd.option_context("display.width", 200, "display.max_columns", 40):
        print(s[[c for c in cols if c in s.columns]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
