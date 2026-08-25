"""How often does the paired test cry wolf on data with no D-effect by construction?

The single shuffle in positive_control.py returned p=0.0419 for P3 -- either a
1-in-20 draw or a miscalibrated test. 500 reps tells us which. Each rep keeps
every event's own 15 returns and only shuffles WHICH D they are attached to,
so any D-block difference that survives is pure test artifact.
"""
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "per_event.csv")
DS = list(range(1, 16))
COLS = [f"D{d}" for d in DS]
BASE = df[COLS].to_numpy().copy()
REPS = 500
rng = np.random.default_rng(20260826)

BLOCKS = {"P1 D1,2 vs D3": ((1, 2), (3,)),
          "P2 D1-4 vs D5-15": (tuple(range(1, 5)), tuple(range(5, 16))),
          "P3 D1,2 vs D3-15": ((1, 2), tuple(range(3, 16)))}
hits = {k: 0 for k in BLOCKS}
meds = {k: [] for k in BLOCKS}

for _ in range(REPS):
    v = BASE.copy()
    for i in range(len(v)):
        rng.shuffle(v[i])
    s = pd.DataFrame(v, columns=COLS)
    for name, (L, R) in BLOCKS.items():
        d = (s[[f"D{x}" for x in L]].mean(axis=1) - s[[f"D{x}" for x in R]].mean(axis=1)).dropna()
        p = wilcoxon(d, alternative="two-sided")[1]
        hits[name] += p < 0.05
        meds[name].append(d.median())

print(f"{REPS} shuffles, nominal alpha = 5%")
print(f"{'test':>18} {'false-positive rate':>20} {'median of medians':>18}")
for k in BLOCKS:
    print(f"{k:>18} {hits[k]/REPS*100:>19.1f}% {np.median(meds[k])*100:>17.2f}%")
