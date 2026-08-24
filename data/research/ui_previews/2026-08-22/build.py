#!/usr/bin/env python3
"""Generate the four static previews from ONE fixture.

Static HTML on purpose: these files get opened straight off disk (file://),
where an external <script> is not reliably allowed to run. A preview that
renders an empty table when Andy double-clicks it is not a preview.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent

# ~30% of live screener rows carry no RS reading (project_screener_findings).
# Rows 3, 6, 8 are the unmeasured ones; row 8 is additionally out of universe,
# which today wears the SAME glyph as an unmeasured number.
ROWS = [
    dict(n=1, tk="MSTR", known=True,  state="BREAKING", rs=(88, 92, 81), accel=1.34,  inu=True),
    dict(n=2, tk="ACMR", known=True,  state="BASING",   rs=(71, 74, 69), accel=0.22,  inu=True),
    dict(n=3, tk="CHYM", known=False, state="BASING",   rs=None,         accel=None,  inu=True),
    dict(n=4, tk="AAOI", known=True,  state="EXTENDED", rs=(64, 58, 44), accel=-0.41, inu=True),
    dict(n=5, tk="CACI", known=True,  state="BASING",   rs=(52, 47, 55), accel=0.08,  inu=True),
    dict(n=6, tk="LGN",  known=False, state="BASING",   rs=None,         accel=None,  inu=True),
    dict(n=7, tk="AA",   known=True,  state="FAILED",   rs=(29, 22, 31), accel=-0.77, inu=True),
    dict(n=8, tk="ABSI", known=False, state=None,       rs=None,         accel=None,  inu=False),
    dict(n=9, tk="MRNA", known=True,  state="BREAKING", rs=(79, 83, 12), accel=0.95,  inu=True),
]


def rs_known(v: int) -> str:
    cls = "hi" if v >= 67 else "lo" if v <= 33 else ""
    return f'<td><span class="{cls}">{v}</span></td>'


def accel_known(r) -> str:
    a = r["accel"]
    sign = "+" if a > 0 else "−"
    return f'<td class="sec">{sign}{abs(a):.2f}</td>'


def align(r, unk_cls="dot-unk") -> str:
    """Left dot: own RS 3M >= 67. Right dot: industry state."""
    left = unk_cls if not r["known"] else ("dot-on" if r["rs"][1] >= 67 else "dot-off")
    right = "dot-on" if r["state"] == "BREAKING" else "dot-off"
    return f'<td class="c"><i class="dot {left}"></i><i class="dot {right}"></i></td>'


def state_cell(r) -> str:
    if r["state"]:
        return f'<td class="l state">{r["state"]}</td>'
    return '<td class="l state"><span class="mut">not in universe</span></td>'


def table(rs_missing, accel_missing, span=None, row_cls=None) -> str:
    body = []
    for r in ROWS:
        cls = f' class="{row_cls(r)}"' if row_cls and row_cls(r) else ""
        if r["rs"] is None:
            rs = span(r) if span else rs_missing * 3
        else:
            rs = "".join(rs_known(v) for v in r["rs"])
        ac = accel_missing if r["accel"] is None else accel_known(r)
        body.append(
            f'<tr{cls}><td class="mut">{r["n"]}</td>'
            f'<td class="l tk">{r["tk"]}</td>{align(r)}{state_cell(r)}{rs}{ac}</tr>'
        )
    return (
        '<div class="wrap"><table><thead><tr>'
        '<th style="width:28px">#</th><th class="l">Ticker</th><th class="c">Align</th>'
        '<th class="l">State</th><th>RS 1M</th><th>RS 3M</th><th>RS 6M</th><th>Accel</th>'
        "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
    )


def page(fn, title, sub, extra_css, body, note) -> None:
    (OUT / fn).write_text(
        f"<!doctype html><meta charset=\"utf-8\"><title>{title}</title>\n"
        f'<link rel="stylesheet" href="_shared.css">\n'
        f"<style>{extra_css}</style>\n"
        f"<h1>{title}</h1>\n<p class=\"sub\">{sub}</p>\n{body}\n"
        f'<p class="note">{note}</p>\n',
        encoding="utf-8",
    )


DASH = '<td class="mut">—</td>'
# measured 2026-08-22: --color-untested is 1.74:1 on the light page ground,
# under the 3:1 a meaning-carrying graphic needs. text-muted is 4.83:1 light /
# 6.33:1 dark, so the dashed slot is drawn in text-muted, not untested.
SLOT_CSS = (".slot{display:inline-block;width:18px;height:11px;vertical-align:-1px;"
            "border-bottom:1px dashed var(--color-text-muted)}")
SLOT = '<td><i class="slot" title="未测量"></i></td>'

page("screener_rs_missing_v0.html", "Screener · 现状（v0，对照组）",
     "行 3/6/8 没有 RS 读数。Align 那一格画了虚线圈说「未测量」；"
     "紧挨着的三个 RS 格写 —；Accel 的 null 也写 —；第 8 行「不在股票池」还是文字。",
     "", table(DASH, DASH),
     "<b>缺陷：</b>同一个事实（这只票没有 RS 读数）在相邻两列长着两张脸"
     "——虚线圈 vs <code>—</code>。而 <code>—</code> 同时又是 accel 的 null。约 30% 的行落在这里。")

page("screener_rs_missing_v1.html", "v1 · 虚线槽位",
     "方向：缺的读数占着它本该占的宽度，画成一条虚线底槽。"
     "Align 圈已经这么说了，数字列跟上，全表只有一种「未测量」的写法。",
     SLOT_CSS, table(SLOT, SLOT),
     "<b>说什么：</b>虚线 = 未测量，全表一种写法，和 Align 圈同源。"
     "<b>没解决：</b>三个 RS 列各画一次，同一句话说了三遍。")

page("screener_rs_missing_v2.html", "v2 · 三列合一",
     "方向：RS 缺就是整套 RS 缺（1M/3M/6M 是同一次计算的三个窗口）。"
     "三格塌成一格，横跨三列写一次原因。",
     ".span{text-align:left;color:var(--color-text-muted);font-size:11px;"
     "border-bottom:1px dashed var(--color-text-muted)}",
     table(DASH, DASH, span=lambda r: '<td colspan="3" class="span">RS 未测量</td>'),
     "<b>说什么：</b>说一遍比说三遍准。"
     "<b>代价：</b><code>colspan</code> 把那三列的数字对齐打断了"
     "——往下扫 RS 3M 一列时，视线要跨过一段横排文字。"
     "<b>没解决：</b>accel 的 <code>—</code> 原样留着。")

page("screener_rs_missing_v3.html", "v3 · 整行降级",
     "方向：没有 RS 的行不该和有读数的行争同一份注意力。"
     "整行压低不透明度，数字列全部留空。",
     "tr.dim td{opacity:.5}",
     table('<td></td>', '<td></td>', row_cls=lambda r: "dim" if r["rs"] is None else ""),
     "<b>说什么：</b>读不出来的行退到背景里。"
     "<b>代价：</b><b>空白 = 未测量 是个约定，页面上没说出口</b>"
     "——读者第一次看见只会觉得渲染坏了。"
     "而且降级用的是不透明度，<b>它同时压低了 ticker 和 state "
     "这两个明明测到了的读数</b>。")

# ── v4: v1 迭代一轮 —— 把 v2「说一遍」和 v3「行级事实」里能偷的偷过来，
#    但都不付它们的代价（colspan 打断对齐 / 不透明度对已测读数撒谎）。
LEGEND = ('<p class="legend"><i class="slot"></i>&nbsp;'
          '未测量 —— 这只票今晚没算出 RS，<b>不是 0，也不是低</b>。'
          '同一个虚线也用在 Align 圈上。</p>')
SLOT4 = ('<td><i class="slot" title="RS 未测量：这只票的 RS 今晚没算出来，'
         '不是 0 也不是低分"></i></td>')
ACC4 = '<td><i class="slot" title="rs_accel 未测量：它读的是同一份 RS"></i></td>'

page("screener_rs_missing_v4.html", "v4 · 虚线槽位 + 一行图例（胜出稿，v1 迭代）",
     "v1 拿下 11/12，扣的那一分在「读者第一次看见得自己学会这个约定」。"
     "v4 把约定写出来，并让 accel 也用同一个槽——于是 <code>—</code> 从这张表里彻底消失，"
     "不再身兼三职。三列各画一次是<b>故意</b>保留的：列对齐是这张表被扫的方式。",
     SLOT_CSS + ".legend{margin:10px 0 0;font-size:11px;color:var(--color-text-muted);"
     "display:flex;align-items:center;gap:2px;max-width:74ch;line-height:1.6}"
     ".legend b{color:var(--color-text-secondary);font-weight:600}",
     table(SLOT4, ACC4) + LEGEND,
     "<b>从 v2 偷的：</b>「RS 缺就是整套 RS 缺」这句话——但放进图例和 title，"
     "不放进表格，所以不欠 <code>colspan</code> 那笔对齐的债。<br>"
     "<b>从 v3 偷的：</b>「这是行级的事实」——但由 Align 那个虚线圈承担，"
     "它本来就在那儿；<b>不碰 ticker 和 state，那两个读数是测到的</b>。<br>"
     "<b>量过的：</b>虚线用 <code>--color-text-muted</code>，"
     "对页底 <b>4.83:1</b>（浅）/ <b>6.33:1</b>（深），过图形对象 3:1。"
     "原本想用的 <code>--color-untested</code> 在浅色页底只有 <b>1.74:1</b>，不及格。<br>"
     "<b>零新增颜色、零动效、零文案增量</b>（图例是一行读数说明，不是解释性长文）。")


print("built:", *sorted(p.name for p in OUT.glob("*.html")))
