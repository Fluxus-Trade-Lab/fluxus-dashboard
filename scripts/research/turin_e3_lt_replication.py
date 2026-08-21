"""E3 -- strategy-level replication of turin_LT (his weekly long-only SPY strat).

His spec (2026-08-20 tweet + TV release notes): SPY weekly, long-only,
conditions = "% > MA / Adv/decl / 252d rvol"; claim = "Outperforms spx b&h
w a min 14.58% dd since 07', live since 22'".

Pre-registered protocol (plan 3.2 E3):
    - dev window: data start -> 2021-12-31 (grid search allowed)
    - forward window: 2022-01-01 -> today (matches his "live since 22'";
      evaluated ONCE, only for dev survivors)
    - dev PASS bar: maxDD < 0.5 x B&H maxDD  AND  CAGR >= B&H CAGR - 1pp
    - NULL verdict: no combo clears the dev bar -> "claim not reproducible"

Grid (3 x 3 x 3 x 2 = 54 combos, all declared here, nothing added after
seeing results):
    A  breadth-MA:   MMTH (% of US stocks > 200dma, TV) > {40, 50, 60}
    B  adv/decl:     combined NYSE+Nasdaq cum AD line:
                     {> 100d SMA, > 200d SMA, R2-style (>100d SMA or 252d z > -1)}
    C  vol:          21d realized vol percentile rank within trailing 756d
                     <= {45, 60, 75}   (45 = his TV default thresh)
    combine:         {AND, 2-of-3}

Execution: signals on weekly (W-FRI) close, position applied the FOLLOWING
week (no lookahead). Long = SPY total return (adj close); cash earns 0.
Window truly starts once all conditions have data (~2008-10, AD warmup) --
we can NOT fully match "since 07"; stated in output.

Usage:  python3 scripts/research/turin_e3_lt_replication.py
Output: data/research/turin_e3_results.json + printed summary
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TVDIR = ROOT / "data/reference/breadth_tv"
CACHE = ROOT / ".cache/risk/e3_spy.pkl"
OUT = ROOT / "data/research/turin_e3_results.json"

DEV_END = "2021-12-31"
CLAIMED_MAXDD = -0.1458


def tv_series(name: str) -> pd.Series:
    s = pd.read_csv(TVDIR / f"{name}.csv", parse_dates=["date"]).set_index("date")["close"]
    return s[~s.index.duplicated(keep="last")]


def load_px(ticker: str, cache: Path) -> pd.Series:
    if cache.exists():
        return pd.read_pickle(cache)
    import yfinance as yf
    h = yf.Ticker(ticker).history(period="max", interval="1d", auto_adjust=True)["Close"]
    h.index = h.index.tz_localize(None).normalize()
    cache.parent.mkdir(parents=True, exist_ok=True)
    h.to_pickle(cache)
    return h


def load_spy() -> pd.Series:
    return load_px("SPY", CACHE)


def perf(weekly_ret: pd.Series) -> dict:
    eq = (1 + weekly_ret).cumprod()
    yrs = len(weekly_ret) / 52.0
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1) if yrs > 0 else np.nan
    dd = float((eq / eq.cummax() - 1).min())
    return {"cagr": round(cagr, 4), "maxdd": round(dd, 4),
            "final_multiple": round(float(eq.iloc[-1]), 3)}


def main() -> None:
    spy = load_spy()
    wk = spy.resample("W-FRI").last().dropna()
    wret = wk.pct_change()

    # --- daily condition inputs -> weekly booleans -----------------------
    mmth = tv_series("INDEX_MMTH")
    net = ((tv_series("INDEX_ADVN") + tv_series("INDEX_ADVQ"))
           - (tv_series("INDEX_DECN") + tv_series("INDEX_DECQ"))).dropna()
    adl = net.cumsum()
    adl_s100 = adl.rolling(100).mean()
    adl_s200 = adl.rolling(200).mean()
    adl_z252 = (adl - adl.rolling(252).mean()) / adl.rolling(252).std()
    rv21 = np.log(spy).diff().rolling(21).std() * np.sqrt(252)
    rv_rank = rv21.rolling(756).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)

    def weekly(s: pd.Series) -> pd.Series:
        return s.resample("W-FRI").last()

    A = {f"mmth>{t}": weekly(mmth) > t for t in (40, 50, 60)}
    B = {"adl>100d": weekly(adl) > weekly(adl_s100),
         "adl>200d": weekly(adl) > weekly(adl_s200),
         "R2style": (weekly(adl) > weekly(adl_s100)) | (weekly(adl_z252) > -1)}
    C = {f"rvrank<={t}": weekly(rv_rank) <= t / 100 for t in (45, 60, 75)}

    combos = []
    for (an, a), (bn, b), (cn, c), mode in itertools.product(
            A.items(), B.items(), C.items(), ("AND", "2of3")):
        sig = (a & b & c) if mode == "AND" else ((a.astype(int) + b.astype(int) + c.astype(int)) >= 2)
        combos.append((f"{an} & {bn} & {cn} [{mode}]", sig))

    # common evaluation window: all inputs present
    valid = weekly(mmth).notna() & weekly(adl_z252).notna() & weekly(rv_rank).notna() & wret.notna()
    start = valid[valid].index[0]
    dev_idx = wret.index[(wret.index >= start) & (wret.index <= DEV_END)]
    fwd_idx = wret.index[wret.index > DEV_END]

    bh_dev, bh_fwd = perf(wret.loc[dev_idx]), perf(wret.loc[fwd_idx])
    bh_full = perf(wret.loc[dev_idx.union(fwd_idx)])
    dd_bar, cagr_bar = 0.5 * bh_dev["maxdd"], bh_dev["cagr"] - 0.01

    # PASS 2 instrument: his pinned thread says "long only LETF port" -- the
    # chart is SPY weekly but the traded leg is plausibly the 3x ETF. Real
    # SPXL data (inception 2008-11) avoids synthetic-leverage approximation.
    spxl = load_px("SPXL", ROOT / ".cache/risk/e3_spxl.pkl")
    lret = spxl.resample("W-FRI").last().dropna().pct_change().reindex(wret.index)

    def run_grid(ret: pd.Series, tag: str):
        rows, survivors = [], []
        for name, sig in combos:
            pos = sig.shift(1).reindex(ret.index).fillna(False)  # next-week execution
            strat = ret.where(pos, 0.0).fillna(0.0)
            pdev = perf(strat.loc[dev_idx])
            tim = round(float(pos.loc[dev_idx].mean()), 3)
            ok = (pdev["maxdd"] > dd_bar) and (pdev["cagr"] >= cagr_bar)
            row = {"combo": name, "instrument": tag, "dev": pdev,
                   "time_in_mkt_dev": tim, "dev_pass": bool(ok)}
            if ok:
                row["forward"] = perf(strat.loc[fwd_idx])
                row["full"] = perf(strat.loc[dev_idx.union(fwd_idx)])
                row["time_in_mkt_fwd"] = round(float(pos.loc[fwd_idx].mean()), 3)
                survivors.append(row)
            rows.append(row)
        return rows, survivors

    rows, survivors = run_grid(wret, "SPY")
    rows2, survivors2 = run_grid(lret, "SPXL")

    verdict = ("REPRODUCIBLE" if (survivors or survivors2)
               else "NULL (claim not reproducible in this grid)")
    out = {
        "protocol": {"window_start_actual": str(start.date()),
                     "dev_end": DEV_END, "note_since07": "cannot match 'since 07' -- AD data starts 2007-09 + warmup",
                     "dev_bar": {"maxdd_better_than": round(dd_bar, 4), "cagr_at_least": round(cagr_bar, 4)},
                     "claimed_maxdd_since07": CLAIMED_MAXDD, "grid_size": len(combos)},
        "buy_and_hold": {"dev": bh_dev, "forward": bh_fwd, "full": bh_full},
        "pass1_spy": {"n_dev_pass": len(survivors), "survivors": survivors, "all_combos": rows},
        "pass2_spxl": {"note": "pinned thread says 'long only LETF port'; real SPXL fund data",
                       "n_dev_pass": len(survivors2), "survivors": survivors2, "all_combos": rows2},
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(out, indent=2))

    print(f"window {start.date()} -> {wret.index[-1].date()}   dev-end {DEV_END}   grid {len(combos)}")
    print(f"B&H dev:  cagr {bh_dev['cagr']:+.2%}  maxdd {bh_dev['maxdd']:.2%}   | forward: cagr {bh_fwd['cagr']:+.2%}  maxdd {bh_fwd['maxdd']:.2%}")
    print(f"dev bar:  maxdd > {dd_bar:.2%}  AND  cagr >= {cagr_bar:.2%}")
    for tag, rws, survs in (("SPY", rows, survivors), ("SPXL", rows2, survivors2)):
        print(f"\n[{tag}] {len(survs)}/{len(combos)} combos clear the dev bar")
        for s in sorted(survs, key=lambda r: r["dev"]["maxdd"], reverse=True)[:8]:
            print(f"  {s['combo']:44s} dev cagr {s['dev']['cagr']:+.2%} dd {s['dev']['maxdd']:.2%} tim {s['time_in_mkt_dev']:.0%}"
                  f"  | fwd cagr {s['forward']['cagr']:+.2%} dd {s['forward']['maxdd']:.2%}"
                  f"  | full dd {s['full']['maxdd']:.2%}")
        if not survs:
            for s in sorted(rws, key=lambda r: -r["dev"]["maxdd"])[:3]:
                print(f"  closest: {s['combo']:40s} dev cagr {s['dev']['cagr']:+.2%} dd {s['dev']['maxdd']:.2%} tim {s['time_in_mkt_dev']:.0%}")
    print(f"\nverdict: {verdict}")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
