"""Jeff Sun's (@jfsrev) scanner list -- his definitions, verbatim, as data.

Two primary sources, both on this machine or linked from it:

  * The TradingView queries: a Colab notebook someone wrote against
    `tradingview_screener` reproducing 5 operational scans + 8 momentum scans
    (drive id 17SGXf_8L1LZQ78XcSEVGJvmGGVSPBLTJ). Every clause below is copied
    from that code, not paraphrased.
  * The Finviz URLs: Jeff's own tweets, archived in JeffSun_Wiki/sources/
    tweets/. A Finviz URL IS the scan definition -- `f=` carries every filter
    -- so those are transcribed as filter codes and decoded with Finviz's
    published semantics (help/screener.ashx: Volatility = "average daily
    high/low % range", Average Volume = 3-month, Relative Volume = today /
    3-month average).

What this module deliberately is NOT: an attempt to reproduce Jeff's lists on
our own universe and call the result "Jeff's scan". Our universe.json lacks
float, short float, IPO date, FCF growth and a 60-day average volume, and its
`avg_volume` is a 20-session mean where TradingView's is 60 and Finviz's is
3 months. `local_mask()` therefore applies only the clauses it CAN express and
returns the list of clauses it skipped, so a partial replication is labelled
as partial rather than passed off as the thing.

Tier (data/reference/METRIC_SOURCES.md): the specs are T1 -- author's own
words. Any local replication is T2 at best, and says which clauses it dropped.

Run the real thing:   `python -m pipeline.screeners.jeff_sun --tv`
(needs `tradingview-screener`; not a pipeline dependency, not in the cron.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

US = ["NASDAQ", "NYSE", "AMEX"]


@dataclass(frozen=True)
class Clause:
    field: str          # TradingView field name (or Finviz code for finviz specs)
    op: str             # '>', '>=', '<', '<=', '==', 'between', 'isin', '>col'
    value: Any


@dataclass(frozen=True)
class Scan:
    key: str
    title: str
    source: str                         # URL / notebook id
    platform: str                       # 'tradingview' | 'finviz'
    clauses: Tuple[Clause, ...]
    post: Tuple[str, ...] = ()          # post-filters applied in pandas, verbatim
    group: str = ""                     # 'Individual' | 'Momentum small' | 'Momentum large' | 'Finviz'
    note: str = ""


def _base(cap_lo=None, cap_hi=None, avgvol=300_000, vol=None, float_lt=None, volm=None):
    c = [Clause("type", "==", "stock"), Clause("exchange", "isin", US)]
    if cap_lo is not None and cap_hi is not None:
        c.append(Clause("market_cap_basic", "between", (cap_lo, cap_hi)))
    elif cap_lo is not None:
        c.append(Clause("market_cap_basic", ">", cap_lo))
    c.append(Clause("average_volume_60d_calc", ">", avgvol))
    if vol is not None:
        c.append(Clause("volume", ">", vol))
    if float_lt is not None:
        c.append(Clause("float_shares_outstanding", "<", float_lt))
    if volm is not None:
        c.append(Clause("Volatility.M", ">", volm))
    return c


COLAB = "colab:17SGXf_8L1LZQ78XcSEVGJvmGGVSPBLTJ"

# ---------------------------------------------------------------- TradingView
TV_SCANS: Dict[str, Scan] = {
    "1_Fundamental_Growth": Scan(
        "1_Fundamental_Growth", "Fundamental Growth (CANSLIM-inspired)", COLAB, "tradingview",
        tuple(_base(cap_lo=300_000_000, avgvol=300_000, float_lt=100_000_000) + [
            Clause("earnings_per_share_diluted_yoy_growth_fq", ">", 25),
            Clause("free_cash_flow_yoy_growth_ttm", ">", 25),
            Clause("total_revenue_yoy_growth_fq", ">", 25),
        ]), group="Individual",
        note="Jeff's tweet 1796806706028302775: sales & EPS >25% YoY, only a 50-MA technical "
             "filter, 1M volatility 3% to drop M&A names; 'not an actionable scan'."),
    "3_Post_Earnings_Cont_Base": Scan(
        "3_Post_Earnings_Cont_Base", "Post-Earnings Continuation Base", COLAB, "tradingview",
        tuple(_base(cap_lo=50_000_000, avgvol=250_000, float_lt=50_000_000) + [
            Clause("close", ">col", "SMA20"),
            Clause("relative_volume_10d_calc", ">=", 2),
            Clause("gap", ">", 5),
        ]), group="Individual"),
    "4_Strongest_Stock_JK": Scan(
        "4_Strongest_Stock_JK", "Strongest Stock (Julian Komar) -- small/mid", COLAB, "tradingview",
        tuple(_base(cap_lo=300_000_000, cap_hi=10_000_000_000, avgvol=500_000, float_lt=50_000_000, volm=3) + [
            Clause("earnings_per_share_diluted_yoy_growth_fq", ">", 25),
            Clause("total_revenue_yoy_growth_fq", ">", 25),
            Clause("close", ">col", "SMA50"),
        ]),
        post=("close >= price_52_week_low * 1.70", "SMA10 <= close", "SMA10 >= close * 0.90"),
        group="Individual", note="screener-overview #14, 'Julian Komar's Strongest Stock Scan (bonus)'"),
    "5_Strongest_Stock_10B_Rev_30_JK": Scan(
        "5_Strongest_Stock_10B_Rev_30_JK", "Strongest Stock (Julian Komar) -- >$10B", COLAB, "tradingview",
        tuple(_base(cap_lo=10_000_000_000, avgvol=500_000, float_lt=150_000_000, volm=2) + [
            Clause("earnings_per_share_diluted_yoy_growth_fq", ">", 25),
            Clause("total_revenue_yoy_growth_fq", ">", 25),
            Clause("close", ">col", "SMA50"),
        ]),
        post=("close >= price_52_week_low * 1.70", "SMA10 <= close", "SMA10 >= close * 0.97"),
        group="Individual"),
    "Daily_Tightness_Swing": Scan(
        "Daily_Tightness_Swing", "Daily Tightness Swing", COLAB, "tradingview",
        tuple(_base(cap_lo=300_000_000, avgvol=300_000, vol=100_000, float_lt=50_000_000, volm=3.5) + [
            Clause("Perf.W", "<", 5),
        ]),
        post=("close >= price_52_week_low * 1.50", "EMA5 <= close", "EMA5 >= close * 0.97", "SMA10 > SMA20"),
        group="Individual",
        note="Jeff's 'Watchlist Scan' tweet 1770337966814363698: tightness = within 5% of the 5-EMA."),
}

_MOM = [("1W", "Perf.W", 20), ("1M", "Perf.1M", 30), ("3M", "Perf.3M", 70), ("6M", "Perf.6M", 100)]
for tf, fld, thr in _MOM:
    TV_SCANS[f"Mom_{tf}_Small"] = Scan(
        f"Mom_{tf}_Small", f"Strongest Mover {tf} -- $300M-$10B", COLAB, "tradingview",
        tuple(_base(cap_lo=300_000_000, cap_hi=10_000_000_000, avgvol=300_000, vol=100_000,
                    float_lt=50_000_000, volm=3) + [Clause(fld, ">", thr)]),
        post=("close >= price_52_week_low * 1.50", "SMA10 <= close", "SMA10 >= close * 0.80"),
        group="Momentum small")
    TV_SCANS[f"Mom_{tf}_Large"] = Scan(
        f"Mom_{tf}_Large", f"Strongest Mover {tf} -- >$10B", COLAB, "tradingview",
        tuple(_base(cap_lo=10_000_000_000, avgvol=300_000, vol=100_000, float_lt=150_000_000)
              + [Clause(fld, ">", thr)]),
        post=("close >= price_52_week_low * 1.50", "SMA10 <= close", "SMA10 >= close * 0.90"),
        group="Momentum large")

# ---------------------------------------------------------------------- Finviz
# Codes decoded per finviz.com/help/screener.ashx. `ta_volatility_mo5` = monthly
# average daily high/low % range over 5; `sh_avgvol_o300` = 3-month average
# volume over 300K; `sh_curvol_o100` = today's volume over 100K.
FINVIZ_SCANS: Dict[str, Scan] = {
    "FV_Mover_1W_20": Scan("FV_Mover_1W_20", "1-Week Mover >20% (Finviz)",
        "https://x.com/jfsrev/status/1659786288067928064", "finviz",
        (Clause("cap", ">=", "small"), Clause("sh_avgvol", ">", 300_000), Clause("sh_curvol", ">", 100_000),
         Clause("ta_perf_1w", ">", 20), Clause("ta_volatility_w", ">", 4)), group="Finviz"),
    "FV_Mover_1M_30": Scan("FV_Mover_1M_30", "1-Month Mover >30% (Finviz)",
        "https://x.com/jfsrev/status/1659786288067928064", "finviz",
        (Clause("cap", ">=", "small"), Clause("sh_avgvol", ">", 300_000), Clause("sh_curvol", ">", 100_000),
         Clause("ta_perf_4w", ">", 30), Clause("ta_volatility_m", ">", 5)), group="Finviz",
        note="Jeff toggles to >50% 'if too many results in a strong market'."),
    "FV_Mover_3M_50": Scan("FV_Mover_3M_50", "3-Month Mover >50% (Finviz)",
        "https://x.com/jfsrev/status/1659786288067928064", "finviz",
        (Clause("cap", ">=", "small"), Clause("sh_avgvol", ">", 300_000), Clause("sh_curvol", ">", 100_000),
         Clause("ta_perf_13w", ">", 50), Clause("ta_volatility_m", ">", 5)), group="Finviz"),
    "FV_Mover_6M_100": Scan("FV_Mover_6M_100", "6-Month Mover >100% (Finviz)",
        "https://x.com/jfsrev/status/1659786288067928064", "finviz",
        (Clause("cap", ">=", "small"), Clause("sh_avgvol", ">", 300_000), Clause("sh_curvol", ">", 100_000),
         Clause("ta_perf_26w", ">", 100), Clause("ta_volatility_m", ">", 5)), group="Finviz"),
    "FV_Qullamaggie_TASR": Scan("FV_Qullamaggie_TASR", "High ADR% x Low Float x High Short Float (Qullamaggie/TASR style)",
        "https://x.com/jfsrev/status/1944595506853970049", "finviz",
        (Clause("cap", ">=", "small"), Clause("ind", "==", "stocksonly"), Clause("sh_avgvol", ">", 1_000_000),
         Clause("sh_float", "<", 100_000_000), Clause("sh_short", ">", 30)), group="Finviz",
        note="'The best % performers almost always have these three ingredients.'"),
    "FV_IPO": Scan("FV_IPO", "IPO screener (weekly)",
        "https://x.com/jfsrev/status/1941836386904285491", "finviz",
        (Clause("cap", ">=", "mid"), Clause("fa_epsyoy1", ">", 0), Clause("ipodate", "==", "prevyear"),
         Clause("sh_avgvol", ">", 1_000_000)), group="Finviz"),
    "FV_Liquid_ETF": Scan("FV_Liquid_ETF", "Liquid ETF (weekly volatility >3)",
        "https://x.com/jfsrev/status/1962458102709837975", "finviz",
        (Clause("ind", "==", "exchangetradedfund"), Clause("sh_avgvol", ">", 1_000_000),
         Clause("ta_volatility_w", ">", 3)), group="Finviz"),
}

ALL_SCANS: Dict[str, Scan] = {**TV_SCANS, **FINVIZ_SCANS}


# ------------------------------------------------------------ TradingView run
def to_tv_query(scan: Scan):
    """Build the tradingview_screener Query for a TV scan. Import is lazy: the
    library is not a pipeline dependency."""
    from tradingview_screener import Query, col
    if scan.platform != "tradingview":
        raise ValueError(f"{scan.key} is a {scan.platform} scan")
    sel = ["name", "close", "change", "volume", "market_cap_basic", "price_52_week_low",
           "SMA10", "SMA20", "SMA50", "EMA5", "Volatility.M", "Perf.W", "Perf.1M", "Perf.3M", "Perf.6M",
           "float_shares_outstanding", "average_volume_60d_calc"]
    conds = []
    for c in scan.clauses:
        f = col(c.field)
        if c.op == "==":        conds.append(f == c.value)
        elif c.op == ">":       conds.append(f > c.value)
        elif c.op == ">=":      conds.append(f >= c.value)
        elif c.op == "<":       conds.append(f < c.value)
        elif c.op == "<=":      conds.append(f <= c.value)
        elif c.op == "between": conds.append(f.between(*c.value))
        elif c.op == "isin":    conds.append(f.isin(list(c.value)))
        elif c.op == ">col":    conds.append(f > col(c.value))
        else: raise ValueError(c.op)
    return (Query().set_markets("america").select(*sel).where(*conds)
            .order_by("change", ascending=False).limit(300))


def apply_post(df, scan: Scan):
    """The notebook's pandas post-filters, evaluated verbatim."""
    if df is None or df.empty or not scan.post:
        return df
    import pandas as pd  # noqa
    mask = pd.Series(True, index=df.index)
    for expr in scan.post:
        mask &= df.eval(expr)
    return df[mask].copy()


def run_tv(scan: Scan):
    total, df = to_tv_query(scan).get_scanner_data()
    return total, apply_post(df, scan)


# ------------------------------------------------------- local (partial) mask
# TradingView field -> (universe column, transform) where we CAN express it.
# Anything not here is reported as skipped.
_LOCAL = {
    "market_cap_basic": ("market_cap", None),
    "close": ("close", None),
    "volume": ("volume", None),
    "Perf.W": ("perf_1w", lambda s: s * 100),
    "Perf.1M": ("perf_1m", lambda s: s * 100),
    "Perf.3M": ("perf_3m", lambda s: s * 100),
    "Perf.6M": ("perf_6m", lambda s: s * 100),
    "total_revenue_yoy_growth_fq": ("revenue_growth", lambda s: s * 100),
    "Volatility.M": ("adr_pct", None),            # since 2026-09-04 adr_pct IS mean(H/L-1)*100 over 20
}
_LOCAL_COL = {"SMA20": "sma20_dist", "SMA50": "sma50_dist"}   # close > SMA  <=>  dist > 0


def local_mask(scan: Scan, universe) -> Tuple[Any, List[str]]:
    """Apply what our universe can express. Returns (mask, skipped_clauses).

    The skipped list is the point: `average_volume_60d_calc` (ours is 20d),
    `float_shares_outstanding`, `free_cash_flow_yoy_growth_ttm`, `gap`,
    `relative_volume_10d_calc` (ours is Finviz's 3-month), EPS yoy fq (ours
    is Finviz's 'this year') and every post-filter needing SMA10/EMA5/52w-low
    price have no faithful local counterpart. A run that drops them is NOT
    Jeff's scan and must not be reported as one.
    """
    import pandas as pd
    m = pd.Series(True, index=universe.index)
    skipped: List[str] = []
    for c in scan.clauses:
        if c.field in ("type", "exchange"):
            continue
        if c.op == ">col" and c.value in _LOCAL_COL:
            m &= pd.to_numeric(universe.get(_LOCAL_COL[c.value]), errors="coerce") > 0
            continue
        spec = _LOCAL.get(c.field)
        if spec is None:
            skipped.append(f"{c.field} {c.op} {c.value}")
            continue
        colname, tf = spec
        s = pd.to_numeric(universe.get(colname), errors="coerce")
        if tf: s = tf(s)
        if c.op == ">":       m &= s > c.value
        elif c.op == ">=":    m &= s >= c.value
        elif c.op == "<":     m &= s < c.value
        elif c.op == "<=":    m &= s <= c.value
        elif c.op == "between": m &= s.between(*c.value)
        else: skipped.append(f"{c.field} {c.op} {c.value}")
    # Post-filters. Exactly one family is expressible on our columns: our
    # `low_52w` is close / 52w-low - 1, so "close >= price_52_week_low * K"
    # is "low_52w >= K - 1" with no approximation. SMA10 / EMA5 are not in
    # the universe (ema10 is a different average); those stay skipped.
    for p in scan.post:
        mm = re.fullmatch(r"close >= price_52_week_low \* ([0-9.]+)", p)
        if mm:
            m &= pd.to_numeric(universe.get("low_52w"), errors="coerce") >= float(mm.group(1)) - 1.0
        else:
            skipped.append(f"post: {p}")
    return m.fillna(False), skipped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tv", action="store_true", help="run the 13 TradingView scans live")
    ap.add_argument("--json", help="write hits here")
    ap.add_argument("--specs", action="store_true", help="print all specs and exit")
    a = ap.parse_args(argv)
    if a.specs or not a.tv:
        for k, s in ALL_SCANS.items():
            print(f"\n[{k}] {s.title}  <{s.platform}>  {s.source}")
            for c in s.clauses: print(f"    {c.field} {c.op} {c.value}")
            for p in s.post: print(f"    post: {p}")
        return 0
    out: Dict[str, Any] = {}
    for k, s in TV_SCANS.items():
        try:
            total, df = run_tv(s)
            out[k] = {"tv_total_before_post": int(total), "hits": int(len(df)),
                      "tickers": sorted(df["name"].astype(str).tolist())}
            print(f"{k:<34} TV匹配 {total:>5}  post 后 {len(df):>4}")
        except Exception as e:  # keep the other scans running
            out[k] = {"error": str(e)[:200]}
            print(f"{k:<34} ERROR {e}")
    if a.json:
        with open(a.json, "w") as f: json.dump(out, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
