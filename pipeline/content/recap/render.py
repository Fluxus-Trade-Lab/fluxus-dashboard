#!/usr/bin/env python3
"""content_<LANG>.json + pack.json → HTML → PDF, then delivery checks.

Usage (needs the recap venv for weasyprint/matplotlib):
    ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.render --date 2026-09-11 --sample
    ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.render --week 2026-W37 --sample

Division of labour:
  pack.json      numbers — rendered straight from the archives so prose cannot mistype them.
  content_*.json words per language (ZH is a rewrite, not a translation layer).
  constants.py   THE RULES — Andy's seven, fixed text; content files may not supply rules.

Reader page carries reader content only (skill 裁决 09-06「内部规则不上成品页」): no source
footnotes, no "left blank" notices, no topic menus. Founders Note absent or GAS unreachable
→ that section is simply not there (Andy 2026-09-13); a failed GAS pull never blocks a PDF.

A PDF is DELIVERED only if pdftotext of it passes
  gates.run_gates   (banned names, 「领导力」, dollar amounts / share counts, "Andy", first person: all 0)
  pages.check_pages (no page with fewer than 3 body lines).
Otherwise it is kept as blocked_*.pdf in the pack directory and the process exits 1; a
previously delivered file of the same name is moved aside so a stale PDF never looks current.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from pipeline.content.recap import month_dir, pack_dir
from pipeline.content.recap.constants import check_rules
from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.pages import check_pages
from pipeline.content.recap.weeks import week_sessions

e = html.escape
TONE = {"up": "#16a34a", "down": "#dc2626", "range": "#2563eb"}
DOTS = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#7c3aed", "#6b7280"]


# ------------------------------------------------------------------ formatting
def pct(x, dp=2):
    return "—" if x is None else f"{x * 100:+.{dp}f}%".replace("-", "−")


def num(x, dp=2):
    return "—" if x is None else f"{x:,.{dp}f}"


def signed(x, dp=0):
    return "—" if x is None else f"{x:+,.{dp}f}".replace("-", "−")


def above20(x):
    return "—" if x is None else f"{x:.1f}%"


def cls(x):
    return "" if x is None else ("up" if x >= 0 else "dn")


def sR(x):
    return "—" if x is None else f"{x:+.2f}R".replace("-", "−")


def rich(s: str) -> str:
    """Content strings may carry <b> only; everything else is escaped."""
    return re.sub(r"&lt;(/?)b&gt;", r"<\1b>", e(s or ""))


# ------------------------------------------------------------------ shared blocks
def section(i: int, title: str, body: str, extra_cls: str = "") -> str:
    return (f'<section class="sec {extra_cls}"><h2><span class="dot" style="background:{DOTS[i % len(DOTS)]}"></span>'
            f'{e(title)}</h2>{body}</section>')


def extra_rows(c: dict, ncols: int) -> str:
    out = []
    for r in c.get("extra_index_rows", []):
        cells = list(r) + [""] * (ncols - len(r))
        out.append('<tr class="ext">' + "".join(f"<td>{rich(v)}</td>" for v in cells[:ncols]) + "</tr>")
    return "".join(out)


def grid(head: list[str], rows_html: str, right: set[int], extra="") -> str:
    h = "".join(f"<th{' class=rn' if i in right else ''}>{e(x)}</th>" for i, x in enumerate(head))
    return f'<div class="code"><table class="grid {extra}"><thead><tr>{h}</tr></thead><tbody>{rows_html}</tbody></table></div>'


def conditions_svg(series: list, caption: str) -> str:
    n = len(series)
    W, base, top = 940, 150, 12
    bw = W / n
    o = ['<svg class="cond" viewBox="0 0 1000 170" role="img">']
    for val in (0, 50, 100):
        y = base - val / 100 * (base - top)
        o.append(f'<line x1="0" x2="{W}" y1="{y:.1f}" y2="{y:.1f}" class="g{" mid" if val == 50 else ""}"/>'
                 f'<text x="{W + 8}" y="{y + 4:.1f}" class="ax">{val}</text>')
    for j, v in enumerate(series):
        h = v / 100 * (base - top)
        o.append(f'<rect x="{j * bw + bw * .15:.1f}" y="{base - h:.1f}" width="{bw * .7:.1f}" height="{h:.1f}" class="{"now" if j == n - 1 else "bar"}"/>')
    o.append(f'<text x="{W - 4}" y="{base - series[-1] / 100 * (base - top) - 6:.1f}" text-anchor="end" class="nl">{series[-1]}</text>')
    o.append(f'<text x="0" y="166" class="ax">{e(caption.format(n=n))}</text></svg>')
    return "".join(o)


def groups_board(pack: dict, L: dict, main: str, alt: str) -> str:
    def panel(kind, title):
        g = pack["groups"][kind]
        items = g["top"][:5] + g["bottom"][-5:]
        mx = max(abs(x[main] or 0) for x in items) or 1
        rows = []
        for i, x in enumerate(items):
            if i == 5:
                rows.append('<div class="sep"></div>')
            v = x[main] or 0
            w = abs(v) / mx * 50
            side = f"left:50%;width:{w:.1f}%" if v >= 0 else f"right:50%;width:{w:.1f}%"
            shift = "" if x["state_P"] in (None, x["state"]) else f' <em>{e(x["state_P"])}→{e(x["state"])}</em>'
            rows.append(f'<div class="br"><div class="bn">{e(x["group"])}{shift}</div>'
                        f'<div class="bt"><span class="z"></span><span class="bf {cls(v)}" style="{side}"></span></div>'
                        f'<div class="bv {cls(v)}">{pct(x[main], 1)}</div><div class="bw">{pct(x[alt], 1)}</div></div>')
        return f'<div class="bp"><h3>{e(title)} <small>{e(L["board_cols"])} · n={g["n"]}</small></h3>' + "".join(rows) + "</div>"
    return f'<div class="board">{panel("industry", L["industries"])}{panel("theme", L["themes"])}</div>'


def ledger(rows: list) -> str:
    return '<div class="code"><table class="led">' + "".join(
        f'<tr><td class="t">{rich(a)}</td><td class="n {("up" if b.startswith("+") else "dn") if b else ""}">{rich(b)}</td><td>{rich(x)}</td></tr>'
        for a, b, x in rows) + "</table></div>"


def olist(items) -> str:
    return '<ol class="nl">' + "".join(f"<li>{rich(x)}</li>" for x in items) + "</ol>"


def founders(c: dict) -> str:
    fn = c.get("founders_note")
    return f'<div class="note"><span class="k">FOUNDERS NOTE</span>{rich(fn)}</div>' if fn else ""


def book_block(pack: dict, c: dict) -> str:
    b, L = pack.get("book") or {}, c["labels"]
    if "open_names" not in b:
        return ""
    cells = [(L["m_return"], f'{b["return_pct"]:+.2f}%'.replace("-", "−") if "return_pct" in b else "—"),
             (L["m_cash"], f'{b["cash_pct"]:.1f}%' if "cash_pct" in b else "—"),
             (L["m_open"], str(b["open_names"])), (L["m_closed"], str(b["closed_trades"])),
             (L["m_openR"], sR(b["open_R_total"])), (L["m_realR"], sR(b["realized_R_period"]))]
    bar = '<div class="metrics">' + "".join(f"<div><span>{e(a)}</span><b>{e(x)}</b></div>" for a, x in cells) + "</div>"
    pos = "".join(f'<tr><td class="t">{e(p["ticker"])}</td><td>{e(L["long"] if p["direction"] == "long" else L["short"])}</td>'
                  f'<td>{e(p["entry_date"])}</td><td class="n {cls(p["open_R"])}">{sR(p["open_R"])}</td></tr>'
                  for p in b["positions"])
    return bar + grid(L["pos_cols"], pos, {3}, "pos") + f'<p class="one">{rich(c["portfolio_note"])}</p>'


# ------------------------------------------------------------------ daily blocks
def index_table(pack: dict, c: dict) -> str:
    rows = []
    for tk in ("SPY", "QQQ", "RSP", "DIA", "IWM"):
        a = pack["assets"]["rows"].get(tk)
        if not a:
            continue
        ev, key = c["index_notes"].get(tk, ["", ""])
        rows.append(f'<tr><td class="t">{tk}</td><td class="n">{num(a["close"])}</td>'
                    f'<td class="n {cls(a["change_pct"])}">{pct(a["change_pct"])}</td>'
                    f'<td class="n">{num(a["rel_volume"])}×</td><td>{rich(ev)}</td><td>{rich(key)}</td></tr>')
    return grid(c["labels"]["index_cols"], "".join(rows) + extra_rows(c, 6), {1, 2, 3})


def state_strip(pack: dict, c: dict) -> str:
    v, L = pack["verdict"], c["labels"]
    T, P = v["T"], v["P"] or {}
    cT, cP = v.get("conditions_T") or {}, v.get("conditions_P") or {}
    b, bp = pack["breadth"]["T"], pack["breadth"]["P"] or {}
    sc = lambda x: "0" if not x else f"{x:+d}"
    cells = [
        (L["state_votes"], f'{T["env"]} {sc(T["score"])}', f'{L["prev"]} {P.get("env", "—")} {sc(P.get("score"))}'),
        (L["state_conditions"], f'{cT.get("score", "—")} / 100', f'{L["prev"]} {cP.get("score", "—")}'),
        (L["state_4pct"], f'{b["up_4pct_stockbee"]:.0f} / {b["down_4pct_stockbee"]:.0f}',
         f'{L["prev"]} {bp.get("up_4pct_stockbee") or 0:.0f} / {bp.get("down_4pct_stockbee") or 0:.0f}'),
        (L["state_adv"], signed(b["net_advances"]), f'{L["prev"]} {signed(bp.get("net_advances"))}'),
        # S&P 500-bound %>20d is NULL in the archive before 2026-09-10 (METRIC_SOURCES) → whole-pool T2108
        ((L["state_sp20"], above20(b["pct_above_20sma_sp500"]), f'{L["prev"]} {above20(bp.get("pct_above_20sma_sp500"))}')
         if b.get("pct_above_20sma_sp500") is not None and bp.get("pct_above_20sma_sp500") is not None
         else (L["state_t2108"], above20(b["t2108"]), f'{L["prev"]} {above20(bp.get("t2108"))}')),
        (L["state_mcc"], signed(b["mcclellan_osc"], 1), f'{L["prev"]} {signed(bp.get("mcclellan_osc"), 1)}'),
    ]
    inner = "".join(f'<div><span>{e(a)}</span><b>{e(x)}</b><i>{e(y)}</i></div>' for a, x, y in cells)
    return f'<div class="strip">{inner}</div><p class="one">{rich(c.get("state_line", ""))}</p>'


# ------------------------------------------------------------------ weekly blocks
def week_index_table(pack: dict, c: dict) -> str:
    rows = []
    for tk in ("SPY", "QQQ", "RSP", "DIA", "IWM"):
        a = pack["assets"]["rows"].get(tk)
        if not a:
            continue
        days = " ".join(f'{x["change_pct"] * 100:+.1f}'.replace("-", "−") for x in a["daily"])
        note = c["index_notes"].get(tk, ["", ""])
        rows.append(f'<tr><td class="t">{tk}</td><td class="n">{num(a["close_T"])}</td>'
                    f'<td class="n {cls(a["week_pct"])}">{pct(a["week_pct"])}</td><td class="n">{days}</td>'
                    f'<td>{rich(note[0])}</td><td>{rich(note[1])}</td></tr>')
    return grid(c["labels"]["week_index_cols"], "".join(rows) + extra_rows(c, 6), {1, 2, 3})


def days_table(pack: dict, c: dict) -> str:
    rows = []
    for r in pack["days"]["rows"]:
        sc = "0" if not r["score"] else f'{r["score"]:+d}'
        lab = f'{r["date"][5:]}{c["labels"]["base_mark"] if r["is_base"] else ""}'
        rows.append(f'<tr class="{"ext" if r["is_base"] else ""}"><td class="t">{e(lab)}</td><td>{e(str(r["env"]))} {sc}</td>'
                    f'<td class="n">{r["conditions"]}</td><td class="n">{r["up_4pct"]:.0f} / {r["down_4pct"]:.0f}</td>'
                    f'<td class="n">{signed(r["net_advances"])}</td>'
                    f'<td class="n">{above20(r["t2108"])}</td>'
                    f'<td class="n">{signed(r["mcclellan_osc"], 1)}</td></tr>')
    return grid(c["labels"]["days_cols"], "".join(rows), {2, 3, 4, 5, 6}) + f'<p class="one">{rich(c.get("state_line", ""))}</p>'


def weekly_k_table(pack: dict, c: dict) -> str:
    wk, L = pack.get("weekly_k") or {}, c["labels"]
    u = wk.get("universe")
    if not u:
        return ""
    want = c.get("weekly_k_names") or []
    names = [n for tk in want for n in u["named"] if n["ticker"] == tk] or u["named"][:8]
    rows = "".join(f'<tr><td class="t">{e(n["ticker"])}</td><td class="n {cls(n["perf_1w"])}">{pct(n["perf_1w"], 1)}</td>'
                   f'<td class="n {cls(n["vs_wk_ema10"])}">{pct(n["vs_wk_ema10"], 1)}</td>'
                   f'<td class="n {cls(n["vs_wk_ema20"])}">{pct(n["vs_wk_ema20"], 1)}</td>'
                   f'<td>{e(L["yes"]) if n["three_weeks_tight"] else ""}</td>'
                   f'<td class="n">{"—" if n["rs_rating"] is None else int(n["rs_rating"])}</td></tr>' for n in names)
    summary = L["wk_summary"].format(n3=u["three_weeks_tight_tradeable"], nt=u["n_tradeable"],
                                      p10=u["pct_tradeable_above_wk_ema10"])
    th = wk.get("themes_rs_0_1w")
    tl = ""
    if th:
        f = lambda xs: " · ".join(f'{t["group"]} {pct(t["rs_0_1w"], 1)}' for t in xs)
        tl = f'<p class="one"><b>{e(L["rs01_top"])}</b> {e(f(th["top"]))}<br><b>{e(L["rs01_bottom"])}</b> {e(f(th["bottom"]))}</p>'
    return (grid(L["wk_cols"], rows, {1, 2, 3, 5}) + f'<p class="one">{e(summary)}</p>' + tl
            + f'<p class="one">{rich(c.get("weekly_k_line", ""))}</p>')


# ------------------------------------------------------------------ page
CSS = """
@page { size: A4; margin: 2.15cm 1.7cm 1.9cm 1.7cm;
  @top-left { content: "FLUXUS CAPITAL"; font: 700 9pt "Hiragino Sans GB","Heiti SC",sans-serif; letter-spacing: .12em;
              color: #1d4ed8; text-decoration: underline; vertical-align: bottom; padding-bottom: 6pt; }
  @top-right { content: "__MAST__"; font: 600 8pt "Hiragino Sans GB","Heiti SC",sans-serif; letter-spacing: .18em;
               color: #6b7280; vertical-align: bottom; padding-bottom: 6pt; }
  @bottom-center { content: "FLUXUS CAPITAL · CONFIDENTIAL · " counter(page) " / " counter(pages);
                   font: 7.5pt "Hiragino Sans GB","Heiti SC",sans-serif; letter-spacing: .1em; color: #9ca3af; } }
html { font-family: "Hiragino Sans GB","Heiti SC",sans-serif; color: #111827; font-size: 9.6pt; line-height: 1.62; background: #fff; }
body { margin: 0; }
.titlebar { border-left: 6px solid var(--tone); padding: 2pt 0 2pt 12pt; margin: 0 0 12pt; }
.titlebar h1 { font-size: 17pt; line-height: 1.25; margin: 0 0 3pt; font-weight: 700; }
.titlebar p { margin: 0; color: #4b5563; font-size: 9pt; }
.sec { margin: 13pt 0 0; }
.sec h2 { font-size: 11pt; margin: 0 0 6pt; font-weight: 700; }
.dot { display: inline-block; width: 7pt; height: 7pt; border-radius: 2pt; margin-right: 7pt; vertical-align: 1pt; }
p { margin: 0 0 6pt; }
b { font-weight: 700; }
.code { background: #f6f8fa; border: 1px solid #e5e7eb; border-radius: 5pt; padding: 6pt 9pt; }
table { border-collapse: collapse; width: 100%; font-family: Menlo,"Hiragino Sans GB",monospace; font-size: 8pt; }
th { text-align: left; font-weight: 600; color: #6b7280; font-size: 7pt; letter-spacing: .06em; padding: 0 8pt 4pt 0; border-bottom: 1px solid #e5e7eb; }
th.rn { text-align: right; }
td { padding: 3.2pt 8pt 3.2pt 0; vertical-align: top; border-bottom: 1px solid #eef0f3; }
tr:last-child td { border-bottom: 0; }
td.t { font-weight: 700; white-space: nowrap; }
td.n { text-align: right; white-space: nowrap; }
tr.ext td { color: #6b7280; }
.up { color: #15803d; } .dn { color: #b91c1c; }
.strip { display: flex; border: 1px solid #e5e7eb; border-radius: 5pt; }
.strip > div { flex: 1; padding: 5pt 7pt; border-right: 1px solid #e5e7eb; }
.strip > div:last-child { border-right: 0; }
.strip span { display: block; font-size: 6.8pt; color: #6b7280; letter-spacing: .04em; }
.strip b { display: block; font-family: Menlo,"Hiragino Sans GB",monospace; font-size: 10.5pt; }
.strip i { display: block; font-style: normal; font-size: 6.8pt; color: #9ca3af; font-family: Menlo,"Hiragino Sans GB",monospace; }
p.one { margin: 6pt 0 0; }
.note { background: #eff6ff; border-left: 3px solid #2563eb; padding: 7pt 10pt; margin-top: 9pt; }
.note .k { font-size: 7.5pt; letter-spacing: .12em; color: #1d4ed8; font-weight: 700; display: block; }
svg.cond { width: 100%; height: auto; margin-top: 6pt; }
svg.cond .bar { fill: #cbd5e1; } svg.cond .now { fill: #1d4ed8; }
svg.cond .g { stroke: #e5e7eb; stroke-width: 1; } svg.cond .g.mid { stroke-dasharray: 3 3; }
svg.cond .ax { font: 9px Menlo,monospace; fill: #9ca3af; } svg.cond .nl { font: 700 12px Menlo,monospace; fill: #1d4ed8; }
.board { display: flex; gap: 14pt; }
.bp { flex: 1; }
.bp h3 { font-size: 8.5pt; margin: 0 0 4pt; } .bp h3 small { font-weight: 400; color: #9ca3af; font-size: 6.8pt; }
.br { display: flex; align-items: center; font-size: 7.3pt; padding: 1.6pt 0; border-bottom: 1px solid #f1f5f9; }
.bn { width: 44%; line-height: 1.25; } .bn em { font-style: normal; color: #7c3aed; font-size: 6.3pt; }
.bt { width: 30%; position: relative; height: 6pt; }
.bt .z { position: absolute; left: 50%; top: -2pt; width: 1px; height: 10pt; background: #d1d5db; }
.bf { position: absolute; top: 0; height: 6pt; } .bf.up { background: #86efac; } .bf.dn { background: #fca5a5; }
.bv, .bw { width: 13%; text-align: right; font-family: Menlo,monospace; } .bw { color: #9ca3af; }
.sep { border-top: 1px dashed #d1d5db; margin: 2pt 0; }
ol.nl { margin: 0; padding-left: 16pt; } ol.nl li { margin: 0 0 3pt; }
.edu { background: #efece3; border: 1px solid #d9cfb8; border-radius: 6pt; padding: 10pt 12pt; page-break-inside: avoid; }
.edu h2 { color: #3b352a; }
.edu img { width: 100%; display: block; margin-top: 6pt; border-radius: 3pt; }
.metrics { display: flex; background: #0b1220; border-radius: 5pt; padding: 7pt 4pt; margin-bottom: 7pt; }
.metrics > div { flex: 1; padding: 0 8pt; border-right: 1px solid #1f2937; }
.metrics > div:last-child { border-right: 0; }
.metrics span { display: block; color: #94a3b8; font-size: 6.6pt; letter-spacing: .12em; }
.metrics b { display: block; color: #60a5fa; font-family: Menlo,"Hiragino Sans GB",monospace; font-size: 12pt; }
table.pos { width: 60%; }
.keep { page-break-inside: avoid; }
"""


def build_html(pack: dict, c: dict, fig: Path) -> str:
    bad = check_rules(c.get("rules"), c["lang"], pack.get("date"))
    if bad:
        raise SystemExit(f"{c['lang']}: {bad}")
    L, weekly = c["labels"], pack.get("kind") == "weekly"
    i = iter(range(30))
    parts = [f'<div class="titlebar" style="--tone:{TONE[c["tone"]]}"><h1>{e(c["title"])}</h1><p>{e(c["subtitle"])}</p></div>',
             section(next(i), L["big_picture"], f'<p>{rich(c["big_picture"])}</p>')]
    if weekly:
        parts += [section(next(i), L["index_action"], week_index_table(pack, c)),
                  section(next(i), L["market_state"], days_table(pack, c) + founders(c), "keep"),
                  section(next(i), L["conditions"], conditions_svg(pack["days"]["conditions_series"], L["cond_caption"])
                          + groups_board(pack, L, "perf_1w", "perf_1m"), "keep")]
        wk = weekly_k_table(pack, c)
        if wk:
            parts.append(section(next(i), L["weekly_k"], wk))  # flows: keeping it whole left page 2 half empty
    else:
        parts += [section(next(i), L["index_action"], index_table(pack, c)),
                  section(next(i), L["market_state"], state_strip(pack, c) + founders(c), "keep"),
                  section(next(i), L["conditions"], conditions_svg(pack["verdict"]["conditions_series"], L["cond_caption"])
                          + groups_board(pack, L, "perf_1d", "perf_1w"), "keep")]
    parts += [section(next(i), L["working"], ledger(c["led"])), section(next(i), L["laggards"], ledger(c["lagged"]))]
    if c.get("sentiment"):
        parts.append(section(next(i), L["sentiment"], f'<p>{rich(c["sentiment"])}</p>'))
    edu = c["education"]
    parts += [section(next(i), L["tomorrow"], olist(c["tomorrow"])),
              section(next(i), L["rules"], olist(c["rules"]), "keep"),
              section(next(i), f'{L["education"]} · {edu["title"]}',
                      f'<p>{rich(edu["body"])}</p><img src="{fig.as_uri()}" alt="">', "edu")]
    book = book_block(pack, c)
    if book:
        parts.append(section(next(i), L["portfolio"], book, "keep"))
    css = CSS.replace("__MAST__", "WEEKLY MARKET RECAP" if weekly else "DAILY MARKET RECAP")
    return (f'<!doctype html><html lang="{"zh-Hans" if c["lang"] == "ZH" else "en"}"><head><meta charset="utf-8">'
            f'<title>{e(c["title"])}</title><style>{css}</style></head><body>{"".join(parts)}</body></html>')


def check_images(doc: str) -> None:
    from urllib.parse import unquote, urlparse
    for src in re.findall(r'<img src="([^"]+)"', doc):
        p = Path(unquote(urlparse(src).path))
        if not p.exists():
            raise SystemExit(f"missing image (weasyprint would drop it silently): {p}")


def pdf_text(pdf: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--date")
    g.add_argument("--week")
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--langs", default="EN,ZH")
    a = ap.parse_args(argv)
    from weasyprint import HTML
    from pipeline.content.recap.figures import FIGURES
    if a.week:
        T = week_sessions(a.week)[-1].isoformat()
        label, pdir, outdir = a.week, month_dir(T, a.sample) / f"pack_{a.week}", month_dir(T, a.sample)
    else:
        label, pdir, outdir = a.date, pack_dir(a.date, a.sample), month_dir(a.date, a.sample)
    pack = json.loads((pdir / "pack.json").read_text())
    status, report, drawn = 0, {}, set()
    for lang in a.langs.split(","):
        t0 = time.time()
        c = json.loads((pdir / f"content_{lang}.json").read_text())
        fname = c["education"]["figure"]
        fig = pdir / f"edu_{fname}.png"
        if fname not in drawn:
            FIGURES[fname](fig)
            drawn.add(fname)
        doc = build_html(pack, c, fig)
        check_images(doc)
        (pdir / f"recap_{lang}.html").write_text(doc)
        partial = pdir / f"partial_{lang}.pdf"
        HTML(string=doc, base_url=str(pdir)).write_pdf(partial)
        text = pdf_text(partial)
        gr, pg = run_gates(text), check_pages(text)
        final = outdir / f"Market_Recap_{label}_{lang}.pdf"
        if gr["ok"] and pg["ok"]:
            shutil.move(partial, final)
            for old in pdir.glob(f"preview_{lang}-*.png"):
                old.unlink()
            subprocess.run(["pdftoppm", "-r", "60", "-png", str(final), str(pdir / f"preview_{lang}")], check=False)
            print(f"DELIVERED {final} · gates 0/0/0/0 · pages {pg['pages']} body lines {pg['body_lines']} · {time.time() - t0:.1f}s")
        else:
            status = 1
            if final.exists():
                shutil.move(final, pdir / f"previous_{lang}.pdf")
            shutil.move(partial, pdir / f"blocked_{lang}.pdf")
            print(f"BLOCKED {lang}: banned={len(gr['banned'])} 领导力={gr['leadership_zh']} money/shares={len(gr['money_shares'])} "
                  f"voice={len(gr['voice'])} thin_pages={pg['thin_pages']} body_lines={pg['body_lines']}", file=sys.stderr)
            for h in gr["banned"] + gr["money_shares"] + gr["voice"]:
                print(f"   {h['gate_rule']}: {h['match']!r} … {h['context']}", file=sys.stderr)
        report[lang] = {"ok": gr["ok"] and pg["ok"], "banned": len(gr["banned"]), "leadership_zh": gr["leadership_zh"],
                        "money_shares": len(gr["money_shares"]), "voice": len(gr["voice"]), "pages": pg["pages"],
                        "body_lines": pg["body_lines"], "thin_pages": pg["thin_pages"], "seconds": round(time.time() - t0, 1)}
    (pdir / "gates_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main())
