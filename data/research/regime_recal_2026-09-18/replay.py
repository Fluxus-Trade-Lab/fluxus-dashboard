import sys, pandas as pd, subprocess, io
wt, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, wt)
from pipeline.screeners.state_board import state_board
from pipeline.screeners import regime
arch = pd.read_csv(io.StringIO(subprocess.run(["git","-C","/Users/taolezhu/Documents/AI-Trading-System","show","origin/main:data/history/breadth_archive.csv"],capture_output=True,text=True).stdout))
arch = arch.sort_values("date").reset_index(drop=True)
rows=[]
for i in range(len(arch)):
    b = state_board(arch.iloc[:i+1], None)
    s = regime.score(b)
    th = next((r["level"] for r in b if r["key"]=="thrust"), None)
    rows.append({"date":arch.date[i],"score":s and s["score"],"measured":s and s["measured"],"thrust":th,"spx":arch.spx_close[i]})
pd.DataFrame(rows).to_csv(out,index=False)
