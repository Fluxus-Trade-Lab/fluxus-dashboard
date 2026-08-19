"""Replay: would I7 have caught the change_pct incident? Reproducible, offline.

Freezes an I4/I7 registry on ticker_events sessions strictly BEFORE the
Finviz `Change` -> `Change %` rename (2026-08-07), then walks every session
from the rename to the newest and reports which reliable series wrote zero
rows -- next to what the old total-row-count band (0.30x/3.0x) said about
the same day, and what breadth counted for that session.

    python data/research/i4_calibration_2026-08/replay.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pipeline.tools.calibrate_i4 import calibrate  # noqa: E402

CUT = "2026-08-07"           # the day the header was renamed
HIST = Path("data/history")

reg = calibrate(HIST, until=CUT)["archives"]["ticker_events.csv"]
reliable = sorted(k for k, v in reg["series"].items() if v["kind"] == "reliable")
print(f"registry frozen on sessions < {CUT}: {reg['sessions']} sessions")
print(f"reliable series: {reliable}\n")

te = pd.read_csv(HIST / "ticker_events.csv", dtype=str)
te["date"] = te["date"].astype(str)
piv = te.pivot_table(index="date", columns="screener", values="ticker", aggfunc="count").sort_index()
tot = piv.sum(axis=1)
br = pd.read_csv(HIST / "breadth_archive.csv").set_index("date")

print(f"{'session':12s} {'rows':>6s} {'x med':>6s} {'old gate':>9s}  {'up4%':>6s}  I7")
for d in piv.index[piv.index >= CUT]:
    prev = tot.loc[tot.index < d].tail(20)
    med = prev.median() if len(prev) >= 5 else float("nan")
    ratio = tot[d] / med if med == med and med else float("nan")
    old = "silent" if 0.30 < ratio < 3.0 else "FIRES"
    dead = [s for s in reliable if s not in piv.columns or piv.loc[d, s] != piv.loc[d, s]]
    up4 = int(br.up_4pct[d]) if d in br.index else -1
    print(f"{d:12s} {int(tot[d]):6d} {ratio:6.2f} {old:>9s}  {up4:6d}  "
          + ("clean" if not dead else "VIOLATION: " + ", ".join(dead)))
