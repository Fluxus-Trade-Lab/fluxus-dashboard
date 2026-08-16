/* ---------- shared helpers ---------- */
const R = DATA.rows.filter(r=>r.excess_3m!=null);
const STATES=['Leading','Improving','Weakening','Lagging'];
const STRETCH=[['rs_3m_6m','3M–6M'],['rs_1m_3m','1M–3M'],['rs_1w_1m','1W–1M'],['rs_0_1w','0–1W']];
const fmtPct=(v,d=0)=>v==null?'—':(v>0?'+':'')+(v*100).toFixed(d)+'%';
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const SORTED=[...R].sort((a,b)=>b.excess_3m-a.excess_3m);
const MX=Math.max(...R.map(r=>Math.abs(r.excess_3m)));
const MA=Math.max(...R.map(r=>Math.abs(r.rs_accel??0)));
const TOOK='var(--took)', REF='var(--refused)', INK='var(--ink)', SEC='var(--sec)',
      MUT='var(--mut)', LINE='var(--line)';
const pol=v=>v>0?TOOK:REF;
/** greyscale ramp — 0 = lightest, 1 = ink. Survives print by construction. */
const ramp=t=>{const g=Math.round(210-Math.max(0,Math.min(1,t))*180);return `rgb(${g},${g-4},${g-10})`};
const PICKS=(()=>{const want=['High Octane','Quantum','Uranium & Nuclear','Airlines'];
  const got=want.map(n=>R.find(r=>r.group===n)).filter(Boolean);
  return got.length>=3?got:SORTED.slice(0,4);})();

/* ================= FIELD geometries ================= */
// F1 beeswarm in four state lanes
function F_swarm(){
  const W=1080,laneH=76,PAD=70,H=laneH*4+30;
  const X=v=>PAD+((v+MX)/(2*MX))*(W-PAD-40);
  const rad=n=>2.6+Math.sqrt(n||1)*0.6;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${X(0)}" y1="12" x2="${X(0)}" y2="${laneH*4+4}" stroke="${INK}" stroke-width="1.2"/>`;
  s+=`<text x="${X(0)}" y="7" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  [-0.2,0.2,0.4].forEach(t=>{s+=`<line x1="${X(t)}" y1="12" x2="${X(t)}" y2="${laneH*4+4}" stroke="${LINE}" stroke-dasharray="2 4"/><text x="${X(t)}" y="7" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${fmtPct(t)}</text>`;});
  STATES.forEach((st,i)=>{
    const y0=18+i*laneH, mid=y0+laneH/2-8, set=R.filter(r=>r.state===st).sort((a,b)=>a.excess_3m-b.excess_3m), placed=[];
    set.forEach(r=>{const cx=X(r.excess_3m),rr=rad(r.members);let k=0,cy=mid,dir=1;
      while(placed.some(p=>Math.hypot(p.cx-cx,p.cy-cy)<p.r+rr+0.8)&&k<70){k++;dir=-dir;cy=mid+dir*Math.ceil(k/2)*3.2;}
      placed.push({cx,cy,r:rr,d:r});});
    s+=`<text x="0" y="${mid+3}" class="mono" font-size="9.5" fill="${MUT}" letter-spacing="1.3">${st.toUpperCase()}</text>`;
    s+=`<text x="0" y="${mid+15}" class="mono" font-size="9" fill="${LINE}">${set.length}</text>`;
    placed.forEach(p=>s+=`<circle cx="${p.cx}" cy="${p.cy}" r="${p.r.toFixed(2)}" fill="${pol(p.d.excess_3m)}" fill-opacity=".82"><title>${esc(p.d.group)} ${fmtPct(p.d.excess_3m)}</title></circle>`);
    if(placed.length){const t=placed.reduce((a,b)=>b.d.excess_3m>a.d.excess_3m?b:a);
      s+=`<text x="${t.cx+t.r+5}" y="${t.cy+3}" font-size="9.5" fill="${INK}">${esc(t.d.group)}</text>`;}
    if(i<3)s+=`<line x1="0" y1="${y0+laneH-10}" x2="${W}" y2="${y0+laneH-10}" stroke="${LINE}" stroke-width=".6"/>`;
  });
  return s+'</svg>';
}
// F2 quadrant — lead (x) vs whether it is still accelerating (y)
function F_quadrant(){
  const W=1080,H=430,P=58;
  const X=v=>P+((v+MX)/(2*MX))*(W-P*2), Y=v=>P+(1-((v+MA)/(2*MA)))*(H-P*2);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<rect x="${X(0)}" y="${P}" width="${W-P-X(0)}" height="${Y(0)-P}" fill="${TOOK}" opacity=".05"/>`;
  s+=`<rect x="${P}" y="${Y(0)}" width="${X(0)-P}" height="${H-P-Y(0)}" fill="${REF}" opacity=".05"/>`;
  s+=`<line x1="${X(0)}" y1="${P}" x2="${X(0)}" y2="${H-P}" stroke="${INK}" stroke-width="1.1"/>`;
  s+=`<line x1="${P}" y1="${Y(0)}" x2="${W-P}" y2="${Y(0)}" stroke="${INK}" stroke-width="1.1"/>`;
  const q=[['已领先 · 还在加速',X(0)+12,P+16,'start'],['已领先 · 正在减速',X(0)+12,H-P-8,'start'],
           ['还落后 · 已在转强',X(0)-12,P+16,'end'],['还落后 · 继续走弱',X(0)-12,H-P-8,'end']];
  q.forEach(([t,x,y,a])=>s+=`<text x="${x}" y="${y}" text-anchor="${a}" font-size="10.5" fill="${MUT}">${t}</text>`);
  R.forEach(r=>{const cx=X(r.excess_3m),cy=Y(r.rs_accel??0),rr=2.4+Math.sqrt(r.members||1)*0.5;
    const lead=r.excess_3m>0, acc=(r.rs_accel??0)>0;
    s+=`<circle cx="${cx}" cy="${cy}" r="${rr.toFixed(2)}" fill="${lead&&acc?TOOK:(!lead&&!acc?REF:'none')}"
        stroke="${lead&&acc?'none':(!lead&&!acc?'none':SEC)}" stroke-width="1.1" fill-opacity=".8"><title>${esc(r.group)}</title></circle>`;});
  SORTED.slice(0,3).concat(SORTED.slice(-2)).forEach(r=>{
    s+=`<text x="${X(r.excess_3m)+7}" y="${Y(r.rs_accel??0)-6}" font-size="10" fill="${INK}">${esc(r.group)}</text>`;});
  s+=`<text x="${W-P}" y="${H-P+18}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">3M vs SPY →</text>`;
  s+=`<text x="${P-8}" y="${P-8}" text-anchor="start" class="mono" font-size="9" fill="${MUT}">↑ 加速度</text>`;
  return s+'</svg>';
}
// F3 dot matrix — one dot per theme, sorted, grey ramp = how far from SPY
function F_matrix(){
  const cols=19,cell=26,W=1080,rows=Math.ceil(SORTED.length/cols),H=rows*cell+50;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  SORTED.forEach((r,i)=>{const cx=18+(i%cols)*cell, cy=22+Math.floor(i/cols)*cell;
    const t=(r.excess_3m+MX)/(2*MX);
    s+=`<circle cx="${cx}" cy="${cy}" r="9.4" fill="${r.excess_3m>0?TOOK:REF}" fill-opacity="${(0.18+Math.abs(r.excess_3m)/MX*0.82).toFixed(2)}"><title>${esc(r.group)} ${fmtPct(r.excess_3m)}</title></circle>`;});
  s+=`<text x="18" y="${H-22}" class="mono" font-size="9.5" fill="${MUT}">每个点 = 一个主题 · 由强到弱 · 不透明度 = 离 SPY 多远</text>`;
  const w=SORTED.filter(r=>r.excess_3m>0).length;
  s+=`<text x="18" y="${H-6}" font-size="11" fill="${INK}"><tspan font-weight="600">${w}</tspan> 跑赢 · <tspan font-weight="600">${SORTED.length-w}</tspan> 跑输</text>`;
  return s+'</svg>';
}
// F4 histogram ridge
function F_ridge(){
  const W=1080,H=250,P=54,B=22;
  const bins=Array.from({length:B},()=>[]);
  R.forEach(r=>{const i=Math.min(B-1,Math.floor(((r.excess_3m+MX)/(2*MX))*B));bins[i].push(r);});
  const mx=Math.max(...bins.map(b=>b.length)), bw=(W-P*2)/B;
  const X=v=>P+((v+MX)/(2*MX))*(W-P*2);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  bins.forEach((b,i)=>{const h=(b.length/mx)*(H-70); const x=P+i*bw;
    const centre=-MX+(i+.5)*(2*MX/B);
    s+=`<rect x="${x+1}" y="${H-40-h}" width="${bw-2}" height="${h}" rx="${Math.min(bw/2-1,10)}"
        fill="${centre>0?TOOK:REF}" fill-opacity=".85"/>`;
    if(b.length)s+=`<text x="${x+bw/2}" y="${H-46-h}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${b.length}</text>`;});
  s+=`<line x1="${X(0)}" y1="14" x2="${X(0)}" y2="${H-34}" stroke="${INK}" stroke-width="1.2"/>`;
  s+=`<text x="${X(0)}" y="10" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  [-.2,.2,.4].forEach(t=>s+=`<text x="${X(t)}" y="${H-22}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${fmtPct(t)}</text>`);
  return s+'</svg>';
}
// F5 radial burst — 76 spokes, length = excess
function F_burst(){
  const W=1080,H=470,cx=W/2,cy=H/2+8,r0=64,rmax=182;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<circle cx="${cx}" cy="${cy}" r="${r0}" fill="none" stroke="${INK}" stroke-width="1.1"/>`;
  [.5,1].forEach(f=>s+=`<circle cx="${cx}" cy="${cy}" r="${r0+f*rmax*.55}" fill="none" stroke="${LINE}" stroke-dasharray="2 4"/>`);
  SORTED.forEach((r,i)=>{const a=(i/SORTED.length)*Math.PI*2-Math.PI/2;
    const len=(r.excess_3m/MX)*rmax*.62, rr=r0+len;
    const x1=cx+Math.cos(a)*r0,y1=cy+Math.sin(a)*r0,x2=cx+Math.cos(a)*rr,y2=cy+Math.sin(a)*rr;
    s+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${pol(r.excess_3m)}" stroke-width="4.2" stroke-linecap="round" opacity=".9"><title>${esc(r.group)} ${fmtPct(r.excess_3m)}</title></line>`;});
  SORTED.slice(0,2).forEach((r,i)=>{const a=(i/SORTED.length)*Math.PI*2-Math.PI/2;
    const rr=r0+(r.excess_3m/MX)*rmax*.62+14;
    s+=`<text x="${cx+Math.cos(a)*rr}" y="${cy+Math.sin(a)*rr}" font-size="10.5" fill="${INK}">${esc(r.group)}</text>`;});
  s+=`<text x="${cx}" y="${cy-4}" text-anchor="middle" class="mono" font-size="11" fill="${MUT}">SPY</text>`;
  s+=`<text x="${cx}" y="${cy+12}" text-anchor="middle" class="mono" font-size="9" fill="${LINE}">向外 = 跑赢</text>`;
  return s+'</svg>';
}
// F6 one axis per state row, dot size = members ("support load" shape)
function F_rows(){
  const W=1080,rh=52,H=rh*4+40,P=88;
  const X=v=>P+((v+MX)/(2*MX))*(W-P-30);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  STATES.forEach((st,i)=>{const y=26+i*rh;
    s+=`<line x1="${P}" y1="${y}" x2="${W-30}" y2="${y}" stroke="${LINE}" stroke-width=".7"/>`;
    s+=`<text x="0" y="${y+3.5}" class="mono" font-size="9.5" fill="${MUT}" letter-spacing="1.3">${st.toUpperCase()}</text>`;
    R.filter(r=>r.state===st).forEach(r=>{
      s+=`<circle cx="${X(r.excess_3m)}" cy="${y}" r="${(3+Math.sqrt(r.members||1)*0.75).toFixed(2)}"
          fill="${pol(r.excess_3m)}" fill-opacity=".5"><title>${esc(r.group)} · ${r.members}</title></circle>`;});});
  s+=`<line x1="${X(0)}" y1="14" x2="${X(0)}" y2="${H-24}" stroke="${INK}" stroke-width="1.2"/>`;
  s+=`<text x="${X(0)}" y="10" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  s+=`<text x="${W-30}" y="${H-8}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">圆面积 = 成员数</text>`;
  return s+'</svg>';
}
// F7 range capsules — each theme a capsule from its 1M to its 3M excess
function F_capsule(){
  const top=[...SORTED.slice(0,16),...SORTED.slice(-8)];
  const W=1080,cw=(W-40)/top.length,H=300,P=40;
  const vals=top.flatMap(r=>[r.perf_1m,r.perf_3m]).filter(v=>v!=null);
  const lo=Math.min(...vals),hi=Math.max(...vals);
  const Y=v=>P+(1-(v-lo)/(hi-lo))*(H-P-52);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="20" y1="${Y(0)}" x2="${W-20}" y2="${Y(0)}" stroke="${INK}" stroke-width="1"/>`;
  top.forEach((r,i)=>{const x=24+i*cw+cw/2;
    const a=Y(r.perf_1m),b=Y(r.perf_3m),up=r.perf_3m>=r.perf_1m;
    s+=`<line x1="${x}" y1="${Math.min(a,b)}" x2="${x}" y2="${Math.max(a,b)}" stroke="${up?TOOK:REF}"
        stroke-width="${Math.max(6,cw*0.42)}" stroke-linecap="round" opacity=".9"><title>${esc(r.group)} 1M ${fmtPct(r.perf_1m)} → 3M ${fmtPct(r.perf_3m)}</title></line>`;});
  s+=`<text x="20" y="${H-28}" class="mono" font-size="9.5" fill="${MUT}">每根胶囊 = 一个主题从 1M 到 3M 的区间 · 深色端在上 = 3M 更高</text>`;
  s+=`<text x="20" y="${H-12}" class="mono" font-size="9" fill="${LINE}">前 16 强 + 后 8 弱</text>`;
  return s+'</svg>';
}
// F8 treemap by members, fill = excess
function F_treemap(){
  const W=1080,H=380;
  const items=[...R].sort((a,b)=>b.members-a.members);
  const total=items.reduce((s,r)=>s+r.members,0);
  let x=0,y=0,rowH=0,out='';
  // simple shelf packing by area
  let cursor=0;
  const rowsOf=[];let row=[],acc=0;
  items.forEach(r=>{row.push(r);acc+=r.members;
    if(acc>total/6.2){rowsOf.push(row);row=[];acc=0;}});
  if(row.length)rowsOf.push(row);
  const rh=H/rowsOf.length;
  rowsOf.forEach((rw,ri)=>{const sum=rw.reduce((s,r)=>s+r.members,0);let cx=0;
    rw.forEach(r=>{const w=(r.members/sum)*W;
      const t=Math.abs(r.excess_3m)/MX;
      out+=`<rect x="${cx+1}" y="${ri*rh+1}" width="${Math.max(1,w-2)}" height="${rh-2}" rx="4"
            fill="${pol(r.excess_3m)}" fill-opacity="${(0.15+t*0.8).toFixed(2)}"><title>${esc(r.group)} ${r.members} · ${fmtPct(r.excess_3m)}</title></rect>`;
      if(w>72)out+=`<text x="${cx+7}" y="${ri*rh+16}" font-size="9.5" fill="${INK}">${esc(r.group).slice(0,16)}</text>`;
      if(w>72)out+=`<text x="${cx+7}" y="${ri*rh+29}" class="mono" font-size="9" fill="${SEC}">${r.members} · ${fmtPct(r.excess_3m)}</text>`;
      cx+=w;});});
  return `<svg viewBox="0 0 ${W} ${H}">${out}</svg>`;
}
// F9 arrow field — from 1M excess to 3M excess
function F_arrows(){
  const W=1080,H=330,P=54;
  const X=v=>P+((v+MX)/(2*MX))*(W-P*2);
  const set=[...R].sort((a,b)=>b.members-a.members).slice(0,44);
  const Y=(i)=>26+ (i%22)*13 + (i>=22? 0:0);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${X(0)}" y1="14" x2="${X(0)}" y2="${H-30}" stroke="${INK}" stroke-width="1.2"/>`;
  set.forEach((r,i)=>{const y=22+i*6.4;
    const a=X((r.perf_1m??0)-0), b=X(r.excess_3m);
    const fwd=b>=a;
    s+=`<line x1="${a}" y1="${y}" x2="${b}" y2="${y}" stroke="${fwd?TOOK:REF}" stroke-width="2" opacity=".75"/>`;
    s+=`<circle cx="${b}" cy="${y}" r="2.8" fill="${fwd?TOOK:REF}"><title>${esc(r.group)}</title></circle>`;});
  s+=`<text x="${P}" y="${H-10}" class="mono" font-size="9.5" fill="${MUT}">箭头起点 = 1M 表现，终点 = 3M 超额 · 向右 = 还在扩大领先</text>`;
  return s+'</svg>';
}
// F10 waffle by state
function F_waffle(){
  const W=1080,cell=17,cols=38,H=Math.ceil(R.length/cols)*cell+70;
  const order=STATES.flatMap(st=>R.filter(r=>r.state===st).sort((a,b)=>b.excess_3m-a.excess_3m));
  const tone={Leading:INK,Improving:SEC,Weakening:MUT,Lagging:LINE};
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  order.forEach((r,i)=>{const x=(i%cols)*cell, y=26+Math.floor(i/cols)*cell;
    s+=`<rect x="${x}" y="${y}" width="${cell-3}" height="${cell-3}" rx="2.5" fill="${tone[r.state]}"><title>${esc(r.group)} · ${r.state}</title></rect>`;});
  STATES.forEach((st,i)=>{const n=R.filter(r=>r.state===st).length;
    s+=`<rect x="${i*168}" y="${H-30}" width="11" height="11" rx="2" fill="${tone[st]}"/>`;
    s+=`<text x="${i*168+17}" y="${H-21}" font-size="10.5" fill="${SEC}">${st} <tspan class="mono" fill="${MUT}">${n}</tspan></text>`;});
  return s+'</svg>';
}

/* ================= COMPARE geometries ================= */
const SMAX=Math.max(...R.flatMap(r=>STRETCH.map(([k])=>Math.abs(r[k]??0))))*0.62;
// C1 slope over the four stretches, with the other 72 as ground noise
function C_slope(picks=PICKS){
  const W=1080,H=300,L=92,Rp=196,T=22,B=42;
  const X=i=>L+i*((W-L-Rp)/3), Y=v=>T+(1-(Math.max(-SMAX,Math.min(SMAX,v))+SMAX)/(2*SMAX))*(H-T-B);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${L}" y1="${Y(0)}" x2="${W-Rp}" y2="${Y(0)}" stroke="${INK}" stroke-width="1"/>`;
  STRETCH.forEach(([,lab],i)=>{s+=`<line x1="${X(i)}" y1="${T}" x2="${X(i)}" y2="${H-B}" stroke="${LINE}" stroke-width=".7"/>`
    +`<text x="${X(i)}" y="${H-B+17}" text-anchor="middle" class="mono" font-size="9.5" fill="${MUT}" letter-spacing="1">${lab}</text>`;});
  s+=`<text x="${L-8}" y="${Y(0)+3}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  R.forEach(r=>{const p=STRETCH.map(([k],i)=>`${X(i)},${Y(r[k]??0)}`).join(' ');
    s+=`<polyline points="${p}" fill="none" stroke="${LINE}" stroke-width=".7" opacity=".6"/>`;});
  picks.forEach(r=>{const pts=STRETCH.map(([k],i)=>[X(i),Y(r[k]??0)]), last=r[STRETCH[3][0]]??0, c=pol(last);
    s+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${c}" stroke-width="2.4" stroke-linejoin="round"/>`;
    pts.forEach((p,i)=>s+=`<circle cx="${p[0]}" cy="${p[1]}" r="${i===3?4.2:2.6}" fill="${c}"/>`);
    s+=`<text x="${W-Rp+10}" y="${pts[3][1]+3}" font-size="11.5" font-weight="600" fill="${c}">${esc(r.group)}</text>`;
    s+=`<text x="${W-Rp+10}" y="${pts[3][1]+16}" class="mono" font-size="9.5" fill="${MUT}">${fmtPct(last)} · ${r.members}n</text>`;});
  return s+'</svg>';
}
// C2 bump — rank among all 76 at each stretch
function C_bump(picks=PICKS){
  const W=1080,H=300,L=92,Rp=196,T=24,B=42;
  const ranks=STRETCH.map(([k])=>{const o=[...R].sort((a,b)=>(b[k]??-9)-(a[k]??-9));
    return new Map(o.map((r,i)=>[r.group,i+1]));});
  const N=R.length, X=i=>L+i*((W-L-Rp)/3), Y=rk=>T+((rk-1)/(N-1))*(H-T-B);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  STRETCH.forEach(([,lab],i)=>{s+=`<line x1="${X(i)}" y1="${T}" x2="${X(i)}" y2="${H-B}" stroke="${LINE}" stroke-width=".7"/>`
    +`<text x="${X(i)}" y="${H-B+17}" text-anchor="middle" class="mono" font-size="9.5" fill="${MUT}" letter-spacing="1">${lab}</text>`;});
  [1,20,40,60,76].forEach(rk=>s+=`<text x="${L-10}" y="${Y(rk)+3}" text-anchor="end" class="mono" font-size="9" fill="${LINE}">#${rk}</text>`);
  R.forEach(r=>{const p=ranks.map((m,i)=>`${X(i)},${Y(m.get(r.group)||N)}`).join(' ');
    s+=`<polyline points="${p}" fill="none" stroke="${LINE}" stroke-width=".7" opacity=".55"/>`;});
  picks.forEach(r=>{const pts=ranks.map((m,i)=>[X(i),Y(m.get(r.group)||N)]);
    const rk0=ranks[0].get(r.group)||N, rk3=ranks[3].get(r.group)||N, up=rk3<rk0, c=up?TOOK:REF;
    s+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${c}" stroke-width="2.6" stroke-linejoin="round"/>`;
    pts.forEach(p=>s+=`<circle cx="${p[0]}" cy="${p[1]}" r="3.4" fill="${c}"/>`);
    s+=`<text x="${W-Rp+10}" y="${pts[3][1]+3}" font-size="11.5" font-weight="600" fill="${c}">${esc(r.group)}</text>`;
    s+=`<text x="${W-Rp+10}" y="${pts[3][1]+16}" class="mono" font-size="9.5" fill="${MUT}">#${rk0} → #${rk3}</text>`;});
  return s+'</svg>';
}
// C3 petal rose — one rose per pick, four petals = four stretches
function C_rose(picks=PICKS){
  const W=1080,H=250,n=picks.length||1,cw=W/n;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  picks.forEach((r,pi)=>{const cx=cw*pi+cw/2, cy=112, r0=16, rmax=74;
    [0,1].forEach(f=>s+=`<circle cx="${cx}" cy="${cy}" r="${r0+rmax*(f?1:.5)}" fill="none" stroke="${LINE}" stroke-dasharray="2 4"/>`);
    STRETCH.forEach(([k,lab],i)=>{const v=r[k]??0;
      const a0=(i/4)*Math.PI*2-Math.PI/2+0.06, a1=((i+1)/4)*Math.PI*2-Math.PI/2-0.06;
      const rr=r0+Math.min(1,Math.abs(v)/SMAX)*rmax;
      const p=(ang,rad)=>[cx+Math.cos(ang)*rad,cy+Math.sin(ang)*rad];
      const A=p(a0,r0),B=p(a0,rr),C=p(a1,rr),D=p(a1,r0);
      s+=`<path d="M${A} L${B} A${rr},${rr} 0 0 1 ${C} L${D} A${r0},${r0} 0 0 0 ${A} Z"
          fill="${pol(v)}" fill-opacity="${(0.3+Math.min(1,Math.abs(v)/SMAX)*0.65).toFixed(2)}"><title>${lab} ${fmtPct(v,1)}</title></path>`;
      const mid=(a0+a1)/2, lp=p(mid,rr+13);
      s+=`<text x="${lp[0]}" y="${lp[1]}" text-anchor="middle" class="mono" font-size="8.5" fill="${MUT}">${lab}</text>`;});
    s+=`<text x="${cx}" y="${H-26}" text-anchor="middle" font-size="11.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${cx}" y="${H-11}" text-anchor="middle" class="mono" font-size="9.5" fill="${MUT}">now ${fmtPct(r.rs_0_1w,1)}</text>`;});
  return s+'</svg>';
}
// C4 relay baton — the four stretches laid end to end as one bar per pick
function C_baton(picks=PICKS){
  const W=1080,rh=54,H=picks.length*rh+46,L=150,AV=W-L-90;
  const tot=r=>STRETCH.reduce((s,[k])=>s+Math.abs(r[k]??0),0);
  const mx=Math.max(...R.map(tot));
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  picks.forEach((r,i)=>{const y=18+i*rh;let x=L;
    STRETCH.forEach(([k,lab],j)=>{const v=r[k]??0, w=(Math.abs(v)/mx)*AV;
      s+=`<rect x="${x}" y="${y}" width="${Math.max(1.5,w)}" height="26" rx="4"
          fill="${pol(v)}" fill-opacity="${(0.34+j*0.22).toFixed(2)}"><title>${lab} ${fmtPct(v,1)}</title></rect>`;
      if(w>46)s+=`<text x="${x+w/2}" y="${y+17}" text-anchor="middle" class="mono" font-size="9" fill="#f2f0e9">${lab}</text>`;
      x+=w+2;});
    s+=`<text x="${L-10}" y="${y+17}" text-anchor="end" font-size="11.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${x+8}" y="${y+17}" class="mono" font-size="10" fill="${SEC}">${fmtPct(r.excess_3m)}</text>`;
    s+=`<text x="${L-10}" y="${y+31}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">${r.members} names</text>`;});
  s+=`<text x="${L}" y="${H-10}" class="mono" font-size="9.5" fill="${MUT}">四段接力首尾相接 · 越靠右越新 · 段越深越近 · 段长 = 该段相对强度的绝对值</text>`;
  return s+'</svg>';
}
// C5 dumbbell — oldest stretch vs newest
function C_dumbbell(picks=PICKS){
  const W=1080,rh=42,H=picks.length*rh+52,L=170,P=60;
  const X=v=>L+((Math.max(-SMAX,Math.min(SMAX,v))+SMAX)/(2*SMAX))*(W-L-P);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${X(0)}" y1="12" x2="${X(0)}" y2="${H-34}" stroke="${INK}" stroke-width="1.1"/>`;
  s+=`<text x="${X(0)}" y="8" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  picks.forEach((r,i)=>{const y=28+i*rh, a=X(r.rs_3m_6m??0), b=X(r.rs_0_1w??0), fwd=b>=a, c=fwd?TOOK:REF;
    s+=`<line x1="${a}" y1="${y}" x2="${b}" y2="${y}" stroke="${c}" stroke-width="3" opacity=".45"/>`;
    s+=`<circle cx="${a}" cy="${y}" r="5" fill="none" stroke="${SEC}" stroke-width="1.6"/>`;
    s+=`<circle cx="${b}" cy="${y}" r="6.4" fill="${c}"/>`;
    s+=`<text x="${L-12}" y="${y+4}" text-anchor="end" font-size="11.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${b+11}" y="${y+4}" class="mono" font-size="10" fill="${c}">${fmtPct(r.rs_0_1w,1)}</text>`;});
  s+=`<text x="${L}" y="${H-10}" class="mono" font-size="9.5" fill="${MUT}">空心 = 最早那段（3M–6M） · 实心 = 最近那段（0–1W） · 线的方向就是它在往哪走</text>`;
  return s+'</svg>';
}
// C6 waterfall — each stretch as a step, cumulative
function C_waterfall(picks=PICKS){
  const W=1080,n=picks.length||1,cw=W/n,H=250;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  const all=R.map(r=>STRETCH.reduce((a,[k])=>a+(r[k]??0),0));
  const m=Math.max(...all.map(Math.abs))*0.75;
  picks.forEach((r,pi)=>{const x0=cw*pi+26,w=cw-58, bw=w/4;
    const Y=v=>34+(1-(Math.max(-m,Math.min(m,v))+m)/(2*m))*(H-100);
    s+=`<line x1="${x0}" y1="${Y(0)}" x2="${x0+w}" y2="${Y(0)}" stroke="${INK}" stroke-width=".9"/>`;
    let acc=0;
    STRETCH.forEach(([k,lab],i)=>{const v=r[k]??0, from=acc; acc+=v;
      const y1=Y(from),y2=Y(acc);
      s+=`<rect x="${x0+i*bw+4}" y="${Math.min(y1,y2)}" width="${bw-8}" height="${Math.max(1.5,Math.abs(y2-y1))}"
          rx="2.5" fill="${pol(v)}" fill-opacity=".85"><title>${lab} ${fmtPct(v,1)}</title></rect>`;
      if(i<3)s+=`<line x1="${x0+i*bw+bw-4}" y1="${y2}" x2="${x0+(i+1)*bw+4}" y2="${y2}" stroke="${LINE}" stroke-dasharray="2 2"/>`;
      s+=`<text x="${x0+i*bw+bw/2}" y="${H-52}" text-anchor="middle" class="mono" font-size="8.5" fill="${MUT}">${lab}</text>`;});
    s+=`<text x="${x0+w/2}" y="${H-28}" text-anchor="middle" font-size="11.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${x0+w/2}" y="${H-13}" text-anchor="middle" class="mono" font-size="9.5" fill="${acc>0?TOOK:REF}">四段合计 ${fmtPct(acc,1)}</text>`;});
  return s+'</svg>';
}
// C7 small multiples — every pick a card with its own sparkline, shared scale
function C_cards(picks=PICKS){
  const W=1080,n=picks.length||1,cw=W/n,H=190;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  picks.forEach((r,pi)=>{const x0=cw*pi+14,w=cw-30;
    const Y=v=>58+(1-(Math.max(-SMAX,Math.min(SMAX,v))+SMAX)/(2*SMAX))*78;
    s+=`<rect x="${x0}" y="8" width="${w}" height="${H-20}" rx="16" fill="var(--bg)"/>`;
    s+=`<text x="${x0+14}" y="30" font-size="12" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${x0+14}" y="44" class="mono" font-size="9" fill="${MUT}">${r.members} names · ${r.state}</text>`;
    const X=i=>x0+20+i*((w-40)/3);
    s+=`<line x1="${x0+20}" y1="${Y(0)}" x2="${x0+w-20}" y2="${Y(0)}" stroke="${LINE}"/>`;
    const pts=STRETCH.map(([k],i)=>[X(i),Y(r[k]??0)]);
    const c=pol(r.rs_0_1w??0);
    s+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${c}" stroke-width="2.2"/>`;
    s+=`<circle cx="${pts[3][0]}" cy="${pts[3][1]}" r="4" fill="${c}"/>`;
    s+=`<text x="${x0+14}" y="${H-18}" class="mono" font-size="15" fill="${c}">${fmtPct(r.rs_0_1w,1)}</text>`;
    s+=`<text x="${x0+w-14}" y="${H-18}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">本周相对</text>`;});
  return s+'</svg>';
}
// C8 orbit — picks as bodies, distance from centre = current relative strength
function C_orbit(picks=PICKS){
  const W=1080,H=330,cx=W/2,cy=H/2;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  [1,2,3].forEach(k=>s+=`<circle cx="${cx}" cy="${cy}" r="${k*44}" fill="none" stroke="${LINE}" stroke-dasharray="2 5"/>`);
  s+=`<circle cx="${cx}" cy="${cy}" r="22" fill="${INK}"/>`;
  s+=`<text x="${cx}" y="${cy+4}" text-anchor="middle" class="mono" font-size="10" fill="#f2f0e9">SPY</text>`;
  picks.forEach((r,i)=>{const a=(i/Math.max(1,picks.length))*Math.PI*2-Math.PI/2;
    const v=r.rs_0_1w??0, rad=44+Math.min(1,Math.abs(v)/SMAX)*94;
    const x=cx+Math.cos(a)*rad,y=cy+Math.sin(a)*rad, c=pol(v);
    // trail across the four stretches
    STRETCH.forEach(([k2],j)=>{const vv=r[k2]??0, rr=44+Math.min(1,Math.abs(vv)/SMAX)*94;
      s+=`<circle cx="${cx+Math.cos(a)*rr}" cy="${cy+Math.sin(a)*rr}" r="${2+j*1.1}" fill="${c}" fill-opacity="${0.16+j*0.24}"/>`;});
    s+=`<circle cx="${x}" cy="${y}" r="${7+Math.sqrt(r.members)*0.5}" fill="${c}"/>`;
    s+=`<text x="${x}" y="${y-16}" text-anchor="middle" font-size="11" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;});
  s+=`<text x="14" y="${H-8}" class="mono" font-size="9.5" fill="${MUT}">离心越远 = 越偏离 SPY · 尾迹由淡到深 = 四段时间顺序 · 圆越大 = 成员越多</text>`;
  return s+'</svg>';
}

/* ================= RANKED geometries ================= */
const pips=(x,y,r,fill)=>{let o='';for(let k=0;k<(r.persistence_of||5);k++)
  o+=`<circle cx="${x+k*7}" cy="${y}" r="2.1" fill="${k<(r.persistence||0)?fill:LINE}"/>`;return o;};
// R1 diverging bars around a centred zero
function R_diverge(n=12){
  const show=[...SORTED.slice(0,n),null,...SORTED.slice(-n)];
  const W=1080,rh=18,H=show.length*rh+30,C=470,HALF=372;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${C}" y1="6" x2="${C}" y2="${H-18}" stroke="${INK}" stroke-width="1.1"/>`;
  [.2,.4].forEach(t=>[1,-1].forEach(g=>{const x=C+g*(t/MX)*HALF;
    s+=`<line x1="${x}" y1="6" x2="${x}" y2="${H-18}" stroke="${LINE}" stroke-dasharray="2 4"/>`
     +`<text x="${x}" y="${H-4}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${fmtPct(g*t)}</text>`;}));
  show.forEach((r,i)=>{const y=10+i*rh;
    if(!r){s+=`<text x="${C}" y="${y+10}" text-anchor="middle" class="mono" font-size="10" fill="${LINE}">· · ·  ${SORTED.length-2*n} more  · · ·</text>`;return;}
    const w=(Math.abs(r.excess_3m)/MX)*HALF, pos=r.excess_3m>0, x=pos?C:C-w;
    s+=`<rect x="${x}" y="${y}" width="${Math.max(1.5,w)}" height="12" rx="3" fill="${pol(r.excess_3m)}"/>`;
    s+=`<text x="${pos?C-9:C+9}" y="${y+10}" text-anchor="${pos?'end':'start'}" font-size="10.5" fill="${INK}">${esc(r.group)}</text>`;
    s+=`<text x="${pos?x+w+8:x-8}" y="${y+10}" text-anchor="${pos?'start':'end'}" class="mono" font-size="10" fill="${SEC}">${fmtPct(r.excess_3m)}</text>`;});
  return s+'</svg>';
}
// R2 chunky arch-top bars, top N only
function R_arch(n=14){
  const rows=SORTED.slice(0,n),W=1080,bw=(W-30)/n,H=290,base=H-52;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  rows.forEach((r,i)=>{const h=(r.excess_3m/MX)*(base-34), x=16+i*bw, w=bw-13, y=base-h, rad=Math.min(w/2,26);
    s+=`<path d="M${x},${base} L${x},${y+rad} A${rad},${rad} 0 0 1 ${x+w},${y+rad} L${x+w},${base} Z"
        fill="${i===0?INK:pol(r.excess_3m)}" fill-opacity="${i===0?1:(0.35+0.6*(r.excess_3m/MX)).toFixed(2)}"/>`;
    s+=`<text x="${x+w/2}" y="${y-8}" text-anchor="middle" class="mono" font-size="10.5" fill="${INK}">${fmtPct(r.excess_3m)}</text>`;
    s+=`<text x="${x+w/2}" y="${base+15}" text-anchor="middle" font-size="9" fill="${SEC}">${esc(r.group).slice(0,13)}</text>`;
    s+=pips(x+w/2-17,base+27,r,MUT);});
  s+=`<line x1="16" y1="${base}" x2="${W-16}" y2="${base}" stroke="${INK}" stroke-width="1"/>`;
  s+=`<text x="16" y="${H-6}" class="mono" font-size="9" fill="${MUT}">柱下五点 = 最近 5 期里有几期它在榜上 · 最强者穿黑</text>`;
  return s+'</svg>';
}
// R3 lollipop comb — all 76 in one comb
function R_comb(){
  const W=1080,H=340,P=44,base=H-72;
  const cw=(W-P*2)/SORTED.length;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${P}" y1="${base}" x2="${W-P}" y2="${base}" stroke="${INK}" stroke-width="1"/>`;
  SORTED.forEach((r,i)=>{const x=P+i*cw+cw/2, h=(r.excess_3m/MX)*(base-40), y=base-h;
    s+=`<line x1="${x}" y1="${base}" x2="${x}" y2="${y}" stroke="${pol(r.excess_3m)}" stroke-width="1.5" opacity=".75"/>`;
    s+=`<circle cx="${x}" cy="${y}" r="${2.4+Math.sqrt(r.members)*0.28}" fill="${pol(r.excess_3m)}"><title>${esc(r.group)} ${fmtPct(r.excess_3m)}</title></circle>`;});
  SORTED.slice(0,3).forEach((r,i)=>{const x=P+SORTED.indexOf(r)*cw+cw/2, y=base-(r.excess_3m/MX)*(base-40);
    s+=`<text x="${x+6}" y="${y-6+i*11}" font-size="10" fill="${INK}">${esc(r.group)}</text>`;});
  const lastPos=SORTED.filter(r=>r.excess_3m>0).length;
  s+=`<line x1="${P+lastPos*cw}" y1="24" x2="${P+lastPos*cw}" y2="${base+18}" stroke="${INK}" stroke-dasharray="3 3"/>`;
  s+=`<text x="${P+lastPos*cw+6}" y="30" class="mono" font-size="9.5" fill="${MUT}">← ${lastPos} 跑赢 · ${SORTED.length-lastPos} 跑输 →</text>`;
  s+=`<text x="${P}" y="${H-10}" class="mono" font-size="9.5" fill="${MUT}">全部 76 条，一把梳子 · 圆点大小 = 成员数</text>`;
  return s+'</svg>';
}
// R4 heat rows — 76 rows × 4 stretches, ink density
function R_heat(){
  const n=26,rows=[...SORTED.slice(0,n)],W=1080,rh=17,H=n*rh+44,L=178,cw=104;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  STRETCH.forEach(([,lab],i)=>s+=`<text x="${L+i*cw+cw/2}" y="14" text-anchor="middle" class="mono" font-size="9" fill="${MUT}" letter-spacing="1">${lab}</text>`);
  s+=`<text x="${L+4*cw+70}" y="14" text-anchor="middle" class="mono" font-size="9" fill="${MUT}" letter-spacing="1">3M vs SPY</text>`;
  rows.forEach((r,i)=>{const y=22+i*rh;
    s+=`<text x="${L-12}" y="${y+11}" text-anchor="end" font-size="10.5" fill="${INK}">${esc(r.group)}</text>`;
    STRETCH.forEach(([k],j)=>{const v=r[k]??0, t=Math.min(1,Math.abs(v)/SMAX);
      s+=`<rect x="${L+j*cw+2}" y="${y}" width="${cw-4}" height="${rh-3}" rx="3"
          fill="${pol(v)}" fill-opacity="${(0.08+t*0.86).toFixed(2)}"><title>${fmtPct(v,1)}</title></rect>`;});
    const w=(Math.abs(r.excess_3m)/MX)*130;
    s+=`<rect x="${L+4*cw+12}" y="${y+2}" width="${Math.max(1,w)}" height="${rh-7}" rx="2" fill="${pol(r.excess_3m)}"/>`;
    s+=`<text x="${L+4*cw+18+w}" y="${y+11}" class="mono" font-size="9.5" fill="${SEC}">${fmtPct(r.excess_3m)}</text>`;});
  s+=`<text x="0" y="${H-8}" class="mono" font-size="9.5" fill="${MUT}">前 26 名 · 一行读完四段接力，深浅 = 强度，左右 = 方向</text>`;
  return s+'</svg>';
}
// R5 stagger cascade columns, all 76
function R_cascade(){
  const W=1080,H=270,P=26,base=H-46,cw=(W-P*2)/SORTED.length;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  SORTED.forEach((r,i)=>{const x=P+i*cw, h=Math.max(2,(Math.abs(r.excess_3m)/MX)*(base-26)), pos=r.excess_3m>0;
    s+=`<rect x="${x+0.6}" y="${pos?base-h:base}" width="${cw-1.6}" height="${h}" rx="1.5"
        fill="${pos?INK:MUT}" fill-opacity="${pos?(0.42+0.58*(r.excess_3m/MX)).toFixed(2):0.5}"><title>${esc(r.group)} ${fmtPct(r.excess_3m)}</title></rect>`;});
  s+=`<line x1="${P}" y1="${base}" x2="${W-P}" y2="${base}" stroke="${INK}" stroke-width="1"/>`;
  s+=`<text x="${P}" y="${H-8}" class="mono" font-size="9.5" fill="${MUT}">76 条按强度排开 · 上为跑赢 · 唯一的墨色梯度就是强度本身</text>`;
  return s+'</svg>';
}
// R6 typographic ranking — the name IS the bar
function R_type(n=16){
  const rows=SORTED.slice(0,n),W=1080,rh=25,H=n*rh+34;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  rows.forEach((r,i)=>{const y=24+i*rh, t=r.excess_3m/MX;
    const size=(12+t*15).toFixed(1), wt=t>0.55?700:(t>0.3?600:500);
    s+=`<text x="34" y="${y}" font-size="${size}" font-weight="${wt}" fill="${ramp(0.25+t*0.75)}"
         letter-spacing="-.01em">${esc(r.group)}</text>`;
    s+=`<text x="0" y="${y}" class="mono" font-size="9.5" fill="${LINE}">${String(i+1).padStart(2,'0')}</text>`;
    s+=`<text x="${W-92}" y="${y}" text-anchor="end" class="mono" font-size="${(10+t*5).toFixed(1)}" fill="${pol(r.excess_3m)}">${fmtPct(r.excess_3m)}</text>`;
    s+=pips(W-78,y-4,r,SEC);});
  s+=`<text x="0" y="${H-6}" class="mono" font-size="9.5" fill="${MUT}">字号和墨色就是柱长 · 没有一根柱子</text>`;
  return s+'</svg>';
}
// R7 rank-shift slope: rank by 1M vs rank by 3M
function R_shift(n=18){
  const by=(k)=>{const o=[...R].sort((a,b)=>(b[k]??-9)-(a[k]??-9));return new Map(o.map((r,i)=>[r.group,i+1]));};
  const A=by('perf_1m'),B=by('excess_3m');
  const rows=SORTED.slice(0,n),W=1080,H=n*20+48,L=300,Rr=300;
  const Y=rk=>26+((rk-1)/(R.length-1))*(H-70);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<text x="${L}" y="14" text-anchor="end" class="mono" font-size="9.5" fill="${MUT}">按 1M 排</text>`;
  s+=`<text x="${W-Rr}" y="14" class="mono" font-size="9.5" fill="${MUT}">按 3M 超额排</text>`;
  rows.forEach(r=>{const a=A.get(r.group)||99,b=B.get(r.group)||99, up=b<a, c=up?TOOK:REF;
    s+=`<line x1="${L}" y1="${Y(a)}" x2="${W-Rr}" y2="${Y(b)}" stroke="${c}" stroke-width="${1+Math.abs(a-b)/14}" opacity=".8"/>`;
    s+=`<text x="${L-8}" y="${Y(a)+3.5}" text-anchor="end" font-size="10.5" fill="${SEC}">${esc(r.group)}</text>`;
    s+=`<text x="${W-Rr+8}" y="${Y(b)+3.5}" font-size="10.5" fill="${INK}">${esc(r.group)} <tspan class="mono" font-size="9" fill="${c}">${a>b?'▲'+(a-b):(a<b?'▼'+(b-a):'—')}</tspan></text>`;});
  s+=`<text x="0" y="${H-6}" class="mono" font-size="9.5" fill="${MUT}">线越粗 = 名次挪得越多 · 蓝 = 短线比中线更强（正在接棒）</text>`;
  return s+'</svg>';
}
// R8 pictorial pips — persistence as the primary mark
function R_pictorial(n=16){
  const rows=SORTED.slice(0,n),W=1080,rh=25,H=n*rh+40,L=190,U=13;
  const mx=Math.max(...rows.map(r=>Math.abs(r.excess_3m)));
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  rows.forEach((r,i)=>{const y=22+i*rh;
    s+=`<text x="${L-12}" y="${y+11}" text-anchor="end" font-size="11" fill="${INK}">${esc(r.group)}</text>`;
    const units=Math.round((Math.abs(r.excess_3m)/mx)*38);
    for(let k=0;k<38;k++){
      s+=`<rect x="${L+k*(U+2.4)*0.62}" y="${y+2}" width="${U*0.5}" height="${U}" rx="2"
          fill="${k<units?pol(r.excess_3m):LINE}" fill-opacity="${k<units?0.9:0.5}"/>`;}
    s+=`<text x="${L+38*(U+2.4)*0.62+10}" y="${y+11}" class="mono" font-size="10" fill="${SEC}">${fmtPct(r.excess_3m)}</text>`;});
  s+=`<text x="0" y="${H-8}" class="mono" font-size="9.5" fill="${MUT}">每一格 = 相同的一份超额 · 数得清，不用估</text>`;
  return s+'</svg>';
}
