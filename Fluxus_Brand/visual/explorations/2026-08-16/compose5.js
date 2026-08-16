const HO=R.find(r=>r.group==='High Octane');
block('Compare · 保留你原有的形状和渐变条，只在一处二选一',
 '你说得对，原版透露的概念就是「三个月前本来就不一样，然后慢慢变化」——那正是我上一轮的 α（全部归零起步）<b>抹掉</b>的东西。所以这一轮回到你原来的构造：<b>每个点是那一段里的相对强弱</b>，线天生从不同高度出发，单调三次插值让它平滑地变（和线上那张同一套算法，曲线永远不越过相邻测点的范围）。<b>渐变条原样保留</b>。窗口按你说的收到 3 个月，砍掉 3–6m 那段——仓库里 <code>segments.js</code> 早就写着它「在三个月之外，把一行加总没有意义」。<br><br>唯一要你选的是纵轴：<b>原始分段值</b>，还是<b>每日速度</b>。',
 [['读法 δ · 原始分段值','y = 那一段里跑赢 SPY 多少（你现在线上的口径）',replayable(chart('seg')),
   '和你截图里一样，三条线到右端会收拢——但那<b>不是</b>大家都在变弱，是三段的长度不同（61 天 / 23 天 / 7 天），短的那段数值天然就小。'],
  ['读法 γ · 每日速度','y = 每天跑赢 SPY 多少（分段值 ÷ 该段天数）· 三段口径统一',replayable(chart('rate')),
   '收拢消失了。而且它的纵轴<b>就是 Field 象限的纵轴（加速度）</b>——上下两层会互相印证，而不是各说各话。']],
 `<div class="warn"><b>为什么我建议 γ</b>，用你截图里那条数据说：<b>High Octane</b> 原始分段是
  ${HO?HO.seg.map(v=>fmtPct(v,1)).join(' → '):''}，看起来像<b>崩塌</b>；
  换成每日速度是 ${HO?HO.rate.map(v=>(v*100).toFixed(2)+'%').join(' → '):''}，
  <b>三段几乎一模一样，它根本没有减速</b>。那个"崩塌"完全是段越来越短造成的假象。
  δ 会让几乎每一个主题看起来都在褪色，而这是一个读图的人最容易做错决定的地方。</div>`);

block('对照 · 两种读法下，同样四条线说的话',
 '把四个主题在两种纵轴下的数字并排放。这不是配色或排版问题，是<b>同一份数据被读成两件事</b>。',
 [['数字对照',' ', (()=>{
   let t='<table style="width:100%;border-collapse:collapse;font-size:11.5px">'
    +'<tr><th style="text-align:left;padding:6px 8px;border-bottom:1.5px solid var(--ink)">主题</th>'
    +LAB.map(l=>`<th style="padding:6px 8px;border-bottom:1.5px solid var(--ink)">${l} <span class="mono" style="color:var(--mut);font-weight:400">原始</span></th>`).join('')
    +LAB.map(l=>`<th style="padding:6px 8px;border-bottom:1.5px solid var(--ink);background:color-mix(in srgb,var(--took) 6%,transparent)">${l} <span class="mono" style="color:var(--mut);font-weight:400">每日</span></th>`).join('')
    +'<th style="text-align:left;padding:6px 8px;border-bottom:1.5px solid var(--ink)">两种读法的差别</th></tr>';
   const NOTE={'High Octane':'原始像崩塌 · 每日<b>纹丝不动</b>','Drones':'两种读法一致：第二段爆发',
     'Cybersecurity':'原始像放缓 · 每日<b>已经转负</b>','Silver':'两种读法一致：来回抽'};
   PICKS.forEach(r=>{t+=`<tr><td style="padding:5px 8px;border-bottom:1px solid var(--line);font-weight:600">${esc(r.group)}</td>`
    +r.seg.map(v=>`<td class="mono" style="text-align:center;padding:5px 8px;border-bottom:1px solid var(--line);color:${v>0?'var(--took)':'var(--refused)'}">${fmtPct(v,1)}</td>`).join('')
    +r.rate.map(v=>`<td class="mono" style="text-align:center;padding:5px 8px;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--took) 6%,transparent);color:${v>0?'var(--took)':'var(--refused)'}">${(v*100).toFixed(2)}%</td>`).join('')
    +`<td style="padding:5px 8px;border-bottom:1px solid var(--line);color:var(--mut)">${NOTE[r.group]||''}</td></tr>`;});
   return t+'</table>';})()]]);
