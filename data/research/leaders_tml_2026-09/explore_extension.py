"""⚠️ 探索性 —— 不在 prereg 里，是跑完主检验之后临时加的。
它把 spec_search_n 从 9 推到 19（+10 = 5 个五分位 × 2 个 horizon），已如实记进 results.md。
问题：Leading 日是不是「更拉伸」，H1 的差是不是延伸度的影子。
"""
import sys
from collections import defaultdict
import numpy as np
from scipy import stats
src = open('data/research/leaders_tml_2026-09/analyze.py').read()
exec(src.split("print('=== 面板 ===')")[0].replace("PANEL = sys.argv[1]", f"PANEL={sys.argv[1]!r}"))
ext = {}
for r in rows:
    try: ext[(r['ticker'], r['date'])] = float(r['atr_from_sma50'])
    except (ValueError, TypeError): pass
print('\n\n============ 探索性（不在 prereg 内）：延伸度中介 ============')
for N in (3, 5):
    recs = [r for r in build(N) if r[2] in ('Leading', 'Weakening')]
    a = [ext[(t,d)] for t,d,g,_,_ in recs if g=='Leading' and (t,d) in ext]
    b = [ext[(t,d)] for t,d,g,_,_ in recs if g=='Weakening' and (t,d) in ext]
    print(f'\n### N={N} · atr_from_sma50 中位 Leading={np.median(a):.2f} (n={len(a)}) '
          f'Weakening={np.median(b):.2f} (n={len(b)}) · MWU p={stats.mannwhitneyu(a,b)[1]:.2e}')
    q = np.quantile([ext[(t,d)] for t,d,_,_,_ in recs if (t,d) in ext], [.2,.4,.6,.8])
    sig = 0; tot = 0
    for i in range(5):
        lo = -np.inf if i==0 else q[i-1]; hi = np.inf if i==4 else q[i]
        L = [x for t,d,g,_,x in recs if g=='Leading'   and (t,d) in ext and lo<=ext[(t,d)]<hi]
        W = [x for t,d,g,_,x in recs if g=='Weakening' and (t,d) in ext and lo<=ext[(t,d)]<hi]
        if len(L)>=15 and len(W)>=15:
            p = stats.mannwhitneyu(L,W)[1]; tot += 1; sig += p<0.05
            print(f'   Q{i+1} ext[{lo:.2f},{hi:.2f})  L n={len(L):3d} 中位={np.median(L)*100:+.2f}%  '
                  f'W n={len(W):3d} 中位={np.median(W)*100:+.2f}%  差={(np.median(L)-np.median(W))*100:+.2f}pp  p={p:.3f}')
    print(f'   → {tot} 层里 {sig} 层 p<0.05（未做多重比较校正；Bonferroni 后阈值 {0.05/max(tot,1):.3f}）')
