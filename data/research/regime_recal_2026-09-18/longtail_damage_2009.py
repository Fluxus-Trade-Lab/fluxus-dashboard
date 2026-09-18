import pandas as pd, numpy as np, sys
SP=sys.argv[1]
sb=pd.read_csv(f"{SP}/stockbee_mm_all.csv",parse_dates=["date"]); sb=sb[(sb.date>="2009-01-01")&(sb.date<="2026-09-17")].set_index("date").sort_index().drop(columns=["spx","t2108"],errors="ignore")
spx=pd.read_csv(f"{SP}/gspc.csv",index_col=0,parse_dates=True).squeeze()
d=sb.join(spx.rename("spx"),how="inner")
s=d.spx.values; d["dd"]=[np.nan if len(s[i+1:i+22])<21 else s[i+1:i+22].min()/s[i]-1 for i in range(len(d))]
sh=d.dn25q/(d.up25q+d.dn25q); d["damage"]=np.select([sh>.55,sh>.45,sh>.35],[1,2,3],4)
bull=(d.up4>=300)&(d.up4.shift()>=300); bear=(d.dn4>=300)&(d.dn4.shift()>=300)
d["thrust"]=np.where(bull&~bear,4,np.where(bear&~bull,0,2))
e=d.dropna(subset=["dd"])
print("sessions",len(e),e.index.min().date(),e.index.max().date(),"base %.1f%%"%((e.dd<=-.05).mean()*100))
for k in ["damage","thrust"]:
    print(k,{int(v):f"{(g.dd<=-.05).mean()*100:.1f}% n={len(g)}" for v,g in e.groupby(k)})
for lo,hi in [("2009","2014"),("2015","2019"),("2020","2023"),("2024","2026")]:
    x=e.loc[lo:hi]; print(" damage",lo,hi,{int(v):f"{(g.dd<=-.05).mean()*100:.0f}%/{len(g)}" for v,g in x.groupby("damage")})
# independent episodes: count distinct 5% drawdown starts (non-overlapping 21d)
flag=(e.dd<=-.05).values; ep=0;i=0
while i<len(flag):
    if flag[i]: ep+=1; i+=21
    else: i+=1
print("independent 5% episodes approx",ep)
e[["damage","thrust","dd"]].to_csv(f"{SP}/longtail.csv")
