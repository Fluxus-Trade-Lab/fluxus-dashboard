"""Fetch CFTC TFF (Traders in Financial Futures) weekly positioning for the
risk-state machine's N2 candidates (data/research/risk_state_machine_plan.md).

Source: CFTC's public Socrata API (publicreporting.cftc.gov, dataset
gpe5-46if = TFF Futures Only). No key, no login; one request per contract.

Contracts (by cftc_contract_market_code -- names changed over the years,
codes did not):
    13874A   E-MINI S&P 500 (CME)          2006-06-13 ->  (~1,050 weekly reports)
    1170E1   VIX FUTURES (CBOE)            2006-08-29 ->

Stored raw (positions in contracts + open interest); derived series (net %OI,
rolling ranks) live in the research scripts so the stored file never bakes in
a transform. report_date is the TUESDAY the positions are as of; the public
release is Friday -- consumers must lag before joining to daily prices.

Output: data/reference/cftc/tff_<code>.csv
Usage:  python3 scripts/research/fetch_cftc_tff.py
"""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/reference/cftc"

CONTRACTS = {
    "13874A": "es",       # E-mini S&P 500
    "1170E1": "vix",      # VIX futures
}

FIELDS = ("report_date_as_yyyy_mm_dd,open_interest_all,"
          "asset_mgr_positions_long,asset_mgr_positions_short,"
          "lev_money_positions_long,lev_money_positions_short,"
          "dealer_positions_long_all,dealer_positions_short_all")

URL = ("https://publicreporting.cftc.gov/resource/gpe5-46if.csv"
       "?$select={fields}&$where=cftc_contract_market_code='{code}'"
       "&$order=report_date_as_yyyy_mm_dd&$limit=5000")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    failures = 0
    for code, tag in CONTRACTS.items():
        url = URL.format(fields=FIELDS.replace(",", "%2C"), code=code)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=60).read().decode()
            df = pd.read_csv(io.StringIO(raw), parse_dates=["report_date_as_yyyy_mm_dd"])
            df = df.rename(columns={"report_date_as_yyyy_mm_dd": "report_date"})
            df["report_date"] = df["report_date"].dt.date
            df = df.sort_values("report_date").drop_duplicates("report_date", keep="last")
            path = OUT / f"tff_{code}_{tag}.csv"
            df.to_csv(path, index=False)
            print(f"{code} ({tag}): n={len(df)}  {df['report_date'].iloc[0]} -> {df['report_date'].iloc[-1]}  -> {path.name}")
        except Exception as e:
            print(f"{code} ({tag}): FAILED {str(e)[:100]}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
