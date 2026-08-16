block('定稿 · FIELD = 象限（不变）',
 '你已经定了：不比体量，比「领先多少 × 还在不在加速」。这一层这轮没动，放在这里只是为了让整页能连着看。上一轮的三个细化（干净 / 边缘直方 / 尾巴）还在第二轮那份文件里。',
 [['象限','x = 3M 超额 · y = 加速度 · 每格一个代表', (()=>{
   const W=1080,H=390,P=58;
   const X=v=>P+((v+MX)/(2*MX))*(W-P*2), Y=v=>P+(1-((v+MA)/(2*MA)))*(H-P*2);
   let s=`<svg viewBox="0 0 ${W} ${H}">`;
   s+=`<rect x="${X(0)}" y="${P}" width="${W-P-X(0)}" height="${Y(0)-P}" fill="${TOOK}" opacity=".045"/>`;
   s+=`<line x1="${X(0)}" y1="${P}" x2="${X(0)}" y2="${H-P}" stroke="${INK}" stroke-width="1.1"/>`;
   s+=`<line x1="${P}" y1="${Y(0)}" x2="${W-P}" y2="${Y(0)}" stroke="${INK}" stroke-width="1.1"/>`;
   [['还在扩大的领先',X(0)+14,P+18,'start'],['正在褪色的领先',X(0)+14,H-P-10,'start'],
    ['落后但在转强',X(0)-14,P+18,'end'],['落后且继续弱',X(0)-14,H-P-10,'end']]
    .forEach(([t,x,y,a])=>s+=`<text x="${x}" y="${y}" text-anchor="${a}" font-size="10.5" fill="${MUT}">${t}</text>`);
   const pts=R.map(r=>({r,cx:X(r.excess_3m),cy:Y(r.rs_accel||0),rr:2.4+Math.sqrt(r.members||1)*0.5}));
   pts.forEach(p=>{const lead=p.r.excess_3m>0,acc=(p.r.rs_accel||0)>0;
     const solid=lead&&acc?TOOK:(!lead&&!acc?REF:null);
     s+=`<circle cx="${p.cx}" cy="${p.cy}" r="${p.rr.toFixed(2)}" fill="${solid||'none'}" stroke="${solid?'none':SEC}" stroke-width="1.1" fill-opacity=".8"><title>${esc(p.r.group)}</title></circle>`;});
   const q=(l,a)=>pts.filter(p=>(p.r.excess_3m>0)===l&&((p.r.rs_accel||0)>0)===a)
     .sort((x,y)=>(Math.abs(y.r.excess_3m)+Math.abs(y.r.rs_accel||0))-(Math.abs(x.r.excess_3m)+Math.abs(x.r.rs_accel||0)))[0];
   const used=[];
   [[1,1],[1,0],[0,1],[0,0]].forEach(([l,a])=>{const p=q(!!l,!!a);if(!p)return;
     let yy=p.cy-9;while(used.some(u=>Math.abs(u-yy)<13))yy-=13;used.push(yy);
     s+=`<line x1="${p.cx}" y1="${p.cy-p.rr}" x2="${p.cx}" y2="${yy+3}" stroke="${LINE}"/>`;
     s+=`<text x="${p.cx+6}" y="${yy}" font-size="10.5" font-weight="600" fill="${INK}">${esc(p.r.group)}</text>`;});
   const hot=pts.filter(p=>p.r.excess_3m>0&&(p.r.rs_accel||0)>0).length;
   s+=`<text x="${W-P}" y="${P-16}" text-anchor="end" class="mono" font-size="10" fill="${SEC}">这一格 ${hot} 个 / 全场 ${R.length}</text>`;
   return s+'</svg>';})()]]);

block('定稿 · RANKED = 零线居中（按你说的，去掉成员数与 ETF 代理）',
 '两个细化，都不再显示成员数、也不再标 ETF 代理。A 是纯净版；B 在右侧补三段迷你条，让人不点开就知道这条的领先是哪一段挣来的——三段和上面那张曲线是同一份数据。',
 [['细化 A','只有名字、条、数值',diverge()],
  ['细化 B','+ 三段迷你条（与 Compare 同源）',diverge({legs:true})]],
 '<p class="note">ETF 代理那件事我不画了，但它仍然是真的（Biotech=XBI、Taiwan=EWT、Healthcare=XLV），已经留在 DESIGN.md 里当数据侧的观察。</p>');

block('⚔️ Compare · 路线 A「曲线」——改成 3 个月',
 '窗口从 6 个月收到 3 个月，顺带解决了一个我上一轮没发现的矛盾：四段 <code>rs_*</code> 累加出来的终点，<b>和榜单印的 excess_3m 对不上</b>（领头的差 5–14%），因为 rs 是复利口径而累加是算术口径。这轮反解出了 SPY 的滚动收益（1W 0.428%、1M 4.446%、3M 5.299%，对全部 76 条<b>精确一致</b>），于是曲线上每个点都是实测的滚动超额，<b>终点精确等于榜单那个数</b>。两层不再打架。',
 [['A1 · 基础','全场 76 条底噪 + 选中四条 · 描线动画',replayable(curve())],
  ['A2 · 阴影','+ 曲线与零线之间填色',replayable(curve({shade:true}))],
  ['A3 · 爆发段加粗','线宽 = 该段跑多快 · 静态也读得懂，不依赖动画',curve({burst:true})]],
 '<div class="warn">四个点：3个月前 / 1个月前 / 1周前 / 今天，按<b>真实日历间距</b>排。点是测量，点之间是插值——真正的日线序列还不存在（归档只有 6 天，本地 OHLC 没有 SPY）。</div>');

block('⚔️ Compare · 路线 B「100 米赛道」——三段',
 '同一份数据的另一种讲法：三段依次推进，跑出的距离就是那一段相对 SPY 的领先，负的那段真的把人拖到起跑线以后。窗口收到 3 个月之后 <b>Drones</b> 反而更清楚：前两个月 −20.4% 一路在落后区，第二段 <b>+34.1% 爆发</b>，最后一周 +3.0% 守住。',
 [['B1 · 十条泳道','前 10 名',replayable(race({n:10}))],
  ['B2 · 十四条泳道','铺开一点，看得出集体节奏',replayable(race({n:14}))]]);

const SC=[
 ['A1 曲线 · 基础',5,4,5,5,5,3,'四条线尾端仍可能靠近（已做垂直去碰撞）'],
 ['A2 曲线 · 阴影',4,4,4,4,4,4,'四条叠加时面积互相糊，且面积在这里没有独立含义'],
 ['A3 曲线 · 爆发加粗',5,5,5,5,5,4,'线宽直接答"爆发在哪段"，静态成立'],
 ['B1 赛道 · 10 条',4,5,3,4,4,5,'只画 10 条，全场 76 的分布不见了'],
 ['B2 赛道 · 14 条',4,5,4,4,4,5,'同上，稍好'],
];
const H=['方案','读数速度','信息增量','密度诚实','灰度存活','宪章符合','视觉张力','合计','实测缺陷'];
let t='<section class="block"><h2>打分</h2><p class="why">窗口收到 3 个月之后，曲线的横轴变得均匀得多（91 / 30 / 7 天，不再被 182 天压扁），A 路线的读数速度和视觉张力都比上一轮好。赛道的优势没变——它回答的是另一个问题——劣势也没变：画不下 76 条。</p><div class="card" style="overflow-x:auto"><table><tr>'
 +H.map((h,i)=>`<th style="text-align:${i===0||i===8?'left':'center'}">${h}</th>`).join('')+'</tr>';
SC.map(r=>[...r.slice(0,7),r.slice(1,7).reduce((a,b)=>a+b,0),r[7]]).sort((a,b)=>b[7]-a[7])
 .forEach(r=>{const win=r[7]>=29;
  t+=`<tr style="${win?'background:color-mix(in srgb,var(--took) 7%,transparent)':''}"><td style="white-space:nowrap;font-weight:${win?600:400}">${r[0]}</td>`
   +r.slice(1,7).map(v=>`<td style="text-align:center;color:${v<=3?'var(--refused)':(v>=5?'var(--took)':'var(--sec)')}" class="mono">${v}</td>`).join('')
   +`<td style="text-align:center;font-weight:600" class="mono">${r[7]}</td><td style="color:var(--mut)">${r[8]}</td></tr>`;});
t+='</table></div><p class="note"><b>建议不变</b>：A3 当主图，B2 当点开单个主题后的第二眼。两者同源，不会互相矛盾。</p></section>';
app.insertAdjacentHTML('beforeend',t);
