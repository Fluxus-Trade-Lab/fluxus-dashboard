import pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
S='/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bc27bd12-cd07-4578-ac34-8d9bf23a0e1b/scratchpad'
y=pd.read_csv(f'{S}/DGS10.csv',parse_dates=['observation_date'],na_values=['.','']).dropna()
y=y.set_index('observation_date')['DGS10'].loc['1990-10-11':'2000-03-24']
s=pd.read_csv(f'{S}/gspc_1990s.csv',parse_dates=[0],index_col=0).squeeze().loc['1990-10-11':'2000-03-24']
n=len(y); share=(y>=5).mean()*100; med=y.median()
assert n==2366 and round(share,1)==95.5, (n,share)

BLUE='#2563eb'; INK='#111827'; SUB='#4b5563'; ORANGE='#ea580c'; GRID='#e5e7eb'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig=plt.figure(figsize=(10,6.2),dpi=200)
gs=fig.add_gridspec(2,1,height_ratios=[3,1.15],hspace=0.12,left=0.075,right=0.97,top=0.74,bottom=0.12)
a=fig.add_subplot(gs[0]); b=fig.add_subplot(gs[1],sharex=a)

a.fill_between(y.index,y.values,5,where=(y.values<5),color=ORANGE,alpha=0.28,linewidth=0,interpolate=True)
a.plot(y.index,y.values,color=BLUE,lw=1.15)
a.axhline(5,color=INK,lw=1.8)
a.set_ylim(3.8,9.2); a.set_yticks([4,5,6,7,8,9]); a.set_yticklabels([f'{v}%' for v in [4,5,6,7,8,9]])
a.text(0,1.025,'10-year Treasury yield, daily close',transform=a.transAxes,color=SUB,fontsize=10,va='bottom')
a.text(pd.Timestamp('1998-08-01'),4.05,'Only dip below 5%:\nSep 1998 – Feb 1999',color=ORANGE,fontsize=9.5,ha='right',va='bottom')

b.plot(s.index,s.values,color=INK,lw=1.1)
b.set_yscale('log'); b.set_yticks([300,600,1200]); b.set_yticklabels(['300','600','1,200']); b.minorticks_off()
b.text(0,1.04,'S&P 500, log scale',transform=b.transAxes,color=SUB,fontsize=10,va='bottom')

for ax in (a,b):
    ax.grid(axis='y',color=GRID,lw=0.8); ax.set_axisbelow(True)
    for sp in ('top','right'): ax.spines[sp].set_visible(False)
    ax.spines['left'].set_color(GRID); ax.spines['bottom'].set_color(GRID)
    ax.tick_params(colors=SUB,length=0)
plt.setp(a.get_xticklabels(),visible=False)
b.xaxis.set_major_locator(mdates.YearLocator()); b.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

fig.text(0.075,0.945,'In the 1990s bull market, the 10-year closed at or above 5%\non 95.5% of trading days',fontsize=16.5,fontweight='bold',color=INK,va='top')
fig.text(0.075,0.835,'S&P 500 +417%, from its Oct 11, 1990 close (295.46) to its Mar 24, 2000 close (1,527.46).',fontsize=10,color=SUB,va='top')
fig.text(0.075,0.805,f'{n:,} daily closes · median {med:.1f}% · above 5% on every close for 1,979 days straight, Oct 1990 – Sep 1998.',fontsize=10,color=SUB,va='top')
fig.text(0.075,0.035,'Data: FRED DGS10 (10-year Treasury, constant maturity) · S&P 500 price index, Yahoo Finance ^GSPC',fontsize=8.5,color=SUB)
fig.text(0.97,0.035,'FLUXUS',fontsize=9,color=INK,fontweight='bold',ha='right')
fig.savefig(f'{S}/1990s_10y_above_5pct_fluxus.png',facecolor='white')
print('ok',n,round(share,1),round(med,2))
