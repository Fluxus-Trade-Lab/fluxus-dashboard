#!/usr/bin/env python3
"""每日复盘草稿生成器 —— 把「写」降级成「改」。

设计原则(2026-08-26 与 Andy 定):
  1. **能算的全部自动填,要判断的一律留空。** 每个 `>>` 是只有他能写的地方。
  2. **教学口径,不是信号口径。** 输出里没有"今天买什么",只有"我当时看到什么、为什么这么算"。
  3. **永不出现美元金额**(`_BOILERPLATE.md` 全刊铁律)。只用 R 和 %。脚本末尾有硬校验。
  4. 没有交易的日子**不跳过** —— "今天没动手"和为什么没动手,本身就是内容。

用法:
    python3 Fluxus_Substack/tools/daily_recap.py                 # 最新有数据的一天
    python3 Fluxus_Substack/tools/daily_recap.py --date 2026-08-19
    python3 Fluxus_Substack/tools/daily_recap.py --out drafts/   # 写文件而不是 stdout
"""
import argparse
import csv
import datetime as dt
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MONEY = re.compile(r'\$\s?[\d,]+(?:\.\d+)?|\b\d[\d,]*\s?(?:dollars|美元|万美元)\b', re.I)


# ── 读数据:优先工作区,缺了回落到 origin/main ──────────────────────────
def read(relpath):
    p = ROOT / relpath
    if p.exists():
        return p.read_text()
    try:
        return subprocess.run(['git', '-C', str(ROOT), 'show', f'origin/main:{relpath}'],
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None


def rows(relpath):
    raw = read(relpath)
    return list(csv.DictReader(io.StringIO(raw))) if raw else []


def num(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def load_trades():
    """全部交易记录。工作区没有就从 origin/main 批量取。"""
    d = ROOT / 'data/output/trades'
    blobs = []
    if d.exists():
        blobs = [f.read_text() for f in sorted(d.glob('*.json'))]
    else:
        listing = subprocess.run(['git', '-C', str(ROOT), 'ls-tree', '-r', 'origin/main',
                                  '--name-only', 'data/output/trades/'],
                                 capture_output=True, text=True).stdout.split()
        for f in listing:
            b = read(f)
            if b:
                blobs.append(b)
    out = []
    for b in blobs:
        try:
            d = json.loads(b)
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict) and isinstance(d.get('trade'), dict):
            out.append(d)      # trades/ 目录里混着索引文件,只要单笔记录
    return out


# ── 各节 ─────────────────────────────────────────────────────────────
def sec_tape(br, date):
    idx = {r['date']: i for i, r in enumerate(br)}
    if date not in idx:
        return f"## ① 盘面\n\n*{date} 没有 breadth 归档。*\n\n>> 【一句话】今天的盘面让我改变了什么?\n"
    i = idx[date]
    t, y = br[i], br[i - 1] if i else None

    def d(k, fmt='{:+.1f}'):
        a, b = num(t.get(k)), num(y.get(k)) if y else None
        return '' if a is None or b is None else f"（{fmt.format(a - b)}）"

    spx = num(t.get('spx_close'))
    spx_chg = ''
    if y and spx and num(y.get('spx_close')):
        spx_chg = f" {(spx / num(y['spx_close']) - 1) * 100:+.2f}%"
    L = [f"## ① 盘面 · {date}", ""]
    L.append(f"S&P **{spx:,.0f}**{spx_chg}" if spx else "")
    L.append(f"4% 上涨 **{t.get('up_4pct')}** / 下跌 **{t.get('down_4pct')}**　·　"
             f"5日比 **{t.get('ratio_5d')}**{d('ratio_5d', '{:+.2f}')}　·　10日比 {t.get('ratio_10d')}")
    L.append(f"20日上方 **{t.get('pct_above_20sma')}%**{d('pct_above_20sma')}　·　"
             f"50日上方 {t.get('pct_above_50sma')}%{d('pct_above_50sma')}　·　"
             f"200日上方 {t.get('pct_above_200sma')}%{d('pct_above_200sma')}")
    L.append(f"新高 **{t.get('new_highs')}** / 新低 **{t.get('new_lows')}**　·　"
             f"麦克莱伦 {t.get('mcclellan_osc')}")
    return '\n'.join(x for x in L if x) + "\n\n>> 【一句话】这些读数今天让我改变了什么?**如果什么都没变,就写「什么都没变」** —— 那也是判断。\n"


def sec_regime(rg, date):
    r = next((x for x in rg if x['date'] == date), None)
    if not r:
        return ''
    on, avail = r.get('lamps_on'), r.get('lamps_available')
    return (f"**Regime**　VIX {r.get('vix')}　·　趋势态 {r.get('ts_state')}　·　"
            f"新高新低态 {r.get('nhnl_state')}　·　信用 OAS {r.get('oas')}　·　"
            f"**灯 {on}/{avail}**\n")


def sec_rotation(gr, date, n=6):
    day = [r for r in gr if r['date'] == date and r.get('kind') == 'industry']
    if not day:
        return f"## ② 轮动\n\n*{date} 没有 groups 归档。*\n\n>> 【一句话】\n"
    for r in day:
        r['_e'] = num(r.get('excess_3m'), -99)
        r['_a'] = num(r.get('rs_accel'), 0)
        r['_p'] = num(r.get('persistence'), 0)
    imp = sorted([r for r in day if r.get('state') == 'Improving'],
                 key=lambda r: (-r['_a'], -r['_p']))[:n]
    strong = sorted(day, key=lambda r: -r['_e'])[:n]
    L = ["## ② 轮动", "",
         f"**当下最强**（3个月超额）　·　共 {len(day)} 组", "",
         "| 组 | excess_3m | 加速度 | 状态 | 持续 |", "|---|---:|---:|---|---:|"]
    for r in strong:
        L.append(f"| {r['group'][:30]} | {r['_e']:+.3f} | {r['_a']:+.3f} | {r.get('state')} | {r['_p']:.0f} |")
    L += ["", "**加速度最快的 Improving**（明天的强,今天还很弱）", "",
          "| 组 | excess_3m | 加速度 | 持续 |", "|---|---:|---:|---:|"]
    for r in imp:
        L.append(f"| {r['group'][:30]} | {r['_e']:+.3f} | **{r['_a']:+.3f}** | {r['_p']:.0f} |")
    n_w = sum(1 for r in strong if r.get('state') == 'Weakening')
    if n_w >= len(strong) - 1:
        L += ["", f"> ⚠️ 最强的 {len(strong)} 组里有 {n_w} 组在 Weakening —— **领导权在换手**。"]
    return '\n'.join(L) + "\n\n>> 【一句话】我更信 persistence 还是排名?这张表今天改变了我什么?\n"


def sec_book(trades, date):
    closed = [t for t in trades if t['trade'].get('exit_date') == date]
    opened = [t for t in trades if t['trade'].get('entry_date') == date]
    L = ["## ④ 我做了什么", ""]
    if not closed and not opened:
        L += ["**今天没动手。**", "",
              ">> 【这一段是内容,不是免责】今天什么都没做的理由是什么?"
              "我在等什么条件?**「没动手」的日子占我全年的大多数,读者最缺的正是这个。**"]
        return '\n'.join(L) + "\n"
    seen_open = set()
    for t in opened:
        tr, e = t['trade'], t.get('entry_snapshot') or {}
        key = (tr['ticker'], tr.get('entry_price'), tr.get('initial_stop'))
        if key in seen_open:
            continue          # 同票同价同止损 = 同一笔的重复记录
        seen_open.add(key)
        ep, sp, atr = num(tr.get('entry_price')), num(tr.get('initial_stop')), num(e.get('atr14'))
        sd = (ep - sp) / ep * 100 if ep and sp else None
        sa = (ep - sp) / atr if ep and sp and atr else None
        L.append(f"**开仓 {tr['ticker']}**　入场 {ep}　止损 {sp}"
                 + (f"　距离 **{sd:.2f}%**" if sd else '')
                 + (f"　= **{sa:.2f} ATR**" if sa else '')
                 + (f"　·　RSI {num(e.get('rsi14')):.0f}" if e.get('rsi14') else '')
                 + (f"　·　52周位置 {num(e.get('position_in_52w_range_pct')):.0f}%"
                    if e.get('position_in_52w_range_pct') else ''))
        L.append(">> 【每笔一句】我当时看到了什么?**为什么止损放在这里,而不是别处?**"
                 "这个距离让我拿到了多大的仓位?")
        L.append("")
    # 同一天同一票的多条记录 = 两腿结构的各腿,合并成一行,但把腿数留在明面上
    byticker = {}
    for t in closed:
        byticker.setdefault(t['trade']['ticker'], []).append(t)
    for tk, legs in sorted(byticker.items(), key=lambda kv: -sum(num(t['trade'].get('realized_R'), 0) for t in kv[1])):
        Rs = [num(t['trade'].get('realized_R')) for t in legs]
        Rs = [x for x in Rs if x is not None]
        caps = [num((t.get('path_analytics') or {}).get('capture_pct')) for t in legs]
        caps = [c for c in caps if c is not None]
        hold = max((num(t['trade'].get('hold_business_days'), 0) for t in legs), default=0)
        lessons = sorted({t['lesson'] for t in legs if t.get('lesson')})
        head = f"**平仓 {tk}**　**{sum(Rs):+.2f}R**"
        if len(legs) > 1:
            head += f"（{len(legs)} 腿:{' / '.join(f'{x:+.2f}' for x in Rs)}）"
        if caps:
            head += f"　吃到 **{sum(caps) / len(caps):.0f}%**"
        head += f"　持仓 {hold:.0f} 天"
        if lessons:
            head += f"　·　机器判词:*{' · '.join(lessons)}*"
        L.append(head)
        L.append(">> 【每笔一句】现在回头看,我离场早了还是晚了?**下次同样的图我会做同样的事吗?**")
        L.append("")
    return '\n'.join(L)


def sec_running(trades, date):
    d0 = dt.date.fromisoformat(date)
    wk = d0 - dt.timedelta(days=d0.weekday())
    yr = d0.replace(month=1, day=1)

    def agg(since):
        v = [num(t['trade'].get('realized_R')) for t in trades
             if t['trade'].get('closed') and t['trade'].get('exit_date')
             and since.isoformat() <= t['trade']['exit_date'] <= date]
        v = [x for x in v if x is not None]
        if not v:
            return None
        return len(v), sum(1 for x in v if x > 0) / len(v) * 100, sum(v)

    L = ["## ⑥ 台账", "", "| 区间 | 笔数 | 胜率 | 累计 R |", "|---|---:|---:|---:|"]
    for name, since in (("本周", wk), ("今年", yr)):
        a = agg(since)
        L.append(f"| {name} | {a[0]} | {a[1]:.1f}% | {a[2]:+.1f} |" if a else f"| {name} | 0 | — | — |")
    return '\n'.join(L) + "\n\n*这一节不用改。它每期都在,而且是发出去就改不了的那部分。*\n"



def sec_bridge(br, rg, date):
    """③ 连接 —— 全文唯一不能自动生成、也唯一不可替代的一节。

    ①②给环境,④给动作,但读者真正看不见的是**中间那一步**:
    环境读数怎么改变了风险预算。这正是 05_SIZING_TERRITORY 第 14–17 条
    (regime → 风险预算 → 仓位)——「别人连原料都有却没人走完的路径」。
    """
    t = next((r for r in br if r['date'] == date), None)
    g = next((r for r in rg if r['date'] == date), None)
    cue = []
    if t:
        cue.append(f"20日上方 {t.get('pct_above_20sma')}%")
        cue.append(f"5日比 {t.get('ratio_5d')}")
        cue.append(f"新高{t.get('new_highs')}/新低{t.get('new_lows')}")
    if g:
        cue.append(f"灯 {g.get('lamps_on')}/{g.get('lamps_available')}")
    return ("## ③ 所以我怎么调整\n\n"
            + (f"*今天的输入:{'　·　'.join(cue)}*\n\n" if cue else "")
            + ">> 【必答,一到三句】上面这些读数**具体改变了我的哪个数字**?\n"
              ">> R 还是 0.25% 吗?总风险上限动了吗?单主题上限动了吗?愿意开几个新仓?\n"
              ">> **如果一个数都没动,就写「一个都没动」并说明为什么** —— 那也是完整的答案。\n\n"
            "> ⚠️ 这一节是全篇唯一不能省的。①②任何人都能生成,④是我的日记,\n"
            "> **只有③是「怎么从读数走到仓位」——那条路径没有别人走完过。**\n")


def sec_tomorrow():
    """⑤ 明天的条件 —— 让这一篇可以被明天那篇回访。"""
    return ("## ⑤ 明天我在等什么\n\n"
            ">> 【必答,写成条件不写成名字】我在等哪个**条件**出现?\n"
            ">> 例:「20日上方重回 55% 以上我才加风险」「贵金属那组 persistence 到 5 天我才认」\n\n"
            "> ⚠️ **写条件,不写「我要买 XYZ」。** 条件是教学,名字加价格是信号——\n"
            "> 信号是 Discord 那档的东西。这条线靠这一节的写法守住。\n"
            "> 而且条件可以被明天的自己回访,名字只能被验证对错。\n")


def sec_callback(outdir, date):
    """开头的回访:把昨天那篇的⑤原样贴出来,逼今天这篇跟它对账。"""
    if not outdir:
        return ''
    prev = sorted(Path(outdir).glob('recap_*.md'))
    prev = [f for f in prev if f.stem[len('recap_'):] < date]
    if not prev:
        return ''
    txt = prev[-1].read_text()
    m = re.search(r'## ⑤ 明天我在等什么\s*\n(.*?)(?=\n## |\Z)', txt, re.S)
    if not m:
        return ''
    body = '\n'.join(l for l in m.group(1).strip().split('\n')
                     if l.strip() and not l.lstrip().startswith(('>>', '>')))
    if not body:
        return ''
    d = prev[-1].stem[len('recap_'):]
    return (f"> **回访 · {d} 我说过:**\n> " + body.replace('\n', '\n> ')
            + "\n>\n>> 【必答】发生了吗?我照做了吗?\n\n---\n")



def build_post(date=None):
    """--post:X 日更的骨架。机器填盘面和分母,他写四行。
    规矩见 Fluxus_Substack/templates/daily_post.md。"""
    br = rows('data/history/breadth_archive.csv')
    trades = load_trades()
    if not date:
        date = br[-1]['date'] if br else dt.date.today().isoformat()
    t = next((r for r in br if r['date'] == date), None)
    i = next((k for k, r in enumerate(br) if r['date'] == date), None)
    y = br[i - 1] if i else None

    def delta(k, fmt='{:+.1f}'):
        a, b = (num(t.get(k)) if t else None), (num(y.get(k)) if y else None)
        return '' if a is None or b is None else f"（{fmt.format(a - b)}）"

    tape = '—'
    if t:
        tape = (f"20日上方 {t.get('pct_above_20sma')}%{delta('pct_above_20sma')}"
                f"　·　5日比 {t.get('ratio_5d')}{delta('ratio_5d', '{:+.2f}')}"
                f"　·　新高{t.get('new_highs')}/新低{t.get('new_lows')}")

    yr = dt.date.fromisoformat(date).replace(month=1, day=1).isoformat()
    v = [num(x['trade'].get('realized_R')) for x in trades
         if x['trade'].get('closed') and x['trade'].get('exit_date')
         and yr <= x['trade']['exit_date'] <= date]
    v = [x for x in v if x is not None]
    denom = (f"今年 {len(v)} 笔 · {sum(1 for x in v if x > 0) / len(v) * 100:.1f}% · {sum(v):+.0f}R"
             if v else '今年 — 笔')

    opened = [x for x in trades if x['trade'].get('entry_date') == date]
    seen, specs = set(), []
    for x in opened:
        tr, e = x['trade'], x.get('entry_snapshot') or {}
        key = (tr['ticker'], tr.get('entry_price'), tr.get('initial_stop'))
        if key in seen:
            continue
        seen.add(key)
        ep, sp, atr = num(tr.get('entry_price')), num(tr.get('initial_stop')), num(e.get('atr14'))
        specs.append(f"${tr['ticker']} · <setup名> · in {ep} / stop {sp}"
                     + (f" / {(ep - sp) / atr:.2f} ATR" if ep and sp and atr else '')
                     + " / <n>%")

    L = [f"# X 日更 · {date}", "",
         "*机器填了盘面和分母。你写 `<>` 里的四处,十分钟以内。*",
         "*规矩:`Fluxus_Substack/templates/daily_post.md`*", "", "```", "〔图〕", ""]
    L += (specs or ["今天没动手。", "", "为什么没有：<在等什么条件>"])
    L += ["",
          "为什么是它：<一到两句。今天这个凭什么排在别的前面>",
          "我看到什么：<一到两句。入场那一刻屏幕上的东西,不是事后的道理>",
          "",
          f"盘面：{tape}",
          "所以：<一句。上面让我把哪个数调了 —— 或者「一个数都没动」+ 为什么>",
          "",
          "明天等：<一个条件,不是一个名字>",
          "", denom, "```", "",
          f"> 配图文件名：`{date}_TICKER_entry_<setup>.png`",
          f"> ⚠️ `{denom}` 这一行要**烧进图里** —— 图会被人截走、脱离上下文。"]
    return '\n'.join(L), date


# ── 主 ───────────────────────────────────────────────────────────────
def build(date=None, outdir=None):
    br, gr, rg = rows('data/history/breadth_archive.csv'), \
        rows('data/history/groups_archive.csv'), rows('data/history/regime_ledger.csv')
    trades = load_trades()
    if not date:
        date = br[-1]['date'] if br else dt.date.today().isoformat()

    parts = [f"# 复盘 · {date}", "",
             "*草稿。`>>` 开头的每一行都要替换成你的话,替换完把 `>>` 删掉。*",
             "*目标 5 分钟读完 —— 机器给读数,你给判断。判断少于三句就不要发。*", "",
             "---", "", sec_callback(outdir, date),
             sec_tape(br, date), sec_regime(rg, date), "---", "",
             sec_rotation(gr, date), "", "---", "", sec_bridge(br, rg, date), "---", "",
             sec_book(trades, date), "---", "", sec_tomorrow(), "---", "",
             sec_running(trades, date), "---", "",
             "*How Much — one letter a week, every Sunday.*",
             "*Every idea arrives with its size and its stop.*", ""]
    return '\n'.join(parts), date


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    ap.add_argument('--out')
    ap.add_argument('--post', action='store_true', help='出 X 日更骨架而不是完整复盘')
    a = ap.parse_args()
    text, date = build_post(a.date) if a.post else build(a.date, a.out)

    hits = MONEY.findall(text)
    if hits:                      # 全刊铁律:永不出现美元金额
        print(f"🔴 输出里出现了金额,已拦下:{hits[:5]}", file=sys.stderr)
        sys.exit(1)

    if a.out:
        p = Path(a.out)
        p.mkdir(parents=True, exist_ok=True)
        f = p / f"recap_{date}.md"
        f.write_text(text)
        print(f"✅ {f}　({len(text)} 字符,待填 {text.count('>>')} 处)")
    else:
        print(text)


if __name__ == '__main__':
    main()
