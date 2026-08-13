#!/usr/bin/env python3
"""把候选图生成一张本地筛选网页。

    python3 scripts/build_visual_gallery.py && open visuals/gallery.html

页面里：
    点图 = 选中 / 取消      双击 = 放大看
    1–9  = 选中第 n 张       J / K = 下一条 / 上一条
    X    = 这条全都不行（标记为需要换搜索词）
    选择存在浏览器 localStorage,随时点「导出 picks.json」存到 visuals/。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "visuals"
MANIFEST = OUT / "manifest.json"
GALLERY = OUT / "gallery.html"

PAGE = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>Fluxus 视觉库 · 筛选台</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#0b0b0c; color:#e8e6e3;
         font:14px/1.6 -apple-system,"PingFang SC","Helvetica Neue",sans-serif; }}
  header {{ position:sticky; top:0; z-index:20; background:#111113ee; backdrop-filter:blur(8px);
            border-bottom:1px solid #26262a; padding:12px 20px;
            display:flex; align-items:center; gap:16px; flex-wrap:wrap; }}
  h1 {{ font-size:15px; margin:0; letter-spacing:.06em; font-weight:600; }}
  .stat {{ font-size:12px; color:#8a8a92; }}
  .stat b {{ color:#e8e6e3; font-weight:600; }}
  button {{ background:#1c1c20; color:#d8d6d3; border:1px solid #33333a; border-radius:6px;
            padding:5px 11px; font-size:12px; cursor:pointer; font-family:inherit; }}
  button:hover {{ border-color:#5a5a66; }}
  button.on {{ background:#2f6f4e; border-color:#3f8f66; color:#fff; }}
  main {{ padding:20px; max-width:1600px; margin:0 auto; }}
  .card {{ border:1px solid #212126; border-radius:10px; margin-bottom:14px;
           background:#101013; overflow:hidden; scroll-margin-top:70px; }}
  .card.cur {{ border-color:#5a6f8f; }}
  .card.done {{ opacity:.55; }}
  .card.dead {{ border-color:#6b3030; }}
  .head {{ display:flex; gap:12px; align-items:baseline; padding:10px 14px;
           border-bottom:1px solid #1c1c20; flex-wrap:wrap; }}
  .code {{ font-weight:700; font-size:13px; letter-spacing:.08em; color:#9fb4d4; }}
  .title {{ font-size:14px; }}
  .sec {{ font-size:11px; color:#6b6b75; margin-left:auto; }}
  .desc {{ padding:8px 14px 0; color:#a8a6a2; font-size:13px; }}
  .q {{ padding:2px 14px 10px; font-size:11px; color:#6b6b75; font-family:ui-monospace,monospace; }}
  .strip {{ display:flex; gap:8px; padding:0 14px 14px; overflow-x:auto; }}
  figure {{ margin:0; position:relative; flex:0 0 auto; cursor:pointer; }}
  figure img {{ height:150px; width:auto; max-width:340px; object-fit:cover; display:block;
                border-radius:6px; border:2px solid transparent; background:#18181c; }}
  figure.pick img {{ border-color:#4ade80; }}
  figure .n {{ position:absolute; top:4px; left:4px; background:#000a; border-radius:4px;
               padding:0 5px; font-size:10px; color:#bbb; }}
  figure.pick .n {{ background:#4ade80; color:#04220f; font-weight:700; }}
  .empty {{ padding:0 14px 14px; color:#6b6b75; font-size:12px; }}
  #lb {{ position:fixed; inset:0; background:#000e; display:none; z-index:50;
         align-items:center; justify-content:center; padding:30px; }}
  #lb img {{ max-width:100%; max-height:100%; }}
  #lb .meta {{ position:absolute; bottom:12px; left:0; right:0; text-align:center;
               font-size:12px; color:#999; }}
</style></head><body>
<header>
  <h1>FLUXUS 视觉库 · 筛选台</h1>
  <span class="stat"><b id="s-done">0</b>/<span id="s-all">0</span> 条已处理 ·
        选中 <b id="s-pick">0</b> 张 · 弃 <b id="s-dead">0</b> 条</span>
  <button id="f-todo">只看未筛</button>
  <button id="f-pick">只看已选</button>
  <button id="f-all" class="on">全部</button>
  <button id="export">导出 picks.json</button>
  <button id="reset">清空选择</button>
</header>
<main id="app"></main>
<div id="lb"><img><div class="meta"></div></div>
<script>
const DATA = {data};
const KEY = 'fluxus-visual-picks-v1';
let state = JSON.parse(localStorage.getItem(KEY) || '{{"picks":{{}},"dead":{{}}}}');
let cur = 0;

const save = () => localStorage.setItem(KEY, JSON.stringify(state));
const picksOf = c => state.picks[c] || [];

function render() {{
  const app = document.getElementById('app');
  app.innerHTML = DATA.map((e, i) => {{
    const picks = picksOf(e.code);
    const dead = !!state.dead[e.code];
    const cls = ['card', i === cur ? 'cur' : '', dead ? 'dead' : (picks.length ? 'done' : '')].join(' ');
    const shots = e.images.map((im, n) => `
      <figure class="${{picks.includes(im.file) ? 'pick' : ''}}" data-code="${{e.code}}" data-file="${{im.file}}"
              data-page="${{im.page || ''}}" data-w="${{im.width||''}}" data-h="${{im.height||''}}">
        <img src="${{im.file}}" loading="lazy" alt="">
        <span class="n">${{n + 1}}</span>
      </figure>`).join('');
    return `<section class="${{cls}}" id="c-${{e.code}}" data-code="${{e.code}}">
      <div class="head"><span class="code">${{e.code}}</span><span class="title">${{e.title}}</span>
        <span class="sec">${{e.section || ''}}${{dead ? ' · 已弃' : ''}}</span></div>
      <div class="desc">${{e.desc || ''}}</div>
      <div class="q">${{e.query || '（无搜索词）'}}</div>
      ${{e.images.length ? `<div class="strip">${{shots}}</div>`
                        : '<div class="empty">没有候选图 — 改搜索词后跑 --refetch</div>'}}
    </section>`;
  }}).join('');
  applyFilter();
  stats();
}}

function stats() {{
  const picked = DATA.filter(e => picksOf(e.code).length).length;
  const dead = Object.keys(state.dead).filter(k => state.dead[k]).length;
  document.getElementById('s-all').textContent = DATA.length;
  document.getElementById('s-done').textContent = picked + dead;
  document.getElementById('s-pick').textContent =
    Object.values(state.picks).reduce((a, b) => a + b.length, 0);
  document.getElementById('s-dead').textContent = dead;
}}

let filter = 'all';
function applyFilter() {{
  document.querySelectorAll('.card').forEach(el => {{
    const c = el.dataset.code;
    const has = picksOf(c).length > 0, dead = !!state.dead[c];
    el.style.display =
      filter === 'todo' ? (has || dead ? 'none' : '') :
      filter === 'pick' ? (has ? '' : 'none') : '';
  }});
}}

function toggle(code, file) {{
  const list = picksOf(code);
  const i = list.indexOf(file);
  if (i >= 0) list.splice(i, 1); else list.push(file);
  state.picks[code] = list;
  if (list.length) state.dead[code] = false;
  save(); render();
}}

document.addEventListener('click', ev => {{
  const fig = ev.target.closest('figure');
  if (fig) {{ cur = DATA.findIndex(e => e.code === fig.dataset.code); toggle(fig.dataset.code, fig.dataset.file); }}
}});
document.addEventListener('dblclick', ev => {{
  const fig = ev.target.closest('figure');
  if (!fig) return;
  const lb = document.getElementById('lb');
  lb.querySelector('img').src = fig.dataset.file;
  lb.querySelector('.meta').textContent = `${{fig.dataset.w}}×${{fig.dataset.h}} · ${{fig.dataset.page}}`;
  lb.style.display = 'flex';
}});
document.getElementById('lb').onclick = e => e.currentTarget.style.display = 'none';

document.addEventListener('keydown', ev => {{
  if (ev.metaKey || ev.ctrlKey) return;
  const e = DATA[cur];
  if (ev.key >= '1' && ev.key <= '9') {{
    const im = e.images[+ev.key - 1];
    if (im) toggle(e.code, im.file);
  }} else if (ev.key === 'j' || ev.key === 'J') {{
    cur = Math.min(cur + 1, DATA.length - 1); render(); focusCur();
  }} else if (ev.key === 'k' || ev.key === 'K') {{
    cur = Math.max(cur - 1, 0); render(); focusCur();
  }} else if (ev.key === 'x' || ev.key === 'X') {{
    state.dead[e.code] = !state.dead[e.code];
    if (state.dead[e.code]) state.picks[e.code] = [];
    save(); render();
  }} else if (ev.key === 'Escape') {{
    document.getElementById('lb').style.display = 'none';
  }}
}});
const focusCur = () => document.getElementById('c-' + DATA[cur].code)
  ?.scrollIntoView({{block: 'start', behavior: 'smooth'}});

document.getElementById('export').onclick = () => {{
  const out = {{
    picks: Object.fromEntries(Object.entries(state.picks).filter(([, v]) => v.length)),
    dead: Object.keys(state.dead).filter(k => state.dead[k]),
  }};
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 2)], {{type: 'application/json'}}));
  a.download = 'picks.json';
  a.click();
}};
document.getElementById('reset').onclick = () => {{
  if (confirm('清空所有选择？')) {{ state = {{picks: {{}}, dead: {{}}}}; save(); render(); }}
}};
for (const [id, f] of [['f-todo','todo'], ['f-pick','pick'], ['f-all','all']]) {{
  document.getElementById(id).onclick = () => {{
    filter = f;
    ['f-todo','f-pick','f-all'].forEach(x => document.getElementById(x).classList.toggle('on', x === id));
    applyFilter();
  }};
}}
render();
</script></body></html>
"""


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = [e for e in manifest["entries"]]
    GALLERY.write_text(PAGE.format(data=json.dumps(entries, ensure_ascii=False)), encoding="utf-8")
    shots = sum(len(e["images"]) for e in entries)
    print(f"{GALLERY.relative_to(ROOT)} — {len(entries)} 条 / {shots} 张候选")
    print(f"打开：open {GALLERY.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
