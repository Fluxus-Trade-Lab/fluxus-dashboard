const R=D.rows, DAYS=D.days, LEG=D.legLabels;
const SORTED=[...R].sort((a,b)=>b.excess_3m-a.excess_3m);
const MX=Math.max(...R.map(r=>Math.abs(r.excess_3m)));
const MA=Math.max(...R.map(r=>Math.abs(r.rs_accel||0)));
const CMAX=Math.max(...R.flatMap(r=>r.cum.map(Math.abs)))*0.78;
const INK='var(--ink)',SEC='var(--sec)',MUT='var(--mut)',LINE='var(--line)',
      TOOK='var(--took)',REF='var(--refused)';
const pol=v=>v>0?TOOK:REF;
const fmtPct=(v,d=0)=>v==null?'—':(v>0?'+':'')+(v*100).toFixed(d)+'%';
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const ramp=t=>{const g=Math.round(210-Math.max(0,Math.min(1,t))*180);return `rgb(${g},${g-4},${g-10})`};
const PICKS=['High Octane','Cybersecurity','Drones','Regional Banks']
  .map(n=>R.find(r=>r.group===n)).filter(Boolean);
const el=s=>{const d=document.createElement('div');d.innerHTML=s.trim();return d.firstChild};
const app=document.getElementById('app');
let UID=0;
function block(title,why,opts,extra){
  const b=el('<section class="block"></section>');
  b.appendChild(el('<h2>'+title+'</h2>'));
  b.appendChild(el('<p class="why">'+why+'</p>'));
  if(extra) b.insertAdjacentHTML('beforeend',extra);
  opts.forEach(([tag,note,svg,foot])=>{
    const o=el('<div class="opt"></div>');
    o.appendChild(el('<div class="opt-h"><b>'+tag+'</b><span>'+note+'</span></div>'));
    const c=el('<div class="card"></div>'); c.innerHTML=svg; o.appendChild(c);
    if(foot) o.insertAdjacentHTML('beforeend','<p class="note">'+foot+'</p>');
    b.appendChild(o);
  });
  app.appendChild(b);
}
/* 重播按钮：把卡片里的 SVG 重新插入一次，动画即重跑 */
function replayable(html,label='重播'){
  const id='rp'+(++UID);
  return `<div id="${id}">${html}</div><button class="replay" onclick="(()=>{const n=document.getElementById('${id}');n.innerHTML=n.innerHTML})()">▶ ${label}</button>`;
}

/* ================= 定稿 1 · FIELD = 象限（三个细化） ================= */
function quad(opts={}){
  const {edge=false,tail=false,label=4,W=1080,H=430,P=64}=opts;
  const X=v=>P+((v+MX)/(2*MX))*(W-P*2), Y=v=>P+(1-((v+MA)/(2*MA)))*(H-P*2);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<rect x="${X(0)}" y="${P}" width="${W-P-X(0)}" height="${Y(0)-P}" fill="${TOOK}" opacity=".045"/>`;
  if(edge){ // 边缘直方：把两条轴上的密度画出来，象限里就不必再猜"中间挤了多少"
    const NB=26,bw=(W-P*2)/NB, bins=Array(NB).fill(0);
    R.forEach(r=>bins[Math.min(NB-1,Math.floor(((r.excess_3m+MX)/(2*MX))*NB))]++);
    const mb=Math.max(...bins);
    bins.forEach((n,i)=>{if(!n)return;const h=(n/mb)*30;
      s+=`<rect x="${P+i*bw+0.8}" y="${P-6-h}" width="${bw-1.6}" height="${h}" rx="1.5" fill="${MUT}" opacity=".3"/>`;});
    const NV=18,bh=(H-P*2)/NV, vb=Array(NV).fill(0);
    R.forEach(r=>vb[Math.min(NV-1,Math.floor((((r.rs_accel||0)+MA)/(2*MA))*NV))]++);
    const mv=Math.max(...vb);
    vb.forEach((n,i)=>{if(!n)return;const w=(n/mv)*30;
      s+=`<rect x="${P-8-w}" y="${H-P-(i+1)*bh+0.8}" width="${w}" height="${bh-1.6}" rx="1.5" fill="${MUT}" opacity=".3"/>`;});
  }
  s+=`<line x1="${X(0)}" y1="${P}" x2="${X(0)}" y2="${H-P}" stroke="${INK}" stroke-width="1.1"/>`;
  s+=`<line x1="${P}" y1="${Y(0)}" x2="${W-P}" y2="${Y(0)}" stroke="${INK}" stroke-width="1.1"/>`;
  [['还在扩大的领先',X(0)+14,P+18,'start'],['正在褪色的领先',X(0)+14,H-P-10,'start'],
   ['落后但在转强',X(0)-14,P+18,'end'],['落后且继续弱',X(0)-14,H-P-10,'end']]
   .forEach(([t,x,y,a])=>s+=`<text x="${x}" y="${y}" text-anchor="${a}" font-size="10.5" fill="${MUT}">${t}</text>`);
  const pts=R.map(r=>({r,cx:X(r.excess_3m),cy:Y(r.rs_accel||0),rr:2.4+Math.sqrt(r.members||1)*0.5}));
  if(tail){ // 小尾巴：从"上一段的强弱"指到"这一段"，方向就是它在往哪个象限走
    pts.forEach(p=>{const prev=p.r.cum[3]-p.r.cum[2];
      const px=X(Math.max(-MX,Math.min(MX,p.r.excess_3m-(p.r.legs[3]||0)*1.6)));
      s+=`<line x1="${px}" y1="${p.cy}" x2="${p.cx}" y2="${p.cy}" stroke="${pol(p.r.legs[3]||0)}" stroke-width="1" opacity=".35"/>`;});
  }
  pts.forEach(p=>{const lead=p.r.excess_3m>0, acc=(p.r.rs_accel||0)>0;
    const solid=lead&&acc?TOOK:(!lead&&!acc?REF:null);
    s+=`<circle cx="${p.cx}" cy="${p.cy}" r="${p.rr.toFixed(2)}" fill="${solid||'none'}" stroke="${solid?'none':SEC}"
        stroke-width="1.1" fill-opacity=".8"><title>${esc(p.r.group)} ${fmtPct(p.r.excess_3m)} · accel ${fmtPct(p.r.rs_accel,1)}</title></circle>`;});
  const q=(l,a)=>pts.filter(p=>(p.r.excess_3m>0)===l&&((p.r.rs_accel||0)>0)===a)
    .sort((x,y)=>(Math.abs(y.r.excess_3m)+Math.abs(y.r.rs_accel||0))-(Math.abs(x.r.excess_3m)+Math.abs(x.r.rs_accel||0)));
  const named=[]; [[1,1],[1,0],[0,1],[0,0]].forEach(([l,a])=>{
    q(!!l,!!a).slice(0,label/4|0||1).forEach(p=>named.push(p));});
  const used=[];
  named.forEach(p=>{let y=p.cy-9; while(used.some(u=>Math.abs(u-y)<13))y-=13; used.push(y);
    s+=`<line x1="${p.cx}" y1="${p.cy-p.rr}" x2="${p.cx}" y2="${y+3}" stroke="${LINE}"/>`;
    s+=`<text x="${p.cx+6}" y="${y}" font-size="10.5" font-weight="600" fill="${INK}">${esc(p.r.group)}</text>`;});
  const hot=pts.filter(p=>p.r.excess_3m>0&&(p.r.rs_accel||0)>0).length;
  s+=`<text x="${W-P}" y="${P-16}" text-anchor="end" class="mono" font-size="10" fill="${SEC}">这一格 ${hot} 个 / 全场 ${R.length}</text>`;
  s+=`<text x="${W-P}" y="${H-P+20}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">3M 超额 →</text>`;
  s+=`<text x="${P}" y="${P-16}" class="mono" font-size="9" fill="${MUT}">↑ 还在加速</text>`;
  return s+'</svg>';
}

/* ================= 定稿 2 · RANKED = 零线居中分岔（三个细化） ================= */
function diverge(opts={}){
  const {n=14,members=false,legs=false}=opts;
  const show=[...SORTED.slice(0,n),null,...SORTED.slice(-n)];
  const W=1080,rh=19,H=show.length*rh+30,C=legs?400:470,HALF=legs?300:372;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${C}" y1="6" x2="${C}" y2="${H-18}" stroke="${INK}" stroke-width="1.1"/>`;
  [.2,.4].forEach(t=>[1,-1].forEach(g=>{const x=C+g*(t/MX)*HALF;
    s+=`<line x1="${x}" y1="6" x2="${x}" y2="${H-18}" stroke="${LINE}" stroke-dasharray="2 4"/>`
     +`<text x="${x}" y="${H-4}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${fmtPct(g*t)}</text>`;}));
  show.forEach((r,i)=>{const y=10+i*rh;
    if(!r){s+=`<text x="${C}" y="${y+11}" text-anchor="middle" class="mono" font-size="10" fill="${LINE}">· · ·  ${SORTED.length-2*n} more  · · ·</text>`;return;}
    const w=(Math.abs(r.excess_3m)/MX)*HALF,pos=r.excess_3m>0,x=pos?C:C-w;
    s+=`<rect x="${x}" y="${y}" width="${Math.max(1.5,w)}" height="12" rx="3" fill="${pol(r.excess_3m)}"/>`;
    s+=`<text x="${pos?C-9:C+9}" y="${y+10}" text-anchor="${pos?'end':'start'}" font-size="10.5" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${pos?x+w+8:x-8}" y="${y+10}" text-anchor="${pos?'start':'end'}" class="mono" font-size="10" fill="${SEC}">${fmtPct(r.excess_3m)}</text>`;
    if(members){const tag=r.proxy?('ETF 代理 '+(r.tickers1||'')):(r.members<20?r.members+' names · 篮子很小':r.members+' names');
      s+=`<text x="${W-4}" y="${y+10}" text-anchor="end" class="mono" font-size="9" fill="${r.members<20?REF:MUT}">${tag}</text>`;}
    if(legs){const bx=W-244,bw=54;
      r.legs.forEach((v,j)=>{const hh=Math.min(11,Math.abs(v)/0.36*11);
        s+=`<rect x="${bx+j*bw+2}" y="${y+6-(v>0?hh:0)}" width="${bw-6}" height="${Math.max(1.2,hh)}"
             fill="${pol(v)}" fill-opacity=".8"><title>${LEG[j]} ${fmtPct(v,1)}</title></rect>`;});
      s+=`<line x1="${bx}" y1="${y+6}" x2="${bx+4*bw-4}" y2="${y+6}" stroke="${LINE}" stroke-width=".7"/>`;}
  });
  if(legs)LEG.forEach((l,j)=>s+=`<text x="${W-244+j*54+24}" y="6" text-anchor="middle" class="mono" font-size="8" fill="${LINE}">${l}</text>`);
  return s+'</svg>';
}

/* ========== 路线 A · 一张图，x = 真日历时间，y = 累计相对强弱 ========== */
function curve(opts={}){
  const {shade=false,burst=false,ghost=true,W=1080,H=340,L=64,Rp=210,T=26,B=46}=opts;
  const d0=DAYS[0], X=day=>L+((day-d0)/(0-d0))*(W-L-Rp);
  const Y=v=>T+(1-(Math.max(-CMAX,Math.min(CMAX,v))+CMAX)/(2*CMAX))*(H-T-B);
  const path=r=>r.cum.map((v,i)=>`${X(DAYS[i]).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${L}" y1="${Y(0)}" x2="${W-Rp}" y2="${Y(0)}" stroke="${INK}" stroke-width="1"/>`;
  s+=`<text x="${L-8}" y="${Y(0)+3}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  [.2,.4,-.2].forEach(t=>{if(Math.abs(t)<CMAX)
    s+=`<line x1="${L}" y1="${Y(t)}" x2="${W-Rp}" y2="${Y(t)}" stroke="${LINE}" stroke-dasharray="2 4"/>`
     +`<text x="${L-8}" y="${Y(t)+3}" text-anchor="end" class="mono" font-size="9" fill="${LINE}">${fmtPct(t)}</text>`;});
  DAYS.forEach((dd,i)=>{s+=`<line x1="${X(dd)}" y1="${T}" x2="${X(dd)}" y2="${H-B}" stroke="${LINE}" stroke-width=".7" opacity=".8"/>`;
    const lab=['6个月前','3个月前','1个月前','1周前','今天'][i];
    s+=`<text x="${X(dd)}" y="${H-B+17}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${lab}</text>`;});
  if(ghost) R.forEach(r=>s+=`<polyline points="${path(r)}" fill="none" stroke="${LINE}" stroke-width=".7" opacity=".5"/>`);
  const used=[];
  PICKS.forEach((r,pi)=>{
    const c=pol(r.cum[4]);
    if(shade){const area=`${X(d0)},${Y(0)} `+path(r)+` ${X(0)},${Y(0)}`;
      s+=`<polygon points="${area}" fill="${c}" opacity=".07"/>`;}
    if(burst){ // 爆发段加粗：哪一段跑得最快，那一段就最粗
      const mx=Math.max(...r.legs.map(Math.abs));
      r.legs.forEach((v,i)=>{const w=1.2+Math.abs(v)/mx*3.6;
        s+=`<line x1="${X(DAYS[i])}" y1="${Y(r.cum[i])}" x2="${X(DAYS[i+1])}" y2="${Y(r.cum[i+1])}"
             stroke="${c}" stroke-width="${w.toFixed(2)}" stroke-linecap="round"/>`;});
    } else {
      s+=`<polyline points="${path(r)}" fill="none" stroke="${c}" stroke-width="2.5" stroke-linejoin="round"
           stroke-dasharray="2400" stroke-dashoffset="2400">
           <animate attributeName="stroke-dashoffset" from="2400" to="0" dur="1.35s" begin="${(pi*0.16).toFixed(2)}s" fill="freeze"/></polyline>`;
    }
    r.cum.forEach((v,i)=>s+=`<circle cx="${X(DAYS[i])}" cy="${Y(v)}" r="${i===4?4.4:2.4}" fill="${c}" opacity="0">
       <animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(pi*0.16+0.28*i).toFixed(2)}s" fill="freeze"/></circle>`);
    let ly=Y(r.cum[4]); while(used.some(u=>Math.abs(u-ly)<26)) ly-=26; used.push(ly);
    s+=`<text x="${W-Rp+12}" y="${ly+3}" font-size="11.5" font-weight="600" fill="${c}" opacity="0">${esc(r.group)}
         <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="${(pi*0.16+1.2).toFixed(2)}s" fill="freeze"/></text>`;
    s+=`<text x="${W-Rp+12}" y="${ly+16}" class="mono" font-size="9.5" fill="${MUT}" opacity="0">6个月累计 ${fmtPct(r.cum[4],1)} · ${r.members}n
         <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="${(pi*0.16+1.3).toFixed(2)}s" fill="freeze"/></text>`;
  });
  s+=`<text x="${L}" y="14" class="mono" font-size="9" fill="${MUT}">纵轴 = 从 6 个月前起，相对 SPY 累计领先/落后 · 横轴按真实日历间距，所以最近三段被压得很窄——那正是它本来的样子</text>`;
  return s+'</svg>';
}

/* ========== 路线 B · 100 米赛道：谁在哪一段爆发，之后守不守得住 ========== */
function race(opts={}){
  const {mode='lane',n=8}=opts;
  const runners=[...R].sort((a,b)=>b.cum[4]-a.cum[4]).slice(0,n);
  const W=1080,rh=mode==='lane'?46:40,H=runners.length*rh+66,L=250,TRACK=W-L-118;
  // 落后区：被 SPY 拖到起跑线以后，是这张图最该让人看见的东西之一
  // （Drones 前两段就在这里），所以不钳位，给左边留出真实空间。
  const BEHIND=88;
  const total=Math.max(...R.map(r=>r.legs.reduce((s,v)=>s+Math.max(0,v),0)));
  const step=v=>(v/total)*(TRACK/1.15);
  const posAt=(r,j)=>L+r.legs.slice(0,j).reduce((a,b)=>a+step(b),0);
  const DUR=[1.0,1.0,1.0,1.0], GAP=0.12;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  // 分段计时线：四道栏
  let acc=0; const marks=[];
  for(let j=0;j<4;j++){acc+=1; marks.push(L+TRACK*(j+1)/4);}
  marks.forEach((x,j)=>{s+=`<line x1="${x}" y1="26" x2="${x}" y2="${H-40}" stroke="${LINE}" stroke-dasharray="3 4"/>`;
    s+=`<text x="${x}" y="20" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${LEG[j]} 结束</text>`;});
  s+=`<line x1="${L}" y1="26" x2="${L}" y2="${H-40}" stroke="${INK}" stroke-width="1.4"/>`;
  s+=`<text x="${L}" y="20" text-anchor="middle" class="mono" font-size="9" fill="${INK}">起跑 · SPY</text>`;
  s+=`<text x="${L-BEHIND/2}" y="${H-26}" text-anchor="middle" class="mono" font-size="8.5" fill="${REF}">← 落后区</text>`;
  runners.forEach((r,i)=>{
    const y=34+i*rh;
    s+=`<rect x="${L-BEHIND}" y="${y}" width="${TRACK+BEHIND}" height="${rh-14}" rx="${(rh-14)/2}" fill="${LINE}" opacity=".22"/>`;
    s+=`<text x="${L-BEHIND-12}" y="${y+(rh-14)/2+4}" text-anchor="end" font-size="11.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    // 每一段跑出的距离 = 该段正超额（负的就是被拖回来）
    let x=L, t=0;
    r.legs.forEach((v,j)=>{
      const dist=step(v);
      const x2=x+dist;   // 不钳位：负的那段真的把人拖回起跑线以后
      const c=v>0?TOOK:REF;
      s+=`<rect x="${Math.min(x,x2)}" y="${y+2}" width="0" height="${rh-18}" rx="${(rh-18)/2}"
           fill="${c}" fill-opacity="${(0.38+j*0.2).toFixed(2)}">
           <animate attributeName="width" from="0" to="${Math.abs(x2-x).toFixed(1)}" dur="${DUR[j]}s" begin="${(t).toFixed(2)}s" fill="freeze"/></rect>`;
      if(Math.abs(x2-x)>46)
        s+=`<text x="${(Math.min(x,x2)+Math.abs(x2-x)/2).toFixed(1)}" y="${y+(rh-14)/2+3}" text-anchor="middle" class="mono"
             font-size="8.5" fill="#f2f0e9" opacity="0">${fmtPct(v,0)}
             <animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(t+DUR[j]*0.7).toFixed(2)}s" fill="freeze"/></text>`;
      x=x2; t+=DUR[j]+GAP;
    });
    // 跑者
    s+=`<circle cy="${y+(rh-14)/2}" r="${5.5+Math.sqrt(r.members)*0.22}" fill="${pol(r.cum[4])}" cx="${L}">
        ${r.legs.map((v,j)=>`<animate attributeName="cx" from="${posAt(r,j).toFixed(1)}" to="${posAt(r,j+1).toFixed(1)}" dur="${DUR[j]}s" begin="${(j*(DUR[j]+GAP)).toFixed(2)}s" fill="freeze"/>`).join('')}
        </circle>`;
    const fin=posAt(r,4);
    s+=`<text x="${W-104}" y="${y+(rh-14)/2+4}" class="mono" font-size="10.5" fill="${pol(r.cum[4])}" opacity="0">${fmtPct(r.cum[4],1)}
         <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="4.5s" fill="freeze"/></text>`;
    // 最大爆发段做个记号
    const bi=r.legs.indexOf(Math.max(...r.legs));
    if(r.legs[bi]>0.08){
      const bx=posAt(r,bi)+step(r.legs[bi])/2;
      s+=`<text x="${bx}" y="${y-1}" text-anchor="middle" class="mono" font-size="8" fill="${MUT}" opacity="0">爆发
          <animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(bi*(1+GAP)+0.9).toFixed(2)}s" fill="freeze"/></text>`;}
  });
  s+=`<text x="${L}" y="${H-16}" class="mono" font-size="9.5" fill="${MUT}">每一段跑出的距离 = 该段相对 SPY 的领先；负的那段会把跑者往回拖 · 四道虚线是分段计时点</text>`;
  return s+'</svg>';
}
