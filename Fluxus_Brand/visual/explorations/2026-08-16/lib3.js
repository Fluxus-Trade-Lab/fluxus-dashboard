const R=D.rows, DAYS=D.days, PT=D.ptLabels, LEG=D.legLabels;
const SORTED=[...R].sort((a,b)=>b.excess_3m-a.excess_3m);
const MX=Math.max(...R.map(r=>Math.abs(r.excess_3m)));
const MA=Math.max(...R.map(r=>Math.abs(r.rs_accel||0)));
const CMAX=Math.max(...R.flatMap(r=>r.cum.map(Math.abs)))*0.82;
const INK='var(--ink)',SEC='var(--sec)',MUT='var(--mut)',LINE='var(--line)',
      TOOK='var(--took)',REF='var(--refused)';
const pol=v=>v>0?TOOK:REF;
const fmtPct=(v,d=0)=>v==null?'—':(v>0?'+':'')+(v*100).toFixed(d)+'%';
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const PICKS=['High Octane','Cybersecurity','Drones','Regional Banks'].map(n=>R.find(r=>r.group===n)).filter(Boolean);
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

/* ---------- Compare · 曲线（3 个月） ---------- */
function curve(opts={}){
  const {burst=false,shade=false,ghost=true,W=1080,H=336,L=70,Rp=214,T=26,B=46}=opts;
  const d0=DAYS[0], X=d=>L+((d-d0)/(0-d0))*(W-L-Rp);
  const Y=v=>T+(1-(Math.max(-CMAX,Math.min(CMAX,v))+CMAX)/(2*CMAX))*(H-T-B);
  const path=r=>r.cum.map((v,i)=>`${X(DAYS[i]).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${L}" y1="${Y(0)}" x2="${W-Rp}" y2="${Y(0)}" stroke="${INK}" stroke-width="1"/>`;
  s+=`<text x="${L-8}" y="${Y(0)+3}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  [.2,.4,-.2].forEach(t=>{if(Math.abs(t)<CMAX)
    s+=`<line x1="${L}" y1="${Y(t)}" x2="${W-Rp}" y2="${Y(t)}" stroke="${LINE}" stroke-dasharray="2 4"/>`
     +`<text x="${L-8}" y="${Y(t)+3}" text-anchor="end" class="mono" font-size="9" fill="${LINE}">${fmtPct(t)}</text>`;});
  DAYS.forEach((dd,i)=>{s+=`<line x1="${X(dd)}" y1="${T}" x2="${X(dd)}" y2="${H-B}" stroke="${LINE}" stroke-width=".7" opacity=".85"/>`
   +`<text x="${X(dd)}" y="${H-B+17}" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${PT[i]}</text>`;});
  if(ghost)R.forEach(r=>s+=`<polyline points="${path(r)}" fill="none" stroke="${LINE}" stroke-width=".7" opacity=".5"/>`);
  const used=[];
  PICKS.forEach((r,pi)=>{const c=pol(r.cum[3]);
    if(shade)s+=`<polygon points="${X(d0)},${Y(0)} ${path(r)} ${X(0)},${Y(0)}" fill="${c}" opacity=".07"/>`;
    if(burst){const mx=Math.max(...r.legs.map(Math.abs));
      r.legs.forEach((v,i)=>{const w=1.3+Math.abs(v)/mx*4.2;
        s+=`<line x1="${X(DAYS[i])}" y1="${Y(r.cum[i])}" x2="${X(DAYS[i+1])}" y2="${Y(r.cum[i+1])}"
             stroke="${c}" stroke-width="${w.toFixed(2)}" stroke-linecap="round"/>`;});
    } else {
      s+=`<polyline points="${path(r)}" fill="none" stroke="${c}" stroke-width="2.5" stroke-linejoin="round"
           stroke-dasharray="2000" stroke-dashoffset="2000">
           <animate attributeName="stroke-dashoffset" from="2000" to="0" dur="1.25s" begin="${(pi*0.15).toFixed(2)}s" fill="freeze"/></polyline>`;}
    r.cum.forEach((v,i)=>s+=`<circle cx="${X(DAYS[i])}" cy="${Y(v)}" r="${i===3?4.4:2.4}" fill="${c}" opacity="${burst?1:0}">${burst?'':
      `<animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(pi*0.15+0.32*i).toFixed(2)}s" fill="freeze"/>`}</circle>`);
    let ly=Y(r.cum[3]); while(used.some(u=>Math.abs(u-ly)<26))ly-=26; used.push(ly);
    const op=burst?'':`<animate attributeName="opacity" from="0" to="1" dur=".4s" begin="${(pi*0.15+1.1).toFixed(2)}s" fill="freeze"/>`;
    s+=`<text x="${W-Rp+12}" y="${ly+3}" font-size="11.5" font-weight="600" fill="${c}" opacity="${burst?1:0}">${esc(r.group)}${op}</text>`;
    s+=`<text x="${W-Rp+12}" y="${ly+16}" class="mono" font-size="9.5" fill="${MUT}" opacity="${burst?1:0}">3个月累计 ${fmtPct(r.cum[3],1)}${op}</text>`;});
  s+=`<text x="${L}" y="14" class="mono" font-size="9" fill="${MUT}">纵轴 = 从 3 个月前起相对 SPY 累计领先 · 终点就是榜单印的那个数 · 横轴按真实日历间距</text>`;
  return s+'</svg>';
}
/* ---------- Compare · 赛道（3 段） ---------- */
function race(opts={}){
  const {n=10,rh=44}=opts;
  const runners=[...R].sort((a,b)=>b.cum[3]-a.cum[3]).slice(0,n);
  const W=1080,H=runners.length*rh+66,L=250,TRACK=W-L-118,BEHIND=92;
  const total=Math.max(...R.map(r=>r.legs.reduce((s,v)=>s+Math.max(0,v),0)));
  const step=v=>(v/total)*(TRACK/1.15);
  const posAt=(r,j)=>L+r.legs.slice(0,j).reduce((a,b)=>a+step(b),0);
  const DUR=1.0,GAP=.12;
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  for(let j=0;j<3;j++){const x=L+TRACK*(j+1)/3;
    s+=`<line x1="${x}" y1="26" x2="${x}" y2="${H-40}" stroke="${LINE}" stroke-dasharray="3 4"/>`
     +`<text x="${x}" y="20" text-anchor="middle" class="mono" font-size="9" fill="${MUT}">${LEG[j]} 结束</text>`;}
  s+=`<line x1="${L}" y1="26" x2="${L}" y2="${H-40}" stroke="${INK}" stroke-width="1.4"/>`
   +`<text x="${L}" y="20" text-anchor="middle" class="mono" font-size="9" fill="${INK}">起跑 · SPY</text>`
   +`<text x="${L-BEHIND/2}" y="${H-26}" text-anchor="middle" class="mono" font-size="8.5" fill="${REF}">← 落后区</text>`;
  runners.forEach((r,i)=>{const y=34+i*rh;
    s+=`<rect x="${L-BEHIND}" y="${y}" width="${TRACK+BEHIND}" height="${rh-14}" rx="${(rh-14)/2}" fill="${LINE}" opacity=".22"/>`;
    s+=`<text x="${L-BEHIND-12}" y="${y+(rh-14)/2+4}" text-anchor="end" font-size="11.5" font-weight="600" fill="${INK}">${esc(r.group)}</text>`;
    let x=L,t=0;
    r.legs.forEach((v,j)=>{const x2=x+step(v),c=v>0?TOOK:REF;
      s+=`<rect x="${Math.min(x,x2).toFixed(1)}" y="${y+2}" width="0" height="${rh-18}" rx="${(rh-18)/2}"
           fill="${c}" fill-opacity="${(0.4+j*0.25).toFixed(2)}">
           <animate attributeName="width" from="0" to="${Math.abs(x2-x).toFixed(1)}" dur="${DUR}s" begin="${t.toFixed(2)}s" fill="freeze"/></rect>`;
      if(Math.abs(x2-x)>50)
        s+=`<text x="${(Math.min(x,x2)+Math.abs(x2-x)/2).toFixed(1)}" y="${y+(rh-14)/2+3}" text-anchor="middle" class="mono"
             font-size="8.5" fill="#f2f0e9" opacity="0">${fmtPct(v,0)}<animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(t+DUR*.7).toFixed(2)}s" fill="freeze"/></text>`;
      x=x2;t+=DUR+GAP;});
    s+=`<circle cy="${y+(rh-14)/2}" r="${5.5+Math.sqrt(r.members)*0.22}" fill="${pol(r.cum[3])}" cx="${L}">
        ${r.legs.map((v,j)=>`<animate attributeName="cx" from="${posAt(r,j).toFixed(1)}" to="${posAt(r,j+1).toFixed(1)}" dur="${DUR}s" begin="${(j*(DUR+GAP)).toFixed(2)}s" fill="freeze"/>`).join('')}</circle>`;
    s+=`<text x="${W-104}" y="${y+(rh-14)/2+4}" class="mono" font-size="10.5" fill="${pol(r.cum[3])}" opacity="0">${fmtPct(r.cum[3],1)}
         <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="3.6s" fill="freeze"/></text>`;
    const bi=r.legs.indexOf(Math.max(...r.legs));
    if(r.legs[bi]>0.08)s+=`<text x="${(posAt(r,bi)+step(r.legs[bi])/2).toFixed(1)}" y="${y-1}" text-anchor="middle" class="mono" font-size="8" fill="${MUT}" opacity="0">爆发
      <animate attributeName="opacity" from="0" to="1" dur=".3s" begin="${(bi*(DUR+GAP)+0.85).toFixed(2)}s" fill="freeze"/></text>`;});
  s+=`<text x="${L}" y="${H-14}" class="mono" font-size="9.5" fill="${MUT}">每段跑出的距离 = 该段相对 SPY 的领先；负的那段真的把人拖到起跑线以后 · 三道虚线是分段计时点</text>`;
  return s+'</svg>';
}
/* ---------- Ranked · 零线居中（去掉成员数与 ETF 代理） ---------- */
function diverge(opts={}){
  const {n=14,legs=false}=opts;
  const show=[...SORTED.slice(0,n),null,...SORTED.slice(-n)];
  const W=1080,rh=19,H=show.length*rh+30,C=legs?438:508,HALF=legs?330:400;
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
    if(legs){const bx=W-186,bw=58;
      r.legs.forEach((v,j)=>{const hh=Math.min(11,Math.abs(v)/0.36*11);
        s+=`<rect x="${bx+j*bw+2}" y="${y+6-(v>0?hh:0)}" width="${bw-6}" height="${Math.max(1.2,hh)}" fill="${pol(v)}" fill-opacity=".8"><title>${LEG[j]} ${fmtPct(v,1)}</title></rect>`;});
      s+=`<line x1="${bx}" y1="${y+6}" x2="${bx+3*bw-4}" y2="${y+6}" stroke="${LINE}" stroke-width=".7"/>`;}});
  if(legs)LEG.forEach((l,j)=>s+=`<text x="${W-186+j*58+26}" y="6" text-anchor="middle" class="mono" font-size="8" fill="${LINE}">${l}</text>`);
  return s+'</svg>';
}
