# -*- coding: utf-8 -*-
"""联邦看板 v2 —— 层次/优先级/交互/可批注(Artifact 评论)。数据全来自 origin/main，只读。
用法: python3 federation_board_v2.py <repo> <out.html>
"""
import subprocess, sys, json, re, datetime

REPO, OUT = sys.argv[1], sys.argv[2]

def git(*a):
    return subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True).stdout

def show(p):
    return git("show", "origin/main:" + p)

LANES = ["DATA ALEX", "UI Claire", "RND Linda", "Studio Q", "Marketing Steve", "Nighty Zac", "Plumber Joe", "Growth Gary", "OPS Fable"]
LANE_KEYS = {
    "DATA ALEX": ["feat(", "fix(watchlist", "fix(schema", "data(", "chore: market", "screener", "数据端", "alex"],
    "UI Claire": ["frontend", "ui claire", "前端", "claire"],
    "RND Linda": ["regime", "gex", "lamp", "风险线", "linda", "模型 r&d"],
    "Studio Q": ["studio q", "draft", "substack", "mrna", "成稿", "写作线"],
    "Marketing Steve": ["steve", "material(", "fix(posts", "brief", "post:", "调研"],
    "Nighty Zac": ["night(", "prereg(", "collect(", "preview(", "tests(", "adr", "vcp", "amplitude", "stockbee", "zac", "夜间"],
    "Plumber Joe": ["joe", "audit", "contracts(§", "巡检"],
    "Growth Gary": ["growth", "product:", "tool(post", "增长官", "gary"],
    "OPS Fable": ["ops", "rules(", "verdict(", "task(", "rescue(", "projects(", "governance", "team"],
}

def lane_of(text):
    t = text.lower()
    for ln, keys in LANE_KEYS.items():
        for k in keys:
            if k in t:
                return ln
    return "联邦"

now = datetime.datetime.now()
cards = []
cid = [0]

def add(col, pri, title, src, lane=None, date=""):
    cid[0] += 1
    cards.append(dict(id="K%03d" % cid[0], col=col, pri=pri, lane=lane or lane_of(title), t=title.strip()[:180], src=src, d=date))

# ---- 待认领:门铃/待合/契约 ----
reports = sorted(re.findall(r"night_reports/(2026-\d\d-\d\d)\.md", git("ls-tree", "-r", "--name-only", "origin/main", "data/research/night_reports/")))
if reports:
    latest = show("data/research/night_reports/%s.md" % reports[-1])
    sec = re.search(r"门铃待按[^\n]*\n(.*?)(\n## |\Z)", latest, re.S)
    if sec:
        for who, what in re.findall(r"\| *\*?\*?([^|*]+?)\*?\*? *\| *([^|]+?) *\|", sec.group(1)):
            if "收件人" in who or "---" in who:
                continue
            add("claim", 1, what.strip(), "晨报 %s 门铃待按" % reports[-1], lane_of(who), reports[-1][5:])

for b in git("branch", "-r", "--no-merged", "origin/main").splitlines():
    b = b.strip()
    if not b or "HEAD" in b or "archive/" in b:
        continue
    n = git("rev-list", "--count", "origin/main.." + b).strip()
    if n and n != "0":
        last = git("log", "-1", "--format=%ad|%s", "--date=format:%m-%d", b).strip().split("|", 1)
        add("claim", 2, "%s（+%s commit）%s" % (b.replace("origin/", ""), n, ("· " + last[1][:70]) if len(last) > 1 else ""), "待合分支", lane_of(b + " " + (last[1] if len(last) > 1 else "")), last[0] if last else "")

contracts = show("data/reference/DATA_CONTRACTS.md")
for line in contracts.splitlines():
    if not re.match(r"^- \[(?:20)?\d\d-", line):
        continue
    if "✅" in line or "~~" in line:
        continue
    date = (re.search(r"\[(?:2026-)?(\d\d-\d\d)\]", line) or [None, ""])[1]
    txt = re.sub(r"[*`]", "", line)
    head = txt[txt.index("]") + 1:].strip()[:150]
    if "待 Andy" in line or ("Andy 拍板" in line and "已" not in line):
        add("blocked", 0, head, "DATA_CONTRACTS 契约行", lane_of(line), date)
    elif "→" in txt[:60]:
        add("claim", 3, head, "DATA_CONTRACTS 契约行", lane_of(txt[:60]), date)

nowmd = show("NOW.md")
for line in nowmd.splitlines():
    if "待你" in line and "- [ ]" in line:
        add("blocked", 0, re.sub(r"[*\[\]~]", "", line.replace("- [ ]", "")).strip()[:150], "NOW.md 待解锁", "OPS Fable", "")

# ---- 进行中/完成:git log ----
log = git("log", "origin/main", "--since=2 days ago", "--format=%h|%ad|%s", "--date=format:%m-%d %H:%M")
for l in log.splitlines():
    h, ad, s = l.split("|", 2)
    age_h = (now - datetime.datetime.strptime("2026-" + ad, "%Y-%m-%d %H:%M")).total_seconds() / 3600
    if age_h < 24:
        add("done", 9, s[:150], "commit " + h, lane_of(s), ad)
    if ad.split(" ")[0] == now.strftime("%m-%d"):
        pass

log7 = git("log", "origin/main", "--since=7 days ago", "--format=%h|%ad|%s", "--date=format:%m-%d %H:%M")
lane_last, lane_today = {}, {}
for l in log7.splitlines():
    h, ad, s = l.split("|", 2)
    ln = lane_of(s)
    lane_last.setdefault(ln, (ad, s))
    if ad.split(" ")[0] == now.strftime("%m-%d"):
        lane_today.setdefault(ln, []).append(s)
for ln, items in lane_today.items():
    for s in items[:3]:
        add("doing", 9, s[:150], "今日 commit", ln, now.strftime("%m-%d"))

gate = re.search(r"周关卡[^\n]*(\d)\s*/\s*5", nowmd)
gate_n = int(gate.group(1)) if gate else None

lanes_data = []
for ln in LANES:
    last = lane_last.get(ln)
    lanes_data.append(dict(name=ln, today=len(lane_today.get(ln, [])), last=("%s · %s" % (last[0], last[1][:64])) if last else "近 7 天无落地"))

data = dict(ts=now.strftime("%Y-%m-%d %H:%M JST"), cards=cards, lanes=lanes_data, gate=gate_n,
            counts={c: sum(1 for k in cards if k["col"] == c) for c in ["claim", "doing", "blocked", "done"]})

HTML = r"""<!doctype html><meta charset="utf-8">
<title>Fluxus 联邦看板</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{--bg:#f7f6f3;--panel:#efede7;--card:#fdfdfb;--ink:#1c1e21;--mut:#7a786f;--line:#e3e1d8;
--p0:#8f6c1e;--p1:#34638c;--p2:#5b7263;--p3:#8a8578;--blk:#a63d35;--don:#33684d;--acc:#2f4a4d;
--p0bg:#f6efdc;--blkbg:#f6e6e4}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#14161a;--panel:#1b1e23;--card:#20242a;
--ink:#e7e5e0;--mut:#8d8b83;--line:#2b2f36;--p0:#c9a24a;--p1:#6f9cc4;--p2:#8aa693;--p3:#7d7a71;
--blk:#c96a61;--don:#6fa588;--acc:#8fb3b6;--p0bg:#2a2416;--blkbg:#2c1d1b}}
:root[data-theme="dark"]{--bg:#14161a;--panel:#1b1e23;--card:#20242a;--ink:#e7e5e0;--mut:#8d8b83;--line:#2b2f36;
--p0:#c9a24a;--p1:#6f9cc4;--p2:#8aa693;--p3:#7d7a71;--blk:#c96a61;--don:#6fa588;--acc:#8fb3b6;--p0bg:#2a2416;--blkbg:#2c1d1b}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:14px/1.5 "IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;padding:26px 30px 60px}
h1{font:600 22px/1.2 "IBM Plex Serif",Georgia,serif;letter-spacing:.01em}
.sub{color:var(--mut);font-size:12px;margin-top:4px}
.top{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px}
.stats{display:flex;gap:22px;font-variant-numeric:tabular-nums}
.stat b{font:600 24px/1 "IBM Plex Serif",serif;display:block}
.stat span{font-size:11px;color:var(--mut);letter-spacing:.08em;text-transform:uppercase}
.gate{margin-top:14px;display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--mut)}
.gate .bar{width:180px;height:6px;background:var(--panel);border:1px solid var(--line);border-radius:3px;overflow:hidden}
.gate .fill{height:100%;background:var(--don)}
.ctrl{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0 14px;align-items:center}
.chip{border:1px solid var(--line);background:var(--card);color:var(--mut);border-radius:999px;
padding:3px 12px;font-size:12px;cursor:pointer;user-select:none}
.chip.on{border-color:var(--acc);color:var(--acc);font-weight:600}
.chip:focus-visible,#q:focus-visible{outline:2px solid var(--acc);outline-offset:1px}
#q{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px;font:12.5px "IBM Plex Sans";width:200px;margin-left:auto}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;align-items:start}
@media(max-width:980px){.board{grid-template-columns:1fr 1fr}}
.col{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;min-height:60px}
.colh{display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;margin-bottom:10px;letter-spacing:.04em}
.colh .n{color:var(--mut);font-weight:400;font-family:"IBM Plex Mono",monospace}
.lgroup{font-size:10.5px;color:var(--mut);letter-spacing:.1em;text-transform:uppercase;margin:10px 2px 6px}
.k{background:var(--card);border:1px solid var(--line);border-radius:7px;padding:8px 10px 8px 12px;margin-bottom:8px;
position:relative;font-size:12.5px;line-height:1.45;word-break:break-word}
.k::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:7px 0 0 7px;background:var(--pc)}
.k .m{display:flex;gap:8px;align-items:baseline;margin-bottom:3px;flex-wrap:wrap}
.k .pid{font:500 10px "IBM Plex Mono",monospace;color:var(--pc);border:1px solid var(--pc);
border-radius:3px;padding:0 4px}
.k .kid{font:400 10px "IBM Plex Mono",monospace;color:var(--mut)}
.k .dt{font:400 10px "IBM Plex Mono",monospace;color:var(--mut);margin-left:auto}
.k .src{display:block;margin-top:4px;font-size:10.5px;color:var(--mut)}
.k.p0{background:var(--p0bg)}.k.blkc{background:var(--blkbg)}
details.k summary{cursor:pointer;list-style:none}
details.k summary::-webkit-details-marker{display:none}
.lanes{margin-top:30px}
h2{font:600 15px "IBM Plex Serif",serif;margin-bottom:10px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:12.5px}
th,td{text-align:left;padding:7px 12px;border-bottom:1px solid var(--line)}
th{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut);background:var(--panel)}
tr:last-child td{border-bottom:none}
td.num{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
.note{margin-top:26px;border:1px dashed var(--line);border-radius:8px;padding:12px 14px;font-size:12px;color:var(--mut)}
.note b{color:var(--ink)}
.hid{display:none}
</style>
<body>
<div class="top">
  <div><h1>Fluxus 联邦看板</h1><div class="sub">__TS__ · 唯一数据源 = origin/main · 只读快照，批注见页脚说明</div></div>
  <div class="stats" id="stats"></div>
</div>
<div class="gate" id="gate"></div>
<div class="ctrl" id="ctrl"></div>
<div class="board" id="board"></div>
<div class="lanes"><h2>八线心跳（近 7 天）</h2><table id="lt"><thead><tr><th>线</th><th>今日落地</th><th>最近一次合 main</th></tr></thead><tbody></tbody></table></div>
<div class="note"><b>怎么批注：</b>选中任何一张卡的文字，用右上角评论功能开线程（写上卡号如 K012），在线程里 @claude 激活后 OPS 会话能读到你的批注并转成裁决/挂单。<b>优先级：</b>P0=等你拍板 · P1=门铃待按 · P2=待合分支 · P3=契约行待办。<b>刷新：</b>对 OPS 说「刷新看板」即重新生成同一链接。挂单不挂人：各线开工先来「待认领」列领走自己的。</div>
<script>
const D=__DATA__;
const PRI={0:["P0",'var(--p0)'],1:["P1",'var(--p1)'],2:["P2",'var(--p2)'],3:["P3",'var(--p3)'],9:["",'var(--don)']};
const COLS=[["claim","待认领 · 挂单板"],["doing","进行中 · 今日"],["blocked","等 Andy 拍板"],["done","已完成 · 24h"]];
const COLC={claim:'var(--p1)',doing:'var(--p1)',blocked:'var(--blk)',done:'var(--don)'};
let fLane=null,fPri=null,q="";
const $=s=>document.querySelector(s);
function chips(){
 const lanes=[...new Set(D.cards.map(c=>c.lane))].sort();
 let h='<span class="chip'+(fLane===null?' on':'')+'" data-l="">全部线</span>';
 for(const l of lanes)h+='<span class="chip'+(fLane===l?' on':'')+'" data-l="'+l+'">'+l+'</span>';
 h+='<span style="width:10px"></span>';
 for(const p of [0,1,2,3])h+='<span class="chip'+(fPri===p?' on':'')+'" data-p="'+p+'">P'+p+'</span>';
 h+='<input id="q" placeholder="搜索…" value="'+q.replace(/"/g,'&quot;')+'">';
 $("#ctrl").innerHTML=h;
 $("#ctrl").querySelectorAll(".chip").forEach(ch=>{ch.tabIndex=0;ch.onclick=()=>{ if(ch.dataset.l!==undefined&&ch.dataset.p===undefined){fLane=ch.dataset.l||null;} if(ch.dataset.p!==undefined){const p=+ch.dataset.p;fPri=(fPri===p)?null:p;} render();};ch.onkeydown=e=>{if(e.key==="Enter")ch.onclick()}});
 const qi=$("#q");qi.oninput=()=>{q=qi.value;render(false)};
}
function visible(c){
 if(fLane&&c.lane!==fLane)return false;
 if(fPri!==null&&c.pri!==fPri)return false;
 if(q&&!(c.t+c.lane+c.src+c.id).toLowerCase().includes(q.toLowerCase()))return false;
 return true;
}
function card(c){
 const[pl,pc]=PRI[c.pri]||PRI[9];
 const cls=(c.pri===0?"p0 ":"")+(c.col==="blocked"?"blkc ":"");
 return '<div class="k '+cls+'" style="--pc:'+pc+'" id="'+c.id+'"><div class="m">'+
  (pl?'<span class="pid">'+pl+'</span>':'')+'<span class="kid">'+c.id+'</span>'+
  (c.d?'<span class="dt">'+c.d+'</span>':'')+'</div>'+c.t+
  '<span class="src">'+c.src+' · '+c.lane+'</span></div>';
}
function render(rebuildChips=true){
 if(rebuildChips)chips();
 let bh="";
 for(const[key,label]of COLS){
  const items=D.cards.filter(c=>c.col===key&&visible(c)).sort((a,b)=>a.pri-b.pri);
  let inner="";
  if(key==="claim"){
   const byLane={};items.forEach(c=>{(byLane[c.lane]=byLane[c.lane]||[]).push(c)});
   for(const ln of Object.keys(byLane).sort())
    inner+='<div class="lgroup">'+ln+' · '+byLane[ln].length+'</div>'+byLane[ln].map(card).join("");
  }else inner=items.map(card).join("");
  bh+='<div class="col"><div class="colh" style="color:'+COLC[key]+'">'+label+'<span class="n">'+items.length+'</span></div>'+(inner||'<div style="color:var(--mut);font-size:12px">（空）</div>')+'</div>';
 }
 $("#board").innerHTML=bh;
 const c=D.counts;
 $("#stats").innerHTML=[["待认领",c.claim],["进行中",c.doing],["等拍板",c.blocked],["24h 完成",c.done]]
  .map(([l,n])=>'<div class="stat"><b>'+n+'</b><span>'+l+'</span></div>').join("");
 if(D.gate!==null){$("#gate").innerHTML='🎮 周关卡 '+D.gate+'/5 <div class="bar"><div class="fill" style="width:'+(D.gate*20)+'%"></div></div>';}
 const tb=$("#lt tbody");tb.innerHTML=D.lanes.map(l=>'<tr><td>'+l.name+'</td><td class="num">'+(l.today||"—")+'</td><td style="color:var(--mut)">'+l.last+'</td></tr>').join("");
}
render();
</script>
</body>"""

out = HTML.replace("__TS__", data["ts"]).replace("__DATA__", json.dumps(data, ensure_ascii=False))
open(OUT, "w", encoding="utf-8").write(out)
print("v2 -> %s | cards=%d claim=%d doing=%d blocked=%d done=%d" % (OUT, len(cards), data["counts"]["claim"], data["counts"]["doing"], data["counts"]["blocked"], data["counts"]["done"]))
