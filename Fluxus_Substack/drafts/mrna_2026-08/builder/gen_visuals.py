"""生成六张主题感知的内联 SVG，写进 imgs.json。数据全部来自已核实的表。"""
import json, io

imgs = json.load(open('imgs.json'))
S = []


def svg(key, w, h, body):
    imgs[key] = f'<svg viewBox="0 0 {w} {h}" role="img">' + ''.join(body) + '</svg>'
    S.append((key, len(imgs[key])))


# ── 1) 决策漏斗 ─────────────────────────────────────────
rows = [
    (600, '① 板块之间 · 196 组的相对强度', '不做半导体', '早于这只票'),
    (430, '② 探头 · 五条同日全中', '名单', '8/12'),
    (300, '③ 这一张图 · 止损放哪', '62.72/60', '8/14'),
]
b = []
y = 8
for wd, left, right, when in rows:
    x = (660 - wd) / 2
    b.append(f'<rect class="fun" x="{x}" y="{y}" width="{wd}" height="36" rx="2"/>')
    b.append(f'<text class="funT" x="{x+10}" y="{y+23}">{left}</text>')
    b.append(f'<text class="lbl" x="{x+wd-8}" y="{y+23}" text-anchor="end">{right}</text>')
    b.append(f'<text class="lbl" x="650" y="{y+23}" text-anchor="end">{when}</text>')
    y += 46
svg('funnel', 660, y + 2, b)

# ── 2) 板块三个月超额（5 个归档日，三条线） ────────────────
dates = ['8/07', '8/12', '8/14', '8/17', '8/20']
series = {
    'lnA': ('软件', [0.078, 0.208, 0.216, 0.183, 0.172]),
    'lnM': ('生物科技', [0.118, 0.131, 0.153, 0.202, None]),
    'lnN': ('半导体', [-0.103, -0.140, -0.118, -0.092, -0.192]),
}
L, R, T, B = 46, 96, 16, 34
W, H = 660, 230
pw, ph = W - L - R, H - T - B
lo, hi = -0.22, 0.26
X = lambda i: L + pw * i / 4
Y = lambda v: T + ph * (hi - v) / (hi - lo)
b = [f'<line class="lvl" x1="{L}" y1="{Y(0):.1f}" x2="{L+pw}" y2="{Y(0):.1f}"/>',
     f'<text class="lbl" x="{L-6}" y="{Y(0)+3:.1f}" text-anchor="end">0</text>']
for cls, (name, vals) in series.items():
    pts = [(i, v) for i, v in enumerate(vals) if v is not None]
    b.append(f'<polyline class="{cls}" points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in pts)}"/>')
    for i, v in pts:
        b.append(f'<circle class="dot{cls[-1]}" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2.4"/>')
    li, lv = pts[-1]
    dy = -10 if li < 4 else 4          # 提前断掉的序列，标签抬到点上方，避开别的线
    dx = 4 if li < 4 else 8
    b.append(f'<text class="funT" x="{X(li)+dx:.1f}" y="{Y(lv)+dy:.1f}">{name} {lv:+.2f}</text>')
for i, d in enumerate(dates):
    b.append(f'<text class="lbl" x="{X(i):.1f}" y="{H-16}" text-anchor="middle">{d}</text>')
b.append(f'<text class="cap" x="{L}" y="{H-2}">三个月超额收益 · 每晚归档 · 8/14 = 买入日</text>')
svg('sectors', W, H, b)

# ── 3) RS 八个交易日 + 80 门槛 ──────────────────────────
vals = [56, 63, 83, 81, 82, 82, 86, 88]
L, R, T, B = 40, 60, 18, 30
W, H = 660, 180
pw, ph = W - L - R, H - T - B
lo, hi = 50, 100
X = lambda i: L + pw * i / 7
Y = lambda v: T + ph * (hi - v) / (hi - lo)
b = [f'<line class="lvl" x1="{L}" y1="{Y(80):.1f}" x2="{L+pw}" y2="{Y(80):.1f}"/>',
     f'<text class="entryT" x="{L+pw+8}" y="{Y(80)+4:.1f}">门槛 80</text>',
     f'<polyline class="lnA" points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))}"/>']
for i, v in enumerate(vals):
    b.append(f'<circle class="dotA" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2.6"/>')
b.append(f'<text class="val" x="{X(0)+2:.1f}" y="{Y(56)-9:.1f}" text-anchor="middle">56</text>')
b.append(f'<text class="val" x="{X(7):.1f}" y="{Y(88)-8:.1f}" text-anchor="middle">88</text>')
b.append(f'<text class="lbl" x="{L}" y="{H-4}">三个月 RS · 买入前八个交易日 · 同期自百分位 48 → 100</text>')
svg('rsline', W, H, b)

# ── 4) 束宽 25% → 4.1% ─────────────────────────────────
data = [('7/15', 25.0), ('7/31', 12.9), ('8/06', 7.0), ('8/11', 4.8), ('8/13', 4.1)]
L, T, B = 44, 26, 40
W, H = 660, 210
pw, ph = W - L - 12, H - T - B
b = [f'<line class="ax" x1="{L}" y1="{T+ph}" x2="{L+pw}" y2="{T+ph}" stroke="var(--rule)"/>']
bw = 58
for i, (d, v) in enumerate(data):
    x = L + pw * (i + .5) / 5 - bw / 2
    hh = ph * v / 26
    cls = 'bar' if v < 6 else 'bar dim'
    b.append(f'<rect class="{cls}" x="{x:.1f}" y="{T+ph-hh:.1f}" width="{bw}" height="{hh:.1f}"/>')
    b.append(f'<text class="val" x="{x+bw/2:.1f}" y="{T+ph-hh-7:.1f}" text-anchor="middle">{v}%</text>')
    b.append(f'<text class="lbl" x="{x+bw/2:.1f}" y="{H-22}" text-anchor="middle">{d}</text>')
b.append(f'<text class="cap" x="{L}" y="{H-4}">均线束宽 =（MA10/20/50 最高 − 最低）÷ 股价 · 六周紧了六倍</text>')
svg('band', W, H, b)

# ── 5) 两笔一样大，代价差 13.6 倍 ────────────────────────
b = []
groups = [(70, '第一笔 · 结构位', '止损 $2.72/股', 0.217), (390, '第二笔 · VWAP 加仓', '止损 $0.20/股', 0.016)]
for x0, name, stop, risk in groups:
    b.append(f'<text class="funT" x="{x0}" y="24">{name}</text>')
    b.append(f'<text class="lbl" x="{x0}" y="40">{stop}</text>')
    b.append(f'<rect class="barP" x="{x0}" y="52" width="200" height="42" rx="2"/>')
    b.append(f'<text class="funT" x="{x0+100}" y="78" text-anchor="middle">仓位 5%</text>')
    hh = max(6, 110 * risk / 0.217)
    b.append(f'<rect class="barR" x="{x0}" y="{116}" width="200" height="{hh:.0f}"/>')
    b.append(f'<text class="val" x="{x0+100}" y="{116+hh+15:.0f}" text-anchor="middle">组合风险 {risk}%</text>')
b.append('<text class="big" x="330" y="182" text-anchor="middle">×13.6</text>')
b.append('<text class="cap" x="70" y="262">仓位一样大。代价差 13.6 倍 —— 差的不是信心，是止损离入场多远</text>')
svg('sizing', 660, 272, b)

# ── 6) 宽度三天：20 日线上方占比 ─────────────────────────
data = [('8/14 买入', 63.3, 'bar'), ('8/17', 56.2, 'bar dim'), ('8/18 减仓', 49.5, 'barR')]
L, T, B = 44, 24, 40
W, H = 660, 200
pw, ph = W - L - 12, H - T - B
lo, hi = 40, 70
Y = lambda v: T + ph * (hi - v) / (hi - lo)
b = [f'<line class="lvl" x1="{L}" y1="{Y(50):.1f}" x2="{L+pw}" y2="{Y(50):.1f}"/>',
     f'<text class="lbl" x="{L-6}" y="{Y(50)+3:.1f}" text-anchor="end">50%</text>']
bw = 120
for i, (d, v, cls) in enumerate(data):
    x = L + pw * (i + .5) / 3 - bw / 2
    b.append(f'<rect class="{cls}" x="{x:.1f}" y="{Y(v):.1f}" width="{bw}" height="{T+ph-Y(v):.1f}"/>')
    b.append(f'<text class="val" x="{x+bw/2:.1f}" y="{Y(v)-7:.1f}" text-anchor="middle">{v}%</text>')
    b.append(f'<text class="lbl" x="{x+bw/2:.1f}" y="{H-22}" text-anchor="middle">{d}</text>')
b.append(f'<text class="cap" x="{L}" y="{H-4}">站在 20 日线上方的股票占比 · 三天从 63% 掉到不足一半</text>')
svg('breadth3', W, H, b)

io.open('imgs.json', 'w').write(json.dumps(imgs))
print(' · '.join(f'{k} {n//1024}KB' if n > 1024 else f'{k} {n}B' for k, n in S))
