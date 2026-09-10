#!/usr/bin/env python3
"""Complete the JGBanks midterm verification (Steve did replication; this does inference).

口径:JGBanks 两窗(选举日→+12m;11/1→次年6/30)照复刻;另加行业标准窗
Stock Trader's Almanac "Sweet Spot"(中期年 Q4 起点=10/1→次年6/30)。
检验:排列检验(在全部年份里随机抽同样本量,问「全正」和「均值这么高」有多罕见),
不是符号检验——「全正」是事后从多窗口/多起点里挑出来的统计量(Steve 的坑单 #2)。
先算最小可能 p:100k 次排列 → 1e-5;选择面 ≈ 4 个周期位 × 3 个窗 = ×12。
"""
import warnings; warnings.filterwarnings("ignore")
import random, statistics as st
import yfinance as yf
import pandas as pd
import datetime as dt

df = yf.download("^GSPC", start="1900-01-01", end="2026-09-11", progress=False, auto_adjust=False)
c = df["Close"]; c = c[c.columns[0]] if hasattr(c, "columns") else c
c = c.dropna()
def px_on_or_after(d):
    seg = c[c.index >= pd.Timestamp(d)]
    return (float(seg.iloc[0]), seg.index[0]) if len(seg) else (None, None)

def election_day(y):
    d = dt.date(y, 11, 1)
    while d.weekday() != 0: d += dt.timedelta(days=1)   # first Monday
    return d + dt.timedelta(days=1)                     # Tuesday after

first_year = c.index[0].year + 1
rows = []
for y in range(first_year, 2026):
    ed = election_day(y)
    a0, _ = px_on_or_after(ed); a1, _ = px_on_or_after(ed + dt.timedelta(days=365))
    b0, _ = px_on_or_after(dt.date(y,11,1)); b1, _ = px_on_or_after(dt.date(y+1,6,30))
    s0, _ = px_on_or_after(dt.date(y,10,1)); s1, _ = px_on_or_after(dt.date(y+1,6,30))
    if None in (a0,a1,b0,b1,s0,s1): continue
    rows.append({"y": y, "cyc": y % 4,           # 2 = midterm (e.g. 2022%4==2)
                 "A": a1/a0-1, "B": b1/b0-1, "S": s1/s0-1})
U = pd.DataFrame(rows)
mid = U[U.cyc == 2]
print(f"universe: {U.y.min()}–{U.y.max()}  n={len(U)} 年;中期年 n={len(mid)} ({list(mid.y)[:3]}…{list(mid.y)[-1:]})")

def stats(g, w):
    r = g[w]; return len(r), (r>0).mean()*100, r.mean()*100

print("\n== 周期位对照(选择面的另一半)==")
NAME = {0:"大选年",1:"大选后",2:"中期年",3:"预选年"}
for w,lab in (("A","选举日→+12m"),("B","11/1→6/30"),("S","Almanac 10/1→6/30")):
    line = []
    for cyc in (0,1,2,3):
        n,pos,mu = stats(U[U.cyc==cyc], w)
        line.append(f"{NAME[cyc]} {pos:.0f}%正/均{mu:+.1f}%")
    print(f"  {lab:22s} " + " · ".join(line))

print("\n== 排列检验(100k 次,从全部年份随机抽 n=中期年样本量)==")
rng = random.Random(7)
years_all = list(U.index)
NPERM = 100_000
for w,lab in (("A","选举日→+12m"),("B","11/1→6/30"),("S","10/1→6/30 (Almanac)")):
    vals = U[w].values
    m = U[U.cyc==2][w].values
    n_m = len(m)
    obs_all_pos = (m>0).all(); obs_mean = m.mean()
    base = (vals>0).mean()
    hit_pos = hit_mean = 0
    for _ in range(NPERM):
        samp = rng.sample(range(len(vals)), n_m)
        sv = vals[samp] if hasattr(vals,'__getitem__') else [vals[i] for i in samp]
        import numpy as np
        sv = np.asarray([vals[i] for i in samp])
        if (sv>0).all(): hit_pos += 1
        if sv.mean() >= obs_mean: hit_mean += 1
    print(f"  {lab:22s} 观测 {int((m>0).sum())}/{n_m} 正 · 均 {obs_mean*100:+.1f}% | 全年基率 {base*100:.0f}% 正 | "
          f"p(随机{n_m}年全正)={hit_pos/NPERM:.4f} · p(均值≥观测)={hit_mean/NPERM:.4f}")
print(f"\n最小可能 p = {1/NPERM:.0e};选择面 ≈ ×12(4周期位×3窗)→ Bonferroni 阈 0.05/12 ≈ 0.0042")
U.to_csv("data/research/midterm_perm_2026-09/universe_windows.csv", index=False)
