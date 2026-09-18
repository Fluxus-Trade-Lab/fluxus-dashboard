"""Combine Stockbee Market Monitor yearly tabs into one daily table, mapping by header name."""
import pandas as pd, glob, io, re, sys
def key(h):
    s=re.sub(r"\s+"," ",str(h).lower())
    if "oscillator" in s or "ratio" in s and "breadth ratio" not in s and "day" not in s: pass
    if re.search(r"\b5 day",s): return "r5"
    if re.search(r"\b10 day",s): return "r10"
    if "34/13 bull" in s or ("13%" in s and "34" in s and "up" in s): return "up13_34"
    if "34/13 bear" in s or ("13%" in s and "34" in s and "down" in s): return "dn13_34"
    if "quarter" in s and "25" in s: return "dn25q" if "down" in s else "up25q"
    if "month" in s and "25" in s and "oscillator" not in s: return "dn25m" if "down" in s else "up25m"
    if ("month" in s and "50" in s) or s.strip() in ("50% up","50% down"): return "dn50m" if "down" in s else "up50m"
    if "4%" in s and "100%" not in s and "200%" not in s:
        return "dn4" if "down" in s else "up4"
    if "t2108" in s: return "t2108"
    if s.strip() in ("s&p","s&p 500"): return "spx"
    return None
rows=[]
for f in sorted(glob.glob("mm_tabs/*.csv")):
    txt=open(f,encoding="utf-8",errors="ignore").read()
    if "<html" in txt[:500].lower(): continue
    lines=txt.splitlines()
    hi=next((i for i,l in enumerate(lines) if l.startswith("Date,")),None)
    if hi is None: continue
    df=pd.read_csv(io.StringIO("\n".join(lines[hi:])),dtype=str,header=0)
    m={}
    for c in df.columns[1:]:
        k=key(c)
        if k and k not in m: m[k]=c
    if not ({"up4","dn4"}<=set(m)): continue
    out=pd.DataFrame({"date":df["Date"]})
    for k,c in m.items(): out[k]=pd.to_numeric(df[c].astype(str).str.replace(",","").str.strip(),errors="coerce")
    out["src"]=f.split("/")[-1][:-4]; rows.append(out)
d=pd.concat(rows,ignore_index=True)
d=d[d.date.astype(str).str.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$")]
def pdt(s):
    a,b,y=s.split("/"); y=int(y); y+=2000 if y<100 else 0
    a,b=int(a),int(b)
    if a>12: a,b=b,a   # dd/mm rows in the 2007 tab
    return pd.Timestamp(y,a,b)
d["date"]=d.date.map(pdt)
# conflicts between tabs on the same date
cols=[c for c in ["up4","dn4","r5","r10","up25q","dn25q","up25m","dn25m","up50m","dn50m","up13_34","dn13_34"] if c in d]
g=d.groupby("date")
conf=[dt for dt,x in g if len(x)>1 and x[["up4","dn4"]].nunique().max()>1]
print("conflicting dates:",len(conf),conf[:5])
d=d.sort_values(["date","src"]).groupby("date",as_index=False).first()
d.to_csv("stockbee_mm_all.csv",index=False)
print(len(d),d.date.min().date(),d.date.max().date())
print(d.notna().groupby(d.date.dt.year).sum()[cols].to_string())
