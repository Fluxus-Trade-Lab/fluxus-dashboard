#!/usr/bin/env python3
"""圈子情绪/注意力指标 —— 全部纯计数，不判方向（Andy 09-07「不需要方向」）。"""
import json,re,collections,statistics as st,sys

OUT_THEME={  # 圈外主题（非美股个股）
 "金":{"GLD","GDX","GDXJ","NUGT","JNUG","PALL","SIL","SLV","XAUUSD","AEM","NEM","WPM","FNV","KGC"},
 "币":{"IBIT","ETHA","MSTR","COIN","BTC","BTCUSD","ETH","BITO","BMNR","MARA","RIOT","CLSK","GLXY","SOL","XRP"},
 "能源":{"USO","UCO","XLE","XOP","OIH","WTI","NGAS","UNG"},
 "债汇":{"TLT","IEF","DXY","UUP","US10Y","TNX","JPY","EUR"},
}
INDEX={"SPY","QQQ","IWM","DIA","SPX","NDX","RSP","QQQE","VIX","UVIX","VXX"}
# 词表：只数词，不判谁对谁错
DEF=r"(?i)\b(cash|sidelines|risk[ -]?off|stopped out|stop(?:ped)? me out|cut (?:my|the)|trim(?:med|ming)?|de-?risk|defensive|hedg(?:e|ed|ing)|drawdown|chop(?:py)?|sit (?:this )?out|wait|patien(?:ce|t)|careful|caution)\b"
OFF=r"(?i)\b(breakout|break(?:ing)? out|added|adding|starter|full size|press(?:ing)?|leader(?:ship)?|thrust|follow[- ]through|new high|all[- ]time high|ripping|squeeze|momo|risk[ -]?on)\b"

def tickers(t):
    return {m.upper() for m in re.findall(r"\$([A-Za-z][A-Za-z.\-]{0,5})\b", t)}

def week_metrics(rows):
    m={}
    m["帖数"]=len(rows); m["人数"]=len({r["h"] for r in rows})
    m["回复占比"]=sum(1 for r in rows if r["is_reply"])/max(len(rows),1)
    per=collections.Counter(r["h"] for r in rows)
    m["人均帖数中位"]=st.median(per.values()) if per else 0
    # ticker 层
    ppl=collections.defaultdict(set); cnt=collections.Counter()
    for r in rows:
        for t in tickers(r["text"]):
            if len(t)>5: continue
            ppl[t].add(r["h"]); cnt[t]+=1
    m["不同ticker数"]=len(ppl)
    top=sorted(ppl.items(),key=lambda x:-len(x[1]))[:3]
    tot=sum(len(v) for v in ppl.values()) or 1
    m["前3集中度"]=sum(len(v) for _,v in top)/tot
    m["前3"]=" ".join(f"{t}({len(v)})" for t,v in top)
    # 圈外主题
    for g,s in OUT_THEME.items():
        who=set()
        for t in s & set(ppl): who |= ppl[t]
        m[f"圈外·{g}人数"]=len(who)
    m["指数提及人数"]=len({h for t in INDEX & set(ppl) for h in ppl[t]})
    # 词频（按帖计，一帖命中算一次）
    d=sum(1 for r in rows if re.search(DEF,r["text"]))
    o=sum(1 for r in rows if re.search(OFF,r["text"]))
    m["防守帖"]=d; m["进攻帖"]=o
    m["防守占比"]=d/max(len(rows),1); m["进攻占比"]=o/max(len(rows),1)
    m["防守/进攻"]=d/max(o,1)
    return m

if __name__=="__main__":
    d=json.load(open(sys.argv[1]))
    ks=list(d.keys())
    M={k:week_metrics(d[k]["rows"]) for k in ks}
    keys=[k for k in M[ks[0]] if k!="前3"]
    print(f"{'指标':16}"+"".join(f"{k:>14}" for k in ks))
    for key in keys:
        vals=[M[k][key] for k in ks]
        f=lambda v: f"{v:.3f}" if isinstance(v,float) else str(v)
        print(f"{key:16}"+"".join(f"{f(v):>14}" for v in vals))
    for k in ks: print(f"\n{k} 前3: {M[k]['前3']}  ({d[k]['d0']}~{d[k]['d1']})")
