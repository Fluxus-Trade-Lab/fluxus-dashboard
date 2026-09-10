#!/usr/bin/env python3
"""Point-in-time drawdown study on ^GSPC (ShortBear's three questions).

口径:标准 drawdown/underwater 框架(Morgan Stanley Counterpoint Global,
"Drawdowns and Recoveries" — Mauboussin):close-based decline from running ATH;
三段计时 = peak→trough / trough→recovery / total underwater。无自造量。
Episode = 相邻两个 ATH 之间的水下期;进行中的最后一段按「删失」处理,
不进 recovery 分布(否则低估恢复时间)。
"""
import warnings; warnings.filterwarnings("ignore")
import yfinance as yf
import pandas as pd

df = yf.download("^GSPC", start="1900-01-01", end="2026-09-11", progress=False, auto_adjust=False)
c = df["Close"]
c = c[c.columns[0]] if hasattr(c, "columns") else c
c = c.dropna()
print(f"^GSPC daily: {c.index[0].date()} → {c.index[-1].date()}  ({len(c):,} bars)")

ath = c.cummax()
dd = c / ath - 1.0

# ── episodes ──
eps = []
cur = None
for dt_, px, peak, d in zip(c.index, c.values, ath.values, dd.values):
    if d >= 0:
        if cur is not None:
            cur["recovery"] = dt_
            eps.append(cur); cur = None
        last_ath_date = dt_
    else:
        if cur is None:
            cur = {"peak_date": last_ath_date, "trough": d, "trough_date": dt_}
        elif d < cur["trough"]:
            cur["trough"], cur["trough_date"] = d, dt_
ongoing = cur  # censored

BUCKETS = [(0,5),(5,10),(10,15),(15,20),(20,30),(30,100)]
def bucket(depth_pct):
    for lo,hi in BUCKETS:
        if lo <= depth_pct < hi: return f"{lo}–{hi if hi<100 else '·'}%"
    return "?"

rows = []
for e in eps:
    depth = -e["trough"]*100
    p2t = (e["trough_date"]-e["peak_date"]).days
    t2r = (e["recovery"]-e["trough_date"]).days
    rows.append({"bucket": bucket(depth), "depth": depth, "p2t": p2t, "t2r": t2r,
                 "uw": p2t+t2r, "peak": e["peak_date"].date(), "trough_date": e["trough_date"].date()})
E = pd.DataFrame(rows)
years = (c.index[-1]-c.index[0]).days/365.25

print("\n== Q1/Q2: 各深度桶的频率与三段计时(已完成 episodes, n=%d;日历日) ==" % len(E))
tab = []
for lo,hi in BUCKETS:
    b = f"{lo}–{hi if hi<100 else '·'}%"
    g = E[E.bucket==b]
    if not len(g): continue
    tab.append({
        "桶": b, "次数": len(g), "频率": f"每 {years/len(g):.1f} 年一次",
        "峰→谷 中位": int(g.p2t.median()), "谷→复原 中位": int(g.t2r.median()),
        "谷→复原 P75": int(g.t2r.quantile(.75)), "谷→复原 P90": int(g.t2r.quantile(.9)),
        "谷→复原 最长": int(g.t2r.max()),
        "总水下 中位": int(g.uw.median()), "总水下 最长": int(g.uw.max()),
    })
T1 = pd.DataFrame(tab)
print(T1.to_string(index=False))

# ── first-touch 条件分析(真正的 point-in-time 问法)──
print("\n== PIT:第一次触及深度 X 那天起,历史上接下来发生了什么 ==")
touch_rows = []
for T in (5,10,15,20,30):
    hits = []
    for e in eps + ([ongoing] if ongoing else []):
        depth = -e["trough"]*100
        if depth < T: continue
        # first touch date: first close with dd <= -T inside this episode
        seg = dd[(dd.index >= e["peak_date"]) & (dd.index <= e.get("recovery", dd.index[-1]))]
        ft = seg[seg <= -T/100].index[0]
        rec = e.get("recovery")
        hits.append({"ft": ft, "rec": rec, "depth": depth,
                     "days": (rec-ft).days if rec is not None else None})
    done = [h for h in hits if h["days"] is not None]
    deeper_T = {5:10,10:15,15:20,20:30,30:50}[T]
    p_deeper = sum(1 for h in hits if h["depth"] >= deeper_T)/len(hits)*100
    ds = sorted(h["days"] for h in done)
    def within(m): return sum(1 for d in ds if d <= m*30.44)/len(hits)*100
    touch_rows.append({
        "触及": f"−{T}%", "历史次数": len(hits), "其中未复原(删失)": len(hits)-len(done),
        f"P(继续跌破 −{deeper_T}%)": f"{p_deeper:.0f}%",
        "触及→新高 中位(日)": int(ds[len(ds)//2]),
        "P25/P75": f"{int(pd.Series(ds).quantile(.25))}/{int(pd.Series(ds).quantile(.75))}",
        "3个月内复原": f"{within(3):.0f}%", "6个月": f"{within(6):.0f}%",
        "12个月": f"{within(12):.0f}%", "24个月": f"{within(24):.0f}%",
    })
T2 = pd.DataFrame(touch_rows)
print(T2.to_string(index=False))

cur_dd = dd.iloc[-1]*100
print(f"\n当前状态: SPX 距 ATH {cur_dd:+.1f}%")
if ongoing: print(f"进行中的水下期: 峰 {ongoing['peak_date'].date()} · 谷 {-ongoing['trough']*100:.1f}% @ {ongoing['trough_date'].date()}(删失,未进上表分布)")
T1.to_csv("data/research/drawdown_pit_2026-09/episode_buckets.csv", index=False)
T2.to_csv("data/research/drawdown_pit_2026-09/first_touch_pit.csv", index=False)
E.to_csv("data/research/drawdown_pit_2026-09/episodes_raw.csv", index=False)
print("\ncsv written")
