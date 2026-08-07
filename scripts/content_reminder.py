#!/usr/bin/env python3
"""每日内容提醒 — 8:00 JST。
两个运行环境:
  · 本地 launchd(Mac 醒着时):macOS 通知
  · GitHub Actions cron 23:00 UTC(Mac 无关):推 Discord webhook(FLUXUS_WEBHOOK_URL secret)
读 Fluxus_Week_Plan.md(当日+明日,JST)+ Fluxus_Receipts/receipts.md(⏳未结项)。
"""
import re, os, sys, json, subprocess, datetime, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAN = ROOT / 'Fluxus_Week_Plan.md'
RECEIPTS = ROOT / 'Fluxus_Receipts' / 'receipts.md'

JST = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(JST).date()
tomorrow = today + datetime.timedelta(days=1)

def day_block(text, d):
    m = re.search(rf'^## {d}[^\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return m.group(1).strip() if m else None

msg_parts = [f'📋 **Fluxus 内容台 · {today}**']
plan = PLAN.read_text(encoding='utf-8') if PLAN.exists() else ''

blk = day_block(plan, today)
msg_parts.append('**— 今天 —**\n' + (blk if blk else '(周计划里没有今天的条目 — 让 Claude 补周计划)'))

blk_t = day_block(plan, tomorrow)
if blk_t:
    first = '\n'.join(blk_t.splitlines()[:2])
    msg_parts.append(f'**— 明天预告 —**\n{first}')

if RECEIPTS.exists():
    pend = [l.strip() for l in RECEIPTS.read_text(encoding='utf-8').splitlines() if '⏳' in l]
    keep = []
    for l in pend:
        cols = [c.strip() for c in l.strip('|').split('|')]
        if len(cols) >= 5:
            keep.append(f'· {cols[0]} {cols[2][:40]} → {cols[4][:40]}')
    if keep:
        msg_parts.append('**— 未结收据 —**\n' + '\n'.join(keep))

msg = '\n\n'.join(msg_parts)

# macOS 通知(仅本地)
if sys.platform == 'darwin' and not os.environ.get('GITHUB_ACTIONS'):
    short = (blk or '无条目').replace('"', "'").replace('\n', ' ')[:120]
    subprocess.run(['osascript', '-e',
                    f'display notification "{short}" with title "Fluxus 内容台" subtitle "{today} 今日清单"'],
                   check=False)

# Discord webhook:优先环境变量(云端 secret),其次 ~/.fluxus_webhook(本地可选)
url = os.environ.get('FLUXUS_WEBHOOK_URL', '')
wf = pathlib.Path.home() / '.fluxus_webhook'
if not url and wf.exists():
    url = wf.read_text().strip()
def post_webhook(u, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(u, data=data, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'FluxusContentReminder/1.0'})
    return urllib.request.urlopen(req, timeout=10)

if url.startswith('https://'):
    try:
        try:
            post_webhook(url, {'content': msg[:1900]})
        except urllib.error.HTTPError as e:
            if e.code == 400:  # 论坛频道:必须带 thread_name → 每日一个主题帖
                post_webhook(url, {'content': msg[:1900],
                                   'thread_name': f'📋 内容台 · {today}'})
            else:
                raise
        print('webhook: sent')
    except Exception as e:
        print(f'webhook: FAILED {e}', file=sys.stderr)

print(msg)
