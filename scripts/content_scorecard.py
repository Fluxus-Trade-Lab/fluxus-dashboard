#!/usr/bin/env python3
"""周度记分卡 — 按口诀分桶,看哪种帖真的带来「意图」。

反多巴胺设计:每周跑一次,**意图指标优先**(收藏率/关注/回复),views 只当分母。
数据源:data/content/posts.csv(Claude 在周日用浏览器抓取后填入)。
用法:python3 scripts/content_scorecard.py [--weeks 1] [--push]
"""
import csv, sys, pathlib, datetime, statistics, json, os, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / 'data' / 'content' / 'posts.csv'

BUCKETS = {
    'DATA': '晒数', 'REPLY': '蹭号', 'JAB': '冷嘲', 'LINE': '金句',
    'CALLBACK': '翻帖', 'SPICE': '撒料', 'TEACH': '教学长文', 'ARC': '剧情',
}

def num(v):
    v = (v or '').strip().replace(',', '')
    try:
        return float(v)
    except ValueError:
        return None

def load(weeks):
    if not CSV.exists():
        sys.exit(f'缺少 {CSV}')
    cutoff = datetime.date.today() - datetime.timedelta(days=7 * weeks)  # localtime-ok: content cadence, not a trading session
    rows = []
    for r in csv.DictReader(CSV.open(encoding='utf-8')):
        try:
            d = datetime.date.fromisoformat(r['date'])
        except (ValueError, KeyError):
            continue
        if d >= cutoff:
            r['_d'] = d
            for k in ('views', 'likes', 'replies', 'reposts', 'bookmarks', 'follows'):
                r[k] = num(r.get(k))
            rows.append(r)
    return rows

def rate(part, whole):
    return (part / whole * 100) if (part and whole) else None

def fmt(x, suffix='', dash='—'):
    return f'{x:.2f}{suffix}' if isinstance(x, float) else dash

def main():
    weeks = 1
    if '--weeks' in sys.argv:
        weeks = int(sys.argv[sys.argv.index('--weeks') + 1])
    rows = load(weeks)
    if not rows:
        sys.exit('窗口内没有帖子 — 先往 data/content/posts.csv 里填数据')

    lines = [f'📊 **内容记分卡 · 近 {weeks} 周**  ({len(rows)} 条帖)', '']

    # —— 意图指标优先 ——
    tot_v = sum(r['views'] or 0 for r in rows)
    tot_b = sum(r['bookmarks'] or 0 for r in rows)
    tot_f = sum(r['follows'] or 0 for r in rows)
    tot_r = sum(r['replies'] or 0 for r in rows)
    lines += ['**总览(意图优先)**',
              f'· 收藏 {int(tot_b)}  → 收藏率 {fmt(rate(tot_b, tot_v), "%")}   ← 最该看的一个数',
              f'· 新增关注 {int(tot_f)}   · 回复 {int(tot_r)}',
              f'· (views {int(tot_v)} — 只当分母,别当成绩)', '']

    # —— 按口诀分桶 ——
    by = {}
    for r in rows:
        by.setdefault(r.get('bucket', '?').strip().upper(), []).append(r)

    lines.append('**按口诀分桶**')
    lines.append('| 桶 | 条 | 收藏率 | 关注 | 回复 | 中位 views |')
    lines.append('|---|---|---|---|---|---|')
    ranked = []
    for b, rs in by.items():
        v = sum(x['views'] or 0 for x in rs)
        bm = sum(x['bookmarks'] or 0 for x in rs)
        f = sum(x['follows'] or 0 for x in rs)
        rp = sum(x['replies'] or 0 for x in rs)
        med = statistics.median([x['views'] for x in rs if x['views']]) if any(x['views'] for x in rs) else None
        br = rate(bm, v)
        ranked.append((br or -1, b, len(rs)))
        name = f'{BUCKETS.get(b, b)} {b}'
        lines.append(f'| {name} | {len(rs)} | {fmt(br, "%")} | {int(f)} | {int(rp)} | {fmt(med) if med else "—"} |')
    lines.append('')

    # —— 单帖榜(按收藏率) ——
    scored = [r for r in rows if r['bookmarks'] and r['views']]
    if scored:
        scored.sort(key=lambda r: r['bookmarks'] / r['views'], reverse=True)
        lines.append('**收藏率最高的 3 条**')
        for r in scored[:3]:
            br = r['bookmarks'] / r['views'] * 100
            lines.append(f'· {br:.2f}%  [{r.get("bucket")}] {r.get("note","")[:44]}')
        lines.append('')

    # —— 结论 ——
    ranked.sort(reverse=True)
    if ranked and ranked[0][0] >= 0:
        top = ranked[0]
        lines.append(f'**下周多写:{BUCKETS.get(top[1], top[1])}**(收藏率最高)')
    else:
        lines.append('_收藏/关注列还是空的 → 这周先补数据,结论下周见_')

    out = '\n'.join(lines)
    print(out)

    if '--push' in sys.argv:
        url = os.environ.get('FLUXUS_WEBHOOK_URL', '')
        wf = pathlib.Path.home() / '.fluxus_webhook'
        if not url and wf.exists():
            url = wf.read_text().strip()
        if url.startswith('https://'):
            payload = {'content': out[:1900]}
            try:
                urllib.request.urlopen(urllib.request.Request(
                    url, data=json.dumps(payload).encode(),
                    headers={'Content-Type': 'application/json'}), timeout=10)
            except Exception:
                payload['thread_name'] = f'📊 记分卡 · {datetime.date.today()}'  # localtime-ok: post label, not a trading date
                try:
                    urllib.request.urlopen(urllib.request.Request(
                        url, data=json.dumps(payload).encode(),
                        headers={'Content-Type': 'application/json'}), timeout=10)
                except Exception as e:
                    print(f'push failed: {e}', file=sys.stderr)

if __name__ == '__main__':
    main()
