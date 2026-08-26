"""Gate 0: does my reconstructed adr_pct measure the same thing production does?

Production (run_all.py:344): adr_pct = atr / close * 100, atr = Finviz ATR14.
Here: Wilder ATR14 from yfinance OHLC. If these are not the same quantity the
whole study is measuring something else, so this runs BEFORE anything else and
the pre-registration voids the round at spearman < 0.95.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
close = pd.read_csv(HERE / "close.csv", index_col=0, parse_dates=True)
high  = pd.read_csv(HERE / "high.csv",  index_col=0, parse_dates=True)
low   = pd.read_csv(HERE / "low.csv",   index_col=0, parse_dates=True)

# drop any bar after the last completed session
LAST = pd.Timestamp("2026-08-25")
close, high, low = close.loc[:LAST], high.loc[:LAST], low.loc[:LAST]

prev = close.shift(1)
tr = pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()]).groupby(level=0).max()
tr = tr.reindex(close.index)
atr14 = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
adr = atr14 / close * 100.0
adr.to_csv(HERE / "adr_pct_recon.csv")

u = json.load(open(HERE / "../../output/universe.json"))
prod = {r["ticker"]: r.get("adr_pct") for r in u["rows"] if r.get("adr_pct") is not None}
mine = adr.loc[LAST]

pairs = [(t, float(v), float(mine[t])) for t, v in prod.items()
         if t in mine.index and pd.notna(mine[t])]
p = np.array([x[1] for x in pairs]); m = np.array([x[2] for x in pairs])
rho, pv = spearmanr(p, m)
mae = float(np.median(np.abs(p - m)))
# what matters operationally: does the 3.5 line put names on the same side?
agree = float(np.mean((p >= 3.5) == (m >= 3.5)))
out = {"n": len(pairs), "spearman": round(float(rho), 4), "p": float(pv),
       "median_abs_err_pp": round(mae, 4),
       "median_prod": round(float(np.median(p)), 3), "median_mine": round(float(np.median(m)), 3),
       "side_of_3.5_agreement": round(agree, 4),
       "verdict": "PASS" if rho >= 0.95 else "VOID (prereg: spearman < 0.95 voids the round)"}
print(json.dumps(out, indent=1))
json.dump(out, open(HERE / "calibration.json", "w"), indent=1)
