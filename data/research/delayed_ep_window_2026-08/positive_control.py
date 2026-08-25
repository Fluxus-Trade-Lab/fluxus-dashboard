"""Positive control: does the paired test fire when an effect really is there?

Growth Gary 2026-08-25: "没有先验证一个检查能报出阳性,就不该信它的阴性."
Inject a known edge into D1/D2 on the SAME events and confirm P1/P3 flip
significant with the right sign. Also inject nothing (shuffle control) and
confirm it stays null.
"""
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "per_event.csv")
DS = range(1, 16)

def paired(sub, left, right):
    L = sub[[f"D{d}" for d in left]].mean(axis=1)
    R = sub[[f"D{d}" for d in right]].mean(axis=1)
    d = (L - R).dropna()
    return d.median(), wilcoxon(d, alternative="two-sided")[1]

print(f"{'injected edge on D1,D2':>24} {'P1 median':>10} {'P1 p':>9} {'P3 median':>10} {'P3 p':>9}")
for edge in (0.0, 0.005, 0.01, 0.02, 0.03):
    s = df.copy()
    for D in (1, 2):
        s[f"D{D}"] = s[f"D{D}"] + edge
    m1, p1 = paired(s, (1, 2), (3,))
    m3, p3 = paired(s, (1, 2), range(3, 16))
    print(f"{edge*100:>23.1f}% {m1*100:>9.2f}% {p1:>9.4f} {m3*100:>9.2f}% {p3:>9.4f}")

rng = np.random.default_rng(20260826)
s = df.copy()
vals = s[[f"D{d}" for d in DS]].to_numpy().copy()
for i in range(len(vals)):
    rng.shuffle(vals[i])                      # destroy any D-ordering, keep each event's own returns
s[[f"D{d}" for d in DS]] = vals
m1, p1 = paired(s, (1, 2), (3,)); m3, p3 = paired(s, (1, 2), range(3, 16))
print(f"{'shuffled D order (null)':>24} {m1*100:>9.2f}% {p1:>9.4f} {m3*100:>9.2f}% {p3:>9.4f}")
