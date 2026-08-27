#!/usr/bin/env python3
"""社交预览图 1200×630 —— DNA 双螺旋,生成式。

⚠️ 为什么不是文字卡:**Substack 的 social preview 会自己把标题和副题压在图上。**
再画一张带标题的卡 = 标题印两遍,自己打自己。(2026-08-27 我犯过一次。)
所以这张图**一个字都不放**,只留视觉,并且在左下留一片安静区给平台的字。

数学:两条相位差 π 的正弦带 + 碱基对横档。
景深靠 z = cos(相位) 驱动:z 越靠前 → 线越粗、越亮、半径越大。

用法: python3 builder/social_helix.py [输出路径]
"""
import math
import subprocess
import sys
from pathlib import Path

W, H = 1200, 630
PX = 2400                       # 渲染倍率
BG0, BG1 = '#0A0F0E', '#101A18'  # 深底(Substack 压白字用)
A_HI, A_LO = '#3FE0B8', '#0D6B5C'  # 强调:亮青绿 → 品牌绿
RUNG = '#7FD8C4'

TURNS = 3.1                     # 转几圈
AMP = 168                       # 螺旋振幅
CY = H * 0.46
N = 460                         # 采样密度
RUNG_EVERY = 11


def lerp(a, b, t):
    return a + (b - a) * t


def hexmix(c1, c2, t):
    p = lambda c: (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
    a, b = p(c1), p(c2)
    return '#%02x%02x%02x' % tuple(round(lerp(a[i], b[i], t)) for i in range(3))


def build():
    out = [
        f'<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>',
        # 右上一团辉光,把视觉重心推离左下的文字区
        f'<radialGradient id="glow" cx="0.72" cy="0.3" r="0.62">'
        f'<stop offset="0" stop-color="{A_HI}" stop-opacity="0.20"/>'
        f'<stop offset="1" stop-color="{A_HI}" stop-opacity="0"/></radialGradient>',
        f'<filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feGaussianBlur stdDeviation="14"/></filter>',
        f'</defs>',
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
        f'<rect width="{W}" height="{H}" fill="url(#glow)"/>',
    ]

    def strand(phase):
        pts = []
        for i in range(N + 1):
            t = i / N
            ang = t * TURNS * 2 * math.pi + phase
            x = lerp(-60, W + 60, t)
            y = CY + AMP * math.sin(ang)
            z = math.cos(ang)                      # +1 最近, -1 最远
            pts.append((x, y, z))
        return pts

    sA, sB = strand(0.0), strand(math.pi)

    # 碱基对横档 —— 先画,让它们在链条后面
    for i in range(0, N + 1, RUNG_EVERY):
        (x1, y1, z1), (x2, y2, _) = sA[i], sB[i]
        d = (z1 + 1) / 2
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{RUNG}" stroke-opacity="{0.10 + 0.34 * d:.3f}" '
                   f'stroke-width="{1.1 + 2.4 * d:.2f}" stroke-linecap="round"/>')

    # 两条链:按段画,才能让粗细/亮度随景深变化
    for pts in (sA, sB):
        for i in range(N):
            (x1, y1, z1), (x2, y2, z2) = pts[i], pts[i + 1]
            d = ((z1 + z2) / 2 + 1) / 2
            col = hexmix(A_LO, A_HI, d)
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                       f'stroke="{col}" stroke-opacity="{0.30 + 0.70 * d:.3f}" '
                       f'stroke-width="{2.0 + 7.5 * d:.2f}" stroke-linecap="round"/>')
        # 节点:近处更大更亮
        for i in range(0, N + 1, RUNG_EVERY):
            x, y, z = pts[i]
            d = (z + 1) / 2
            if d < 0.35:
                continue
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{1.6 + 5.4 * d:.2f}" '
                       f'fill="{hexmix(A_LO, A_HI, d)}" fill-opacity="{0.35 + 0.6 * d:.3f}"/>')

    # 左下压暗 —— Substack 在这里叠标题
    out.append(f'<rect x="0" y="{H * 0.52:.0f}" width="{W * 0.66:.0f}" height="{H * 0.48:.0f}" '
               f'fill="{BG0}" fill-opacity="0.55" filter="url(#soft)"/>')
    # 顶部品牌条
    out.append(f'<rect x="0" y="0" width="{W}" height="6" fill="{A_HI}" fill-opacity="0.9"/>')
    return ''.join(out)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parent.parent / 'assets_x' / 'social_helix.png'
    tmp = Path('/tmp/fluxus_helix')
    tmp.mkdir(exist_ok=True)
    f = tmp / 'helix.svg'
    # qlmanage 按正方形定标(export_x.py / social_card.py 都踩过):
    # viewBox 撑方 + 内容垂直居中,出图后居中裁回 630。
    vy = -(W - H) / 2
    f.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {vy} {W} {W}" '
                 f'width="{PX}" height="{PX}">'
                 f'<rect x="0" y="{vy}" width="{W}" height="{W}" fill="{BG0}"/>{build()}</svg>')
    subprocess.run(['qlmanage', '-t', '-s', str(PX), '-o', str(tmp), str(f)],
                   check=True, capture_output=True)
    made = tmp / (f.name + '.png')
    if not made.exists():
        raise SystemExit('qlmanage 没产出 PNG')
    subprocess.run(['sips', '-s', 'format', 'png', '-c', str(round(PX * H / W)), str(PX),
                    str(made), '--out', str(out)], check=True, capture_output=True)
    subprocess.run(['sips', '-z', str(H), str(W), str(out)], check=True, capture_output=True)
    print('✅', out)
    print(subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', str(out)],
                         capture_output=True, text=True).stdout.strip())


if __name__ == '__main__':
    main()
