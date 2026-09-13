#!/usr/bin/env python3
"""Visual-line layout for the recap samples: one static review page (issue × language × A/B) + A4 PDFs.

Usage (recap venv):
    ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.visual --sample

Design is the Visual line's, copied not redesigned: CSS verbatim in visual_assets/recap_visual.css;
components ported from their build_recap.py / build_recap_0911.py (drop line, conditions chart,
vote strip, board tables, bar panels, ledgers, statebar, metrics, book table, tell schematic).
Local additions only: CJK font fallback, the education topic cards, tell classes for the
schematics, print rules. No new colours — every addition uses the Visual CSS variables.

Content is not rewritten here: words come from content_<LANG>.json, numbers from pack.json and the
origin/main archives as of the issue date.

Delivery checks (all must pass, else the output is written as blocked_* and exit 1):
  page text of every issue × language × layout: gates.run_gates + constants.check_rules
  every PDF: the same gates on pdftotext + pages.check_pages
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from pipeline.content.recap import month_dir, pack_dir
from pipeline.content.recap.build_pack import csv_rows, show
from pipeline.content.recap.constants import check_rules
from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.pages import check_pages
from pipeline.content.recap.visual_figs import FIGS
from pipeline.content.recap.weeks import week_sessions
from pipeline.marketcal import is_trading_day

import datetime as dt

e = html.escape
ASSETS = Path(__file__).with_name("visual_assets")
FONT_DIR = Path.home() / ".venvs" / "fluxus-recap" / "fonts"
ISSUES = [("W37", "2026-W37"), ("09-11", "2026-09-11"), ("09-10", "2026-09-10"), ("09-09", "2026-09-09"), ("09-08", "2026-09-08")]
FONTS_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600'
              '&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">')

EXTRA_CSS = """
:root{
  --sans:"IBM Plex Sans","PingFang SC","Hiragino Sans GB",sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans","PingFang SC","Hiragino Sans GB",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,"PingFang SC","Hiragino Sans GB",monospace;
}
[hidden]{display:none!important}
.switches{display:flex;flex-wrap:wrap;gap:12px 18px;margin-top:22px}
.switches .switch{margin:0}
.edu-pick{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:0 0 14px}
@media(max-width:560px){.edu-pick{grid-template-columns:1fr}}
.edu-pick .card{border:1px solid var(--rule);padding:10px 12px;background:var(--sheet)}
.edu-pick .card.on{border:1.5px solid var(--ink)}
.edu-pick .k{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.edu-pick .card.on .k{color:var(--ink)}
.edu-pick b{display:block;font-size:13.5px;line-height:1.35;margin:3px 0 4px;color:var(--ink)}
.edu-pick .card.off b{color:var(--muted);font-weight:500}
.edu-pick p{margin:0;font-size:12px;line-height:1.5;color:var(--muted)}
.tell .ma{stroke:var(--accent)} .tell .ma2{stroke:var(--muted)}
.tell .evt{fill:none}
.tell .lvl{stroke:var(--accent);stroke-width:2}
.tell .guide{stroke:var(--rule);stroke-width:1.2;stroke-dasharray:4 4}
.tell .mark{fill:none;stroke:var(--muted);stroke-width:1.4}
.tell .lead{stroke:var(--muted);stroke-width:1}
.tell .zone-up{fill:var(--up);opacity:.07} .tell .zone-dn{fill:var(--dn);opacity:.07}
.tell .lab-acc{fill:var(--accent);font-weight:600}
table.idx.wk td:nth-child(n+2){white-space:nowrap}
.metrics.six{grid-template-columns:repeat(3,minmax(0,1fr))}
"""

PRINT_CSS = """
@page{size:A4;margin:15mm 14mm 16mm;
  @bottom-center{content:"FLUXUS CAPITAL · CONFIDENTIAL · " counter(page) " / " counter(pages);
    font-family:"IBM Plex Mono","Hiragino Sans GB",monospace;font-size:7pt;letter-spacing:.12em;color:var(--muted)}}
@media print{
  body{padding:0;background:var(--sheet)}
  .top,[data-layout="B"]{display:none!important}
  .sheet,.sheet.a{border:0;padding:0;margin:0;max-width:none;background:var(--sheet)}
  .sheet+.sheet .mast,.sheet+.sheet hr.r.ink{display:none}
  .folio{display:none}
  .sec{break-inside:avoid}
  .sec.edu{break-inside:auto}
  .tell,.edu-pick{break-inside:avoid}
  .hl-a{font-size:25px}
  .scroll{overflow:visible}
  .drop.thin{height:38px}
  .votes{grid-template-columns:repeat(6,1fr)}
  .prose{max-width:none}
}
"""

VL = {
    "EN": {"legend": ("counts for", "counts against", "inside its line", "not counted", "number = distance past each vote’s own line"),
           "units": {"ratio": "ratio", "names": "names", "points": "points", "warnings": "warnings", "": ""},
           "votes": "votes", "top3": "top 3 · bottom 3", "d1": "1 day", "w1": "1 week", "ll": "Leaders and Laggards",
           "rot_d": "Rotation · the session", "rot_w": "Rotation · the week", "board": "The Board",
           "b_votes": "Breadth votes", "b_cond": "Conditions", "b_led": "Led", "b_paid": "Paid",
           "pick_on": "A · sample default", "pick_off": "B · alternative",
           "schem": "Schematic — illustrates the concept, not price data.", "score": "Weekly Scorecard",
           "tape": "The Tape", "founders": "Founders Note", "sessions": "Session by session",
           "daily": "Daily Market Recap", "weekly": "Weekly Market Recap", "droparia": "SPX drop line, 21 sessions",
           "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
           "vlabels": {}},
    "ZH": {"legend": ("计入看多", "计入看空", "在线内", "未计入", "数字 = 离各自那条线的距离"),
           "units": {"ratio": "比值", "names": "只", "points": "点", "warnings": "条", "": ""},
           "votes": "票", "top3": "前 3 · 后 3", "d1": "1 日", "w1": "1 周", "ll": "领涨与落后",
           "rot_d": "轮动 · 当天", "rot_w": "轮动 · 本周", "board": "看板",
           "b_votes": "广度票板", "b_cond": "市场状况", "b_led": "领涨", "b_paid": "让位",
           "pick_on": "A · 样张默认", "pick_off": "B · 备选",
           "schem": "示意图——说明概念，不是真实价格。", "score": "周成绩单",
           "tape": "盘面", "founders": "Founders Note", "sessions": "逐日读数",
           "daily": "Daily Market Recap", "weekly": "Weekly Market Recap", "droparia": "SPX 掉落线，21 个交易日",
           "months": [f"{i}月" for i in range(1, 13)],
           "vlabels": {"5-day ratio": "5 日比", "10-day ratio": "10 日比", "Thrust": "推力", "Quarterly spread": "季度差",
                       "13%/34d spread": "13%/34 日差", "New highs vs lows": "新高对新低", "McClellan": "McClellan",
                       "% above 200-day": "站上 200 日线占比", "T2108 zone": "T2108 区间", "SPY warnings": "SPY 警示",
                       "QQQ warnings": "QQQ 警示", "Benchmark trend": "基准趋势"}},
}


# ------------------------------------------------------------------ formatting
def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct(x, dp=2):
    return "—" if x is None else f"{x * 100:+.{dp}f}%".replace("-", "−")


def cls(x):
    return "" if x is None else ("up" if x >= 0 else "dn")


def signed(v, unit):
    if v is None:
        return "—"
    return (f"{v:+.0f}" if unit in ("names", "warnings") else f"{v:+.2f}").replace("-", "−")


def sR(x):
    return "—" if x is None else f"{x:+.2f}R".replace("-", "−")


def rich(s):
    return re.sub(r"&lt;(/?)b&gt;", r"<\1b>", e(s or ""))


def sign_cls(s):
    return "" if not s else ("up" if s.strip().startswith("+") else "dn" if s.strip().startswith(("−", "-")) else "")


# ------------------------------------------------------------------ archive reads (as of D)
def spx_segment(D):
    rows = sorted({(r["date"], float(r["spx_close"])) for r in csv_rows("data/history/breadth_archive.csv")
                   if r["date"] <= D and fl(r.get("spx_close")) and is_trading_day(dt.date.fromisoformat(r["date"]))})
    seg = rows[-21:]
    assert seg[-1][0] == D and len(seg) == 21, (D, seg[-1])
    return seg


def drop_line(D):
    """Ported from build_recap_0911.py: 21-session SPX log drawdown, Chaikin-smoothed, arc-normalised."""
    seg = spx_segment(D)
    p0 = seg[0][1]
    pts = [(float(k), -math.log(p / p0) * 100.0) for k, (_, p) in enumerate(seg)]

    def chaikin(P, it=3):
        for _ in range(it):
            o = [P[0]]
            for a, c in zip(P, P[1:]):
                o.append((a[0] * .75 + c[0] * .25, a[1] * .75 + c[1] * .25))
                o.append((a[0] * .25 + c[0] * .75, a[1] * .25 + c[1] * .75))
            o.append(P[-1])
            P = o
        return P
    S = chaikin(pts)
    L = sum(math.dist(a, c) for a, c in zip(S, S[1:]))
    S = [(x * 1000 / L, y * 1000 / L) for x, y in S]
    arc = sum(math.dist(a, c) for a, c in zip(S, S[1:])) / 1000
    xs, ys = [p[0] for p in S], [p[1] for p in S]
    k = 1000 / (max(xs) - min(xs))
    P = [((x - min(xs)) * k, (y - min(ys)) * k) for x, y in S]
    H = (max(ys) - min(ys)) * k
    return {"d": "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in P), "h": H, "arc": arc, "d0": seg[0][0]}


_json_cache: dict = {}


def jshow(path):
    if path not in _json_cache:
        _json_cache[path] = json.loads(show(path))
    return _json_cache[path]


def cond_hist(D):
    return [h for h in jshow("data/output/breadth.json")["conditions"]["history"] if h["date"] <= D]


def verdict(D):
    return jshow("data/output/breadth_replay.json")["verdicts"][D]


def by_kind(D):
    out = defaultdict(list)
    for r in csv_rows("data/history/groups_archive.csv"):
        if r["date"] == D and fl(r["perf_1d"]) is not None and fl(r["perf_1w"]) is not None:
            out[r["kind"]].append(r)
    return out


# ------------------------------------------------------------------ components (ported)
from pipeline.content.recap.svg_attrs import presentational  # noqa: E402  (print renderers ignore page CSS on inline SVG)


def drop_svg(dl, stroke, klass, aria, pad=6):
    return presentational(f'<svg class="drop {klass}" viewBox="{-pad} {-pad} {1000 + 2 * pad} {dl["h"] + 2 * pad:.1f}" role="img" aria-label="{e(aria)}">'
                          f'<path style="stroke-width:{stroke}" d="{dl["d"]}"/></svg>')


def reg_line(dl, D, tag, suffix=""):
    return f'<p class="reg">1m · drop <span class="m">#{e(tag)}</span> · {dl["d0"]} → {D} · SPX · ∫ = {dl["arc"]:.3f} m{e(suffix)}</p>'


def cond_chart(cond, V):
    n = len(cond)
    W, base, top = 940, 190, 18
    bw = W / n
    o = [f'<svg class="chart" viewBox="0 0 1000 222" role="img" aria-label="Market conditions {cond[-1]["score"]}">']
    for v in (0, 50, 100):
        y = base - (v / 100) * (base - top)
        o.append(f'<line class="grid{" mid" if v == 50 else ""}" x1="0" x2="{W}" y1="{y:.1f}" y2="{y:.1f}"/><text class="ax" x="{W + 10}" y="{y + 4:.1f}">{v}</text>')
    lastm, lastx = None, -999
    for j, h in enumerate(cond):
        x = j * bw
        hh = (h["score"] / 100) * (base - top)
        o.append(f'<rect class="{"bar now" if j == n - 1 else "bar"}" x="{x + bw * 0.14:.2f}" y="{base - hh:.2f}" width="{max(bw * 0.72, 0.6):.2f}" height="{hh:.2f}"/>')
        m = h["date"][:7]
        if m != lastm:
            mon = V["months"][int(m[5:]) - 1]
            lab = f"{mon} {m[2:4]}" if (m[5:] == "01" or lastm is None) else mon
            if x - lastx >= 48:
                o.append(f'<text class="ax" x="{x:.1f}" y="216">{e(lab)}</text>')
                lastx = x
            lastm = m
    lx, ly = (n - 1) * bw + bw / 2, base - (cond[-1]["score"] / 100) * (base - top)
    o.append(f'<text class="nowlab" x="{lx - 8:.1f}" y="{ly - 8:.1f}" text-anchor="end">{cond[-1]["score"]}</text></svg>')
    return presentational("".join(o))


SIDE = {"bull": "for", "bear": "against", "neutral": "near"}


def vote_strip(verd, V, big=False):
    c = []
    for v in verd["vote_detail"]:
        if not v["measurable"]:
            g, num, note = "uncounted", "—", V["legend"][3]
        else:
            g, num, note = SIDE[v["side"]], signed(v["margin"], v["unit"]), V["units"].get(v["unit"], v["unit"])
        lab = V["vlabels"].get(v["label"], v["label"])
        # glyph wrapped in a div: a bare span as a grid item is stretched to the cell width by print renderers
        c.append(f'<div class="vote"><div><span class="g {g}" aria-hidden="true"></span></div><div class="vnum">{num}</div><div class="vunit">{e(note)}</div><div class="vlab">{e(lab)}</div></div>')
    return f'<div class="votes{" big" if big else ""}">{"".join(c)}</div>'


def legend(V):
    a, b, c, d, n = V["legend"]
    return (f'<div class="legend"><span><span class="g for"></span>{e(a)}</span><span><span class="g against"></span>{e(b)}</span>'
            f'<span><span class="g near"></span>{e(c)}</span><span><span class="g uncounted"></span>{e(d)}</span><span class="lg-note">{e(n)}</span></div>')


def tb(bk, kind, col, n=3):
    s = sorted(bk[kind], key=lambda r: fl(r[col]), reverse=True)
    return s[:n], s[-n:]


def board_table(bk, kind, title, V):
    def rows(lst, col):
        return "".join(f'<tr><td class="gname">{e(r["group"])}</td><td class="st">{e(r["state"])}</td><td class="n {cls(fl(r[col]))}">{pct(fl(r[col]))}</td></tr>' for r in lst)

    def block(lab, col):
        t, b = tb(bk, kind, col)
        return f'<div class="lcol"><div class="lhead">{e(lab)}</div><table class="lt">{rows(t, col)}<tr class="gap"><td colspan="3"></td></tr>{rows(b, col)}</table></div>'
    return f'<div class="lpanel"><h4>{e(title)}</h4><div class="lgrid">{block(V["d1"], "perf_1d")}{block(V["w1"], "perf_1w")}</div></div>'


def bars_panel(bk, kind, title, col, lab):
    top, bot = tb(bk, kind, col, 4)
    items = top + bot
    mx = max(abs(fl(r[col])) for r in items) or 1
    o = [f'<div class="bpanel"><h4>{e(title)} <span>{e(lab)}</span></h4>']
    for j, r in enumerate(items):
        v = fl(r[col])
        w = abs(v) / mx * 50
        if j == len(top):
            o.append('<div class="bsep"></div>')
        pos = "left:50%" if v >= 0 else "right:50%"
        o.append(f'<div class="brow"><div class="bname">{e(r["group"])}</div><div class="btrack"><span class="zero"></span><span class="bfill {"pos" if v >= 0 else "neg"}" style="{pos};width:{w:.2f}%"></span></div><div class="bval {cls(v)}">{pct(v, 1)}</div></div>')
    o.append("</div>")
    return "".join(o)


def ledger(rows):
    return '<div class="scroll"><table class="led">' + "".join(
        f'<tr><td class="t">{rich(a)}</td><td class="n {sign_cls(b)}">{rich(b)}</td><td>{rich(x)}</td></tr>' for a, b, x in rows) + "</table></div>"


def olist(items, klass):
    return f'<ol class="{klass}">' + "".join(f"<li>{rich(x)}</li>" for x in items) + "</ol>"


def statebar(cells, big=False):
    return f'<div class="statebar{" big" if big else ""}">' + "".join(f"<div><span>{e(a)}</span><b>{e(b)}</b></div>" for a, b in cells) + "</div>"


def table_idx(head, rows_html, right=(), extra=""):
    h = "".join(f"<th{' class=rn' if i in right else ''}>{e(x)}</th>" for i, x in enumerate(head))
    return f'<div class="scroll"><table class="idx {extra}"><thead><tr>{h}</tr></thead><tbody>{rows_html}</tbody></table></div>'


def edu_pick(c, V):
    cards = []
    for o in c["education"]["options"]:
        on = o["key"] == "A"
        cards.append(f'<div class="card {"on" if on else "off"}"><div class="k">{e(V["pick_on"] if on else V["pick_off"])}</div>'
                     f'<b>{e(o["title"])}</b><p>{e(o.get("why", ""))}</p></div>')
    return f'<div class="edu-pick">{"".join(cards)}</div>'


# ------------------------------------------------------------------ issue model
class Issue:
    def __init__(self, tag, label, sample):
        self.tag, self.label = tag, label
        self.weekly = label.startswith("20") and "-W" in label
        if self.weekly:
            self.D = week_sessions(label)[-1].isoformat()
            self.pdir = month_dir(self.D, sample) / f"pack_{label}"
        else:
            self.D = label
            self.pdir = pack_dir(label, sample)
        self.pack = json.loads((self.pdir / "pack.json").read_text())
        self.content = {lang: json.loads((self.pdir / f"content_{lang}.json").read_text()) for lang in ("EN", "ZH")}
        self.dl = drop_line(self.D)
        self.cond = cond_hist(self.D)
        assert self.cond[-1]["date"] == self.D
        self.verd = verdict(self.D)
        self.bk = by_kind(self.D)
        self.no = self.label.split("-")[-1] if self.weekly else self.D[5:].replace("-", "")

    # --- data cells
    def asset(self, tk):
        return self.pack["assets"]["rows"].get(tk)

    def chg(self, tk):
        a = self.asset(tk)
        return None if not a else (a["week_pct"] if self.weekly else a["change_pct"])

    def last(self, tk):
        a = self.asset(tk)
        return None if not a else (a["close_T"] if self.weekly else a["close"])

    def score(self):
        s = self.verd["score"]
        return f"{s:+d}" if s else "0"

    def state_cells(self, c):
        L = c["labels"]
        if self.weekly:
            fri = self.pack["days"]["rows"][-1]
            low = min(self.pack["days"]["rows"][1:], key=lambda r: r["score"] or 0)
            return [(f'SPY · {c["labels"]["week_index_cols"][2]}', pct(self.chg("SPY"))),
                    (L["state_votes"], f'{low["env"]} {low["score"]:+d} → {fri["env"]} {fri["score"] or 0:+d}'.replace("+0", "0")),
                    (L["state_conditions"], f'{low["conditions"]} → {fri["conditions"]}'),
                    (L["state_4pct"], f'{fri["up_4pct"]:.0f} / {fri["down_4pct"]:.0f}')]
        b = self.pack["breadth"]["T"]
        cT = self.pack["verdict"]["conditions_T"] or {}
        return [(L["state_votes"], f'{self.verd["env"]} {self.score()}'),
                (L["state_conditions"], f'{cT.get("score", "—")} / 100'),
                (L["state_4pct"], f'{b["up_4pct_stockbee"]:.0f} / {b["down_4pct_stockbee"]:.0f}'),
                (L["state_adv"], f'{b["net_advances"]:+,.0f}'.replace("-", "−"))]

    # --- tables
    def index_rows(self, c):
        rows = []
        for tk in ("SPY", "QQQ", "RSP", "DIA", "IWM"):
            a = self.asset(tk)
            if not a:
                continue
            ev, note = c["index_notes"].get(tk, ["", ""])
            if self.weekly:
                days = " ".join(f'{x["change_pct"] * 100:+.1f}'.replace("-", "−") for x in a["daily"])
                rows.append(f'<tr><td class="t">{tk}</td><td class="n">{a["close_T"]:,.2f}</td><td class="n {cls(a["week_pct"])}">{pct(a["week_pct"])}</td>'
                            f'<td class="n">{days}</td><td>{rich(ev)}</td><td>{rich(note)}</td></tr>')
            else:
                rows.append(f'<tr><td class="t">{tk}</td><td class="n">{a["close"]:,.2f}</td><td class="n {cls(a["change_pct"])}">{pct(a["change_pct"])}</td>'
                            f'<td class="n">{a["rel_volume"]:.2f}×</td><td>{rich(ev)}</td><td>{rich(note)}</td></tr>')
        for r in c.get("extra_index_rows", []):
            cells = (list(r) + [""] * 6)[:6]
            rows.append("<tr>" + "".join(f'<td class="{k}">{rich(v)}</td>' for k, v in zip(("t", "n", "n", "n", "", ""), cells)) + "</tr>")
        head = c["labels"]["week_index_cols"] if self.weekly else c["labels"]["index_cols"]
        return table_idx(head, "".join(rows), right=(1, 2, 3), extra="wk" if self.weekly else "")

    def tiles(self, c):
        t = []
        for tk in ("SPY", "QQQ", "RSP", "DIA", "IWM"):
            a = self.asset(tk)
            if not a:
                continue
            ev = c["index_notes"].get(tk, ["", ""])[0]
            t.append(f'<div class="bi"><div class="bi-t">{tk}</div><div class="bi-c {cls(self.chg(tk))}">{pct(self.chg(tk))}</div>'
                     f'<div class="bi-l">{self.last(tk):,.2f}</div><div class="bi-d">{rich(ev)}</div></div>')
        for r in c.get("extra_index_rows", []):
            t.append(f'<div class="bi"><div class="bi-t">{rich(r[0])}</div><div class="bi-c">{rich(r[2])}</div>'
                     f'<div class="bi-l">{rich(r[1])}</div><div class="bi-d">{rich(r[4])}</div></div>')
        return f'<div class="bigidx{" seven" if len(t) >= 6 else ""}">{"".join(t)}</div>'

    def days_table(self, c):
        rows = []
        for r in self.pack["days"]["rows"]:
            sc = f'{r["score"]:+d}' if r["score"] else "0"
            lab = r["date"][5:] + (c["labels"]["base_mark"] if r["is_base"] else "")
            rows.append(f'<tr><td class="t">{e(lab)}</td><td>{e(str(r["env"]))} {sc}</td><td class="n">{r["conditions"]}</td>'
                        f'<td class="n">{r["up_4pct"]:.0f} / {r["down_4pct"]:.0f}</td><td class="n">{r["net_advances"]:+,.0f}</td>'
                        f'<td class="n">{r["t2108"]:.1f}%</td><td class="n">{r["mcclellan_osc"]:+.1f}</td></tr>'.replace("+-", "−").replace("-", "−").replace("<td class=\"t\">−", "<td class=\"t\">-"))
        return table_idx(c["labels"]["days_cols"], "".join(rows), right=(2, 3, 4, 5, 6))

    def scorecard(self, c):
        cells = "".join(f'<div><span>{tk}</span><b class="{cls(self.chg(tk))}">{pct(self.chg(tk))}</b></div>' for tk in ("SPY", "QQQ", "RSP", "IWM"))
        return f'<div class="metrics">{cells}</div>'

    def weekly_k(self, c):
        wk, L = self.pack.get("weekly_k") or {}, c["labels"]
        u = wk.get("universe")
        if not u:
            return ""
        want = c.get("weekly_k_names") or []
        names = [n for tk in want for n in u["named"] if n["ticker"] == tk]
        rows = "".join(f'<tr><td class="t">{e(n["ticker"])}</td><td class="n {cls(n["perf_1w"])}">{pct(n["perf_1w"], 1)}</td>'
                       f'<td class="n {cls(n["vs_wk_ema10"])}">{pct(n["vs_wk_ema10"], 1)}</td><td class="n {cls(n["vs_wk_ema20"])}">{pct(n["vs_wk_ema20"], 1)}</td>'
                       f'<td>{e(L["yes"]) if n["three_weeks_tight"] else ""}</td><td class="n">{int(n["rs_rating"]) if n["rs_rating"] is not None else "—"}</td></tr>' for n in names)
        summ = L["wk_summary"].format(n3=u["three_weeks_tight_tradeable"], nt=u["n_tradeable"], p10=u["pct_tradeable_above_wk_ema10"])
        th = wk.get("themes_rs_0_1w")
        tl = ""
        if th:
            f = lambda xs: " · ".join(f'{t["group"]} {pct(t["rs_0_1w"], 1)}' for t in xs)
            tl = f'<p class="prose"><b>{e(L["rs01_top"])}</b> {e(f(th["top"]))}<br><b>{e(L["rs01_bottom"])}</b> {e(f(th["bottom"]))}</p>'
        return (table_idx(L["wk_cols"], rows, right=(1, 2, 3, 5)) + f'<p class="schem">{e(summ)}</p>' + tl
                + f'<p class="prose">{rich(c.get("weekly_k_line", ""))}</p>')

    def book(self, c):
        b, L = self.pack.get("book") or {}, c["labels"]
        if "open_names" not in b:
            return ""
        cells = [(L["m_return"], f'{b["return_pct"]:+.2f}%'.replace("-", "−")), (L["m_cash"], f'{b["cash_pct"]:.1f}%'),
                 (L["m_open"], str(b["open_names"])), (L["m_closed"], str(b["closed_trades"])),
                 (L["m_openR"], sR(b["open_R_total"])), (L["m_realR"], sR(b["realized_R_period"]))]
        m = '<div class="metrics six">' + "".join(f"<div><span>{e(a)}</span><b>{e(x)}</b></div>" for a, x in cells) + "</div>"
        head = "".join(f"<th{' class=rn' if i == 3 else ''}>{e(h)}</th>" for i, h in enumerate(L["pos_cols"]))
        rows = "".join(f'<tr><td class="t">{e(p["ticker"])}</td><td>{e(L["long"] if p["direction"] == "long" else L["short"])}</td>'
                       f'<td>{e(p["entry_date"])}</td><td class="n {cls(p["open_R"])}">{sR(p["open_R"])}</td></tr>' for p in b["positions"])
        return m + f'<div class="scroll"><table class="book"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div><p class="prose">{rich(c["portfolio_note"])}</p>'

    def board_rows(self, c):
        V, L = VL[c["lang"]], c["labels"]
        col = "perf_1w" if self.weekly else "perf_1d"
        th = sorted(self.bk["theme"], key=lambda r: fl(r[col]), reverse=True)
        rows = [(V["b_votes"], f'{self.verd["env"]} {self.score()}', ""),
                (V["b_cond"], f'{self.cond[-1]["score"]} / 100', "")]
        rows += [(tk, pct(self.chg(tk)), cls(self.chg(tk))) for tk in ("SPY", "QQQ", "RSP")]
        rows += [(V["b_led"], f'{th[0]["group"]} {pct(fl(th[0][col]), 1)}', ""), (V["b_paid"], f'{th[-1]["group"]} {pct(fl(th[-1][col]), 1)}', "")]
        return "".join(f'<div class="brd-row"><span>{e(a)}</span><b class="{k}">{e(b)}</b></div>' for a, b, k in rows)

    # --- sheets
    def mast(self, V):
        return f'<div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>{V["weekly" if self.weekly else "daily"]} · No. {e(self.no)}</span></div><hr class="r ink">'

    def folio(self, V, n, total, b=False):
        fm = f'<span class="fl">{drop_svg(self.dl, 2, "fmark", "", 4)}</span>' if b else ""
        return f'<div class="folio{" b" if b else ""}">{fm}<span>Fluxus Capital · {V["weekly" if self.weekly else "daily"]}</span><span>{n} / {total}</span></div>'

    def layout_a(self, lang):
        c, V = self.content[lang], VL[lang]
        L = c["labels"]
        fn = (f'<section class="sec note-blk"><h3>{e(V["founders"])}</h3><p class="prose">{rich(c["founders_note"])}</p></section>' if c.get("founders_note") else "")
        s1 = (f'<article class="sheet a">{self.mast(V)}{drop_svg(self.dl, 2.5, "thin", V["droparia"])}{reg_line(self.dl, self.D, self.no)}'
              f'<h2 class="hl-a">{e(c["title"])}</h2><p class="byline">{e(c["subtitle"])}</p>'
              f'<section class="sec"><h3>{e(L["big_picture"])}</h3><p class="prose">{rich(c["big_picture"])}</p></section>'
              f'<section class="sec"><h3>{e(L["index_action"])}</h3>{self.index_rows(c)}</section>'
              + (f'<section class="sec"><h3>{e(V["score"])}</h3>{self.scorecard(c)}</section>' if self.weekly else "")
              + f'{self.folio(V, 1, 4)}</article>')
        s2 = (f'<article class="sheet a">{self.mast(V)}'
              f'<section class="sec first"><h3>{e(L["market_state"])}</h3>{statebar(self.state_cells(c))}'
              f'<div class="state-row" style="margin-top:14px"><span class="env">{e(self.verd["env"])}</span><span class="score">{self.score()}<small> / {len(self.verd["vote_detail"])} {e(V["votes"])}</small></span></div>'
              f'{vote_strip(self.verd, V)}{legend(V)}<p class="prose" style="margin-top:12px">{rich(c.get("state_line", ""))}</p></section>'
              + (f'<section class="sec"><h3>{e(V["sessions"])}</h3>{self.days_table(c)}</section>' if self.weekly else "")
              + f'<section class="sec"><h3>{e(L["conditions"])} <span class="h3n">{self.cond[-1]["score"]} / 100</span></h3>{cond_chart(self.cond, V)}</section>'
              f'{fn}<section class="sec"><h3>{e(V["ll"])} <span class="h3n">{e(V["top3"])}</span></h3>'
              f'<div class="lwrap">{board_table(self.bk, "industry", L["industries"], V)}{board_table(self.bk, "theme", L["themes"], V)}</div></section>'
              f'{self.folio(V, 2, 4)}</article>')
        wk = self.weekly_k(c) if self.weekly else ""
        s3 = (f'<article class="sheet a">{self.mast(V)}'
              f'<section class="sec first"><h3>{e(L["working"])}</h3>{ledger(c["led"])}</section>'
              f'<section class="sec"><h3>{e(L["laggards"])}</h3>{ledger(c["lagged"])}</section>'
              + (f'<section class="sec"><h3>{e(L["weekly_k"])}</h3>{wk}</section>' if wk else "")
              + (f'<section class="sec"><h3>{e(L["sentiment"])}</h3><p class="prose">{rich(c["sentiment"])}</p></section>' if c.get("sentiment") else "")
              + f'<section class="sec"><h3>{e(L["tomorrow"])}</h3>{olist(c["tomorrow"], "ol-a")}</section>'
              f'<section class="sec"><h3>{e(L["rules"])}</h3>{olist(c["rules"], "ol-a")}</section>'
              f'{self.folio(V, 3, 4)}</article>')
        edu = c["education"]
        book = self.book(c)
        s4 = (f'<article class="sheet a">{self.mast(V)}'
              f'<section class="sec first edu"><h3>{e(L["education"])} <span class="h3n">{e(edu["title"])}</span></h3>{edu_pick(c, V)}'
              f'<p class="prose">{rich(edu["body"])}</p>{FIGS[edu["figure"]](lang)}<p class="schem">{e(V["schem"])}</p></section>'
              + (f'<section class="sec"><h3>{e(L["portfolio"])}</h3>{book}</section>' if book else "")
              + f'{self.folio(V, 4, 4)}</article>')
        return s1 + s2 + s3 + s4

    def layout_b(self, lang):
        c, V = self.content[lang], VL[lang]
        L = c["labels"]
        d = dt.date.fromisoformat(self.D)
        if lang == "EN":
            when = (f'Week {self.label.split("W")[-1]} · {d:%B} {week_sessions(self.label)[0].day}–{d.day} · {d.year}' if self.weekly
                    else f'{d:%A} · {d:%B} {d.day} · {d.year}')
        else:
            wd = "一二三四五六日"[d.weekday()]
            when = (f'{d.year} 年第 {self.label.split("W")[-1]} 周 · {d.month} 月 {week_sessions(self.label)[0].day}–{d.day} 日' if self.weekly
                    else f'{d.year} 年 {d.month} 月 {d.day} 日 · 周{wd}')
        head = re.split(r"\s+—\s+|——", c["title"], maxsplit=1)
        hl = "<br>".join(e(x) for x in head)
        cover = (f'<article class="sheet b cover"><div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>{e(when)}</span></div>'
                 f'<div class="hero">{drop_svg(self.dl, 7, "hero", V["droparia"])}</div>{reg_line(self.dl, self.D, self.no)}<hr class="r ink">'
                 f'<h2 class="hl-b">{hl}</h2><div class="cover-grid"><p class="prose lead">{rich(c["big_picture"])}</p>'
                 f'<aside class="board"><div class="brd-h">{e(V["board"])}</div>{self.board_rows(c)}</aside></div>{self.folio(V, 1, 4, True)}</article>')
        s2 = (f'<article class="sheet b"><div class="kicker">{e(V["tape"])}</div><h3 class="hb">{e(L["index_action"])}</h3>{self.tiles(c)}'
              + (f'<div class="kicker sp">{e(V["score"])}</div>{self.scorecard(c)}' if self.weekly else "")
              + f'<div class="kicker sp">{e(L["market_state"])}</div>{statebar(self.state_cells(c), big=True)}'
              f'<div class="state-b" style="margin-top:16px"><span class="env-b">{e(self.verd["env"])}</span><span class="score-b">{self.score()}<small>/ {len(self.verd["vote_detail"])}</small></span></div>'
              f'{vote_strip(self.verd, V, big=True)}{legend(V)}<p class="prose" style="margin-top:12px">{rich(c.get("state_line", ""))}</p>'
              + (f'<div class="kicker sp">{e(V["sessions"])}</div>{self.days_table(c)}' if self.weekly else "")
              + f'<div class="kicker sp">{e(L["conditions"])} · <b>{self.cond[-1]["score"]} / 100</b></div>{cond_chart(self.cond, V)}{self.folio(V, 2, 4, True)}</article>')
        wk = self.weekly_k(c) if self.weekly else ""
        s3 = (f'<article class="sheet b"><div class="split-b"><div><div class="kicker">{e(L["working"])}</div>{ledger(c["led"])}</div>'
              f'<div><div class="kicker">{e(L["laggards"])}</div>{ledger(c["lagged"])}</div></div>'
              + (f'<div class="kicker sp">{e(L["sentiment"])}</div><p class="prose">{rich(c["sentiment"])}</p>' if c.get("sentiment") else "")
              + f'<div class="kicker sp">{e(V["rot_d"])}</div><div class="bars2">{bars_panel(self.bk, "industry", L["industries"], "perf_1d", V["d1"])}{bars_panel(self.bk, "theme", L["themes"], "perf_1d", V["d1"])}</div>'
              f'<div class="kicker sp">{e(V["rot_w"])}</div><div class="bars2">{bars_panel(self.bk, "industry", L["industries"], "perf_1w", V["w1"])}{bars_panel(self.bk, "theme", L["themes"], "perf_1w", V["w1"])}</div>'
              + (f'<div class="kicker sp">{e(L["weekly_k"])}</div>{wk}' if wk else "")
              + f'{self.folio(V, 3, 4, True)}</article>')
        edu = c["education"]
        book = self.book(c)
        fn = (f'<div class="kicker">{e(V["founders"])}</div><p class="prose">{rich(c["founders_note"])}</p><div class="kicker sp">{e(L["tomorrow"])}</div>'
              if c.get("founders_note") else f'<div class="kicker">{e(L["tomorrow"])}</div>')
        s4 = (f'<article class="sheet b"><div class="pull edu"><div class="kicker">{e(L["education"])}</div><h3 class="hb big">{e(edu["title"])}</h3>'
              f'{edu_pick(c, V)}<p class="prose lead">{rich(edu["body"])}</p></div>'
              f'{FIGS[edu["figure"]](lang)}<p class="schem">{e(V["schem"])}</p>'
              f'<div class="split-b" style="margin-top:34px"><div>{fn}{olist(c["tomorrow"], "ol-b")}'
              + (f'<div class="kicker sp">{e(L["portfolio"])}</div>{book}' if book else "")
              + f'</div><div><div class="kicker">{e(L["rules"])}</div>{olist(c["rules"], "ol-b rules")}</div></div>{self.folio(V, 4, 4, True)}</article>')
        return cover + s2 + s3 + s4


# ------------------------------------------------------------------ page + checks
def css_bundle(for_pdf=False):
    base = (ASSETS / "recap_visual.css").read_text()
    fonts = ""
    if for_pdf:
        faces = []
        for f in sorted(FONT_DIR.glob("IBMPlex*-*.woff")):  # Fontsource latin WOFF; CJK falls back to Hiragino
            fam, wt = f.stem.rsplit("-", 1)
            family = {"IBMPlexSans": "IBM Plex Sans", "IBMPlexSansCondensed": "IBM Plex Sans Condensed", "IBMPlexMono": "IBM Plex Mono"}[fam]
            faces.append(f'@font-face{{font-family:"{family}";font-weight:{wt};src:url("{f.as_uri()}")}}')
        if not faces:
            raise SystemExit(f"no IBM Plex fonts in {FONT_DIR} — PDFs must not fetch fonts at render time")
        fonts = "\n".join(faces) + "\n:root{--sans:\"IBM Plex Sans\",\"Hiragino Sans GB\",\"Heiti SC\",sans-serif;" \
            "--cond:\"IBM Plex Sans Condensed\",\"IBM Plex Sans\",\"Hiragino Sans GB\",\"Heiti SC\",sans-serif;" \
            "--mono:\"IBM Plex Mono\",Menlo,\"Hiragino Sans GB\",monospace}\n"
    return base + EXTRA_CSS + (fonts if for_pdf else "") + PRINT_CSS


def html_text(fragment: str) -> str:
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</(p|div|li|tr|h\d|section|article)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s)


JS = """
(function(){
  var st={issue:'W37',lang:'ZH',layout:'A'};
  try{var s=JSON.parse(localStorage.getItem('fluxusRecapSamplesW37')||'{}');for(var k in st){if(s[k])st[k]=s[k];}}catch(e){}
  var blocks=document.querySelectorAll('.variant'), btns=document.querySelectorAll('[data-set]');
  function render(){
    blocks.forEach(function(b){ b.hidden=!(b.getAttribute('data-issue')===st.issue&&b.getAttribute('data-lang')===st.lang&&b.getAttribute('data-layout')===st.layout); });
    btns.forEach(function(x){ x.setAttribute('aria-pressed', st[x.getAttribute('data-set')]===x.getAttribute('data-val')?'true':'false'); });
    document.documentElement.lang = st.lang==='ZH'?'zh-Hans':'en';
    try{localStorage.setItem('fluxusRecapSamplesW37', JSON.stringify(st));}catch(e){}
  }
  btns.forEach(function(x){ x.addEventListener('click',function(){ st[x.getAttribute('data-set')]=x.getAttribute('data-val'); render(); }); });
  render();
})();
"""


def header():
    def group(name, aria, opts, default):
        return (f'<div class="switch" role="group" aria-label="{e(aria)}">' + "".join(
            f'<button type="button" data-set="{name}" data-val="{v}" aria-pressed="{"true" if v == default else "false"}">{e(t)}</button>' for v, t in opts) + "</div>")
    return ('<header class="top"><p class="eyebrow">Fluxus Capital · Market Recap · 样张 · W37</p>'
            '<h1>复盘样张 · Visual 版式</h1>'
            '<p class="lede">五期内容不变，换成 Visual 线 9/11 周刊的视觉系统。A 登记体、B 掉落体，中英各一套；教育段加 A/B 选题，样张默认 A。</p>'
            '<div class="switches">'
            + group("issue", "期数", [(t, t) for t, _ in ISSUES], "W37")
            + group("lang", "语言", [("ZH", "中"), ("EN", "EN")], "ZH")
            + group("layout", "排版", [("A", "A · 登记体"), ("B", "B · 掉落体")], "A")
            + "</div></header>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--no-pdf", action="store_true", help="build and check the page only")
    a = ap.parse_args(argv)
    t0 = time.time()
    issues = [Issue(tag, label, a.sample) for tag, label in ISSUES]
    out = month_dir(issues[1].D, a.sample) / "visual"
    out.mkdir(parents=True, exist_ok=True)
    head = header()
    variants, report, status = [], {"page": {}, "pdf": {}}, 0
    for iss in issues:
        for lang in ("ZH", "EN"):
            bad = check_rules(iss.content[lang].get("rules"), lang, iss.D)
            for layout in ("A", "B"):
                body = iss.layout_a(lang) if layout == "A" else iss.layout_b(lang)
                default = iss.tag == "W37" and lang == "ZH" and layout == "A"
                variants.append(f'<div class="variant" data-issue="{iss.tag}" data-lang="{lang}" data-layout="{layout}"'
                                f'{"" if default else " hidden"}><div id="v-{iss.tag}-{lang}-{layout}">{body}</div></div>')
                g = run_gates(html_text(head + body))
                ok = g["ok"] and not bad
                report["page"][f"{iss.tag}/{lang}/{layout}"] = {"ok": ok, "banned": len(g["banned"]), "leadership_zh": g["leadership_zh"],
                                                                "money_shares": len(g["money_shares"]), "voice": len(g["voice"]), "rules": bad}
                if not ok:
                    status = 1
                    print(f"PAGE BLOCKED {iss.tag}/{lang}/{layout}: {bad or ''} " + "; ".join(f'{h["gate_rule"]}:{h["match"]!r}' for h in g["banned"] + g["money_shares"] + g["voice"]), file=sys.stderr)
    page = (f'<title>Fluxus Recap Samples W37</title>\n{FONTS_LINK}\n<style>{css_bundle()}</style>\n{head}\n'
            + "\n".join(variants) + f"\n<script>{JS}</script>\n")
    target = out / ("recap_samples.html" if status == 0 else "blocked_recap_samples.html")
    target.write_text(page)
    print(f"{'PAGE' if status == 0 else 'BLOCKED PAGE'} {target} · {len(page.encode()) / 1024:.0f} KB · {time.time() - t0:.1f}s")

    if a.no_pdf:
        (out / "visual_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
        return status
    from weasyprint import HTML
    pdf_css = css_bundle(for_pdf=True)
    blocked_dir = out / "_blocked"
    for iss in issues:
        for lang in ("EN", "ZH"):
            t1 = time.time()
            doc = (f'<!doctype html><html lang="{"zh-Hans" if lang == "ZH" else "en"}"><head><meta charset="utf-8"><title>{e(iss.content[lang]["title"])}</title>'
                   f'<style>{pdf_css}</style></head><body>{iss.layout_a(lang)}</body></html>')
            final = out / f"Market_Recap_{iss.label}_{lang}.pdf"
            tmp = out / f".partial_{iss.label}_{lang}.pdf"
            HTML(string=doc, base_url=str(out)).write_pdf(tmp)
            text = subprocess.run(["pdftotext", "-layout", str(tmp), "-"], capture_output=True, text=True, check=True).stdout
            g, pg = run_gates(text), check_pages(text)
            bad = check_rules(iss.content[lang].get("rules"), lang, iss.D)
            ok = g["ok"] and pg["ok"] and not bad
            report["pdf"][f"{iss.label}/{lang}"] = {"ok": ok, "pages": pg["pages"], "body_lines": pg["body_lines"], "thin": pg["thin_pages"],
                                                     "banned": len(g["banned"]), "voice": len(g["voice"]), "money": len(g["money_shares"]),
                                                     "leadership_zh": g["leadership_zh"], "rules": bad, "seconds": round(time.time() - t1, 1)}
            if ok:
                shutil.move(tmp, final)
                subprocess.run(["pdftoppm", "-r", "50", "-png", str(final), str(out / f"_preview_{iss.label}_{lang}")], check=False)
                print(f"DELIVERED {final} · pages {pg['pages']} {pg['body_lines']} · {time.time() - t1:.1f}s")
            else:
                status = 1
                blocked_dir.mkdir(exist_ok=True)
                if final.exists():
                    shutil.move(final, blocked_dir / f"previous_{final.name}")
                shutil.move(tmp, blocked_dir / final.name)
                print(f"PDF BLOCKED {final.name}: thin={pg['thin_pages']} {pg['body_lines']} banned={len(g['banned'])} voice={len(g['voice'])} "
                      f"money={len(g['money_shares'])} rules={bad} " + "; ".join(f'{h["gate_rule"]}:{h["match"]!r}' for h in g["banned"] + g["money_shares"] + g["voice"]), file=sys.stderr)
    (out / "visual_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main())
