/* ================= 打分 + 两个合成版 ================= */
// 修掉实测发现的缺陷后重画的几何
function F_quadrant2(){
  const W=1080,H=430,P=64;
  const X=v=>P+((v+MX)/(2*MX))*(W-P*2), Y=v=>P+(1-((v+MA)/(2*MA)))*(H-P*2);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  // 极淡的象限底，只留一格：还在加速的领先者——这一格才是要找的东西
  s+=`<rect x="${X(0)}" y="${P}" width="${W-P-X(0)}" height="${Y(0)-P}" fill="${TOOK}" opacity=".045"/>`;
  s+=`<line x1="${X(0)}" y1="${P}" x2="${X(0)}" y2="${H-P}" stroke="${INK}" stroke-width="1.1"/>`;
  s+=`<line x1="${P}" y1="${Y(0)}" x2="${W-P}" y2="${Y(0)}" stroke="${INK}" stroke-width="1.1"/>`;
  [['还在扩大的领先',X(0)+14,P+18,'start'],['正在褪色的领先',X(0)+14,H-P-10,'start'],
   ['落后但在转强',X(0)-14,P+18,'end'],['落后且继续弱',X(0)-14,H-P-10,'end']]
   .forEach(([t,x,y,a])=>s+=`<text x="${x}" y="${y}" text-anchor="${a}" font-size="10.5" fill="${MUT}">${t}</text>`);
  const pts=R.map(r=>({r,cx:X(r.excess_3m),cy:Y(r.rs_accel??0),rr:2.4+Math.sqrt(r.members||1)*0.5}));
  pts.forEach(p=>{const lead=p.r.excess_3m>0, acc=(p.r.rs_accel??0)>0;
    const solid=lead&&acc?TOOK:(!lead&&!acc?REF:null);
    s+=`<circle cx="${p.cx}" cy="${p.cy}" r="${p.rr.toFixed(2)}" fill="${solid||'none'}"
        stroke="${solid?'none':SEC}" stroke-width="1.1" fill-opacity=".8"><title>${esc(p.r.group)} ${fmtPct(p.r.excess_3m)} · accel ${fmtPct(p.r.rs_accel,1)}</title></circle>`;});
  // 只给四个象限各一个代表命名，且垂直去碰撞
  const pick=[]; const q=(lead,acc)=>pts.filter(p=>(p.r.excess_3m>0)===lead&&((p.r.rs_accel??0)>0)===acc)
    .sort((a,b)=>Math.abs(b.r.excess_3m)+Math.abs(b.r.rs_accel??0)-(Math.abs(a.r.excess_3m)+Math.abs(a.r.rs_accel??0)))[0];
  [[1,1],[1,0],[0,1],[0,0]].forEach(([l,a])=>{const p=q(!!l,!!a); if(p)pick.push(p);});
  const used=[];
  pick.forEach(p=>{let y=p.cy-9; while(used.some(u=>Math.abs(u-y)<13)) y-=13; used.push(y);
    s+=`<line x1="${p.cx}" y1="${p.cy-p.rr}" x2="${p.cx}" y2="${y+3}" stroke="${LINE}"/>`;
    s+=`<text x="${p.cx+6}" y="${y}" font-size="10.5" font-weight="600" fill="${INK}">${esc(p.r.group)}</text>`;});
  const hot=pts.filter(p=>p.r.excess_3m>0&&(p.r.rs_accel??0)>0).length;
  s+=`<text x="${W-P}" y="${P-16}" text-anchor="end" class="mono" font-size="10" fill="${SEC}">这一格 ${hot} 个 / 全场 ${R.length}</text>`;
  s+=`<text x="${W-P}" y="${H-P+20}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">3M 超额 →</text>`;
  s+=`<text x="${P}" y="${P-16}" class="mono" font-size="9" fill="${MUT}">↑ 还在加速</text>`;
  return s+'</svg>';
}
function C_cards2(picks=PICKS){
  const W=1080,n=picks.length||1,cw=W/n,H=214;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  picks.forEach((r,pi)=>{const x0=cw*pi+12,w=cw-26;
    const Y=v=>72+(1-(Math.max(-SMAX,Math.min(SMAX,v))+SMAX)/(2*SMAX))*72;
    s+=`<rect x="${x0}" y="6" width="${w}" height="${H-16}" rx="18" fill="var(--bg)"/>`;
    s+=`<text x="${x0+16}" y="30" font-size="12.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${x0+16}" y="45" class="mono" font-size="9" fill="${MUT}">${r.members} names · ${r.state}</text>`;
    const X=i=>x0+22+i*((w-44)/3);
    s+=`<line x1="${x0+22}" y1="${Y(0)}" x2="${x0+w-22}" y2="${Y(0)}" stroke="${LINE}"/>`;
    s+=`<text x="${x0+w-22}" y="${Y(0)-4}" text-anchor="end" class="mono" font-size="8" fill="${LINE}">SPY</text>`;
    const pts=STRETCH.map(([k],i)=>[X(i),Y(r[k]??0)]), c=pol(r.rs_0_1w??0);
    s+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${c}" stroke-width="2.2" stroke-linejoin="round"/>`;
    pts.forEach((p,i)=>s+=`<circle cx="${p[0]}" cy="${p[1]}" r="${i===3?4:2.2}" fill="${c}"/>`);
    STRETCH.forEach(([,lab],i)=>s+=`<text x="${X(i)}" y="${H-40}" text-anchor="middle" class="mono" font-size="7.5" fill="${LINE}">${lab}</text>`);
    s+=`<text x="${x0+16}" y="${H-16}" class="mono" font-size="17" fill="${c}">${fmtPct(r.rs_0_1w,1)}</text>`;
    s+=`<text x="${x0+w-16}" y="${H-16}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">本周相对 SPY</text>`;});
  return s+'</svg>';
}
function R_type2(n=16){
  const rows=SORTED.slice(0,n),W=1080,rh=26,H=n*rh+36;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  rows.forEach((r,i)=>{const y=25+i*rh, t=r.excess_3m/MX;
    s+=`<text x="0" y="${y}" class="mono" font-size="9.5" fill="${LINE}">${String(i+1).padStart(2,'0')}</text>`;
    s+=`<text x="30" y="${y}" font-size="${(12+t*15).toFixed(1)}" font-weight="${t>0.55?700:(t>0.3?600:500)}"
         fill="${ramp(0.25+t*0.75)}" letter-spacing="-.01em">${esc(r.group)}</text>`;
    // 画出来才发现的事：members==1 的几条不是小主题，是用一只 ETF 代理整个主题
    // （Biotech=XBI、Taiwan=EWT、Healthcare=XLV）。榜单把一只 ETF 和一个 286 只
    // 的篮子并排排名，页面上却没有任何东西区分它们。所以不写 "1 names"。
    const tag = r.members===1 ? 'ETF \u4ee3\u7406'
      : (r.members<20 ? r.members+' names \u00b7 \u7bee\u5b50\u5f88\u5c0f' : r.members+' names');
    s+=`<text x="${W-238}" y="${y}" text-anchor="end" class="mono" font-size="9.5"
         fill="${r.members<20?REF:MUT}">${tag}</text>`;
    s+=`<text x="${W-96}" y="${y}" text-anchor="end" class="mono" font-size="${(10+t*5).toFixed(1)}" fill="${pol(r.excess_3m)}">${fmtPct(r.excess_3m)}</text>`;
    s+=pips(W-80,y-4,r,SEC);});
  s+=`<text x="0" y="${H-6}" class="mono" font-size="9.5" fill="${MUT}">字号与墨色就是柱长 · 写 ETF 代理的那几条，整个主题就是一只 ETF · 右侧五点 = 5 期里在榜几期</text>`;
  return s+'</svg>';
}
variant('V16 · 象限 / 卡片 / 字体排名　【打分后的合成版】',
 '打分的结论不是"选哪一个"，而是<b>没有一个变体三层全赢</b>。V02 的象限是唯一给出新信息的 Field；V08/V14 的卡片是读得最快、且唯一不会撞标签的 Compare；V05 的字体排名是密度最高的 Ranked。这一版把三者合起来，并修掉实测到的缺陷：象限底色从两块压到一块（只留"还在扩大的领先"），四个象限各点名一个代表并做垂直去碰撞；榜单加上成员数，少于 20 的标红——这是 V06 树图教我的，并且画出来之后多捡到一件事：榜上 members==1 的三条是<b>用一只 ETF 代理整个主题</b>（XBI / EWT / XLV），页面把它和一个 286 只的篮子并排排名。原本的说法是"一个 3 只股票的主题也能排第一"。',
 [['Field','x = 3M 超额 · y = 加速度 · 只有一格是要找的',F_quadrant2()],
  ['Compare','每个选中一张卡片 · 共用刻度 · 不会撞标签',C_cards2()],
  ['Ranked','字号即长度 · 成员数 < 20 标红',R_type2(16)]]);

variant('V17 · 树图 / 卡片 / 分岔　【体量优先的合成版】',
 'V16 的替代路线。如果认为页面最该先说的是<b>体量</b>而不是加速度，就用树图开场：Small Caps 1583 只、High Beta 1057 只，两块巨大的浅色格子只跑赢 SPY 5% 和 2%；而 +47% 的 52-Week High Leaders 只是一小格 88 只。柱状图会把这两件事画得一样长，树图不会。',
 [['Field','格子面积 = 成员数 · 浓度 = 超额',F_treemap()],
  ['Compare','每个选中一张卡片',C_cards2()],
  ['Ranked','零线居中 · 左右各 14',R_diverge(14)]]);

/* ---------- 打分表 ---------- */
const SC=[
 ['V01 蜂群/斜率/分岔',4,2,5,4,5,3,'Compare 右缘标签互相压字'],
 ['V02 象限/名次/热行',4,5,4,4,5,4,'象限底色过重；右缘标签撞车'],
 ['V03 点阵/花瓣/巨柱',3,2,3,4,4,5,'玫瑰四朵形状太像，比不出来；中间浅点几乎不可见'],
 ['V04 山脊/接力棒/梳子',5,3,5,5,3,3,'接力棒用 |v| 当长度，跑输的段也画得长——长度骗人'],
 ['V05 状态行/哑铃/字体',4,2,3,5,5,4,'哑铃的数值压在连线上'],
 ['V06 树图/瀑布/迁移',3,5,5,4,4,4,'名次迁移右侧标签整叠塌陷，基本不可读'],
 ['V07 放射/轨道/层叠',2,1,4,3,2,5,'轨道按角度摆放，距离无法互相比较；层叠柱丢了配对色'],
 ['V08 胶囊/卡片/象形',5,2,2,5,5,4,'胶囊只画了 24 条，那是排名不是全场'],
 ['V09 华夫/接力棒/拱顶',3,1,2,4,3,4,'华夫只答"成色"，不答"多强"；接力棒同 V04 的病'],
 ['V10 象限/玫瑰/分岔',3,4,4,4,4,4,'玫瑰拖后腿'],
 ['V11 蜂群/轨道/热行',3,3,4,3,4,4,'轨道同 V07'],
 ['V12 点阵/名次/象形',4,3,3,5,5,3,'三层都靠"数个数"，缺一个能看趋势的'],
 ['V13 树图/哑铃/梳子',3,4,5,4,4,3,'哑铃同 V05'],
 ['V14 山脊/卡片/字体',5,2,4,5,5,4,'三层都好读，但没有一层给出新信息'],
 ['V15 状态行/瀑布/层叠',3,2,4,3,3,3,'层叠柱丢配对色；整体偏平'],
 ['V16 象限/卡片/字体 ★',5,5,4,5,5,4,'合成版：缺陷已修'],
 ['V17 树图/卡片/分岔 ★',4,5,5,4,5,4,'合成版：树图的行高不均、小格标签溢出仍在'],
];
const HEAD=['变体','读数速度','信息增量','密度诚实','灰度存活','宪章符合','视觉张力','合计','实测缺陷'];
let t='<section class="variant"><h2>打分（0–5 × 6 项）</h2>'
 +'<p class="why">不是审美投票。六项里有四项是可验证的：能不能在 3 秒内读出主答案、有没有说出旧页面说不出的话、'
 +'76 条会不会挤成一团或被截断、转成灰度还认不认得出、颜色有没有在不表达含义的地方出现。'
 +'最后一项"视觉张力"是主观的，我给它和其它项一样的权重，不多不少。</p>'
 +'<div class="card" style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;font-size:11.5px">'
 +'<tr>'+HEAD.map((h,i)=>`<th style="text-align:${i===0||i===8?'left':'center'};padding:6px 8px;border-bottom:1.5px solid var(--ink);font-weight:600;white-space:nowrap">${h}</th>`).join('')+'</tr>';
SC.map(r=>[...r.slice(0,7),r.slice(1,7).reduce((a,b)=>a+b,0),r[7]])
  .sort((a,b)=>b[7]-a[7])
  .forEach(r=>{const star=r[0].includes('★');
   t+=`<tr style="${star?'background:color-mix(in srgb,var(--took) 7%,transparent)':''}">`
    +`<td style="padding:5px 8px;border-bottom:1px solid var(--line);white-space:nowrap;font-weight:${star?600:400}">${r[0]}</td>`
    +r.slice(1,7).map(v=>`<td style="text-align:center;padding:5px 8px;border-bottom:1px solid var(--line);color:${v<=2?'var(--refused)':(v>=5?'var(--took)':'var(--sec)')}" class="mono">${v}</td>`).join('')
    +`<td style="text-align:center;padding:5px 8px;border-bottom:1px solid var(--line);font-weight:600" class="mono">${r[7]}</td>`
    +`<td style="padding:5px 8px;border-bottom:1px solid var(--line);color:var(--mut)">${r[8]}</td></tr>`;});
t+='</table></div><p class="note">缺陷列全部是<b>渲染出来看到的</b>，不是预判的。V06 的名次迁移我原本以为是这批里最聪明的一张，'
 +'画出来才发现 18 条线的右端全部塌在一起——因为我拿全场 76 名去定纵坐标，却只画了 18 条。</p></section>';
app.insertAdjacentHTML('afterbegin',t);
