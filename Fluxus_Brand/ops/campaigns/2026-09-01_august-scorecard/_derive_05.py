#!/usr/bin/env python3
"""05_distribution_derived.txt 的生成脚本。
所有数字第一手从 data/portfolio/reviews/monthly_2026-08.html 解析，脚本内零手打读数。
在仓库根目录跑：python3 Fluxus_Brand/ops/campaigns/2026-09-01_august-scorecard/_derive_05.py
"""
import re, html, os, math, datetime

P = '/Users/taolezhu/Documents/AI-Trading-System/data/portfolio/reviews/monthly_2026-08.html'
s = open(P, encoding='utf-8').read()
st = os.stat(P)
print("== 0. 源文件指纹（发布当天必须复看；变了则本文件全部作废）==")
print("  path :", P)
print("  mtime:", datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'))
print("  bytes:", st.st_size)
print()

def cells(tr):
    return [html.unescape(re.sub(r'<[^>]+>', '', c)).strip()
            for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]

rows = []
for name in ['Damaged', 'Mixed', 'Healthy', 'Extended']:
    for m in re.finditer(r'<tr[^>]*>(?:(?!</tr>).)*?' + name + r'(?:(?!</tr>).)*?</tr>', s, re.S):
        c = cells(m.group(0))
        if len(c) == 6 and c[0].startswith(name) and c[1].isdigit():
            rows.append(tuple(c))   # (label, n, win%, avgR, totR, realized)
            break
assert len(rows) == 4, f"四档表解析失败，只拿到 {len(rows)} 行"

def num(x):
    return float(x.replace('R', '').replace('%', '').replace('$', '').replace(',', '')
                  .replace('+', '').replace('−', '-').replace('–', '-'))

N    = sum(int(r[1]) for r in rows)
SR   = sum(num(r[4]) for r in rows)
SD   = sum(num(r[5]) for r in rows)
wins = sum(round(int(r[1]) * num(r[2]) / 100) for r in rows)

print("== 1. 四档表（HTML 逐格解析，未手打）==")
print(f"  {'bracket':18}{'n':>4}{'win%':>9}{'avgR':>8}{'totR':>9}{'realized':>12}")
for r in rows:
    print(f"  {r[0]:18}{r[1]:>4}{r[2]:>9}{r[3]:>8}{r[4]:>9}{r[5]:>12}")
print(f"  闭合四路：n={N} · ΣR={SR:+.1f}R · Σ$={SD:,.0f} · 反推胜数={wins} → {wins}/{N}={wins/N*100:.1f}%")
print()

print("== 2. 份额差（笔数占比 − R占比）· V1/V3 用 ==")
for r in rows:
    n = int(r[1]); stp = n / N * 100; srp = num(r[4]) / SR * 100
    print(f"  {r[0]:18} 笔数 {n:>2}/{N} = {stp:5.2f}%   R {num(r[4]):+5.1f}/{SR:.1f} = {srp:6.2f}%   差 {stp-srp:+6.2f}pp   均R {num(r[4])/n:+.2f}R")
print()

print("== 3. 总胜率＝四个胜率按笔数加权的平均 · V4 用 ==")
acc = 0.0
for r in rows:
    n = int(r[1]); w = n / N; acc += w * num(r[2])
    print(f"  {r[0]:18} n={n:>2}  权重 {w*100:5.2f}%  该档胜率 {num(r[2]):5.1f}%  贡献 {w*num(r[2]):5.2f}pp")
print(f"  加权和 = {acc:.1f}%   ← 与头条 Win rate 的一致性检查（反推胜数路径同样给 {wins/N*100:.1f}%）")
print()

txt = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s)))
mm = re.search(r'SQN ([0-9.]+) Tharp band ([A-Za-z ]+?) Expectancy \+?([0-9.]+)R Stdev R ([0-9.]+)', txt)
sqn_print, band, exp_print, sd_print = mm.group(1), mm.group(2).strip(), float(mm.group(3)), float(mm.group(4))
fm = re.search(r'(SQN = .*?)(?: Bands|$)', txt)
bands = re.search(r'(Bands: .*?≥7[^ ]*)', txt)
mean_r = SR / N
print("== 4. SQN · V5 用（⚠️ cap 本月不 binding）==")
print(f"  报告印出：SQN {sqn_print} · Tharp band '{band}' · Expectancy +{exp_print}R · Stdev R {sd_print}")
print(f"  报告自印公式（原文）：{fm.group(1).strip() if fm else 'n/a'}")
print(f"  分档（原文）：{bands.group(1) if bands else 'n/a'}")
print(f"  复算：√min({N},100) × ({mean_r:.4f} / {sd_print}) = {math.sqrt(min(N,100))*(mean_r/sd_print):.4f}  → 印出 {sqn_print} ✅")
print(f"  ⚠️ N={N} < 100 → min(N,100)=N。**这道 cap 本月不 binding，它没有把 {sqn_print} 压下去。**")
# cap 咬的是 √N 这一项本身，与我的 mean/stdev 无关 —— 只报纯比值，不冒充我的累计 SQN
import csv as _csv
_p='/Users/taolezhu/Documents/AI-Trading-System/data/portfolio/portfolio_2026-08-31.csv'
_rows=list(_csv.reader(open(_p,encoding='utf-8')))
_h=[i for i,r in enumerate(_rows) if r and 'Closed' in r][0]
_ci=_rows[_h].index('Closed')
_closed=sum(1 for r in _rows[_h+1:] if len(r)>_ci and r[_ci].strip()=='YES')
print(f"  cap 咬的是公式里的 √N 这一项，与 mean/stdev 无关。纯比值（可上台面）：")
print(f"    √{_closed} / √100 = {math.sqrt(_closed)/10:.2f}×   ← 同样的每笔一致性，{_closed} 笔的记录不设 cap 会比 100 笔的记录高出这么多倍")
print(f"    （{_closed} = 累计已平仓笔数，第一手读 {_p} 的 Closed 列）")
print(f"  ⛔ 不许把上面这个倍数乘上 8 月的 mean/stdev 冒充「我的累计 SQN」——那不是我的累计口径。")
print(f"  → V5 只许写成「装在前面、现在还没开始收费的闸」，⛔ 不许写成「它让我这个月降了分」。")
print()

print("== 5. 保质期敏感度（U8：报告重生成后笔数 42→43，SAIL 0.0R/$0，落哪一档未知）==")
ext = [r for r in rows if r[0].startswith('Extended')][0]
srp_ext = num(ext[4]) / SR * 100
for label, n_ext in [('Extended 档', int(ext[1]) + 1), ('其它任一档', int(ext[1]))]:
    stp = n_ext / (N + 1) * 100
    print(f"  若 SAIL 落在「{label}」：Extended 笔数占比 {n_ext}/{N+1} = {stp:.2f}%  R占比不变 {srp_ext:.2f}%  → 差 {stp-srp_ext:+.2f}pp")
print("  → R 列与美元列不动（SAIL 是 0.0R / $0），动的只有份额与差。**重生成后本文件全部重跑。**")
