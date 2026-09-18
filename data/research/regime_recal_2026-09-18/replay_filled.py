"""Replay state_board + regime.score over breadth_archive with the *_stockbee columns
back-filled from Stockbee's own Market Monitor sheet where our archive has none."""
import sys, io, subprocess, pandas as pd, numpy as np
wt, sbfile, out = sys.argv[1:4]
px = pd.read_csv(sys.argv[4], index_col=0, parse_dates=True) if len(sys.argv) > 4 else None
sys.path.insert(0, wt)
from pipeline.screeners.state_board import state_board
from pipeline.screeners import regime
a = pd.read_csv(io.StringIO(subprocess.run(["git","-C",wt,"show","HEAD:data/history/breadth_archive.csv"],capture_output=True,text=True).stdout))
sb = pd.read_csv(sbfile, parse_dates=["date"]); sb["date"]=sb.date.dt.strftime("%Y-%m-%d")
MAP = {"up_4pct_stockbee":"up4","down_4pct_stockbee":"dn4","ratio_5d_stockbee":"r5","ratio_10d_stockbee":"r10",
       "up_25pct_qtr_stockbee":"up25q","down_25pct_qtr_stockbee":"dn25q",
       "up_13pct_34d_stockbee":"up13_34","down_13pct_34d_stockbee":"dn13_34",
       "up_25pct_month_stockbee":"up25m","down_25pct_month_stockbee":"dn25m",
       "up_50pct_month_stockbee":"up50m","down_50pct_month_stockbee":"dn50m"}
a = a.merge(sb[["date"]+list(MAP.values())], on="date", how="left")
filled = {}
for ours, his in MAP.items():
    if ours not in a: a[ours] = np.nan
    before = a[ours].notna().sum()
    a[ours] = a[ours].fillna(a[his]); filled[ours] = int(a[ours].notna().sum() - before)
a = a.drop(columns=list(MAP.values())).sort_values("date").reset_index(drop=True)
print("filled from Stockbee:", filled, file=sys.stderr)
rows = []
for i in range(len(a)):
    h = None
    if px is not None:
        w = px[px.index <= pd.Timestamp(a.date[i])].tail(60)
        h = {k.lower(): {"candles": [{"c": float(v)} for v in w[k].dropna()]} for k in ("SPY", "QQQ")}
    b = state_board(a.iloc[:i+1], h); s = regime.score(b)
    r = {"date": a.date[i], "spx": a.spx_close[i], "score": s and s["score"], "measured": s and s["measured"]}
    r.update({x["key"]: x["level"] for x in b}); rows.append(r)
pd.DataFrame(rows).to_csv(out, index=False)
