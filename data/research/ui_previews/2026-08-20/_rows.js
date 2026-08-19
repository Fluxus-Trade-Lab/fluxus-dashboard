const ROWS=[
 {t:'AEHR',a:1.9,rs:96},{t:'MSTR',a:3.4,rs:91},{t:'LSCC',a:5.2,rs:88},{t:'AZTA',a:6.8,rs:84},
 {t:'PENG',a:8.1,rs:79},{t:'CBRL',a:-1.4,rs:62},{t:'FRMI',a:-3.2,rs:55},{t:'STDN',a:null,rs:71}];
const STOPS={light:[[0,'#dbe9f6'],[4,'#8fbfe0'],[7,'#e09a72'],[10,'#c9432b']],
             dark:[[0,'#16304d'],[4,'#2b6ea8'],[7,'#c06a2a'],[10,'#f0705a']]};
const hex=c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16));
const lum=c=>{const s=hex(c).map(v=>{v/=255;return v<=.03928?v/12.92:((v+.055)/1.055)**2.4});
  return .2126*s[0]+.7152*s[1]+.0722*s[2]};
const ratio=(a,b)=>{const[x,y]=[lum(a),lum(b)].sort((m,n)=>n-m);return (x+.05)/(y+.05)};
const mix=(a,b,t)=>'#'+hex(a).map((v,i)=>Math.round(v+(hex(b)[i]-v)*t).toString(16).padStart(2,'0')).join('');
function atrFill(v,dark){
  if(v==null||!isFinite(v)||v<0)return null;
  const s=STOPS[dark?'dark':'light'],x=Math.min(v,s[s.length-1][0]);let bg=s[s.length-1][1];
  for(let i=1;i<s.length;i++){if(x<=s[i][0]){bg=mix(s[i-1][1],s[i][1],(x-s[i-1][0])/(s[i][0]-s[i-1][0]));break}}
  const inks=dark?['#ffffff','#12110F']:['#292524','#ffffff'];
  return {bg,fg:ratio(inks[0],bg)>=ratio(inks[1],bg)?inks[0]:inks[1]};
}
const isDark=()=>matchMedia('(prefers-color-scheme:dark)').matches;
