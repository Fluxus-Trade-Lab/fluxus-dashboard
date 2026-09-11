import csv, glob, os, json, collections
STORE={}
for x in glob.glob('data/output/tickers/*.json'):
    t=os.path.basename(x)[:-5]; d=json.load(open(x)); o=d.get('ohlc_2y') or []
    if o: STORE[t]=(o,{b['date']:i for i,b in enumerate(o)})
rows=list(csv.DictReader(open('data/history/ticker_events.csv')))
CAL=[b['date'] for b in STORE[next(iter(STORE))][0]]; CALI={d:i for i,d in enumerate(CAL)}
def pct(t,date):
    if t not in STORE: return None
    o,idx=STORE[t]; i=idx.get(date)
    if not i: return None
    p=o[i-1]['close']
    return None if not p else o[i]['close']/p-1.0
def perrow(target, presets_only, span=25):
    rs=[r for r in rows if r['date']==target and r['change_pct'] not in ('0.0','0','')
        and (r['screener'].startswith('preset:') if presets_only else True)]
    i=CALI[target]; cands=CAL[i-span:i+6]
    hit=collections.Counter(); nomatch=0; tot=0
    for r in rs:
        if r['ticker'] not in STORE: continue
        tot+=1
        cp=float(r['change_pct']); got=[]
        for c in cands:
            b=pct(r['ticker'],c)
            if b is not None and abs(cp-b)<=0.005: got.append(c)
        if not got: nomatch+=1
        else:
            for g in got: hit[g]+=1
    print('\n%s presets_only=%s  可比行 %d，配不上任何一天 %d (%.0f%%)'%(target,presets_only,tot,nomatch,100*nomatch/max(tot,1)))
    print('  命中日分布 top8:', hit.most_common(8))
perrow('2026-08-17', True)
perrow('2026-08-07', False)
perrow('2026-09-09', False)
