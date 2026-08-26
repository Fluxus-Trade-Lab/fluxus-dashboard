"""Pull daily OHLC for every ticker_events name. Writes close.csv/high.csv/low.csv.

Only bars up to the last completed session (2026-08-25) are used downstream;
we pull through 2026-08-26 and drop the incomplete bar in measure.py.
"""
import sys, time
from pathlib import Path
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
START, END = "2026-01-02", "2026-08-27"

ev = pd.read_csv(HERE / "../../history/ticker_events.csv")
tickers = sorted(ev.ticker.dropna().unique().tolist())
tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
print(f"{len(tickers)} tickers", flush=True)
tickers = ["SPY"] + [t for t in tickers if t != "SPY"]

CH = 200
frames = {"Close": [], "High": [], "Low": []}
for i in range(0, len(tickers), CH):
    chunk = tickers[i:i + CH]
    for attempt in range(3):
        try:
            d = yf.download(chunk, start=START, end=END, auto_adjust=False,
                            progress=False, threads=True, group_by="column")
            break
        except Exception as e:                                    # noqa: BLE001
            print(f"  chunk {i} attempt {attempt}: {e}", flush=True)
            time.sleep(5)
    else:
        print(f"  chunk {i} FAILED", flush=True); continue
    for field in frames:
        if field in d.columns.get_level_values(0):
            frames[field].append(d[field])
    print(f"  {i + len(chunk)}/{len(tickers)}", flush=True)
    time.sleep(1)

for field, parts in frames.items():
    out = pd.concat(parts, axis=1).sort_index()
    out = out.loc[:, ~out.columns.duplicated()]
    out.to_csv(HERE / f"{field.lower()}.csv")
    print(field, out.shape, flush=True)
