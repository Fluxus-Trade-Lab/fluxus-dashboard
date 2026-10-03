#!/usr/bin/env python3
"""提词卡 v2：一页幻灯片配一段提词（Andy 2026-10-03「幻灯片设计和提词卡的结合设计的不好」）。

读幻灯片生成器用的同一份内容 JSON（每页 slides[i].cue = {say, explain[], asks[{ask, quotes[{text,zh,date,source}]}]}），
左边是这一页幻灯片的图，右边是：怎么讲 · 名词解释（会员没有 dashboard，屏幕上每个数都要能讲清）· 引导问题 → 你当时的原话。
用法：python3 build_cue_slides.py <ep.json> <slides_png_dir> <out_dir>
  out_dir 下生成 index.html 与 s/NN.jpg（发 Artifact 时用 files 一起传）。
⚠️ 内容是付费课程材料：只在课程私有仓跑，产物不进公开仓。
"""
import html, json, subprocess, sys
from pathlib import Path

E = html.escape


def main():
    ep, png_dir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    D = json.load(open(ep, encoding='utf-8'))
    pngs = sorted(png_dir.glob('*.png'))
    if len(pngs) != len(D['slides']):
        raise SystemExit(f'幻灯片 {len(pngs)} 张，内容 {len(D["slides"])} 页，对不上：先重新渲染幻灯片')
    (out / 's').mkdir(parents=True, exist_ok=True)
    nav, body = [], []
    for i, (s, p) in enumerate(zip(D['slides'], pngs), 1):
        jpg = out / 's' / f'{i:02d}.jpg'
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '82', str(p), '--out', str(jpg)],
                       check=True, capture_output=True)
        c = s.get('cue', {})
        title = s.get('title') or {'title': '封面', 'closing': '收尾'}.get(s['type']) or s.get('name') or f'段落 {s.get("idx", "")}'
        nav.append(f'<a href="#p{i}">{i:02d}</a>')
        ex = ''.join(f'<li>{E(x)}</li>' for x in c.get('explain', []))
        asks = ''
        for a in c.get('asks', []):
            qs = ''.join(
                f'<blockquote><p>{E(q["text"])}</p>'
                + (f'<p class="zh">【翻译】{E(q["zh"].removeprefix("【翻译】"))}</p>' if q.get('zh') else '')
                + f'<cite>{E(q.get("date", ""))} · {E(q.get("source", "").split(" · ")[-1][:40])}</cite></blockquote>'
                for q in a['quotes'])
            asks += f'<div class="ask"><h4>问：{E(a["ask"])}</h4>{qs}</div>'
        body.append(
            f'<section id="p{i}"><div class="pic"><div class="no">{i:02d} / {len(pngs)}</div>'
            f'<img src="s/{i:02d}.jpg" alt="第 {i} 页"></div><div class="cue"><h2>{E(title)}</h2>'
            + (f'<h3>怎么讲</h3><p class="say">{E(c["say"])}</p>' if c.get('say') else '')
            + (f'<h3>名词解释</h3><ul>{ex}</ul>' if ex else '')
            + (f'<h3>引导问题 → 你当时的原话</h3>{asks}' if asks else '')
            + '</div></section>')
    page = f'''<title>EP01 提词卡</title>
<style>
:root{{--bg:#F2F0EC;--fg:#1D1B18;--mu:#6E6A62;--card:#FFFFFF;--line:#DDD8D0;--ac:#9A4A1F}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#151412;--fg:#ECE9E2;--mu:#9C978D;--card:#1F1D1A;--line:#35322D;--ac:#E39A6B}}}}
:root[data-theme=dark]{{--bg:#151412;--fg:#ECE9E2;--mu:#9C978D;--card:#1F1D1A;--line:#35322D;--ac:#E39A6B}}
body{{background:var(--bg);color:var(--fg);font-family:"PingFang SC","Noto Sans SC",system-ui,sans-serif;margin:0;padding-inline:16px}}
nav{{position:sticky;top:env(safe-area-inset-top,0px);background:var(--bg);display:flex;flex-wrap:wrap;gap:6px;padding-block:10px;border-bottom:1px solid var(--line);z-index:2}}
nav a{{font:13px/1 ui-monospace,Menlo,monospace;color:var(--mu);text-decoration:none;padding:6px 8px;border:1px solid var(--line);background:var(--card)}}
nav a:hover,nav a:focus-visible{{color:var(--fg);border-color:var(--fg)}}
section{{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:28px;padding-block:28px;border-bottom:1px solid var(--line);scroll-margin-top:56px}}
@media (max-width:900px){{section{{grid-template-columns:1fr}}}}
.pic{{position:sticky;top:64px;align-self:start}}
.pic img{{width:100%;display:block;border:1px solid var(--line)}}
.no{{font:12px ui-monospace,Menlo,monospace;color:var(--mu);margin-bottom:6px}}
h2{{font-size:24px;margin:0 0 6px;text-wrap:balance}}
h3{{font-size:13px;letter-spacing:.12em;color:var(--mu);margin:20px 0 6px;font-weight:500}}
.say{{font-size:19px;line-height:1.7;margin:0}}
ul{{margin:0;padding-left:20px}} li{{font-size:16px;line-height:1.65;margin:4px 0}}
.ask{{background:var(--card);border:1px solid var(--line);padding:12px 16px;margin:10px 0}}
.ask h4{{margin:0 0 8px;font-size:17px}}
blockquote{{margin:8px 0;padding-left:12px;border-left:3px solid var(--ac)}}
blockquote p{{margin:0;font-size:16px;line-height:1.6}} .zh{{color:var(--mu);font-size:14px!important}}
cite{{display:block;font:12px ui-monospace,Menlo,monospace;color:var(--mu);font-style:normal;margin-top:2px}}
</style>
<nav>{"".join(nav)}</nav>
{"".join(body)}
<script>
document.addEventListener('keydown',e=>{{if(!['ArrowDown','ArrowUp','PageDown','PageUp'].includes(e.key))return;
const ss=[...document.querySelectorAll('section')];const y=window.scrollY+80;
let i=ss.findIndex(s=>s.offsetTop>y-5);if(i<0)i=ss.length;const cur=Math.max(0,i-1);
const t=(e.key==='ArrowDown'||e.key==='PageDown')?Math.min(ss.length-1,cur+1):Math.max(0,cur-1);
e.preventDefault();ss[t].scrollIntoView({{behavior:'smooth'}});}});
</script>'''
    (out / 'index.html').write_text(page, encoding='utf-8')
    print('cue', out / 'index.html', len(pngs), 'pages')


if __name__ == '__main__':
    main()
