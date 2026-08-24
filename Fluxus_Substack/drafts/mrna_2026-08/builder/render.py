import re, io, json, sys, html as H

imgs = json.load(open('imgs.json'))
SRC = '/Users/taolezhu/Documents/AI-Trading-System/Fluxus_Substack/drafts/mrna_2026-08/'

CSS = r'''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@500;700&family=Noto+Serif+SC:wght@400;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{--ground:#F6F7F6;--panel:#FFF;--ink:#15191A;--muted:#6C7573;--rule:#DCE0DE;--rule-soft:#E9ECEA;
--accent:#0D6B5C;--accent-soft:#E2EEEA;--neg:#A33B2C;--pos:#0D6B5C;
--serif:"Noto Serif SC",Songti SC,Georgia,serif;--sans:"Noto Sans SC","PingFang SC",Arial,sans-serif;
--mono:"IBM Plex Mono","SF Mono",Menlo,monospace;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#0E1112;--panel:#151A1A;--ink:#E7EBE9;
--muted:#89928F;--rule:#242A29;--rule-soft:#1B2120;--accent:#4CC0A6;--accent-soft:#16302B;--neg:#D6705F;--pos:#4CC0A6;}}
:root[data-theme="dark"]{--ground:#0E1112;--panel:#151A1A;--ink:#E7EBE9;--muted:#89928F;--rule:#242A29;
--rule-soft:#1B2120;--accent:#4CC0A6;--accent-soft:#16302B;--neg:#D6705F;--pos:#4CC0A6;}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--serif);font-size:17px;line-height:1.85;-webkit-font-smoothing:antialiased}
.wrap{max-width:41rem;margin:0 auto;padding:0 1.4rem 6rem}
header.mast{border-bottom:1px solid var(--rule);padding:3.5rem 0 1.6rem;margin-bottom:2.2rem}
.kicker{font-family:var(--mono);font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin:0 0 1.1rem}
h1{font-family:var(--sans);font-weight:700;font-size:clamp(1.9rem,5.4vw,2.7rem);line-height:1.25;letter-spacing:-.02em;margin:0 0 .9rem;text-wrap:balance}
.dek{font-family:var(--mono);font-size:.86rem;line-height:1.7;color:var(--muted);margin:0}
.byline{font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-top:1.5rem;display:flex;flex-wrap:wrap;gap:.5rem 1.2rem}
.byline b{color:var(--ink);font-weight:500}
.draft{border:1px solid var(--rule);border-left:3px solid var(--accent);background:var(--panel);padding:.85rem 1.05rem;
margin:0 0 2.4rem;font-family:var(--mono);font-size:.75rem;line-height:1.65;color:var(--muted)}
.draft b{color:var(--ink);font-weight:600}
h2{font-family:var(--sans);font-weight:700;font-size:1.32rem;line-height:1.4;letter-spacing:-.01em;margin:3.2rem 0 1.1rem;
padding-top:1.3rem;border-top:1px solid var(--rule);text-wrap:balance}
h3{font-family:var(--sans);font-weight:500;font-size:1.02rem;margin:2.2rem 0 .7rem;letter-spacing:.01em}
p{margin:0 0 1.15rem}
strong{font-weight:600}
em{font-style:italic;color:var(--muted)}
blockquote{margin:1.8rem 0;padding:0 0 0 1.1rem;border-left:2px solid var(--accent);font-family:var(--sans);
font-weight:500;font-size:1.05rem;line-height:1.7;color:var(--ink)}
blockquote p{margin:0 0 .55rem}blockquote p:last-child{margin:0}
blockquote.src{font-family:var(--serif);font-weight:400;font-size:.95rem;color:var(--muted);border-left-color:var(--rule)}
.tw{overflow-x:auto;margin:1.7rem 0}
table{border-collapse:collapse;width:100%;font-family:var(--mono);font-size:.79rem;font-variant-numeric:tabular-nums;line-height:1.5}
th,td{padding:.5rem .7rem;text-align:right;border-bottom:1px solid var(--rule-soft);white-space:nowrap}
th:first-child,td:first-child{text-align:left;padding-left:0;font-family:var(--sans);font-size:.82rem;white-space:normal}
th:last-child,td:last-child{padding-right:0}
thead th{border-bottom:1px solid var(--rule);color:var(--muted);font-weight:500;font-size:.72rem;letter-spacing:.06em}
tbody tr:last-child td{border-bottom:0}
.neg{color:var(--neg)}.pos{color:var(--pos)}
ol.rules{counter-reset:r;list-style:none;padding:0;margin:1.4rem 0}
ol.rules li{counter-increment:r;position:relative;padding:.55rem 0 .55rem 2.3rem;border-bottom:1px solid var(--rule-soft)}
ol.rules li:last-child{border-bottom:0}
ol.rules li::before{content:counter(r);position:absolute;left:0;top:.62rem;font-family:var(--mono);font-size:.72rem;color:var(--accent);font-weight:600}
figure{margin:2.3rem 0}
figure img{width:100%;display:block;border:1px solid var(--rule);background:#0d0f10}
figcaption{font-family:var(--mono);font-size:.72rem;line-height:1.6;color:var(--muted);margin-top:.7rem;border-left:2px solid var(--accent);padding-left:.7rem}
figcaption b{color:var(--ink);font-weight:500}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:.7rem}
@media (max-width:620px){.pair{grid-template-columns:1fr}}
.pairlab{font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;color:var(--accent);text-transform:uppercase;margin-bottom:.35rem}
.chart{margin:2.1rem 0;border:1px solid var(--rule);background:var(--panel);padding:1.2rem 1rem .8rem}
.chart svg{width:100%;height:auto;display:block}
.chart .g{stroke:var(--rule-soft);stroke-width:1}
.chart text.ax{font-family:var(--mono);font-size:9px;fill:var(--muted)}
.chart .lvl{stroke:var(--ink);stroke-width:1;stroke-dasharray:4 3;opacity:.75}
.chart .lvlT,.chart .entryT{font-family:var(--mono);font-size:9.5px;fill:var(--ink);font-weight:600}
.chart .entry{stroke:var(--accent);stroke-width:1.2}.chart .entryT{fill:var(--accent)}
.chart .risk{fill:var(--neg);opacity:.12}
.chart .m10{fill:none;stroke:var(--muted);stroke-width:1;opacity:.55}
.chart .m20{fill:none;stroke:var(--accent);stroke-width:1.4}
.chart .m50{fill:none;stroke:var(--muted);stroke-width:1.4;stroke-dasharray:3 2;opacity:.8}
.chart .wick{stroke-width:1}
.chart .wick.up,.chart .body.up{stroke:var(--pos)}.chart .wick.dn,.chart .body.dn{stroke:var(--neg)}
.chart .body.up{fill:var(--ground)}.chart .body.dn{fill:var(--neg)}
.chart .note{font-family:var(--mono);font-size:8.6px;fill:var(--ink);font-weight:600}
.chart .cap{font-family:var(--mono);font-size:9px;fill:var(--muted)}
.chart .bar{fill:var(--accent)}.chart .bar.dim{fill:var(--muted);opacity:.32}
.chart .fun{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1}
.chart .funT{font-family:var(--mono);font-size:10.5px;fill:var(--ink);font-weight:600}
.chart .lnA{fill:none;stroke:var(--accent);stroke-width:1.8}
.chart .lnN{fill:none;stroke:var(--neg);stroke-width:1.8}
.chart .lnM{fill:none;stroke:var(--muted);stroke-width:1.6;opacity:.85}
.chart .dotA{fill:var(--accent)}.chart .dotN{fill:var(--neg)}.chart .dotM{fill:var(--muted)}
.chart .barP{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1}
.chart .barR{fill:var(--neg);opacity:.85}
.chart .big{font-family:var(--sans);font-size:22px;font-weight:700;fill:var(--ink)}
.chart .lbl{font-family:var(--mono);font-size:9.5px;fill:var(--muted)}
.chart .val{font-family:var(--mono);font-size:10.5px;fill:var(--ink);font-weight:600}
.facts{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);padding:.4rem 0;margin:0 0 1.8rem}
.facts div{display:grid;grid-template-columns:5.6rem 1fr;gap:1rem;padding:.62rem 0;border-bottom:1px solid var(--rule-soft);align-items:baseline}
.facts div:last-child{border-bottom:0}
.facts .d{font-family:var(--mono);font-size:.8rem;color:var(--accent);font-weight:500}
.facts p{margin:0}
@media (max-width:640px){.facts div{grid-template-columns:4.6rem 1fr;gap:.7rem}}
.ledger{margin:3.2rem 0 0;border-top:2px solid var(--ink);border-bottom:1px solid var(--rule);padding:.9rem 0;
font-family:var(--mono);font-size:.74rem;display:flex;flex-wrap:wrap;gap:.35rem 1.1rem;color:var(--muted);font-variant-numeric:tabular-nums}
.ledger b{color:var(--ink);font-weight:600}.ledger .lb{color:var(--accent)}
hr{border:0;border-top:1px solid var(--rule);margin:2.6rem 0}
@media (max-width:640px){body{font-size:16px}h2{font-size:1.18rem}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>'''


def inline(t):
    t = H.escape(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    t = re.sub(r'〔(.+?)〕', r'<span style="color:var(--accent);font-family:var(--mono);font-size:.8em">〔\1〕</span>', t)
    return t


def cellclass(c):
    s = re.sub(r'<[^>]+>', '', c)
    if re.search(r'−|-\d', s) and '%' in s or s.strip().startswith('−'):
        return ' class="neg"'
    if re.match(r'^\+', s.strip()):
        return ' class="pos"'
    return ''


def render(md):
    lines = md.split('\n')
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if re.match(r'^\|', ln) and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|', lines[i + 1]):
            rows = []
            while i < len(lines) and re.match(r'^\|', lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            head, body = rows[0], rows[2:]
            th = ''.join(f'<th>{inline(c)}</th>' for c in head)
            tb = ''
            for r in body:
                tb += '<tr>' + ''.join(f'<td{cellclass(inline(c))}>{inline(c)}</td>' for c in r) + '</tr>'
            hd = f'<thead><tr>{th}</tr></thead>' if any(c for c in head) else ''
            out.append(f'<div class="tw"><table>{hd}<tbody>{tb}</tbody></table></div>')
            continue
        if ln.startswith('> '):
            buf = []
            while i < len(lines) and lines[i].startswith('>'):
                buf.append(lines[i].lstrip('>').strip()); i += 1
            cls = ' class="src"' if buf and buf[0].startswith('*') else ''
            out.append(f'<blockquote{cls}>' + ''.join(f'<p>{inline(b)}</p>' for b in buf if b) + '</blockquote>')
            continue
        if re.match(r'^\d+\.\s', ln):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i]):
                items.append(re.sub(r'^\d+\.\s', '', lines[i])); i += 1
            out.append('<ol class="rules">' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol>')
            continue
        if ln.startswith('### '):
            out.append(f'<h3>{inline(ln[4:])}</h3>'); i += 1; continue
        if ln.startswith('## '):
            out.append(f'<h2>{inline(ln[3:])}</h2>'); i += 1; continue
        if ln.strip() == '---':
            i += 1; continue
        if ln.strip():
            out.append(f'<p>{inline(ln.strip())}</p>')
        i += 1
    return '\n'.join(out)


FIGS = {
 '目标价从哪来': f'<figure><img src="{imgs["fast"]}" alt="MRNA 全历史与 120 水平线"><figcaption><b>那条横穿全图的线就是 120。</b>2020 年冲上去的那段中间几乎没有交易——没有交易的地方，回来的时候一样快。<b>目标价不是猜的，是这段历史给的。</b></figcaption></figure>',
 '你自己': f'<figure><img src="{imgs["daily"]}" alt="MRNA 日线全景：一年底部与 60 一线"><figcaption><b>放远看同一件事。</b>左边横着的是躺了一年的底，那条水平线就是 60——2026 年它被反复测试过。右边那根直上直下的是 8月19日。</figcaption></figure>',
 '开盘第一分钟': f'<figure><img src="{imgs["minute"]}" alt="MRNA 8月19日一分钟图，开盘量能爆发"><figcaption><b>8月19日，一分钟。</b>左下两个标记是盘前那两笔。开盘第一分钟 RVOL 直接爆了，之后价格全程站在一分钟开盘区间之上。</figcaption></figure>',
 '先板块，再探头': f'<div class="chart">{imgs["funnel"]}</div>',
 '三个月超额收益，每晚归档': f'<div class="chart">{imgs["sectors"]}</div>',
 '那八个交易日': f'<div class="chart">{imgs["rsline"]}</div>',
 '怎么量': f'<div class="chart">{imgs["band"]}</div>',
 '第一笔买的是结构': f'<div class="chart">{imgs["sizing"]}</div>',
 '市场连着三天变坏': f'<div class="chart">{imgs["breadth3"]}</div>',
 '八月上半月市场在磨': f'<figure><img src="{imgs["qqq"]}" alt="QQQ 日线，8月中旬动能停滞"><figcaption><b>8月13–14 的 QQQ。</b>七月底那波动能反转向上之后，这里停住了。我当时不在看生物科技。</figcaption></figure>',
 '半导体整个八月一次都没转正': f'<figure><div class="pair"><div><div class="pairlab">XBI · 生物科技</div><img src="{imgs["xbi"]}" alt="XBI 日线"></div><div><div class="pairlab">SNOW · 软件</div><img src="{imgs["snow"]}" alt="SNOW 日线"></div></div><figcaption><b>当时看到 XBI 那张图，我的第一反应是：这个图非常眼熟。</b><br>盘整 → 突破 → 拉伸 → 回踩均线 → 再拉伸。<b>两张图是同一个形状</b>——右边是我六七月一直在做的软件板块。</figcaption></figure>',
 '而 60 是这张图挂着的那根钉子': f'<div class="chart">{imgs["zoomsvg"]}</div>',
 '它还有一个不寻常的地方': f'<figure><img src="{imgs["fast"]}" alt="MRNA 全历史与 120 水平线"><figcaption><b>那条横穿全图的线就是 120。</b>2020 年从二十几块冲上去的时候中间几乎没有交易——<b>没有交易的地方，回来的时候一样快。</b>目标价不是猜的，是这段历史给的。</figcaption></figure>',
 '我看的是一分钟，不是五分钟': f'<figure><img src="{imgs["minute"]}" alt="MRNA 8月19日一分钟图"><figcaption><b>8月19日，一分钟。</b>开盘第一分钟 <b>140k 股</b>，第一根五分钟就收回了 VWAP。</figcaption></figure>',
}


EN_FIGS = {
 'Sector first. Then what surfaced': f'<div class="chart">{imgs["funnel_en"]}</div>',
 'The group data had been saying': f'<div class="chart">{imgs["sectors_en"]}</div>',
 'On any given Thursday': f'<figure><div class="pair"><div><div class="pairlab">XBI · Biotech</div><img src="{imgs["xbi"]}" alt="XBI daily"></div><div><div class="pairlab">SNOW · Software</div><img src="{imgs["snow"]}" alt="SNOW daily"></div></div><figcaption><b>The chart that made biotech familiar.</b> Base → breakout → extend → pull back to the average → extend again. <b>Same shape</b> — the right panel is the software group I had been trading since June.</figcaption></figure>',
 'A stock climbing off the floor': f'<div class="chart">{imgs["rsline_en"]}</div>',
 'My rule is short': f'<div class="chart">{imgs["band_en"]}</div>',
 'And $60 is the nail': f'<div class="chart">{imgs["zoomsvg_en"]}</div>',
 'The first buys the': f'<div class="chart">{imgs["sizing_en"]}</div>',
 'Three sessions of deterioration': f'<div class="chart">{imgs["breadth3_en"]}</div>',
 'The first half of August was a grind': f'<figure><img src="{imgs["qqq"]}" alt="QQQ daily, momentum stalling mid-August"><figcaption><b>QQQ, Aug 13–14.</b> The late-July momentum turn stalls here. I was not looking at biotech.</figcaption></figure>',
 'Where the target came from': f'<figure><img src="{imgs["fast"]}" alt="MRNA full history with the 120 level"><figcaption><b>The horizontal line across the whole chart is 120.</b> The COVID run went through that zone with almost no trading. <b>Empty on the way up, empty on the way back — the target came from this history, not from a guess.</b></figcaption></figure>',
 'Your own chart has a line like that': f'<figure><img src="{imgs["daily"]}" alt="MRNA daily, one-year base and the 60 level"><figcaption><b>Zoomed out.</b> The flat stretch on the left is a year-long base; the horizontal line is 60, tested repeatedly through 2026. The vertical bar on the right is Aug 19.</figcaption></figure>',
 'The first minute of the open': f'<figure><img src="{imgs["minute"]}" alt="MRNA one-minute chart, Aug 19 open"><figcaption><b>Aug 19, one-minute.</b> The two marks at lower left are the pre-market trades. RVOL exploded on the first minute; price held above the one-minute opening range all day.</figcaption></figure>',
}

def build(src, out, title, kicker, dek, badge, note, figkeys, clean=False, figs=None, h1=None):
    md = io.open(SRC + src, encoding='utf-8').read()
    md = md.split('## 拆出去的四个零件')[0]
    md = re.sub(r'^# .*$', '', md, flags=re.M)
    md = re.sub(r'^### \*.*\*$', '', md, flags=re.M)
    # 只删单星号的斜体元信息行；**整段加粗** 必须留下
    md = re.sub(r'^\*(?!\*)[^\n]*(?<!\*)\*\s*$', '', md, flags=re.M)

    MARK = '以上是全部事实。下面是复盘。' if '以上是全部事实' in md else 'Those are the facts. What follows is the review.'
    head, rest = md.split(MARK, 1)
    facts = []
    for m in re.finditer(r'\*\*(.+?)\*\*[，,.]?\s*(.+)', head):
        d, t = m.group(1).rstrip('.'), m.group(2).strip()
        if re.match(r'^(\d+月|Aug )', d):
            facts.append(f'<div><span class="d">{inline(d)}</span><p>{inline(t)}</p></div>')
    body = render(MARK + rest)
    ALT = {'而 60 是这张图挂着的那根钉子': ['而 60 是这张图挂着的那根钉子', '而 60 块钱是整件事挂着的那根钉子'],
           '你自己': ['你自己那张图上也有一条', '你自己手上那张图也有一条'],
           '半导体整个八月一次都没转正': ['半导体整个八月一次都没转正']}
    figs = figs or FIGS
    for k in figkeys:
        fig = figs[k]
        pos = -1
        for cand in ALT.get(k, [k]):
            pos = body.find(cand)
            if pos >= 0: break
        if pos < 0:
            print('  !! 锚点找不到:', k); continue
        start = body.rfind('<p>', 0, pos)
        if start < 0:
            start = pos
        body = body[:start] + fig + '\n' + body[start:]
    html = f'''<title>{title}</title>
{CSS}
<div class="wrap">
<header class="mast">
  <p class="kicker">{kicker}</p>
  <h1>{h1 or '我是怎么吃到 $MRNA 那 176% 的'}</h1>
  <p class="dek">{dek}</p>
  <div class="byline"><span><b>Fluxus</b></span><span>2026-08-24</span>{'' if clean else f'<span>{badge}</span>'}</div>
</header>
{'' if clean else f'<div class="draft">{note}</div>'}
<div class="facts">{''.join(facts)}</div>
{body}
<div class="ledger"><span class="lb">台账</span><span>$MRNA</span><span>8/14 入场 <b>62.72</b></span><span>止损 <b>60</b></span><span>交易风险 <b>0.233%</b></span><span>8/19 平仓</span><span><b>+23R</b></span></div>
</div>'''
    io.open(SRC + out, 'w', encoding='utf-8').write(html)
    src_z = len(re.findall('[一-鿿]', md))
    txt = re.sub(r'<[^>]+>', '', html)
    out_z = len(re.findall('[一-鿿]', txt))
    flag = 'OK' if out_z >= src_z * 0.97 else f'!! 丢了 {src_z-out_z} 字'
    print(f'  {out}: 源 {src_z} 字 → 渲染 {out_z} 字  {flag}')
    return len(html) // 1024


a = build('DRAFT_v1_full_zh.md', 'preview.html', 'MRNA 的十二天', 'How Much',
          '三个筛子、五条探头准则，以及"多大"的确切答案：0.25% 换 23R', '', '',
          ['八月上半月市场在磨', '半导体整个八月一次都没转正', '而 60 是这张图挂着的那根钉子',
           '它还有一个不寻常的地方', '我看的是一分钟，不是五分钟'], clean=True)
b = build('DRAFT_v2_trunk_zh.md', 'preview_trunk.html', 'MRNA 主干', 'How Much',
          '三个筛子、五条探头准则，以及"多大"的确切答案：0.25% 换 23R', '', '',
          ['先板块，再探头', '三个月超额收益，每晚归档', '半导体整个八月一次都没转正',
           '那八个交易日', '怎么量', '而 60 是这张图挂着的那根钉子', '你自己', '目标价从哪来',
           '第一笔买的是结构', '市场连着三天变坏', '开盘第一分钟'], clean=True)
c = build('DRAFT_v2_trunk_en.md', 'preview_en.html', 'How I Caught 176% in MRNA', 'How Much',
          'The exact 3 filters, the 5 scanner rules, and exactly how much: 0.25% for 23R', '', '',
          list(EN_FIGS.keys()), clean=True, figs=EN_FIGS, h1='How I Caught a 176% Move in $MRNA')
print('完整版', a, 'KB · 主干版', b, 'KB · EN', c, 'KB')
