"""TML 前瞻验 —— 按 prereg.md 跑，不加戏。

用法（价格面板先由 fetch 步骤落进 scratchpad，见 README 的复现命令）：
    python3 data/research/leaders_tml_2026-09/analyze.py <price_panel.pkl>

输出全部打印成表，散文里的每个数字都必须能在这里指到一行
（`pitfall_i_misread_my_own_table`：散文里不许出现手打的数字）。
"""
import csv, sys, json
from collections import defaultdict
import numpy as np, pandas as pd
from scipy import stats

PANEL = sys.argv[1]
LOG = 'data/history/leaders_log.csv'
BAD_ENDPOINTS = {'2026-08-28'}   # yfinance 当前缺该日 245/283 只；我们自己的归档有，见 README
RNG = np.random.default_rng(20260903)

close = pd.read_pickle(PANEL)
close.index = [str(d.date()) for d in close.index]
sessions = list(close.index)
rows = list(csv.DictReader(open(LOG)))

def fwd(t, d, n):
    if t not in close.columns or d not in sessions: return None
    i = sessions.index(d)
    if i + n >= len(sessions): return None
    e = sessions[i + n]
    if e in BAD_ENDPOINTS: return None
    a, b = close[t].get(d), close[t].get(e)
    if a is None or b is None or pd.isna(a) or pd.isna(b) or a <= 0: return None
    return b / a - 1.0

def label(r):
    gs, tml = r['group_state'], r['tml'] == 'True'
    return gs, tml

def build(n):
    """返回 [(ticker, date, group_state, tml, excess)]"""
    out = []
    for r in rows:
        t, d = r['ticker'], r['date']
        rt, sp = fwd(t, d, n), fwd('SPY', d, n)
        if rt is None or sp is None: continue
        gs, tml = label(r)
        out.append((t, d, gs, tml, rt - sp))
    return out

def paired_wilcoxon(recs, in_mask, out_mask):
    """票级配对：每票取 in 组均值与 out 组均值之差。"""
    a, b = defaultdict(list), defaultdict(list)
    for t, d, gs, tml, x in recs:
        if in_mask(gs, tml): a[t].append(x)
        elif out_mask(gs, tml): b[t].append(x)
    pairs = [(t, np.mean(a[t]), np.mean(b[t])) for t in a if t in b]
    if len(pairs) < 6: return dict(n=len(pairs), p=None, med_diff=None)
    diff = np.array([p[1] - p[2] for p in pairs])
    stat, p = stats.wilcoxon(diff)
    return dict(n=len(pairs), p=p, med_diff=float(np.median(diff)),
                mean_diff=float(diff.mean()),
                med_in=float(np.median([p[1] for p in pairs])),
                med_out=float(np.median([p[2] for p in pairs])), diff=diff)

LEAD  = lambda gs, tml: gs == 'Leading'
WEAK  = lambda gs, tml: gs == 'Weakening'
TMLm  = lambda gs, tml: tml
LEADnT= lambda gs, tml: gs == 'Leading' and not tml
NOTTML= lambda gs, tml: not tml

def pct(x): return 'n/a' if x is None else f'{x*100:+.3f}%'
def pv(x):  return 'n/a' if x is None else (f'{x:.4f}' if x >= 1e-4 else f'{x:.1e}')

print('=== 面板 ===')
print('sessions:', ' '.join(sessions))
print('丢弃终点:', BAD_ENDPOINTS)

# prereg §6.2 两个源的一致性核对
mism = []
for r in rows:
    t, d = r['ticker'], r['date']
    if t in close.columns and d in sessions:
        a = close[t].get(d)
        if a is not None and not pd.isna(a) and float(r['close']) > 0:
            rel = abs(a / float(r['close']) - 1)
            if rel > 0.02: mism.append((t, d, float(r['close']), round(float(a), 2), round(rel * 100, 1)))
print(f'\n=== 两个源的 close 一致性（|差|>2% 的行）: {len(mism)} / {len(rows)} ===')
for m in mism[:12]: print('  ', m)

results = {}
for n in (3, 5, 10):
    recs = build(n)
    ndates = len(set(d for _, d, _, _, _ in recs))
    print(f'\n================ N = {n} 个 session ================')
    print(f'可用 as_of {ndates} 个 · 行 {len(recs)} · 票 {len(set(r[0] for r in recs))}')
    for name, im, om in (('H1 Leading vs Weakening', LEAD, WEAK),
                         ('H2 Leading内 rs1m>=80 vs <80', TMLm, LEADnT),
                         ('H3 TML vs 全部非TML(混合体)', TMLm, NOTTML)):
        r = paired_wilcoxon(recs, im, om)
        print(f'  {name:34s} n票={r["n"]:4d}  中位差={pct(r["med_diff"])}  '
              f'p={pv(r["p"])}  (in中位={pct(r.get("med_in"))} out中位={pct(r.get("med_out"))})')
        results[(n, name)] = r
    # 描述性：各态的原始超额中位
    for gs in ('Leading', 'Weakening', 'Improving', 'Lagging'):
        xs = [x for _, _, g, _, x in recs if g == gs]
        if xs: print(f'    [描述] {gs:10s} n行={len(xs):5d} 超额中位={pct(float(np.median(xs)))}')

# ---- 对照 ----
N0 = 5
recs = build(N0)
真 = paired_wilcoxon(recs, LEAD, WEAK)
print(f'\n=== 阴性对照（N={N0}，日期内随机重排标签 1000 次）===')
bydate = defaultdict(list)
for i, r in enumerate(recs): bydate[r[1]].append(i)
ps, eff = [], []
for _ in range(1000):
    sh = list(recs)
    for d, idx in bydate.items():
        labs = [(recs[i][2], recs[i][3]) for i in idx]
        RNG.shuffle(labs)
        for i, (gs, tml) in zip(idx, labs):
            t, dd, _, _, x = recs[i]; sh[i] = (t, dd, gs, tml, x)
    rr = paired_wilcoxon(sh, LEAD, WEAK)
    if rr['p'] is not None: ps.append(rr['p']); eff.append(rr['med_diff'])
ps = np.array(ps); eff = np.array(eff)
print(f'  p<0.05 的比例 {np.mean(ps < 0.05):.3f}（该为 ~0.05）· p 中位 {np.median(ps):.3f}')
print(f'  重排后中位差的 2.5/97.5 分位 {pct(np.quantile(eff,.025))} .. {pct(np.quantile(eff,.975))}'
      f'  · 真实读数 {pct(真["med_diff"])}')

print(f'\n=== 阳性对照 / 分辨率地板（N={N0}，往 Leading 行注射已知效应，票级 bootstrap 500 次）===')
tickers = sorted(set(r[0] for r in recs))
byt = defaultdict(list)
for r in recs: byt[r[0]].append(r)
for inj in (0.000, 0.005, 0.010, 0.020, 0.030):
    hit = 0; tried = 0
    for _ in range(500):
        pick = RNG.choice(tickers, size=len(tickers), replace=True)
        boot = []
        for k, t in enumerate(pick):
            for (_, d, gs, tml, x) in byt[t]:
                boot.append((f'{t}#{k}', d, gs, tml, x + (inj if gs == 'Leading' else 0.0)))
        rr = paired_wilcoxon(boot, LEAD, WEAK)
        if rr['p'] is not None:
            tried += 1; hit += (rr['p'] < 0.05)
    print(f'  注射 {inj*100:+.1f}%  →  p<0.05 的比例 {hit/max(tried,1):.3f}  ({tried} 次有效)')

print(f'\n=== 最小可能 p（配对 Wilcoxon, n={真["n"]}）===')
print(f'  两侧下限 = 2/2^n = {2/2**真["n"]:.3e} —— 远小于 0.05，本设计不存在分辨率地板式的结构性失明')

# ============================ 对照与稳健性（04:5x 之后追加，全部按 prereg §3/§4）============
def within_date(recs):
    """日期内对照：同一天 Leading 中位 − Weakening 中位，再对日期做符号检验。"""
    ds=sorted(set(d for _,d,_,_,_ in recs)); out=[]
    for d in ds:
        L=[x for _,dd,g,_,x in recs if dd==d and g=='Leading']
        W=[x for _,dd,g,_,x in recs if dd==d and g=='Weakening']
        if len(L)>=10 and len(W)>=10:
            out.append((d,len(L),float(np.median(L)),len(W),float(np.median(W)),
                        float(stats.mannwhitneyu(L,W)[1])))
    return out

def two_way_demedian(recs, iters=30):
    """票 + 日期 两向去中位，再在行级比 Leading vs Weakening。"""
    x=np.array([r[4] for r in recs]); tk=[r[0] for r in recs]; dt=[r[1] for r in recs]
    for _ in range(iters):
        for keys in (tk,dt):
            m=defaultdict(list)
            for k,v in zip(keys,x): m[k].append(v)
            m={k:np.median(v) for k,v in m.items()}
            x=np.array([v-m[k] for k,v in zip(keys,x)])
    lead=np.array([g=='Leading' for _,_,g,_,_ in recs])
    return dict(n_lead=int(lead.sum()), n_weak=int((~lead).sum()),
                med_lead=float(np.median(x[lead])), med_weak=float(np.median(x[~lead])),
                p=float(stats.mannwhitneyu(x[lead],x[~lead])[1]))

def null_calibration(recs, mode, iters=600, seed=77):
    """mode='ret' 同日内打散收益（保留全部标签结构）· mode='lab' 同日内打散标签。"""
    rng=np.random.default_rng(seed); bydate=defaultdict(list)
    for i,r in enumerate(recs): bydate[r[1]].append(i)
    eff=[];ps=[]
    for _ in range(iters):
        sh=list(recs)
        for d,idx in bydate.items():
            if mode=='ret':
                vals=[recs[i][4] for i in idx]; rng.shuffle(vals)
                for i,v in zip(idx,vals):
                    t,dd,g,m,_=recs[i]; sh[i]=(t,dd,g,m,v)
            else:
                labs=[(recs[i][2],recs[i][3]) for i in idx]; rng.shuffle(labs)
                for i,(g,m) in zip(idx,labs):
                    t,dd,_,_,v=recs[i]; sh[i]=(t,dd,g,m,v)
        rr=paired_wilcoxon(sh,LEAD,WEAK)
        if rr['p'] is not None: eff.append(rr['med_diff']); ps.append(rr['p'])
    eff=np.array(eff);ps=np.array(ps)
    return dict(med=float(np.median(eff)), lo=float(np.quantile(eff,.025)),
                hi=float(np.quantile(eff,.975)), rej=float(np.mean(ps<0.05)), eff=eff)

def power_curve(recs, injections, iters=300, seed=2026):
    """先减掉估计效应把真效应置零，再注射已知效应 —— 这才是功效曲线。"""
    shift=paired_wilcoxon(recs,LEAD,WEAK)['med_diff']
    nulled=[(t,d,g,m,x-(shift if g=='Leading' else 0.0)) for t,d,g,m,x in recs]
    chk=paired_wilcoxon(nulled,LEAD,WEAK)
    rng=np.random.default_rng(seed); byt=defaultdict(list)
    for r in nulled: byt[r[0]].append(r)
    tickers=sorted(byt)
    out=[]
    for inj in injections:
        hit=tried=0
        for _ in range(iters):
            pick=rng.choice(tickers,size=len(tickers),replace=True); boot=[]
            for k,t in enumerate(pick):
                for (_,d,g,m,v) in byt[t]: boot.append((f'{t}#{k}',d,g,m,v+(inj if g=='Leading' else 0.0)))
            rr=paired_wilcoxon(boot,LEAD,WEAK)
            if rr['p'] is not None: tried+=1; hit+=(rr['p']<0.05)
        out.append((inj, hit/max(tried,1)))
    return dict(shift=float(shift), nulled_p=float(chk['p']), curve=out)

print('\n\n================== 对照与稳健性 ==================')
for N in (3,5):
    recs=[r for r in build(N) if r[2] in ('Leading','Weakening')]
    real=paired_wilcoxon(recs,LEAD,WEAK)
    print(f'\n########## N={N} · 行 {len(recs)} · 配对法真实读数 {real["med_diff"]*100:+.3f}pp '
          f'名义 p={real["p"]:.2e} (n票={real["n"]})')
    print('  [C1 日期内对照] as_of / L n / L中位 / W n / W中位 / 差pp / MWU p')
    wd=within_date(recs); difs=[]
    for d,nl,ml,nw,mw,p in wd:
        difs.append(ml-mw)
        print(f'      {d}  {nl:3d} {ml*100:+7.2f}%  {nw:3d} {mw*100:+7.2f}%  {(ml-mw)*100:+6.2f}pp  p={p:.3f}')
    neg=sum(1 for v in difs if v<0)
    print(f'      → {neg}/{len(difs)} 为负 · 符号检验 p={stats.binomtest(neg,len(difs),0.5).pvalue:.4f}'
          f' · 全同号时的最小可能 p={stats.binomtest(0,len(difs),0.5).pvalue:.4f}'
          f' · 差的中位 {np.median(difs)*100:+.2f}pp')
    tw=two_way_demedian(recs)
    print(f'  [C2 双向去中位·行级] Leading n={tw["n_lead"]} 中位={tw["med_lead"]*100:+.3f}pp · '
          f'Weakening n={tw["n_weak"]} 中位={tw["med_weak"]*100:+.3f}pp · '
          f'差={(tw["med_lead"]-tw["med_weak"])*100:+.3f}pp · MWU p={tw["p"]:.5f}')
    for mode,tag in (('ret','C3 同日打散收益(保留标签结构)'),('lab','C4 同日打散标签(prereg 那个)')):
        nc=null_calibration(recs,mode)
        pemp=(np.sum(nc['eff']<=real['med_diff'])+1)/(len(nc['eff'])+1)
        print(f'  [{tag}] 零分布中位 {nc["med"]*100:+.3f}pp · 95%区间 [{nc["lo"]*100:+.3f},{nc["hi"]*100:+.3f}]pp'
              f' · 名义p<0.05 的实际比例 {nc["rej"]:.3f} (该为 0.050) · 真实读数经验 p={pemp:.4f}')
    pc=power_curve(recs,(0.005,0.010,0.015,0.020))
    print(f'  [C5 功效/分辨率地板] 置零校验 p={pc["nulled_p"]:.3f}（该 >0.05）· ' +
          ' · '.join(f'注射{i*100:+.1f}pp→{r:.3f}' for i,r in pc['curve']))
