"""Rebuild a regime_ledger row as of DATE from committed files only (no refetch).
correction_risk.json from the commit that published DATE; series truncated to what
existed at run time: TV/TICK/DIX <= DATE, FRED < DATE (FRED posts a day late)."""
import json, subprocess, sys, tempfile, csv, io
from pathlib import Path
import pandas as pd
REPO = Path("/Users/taolezhu/Documents/AI-Trading-System")
sys.path.insert(0, str(REPO))
from pipeline.risk import regime_ledger as L

def show(rev, p):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{p}"], capture_output=True, text=True, check=True).stdout

def rebuild(date, cr_rev, fred_lag=True, series_rev="origin/main"):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "tv").mkdir()
    cr = tmp / "cr.json"; cr.write_text(show(cr_rev, "data/output/correction_risk.json"))
    for name in ["INDEX_HIGN", "INDEX_LOWN", "FRED_BAMLH0A0HYM2", "USI_TICK_hlc"]:
        df = pd.read_csv(io.StringIO(show(series_rev, f"data/reference/breadth_tv/{name}.csv")), dtype=str)
        cut = (df["date"] < date) if (name.startswith("FRED") and fred_lag) else (df["date"] <= date)
        df[cut].to_csv(tmp / "tv" / f"{name}.csv", index=False)
    dix = pd.read_csv(io.StringIO(show(series_rev, "SqueezeMetrics/DIX.csv")), dtype=str)
    dix[dix["date"] <= date].to_csv(tmp / "DIX.csv", index=False)
    L.CR_JSON, L.TVDIR, L.DIXCSV = cr, tmp / "tv", tmp / "DIX.csv"
    row, _ = L.build_row(refresh=False)
    return row

def fmt(row):
    b = io.StringIO(); w = csv.DictWriter(b, fieldnames=L.FIELDS, lineterminator="\n"); w.writerow(row); return b.getvalue().strip()

if __name__ == "__main__":
    ledger = {l.split(",")[0]: l for l in show("origin/main", "data/history/regime_ledger.csv").splitlines()}
    for date, rev in [("2026-09-15", "88295474"), ("2026-09-17", "fa77725b"), ("2026-09-16", "27883a92")]:
        r = fmt(rebuild(date, rev))
        truth = ledger.get(date)
        print(date, "MATCH" if r == truth else "DIFF")
        print("  rebuilt:", r)
        if truth: print("  ledger :", truth)
