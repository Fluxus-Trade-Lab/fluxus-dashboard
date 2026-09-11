exec(open('recompute.py').read().split("# week-cluster bootstrap")[0].replace("print(","(lambda *a,**k: None)("))
# 1) stale/ffill: fraction of events whose t..t+5 window has any zero daily change
z = 0; zb=0
for jj, tt in zip(D.j.values, D.t.values):
    w = C[tt:tt+6, jj]; z += np.any(np.diff(w) == 0)
    wb = C[tt-5:tt+1, jj]; zb += np.any(np.diff(wb) == 0)
print('events w/ a zero-change day in t..t+5:', z/len(D), ' in t-5..t:', zb/len(D))
# tickers whose last non-changing run ends at panel end (stale ffill tail)
tail=[]
for jj in stk_idx:
    col=C[:,jj]; d=np.diff(col); nz=np.where(d!=0)[0]
    if len(nz): tail.append(T-2-nz[-1])
tail=np.array(tail); print('tickers with >=5 flat trailing days:', (tail>=5).sum())
# 2) refractory > 10 (t+11) variant
rows2=[]
for jj in stk_idx:
    idx=np.where(base[:,jj])[0]; last=-10**9
    for tt in idx:
        if tt-last>10: last=tt; rows2.append((jj,tt))
print('dedup count with gap>10:', len(rows2))
# 3) vol by k with ddof=0 and vol-stratified H-M
D['vol0'] = pd.DataFrame(ret).rolling(20,min_periods=20).std(ddof=0).values[D.t.values-5, D.j.values]
print(D.groupby('k').vol0.median().round(4).to_dict())
D['vq']=pd.qcut(D.vol,5,labels=False)
for q in range(5):
    s=D[D.vq==q]
    print('volQ',q,'n',len(s),'P10 k<=1',round((s[s.k<=1].x5>=.1).mean(),4),'k>=3',round((s[s.k>=3].x5>=.1).mean(),4),
          'med k<=1',round(s[s.k<=1].x5.median(),4),'k>=3',round(s[s.k>=3].x5.median(),4), 'share k>=3', round((s.k>=3).mean(),3))
# vol-normalized tail: x5/vol >= 2
z=D.x5/D.vol
for kk in range(5): print('k',kk,'P(x5/vol20>=2)',round((z[D.k==kk]>=2).mean(),4))
