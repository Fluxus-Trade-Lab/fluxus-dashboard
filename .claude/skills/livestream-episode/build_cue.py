#!/usr/bin/env python3
"""直播提词卡 v3：讲稿 JSON + 案例图 + dashboard 截图 → 一页纵向长页（深色、大字，直播时从上往下滚）。
用法：python3 build_cue.py <script.json> <out.html>
图片按相对路径 img/<名> 引用，发布时用 Artifact files 一并上传。"""
import json, sys, html, re

D = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
E = lambda s: html.escape(str(s))

IMG_MAP = {
    'case_A.png': ('img/case_A.png', '案例 A · QQQ'),
    'case_B.png': ('img/case_B.png', '案例 B · SOXX'),
    'case_C.png': ('img/case_C.png', '案例 C · NOW'),
    'dash_market.png': ('img/dash_market.png', 'Dashboard · Market State（10/2 收盘）'),
    'dash_rotation.png': ('img/dash_rotation.png', 'Themes · 主题轮动（10/2）'),
    'dash_screener.png': ('img/dash_screener.png', 'Screener · 今天的漏斗（10/2）'),
    'dash_breadth.png': ('img/dash_breadth.png', 'Market State 详情页'),
    'dash_groups.png': ('img/dash_groups.png', 'Groups 页'),
    '图 0-14': ('img/book_0-14.png', '书 图 0-14 · NVDA 价格周期一圈'),
    '图 1-1': ('img/book_1-1.png', '书 图 1-1 · QQQ 2022 红灯年'),
    '图 2-1': ('img/book_2-1.svg', '书 图 2-1 · 从森林到树木'),
}

def images_in(text):
    found = []
    for k, v in IMG_MAP.items():
        if k in text and v not in found:
            found.append(v)
    return found

def gallery(imgs):
    if not imgs:
        return ''
    out = ['<div class="gal">']
    for src, cap in imgs:
        out.append(f'<figure><button class="zoom" data-src="{E(src)}" data-cap="{E(cap)}" aria-label="放大：{E(cap)}">'
                   f'<img src="{E(src)}" alt="{E(cap)}" loading="lazy"></button><figcaption>{E(cap)}</figcaption></figure>')
    out.append('</div>')
    return ''.join(out)

def ul(items, cls=''):
    return f'<ul class="{cls}">' + ''.join(f'<li>{E(i)}</li>' for i in items) + '</ul>' if items else ''

def ol(items):
    return '<ol class="ops">' + ''.join(f'<li>{E(re.sub(r"^\s*\d+[.、]\s*", "", i))}</li>' for i in items) + '</ol>' if items else ''

def case_block(key, c):
    imgs = images_in(f'case_{key}.png')
    steps = ''.join(
        f'<div class="step"><div class="stop">{E(s.get("stop",""))}</div>'
        f'<p class="say">{E(s.get("say",""))}</p>'
        + (f'<p class="ask">💬 {E(s["ask"])}</p>' if s.get('ask') else '')
        + (f'<p class="rev">✅ {E(s["reveal"])}</p>' if s.get('reveal') else '')
        + '</div>' for s in c.get('replay_steps', []))
    return (f'<section class="case" id="case{key}"><h3>{E(c.get("title",""))}</h3>'
            f'<div class="meta">{E(c.get("chart",""))} · 书：{E(c.get("book_ref",""))}</div>'
            f'{gallery(imgs)}{steps}'
            f'<p class="wrap">一句话收：{E(c.get("wrap","").replace("一句话收：",""))}</p>'
            f'<div class="src">出处：{E(c.get("source",""))}</div></section>')

recap = ''
if D.get('recap_points'):
    rows = ''.join(f'<tr><td>{E(r["pt"])}</td><td class="w">{E(r["where"])}</td><td class="w b">{E(r["book"])}</td></tr>' for r in D['recap_points'])
    recap = (f'<section class="recap" id="recap"><h2>{E(D.get("recap_title","本周五复盘的要点 → 今晚讲在哪"))}</h2>'
             f'<div class="tw"><table><thead><tr><th>复盘要点（10/2 周五）</th><th>讲在哪一段</th><th>对应书</th></tr></thead><tbody>{rows}</tbody></table></div></section>')
segs_html, nav = [], []
for s in D['segments']:
    sid = s['id']
    nav.append(f'<a href="#{sid}">{E(s["no"])} {E(s["title"].split("·")[0].strip())}<span>{E(s["minutes"])}</span></a>')
    body = [f'<p class="goal">🎯 {E(s.get("goal",""))}</p>']
    body.append('<div class="k">讲稿</div>' + ''.join(f'<p class="script">{E(p)}</p>' for p in s.get('script', [])))
    if s.get('points'):
        body.append('<div class="k">要点</div>' + ul(s['points'], 'pts'))
    imgs = images_in(s.get('visual', ''))
    body.append('<div class="k">画面</div>' + f'<p class="vis">{E(s.get("visual",""))}</p>' + gallery(imgs))
    if sid == 's3':
        body.append(''.join(case_block(k, D['cases'][k]) for k in ('A', 'B', 'C')))
    if s.get('ops'):
        body.append('<div class="k">Dashboard 操作</div>' + ol(s['ops']))
    if s.get('ask'):
        body.append('<div class="k">问观众</div>' + ''.join(f'<p class="ask">💬 {E(a)}</p>' for a in s['ask']))
    if sid == 's6' and D.get('homework'):
        body.append('<div class="k">作业</div>' + ''.join(f'<p class="script">{E(l)}</p>' for l in D['homework'].split('\n') if l.strip()))
    if sid == 's5' and D.get('qa_prep'):
        qa = ''.join(f'<details class="qa"><summary>{E(q["q"])}</summary><p>{E(q["a"])}</p><div class="src">{E(q.get("ref",""))}</div></details>' for q in D['qa_prep'])
        body.append('<div class="k">问答预案（点开看答法）</div>' + qa)
    body.append(f'<p class="trans">➜ 过渡：{E(s.get("transition",""))}</p>')
    body.append(f'<div class="clip">✂️ 短片：{E(s.get("clip",""))}</div>')
    segs_html.append(f'<section class="seg" id="{sid}"><header><span class="no">{E(s["no"])}</span>'
                     f'<h2>{E(s["title"])}</h2><span class="min">{E(s["minutes"])}</span></header>{"".join(body)}</section>')

page = f'''<title>直播 01 提词卡 · CH00–02</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700;900&display=swap">
<style>
:root{{color-scheme:dark;--bg:#0D0F14;--card:#171B24;--card2:#1F2430;--ink:#ECEEF2;--sub:#A3A9B8;--mute:#6B7285;--line:#2A3040;
--amb:#E0A458;--ambbg:#33281A;--ok:#5BBF8F;--okbg:#173025;--blu:#7EA6E8;--blubg:#1B2638;--hot:#E8766C;
--mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;--sans:'Noto Sans SC',system-ui,-apple-system,'PingFang SC',sans-serif}}
@media (prefers-color-scheme: light){{:root:not([data-theme="dark"]){{color-scheme:light;--bg:#F4F5F7;--card:#FFFFFF;--card2:#F0F2F5;--ink:#1A1D24;--sub:#4E5566;--mute:#8A91A2;--line:#DCE0E7;--ambbg:#FBF0DC;--amb:#9A6420;--okbg:#E3F3EA;--ok:#2C7D57;--blubg:#E5EDF9;--blu:#2F5DA8}}}}
:root[data-theme="light"]{{color-scheme:light;--bg:#F4F5F7;--card:#FFFFFF;--card2:#F0F2F5;--ink:#1A1D24;--sub:#4E5566;--mute:#8A91A2;--line:#DCE0E7;--ambbg:#FBF0DC;--amb:#9A6420;--okbg:#E3F3EA;--ok:#2C7D57;--blubg:#E5EDF9;--blu:#2F5DA8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:19px;line-height:1.75;-webkit-font-smoothing:antialiased}}
.wrapper{{max-width:1060px;margin:0 auto;padding-inline:16px;padding-block:22px 80px}}
.top h1{{font-size:clamp(24px,3vw,34px);margin:4px 0 6px;font-weight:900}}
.eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;color:var(--mute)}}
.lede{{color:var(--sub);font-size:16px;margin:0 0 14px}}
nav.toc{{position:sticky;top:env(safe-area-inset-top,0px);z-index:10;display:flex;gap:6px;overflow-x:auto;padding:10px 0;background:var(--bg);border-bottom:1px solid var(--line);margin-bottom:18px}}
nav.toc a{{flex:none;font-size:14px;color:var(--ink);text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 10px;white-space:nowrap}}
nav.toc a span{{color:var(--mute);font-family:var(--mono);font-size:12px;margin-left:6px}}
.seg{{background:var(--card);border-radius:14px;padding:18px 20px 22px;margin:0 0 22px;border-left:5px solid var(--blu)}}
.seg:nth-of-type(2){{border-left-color:var(--amb)}} .seg:nth-of-type(3){{border-left-color:var(--ok)}} .seg:nth-of-type(4){{border-left-color:var(--hot)}} .seg:nth-of-type(5){{border-left-color:var(--sub)}} .seg:nth-of-type(6){{border-left-color:var(--blu)}}
.seg header{{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:8px}}
.seg .no{{font-size:30px;font-weight:900}} .seg h2{{margin:0;font-size:24px;font-weight:900;flex:1;min-width:200px}}
.seg .min{{font-family:var(--mono);font-size:15px;color:var(--sub);background:var(--card2);padding:2px 10px;border-radius:6px}}
.goal{{font-size:21px;font-weight:700;margin:6px 0 12px}}
.k{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;color:var(--mute);text-transform:uppercase;margin:16px 0 6px}}
.script{{margin:0 0 12px;font-size:20px}}
ul.pts{{margin:0;padding-left:22px}} ul.pts li{{margin:4px 0}}
.vis{{color:var(--sub);font-size:16px;margin:0 0 8px}}
.gal{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin:8px 0}}
figure{{margin:0}} figure img{{width:100%;border-radius:8px;display:block;border:1px solid var(--line);background:#0F1115}}
figcaption{{font-size:13px;color:var(--mute);margin-top:4px}}
button.zoom{{all:unset;cursor:zoom-in;display:block}} button.zoom:focus-visible{{outline:2px solid var(--blu);outline-offset:3px;border-radius:8px}}
ol.ops{{margin:0;padding-left:24px}} ol.ops li{{margin:6px 0}}
.ask{{background:var(--ambbg);color:var(--ink);border-radius:8px;padding:8px 12px;margin:8px 0;font-size:19px}}
.rev{{background:var(--okbg);border-radius:8px;padding:8px 12px;margin:8px 0}}
.trans{{color:var(--blu);margin:16px 0 6px;font-weight:500}}
.clip{{font-size:14px;color:var(--sub);background:var(--card2);border-radius:8px;padding:6px 10px;display:inline-block}}
.case{{background:var(--card2);border-radius:12px;padding:14px 16px;margin:14px 0}}
.case h3{{margin:0 0 4px;font-size:22px}} .meta{{color:var(--sub);font-size:14px;margin-bottom:8px}}
.step{{border-top:1px dashed var(--line);padding-top:10px;margin-top:10px}}
.stop{{font-family:var(--mono);font-size:15px;color:var(--amb);font-weight:500}}
.say{{margin:4px 0 6px}}
.wrap{{font-weight:700;margin:12px 0 4px}}
.src{{font-size:13px;color:var(--mute)}}
details.qa{{background:var(--card2);border-radius:8px;padding:8px 12px;margin:6px 0}}
details.qa summary{{cursor:pointer;font-weight:500}} details.qa p{{margin:8px 0 4px}}
section.recap{{background:var(--card);border-radius:14px;padding:16px 18px;margin:0 0 22px;border-left:5px solid var(--ok)}}
section.recap h2{{margin:0 0 10px;font-size:22px;font-weight:900}}
.tw{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:16px}}
th{{text-align:left;font-family:var(--mono);font-size:12px;letter-spacing:.1em;color:var(--mute);font-weight:500;padding:6px 8px;border-bottom:1px solid var(--line)}}
td{{padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}} td.w{{white-space:nowrap;color:var(--sub);font-size:14px}} td.b{{color:var(--mute)}}
dialog{{border:0;padding:0;background:transparent;max-width:96vw;max-height:94vh}}
dialog::backdrop{{background:rgba(0,0,0,.85)}}
dialog img{{max-width:96vw;max-height:88vh;display:block;border-radius:8px}}
dialog p{{color:#ddd;text-align:center;margin:6px 0 0;font-size:14px}}
@media (max-width:640px){{body{{font-size:17px}} .script{{font-size:17px}} .seg{{padding:14px}}}}
</style>
<div class="wrapper">
<div class="top"><div class="eyebrow">FLUXUS 会员直播 · 01 · 2026-10-03 周六 · 读 10/2 周五收盘</div>
<h1>直播 01 提词卡 · 先看环境（第 0–2 章）</h1>
<p class="lede">六段，从上往下讲。每段：一句目标 → 讲稿 → 要点 → 画面 → 操作 → 问观众 → 过渡。点图放大。案例数字全部按日线收盘价复核（10-03 JST）。</p></div>
<nav class="toc"><a href="#recap">复盘要点</a>{"".join(nav)}</nav>
{recap}
{"".join(segs_html)}
<p class="src">讲稿：Studio Q 按书 CH00–02 写，图号以书为准（0-14 NVDA、1-1 QQQ 2022、2-1 森林到树木）；三问＝§1.2 红绿灯，四问＝§1.7 环境。案例图与截图：OPS 10-03 生成，dashboard 为线上 10/2 收盘读数。</p>
</div>
<dialog id="dlg"><img id="dlgimg" alt=""><p id="dlgcap"></p></dialog>
<script>
(function(){{var d=document.getElementById('dlg'),i=document.getElementById('dlgimg'),c=document.getElementById('dlgcap');
document.addEventListener('click',function(e){{var b=e.target.closest&&e.target.closest('button.zoom');if(b){{i.src=b.dataset.src;i.alt=b.dataset.cap;c.textContent=b.dataset.cap;d.showModal&&d.showModal();return}}if(e.target===d||e.target===i)d.close()}});}})();
</script>
'''
open(OUT, 'w').write(page)
print('ok', len(page))
