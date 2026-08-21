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
          "stale_ts_d", "stale_nhnl_d", "stale_oas_d", "stale_gex_d"]


def _tv_refresh(symbols: list[tuple[str, str]]) -> None:
    """Best-effort refresh of TV-sourced CSVs; silence on any failure."""
    try:
        from tvDatafeed import Interval, TvDatafeed
        tv = TvDatafeed()
        for sym, ex in symbols:
            try:
                df = tv.get_hist(symbol=sym, exchange=ex, interval=Interval.in_daily, n_bars=20000)
                if df is None or len(df) == 0:
                    continue
                out = df[["close"]].copy()
                out.index = out.index.normalize().date
                out.index.name = "date"
                out.to_csv(TVDIR / f"{ex}_{sym.replace('.', '_')}.csv")
            except Exception:
                continue
    except Exception:
        return


def _dix_refresh() -> None:
    try:
        import requests
        r = requests.get("https://squeezemetrics.com/monitor/static/DIX.csv", timeout=45)
        if r.ok and r.text.startswith("date,price,dix,gex"):
            DIXCSV.write_text(r.text)
    except Exception:
        return


def _series(path: Path, col: str = "close") -> Optional[pd.Series]:
    if not path.exists():
        return None
    s = pd.read_csv(path, parse_dates=["date"]).set_index("date")[col]
    return s[~s.index.duplicated(keep="last")].dropna()


def _staleness(dim_date, ledger_date) -> int:
    return int((pd.Timestamp(ledger_date) - pd.Timestamp(dim_date)).days)


def build_row(refresh: bool = True) -> Optional[dict]:
    cr = json.loads(CR_JSON.read_text())
    today = cr["today"]
    date = today["date"]
    ts = (cr.get("ts_dimension") or {}).get("today") or {}

    if refresh:
        _tv_refresh([("HIGN", "INDEX"), ("LOWN", "INDEX"), ("BAMLH0A0HYM2", "FRED")])
        _dix_refresh()

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

    lamps = [row[k] for k in ("lamp_ts", "lamp_nhnl", "lamp_credit", "lamp_gex")]
    avail = [x for x in lamps if x != ""]
    row["lamps_on"] = sum(avail)
    row["lamps_available"] = len(avail)
    return row


def append(row: dict) -> bool:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if LEDGER.exists():
        with open(LEDGER) as f:
            dates = {r["date"] for r in csv.DictReader(f)}
        if row["date"] in dates:
            return False
    new = not LEDGER.exists()
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return True


def main() -> int:
    refresh = "--no-refresh" not in sys.argv
    row = build_row(refresh=refresh)
    if row is None:
        print("regime_ledger: no correction_risk.json -- nothing to log")
        return 1
    if append(row):
        print(f"regime_ledger: {row['date']}  lamps {row['lamps_on']}/{row['lamps_available']} "
              f"(ts={row['lamp_ts']} nhnl={row['lamp_nhnl']} credit={row['lamp_credit']} gex={row['lamp_gex']})  "
              f"prob_3d={row['prob_3d']}  spx={row['spx_close']}")
    else:
        print(f"regime_ledger: {row['date']} already logged -- skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
