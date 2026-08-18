"""Which signal (or combo) notices a theme leader's leg first?

For each theme, take the members with the best 2026 YTD return (the leaders),
compute every signal we own DAILY from bars with our own engines (VCS v2,
Structure Pivot, Morales pocket pivot, ATR Matrix, generic breakouts), find
every leg (a close from which the next 20 sessions gain >= LEG_PCT), and score
each signal by (a) how often it fired inside the [-5, +2] window around a leg
start, (b) how often it fired with no leg following (false alarms), (c) the
median 20-session return after its fires. Also reports data-quality flags per
ticker (short history, gaps, extreme bars, adjust suspicion).

    python -m pipeline.tools.leader_footprint --themes "Cloud Software,Cybersecurity,Memory & Storage,High Octane" \
        --bars data/research/scanner_validation_2026-08/event_bars.pkl --start 2026-01-02 --top 8 \
        --out data/research/scanner_validation_2026-08/leaders
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.screeners import structure_pivot as SP
from pipeline.screeners.vcs import vcs as vcs_engine

LEG_PCT = 0.25
LEG_H = 20
PRE, POST = 5, 2


def build_panel(bars: dict, start: str):
    """Daily cross-sectional percentiles from every ticker with bars: perf_1w/1m/3m/6m
    pctiles (rank of window return), rs_21d/63d/126d = same numbers on 0-99, and
    a 4-window composite. Returns dict of DataFrames indexed by date, columns tickers."""
    closes = pd.DataFrame({t: b["Close"] for t, b in bars.items() if t != "SPY" and len(b) > 130})
    closes = closes.sort_index().ffill(limit=3)
    out = {}
    for name, n in (("p1w", 5), ("p1m", 21), ("p3m", 63), ("p6m", 126)):
        r = closes / closes.shift(n) - 1
        out[name] = r
        out[name + "_pct"] = r.rank(axis=1, pct=True)
    comp = (out["p1w_pct"] + out["p1m_pct"] + out["p3m_pct"] + out["p6m_pct"]) / 4
    out["comp_pct"] = comp.rank(axis=1, pct=True)
    return {k: v.loc[start:] for k, v in out.items()}


def preset_flags(t: str, b: pd.DataFrame, df: pd.DataFrame, panel: dict) -> pd.DataFrame:
    """The Screener presets / Python screeners, approximated from bars + the
    cross-sectional panel (h_score / industry-dependent parts omitted)."""
    c, h, l, o, v = b["Close"], b["High"], b["Low"], b["Open"], b["Volume"]
    idx = df.index
    def col(name):
        return panel[name][t].reindex(idx) if t in panel[name].columns else pd.Series(np.nan, index=idx)
    p1w, p1m, p3m = col("p1w_pct"), col("p1m_pct"), col("p3m_pct")
    rs21 = p1m * 99; rs63 = p3m * 99
    comp = col("comp_pct")
    sma50 = c.rolling(50).mean(); sma200 = c.rolling(200).mean()
    wk = c.resample("W-FRI").last()
    def wma(s, n):
        w = np.arange(1, n + 1); return s.rolling(n).apply(lambda x: (x * w).sum() / w.sum(), raw=True)
    wk_tb = (wma(wk, 10) > wma(wk, 30)).reindex(c.index, method="ffill")
    trend_base = (c > sma50) & wk_tb.fillna(False)
    rv = df["rv"]; chg = df["chg"]; atr50 = df["atr50"]; e21 = df["e21"]
    adr = ((h / l - 1).rolling(20).mean() * 100)
    dcr = (c - l) / (h - l).replace(0, np.nan)
    from_open = c / o - 1
    perf1w = c / c.shift(5) - 1; perf1m = c / c.shift(21) - 1
    hi52 = c.rolling(252, min_periods=120).max(); off_hi = c / hi52 - 1
    avgv = v.rolling(20).mean()
    pp30 = df["sig_pp"].astype(int).rolling(30, min_periods=1).sum()
    ti65 = c.rolling(7).mean() / c.rolling(65).mean(); mdt = c / c.rolling(126).mean(); low52 = c / c.rolling(252, min_periods=120).min()
    quiet = chg.abs() <= 0.01
    bo = (chg >= 0.04) & (rv >= 1.5)
    bo1y = bo.astype(int).rolling(252, min_periods=60).sum(); bo3m = bo.astype(int).rolling(63, min_periods=20).sum()
    P = pd.DataFrame(index=idx)
    P["pre_composite97"] = comp >= 0.97
    P["pre_weekly_mom97"] = (p1w >= 0.97) & (p3m >= 0.85) & trend_base.reindex(idx) & adr.reindex(idx).between(3.5, 10)
    P["pre_monthly_leader97"] = (rs21 >= 97) & trend_base.reindex(idx) & adr.reindex(idx).between(3.5, 6)
    P["pre_4pct_bullish"] = (chg >= 0.04) & (rv >= 1) & (from_open.reindex(idx) >= 0) & (rs21 >= 60) & adr.reindex(idx).between(3.5, 10)
    P["pre_vol_up"] = (chg >= 0) & (rv >= 1.5) & adr.reindex(idx).between(3.5, 10)
    P["pre_weekly20"] = (perf1w.reindex(idx) >= 0.20) & adr.reindex(idx).between(3.5, 10)
    P["pre_healthy_charts"] = (c > sma50).reindex(idx) & (c > sma200).reindex(idx) & off_hi.reindex(idx).between(-0.25, -0.05) & (perf1m.reindex(idx) > 0) & (rs63 >= 80) & (rv >= 0.5)
    P["pre_ema21_watch"] = trend_base.reindex(idx) & e21.between(-0.5, 1) & atr50.between(0, 3) & perf1w.reindex(idx).between(0, 0.15) & (dcr.reindex(idx) >= 0.2) & (df["sig_pp"].astype(int).rolling(10, min_periods=1).sum() >= 1) & adr.reindex(idx).between(3, 6)
    P["pre_liquid_leader"] = (avgv.reindex(idx) >= 2e6) & (c > sma50).reindex(idx) & (rs63 >= 80)
    P["pre_ll_pullback"] = P["pre_liquid_leader"] & (perf1w.reindex(idx) < 0.12) & e21.between(0.5, 1) & atr50.between(0, 3)
    P["pre_anticipation"] = ((ti65.reindex(idx) > 1.05) | (low52.reindex(idx) >= 1.8) | (mdt.reindex(idx) > 1.19)) & quiet & (df["vcs"] >= 60) & (adr.reindex(idx) >= 3)
    P["pre_sugar_babies"] = (bo1y.reindex(idx) >= 10) & (bo3m.reindex(idx) >= 2)
    P["pre_stockbee_9m"] = (avgv.reindex(idx) >= 9e6) & (rv >= 1.5) & (chg >= 0.05) & (dcr.reindex(idx) >= 0.6)
    P["pre_pp_count"] = (pp30 >= 3) & trend_base.reindex(idx) & adr.reindex(idx).between(3.5, 6)
    P["pre_pocket_pivot"] = df["sig_pp"] & trend_base.reindex(idx) & adr.reindex(idx).between(3.5, 6)
    P["pre_extended7"] = atr50 >= 7
    P["pre_stop_hit"] = df["sp_signal"] == "stop_hit"
    P["pre_ll_break"] = df["sp_signal"] == "ll_break"
    P["pre_mom97_x_atr4"] = P["pre_composite97"] & (atr50 <= 4) & (atr50 > 0)
    return P.fillna(False).astype(bool)


def daily_signals(b: pd.DataFrame, spy: pd.Series, start: str) -> pd.DataFrame:
    c, h, l, o, v = b["Close"], b["High"], b["Low"], b["Open"], b["Volume"]
    df = pd.DataFrame(index=b.index)
    chg = c.pct_change()
    rv = v / v.rolling(50).mean().shift(1)
    ema10 = c.ewm(span=10, adjust=False).mean(); ema21 = c.ewm(span=21, adjust=False).mean()
    sma50 = c.rolling(50).mean()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    atr50 = (c - sma50) / atr
    e21 = (c - ema21) / atr
    hi20 = c > c.rolling(20).max().shift(1)
    rs = c / spy.reindex(c.index).ffill()
    rs_hi = rs >= rs.rolling(21).max()
    rs_pct = rs.rolling(21).apply(lambda w: (w <= w[-1]).mean() * 100, raw=True)
    df["chg"] = chg; df["rv"] = rv; df["atr50"] = atr50; df["e21"] = e21
    df["sig_4pct"] = (chg >= 0.04) & (rv >= 1)
    df["sig_ep"] = (chg >= 0.10) & (rv >= 3)
    df["sig_x_ema21"] = (c > ema21) & (c.shift(1) <= ema21.shift(1))
    df["sig_x_sma50"] = (c > sma50) & (c.shift(1) <= sma50.shift(1))
    df["sig_hi20"] = hi20
    df["sig_rs_hi21"] = rs_hi
    df["sig_pullback"] = (e21.between(0.5, 1.0)) & (atr50.between(0, 3)) & (c > sma50) & (chg.abs() < 0.04)
    df["sig_4pct_combo"] = df["sig_4pct"] & (atr50 <= 4) & (chg <= 0.08) & hi20 & rs_hi
    df["sig_first_wave"] = df["sig_4pct"] & (atr50 <= 4) & hi20 & rs_hi
    # Morales pocket pivot: up day, volume > max volume of down days in prior 10
    down_vol = v.where(c < c.shift(1))
    df["sig_pp"] = (c > c.shift(1)) & (v > down_vol.shift(1).rolling(10, min_periods=1).max())
    # VCS v2 series
    try:
        vr = vcs_engine(b[["High", "Low", "Close", "Volume"]])
        vs = vr.series if vr.series is not None else pd.Series(np.nan, index=b.index)
        vs.index = b.index[-len(vs):]
        df["vcs"] = vs.reindex(b.index)
    except Exception:
        df["vcs"] = np.nan
    df["sig_vcs60"] = df["vcs"] >= 60
    # Structure pivot signals: expanding runs from `start`
    sp_sig = pd.Series(None, index=b.index, dtype=object)
    idx0 = b.index.searchsorted(pd.Timestamp(start))
    for i in range(max(idx0, SP.MIN_BARS), len(b)):
        try:
            r = SP.run(b.iloc[: i + 1][["Open", "High", "Low", "Close"]])
            sp_sig.iloc[i] = r.signal
        except Exception:
            pass
    df["sp_signal"] = sp_sig
    df["sig_sp_entry"] = sp_sig.isin(["1st_break", "2nd_break", "counter_break"])
    df["fwd20"] = c.shift(-LEG_H) / c - 1
    df["fwd10"] = c.shift(-10) / c - 1
    df["max_fwd20"] = c[::-1].rolling(LEG_H, min_periods=1).max()[::-1].shift(-1) / c - 1
    return df.loc[start:]


def legs(df: pd.DataFrame):
    """Leg starts: first day of a run where max close in next 20 >= +LEG_PCT."""
    on = df["max_fwd20"] >= LEG_PCT
    starts = []
    prev = False
    for d, flag in on.items():
        if flag and not prev:
            starts.append(d)
        prev = bool(flag)
    return starts


def quality(t, b: pd.DataFrame, start: str) -> dict:
    w = b.loc[start:]
    gaps = 0
    if len(w) > 1:
        bd = pd.bdate_range(w.index[0], w.index[-1])
        gaps = max(0, len(bd) - len(w) - 12)     # allow ~12 holidays/yr
    ext = int((w["Close"].pct_change().abs() > 0.5).sum())
    return {"ticker": t, "bars_total": len(b), "bars_since_start": len(w), "first_bar": str(b.index[0].date()),
            "gaps_est": int(gaps), "moves_gt50pct": ext, "warmup_ok": len(b.loc[:start]) >= 100}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--themes", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--start", default="2026-01-02")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    bars = pickle.load(open(a.bars, "rb"))
    spy = bars["SPY"]["Close"]
    groups = {t["group"]: t for t in json.load(open("data/output/groups.json"))["themes"]}
    sig_cols = None
    all_fires, all_legs, dq, leaders_out = [], [], [], {}
    panel = build_panel(bars, a.start)
    for th in [x.strip() for x in a.themes.split(",")]:
        members = [t for t in groups[th]["tickers"] if t in bars and len(bars[t].loc[a.start:]) >= 60]
        ytd = {}
        for t in members:
            c = bars[t]["Close"]; w = c.loc[a.start:]
            ytd[t] = float(w.iloc[-1] / w.iloc[0] - 1)
        leaders = sorted(ytd, key=lambda t: -ytd[t])[: a.top]
        leaders_out[th] = [(t, round(ytd[t] * 100, 1)) for t in leaders]
        for t in leaders:
            b = bars[t]
            dq.append({"theme": th, **quality(t, b, a.start), "ytd_pct": round(ytd[t] * 100, 1)})
            df = daily_signals(b, spy, a.start)
            P = preset_flags(t, b, df, panel)
            df = df.join(P)
            sig_cols = [c for c in df.columns if c.startswith("sig_") or c.startswith("pre_")]
            L = legs(df)
            for d in L:
                all_legs.append({"theme": th, "ticker": t, "leg_start": str(d.date()), "close": float(b["Close"].loc[d]),
                                 "max_fwd20": float(df.loc[d, "max_fwd20"]), "atr50": float(df.loc[d, "atr50"]) if pd.notna(df.loc[d, "atr50"]) else None})
            for s in sig_cols:
                for d in df.index[df[s].fillna(False).astype(bool)]:
                    # nearest leg start relative to this fire
                    rel = [ (ls - d).days for ls in L ]
                    near = None
                    for ls in L:
                        k = int(np.busday_count(d.date(), ls.date())) if ls >= d else -int(np.busday_count(ls.date(), d.date()))
                        if -POST <= -k <= PRE or (-PRE <= k <= POST):
                            near = k; break
                    all_fires.append({"theme": th, "ticker": t, "signal": s, "date": str(d.date()),
                                      "hit_window": near is not None, "fwd10": df.loc[d, "fwd10"], "fwd20": df.loc[d, "fwd20"],
                                      "leg_within20": bool(df.loc[d, "max_fwd20"] >= LEG_PCT)})
    F = pd.DataFrame(all_fires); Lg = pd.DataFrame(all_legs); Q = pd.DataFrame(dq)
    F.to_csv(out / "fires.csv", index=False); Lg.to_csv(out / "legs.csv", index=False); Q.to_csv(out / "data_quality.csv", index=False)
    json.dump(leaders_out, open(out / "leaders.json", "w"), indent=1)
    # scoreboard
    rows = []
    n_legs = len(Lg)
    for s, g in F.groupby("signal"):
        # legs caught: a leg is caught if any fire of s within [-PRE,+POST]
        caught = 0
        for _, lg in Lg.iterrows():
            d0 = pd.Timestamp(lg.leg_start)
            f = g[(g.ticker == lg.ticker)]
            ds = pd.to_datetime(f.date)
            k = [(int(np.busday_count(min(x.date(), d0.date()), max(x.date(), d0.date()))) * (1 if x <= d0 else -1)) for x in ds]
            if any(-POST <= kk <= PRE for kk in k):
                caught += 1
        rows.append({"signal": s, "fires": len(g), "legs": n_legs, "legs_caught": caught,
                     "recall": round(caught / max(1, n_legs), 3),
                     "precision(leg_within20)": round(g.leg_within20.mean(), 3),
                     "fwd10_med": round(float(g.fwd10.median()) * 100, 2), "fwd20_med": round(float(g.fwd20.median()) * 100, 2),
                     "fwd20_win": round(float((g.fwd20 > 0).mean()), 2)})
    S = pd.DataFrame(rows).sort_values("recall", ascending=False)
    S.to_csv(out / "scoreboard.csv", index=False)
    pd.set_option("display.width", 200)
    print("leaders:", json.dumps(leaders_out, ensure_ascii=False))
    print(f"legs (>= +{int(LEG_PCT*100)}% within {LEG_H}): {n_legs}")
    print(S.to_string(index=False))
    print("\nDATA QUALITY:")
    print(Q.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
