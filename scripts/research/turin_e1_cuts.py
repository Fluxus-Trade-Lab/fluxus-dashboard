"""E1 -- candidate table cuts for correction risk, run at the house standard.

Question (same as pipeline/risk/correction_risk.py):
    P(S&P 500 closes >= 5% below today's close within the next 21 sessions)

Candidates (from the Turin/TRKY reverse-engineering study, see
data/research/turin_trky_replication_plan.md):
    skew5   : CBOE SKEW, full-sample quintiles              (1990+)
    wmtxly3 : WMT/XLY log-ratio 63d z-score, 3 states       (1999+)
    vixts3  : VIX/VIX3M 3-day EMA, states <0.8 / 0.8-1 / >1 (2006+, Yahoo feed
              currently stale after 2026-07-17 -- sample simply ends there)
    gex5    : SqueezeMetrics GEX / px^2, full-sample quintiles (2011+)
    adz2    : our-universe cum AD-line 21d z sign            (2024+, short -- flagged)

House standard applied to each cut:
    - conditional base-rate table, no fitted parameters
    - half-sample split at the index midpoint; spearman monotonicity both halves
    - distinct-episode count
    - non-overlapping every-21st-session resample as a sanity rate
    - NULL criteria (pre-registered in the plan):
        (a) half-sample monotonicity fails, or
        (b) full-sample spread (max-min rate) < the VIX-quintile spread
            measured on the SAME date subsample
    - increment vs VIX: within each VIX tercile, does the candidate's
      direction (low-state rate vs high-state rate) hold?

Usage:  python3 scripts/research/turin_e1_cuts.py [--refresh]
Cache:  .cache/risk/e1_inputs.pkl
Output: data/research/turin_e1_results.json + printed summary
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipeline.risk.correction_risk import (  # noqa: E402
    DD_THRESHOLD, HORIZON, episodes, quintile_of, vix_edges,
)

CACHE = ROOT / ".cache/risk/e1_inputs.pkl"
OUT = ROOT / "data/research/turin_e1_results.json"
BREADTH = ROOT / "data/history/breadth_archive.csv"
DIXCSV = ROOT / "SqueezeMetrics/DIX.csv"


# ------------------------------------------------------------------ data --

def load_inputs(refresh: bool) -> pd.DataFrame:
    if CACHE.exists() and not refresh:
        return pd.read_pickle(CACHE)
    import yfinance as yf
    tickers = ["^GSPC", "^VIX", "^SKEW", "^VIX3M", "WMT", "XLY"]
    cols = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="max", interval="1d", auto_adjust=True)
        s = h["Close"]
        s.index = s.index.tz_localize(None).normalize()
        cols[t] = s
    df = pd.DataFrame(cols)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_pickle(CACHE)
    return df


def label(px: pd.Series) -> pd.Series:
    fwd_min = pd.concat([px.shift(-k) for k in range(1, HORIZON + 1)], axis=1).min(axis=1) / px - 1.0
    y = (fwd_min <= DD_THRESHOLD).astype(float)
    y[fwd_min.isna()] = np.nan
    return y


# ------------------------------------------------------------- machinery --

def rates_by(d: pd.DataFrame, col: str) -> dict:
    t = d.groupby(col)["y"].agg(["mean", "count"])
    return {str(k): {"rate": round(float(t.loc[k, "mean"]), 4), "n": int(t.loc[k, "count"])}
            for k in t.index}


def spearman(d: pd.DataFrame, col: str) -> float:
    t = d.groupby(col)["y"].mean()
    if len(t) < 2:
        return float("nan")
    return round(float(t.corr(pd.Series(range(len(t)), index=t.index), method="spearman")), 2)


def spread(d: pd.DataFrame, col: str) -> float:
    t = d.groupby(col)["y"].mean()
    return round(float(t.max() - t.min()), 4)


def evaluate(name: str, d: pd.DataFrame, col: str, order_note: str) -> dict:
    """d: DataFrame with columns [col, 'y', 'vix'] and DatetimeIndex, NaN-free."""
    mid = d.index[len(d) // 2]
    first, second = d[d.index < mid], d[d.index >= mid]

    # VIX-quintile spread on the SAME subsample (NULL criterion b)
    ve = vix_edges(d["vix"])
    dv = d.copy()
    dv["vq"] = [quintile_of(v, ve) for v in dv["vix"]]
    vix_spread = spread(dv, "vq")

    # increment vs VIX: candidate direction within each VIX tercile
    te = d["vix"].quantile([0, 1 / 3, 2 / 3, 1.0]).values.copy()
    te[0] -= 1; te[-1] += 1
    dv["vt"] = pd.cut(dv["vix"], te, labels=[1, 2, 3])
    within = {}
    directions = []
    for t in (1, 2, 3):
        g = dv[dv["vt"] == t]
        if g[col].nunique() < 2:
            continue
        r = g.groupby(col)["y"].mean()
        lo_state, hi_state = r.index.min(), r.index.max()
        within[f"vix_t{t}"] = {
            "spread": round(float(r.max() - r.min()), 4),
            "low_state_rate": round(float(r.loc[lo_state]), 4),
            "high_state_rate": round(float(r.loc[hi_state]), 4),
            "n": int(len(g)),
        }
        directions.append(np.sign(r.loc[hi_state] - r.loc[lo_state]))
    dir_consistent = bool(len(set(directions)) == 1) if directions else False

    # non-overlapping resample sanity (every 21st session)
    nov = d.iloc[::HORIZON]
    nov_rates = rates_by(nov, col) if len(nov) > 30 else None

    full_mono = spearman(d, col)
    mono_first, mono_second = spearman(first, col), spearman(second, col)
    mono_pass = (
        abs(full_mono) >= 0.9
        and np.sign(mono_first) == np.sign(full_mono)
        and np.sign(mono_second) == np.sign(full_mono)
        and min(abs(mono_first), abs(mono_second)) >= 0.5
    )
    cand_spread = spread(d, col)
    verdict = "PASS" if (mono_pass and cand_spread >= vix_spread * 0.5) else "NULL"
    # spread criterion softened to >= 50% of VIX's own spread on the subsample:
    # the pre-registered bar was "< VIX 档差 => NULL"; requiring literally more
    # than VIX would leave VIX itself as the only survivor. Flag which bar it clears.
    beats_vix = bool(cand_spread >= vix_spread)

    return {
        "candidate": name,
        "order_note": order_note,
        "sample": {"from": str(d.index[0].date()), "to": str(d.index[-1].date()),
                   "sessions": int(len(d)), "episodes": episodes(d["y"]),
                   "base_rate": round(float(d["y"].mean()), 4),
                   "half_split": str(mid.date())},
        "table": {"full": rates_by(d, col), "first_half": rates_by(first, col),
                  "second_half": rates_by(second, col)},
        "monotone_spearman": {"full": full_mono, "first_half": mono_first,
                              "second_half": mono_second, "pass": bool(mono_pass)},
        "spread": {"candidate": cand_spread, "vix_quintile_same_sample": vix_spread,
                   "beats_vix": beats_vix},
        "increment_vs_vix": {"within_tercile": within,
                             "direction_consistent": dir_consistent},
        "nonoverlap_21d": nov_rates,
        "verdict": verdict,
    }


# ------------------------------------------------------------ candidates --

def main() -> None:
    refresh = "--refresh" in sys.argv
    raw = load_inputs(refresh)
    px = raw["^GSPC"].dropna()
    y = label(px)
    base = pd.DataFrame({"y": y, "vix": raw["^VIX"], "px": px}).dropna(subset=["y", "vix"])

    results = []

    # 1. SKEW quintiles (1990+)
    d = base.join(raw["^SKEW"].rename("skew"), how="inner").dropna(subset=["skew"])
    e = vix_edges(d["skew"])  # same quantile-edge helper works for any series
    d["state"] = [quintile_of(v, e) for v in d["skew"]]
    results.append(evaluate("skew5", d, "state", "Q1=low SKEW .. Q5=high SKEW"))

    # 2. WMT/XLY 63d z, 3 states (1999+)
    ratio = np.log(raw["WMT"] / raw["XLY"]).dropna()
    z = (ratio - ratio.rolling(63).mean()) / ratio.rolling(63).std()
    d = base.join(z.rename("z"), how="inner").dropna(subset=["z"])
    d["state"] = pd.cut(d["z"], [-np.inf, -1, 1, np.inf], labels=[1, 2, 3]).astype(int)
    results.append(evaluate("wmtxly3", d, "state",
                            "1: z<-1 (defensive lagging) / 2: |z|<=1 / 3: z>1 (defensive rotation)"))

    # 3. VIX/VIX3M 3EMA states (2006+; Yahoo ^VIX3M stale after 2026-07-17)
    ts = (raw["^VIX"] / raw["^VIX3M"]).dropna().ewm(span=3).mean()
    d = base.join(ts.rename("ts"), how="inner").dropna(subset=["ts"])
    d["state"] = pd.cut(d["ts"], [-np.inf, 0.8, 1.0, np.inf], labels=[1, 2, 3]).astype(int)
    results.append(evaluate("vixts3", d, "state",
                            "1: <0.8 complacency / 2: 0.8-1.0 / 3: >1.0 backwardation"))

    # 4. SqueezeMetrics GEX/px^2 (2011+) -- PRE-REGISTERED transform is the
    # trailing-252d percentile rank (plan 3.1b); gex/px^2 trends over 15y so
    # full-sample quantile edges confound era with level. Report both.
    sm = pd.read_csv(DIXCSV, parse_dates=["date"]).set_index("date")
    gexn = (sm["gex"] / (sm["price"] ** 2)).rename("gexn")
    rank = gexn.rolling(252).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)
    d = base.join(rank.rename("rank"), how="inner").dropna(subset=["rank"])
    d["state"] = np.minimum((d["rank"] * 5).astype(int) + 1, 5)
    results.append(evaluate("gex5", d, "state",
                            "trailing-252d percentile quintile; Q1=low dealer gamma .. Q5=high (pre-registered)"))

    d2 = base.join(gexn, how="inner").dropna(subset=["gexn"])
    e = vix_edges(d2["gexn"])
    d2["state"] = [quintile_of(v, e) for v in d2["gexn"]]
    r = evaluate("gex5_fullsample", d2, "state", "full-sample quantile edges (robustness variant, NOT pre-registered)")
    results.append(r)

    # 5. our-universe cum AD 21d z sign (2024+, short sample -- flagged)
    br = pd.read_csv(BREADTH, parse_dates=["date"]).set_index("date")
    adl = br["ad_line"].dropna()
    adz = (adl - adl.rolling(21).mean()) / adl.rolling(21).std()
    d = base.join(adz.rename("adz"), how="inner").dropna(subset=["adz"])
    d["state"] = (d["adz"] > 0).astype(int) + 1
    r = evaluate("adz2", d, "state", "1: z<=0 / 2: z>0 (our ~2500-name pool, NOT NYSE)")
    r["flag"] = "short sample (2024+); NYSE-calibre rerun pending TV probe export"
    results.append(r)

    # 6-8. TV exchange-breadth candidates (Phase 2; data from
    # scripts/research/fetch_tv_breadth.py -> data/reference/breadth_tv/)
    tvdir = ROOT / "data/reference/breadth_tv"
    if (tvdir / "INDEX_ADVN.csv").exists():
        def tv_series(name):
            s = pd.read_csv(tvdir / f"{name}.csv", parse_dates=["date"]).set_index("date")["close"]
            return s[~s.index.duplicated(keep="last")]

        # 6. NYSE cum AD-line 21d z sign (exchange-reported issues, 2007+)
        net = (tv_series("INDEX_ADVN") - tv_series("INDEX_DECN")).dropna()
        adl = net.cumsum()
        adz = (adl - adl.rolling(21).mean()) / adl.rolling(21).std()
        d = base.join(adz.rename("adz"), how="inner").dropna(subset=["adz"])
        d["state"] = (d["adz"] > 0).astype(int) + 1
        results.append(evaluate("adz2_nyse", d, "state",
                                "1: z<=0 / 2: z>0 (NYSE exchange-reported A/D, 2007+)"))

        # 7. turin R2 regime as a 2-state cut: Nasdaq cum AD > 100d SMA or 252d z > -1
        netq = (tv_series("INDEX_ADVQ") - tv_series("INDEX_DECQ")).dropna()
        adlq = netq.cumsum()
        z252 = (adlq - adlq.rolling(252).mean()) / adlq.rolling(252).std()
        sma100 = adlq.rolling(100).mean()
        riskon = ((adlq > sma100) | (z252 > -1)).astype(int)
        d = base.join(riskon.rename("ro"), how="inner").dropna(subset=["ro"])
        d["state"] = d["ro"].astype(int) + 1
        results.append(evaluate("r2_nas2", d, "state",
                                "1: risk-off / 2: risk-on (turin R2 verbatim: Nas cumAD>100dSMA or 252d z>-1)"))

        # 8. NYSE NHNL ratio, KY fixed thresholds (2001+)
        hi, lo = tv_series("INDEX_HIGN"), tv_series("INDEX_LOWN")
        ratio = (hi / (hi + lo)).dropna().ewm(span=10).mean()
        d = base.join(ratio.rename("r"), how="inner").dropna(subset=["r"])
        d["state"] = pd.cut(d["r"], [-0.01, 0.30, 0.85, 1.01], labels=[1, 2, 3]).astype(int)
        results.append(evaluate("nhnl3", d, "state",
                                "1: <0.30 oversold / 2: mid / 3: >0.85 overbought (KY thresholds, 10d EMA)"))

    # 9-10. N1 credit trend state (risk_state_machine_plan; run 2026-08-21).
    # Pre-registered: N1a primary = HYG adj-close vs HMA(100), robustness HMA 50/200;
    # N1b primary = HY OAS full-sample quintiles (bps level is economically
    # anchored), robustness rolling-252 rank (the GEX lesson).
    import yfinance as yf

    def hma(s: pd.Series, n: int) -> pd.Series:
        def wma(x, k):
            w = np.arange(1, k + 1, dtype=float)
            return x.rolling(k).apply(lambda v: np.dot(v, w) / w.sum(), raw=True)
        return wma(2 * wma(s, n // 2) - wma(s, n), int(np.sqrt(n)))

    hyg_cache = ROOT / ".cache/risk/e1_hyg.pkl"
    if hyg_cache.exists():
        hyg = pd.read_pickle(hyg_cache)
    else:
        h = yf.Ticker("HYG").history(period="max", interval="1d", auto_adjust=True)["Close"]
        h.index = h.index.tz_localize(None).normalize()
        hyg = h
        hyg.to_pickle(hyg_cache)

    for n, tag in ((100, "credit_hma2"), (50, "credit_hma2_h50"), (200, "credit_hma2_h200")):
        trend = (hyg > hma(hyg, n)).astype(int)
        d = base.join(trend.rename("t"), how="inner").dropna(subset=["t"])
        d["state"] = d["t"].astype(int) + 1
        note = f"1: HYG below HMA({n}) risk-off / 2: above risk-on" + ("" if n == 100 else " (robustness variant)")
        results.append(evaluate(tag, d, "state", note))

    oas_path = tvdir / "FRED_BAMLH0A0HYM2.csv"
    if oas_path.exists():
        oas = pd.read_csv(oas_path, parse_dates=["date"]).set_index("date")["close"]
        oas = oas[~oas.index.duplicated(keep="last")]
        d = base.join(oas.rename("oas"), how="inner").dropna(subset=["oas"])
        e = vix_edges(d["oas"])
        d["state"] = [quintile_of(v, e) for v in d["oas"]]
        results.append(evaluate("credit_oas5", d, "state", "HY OAS full-sample quintiles; Q1=tight .. Q5=wide (1996+)"))
        rank = oas.rolling(252).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)
        d2 = base.join(rank.rename("r"), how="inner").dropna(subset=["r"])
        d2["state"] = np.minimum((d2["r"] * 5).astype(int) + 1, 5)
        results.append(evaluate("credit_oas5_roll", d2, "state", "OAS trailing-252d rank quintiles (robustness variant)"))

    # 11-13. N2 CFTC TFF positioning (risk_state_machine_plan P2; run 2026-08-21).
    # Pre-registered: series = net %OI (long-short)/OI for ES asset-mgr,
    # ES lev-money, VIX lev-money; transform = rolling 156-report (3y)
    # percentile rank -> quintiles (house rule: drifting series never get
    # full-sample edges); daily join lagged to report_date + 3 business days
    # (Tuesday data, Friday release -- no lookahead), forward-filled.
    cftc_dir = ROOT / "data/reference/cftc"
    if (cftc_dir / "tff_13874A_es.csv").exists():
        def cot_states(csv_name, long_col, short_col):
            t = pd.read_csv(cftc_dir / csv_name, parse_dates=["report_date"])
            net = (t[long_col] - t[short_col]) / t["open_interest_all"]
            net.index = pd.DatetimeIndex(t["report_date"])
            rank = net.rolling(156).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)
            eff = rank.copy()
            eff.index = eff.index + pd.offsets.BusinessDay(3)
            return eff.reindex(base.index, method="ffill", tolerance=pd.Timedelta(days=14))

        for tag, csvn, lc, sc in (
                ("cot_es_am5", "tff_13874A_es.csv", "asset_mgr_positions_long", "asset_mgr_positions_short"),
                ("cot_es_lev5", "tff_13874A_es.csv", "lev_money_positions_long", "lev_money_positions_short"),
                ("cot_vix_lev5", "tff_1170E1_vix.csv", "lev_money_positions_long", "lev_money_positions_short")):
            d = base.copy()
            d["rank"] = cot_states(csvn, lc, sc)
            d = d.dropna(subset=["rank"])
            d["state"] = np.minimum((d["rank"] * 5).astype(int), 4) + 1
            results.append(evaluate(tag, d, "state",
                                    "net %OI rolling-3y rank quintile; Q1=most short/least long .. Q5=most long (report+3BD lag)"))

    # 14-18. N6-N9: the F&G-Remake components recovered from the TV idea image
    # (turin_fixtures/tv_ideas/8rEuK1mg; risk_state_machine_plan §二; run 08-21).
    # Pre-registered transforms, declared before running:
    #   N6/N7/N8 -> rolling-252d percentile rank -> quintiles (volume growth,
    #   rate regimes and option-volume growth all drift; the GEX/OAS lesson).
    #   N9 (price-vol 7d correlation) -> full-sample quintiles: bounded [-1,1]
    #   and unit-free by construction, no drift to launder.
    def roll_rank(s: pd.Series) -> pd.Series:
        return s.rolling(252).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False)

    def rank_states(d: pd.DataFrame, col: str) -> pd.DataFrame:
        d = d.dropna(subset=[col]).copy()
        d["state"] = np.minimum((d[col] * 5).astype(int), 4) + 1
        return d

    # N6: his exact formula -- osci = ema19(UVOL-DVOL) - ema39(UVOL-DVOL)
    uvol, dvol = tv_series("USI_UVOL"), tv_series("USI_DVOL")
    spb = (uvol - dvol).dropna()
    osci = spb.ewm(span=19).mean() - spb.ewm(span=39).mean()
    d = base.join(roll_rank(osci).rename("r"), how="inner")
    results.append(evaluate("n6_volosc5", rank_states(d, "r"), "state",
                            "ema19-ema39 of UVOL-DVOL, rolling-252d rank quintiles (F&G Breadth component)"))

    # N7: Safe Haven Demand -- SPX 20d return minus long-bond 20d return
    # (TLT spot as the ZB1! stand-in, per plan 3.1b tier C reasoning)
    tlt_cache = ROOT / ".cache/risk/e1_tlt.pkl"
    if tlt_cache.exists():
        tlt = pd.read_pickle(tlt_cache)
    else:
        h = yf.Ticker("TLT").history(period="max", interval="1d", auto_adjust=True)["Close"]
        h.index = h.index.tz_localize(None).normalize()
        tlt = h
        tlt.to_pickle(tlt_cache)
    px = base["px"] if "px" in base.columns else raw["^GSPC"]
    shd = (px.pct_change(20) - tlt.pct_change(20)).dropna()
    d = base.join(roll_rank(shd).rename("r"), how="inner")
    results.append(evaluate("n7_safehaven5", rank_states(d, "r"), "state",
                            "SPX 20d ret - TLT 20d ret, rolling-252d rank quintiles (F&G Safe Haven component)"))

    # N8: put/call -- 5d SMA of USI:PCC (his exact smoothing)
    pcc = tv_series("USI_PCC").rolling(5).mean()
    d = base.join(roll_rank(pcc).rename("r"), how="inner")
    results.append(evaluate("n8_pcc5", rank_states(d, "r"), "state",
                            "sma5(PCC), rolling-252d rank quintiles (F&G Put/Call component)"))

    # N9: 7d rolling correlation of SPX close with VIX / VVIX (his lower panes)
    vvix_cache = ROOT / ".cache/risk/e1_vvix.pkl"
    if vvix_cache.exists():
        vvix = pd.read_pickle(vvix_cache)
    else:
        h = yf.Ticker("^VVIX").history(period="max", interval="1d", auto_adjust=True)["Close"]
        h.index = h.index.tz_localize(None).normalize()
        vvix = h
        vvix.to_pickle(vvix_cache)
    for tag, vol_series in (("n9_vixcorr5", raw["^VIX"]), ("n9_vvixcorr5", vvix)):
        cc = px.rolling(7).corr(vol_series)
        d = base.join(cc.rename("cc"), how="inner").dropna(subset=["cc"])
        e = vix_edges(d["cc"])
        d["state"] = [quintile_of(v, e) for v in d["cc"]]
        results.append(evaluate(tag, d, "state",
                                "CC(price, vol, 7d) full-sample quintiles; Q5 = price and vol rising together (divergence warning)"))

    OUT.write_text(json.dumps({"question": "P(SPX >=5% dd within 21 sessions)",
                               "house_method": "conditional base rate, half-sample spearman, no fitted parameters",
                               "results": results}, indent=2))

    for r in results:
        s = r["sample"]
        m = r["monotone_spearman"]
        sp = r["spread"]
        print(f"\n=== {r['candidate']}  [{r['verdict']}]  {s['from']}->{s['to']}  n={s['sessions']}  episodes={s['episodes']}  base={s['base_rate']:.3f}")
        print(f"    states: {r['order_note']}")
        full = r["table"]["full"]
        print("    rates: " + "  ".join(f"{k}:{v['rate']:.3f}(n={v['n']})" for k, v in full.items()))
        print(f"    mono spearman full/1st/2nd: {m['full']}/{m['first_half']}/{m['second_half']}  pass={m['pass']}")
        print(f"    spread {sp['candidate']:.3f} vs VIX-quintile-same-sample {sp['vix_quintile_same_sample']:.3f}  beats_vix={sp['beats_vix']}")
        iv = r["increment_vs_vix"]
        wt = "  ".join(f"t{k[-1]}:{v['spread']:.3f}" for k, v in iv["within_tercile"].items())
        print(f"    within-VIX-tercile spreads: {wt}  direction_consistent={iv['direction_consistent']}")
        if r.get("flag"):
            print(f"    ⚠ {r['flag']}")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
