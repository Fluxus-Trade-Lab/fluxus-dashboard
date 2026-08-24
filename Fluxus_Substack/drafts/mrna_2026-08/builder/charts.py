import json, io, statistics as st

R = '/Users/taolezhu/Documents/AI-Trading-System/'

# ---------------- 1) MRNA 8 日 zoom（7/28 → 8/14，不含爆发日） ----------------
d = json.load(open(R + 'data/output/tickers/MRNA.json'))
o = d['ohlc_2y']
idx = {str(r['date'])[:10]: i for i, r in enumerate(o)}


def ma(i, n):
    return st.mean([x['close'] for x in o[i - n + 1:i + 1]])


win = [r for r in o if '2026-07-28' <= str(r['date'])[:10] <= '2026-08-14']
lo = min(r['low'] for r in win) - 1.2
hi = max(r['high'] for r in win) + 1.2

W, H = 768, 330
L, Rr, T, B = 46, 78, 18, 44
pw, ph = W - L - Rr, H - T - B
n = len(win)
step = pw / n


def X(k):
    return L + step * (k + .5)


def Y(v):
    return T + ph * (hi - v) / (hi - lo)


s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="MRNA 日线 7月28日至8月14日入场日，均线收敛于 60 一线">']
# grid
for v in range(int(lo) + 1, int(hi) + 1):
    if v % 2 == 0:
        s.append(f'<line class="g" x1="{L}" y1="{Y(v):.1f}" x2="{L+pw:.1f}" y2="{Y(v):.1f}"/>')
        s.append(f'<text class="ax" x="{L-6}" y="{Y(v)+3:.1f}" text-anchor="end">{v}</text>')

# 60 支撑线
s.append(f'<line class="lvl" x1="{L}" y1="{Y(60):.1f}" x2="{L+pw+58:.1f}" y2="{Y(60):.1f}"/>')
s.append(f'<text class="lvlT" x="{L+pw+62:.1f}" y="{Y(60)+3.5:.1f}">60 分水岭</text>')

# 均线
for nn, cls in ((10, 'm10'), (20, 'm20'), (50, 'm50')):
    pts = []
    for k, r in enumerate(win):
        i = idx[str(r['date'])[:10]]
        pts.append(f'{X(k):.1f},{Y(ma(i, nn)):.1f}')
    s.append(f'<polyline class="{cls}" points="{" ".join(pts)}"/>')

# candles
for k, r in enumerate(win):
    up = r['close'] >= r['open']
    cl = 'up' if up else 'dn'
    cx = X(k)
    s.append(f'<line class="wick {cl}" x1="{cx:.1f}" y1="{Y(r["high"]):.1f}" x2="{cx:.1f}" y2="{Y(r["low"]):.1f}"/>')
    yo, yc = Y(r['open']), Y(r['close'])
    top, hgt = min(yo, yc), max(abs(yc - yo), 1.4)
    bw = step * .58
    s.append(f'<rect class="body {cl}" x="{cx-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{hgt:.1f}"/>')

lab = {'2026-08-07': ('8/7 反包 +10%', -1), '2026-08-12': ('8/12 破 20MA · 20日新高', -1),
       '2026-08-13': ('8/13 十字星', 1), '2026-08-14': ('8/14 买入 62.72', 1)}
for k, r in enumerate(win):
    dt = str(r['date'])[:10]
    if dt in lab:
        txt, dir_ = lab[dt]
        yy = Y(r['high']) - 9 if dir_ < 0 else Y(r['low']) + 15
        anchor = 'middle' if k < n - 3 else 'end'
        s.append(f'<text class="note" x="{X(k):.1f}" y="{yy:.1f}" text-anchor="{anchor}">{txt}</text>')

# entry / stop
s.append(f'<line class="entry" x1="{X(n-1)-step*.7:.1f}" y1="{Y(62.72):.1f}" x2="{L+pw+58:.1f}" y2="{Y(62.72):.1f}"/>')
s.append(f'<text class="entryT" x="{L+pw+62:.1f}" y="{Y(62.72)+3.5:.1f}">入场 62.72</text>')
s.append(f'<rect class="risk" x="{X(n-1)-step*.7:.1f}" y="{Y(62.72):.1f}" width="{pw+58-(X(n-1)-step*.7):.1f}" height="{Y(60)-Y(62.72):.1f}"/>')

for k, r in enumerate(win):
    if k % 3 == 0 or k == n - 1:
        s.append(f'<text class="ax" x="{X(k):.1f}" y="{H-24}" text-anchor="middle">{str(r["date"])[5:10]}</text>')
s.append(f'<text class="cap" x="{L}" y="{H-6}">风险 $2.72／股 = 0.73 个 ATR。三条均线全在 60 一线。</text>')
s.append('</svg>')
zoom = '\n'.join(s)

# ---------------- 2) SNOW vs XBI 同构 ----------------
def series(t, a, b):
    dd = json.load(open(R + f'data/output/tickers/{t}.json'))
    oo = dd.get('ohlc_1y') or dd.get('ohlc_2y')
    return [r for r in oo if a <= str(r['date'])[:10] <= b]


A, B2 = '2026-05-15', '2026-08-07'
sn, xb = series('SNOW', A, B2), series('XBI', A, B2)
m = min(len(sn), len(xb))
sn, xb = sn[-m:], xb[-m:]
nsn = [r['close'] / sn[0]['close'] * 100 for r in sn]
nxb = [r['close'] / xb[0]['close'] * 100 for r in xb]
allv = nsn + nxb
ylo, yhi = min(allv) - 4, max(allv) + 6

W2, H2 = 700, 300
L2, R2, T2, B2p = 42, 60, 22, 42
pw2, ph2 = W2 - L2 - R2, H2 - T2 - B2p


def X2(k):
    return L2 + pw2 * k / (m - 1)


def Y2(v):
    return T2 + ph2 * (yhi - v) / (yhi - ylo)


t = [f'<svg viewBox="0 0 {W2} {H2}" role="img" aria-label="SNOW 与 XBI 同期归一化走势对比">']
for v in (100, 120, 140, 160):
    if ylo < v < yhi:
        t.append(f'<line class="g" x1="{L2}" y1="{Y2(v):.1f}" x2="{L2+pw2:.1f}" y2="{Y2(v):.1f}"/>')
        t.append(f'<text class="ax" x="{L2-6}" y="{Y2(v)+3:.1f}" text-anchor="end">{v}</text>')
t.append(f'<line class="base" x1="{L2}" y1="{Y2(100):.1f}" x2="{L2+pw2:.1f}" y2="{Y2(100):.1f}"/>')
t.append('<polyline class="sSNOW" points="' + ' '.join(f'{X2(k):.1f},{Y2(v):.1f}' for k, v in enumerate(nsn)) + '"/>')
t.append('<polyline class="sXBI" points="' + ' '.join(f'{X2(k):.1f},{Y2(v):.1f}' for k, v in enumerate(nxb)) + '"/>')
t.append(f'<text class="lgSNOW" x="{X2(m-1)+6:.1f}" y="{Y2(nsn[-1])+4:.1f}">SNOW</text>')
t.append(f'<text class="lgXBI" x="{X2(m-1)+6:.1f}" y="{Y2(nxb[-1])+4:.1f}">XBI</text>')
for k in range(0, m, max(1, m // 5)):
    t.append(f'<text class="ax" x="{X2(k):.1f}" y="{H2-22}" text-anchor="middle">{str(sn[k]["date"])[5:10]}</text>')
t.append(f'<text class="cap" x="{L2}" y="{H2-5}">同期归一化到 100。突破 → 回踩 → 再拉伸 → 回踩 —— 同一个形状。</text>')
t.append('</svg>')
snow = '\n'.join(t)

io.open('chart_zoom.svg', 'w').write(zoom)
io.open('chart_snow.svg', 'w').write(snow)
print('zoom', len(zoom) // 1024, 'KB ·', 'snow', len(snow) // 1024, 'KB · bars', n, m)
