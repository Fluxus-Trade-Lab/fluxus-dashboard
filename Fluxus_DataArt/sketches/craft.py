"""细活工具箱:tapered 笔画、平滑曲线、植物学花形。无随机抖动——参数化的克制变化。"""
import math


def smooth_path(pts):
    """Catmull-Rom -> cubic Bézier,专业的平滑曲线。"""
    if len(pts) < 3:
        return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    p = [pts[0]] + list(pts) + [pts[-1]]
    d = f"M {p[1][0]:.1f} {p[1][1]:.1f}"
    for i in range(1, len(p) - 2):
        c1 = (p[i][0] + (p[i+1][0] - p[i-1][0]) / 6, p[i][1] + (p[i+1][1] - p[i-1][1]) / 6)
        c2 = (p[i+1][0] - (p[i+2][0] - p[i][0]) / 6, p[i+1][1] - (p[i+2][1] - p[i][1]) / 6)
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p[i+1][0]:.1f} {p[i+1][1]:.1f}"
    return d


def _resample(pts, n):
    """polyline 重采样为 n 点(近似等距)。"""
    if len(pts) < 2:
        return pts * n
    segs = []
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, L)); total += L
    out, target = [], [total * i / (n - 1) for i in range(n)]
    acc, si = 0.0, 0
    for t in target:
        while si < len(segs) - 1 and acc + segs[si][2] < t:
            acc += segs[si][2]; si += 1
        a, b, L = segs[si]
        f = 0 if L == 0 else min(max((t - acc) / L, 0), 1)
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def tapered(pts, w0, w1, n=26):
    """沿曲线的收笔笔画:返回闭合轮廓 path(填充,不描边)。w0 起笔宽,w1 收笔宽。"""
    p = _resample(pts, n)
    left, right = [], []
    for i, (x, y) in enumerate(p):
        if i == 0:
            tx, ty = p[1][0] - x, p[1][1] - y
        elif i == len(p) - 1:
            tx, ty = x - p[-2][0], y - p[-2][1]
        else:
            tx, ty = p[i+1][0] - p[i-1][0], p[i+1][1] - p[i-1][1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        t = i / (len(p) - 1)
        w = (w0 + (w1 - w0) * t) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    path = smooth_path(left) + " L " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in reversed(right)) + " Z"
    return path


def stem_curve(x0, y0, x1, y1, sway=0.22, phase=0.0):
    """植物茎的 S 曲线:从 (x0,y0) 到 (x1,y1),sway 控制侧摆比例。"""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    px, py = -dy / (L or 1), dx / (L or 1)
    pts = []
    for i in range(9):
        t = i / 8
        s = math.sin(t * math.pi * 1.35 + phase) * sway * L * (1 - t * 0.4)
        pts.append((x0 + dx * t + px * s, y0 + dy * t + py * s))
    return pts


def umbel(cx, cy, rad, n, color, sw=1.0, dot=1.6, op=0.9):
    """伞形花序(AI 链):n 根细梗从花心放射,端点结小果。返回 svg 片段 list。"""
    out = []
    for i in range(n):
        a = i / n * 2 * math.pi - math.pi / 2
        r1 = rad * (0.92 + 0.08 * math.sin(i * 2.399))   # 黄金角微差,自然而非随机
        ex, ey = cx + math.cos(a) * r1, cy + math.sin(a) * r1
        mx, my = cx + math.cos(a) * r1 * 0.5, cy + math.sin(a) * r1 * 0.55 - rad * 0.06
        out.append(f'<path d="M {cx:.1f} {cy:.1f} Q {mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" opacity="{op}" stroke-linecap="round"/>')
        out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{dot:.2f}" fill="{color}" opacity="{op}"/>')
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{max(rad*0.14,1.4):.2f}" fill="{color}" opacity="{min(op+0.05,1)}"/>')
    return out


def five_petal(cx, cy, rad, color, op=0.85):
    """五瓣花(其他品种):花瓣为椭圆轮廓,12% 填充 + 描边。"""
    out = []
    rx, ry = rad * 0.42, rad
    for i in range(5):
        a = i / 5 * 360 - 90 + 3.5 * math.sin(i * 2.1)
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy - rad*0.52:.1f}" rx="{rx:.1f}" ry="{ry*0.52:.1f}" fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-width="1" opacity="{op}" transform="rotate({a:.0f} {cx:.1f} {cy:.1f})"/>')
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad*0.16:.2f}" fill="{color}" opacity="{op}"/>')
    return out


def falling_petals(cx, cy, n, color, drift=1):
    """落瓣(分批落袋):花旁飘落的小逗点,n = 批次。"""
    out = []
    for i in range(n):
        px = cx + drift * (10 + i * 7)
        py = cy + 14 + i * 12
        out.append(f'<path d="M {px:.1f} {py:.1f} q {3*drift} 2 {4.5*drift} 6.5" fill="none" stroke="{color}" stroke-width="1.1" opacity="{0.6 - i*0.12}" stroke-linecap="round"/>')
    return out
