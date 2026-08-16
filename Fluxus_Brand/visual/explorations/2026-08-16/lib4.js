const R=D.rows, SORTED=[...R].sort((a,b)=>b.excess_3m-a.excess_3m);
const MX=Math.max(...R.map(r=>Math.abs(r.excess_3m)));
const MA=Math.max(...R.map(r=>Math.abs(r.rs_accel||0)));
const INK='var(--ink)',SEC='var(--sec)',MUT='var(--mut)',LINE='var(--line)',
      TOOK='var(--took)',REF='var(--refused)';
const pol=v=>v>0?TOOK:REF;
const fmtPct=(v,d=0)=>v==null?'—':(v>0?'+':'')+(v*100).toFixed(d)+'%';
const fmtRate=v=>(v>0?'+':'')+(v*100).toFixed(2)+'%/日';
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const PICKS=['High Octane','Cybersecurity','Drones','Regional Banks'].map(n=>R.find(r=>r.group===n)).filter(Boolean);
/* 身份色：刻意避开配对的蓝红，它们只回答"这是哪一条"，永不回答"哪一边" */
const IDENT=['#6b7f8c','#8c7f6b','#7d6b8c','#6b8c7f'];
const el=s=>{const d=document.createElement('div');d.innerHTML=s.trim();return d.firstChild};
const app=document.getElementById('app');
let UID=0;
function block(title,why,opts,extra){
  const b=el('<section class="block"></section>');
  b.appendChild(el('<h2>'+title+'</h2>'));
  b.appendChild(el('<p class="why">'+why+'</p>'));
  if(extra)b.insertAdjacentHTML('beforeend',extra);
  opts.forEach(([tag,note,svg,foot])=>{
    const o=el('<div class="opt"></div>');
    o.appendChild(el('<div class="opt-h"><b>'+tag+'</b><span>'+note+'</span></div>'));
    const c=el('<div class="card"></div>');c.innerHTML=svg;o.appendChild(c);
    if(foot)o.insertAdjacentHTML('beforeend','<p class="note">'+foot+'</p>');
    b.appendChild(o);});
  app.appendChild(b);
}
function replayable(html,label='重播'){
  const id='rp'+(++UID);
  return `<div id="${id}">${html}</div><button class="replay" onclick="(()=>{const n=document.getElementById('${id}');n.innerHTML=n.innerHTML})()">▶ ${label}</button>`;
}

/* ============ Compare · 三种读法 ============
   α 累计式：全部从 3 个月前的 0 出发（我做的归一化）—— 答"这三个月谁走得远"
   β 回看式：y = 从那个时点持有到今天的超额（payload 原始数字，零加工）—— 答"从哪天上车、今天领先多少"
   γ 速度式：y = 每日超额速度（超额 ÷ 天数）—— 答"它在加速还是在减速"        */
const MODES={
  alpha:{pts:[-91,-30,-7,0],lab:['3个月前','1个月前','1周前','今天'],
    val:r=>r.cum, yfmt:v=>fmtPct(v,0),
    title:'累计式', desc:'全部从 3 个月前的 0 出发。终点 = 榜单印的数。这是<b>我做的归一化</b>。'},
  beta:{pts:[-91,-30,-7],lab:['3个月前上车','1个月前上车','1周前上车'],
    val:r=>[r.excess_3m,r.excess_1m,r.excess_1w], yfmt:v=>fmtPct(v,0),
    title:'回看式', desc:'y = 从那个时点持有到今天，比 SPY 多赚多少。<b>直接是 payload 里的三个数，零加工</b>。'},
  gamma:{pts:[-91,-30,-7],lab:['近3个月','近1个月','近1周'],
    val:r=>[r.excess_3m/91,r.excess_1m/30,r.excess_1w/7], yfmt:v=>(v*100).toFixed(2)+'%',
    title:'速度式', desc:'y = 每天挣到的超额（超额 ÷ 天数）。三个窗口口径统一，<b>向右上 = 在加速</b>。'}
};
function compare(mode,opts={}){
  const M=MODES[mode], {ident=false,ghost=true,W=1080,H=330,L=76,Rp=214,T=28,B=46}=opts;
  const vals=R.flatMap(r=>M.val(r)), lim=Math.max(...vals.map(Math.abs))*(mode==='alpha'?0.82:0.9);
  const xs=M.pts, d0=xs[0], dN=xs[xs.length-1];
  const X=d=>L+((d-d0)/(dN-d0))*(W-L-Rp);
  const Y=v=>T+(1-(Math.max(-lim,Math.min(lim,v))+lim)/(2*lim))*(H-T-B);
  const pathOf=r=>M.val(r).map((v,i)=>`${X(xs[i]).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${L}" y1="${Y(0)}" x2="${W-Rp}" y2="${Y(0)}" stroke="${INK}" stroke-width="1"/>`;
  s+=`<text x="${L-8}" y="${Y(0)+3}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  const ticks = mode==='gamma'?[0.005,-0.005]:[0.2,0.4,-0.2];
  ticks.forEach(t=>{if(Math.abs(t)<lim)
    s+=`<line x1="${L}" y1="${Y(t)}" x2="${W-Rp}" y2="${Y(t)}" stroke="${LINE}" stroke-dasharray="2 4"/>`
     +`<text x="${L-8}" y="${Y(t)+3}" text-anchor="end" class="mono" font-size="9" fill="${LINE}">${M.yfmt(t)}</text>`;});
  xs.forEach((dd,i)=>{s+=`<line x1="${X(dd)}" y1="${T}" x2="${X(dd)}" y2="${H-B}" stroke="${LINE}" stroke-width=".7" opacity=".85"/>`
   +`<text x="${X(dd)}" y="${H-B+17}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${M.lab[i]}</text>`;});
  if(ghost)R.forEach(r=>s+=`<polyline points="${pathOf(r)}" fill="none" stroke="${LINE}" stroke-width=".7" opacity=".5"/>`);
  const used=[];
  PICKS.forEach((r,pi)=>{
    const v=M.val(r), segs=v.length-1;
    const base = ident?IDENT[pi%IDENT.length]:pol(v[v.length-1]);
    // 线宽恒定；"跑得快"用墨色深浅表达，不用粗细（Andy 2026-08-16）
    const mag=v.map((x,i)=>i?Math.abs(v[i]-v[i-1]):0).slice(1);
    const mmax=Math.max(...mag,1e-9);
    for(let i=0;i<segs;i++){
      const t=mag[i]/mmax;                    // 0..1，这一段跑得多快
      const op=(0.34+t*0.66).toFixed(2);
      s+=`<line x1="${X(xs[i])}" y1="${Y(v[i])}" x2="${X(xs[i+1])}" y2="${Y(v[i+1])}"
           stroke="${base}" stroke-opacity="${op}" stroke-width="2.6" stroke-linecap="round"
           stroke-dasharray="900" stroke-dashoffset="900">
           <animate attributeName="stroke-dashoffset" from="900" to="0" dur="${(1.15/segs).toFixed(2)}s"
             begin="${(i*1.15/segs).toFixed(2)}s" fill="freeze"/></line>`;   /* 全部同时起跑：begin 不含 pi */
    }
    v.forEach((x,i)=>s+=`<circle cx="${X(xs[i])}" cy="${Y(x)}" r="${i===v.length-1?4.4:2.4}" fill="${base}" opacity="0">
      <animate attributeName="opacity" from="0" to="1" dur=".28s" begin="${(i*1.15/segs).toFixed(2)}s" fill="freeze"/></circle>`);
    let ly=Y(v[v.length-1]); while(used.some(u=>Math.abs(u-ly)<25))ly-=25; used.push(ly);
    s+=`<text x="${W-Rp+12}" y="${ly+3}" font-size="11.5" font-weight="600" fill="${base}" opacity="0">${esc(r.group)}
        <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="1.2s" fill="freeze"/></text>`;
    s+=`<text x="${W-Rp+12}" y="${ly+16}" class="mono" font-size="9.5" fill="${MUT}" opacity="0">${M.yfmt(v[v.length-1])}
        <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="1.28s" fill="freeze"/></text>`;});
  s+=`<text x="${L}" y="14" class="mono" font-size="9" fill="${MUT}">${M.title} · 线宽恒定，墨色深浅 = 这一段跑得多快 · 四条同时起跑</text>`;
  return s+'</svg>';
}

/* ============ Race · 零线居中 / 动态平衡 ============ */
function race(opts={}){
  const {n=12,rh=42}=opts;
  const runners=[...R].sort((a,b)=>b.excess_3m-a.excess_3m).slice(0,n);
  // 动态平衡：先量出被画的这些人真正会跑到哪、退到哪，再据此排版——没有人会跑出赛道
  let lo=0,hi=0;
  runners.forEach(r=>{let a=0;r.legs.forEach(v=>{a+=v;lo=Math.min(lo,a);hi=Math.max(hi,a);});});
  const pad=(hi-lo)*0.06 || 0.02;
  lo-=pad; hi+=pad;
  const W=1080,H=runners.length*rh+70,L=196,TRACK=W-L-116;
  const X=v=>L+((v-lo)/(hi-lo))*TRACK;      // v = 累计超额
  const ZERO=X(0);
  const posAt=(r,j)=>X(r.legs.slice(0,j).reduce((a,b)=>a+b,0));
  const DUR=1.0,GAP=.12;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<rect x="${L}" y="20" width="${ZERO-L}" height="${H-58}" fill="${REF}" opacity=".035"/>`;
  runners.forEach((r,i)=>{const y=36+i*rh;
    s+=`<rect x="${L}" y="${y}" width="${TRACK}" height="${rh-14}" rx="${(rh-14)/2}" fill="${LINE}" opacity=".2"/>`;
    s+=`<text x="${L-12}" y="${y+(rh-14)/2+4}" text-anchor="end" font-size="11" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    let acc=0,t=0;
    r.legs.forEach((v,j)=>{const x1=X(acc); acc+=v; const x2=X(acc), c=v>0?TOOK:REF;
      s+=`<rect x="${Math.min(x1,x2).toFixed(1)}" y="${y+2}" width="0" height="${rh-18}" rx="${(rh-18)/2}"
           fill="${c}" fill-opacity="${(0.4+j*0.25).toFixed(2)}">
           <animate attributeName="width" from="0" to="${Math.abs(x2-x1).toFixed(1)}" dur="${DUR}s" begin="${t.toFixed(2)}s" fill="freeze"/></rect>`;
      if(Math.abs(x2-x1)>46)
        s+=`<text x="${((Math.min(x1,x2)+Math.abs(x2-x1)/2)).toFixed(1)}" y="${y+(rh-14)/2+3}" text-anchor="middle" class="mono"
             font-size="8.5" fill="#f2f0e9" opacity="0">${fmtPct(v,0)}<animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(t+DUR*.7).toFixed(2)}s" fill="freeze"/></text>`;
      t+=DUR+GAP;});
    s+=`<circle cy="${y+(rh-14)/2}" r="${5+Math.sqrt(r.members)*0.2}" fill="${pol(r.excess_3m)}" cx="${ZERO}">
        ${r.legs.map((v,j)=>`<animate attributeName="cx" from="${posAt(r,j).toFixed(1)}" to="${posAt(r,j+1).toFixed(1)}" dur="${DUR}s" begin="${(j*(DUR+GAP)).toFixed(2)}s" fill="freeze"/>`).join('')}</circle>`;
    s+=`<text x="${W-100}" y="${y+(rh-14)/2+4}" class="mono" font-size="10.5" fill="${pol(r.excess_3m)}" opacity="0">${fmtPct(r.excess_3m,1)}
         <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="3.6s" fill="freeze"/></text>`;});
  s+=`<line x1="${ZERO}" y1="20" x2="${ZERO}" y2="${H-38}" stroke="${INK}" stroke-width="1.4"/>`;
  s+=`<text x="${ZERO}" y="14" text-anchor="middle" class="mono" font-size="9" fill="${INK}">SPY · 起跑</text>`;
  s+=`<text x="${(L+ZERO)/2}" y="${H-22}" text-anchor="middle" class="mono" font-size="8.5" fill="${REF}">← 落后区</text>`;
  s+=`<text x="${L}" y="${H-6}" class="mono" font-size="9.5" fill="${MUT}">赛道按被画的这些人真正的最远/最退距离排版，所以没有人会跑出赛道 · 起跑线随之左右浮动</text>`;
  return s+'</svg>';
}

/* ============ Ranked · 三段迷你条的三种画法 ============ */
const LEGSTYLE={
  bar:(r,x,y,bw)=>r.legs.map((v,j)=>{const hh=Math.min(11,Math.abs(v)/0.36*11);
    return `<rect x="${x+j*bw+2}" y="${y+6-(v>0?hh:0)}" width="${bw-6}" height="${Math.max(1.2,hh)}" fill="${pol(v)}" fill-opacity=".8"/>`}).join(''),
  /* 等高色阶：三格同宽同高，只有墨的浓淡在变——粗细完全一致 */
  tone:(r,x,y,bw)=>r.legs.map((v,j)=>{const t=Math.min(1,Math.abs(v)/0.36);
    return `<rect x="${x+j*bw+1.5}" y="${y+1}" width="${bw-4}" height="10" rx="2"
      fill="${pol(v)}" fill-opacity="${(0.1+t*0.85).toFixed(2)}"><title>${D.legLabels[j]} ${fmtPct(v,1)}</title></rect>`}).join(''),
  /* 迷你折线：一条连续的线，末端一个点——最安静 */
  spark:(r,x,y,bw)=>{const w=bw*3-6, mx=0.36;
    const px=i=>x+2+i*(w/2), py=v=>y+6-Math.max(-10,Math.min(10,v/mx*10));
    const pts=r.legs.map((v,i)=>`${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(' ');
    return `<line x1="${x+2}" y1="${y+6}" x2="${x+2+w}" y2="${y+6}" stroke="${LINE}" stroke-width=".7"/>`
      +`<polyline points="${pts}" fill="none" stroke="${pol(r.legs[2])}" stroke-width="1.6" stroke-linejoin="round"/>`
      +`<circle cx="${px(2)}" cy="${py(r.legs[2])}" r="2.2" fill="${pol(r.legs[2])}"/>`;}
};
function diverge(opts={}){
  const {n=14,legs=null}=opts;
  const show=[...SORTED.slice(0,n),null,...SORTED.slice(-n)];
  const W=1080,rh=19,H=show.length*rh+30,C=legs?438:508,HALF=legs?330:400,BX=W-180,BW=56;
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
    if(legs)s+=LEGSTYLE[legs](r,BX,y,BW);});
  if(legs)D.legLabels.forEach((l,j)=>s+=`<text x="${BX+(legs==='spark'?j*(BW*3-6)/2+2:j*BW+BW/2)}" y="6" text-anchor="middle" class="mono" font-size="8" fill="${LINE}">${l}</text>`);
  return s+'</svg>';
}
