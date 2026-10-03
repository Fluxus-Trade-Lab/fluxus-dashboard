import pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.dates as mdates
S='/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/bc27bd12-cd07-4578-ac34-8d9bf23a0e1b/scratchpad'
d=pd.read_csv(f'{S}/semi.csv',parse_dates=['date']).set_index('date')
s=d['semi_pct_above_50sma']; m=d['mkt_pct_above_50sma']
assert s.iloc[-1]==77.5 and m.iloc[-1]==27.43 and len(d)==44, (s.iloc[-1],m.iloc[-1],len(d))
cross=d.index[(s>m)][0]
BLUE='#2563eb'; INK='#111827'; SUB='#4b5563'; GREY='#9ca3af'; GRID='#e5e7eb'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig=plt.figure(figsize=(10,6.2),dpi=200)
a=fig.add_axes([0.075,0.12,0.84,0.6])
a.plot(m.index,m.values,color=GREY,lw=2)
a.plot(s.index,s.values,color=BLUE,lw=2.4)
a.text(s.index[-1]+pd.Timedelta(days=0.6),s.iloc[-1],f'Semis\n{s.iloc[-1]:.0f}%',color=BLUE,fontsize=11,fontweight='bold',va='center')
a.text(m.index[-1]+pd.Timedelta(days=0.6),m.iloc[-1],f'All stocks\n{m.iloc[-1]:.0f}%',color=SUB,fontsize=11,fontweight='bold',va='center')
a.axvline(cross,color=INK,lw=0.8,ls=':')
a.text(cross-pd.Timedelta(days=0.5),96,f'Semis pull ahead\n{cross:%b %-d}',color=INK,fontsize=9.5,ha='right',va='top')
a.set_ylim(0,100); a.set_yticks([0,25,50,75,100]); a.set_yticklabels([f'{v}%' for v in [0,25,50,75,100]])
a.grid(axis='y',color=GRID,lw=0.8); a.set_axisbelow(True)
for sp in ('top','right'): a.spines[sp].set_visible(False)
a.spines['left'].set_color(GRID); a.spines['bottom'].set_color(GRID); a.tick_params(colors=SUB,length=0)
a.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0,interval=2)); a.xaxis.set_major_formatter(mdates.DateFormatter('%b %-d'))
a.text(0,1.03,'Share of stocks above their 50-day moving average',transform=a.transAxes,color=SUB,fontsize=10,va='bottom')
fig.text(0.075,0.945,'Semis pulled ahead of the market on September 18',fontsize=16,fontweight='bold',color=INK,va='top')
fig.text(0.075,0.875,'120 semiconductor stocks vs all stocks in our dashboard universe, Aug 3 – Oct 2, 2026.',fontsize=10,color=SUB,va='top')
fig.text(0.075,0.845,'Only one of the 120 made a new 52-week high in these 44 sessions.',fontsize=10,color=SUB,va='top')
fig.text(0.075,0.035,'Data: Fluxus dashboard breadth series, Oct 2 close · semis = three semiconductor theme groups combined',fontsize=8.5,color=SUB)
fig.text(0.97,0.035,'@Fluxus_Z',fontsize=9.5,color=INK,fontweight='bold',ha='right')
fig.savefig(f'{S}/semis_vs_market_50dma_fluxus.png',facecolor='white')
print('ok',cross.date())
