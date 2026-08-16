const R=D.rows, LAB=D.segLabels, DAYS=D.segDays;
const SORTED=[...R].sort((a,b)=>b.excess_3m-a.excess_3m);
const INK='var(--ink)',SEC='var(--sec)',MUT='var(--mut)',LINE='var(--line)',TOOK='var(--took)',REF='var(--refused)';
const pol=v=>v>0?TOOK:REF;
const fmtPct=(v,d=1)=>(v>0?'+':'')+(v*100).toFixed(d)+'%';
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const PICKS=['High Octane','Drones','Cybersecurity','Silver'].map(n=>R.find(r=>r.group===n)).filter(Boolean);
const el=s=>{const d=document.createElement('div');d.innerHTML=s.trim();return d.firstChild};
const app=document.getElementById('app');let UID=0;
function block(t,w,opts,extra){const b=el('<section class="block"></section>');
 b.appendChild(el('<h2>'+t+'</h2>'));b.appendChild(el('<p class="why">'+w+'</p>'));
 if(extra)b.insertAdjacentHTML('beforeend',extra);
 opts.forEach(([tag,note,html,foot])=>{const o=el('<div class="opt"></div>');
  o.appendChild(el('<div class="opt-h"><b>'+tag+'</b><span>'+note+'</span></div>'));
  const c=el('<div class="card"></div>');c.innerHTML=html;o.appendChild(c);
  if(foot)o.insertAdjacentHTML('beforeend','<p class="note">'+foot+'</p>');b.appendChild(o);});
 app.appendChild(b);}
function replayable(h,l='重播'){const id='rp'+(++UID);
 return `<div id="${id}">${h}</div><button class="replay" onclick="(()=>{const n=document.getElementById('${id}');n.innerHTML=n.innerHTML})()">▶ ${l}</button>`;}
/* Fritsch–Carlson 单调三次插值：曲线永远不越过相邻两个测点的范围，
   所以它和折线一样诚实，只是好看。这是线上那张图用的同一套。 */
function monotone(pts){
  const n=pts.length; if(n<2)return '';
  const dx=[],dy=[],m=[];
  for(let i=0;i<n-1;i++){dx.push(pts[i+1][0]-pts[i][0]);dy.push(pts[i+1][1]-pts[i][1]);m.push(dy[i]/dx[i]);}
  const t=[m[0]];
  for(let i=1;i<n-1;i++) t.push(m[i-1]*m[i]<=0?0:(m[i-1]+m[i])/2);
  t.push(m[n-2]);
  for(let i=0;i<n-1;i++){if(m[i]===0){t[i]=0;t[i+1]=0;continue;}
    const a=t[i]/m[i],b=t[i+1]/m[i],h=Math.hypot(a,b);
    if(h>3){t[i]=3*a/h*m[i];t[i+1]=3*b/h*m[i];}}
  let d=`M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for(let i=0;i<n-1;i++){const h=dx[i];
    d+=` C${(pts[i][0]+h/3).toFixed(1)},${(pts[i][1]+t[i]*h/3).toFixed(1)}`
     + ` ${(pts[i+1][0]-h/3).toFixed(1)},${(pts[i+1][1]-t[i+1]*h/3).toFixed(1)}`
     + ` ${pts[i+1][0].toFixed(1)},${pts[i+1][1].toFixed(1)}`;}
  return d;}
/* 渐变条：原样保留线上那条——四段（现三段）连成一条连续色带，
   蓝=领先 红=落后，浓度=多远；停靠点与曲线的取样列同一个坐标系。 */
function ribbon(r,key,span,xsPct){
  const v=r[key];
  const col=x=>x==null?'transparent':
    `color-mix(in srgb, ${x>0?'var(--took)':'var(--refused)'} ${Math.round(12+78*Math.min(1,Math.abs(x)/span))}%, transparent)`;
  const stops=v.map((x,i)=>`${col(x)} ${xsPct(i)}%`).join(', ');
  return `<div style="height:10px;border-radius:5px;background:linear-gradient(90deg,${stops})"
    title="${r.group}"></div>`;}
function chart(key,opts={}){
  const {ident=false,W=1080,H=300,L=92,Rp=210,T=26,B=44}=opts;
  const vals=R.flatMap(r=>r[key]); const span=Math.max(...vals.map(Math.abs))*0.86;
  const X=i=>L+i*((W-L-Rp)/(LAB.length-1));
  const Y=v=>T+(1-(Math.max(-span,Math.min(span,v))+span)/(2*span))*(H-T-B);
  const IDENT=['#6b7f8c','#8c7f6b','#7d6b8c','#6b8c7f'];
  const yfmt=v=>key==='rate'?(v*100).toFixed(2)+'%/日':fmtPct(v,0);
  let s=`<svg viewBox="0 0 ${W} ${H}">`;
  s+=`<line x1="${L}" y1="${Y(0)}" x2="${W-Rp}" y2="${Y(0)}" stroke="${INK}" stroke-width="1"/>`;
  s+=`<text x="${L-8}" y="${Y(0)+3}" text-anchor="end" class="mono" font-size="9" fill="${MUT}">SPY</text>`;
  [span*0.55,-span*0.55].forEach(t=>s+=`<line x1="${L}" y1="${Y(t)}" x2="${W-Rp}" y2="${Y(t)}" stroke="${LINE}" stroke-dasharray="2 4"/>`
   +`<text x="${L-8}" y="${Y(t)+3}" text-anchor="end" class="mono" font-size="9" fill="${LINE}">${yfmt(t)}</text>`);
  LAB.forEach((l,i)=>{s+=`<line x1="${X(i)}" y1="${T}" x2="${X(i)}" y2="${H-B}" stroke="${LINE}" stroke-width=".7"/>`
   +`<text x="${X(i)}" y="${H-B+17}" text-anchor="middle" class="mono" font-size="9.5" fill="${MUT}">${l}</text>`
   +`<text x="${X(i)}" y="${H-B+29}" text-anchor="middle" class="mono" font-size="8" fill="${LINE}">${DAYS[i]} 天</text>`;});
  R.forEach(r=>s+=`<path d="${monotone(r[key].map((v,i)=>[X(i),Y(v)]))}" fill="none" stroke="${LINE}" stroke-width=".7" opacity=".5"/>`);
  const used=[];
  PICKS.forEach((r,pi)=>{const v=r[key], base=ident?IDENT[pi%4]:pol(v[v.length-1]);
    const d=monotone(v.map((x,i)=>[X(i),Y(x)]));
    s+=`<path d="${d}" fill="none" stroke="${base}" stroke-width="2.6" stroke-linecap="round"
         stroke-dasharray="1400" stroke-dashoffset="1400">
         <animate attributeName="stroke-dashoffset" from="1400" to="0" dur="1.2s" begin="0s" fill="freeze"/></path>`;
    v.forEach((x,i)=>s+=`<circle cx="${X(i)}" cy="${Y(x)}" r="${i===v.length-1?4.4:2.8}" fill="${base}" opacity="0">
      <animate attributeName="opacity" from="0" to="1" dur=".26s" begin="${(i*0.4).toFixed(2)}s" fill="freeze"/></circle>`);
    let ly=Y(v[v.length-1]); while(used.some(u=>Math.abs(u-ly)<25))ly-=25; used.push(ly);
    s+=`<text x="${W-Rp+12}" y="${ly+3}" font-size="11.5" font-weight="600" fill="${base}" opacity="0">${esc(r.group)}
      <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="1.2s" fill="freeze"/></text>`;
    s+=`<text x="${W-Rp+12}" y="${ly+16}" class="mono" font-size="9.5" fill="${MUT}" opacity="0">${yfmt(v[v.length-1])}
      <animate attributeName="opacity" from="0" to="1" dur=".4s" begin="1.28s" fill="freeze"/></text>`;});
  s+='</svg>';
  const xsPct=i=>(L+i*((W-L-Rp)/(LAB.length-1)))/W*100;
  let rib='<div style="margin-top:10px">';
  PICKS.forEach((r,pi)=>{const base=ident?IDENT[pi%4]:pol(r[key][r[key].length-1]);
    rib+=`<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
      <span style="width:7px;height:7px;border-radius:50%;background:${base};flex:none"></span>
      <div style="flex:1">${ribbon(r,key,span,xsPct)}</div>
      <span class="mono" style="font-size:9.5px;color:var(--mut);width:120px;text-align:right">${esc(r.group)}</span></div>`;});
  rib+='</div>';
  return s+rib;}
