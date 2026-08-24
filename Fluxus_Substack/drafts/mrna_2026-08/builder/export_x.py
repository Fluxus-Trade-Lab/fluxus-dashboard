#!/usr/bin/env python3
"""把 preview_en.html 里的内联 SVG 导出成 X 长文用的 PNG。

为什么要这个脚本：08-24 发文当天发现两张图右缘被裁（"Software +0.17" 少一位、
"60 = the line" 少半句）——原因是 viewBox 宽度按中文标签算的，英文标签更长。
当时的导出是临时拼的，没留下来，只好重来一遍。这次固化。

用法：python3 builder/export_x.py            # 导出全部
      python3 builder/export_x.py 0 3        # 只导出第 0、3 张
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'preview_en.html'
OUT = ROOT / 'assets_x'
TMP = Path('/tmp/fluxus_x_export')
PX = 1600  # 导出长边像素

# preview_en.html 的 :root 令牌，导出时必须字面写死（页面 CSS 不跟着 PNG 走）
TOKENS = {
    '--ground': '#F6F7F6', '--panel': '#FFFFFF', '--ink': '#15191A',
    '--muted': '#6C7573', '--rule': '#DCE0DE', '--rule-soft': '#E9ECEA',
    '--accent': '#0D6B5C', '--accent-soft': '#E2EEEA', '--neg': '#A33B2C',
    '--pos': '#0D6B5C',
}
MONO = '"IBM Plex Mono","SF Mono",Menlo,monospace'
SANS = '"Helvetica Neue",Arial,sans-serif'

STYLE = f"""
text {{ font-family:{MONO}; }}
.lnA,.lnN,.lnM,.m10,.m20,.m50 {{ fill:none; }}
.lnA {{ stroke:{TOKENS['--accent']}; stroke-width:1.8 }}
.lnM {{ stroke:{TOKENS['--muted']}; stroke-width:1.6; opacity:.85 }}
.lnN {{ stroke:{TOKENS['--neg']}; stroke-width:1.8 }}
.dotA {{ fill:{TOKENS['--accent']} }}
.dotM {{ fill:{TOKENS['--muted']} }}
.dotN {{ fill:{TOKENS['--neg']} }}
.funT {{ font-size:10.5px; fill:{TOKENS['--ink']}; font-weight:600 }}
.lbl  {{ font-size:9.5px; fill:{TOKENS['--muted']} }}
.cap  {{ font-size:9px;  fill:{TOKENS['--muted']} }}
.val  {{ font-size:10.5px; fill:{TOKENS['--ink']}; font-weight:600 }}
.note {{ font-size:8.6px; fill:{TOKENS['--ink']}; font-weight:600 }}
.ax   {{ font-size:9px;  fill:{TOKENS['--muted']} }}
.lvl  {{ stroke:{TOKENS['--ink']}; stroke-width:1; stroke-dasharray:4 3; opacity:.75 }}
.lvlT,.entryT {{ font-size:9.5px; fill:{TOKENS['--ink']}; font-weight:600 }}
.entry {{ stroke:{TOKENS['--accent']}; stroke-width:1.2 }}
.entryT {{ fill:{TOKENS['--accent']} }}
.risk {{ fill:{TOKENS['--neg']}; opacity:.12 }}
.g    {{ stroke:{TOKENS['--rule-soft']}; stroke-width:1 }}
.m10  {{ stroke:{TOKENS['--muted']}; stroke-width:1; opacity:.55 }}
.m20  {{ stroke:{TOKENS['--accent']}; stroke-width:1.4 }}
.m50  {{ stroke:{TOKENS['--muted']}; stroke-width:1.4; stroke-dasharray:3 2; opacity:.8 }}
.wick {{ stroke-width:1 }}
.wick.up,.body.up {{ stroke:{TOKENS['--pos']} }}
.wick.dn,.body.dn {{ stroke:{TOKENS['--neg']} }}
.body.up {{ fill:{TOKENS['--ground']} }}
.body.dn {{ fill:{TOKENS['--neg']} }}
.bar  {{ fill:{TOKENS['--accent']} }}
.bar.dim {{ fill:{TOKENS['--muted']}; opacity:.32 }}
.fun  {{ fill:{TOKENS['--accent-soft']}; stroke:{TOKENS['--accent']}; stroke-width:1 }}
.barP {{ fill:{TOKENS['--accent-soft']}; stroke:{TOKENS['--accent']}; stroke-width:1 }}
.barR {{ fill:{TOKENS['--neg']}; opacity:.85 }}
.big  {{ font-family:{SANS}; font-size:22px; font-weight:700; fill:{TOKENS['--ink']} }}
"""

# 每张图：输出文件名 · 中文残留标签的英文替换 · 右侧留白（英文标签更长）
JOBS = {
    0: dict(name='03_sectors.png', pad_right=46, zh={}),
    1: dict(name='05_rsline.png',  pad_right=0,  zh={}),
    2: dict(name='06_band.png',    pad_right=0,  zh={}),
    3: dict(name='07_zoom.png',    pad_right=80,
            zh={'60 分水岭': '60 = the line', '入场 62.72': 'entry 62.72'}),
    4: dict(name='10_sizing.png',  pad_right=0,  zh={}),
    5: dict(name='11_breadth.png', pad_right=0,  zh={}),
}


def extract():
    src = SRC.read_text()
    return re.findall(r'<svg viewBox="([^"]+)"[^>]*>(.*?)</svg>', src, re.S)


def build(idx, viewbox, body, job):
    for zh, en in job['zh'].items():
        if zh not in body:
            print(f'  ⚠ 图 {idx}: 没找到中文标签 {zh!r}，可能上游已改')
        body = body.replace(zh, en)
    x0, y0, w, h = (float(v) for v in viewbox.split())
    w += job['pad_right']
    # qlmanage 按正方形画布缩放（按高度定标），所以先把 viewBox 撑成正方形、
    # 内容垂直居中，出图后再用 sips 居中裁回真实高度。
    side = max(w, h)
    vy = y0 - (side - h) / 2
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {vy} {side} {side}" '
           f'width="{PX}" height="{PX}">'
           f'<style>{STYLE}</style>'
           f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="{TOKENS["--panel"]}"/>'
           f'{body}</svg>')
    return html.unescape(doc), w, h, side


def rasterize(svg_path, out_path, h, side):
    subprocess.run(['qlmanage', '-t', '-s', str(PX), '-o', str(TMP), str(svg_path)],
                   check=True, capture_output=True)
    made = TMP / (svg_path.name + '.png')
    if not made.exists():
        raise RuntimeError(f'qlmanage 没产出 {made}')
    crop_h = max(1, round(PX * h / side))
    subprocess.run(['sips', '-s', 'format', 'png', '-c', str(crop_h), str(PX),
                    str(made), '--out', str(out_path)], check=True, capture_output=True)
    return out_path


def main(which):
    TMP.mkdir(exist_ok=True)
    svgs = extract()
    for idx in which:
        job = JOBS[idx]
        viewbox, body = svgs[idx]
        doc, w, h, side = build(idx, viewbox, body, job)
        p = TMP / f'{idx}.svg'
        p.write_text(doc)
        out = rasterize(p, OUT / job['name'], h, side)
        print(f'✓ 图 {idx} → {job["name"]}  viewBox {w:.0f}×{h:.0f}  {out.stat().st_size // 1024} KB')


if __name__ == '__main__':
    args = [int(a) for a in sys.argv[1:]] or sorted(JOBS)
    main(args)
