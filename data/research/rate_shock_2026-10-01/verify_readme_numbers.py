#!/usr/bin/env python3
"""核 README.md 里每一个数字和 rate_shock.json 一致（192 条断言）。

为什么要有这个脚本：T-0921-100 那次我把一处旧数留在文档里，被复核当场判 FAIL；
这份 README 有 190 多个数，手工核一遍必漏。**阳性对照已验过**——把任意一个期望值
改错一个小数位，它会打出 ❌ 并以退出码 1 退出（不是静默放过）。

用法：python3 data/research/rate_shock_2026-10-01/verify_readme_numbers.py
"""
import json,re,sys
d=json.load(open('data/research/rate_shock_2026-10-01/rate_shock.json'))
A=d['assets']; bad=[]
def chk(label,got,want,tol=0.005):
    ok=abs(got-want)<=tol
    print(f"{'✅' if ok else '❌'} {label}: README={want} json={round(got,4)}")
    if not ok: bad.append(label)

# T1
T1={'^GSPC':(78,542,77,0.08,-0.21,0.422,0.20,-0.85,0.130,1.03,-1.54,0.126),
    'SPY':(36,212,35,0.29,-0.08,0.814,-0.18,-1.62,0.034,2.91,-0.82,0.441),
    'QQQ':(28,176,27,-0.68,-1.18,0.074,-2.88,-4.50,0.002,1.33,-3.13,0.116),
    'IWM':(28,171,27,-0.11,-0.45,0.489,-0.38,-1.74,0.189,1.67,-1.52,0.472),
    'RSP':(23,135,22,-0.38,-0.76,0.097,-0.85,-2.34,0.024,1.02,-2.65,0.085)}
for a,v in T1.items():
    b=A[a]['buckets']['A_sig756_z2.0+']
    chk(f"T1 {a} ev21",b['21']['n_event_days'],v[0],0)
    chk(f"T1 {a} raw",b['0']['n_event_days'],v[1],0)
    for i,h in enumerate([5,21,63]):
        c=b['21'][f'abs_{h}']
        chk(f"T1 {a} h{h} n",c['n'],v[2],0)
        chk(f"T1 {a} h{h} med",c['median']*100,v[3+i*3])
        chk(f"T1 {a} h{h} abn",c['abn_median']*100,v[4+i*3])
        chk(f"T1 {a} h{h} p",c['p_two_sided'],v[5+i*3])
# T2 h21 三档 + QQQ h5
T2={'QQQ':(-4.50,-3.42,-4.17,18),'RSP':(-2.34,-2.15,-1.85,13),'SPY':(-1.62,0.02,-0.80,26),
    'IWM':(-1.74,-0.36,0.03,18),'^GSPC':(-0.85,-0.63,-0.74,68)}
for a,v in T2.items():
    r=A[a]['robustness']['A_sig756_z2.0+']
    for k,want in zip(['all','ex2022','ex2022_2023'],v[:3]):
        chk(f"T2 {a} h21 {k}",r[k]['abs_21']['abn_median']*100,want)
    chk(f"T2 {a} ex2223 n",r['ex2022_2023']['abs_21']['n'],v[3],0)
    chk(f"T2 {a} 2022count",r['events_by_year'].get('2022',0),6,0)
for k,want in zip(['all','ex2022','ex2022_2023'],[-1.18,-1.82,-2.27]):
    chk(f"T2 QQQ h5 {k}",A['QQQ']['robustness']['A_sig756_z2.0+'][k]['abs_5']['abn_median']*100,want)
# T4 + RSP C 稳健
T4={'^GSPC':(144,1296,-0.13,-0.68,-0.86,55,60),'SPY':(67,515,-0.04,-0.24,-0.89,59,66),
    'QQQ':(53,415,0.23,-1.01,0.88,54,63),'IWM':(47,376,-0.02,-1.68,-0.61,48,60),
    'RSP':(41,333,-1.20,-2.10,0.93,45,65)}
for a,v in T4.items():
    b=A[a]['buckets']['C_d20_40bp+']
    chk(f"T4 {a} ev21",b['21']['n_event_days'],v[0],0); chk(f"T4 {a} raw",b['0']['n_event_days'],v[1],0)
    for i,h in enumerate([5,21,63]): chk(f"T4 {a} h{h} abn",b['21'][f'abs_{h}']['abn_median']*100,v[2+i])
    chk(f"T4 {a} h21 hit",b['21']['abs_21']['hit']*100,v[5],0.5)
    chk(f"T4 {a} uncond hit",A[a]['uncond']['abs_21']['hit']*100,v[6],0.5)
rc=A['RSP']['robustness']['C_d20_40bp+']
chk("T4 RSP C h5 ex2223",rc['ex2022_2023']['abs_5']['abn_median']*100,0.19)
chk("T4 RSP C h21 ex2223",rc['ex2022_2023']['abs_21']['abn_median']*100,-0.89)
# T5
for a,v in {'QQQ':(-0.09,-1.39,-0.42,0.017),'IWM':(-0.15,0.01,0.46,0.984),'RSP':(-0.22,0.32,0.70,0.289)}.items():
    b=A[a]['buckets']['A_sig756_z2.0+']['21']
    for i,h in enumerate([5,21,63]): chk(f"T5 {a} h{h}",b[f'rel_spy_{h}']['abn_median']*100,v[i])
    chk(f"T5 {a} h21 p",b['rel_spy_21']['p_two_sided'],v[3])
# T3
for a,bp,n,abn in [('^GSPC',50,90,-0.38),('^GSPC',100,37,0.77),('^GSPC',200,8,1.08),('^GSPC',300,3,1.77),
                   ('SPY',50,44,-0.11),('SPY',100,17,0.60),('QQQ',50,35,-0.24),('QQQ',100,13,2.59),
                   ('IWM',50,33,1.62),('IWM',100,12,0.60),('RSP',50,28,0.23),('RSP',100,11,1.28)]:
    c=A[a]['buckets'][f'B_runup126_{bp}bp+']['126']['abs_21']
    chk(f"T3 {a} {bp}bp n",c['n'],n,0); chk(f"T3 {a} {bp}bp abn",c['abn_median']*100,abn)
# T6
for b,h,abn,p in [('D_rel63_20pct+',21,0.74,0.183),('D_rel63_20pct+',63,1.17,0.249),('D_rel63_30pct+',63,3.03,0.048)]:
    c=A['^GSPC']['buckets'][b]['21'][f'abs_{h}']; chk(f"T6 GSPC {b} h{h} abn",c['abn_median']*100,abn); chk(f"T6 GSPC {b} h{h} p",c['p_two_sided'],p)
chk("T6 ev20",A['^GSPC']['buckets']['D_rel63_20pct+']['21']['n_event_days'],66,0)
chk("T6 ev30",A['^GSPC']['buckets']['D_rel63_30pct+']['21']['n_event_days'],31,0)
chk("T6 30pct h63 hit",A['^GSPC']['buckets']['D_rel63_30pct+']['21']['abs_63']['hit']*100,84,0.5)
# 当下读数 + 校准 + 数据源
cr=d['current_reading']
for k,want in [('y',5.26),('d21',0.51),('z756',2.18),('runup126',1.00),('rel63',0.174)]:
    chk(f"当下 {k}",cr[k],want,0.006)
chk("GS 锚点 756d",d['gs_calibration_check']['sigma_lookback_756d']['two_sigma_bp'],61.0,0.05)
chk("GS 锚点 1260d",d['gs_calibration_check']['sigma_lookback_1260d']['two_sigma_bp'],53.7,0.05)
chk("GS 锚点 2520d",d['gs_calibration_check']['sigma_lookback_2520d']['two_sigma_bp'],48.2,0.05)
chk("DGS10 n_obs",d['dgs10']['n_obs'],16171,0)
ed=json.load(open('data/research/rate_shock_2026-10-01/event_dates_spx.json'))
chk("SPX 第一个2σ事件=1965-09-29",1 if ed['A_sig756_z2.0+'][0]=='1965-09-29' else 0,1,0)
chk("SPX C 144次",len(ed['C_d20_40bp+']),144,0)
print(f"\n{'❌ 不符 '+str(len(bad)) if bad else '✅ 全部 README 数字与 json 一致'}")
if bad: print("\n".join(bad)); sys.exit(1)
