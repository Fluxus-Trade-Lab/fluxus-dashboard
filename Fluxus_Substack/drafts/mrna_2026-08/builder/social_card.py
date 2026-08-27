#!/usr/bin/env python3
"""社交预览卡 1200×630(1.91:1) —— Substack / X / LinkedIn 分享时的那张图。

为什么不直接裁一张图表:卡片在时间线里只有几百像素宽,
图表缩到那个尺寸标签全糊。**大字和数字能活下来,曲线活不下来。**
所以卡片只放:一个判断 + 三个数 + 台账一行。

配色和字体照 preview_en.html 的 :root 令牌,和文章里的图是同一套。
边缘留 72px 安全区(Substack 提示:重要文字和 logo 别贴边)。

用法: python3 builder/social_card.py [输出路径]
"""
import subprocess
import sys
from pathlib import Path

W, H = 1200, 630
PAD = 72                       # 安全区
INK, MUTED = '#15191A', '#6C7573'
ACCENT, NEG = '#0D6B5C', '#A33B2C'
GROUND, RULE = '#F6F7F6', '#DCE0DE'
MONO = '&#34;IBM Plex Mono&#34;,&#34;SF Mono&#34;,Menlo,monospace'
SERIF = 'Georgia,&#34;Times New Roman&#34;,serif'

NUMS = [('0.25%', 'risked', MUTED),
        ('+176.97%', 'the move', INK),
        ('+23R', 'came back', ACCENT)]


def svg():
    x0 = PAD
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{GROUND}"/>',
        f'<rect x="0" y="0" width="{W}" height="8" fill="{ACCENT}"/>',
        # 眉标
        f'<text x="{x0}" y="{PAD + 34}" font-family="{MONO}" font-size="19" letter-spacing="3.5" '
        f'fill="{MUTED}">FLUXUS CAPITAL &#183; METHOD</text>',
        # 主标题(两行,手动断行 —— SVG 不换行)
        f'<text x="{x0}" y="{PAD + 132}" font-family="{SERIF}" font-size="70" font-weight="700" '
        f'fill="{INK}">How I Caught a 176% Move</text>',
        f'<text x="{x0}" y="{PAD + 208}" font-family="{SERIF}" font-size="70" font-weight="700" '
        f'fill="{INK}">in $MRNA</text>',
        # 副题
        f'<text x="{x0}" y="{PAD + 262}" font-family="{MONO}" font-size="23" fill="{MUTED}">'
        f'Three filters, five rules, and exactly how much.</text>',
        f'<line x1="{x0}" y1="{PAD + 306}" x2="{W - PAD}" y2="{PAD + 306}" stroke="{RULE}" stroke-width="1"/>',
    ]
    # 三个数
    for i, (big, lab, col) in enumerate(NUMS):
        cx = x0 + i * 348
        parts.append(f'<text x="{cx}" y="{PAD + 380}" font-family="{MONO}" font-size="58" '
                     f'font-weight="700" fill="{col}">{big}</text>')
        parts.append(f'<text x="{cx}" y="{PAD + 414}" font-family="{MONO}" font-size="20" '
                     f'letter-spacing="1.5" fill="{MUTED}">{lab}</text>')
    # 台账
    parts.append(f'<text x="{x0}" y="{H - PAD + 6}" font-family="{MONO}" font-size="20" '
                 f'fill="{MUTED}">in 62.72 Aug 14 &#183; stop 60 &#183; trade risk 0.233% '
                 f'&#183; out Aug 19</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parent.parent / 'assets_x' / 'social_card.png'
    tmp = Path('/tmp/fluxus_social')
    tmp.mkdir(exist_ok=True)
    f = tmp / 'card.svg'
    # ⚠️ qlmanage 按**正方形画布**定标(export_x.py 踩过同一个坑):
    # 直接给 1200×630 会被按高度放大 → 右边裁掉。
    # 解法:viewBox 撑成正方形、内容垂直居中,出图后 sips 居中裁回 630。
    body = svg().split('\n', 1)[1].rsplit('</svg>', 1)[0]
    px = 2400
    vy = -(W - H) / 2
    f.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {vy} {W} {W}" '
                 f'width="{px}" height="{px}"><rect x="0" y="{vy}" width="{W}" height="{W}" '
                 f'fill="{GROUND}"/>{body}</svg>')
    subprocess.run(['qlmanage', '-t', '-s', str(px), '-o', str(tmp), str(f)],
                   check=True, capture_output=True)
    made = tmp / (f.name + '.png')
    if not made.exists():
        raise SystemExit('qlmanage 没产出 PNG')
    crop_h = round(px * H / W)
    subprocess.run(['sips', '-s', 'format', 'png', '-c', str(crop_h), str(px),
                    str(made), '--out', str(out)], check=True, capture_output=True)
    subprocess.run(['sips', '-z', str(H), str(W), str(out)], check=True, capture_output=True)
    dim = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', str(out)],
                         capture_output=True, text=True).stdout
    print(f'✅ {out}')
    print(dim.strip())


if __name__ == '__main__':
    main()
