import yfinance as yf, pandas as pd, numpy as np, matplotlib, time, sys
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
fp="/System/Library/Fonts/Hiragino Sans GB.ttc"; fm.fontManager.addfont(fp); plt.rcParams["font.family"]=fm.FontProperties(fname=fp).get_name()
OUT=sys.argv[1]
import os
# Andy 10-03：「dashboard截图和案例截图应该用浅色背景」→ 默认浅色；CASE_THEME=dark 取回旧深色
if os.environ.get("CASE_THEME","light")=="dark":
    BG="#0F1115"; INK="#E8EAEF"; SUB="#8B90A0"; LINE="#262A35"; UP="#5BBF8F"; DN="#E0685F"; E10="#E0A458"; E20="#7EA6E8"; S50="#C792EA"
else:
    BG="#FFFFFF"; INK="#1D1B18"; SUB="#6E6A62"; LINE="#E6E2DB"; UP="#2F8F5B"; DN="#C8453B"; E10="#D9822B"; E20="#2F64B0"; S50="#8A4FB8"
def get(t):
    for k in range(4):
        x=yf.download(t,start="2025-09-01",end="2026-10-03",progress=False,auto_adjust=False)
        if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
        x=x.dropna(subset=["Open","High","Low","Close"])
        if len(x)>100: return x
        time.sleep(3)
    raise SystemExit(f"no data {t}")
def chart(t, start, end, marks, title, fname, sub):
    x=get(t); c=x["Close"]; x["e10"]=c.ewm(span=10,adjust=False).mean(); x["e20"]=c.ewm(span=20,adjust=False).mean(); x["s50"]=c.rolling(50).mean()
    d=x.loc[start:end]; n=len(d); idx=np.arange(n)
    fig,ax=plt.subplots(figsize=(16,9),dpi=120); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    for i,(o,h,l,cl) in enumerate(zip(d["Open"],d["High"],d["Low"],d["Close"])):
        col=UP if cl>=o else DN
        ax.vlines(i,l,h,color=col,lw=1.1); ax.add_patch(plt.Rectangle((i-0.32,min(o,cl)),0.64,max(abs(cl-o),1e-6),color=col))
    ax.plot(idx,d["e10"],color=E10,lw=1.8,label="10 日 EMA"); ax.plot(idx,d["e20"],color=E20,lw=1.8,label="20 日 EMA"); ax.plot(idx,d["s50"],color=S50,lw=2.2,label="50 日均线")
    lo,hi=float(d["Low"].min()),float(d["High"].max()); pad=(hi-lo)*0.12; ax.set_ylim(lo-pad,hi+pad*1.6)
    for k,(day,txt) in enumerate(marks,1):
        i=d.index.get_loc(pd.Timestamp(day)); y=float(d["High"].iloc[i])
        ax.annotate(f"{k}",(i,y),xytext=(i,y+pad*0.9),ha="center",va="center",color=BG,fontsize=15,fontweight="bold",
                    bbox=dict(boxstyle="circle,pad=0.35",fc=INK,ec=INK),arrowprops=dict(arrowstyle="-",color=SUB,lw=1))
    ticks=[i for i in range(n) if i==0 or d.index[i].month!=d.index[i-1].month]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{d.index[i].month} 月" for i in ticks],color=SUB,fontsize=14)
    ax.tick_params(axis="y",colors=SUB,labelsize=13); [s.set_color(LINE) for s in ax.spines.values()]; ax.grid(color=LINE,lw=0.6,alpha=0.7)
    ax.set_xlim(-1,n+1)
    fig.text(0.04,0.94,title,color=INK,fontsize=26,fontweight="bold"); fig.text(0.04,0.895,sub,color=SUB,fontsize=15)
    leg=ax.legend(loc="upper left",frameon=False,fontsize=14,ncol=3); [tx.set_color(INK) for tx in leg.get_texts()]
    for k,(day,txt) in enumerate(marks,1):
        fig.text(0.04+(k-1)*(0.94/len(marks)),0.035,f"{k}  {txt}",color=INK,fontsize=13)
    plt.subplots_adjust(left=0.05,right=0.97,top=0.86,bottom=0.13); fig.savefig(f"{OUT}/{fname}",facecolor=BG); plt.close(fig); print("saved",fname)
chart("QQQ","2026-08-03","2026-10-02",[("2026-09-18","9/18 日线、周线、5 日线都转「是」"),("2026-09-25","9/25 一路没红灯"),("2026-10-02","10/2 收 749.58，+3.90%")],"案例 A · 牛市中段：QQQ","case_A.png","2026 年 8–10 月日线 · 9/18 起日线信号连续 11 个交易日为「是」")
chart("SOXX","2026-03-16","2026-08-14",[("2026-06-22","6/22 收 655.01 见顶"),("2026-06-23","6/23 破 10 日线，转红"),("2026-07-13","7/13 收破 50 日线"),("2026-07-29","7/29 收 465.00，-29%")],"案例 B · 见顶：SOXX（半导体）","case_B.png","2026 年 3–8 月日线 · 3/30→6/22 涨 111%，之后高点一周比一周低")
chart("NOW","2026-03-02","2026-09-15",[("2026-04-10","4/10 收 83.00"),("2026-04-23","4/23 收 84.78"),("2026-05-13","5/13 收 87.05"),("2026-05-18","5/18 站回 50 日线"),("2026-06-25","6/25 收 89.52")],"案例 C · 底部：NOW（ServiceNow）","case_C.png","2026 年 3–9 月日线 · 四个低点一个比一个高，之后涨到 147.99")
