#!/usr/bin/env python3
"""把两面墙内嵌进自包含网页 index.html:横向漫游 + 翻面 + 细看。"""
from pathlib import Path

HERE = Path(__file__).parent
front = (HERE.parent / "sketches/sketch_03_wall.svg").read_text()
back = (HERE.parent / "sketches/sketch_04_back_wall.svg").read_text()

html = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>同一个动作 · The Same Gesture — 2026 H1</title>
<style>
  html,body{margin:0;height:100%;background:#171512;color:#d8d2c4;
    font-family:Georgia,"Songti SC",serif;overflow:hidden}
  .face{position:absolute;inset:0 0 76px 0;overflow-x:auto;overflow-y:hidden;
    opacity:0;pointer-events:none;transition:opacity .55s ease;
    scrollbar-width:thin;scrollbar-color:#4a443a #171512}
  .face.show{opacity:1;pointer-events:auto}
  .wall{min-height:100%;padding:2.5vh 6vw;box-sizing:border-box;display:flex;align-items:center}
  .wall svg{height:84vh;width:auto;flex:none;display:block;box-shadow:0 30px 90px rgba(0,0,0,.55);
    transition:height .6s ease;background:transparent}
  .zoomed .wall svg{height:200vh}
  .zoomed .wall{align-items:flex-start}
  .zoomed .face{overflow-y:auto}
  #bar{position:fixed;left:0;right:0;bottom:0;height:76px;display:flex;gap:14px;
    align-items:center;justify-content:center;background:linear-gradient(transparent,#0d0c0a 40%)}
  button{background:none;border:1px solid #6a6354;color:#d8d2c4;font:inherit;
    font-size:15px;padding:9px 22px;border-radius:22px;cursor:pointer;letter-spacing:.1em}
  button:hover{border-color:#c1912a;color:#e8cf7a}
  #hint{position:fixed;top:18px;right:24px;font-size:13px;opacity:.55;font-style:italic}
  #side{position:fixed;top:16px;left:24px;font-size:14px;opacity:.8;letter-spacing:.2em}
  #seal{display:inline-block;width:10px;height:10px;background:#9e2b1f;border-radius:2px;
    margin-right:8px;vertical-align:baseline}
</style>
</head>
<body>
<div id="frontFace" class="face show"><div class="wall">__FRONT__</div></div>
<div id="backFace" class="face"><div class="wall">__BACK__</div></div>
<div id="side"><span id="seal"></span><span id="sideName">正面 · 园子</span></div>
<div id="hint">横向滚动 = 在墙前走过 · 一月在左,七月在右</div>
<div id="bar">
  <button id="flipBtn">翻 面</button>
  <button id="zoomBtn">走 近 看</button>
</div>
<script>
const front=document.getElementById('frontFace'),back=document.getElementById('backFace');
const sideName=document.getElementById('sideName'),hint=document.getElementById('hint');
let showingFront=true,zoomed=false;
function cur(){return showingFront?front:back}
// 滚轮纵向 -> 横向漫游
for(const f of [front,back]){
  f.addEventListener('wheel',e=>{
    if(Math.abs(e.deltaY)>Math.abs(e.deltaX)&&!zoomed){f.scrollLeft+=e.deltaY;e.preventDefault();}
  },{passive:false});
}
document.getElementById('flipBtn').onclick=()=>{
  const a=cur();
  const frac=a.scrollLeft/Math.max(a.scrollWidth-a.clientWidth,1);
  showingFront=!showingFront;
  const b=cur();
  front.classList.toggle('show',showingFront);
  back.classList.toggle('show',!showingFront);
  // 反面是镜像:翻到布的另一侧,站在墙的同一个位置
  requestAnimationFrame(()=>{b.scrollLeft=(1-frac)*(b.scrollWidth-b.clientWidth);});
  sideName.textContent=showingFront?'正面 · 园子':'反面 · 手迹';
  hint.textContent=showingFront?'横向滚动 = 在墙前走过 · 一月在左,七月在右'
                              :'布翻过来了 · 一月在右 · 悬线垂深 = 持仓天数';
};
document.getElementById('zoomBtn').onclick=e=>{
  zoomed=!zoomed;document.body.classList.toggle('zoomed',zoomed);
  e.target.textContent=zoomed?'退 后 看':'走 近 看';
};
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowRight')cur().scrollLeft+=160;
  if(e.key==='ArrowLeft')cur().scrollLeft-=160;
  if(e.key==='f'||e.key==='F')document.getElementById('flipBtn').click();
  if(e.key==='z'||e.key==='Z')document.getElementById('zoomBtn').click();
});
</script>
</body>
</html>
"""
html = html.replace("__FRONT__", front).replace("__BACK__", back)
out = HERE / "index.html"
out.write_text(html)
print("wrote", out, out.stat().st_size, "bytes")
