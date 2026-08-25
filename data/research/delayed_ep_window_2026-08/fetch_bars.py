"""Pull daily bars for every episodic_pivot ticker + SPY into a local parquet-ish cache.

Read-only w.r.t. the repo: writes one CSV under this research folder so the
measurement script never needs the network twice. Nothing here touches
data/output or data/history.
"""
import csv, sys, time, warnings
from pathlib import Path
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "bars.csv"

rows = [r for r in csv.DictReader(open(ROOT / "data/history/ticker_events.csv"))
        if r["screener"] == "episodic_pivot"]
tickers = sorted({r["ticker"] for r in rows}) + ["SPY"]
print(f"{len(rows)} EP events, {len(tickers)} symbols (incl SPY)")

frames = []
CH = 50
for i in range(0, len(tickers), CH):
    chunk = tickers[i:i + CH]
    d = yf.download(chunk, start="2026-02-20", end="2026-08-26",
                    progress=False, auto_adjust=False, threads=True)
    if d.empty:
        print("  empty chunk", i); continue
    cl = d["Close"]
    if isinstance(cl, pd.Series):
        cl = cl.to_frame(chunk[0])
    frames.append(cl)
    print(f"  {i//CH+1}/{(len(tickers)+CH-1)//CH} -> {cl.shape}")
    time.sleep(1.5)

close = pd.concat(frames, axis=1)
close = close.loc[:, ~close.columns.duplicated()]
# last completed session is 2026-08-24; 08-25 is an intraday quote -> drop it
close = close[close.index <= "2026-08-24"]
close.index.name = "date"
close.to_csv(OUT)
print("wrote", OUT, close.shape, "last bar", close.index.max().date())
