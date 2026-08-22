"""Regime ledger -- nightly forward log of the risk-state machine.

One row per trading date: the correction-risk 3d cell (VIX quintile x 200dma
x VIX-TS state) plus four confluence LAMPS, each the danger pole of a cut that
passed the E1 house checks (data/research/turin_e1_results.json):

    lamp_ts     VIX/VIX3M 3EMA > 1.0 (backwardation)            E1 rate 32.1%
    lamp_nhnl   NYSE NHNL ratio 10d EMA < 0.30 (washout zone)   E1 rate 37.2%
    lamp_credit HY OAS trailing-252d pct rank >= 0.8 (Q5 wide)  E1 rate 34.8%
    lamp_gex    SqueezeMetrics GEX/px^2 252d pct rank < 0.2     E1 rate 21.2%

Lamps are counted, never weighted or averaged (design principle #6, see
data/research/risk_state_machine_plan.md P3). Output language downstream is a
position-budget band, never a direction call. Forward ledger discipline: 6-12
months of rows is the entry ticket for any signalisation talk -- until then
this file is an internal record only (project parked; frontend NOT wired).

Sources & failure domains (each dimension degrades to absence + staleness):
  - main reading: data/output/correction_risk.json (written moments earlier in
    the same nightly run)
  - NHNL / OAS: data/reference/breadth_tv/*.csv, refreshed in-process via
    tvdatafeed when importable (anonymous websocket); otherwise used as-is
  - GEX: SqueezeMetrics/DIX.csv, refreshed via the public CSV endpoint when
    reachable; otherwise used as-is

Idempotent: appending is skipped when the ledger already has the date.
Dates come from the data itself, never the host clock (feedback: trading
dates are ET; pipeline.marketcal governs anything clock-like).

Usage:  python3 -m pipeline.risk.regime_ledger [--no-refresh]
Output: data/history/regime_ledger.csv (append)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CR_JSON = ROOT / "data/output/correction_risk.json"
TVDIR = ROOT / "data/reference/breadth_tv"
DIXCSV = ROOT / "SqueezeMetrics/DIX.csv"
LEDGER = ROOT / "data/history/regime_ledger.csv"

FIELDS = ["date", "spx_close", "vix", "vix_q", "above200", "ts_ema", "ts_state",
          "prob_3d", "n_cell_3d", "prob_2d",
          "nhnl_ratio", "nhnl_state", "oas", "oas_rank252", "gexn_rank252",
          "lamp_ts", "lamp_nhnl", "lamp_credit", "lamp_gex",
          "lamps_on", "lamps_available",
          "stale_ts_d", "stale_nhnl_d", "stale_oas_d", "stale_gex_d",
          # LBR TICK cycle readings (Andy 2026-08-22): recorded, never a lamp
          # until it earns one -- forward-ledger discipline. SMA15 of NYSE
          # TICK daily H/C/L (indicators/fluxus-lbr-tick-cycle.txt); the
          # spread rank is the feed-agnostic zone measure (ChartsLector's
          # good idea; his TICK.NY feed choice undershoots Linda's, ours is
          # closer -- see the .txt comparison).
          "tick_ma_hi", "tick_ma_cl", "tick_ma_lo", "tick_spread_rank252",
          "tick_zone", "stale_tick_d"]

TICK_CSV_NAME = "USI_TICK_hlc.csv"
TICK_N = 15
TICK_UP, TICK_DN = 650.0, -650.0  # TV-feed calibrated level zones


def _tv_refresh(symbols: list[tuple[str, str]]) -> list[str]:
    """Refresh TV-sourced CSVs. Failures are RETURNED, never swallowed
    (Andy 2026-08-21: dependency problems must be reported); the caller
    degrades to the committed CSVs and surfaces the errors."""
    errors: list[str] = []
    try:
        from tvDatafeed import Interval, TvDatafeed
    except Exception as e:
        return [f"tvdatafeed import failed ({e!r}) -- NHNL/credit lamps running on committed CSVs"]
    try:
        tv = TvDatafeed()
    except Exception as e:
        return [f"tvdatafeed connect failed ({e!r})"]
    for sym, ex in symbols:
        try:
            df = tv.get_hist(symbol=sym, exchange=ex, interval=Interval.in_daily, n_bars=20000)
            if df is None or len(df) == 0:
                errors.append(f"tv refresh {ex}:{sym}: empty response")
                continue
            out = df[["close"]].copy()
            out.index = out.index.normalize().date
            out.index.name = "date"
            out.to_csv(TVDIR / f"{ex}_{sym.replace('.', '_')}.csv")
        except Exception as e:
            errors.append(f"tv refresh {ex}:{sym}: {str(e)[:80]}")
    return errors


def _tick_refresh() -> list[str]:
    """Rebuild daily TICK H/L/C from hourly bars (TV's TICK daily is
    close-only) and overwrite the CSV. Errors returned, not swallowed."""
    try:
        from tvDatafeed import Interval, TvDatafeed
    except Exception as e:
        return [f"tick refresh: tvdatafeed import failed ({e!r})"]
    try:
        tv = TvDatafeed()
        h = tv.get_hist(symbol="TICK", exchange="USI", interval=Interval.in_1_hour, n_bars=5000)
        if h is None or len(h) == 0:
            return ["tick refresh: empty response"]
        h = h.copy()
        h["day"] = h.index.normalize()
        daily = h.groupby("day").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
        daily.index = daily.index.date
        daily.index.name = "date"
        # feed-tz stubs land on weekends (Friday's last bar after midnight);
        # a stub day would pollute the SMA, so only real sessions survive
        from pipeline.marketcal import is_trading_day
        daily = daily[[is_trading_day(d) for d in daily.index]]
        daily.to_csv(TVDIR / TICK_CSV_NAME)
        return []
    except Exception as e:
        return [f"tick refresh: {str(e)[:80]}"]


def _dix_refresh() -> list[str]:
    try:
        import requests
        r = requests.get("https://squeezemetrics.com/monitor/static/DIX.csv", timeout=45)
        if r.ok and r.text.startswith("date,price,dix,gex"):
            DIXCSV.write_text(r.text)
            return []
        return [f"DIX refresh: unexpected response (status {r.status_code})"]
    except Exception as e:
        return [f"DIX refresh: {str(e)[:80]}"]


def report_problems(row: dict, refresh_errors: list[str]) -> list[str]:
    """Everything a human should see: refresh failures + lamps lost to
    staleness. Printed as GitHub Actions warning annotations when in CI."""
    import os
    problems = list(refresh_errors)
    for dim, key in (("ts", "stale_ts_d"), ("nhnl", "stale_nhnl_d"),
                     ("credit", "stale_oas_d"), ("gex", "stale_gex_d"),
                     ("tick", "stale_tick_d")):
        v = row.get(key)
        if v == "":
            problems.append(f"lamp_{dim}: data source absent")
        elif isinstance(v, int) and v > 7:
            problems.append(f"lamp_{dim}: stale {v}d (>7) -- lamp marked absent")
    for p in problems:
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning title=regime_ledger::{p}")
        else:
            print(f"regime_ledger WARNING: {p}", file=sys.stderr)
    return problems


def _series(path: Path, col: str = "close") -> Optional[pd.Series]:
    if not path.exists():
        return None
    s = pd.read_csv(path, parse_dates=["date"]).set_index("date")[col]
    return s[~s.index.duplicated(keep="last")].dropna()


def _staleness(dim_date, ledger_date) -> int:
    # a dimension refreshed after the ledger date is simply fresh, never negative
    return max(0, int((pd.Timestamp(ledger_date) - pd.Timestamp(dim_date)).days))


def build_row(refresh: bool = True) -> tuple[Optional[dict], list[str]]:
    cr = json.loads(CR_JSON.read_text())
    today = cr["today"]
    date = today["date"]
    ts = (cr.get("ts_dimension") or {}).get("today") or {}

    refresh_errors: list[str] = []
    if refresh:
        refresh_errors += _tv_refresh([("HIGN", "INDEX"), ("LOWN", "INDEX"), ("BAMLH0A0HYM2", "FRED")])
        refresh_errors += _tick_refresh()
        refresh_errors += _dix_refresh()

    row: dict = {
        "date": date, "spx_close": today.get("spx_close"),
        "vix": today["vix"], "vix_q": today["vix_quintile"],
        "above200": int(bool(today["above_200dma"])),
        "ts_ema": ts.get("ts_ema"), "ts_state": ts.get("ts_state"),
        "prob_3d": ts.get("prob_3d"), "n_cell_3d": ts.get("n_cell_3d"),
        "prob_2d": today.get("prob"),
        "stale_ts_d": _staleness(ts["date"], date) if ts.get("date") else "",
    }
    row["lamp_ts"] = ("" if ts.get("ts_state") is None
                      else int(ts["ts_state"] == 3 and row["stale_ts_d"] != "" and row["stale_ts_d"] <= 7))

    hi, lo = _series(TVDIR / "INDEX_HIGN.csv"), _series(TVDIR / "INDEX_LOWN.csv")
    if hi is not None and lo is not None:
        r = (hi / (hi + lo)).dropna().ewm(span=10).mean()
        row["nhnl_ratio"] = round(float(r.iloc[-1]), 4)
        row["nhnl_state"] = 1 if r.iloc[-1] < 0.30 else (3 if r.iloc[-1] > 0.85 else 2)
        row["stale_nhnl_d"] = _staleness(r.index[-1], date)
        row["lamp_nhnl"] = int(row["nhnl_state"] == 1 and row["stale_nhnl_d"] <= 7)
    else:
        row.update({"nhnl_ratio": "", "nhnl_state": "", "stale_nhnl_d": "", "lamp_nhnl": ""})

    oas = _series(TVDIR / "FRED_BAMLH0A0HYM2.csv")
    if oas is not None and len(oas) > 252:
        w = oas.tail(252)
        rank = float((w <= oas.iloc[-1]).mean())
        row["oas"] = round(float(oas.iloc[-1]), 2)
        row["oas_rank252"] = round(rank, 3)
        row["stale_oas_d"] = _staleness(oas.index[-1], date)
        row["lamp_credit"] = int(rank >= 0.8 and row["stale_oas_d"] <= 7)
    else:
        row.update({"oas": "", "oas_rank252": "", "stale_oas_d": "", "lamp_credit": ""})

    if DIXCSV.exists():
        sm = pd.read_csv(DIXCSV, parse_dates=["date"]).set_index("date")
        gexn = (sm["gex"] / (sm["price"] ** 2)).dropna()
        if len(gexn) > 252:
            rank = float((gexn.tail(252) <= gexn.iloc[-1]).mean())
            row["gexn_rank252"] = round(rank, 3)
            row["stale_gex_d"] = _staleness(gexn.index[-1], date)
            row["lamp_gex"] = int(rank < 0.2 and row["stale_gex_d"] <= 7)
        else:
            row.update({"gexn_rank252": "", "stale_gex_d": "", "lamp_gex": ""})
    else:
        row.update({"gexn_rank252": "", "stale_gex_d": "", "lamp_gex": ""})

    tick_path = TVDIR / TICK_CSV_NAME
    if tick_path.exists():
        t = pd.read_csv(tick_path, parse_dates=["date"]).set_index("date").sort_index()
        if len(t) > 252 + TICK_N:
            m_hi = t["high"].rolling(TICK_N).mean()
            m_lo = t["low"].rolling(TICK_N).mean()
            m_cl = t["close"].rolling(TICK_N).mean()
            spread = m_hi - m_lo
            w = spread.dropna().tail(252)
            row["tick_ma_hi"] = round(float(m_hi.iloc[-1]), 1)
            row["tick_ma_cl"] = round(float(m_cl.iloc[-1]), 1)
            row["tick_ma_lo"] = round(float(m_lo.iloc[-1]), 1)
            row["tick_spread_rank252"] = round(float((w <= spread.iloc[-1]).mean()), 3)
            row["tick_zone"] = ("sell" if m_hi.iloc[-1] >= TICK_UP
                                else "buy" if m_lo.iloc[-1] <= TICK_DN else "neutral")
            row["stale_tick_d"] = _staleness(t.index[-1], date)
        else:
            row.update({"tick_ma_hi": "", "tick_ma_cl": "", "tick_ma_lo": "",
                        "tick_spread_rank252": "", "tick_zone": "", "stale_tick_d": ""})
    else:
        row.update({"tick_ma_hi": "", "tick_ma_cl": "", "tick_ma_lo": "",
                    "tick_spread_rank252": "", "tick_zone": "", "stale_tick_d": ""})

    lamps = [row[k] for k in ("lamp_ts", "lamp_nhnl", "lamp_credit", "lamp_gex")]
    avail = [x for x in lamps if x != ""]
    row["lamps_on"] = sum(avail)
    row["lamps_available"] = len(avail)
    return row, refresh_errors


TICK_CYCLE_JSON = ROOT / "data/output/tick_cycle.json"

# 17-year zone-test evidence (C_long variant, our construction on the long
# TICK.NY feed; scripts/research/lbr_tick_zone_test.py 2026-08-22). Baked as
# constants: the page prints the account, it never recomputes it.
_EVIDENCE = {"window_years": 17, "n_sell_entries": 71,
             "sell_fwd21_med": 0.011, "base_fwd21_med": 0.0158,
             "sell_p_dd5": 0.099, "base_p_dd5": 0.154}


def write_tick_cycle_json(ledger_date: str) -> Optional[dict]:
    """Morning page 1 (market layer) reading of the LBR TICK cycle
    (Andy 2026-08-22). Band by spread rank -- the feed-agnostic measure:
    <=0.10 grind (red, compressed band), >=0.90 washout (green), else
    neutral. The reading sentence is a calculated account, page-copy rules
    apply (trading content only). Spec: indicators/fluxus-lbr-tick-cycle.txt."""
    path = TVDIR / TICK_CSV_NAME
    if not path.exists():
        return None
    t = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    if len(t) < 252 + TICK_N:
        return None
    m_hi = t["high"].rolling(TICK_N).mean()
    m_lo = t["low"].rolling(TICK_N).mean()
    m_cl = t["close"].rolling(TICK_N).mean()
    spread = (m_hi - m_lo).dropna()
    rank = spread.rolling(252).apply(lambda w: (w <= w.iloc[-1]).mean(), raw=False).dropna()

    def band_of(r: float) -> str:
        return "grind" if r <= 0.10 else ("washout" if r >= 0.90 else "neutral")

    bands = rank.map(band_of)
    cur = bands.iloc[-1]
    since = bands.index[-1]
    for d in reversed(bands.index):
        if bands.loc[d] != cur:
            break
        since = d

    r = float(rank.iloc[-1])
    if cur == "grind":
        reading = (f"红带磨市：TICK 高低带收缩到一年 {r:.0%} 分位（{since.date()} 入带）。"
                   f"17 年账本：入带后 21 日收益中位约为基准一半（+1.1% vs +1.6%），"
                   f"5% 回撤概率反而低于基准（9.9% vs 15.4%）——磨，不是崩。")
    elif cur == "washout":
        reading = (f"绿带 washout：TICK 高低带张到一年 {r:.0%} 分位（{since.date()} 入带）。"
                   f"17 年账本：入带后前瞻收益高于基准（fwd21 +2.6% vs +1.6%），历来是买入机会带。")
    else:
        reading = f"TICK 高低带处于中性区（一年 {r:.0%} 分位），无带内读数。"

    out = {"as_of": str(t.index[-1].date()),
           "source": "USI:TICK hourly-rebuilt daily H/L, SMA15; spec indicators/fluxus-lbr-tick-cycle.txt",
           "ma_high": round(float(m_hi.iloc[-1]), 1),
           "ma_close": round(float(m_cl.iloc[-1]), 1),
           "ma_low": round(float(m_lo.iloc[-1]), 1),
           "spread_rank252": round(r, 3),
           "band": cur, "band_since": str(since.date()),
           "reading": reading,
           "evidence": _EVIDENCE,
           "stale_days": _staleness(t.index[-1], ledger_date),
           "note": "band 语义: grind=价差收缩(自满磨市, 收益变薄非回撤警报) / washout=价差张开(洗盘买入带); timing 语境读数, 不是尾部风险维度 (E1 NULL, 不设灯)"}
    TICK_CYCLE_JSON.parent.mkdir(parents=True, exist_ok=True)
    TICK_CYCLE_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def append(row: dict) -> bool:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if LEDGER.exists():
        with open(LEDGER) as f:
            reader = csv.DictReader(f)
            old_fields = reader.fieldnames or []
            existing = list(reader)
        if row["date"] in {r["date"] for r in existing}:
            return False
        if old_fields != FIELDS:
            # schema grew (e.g. tick columns 2026-08-22): rewrite once, old
            # rows keep "" in the new columns -- append-only in rows, not
            # in columns. Never drops a column that has data.
            missing_old = [c for c in old_fields if c not in FIELDS]
            if missing_old:
                raise RuntimeError(f"regime_ledger: refusing to drop columns {missing_old}")
            with open(LEDGER, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                for r in existing:
                    w.writerow({k: r.get(k, "") for k in FIELDS})
    new = not LEDGER.exists()
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return True


def main() -> int:
    refresh = "--no-refresh" not in sys.argv
    row, refresh_errors = build_row(refresh=refresh)
    if row is None:
        print("regime_ledger: no correction_risk.json -- nothing to log")
        return 1
    report_problems(row, refresh_errors)
    if append(row):
        print(f"regime_ledger: {row['date']}  lamps {row['lamps_on']}/{row['lamps_available']} "
              f"(ts={row['lamp_ts']} nhnl={row['lamp_nhnl']} credit={row['lamp_credit']} gex={row['lamp_gex']})  "
              f"prob_3d={row['prob_3d']}  spx={row['spx_close']}")
    else:
        print(f"regime_ledger: {row['date']} already logged -- skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
