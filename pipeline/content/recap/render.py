#!/usr/bin/env python3
"""content_<LANG>.json + pack.json → HTML → PDF, then three delivery gates.

Usage (needs the recap venv for weasyprint/matplotlib):
    ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.render --date 2026-09-11 --sample

Division of labour:
  pack.json      numbers (index %, market state, breadth, groups, book R/%) — rendered
                 straight from the archives so a prose writer cannot mistype them.
  content_*.json words (title, big picture, notes per row, rules, education) — written
                 per language; ZH is a rewrite, not a translation layer.

A PDF is DELIVERED only if pdftotext of it passes gates.run_gates (banned names = 0,
「领导力」 = 0, dollar amounts / share counts = 0). Otherwise it is moved aside as
blocked_*.pdf inside the pack directory and the process exits 1.
Every <img> must exist before rendering: weasyprint drops a missing image silently.
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
from pipeline.content.recap.gates import run_gates

e = html.escape
TONE = {"up": "#16a34a", "down": "#dc2626", "range": "#2563eb"}
DOTS = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#7c3aed", "#6b7280"]


# ------------------------------------------------------------------ formatting
def pct(x, dp=2, signed=True):
    if x is None:
        return "—"
    s = f"{x * 100:+.{dp}f}%" if signed else f"{x * 100:.{dp}f}%"
    return s.replace("-", "−")


def num(x, dp=2):
    return "—" if x is None else f"{x:,.{dp}f}"


def cls(x):
    return "" if x is None else ("up" if x >= 0 else "dn")


def rich(s: str) -> str:
    """Content strings may carry <b> only; everything else is escaped."""
    s = e(s or "")
    return re.sub(r"&lt;(/?)b&gt;", r"<\1b>", s)


# ------------------------------------------------------------------ blocks
def section(i: int, title: str, body: str, extra_cls: str = "") -> str:
    return (f'<section class="sec {extra_cls}"><h2><span class="dot" style="background:{DOTS[i % len(DOTS)]}"></span>'
            f'{e(title)}</h2>{body}</section>')


def index_table(pack: dict, c: dict) -> str:
    L = c["labels"]
    rows = []
    for tk in ("SPY", "QQQ", "RSP", "DIA", "IWM"):
        a = pack["assets"]["rows"].get(tk)
        if not a:
            continue
        ev, key = c["index_notes"].get(tk, ["", ""])
        rows.append(f'<tr><td class="t">{tk}</td><td class="n">{num(a["close"])}</td>'
                    f'<td class="n {cls(a["change_pct"])}">{pct(a["change_pct"])}</td>'
                    f'<td class="n">{num(a["rel_volume"])}×</td><td>{rich(ev)}</td><td>{rich(key)}</td></tr>')
    for r in c.get("extra_index_rows", []):
        rows.append('<tr class="ext">' + "".join(
            f'<td class="{k}">{rich(v)}</td>' for k, v in zip(("t", "n", "n", "n", "", ""), r)) + "</tr>")
    head = "".join(f"<th{' class=rn' if i in (1, 2, 3) else ''}>{e(h)}</th>" for i, h in enumerate(L["index_cols"]))
    return f'<div class="code"><table class="grid"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def state_strip(pack: dict, c: dict) -> str:
    v, L = pack["verdict"], c["labels"]
    T, P = v["T"], v["P"] or {}
    cT, cP = v.get("conditions_T") or {}, v.get("conditions_P") or {}
    b, bp = pack["breadth"]["T"], pack["breadth"]["P"] or {}
    cells = [
        (L["state_votes"], f'{T["env"]} {T["score"]:+d}'.replace("+0", "0"), f'{L["prev"]} {P.get("env", "—")} {P.get("score", 0):+d}'),
        (L["state_conditions"], f'{cT.get("score", "—")} / 100', f'{L["prev"]} {cP.get("score", "—")}'),
        (L["state_4pct"], f'{b["up_4pct_stockbee"]:.0f} / {b["down_4pct_stockbee"]:.0f}',
         f'{L["prev"]} {bp.get("up_4pct_stockbee", 0):.0f} / {bp.get("down_4pct_stockbee", 0):.0f}'),
        (L["state_adv"], f'{b["net_advances"]:+,.0f}'.replace("-", "−"), f'{L["prev"]} {bp.get("net_advances", 0):+,.0f}'.replace("-", "−")),
        (L["state_sp20"], f'{b["pct_above_20sma_sp500"]:.1f}%', f'{L["prev"]} {bp.get("pct_above_20sma_sp500", 0):.1f}%'),
        (L["state_mcc"], f'{b["mcclellan_osc"]:+.1f}'.replace("-", "−"), f'{L["prev"]} {bp.get("mcclellan_osc", 0):+.1f}'.replace("-", "−")),
    ]
    inner = "".join(f'<div><span>{e(a)}</span><b>{e(x)}</b><i>{e(y)}</i></div>' for a, x, y in cells)
    return f'<div class="strip">{inner}</div><p class="one">{rich(c.get("state_line", ""))}</p>'


def conditions_svg(pack: dict, c: dict) -> str:
    s = pack["verdict"]["conditions_series"]
    n = len(s)
    W, base, top = 940, 150, 12
    bw = W / n
    o = [f'<svg class="cond" viewBox="0 0 1000 170" role="img">']
    for val in (0, 50, 100):
        y = base - val / 100 * (base - top)
        o.append(f'<line x1="0" x2="{W}" y1="{y:.1f}" y2="{y:.1f}" class="g{" mid" if val == 50 else ""}"/>'
                 f'<text x="{W + 8}" y="{y + 4:.1f}" class="ax">{val}</text>')
    for j, v in enumerate(s):
        h = v / 100 * (base - top)
        o.append(f'<rect x="{j * bw + bw * .15:.1f}" y="{base - h:.1f}" width="{bw * .7:.1f}" height="{h:.1f}" class="{"now" if j == n - 1 else "bar"}"/>')
    o.append(f'<text x="{W - 4}" y="{base - s[-1] / 100 * (base - top) - 6:.1f}" text-anchor="end" class="nl">{s[-1]}</text>')
    o.append(f'<text x="0" y="166" class="ax">{e(c["labels"]["cond_caption"].format(n=n))}</text></svg>')
    return "".join(o)


def groups_board(pack: dict, c: dict) -> str:
    L = c["labels"]
    def panel(kind, title):
        g = pack["groups"][kind]
        items = g["top"][:5] + g["bottom"][-5:]
        mx = max(abs(x["perf_1d"]) for x in items) or 1
        rows = []
        for i, x in enumerate(items):
            if i == 5:
                rows.append('<div class="sep"></div>')
            w = abs(x["perf_1d"]) / mx * 50
            side = f"left:50%;width:{w:.1f}%" if x["perf_1d"] >= 0 else f"right:50%;width:{w:.1f}%"
            shift = "" if x["state_P"] in (None, x["state"]) else f' <em>{e(x["state_P"])}→{e(x["state"])}</em>'
            rows.append(f'<div class="br"><div class="bn">{e(x["group"])}{shift}</div>'
                        f'<div class="bt"><span class="z"></span><span class="bf {cls(x["perf_1d"])}" style="{side}"></span></div>'
                        f'<div class="bv {cls(x["perf_1d"])}">{pct(x["perf_1d"], 1)}</div>'
                        f'<div class="bw">{pct(x["perf_1w"], 1)}</div></div>')
        return (f'<div class="bp"><h3>{e(title)} <small>{e(L["board_cols"])} · n={g["n"]}</small></h3>'
                + "".join(rows) + "</div>")
    return f'<div class="board">{panel("industry", L["industries"])}{panel("theme", L["themes"])}</div>'


def ledger(rows: list) -> str:
    return '<div class="code"><table class="led">' + "".join(
        f'<tr><td class="t">{rich(a)}</td><td class="n {("up" if b.startswith("+") else "dn") if b else ""}">{rich(b)}</td><td>{rich(x)}</td></tr>'
        for a, b, x in rows) + "</table></div>"


def olist(items: list) -> str:
    return '<ol class="nl">' + "".join(f"<li>{rich(x)}</li>" for x in items) + "</ol>"


def book_block(pack: dict, c: dict) -> str:
    b, L = pack.get("book") or {}, c["labels"]
    if "open_names" not in b:
        return f'<p class="ph">{e(L["book_missing"])} ({e(str(b.get("status")))})</p>'
    def sR(x): return f"{x:+.2f}R".replace("-", "−")
    def sP(x): return f"{x:+.2f}%".replace("-", "−")
    cells = [(L["m_return"], sP(b["return_pct"]) if "return_pct" in b else "—"),
             (L["m_cash"], f'{b["cash_pct"]:.1f}%' if "cash_pct" in b else "—"),
             (L["m_open"], str(b["open_names"])),
             (L["m_closed"], str(b["closed_trades"])),
             (L["m_openR"], sR(b["open_R_total"])),
             (L["m_realR"], sR(b["realized_R_session"]))]
    bar = '<div class="metrics">' + "".join(f"<div><span>{e(a)}</span><b>{e(x)}</b></div>" for a, x in cells) + "</div>"
    pos = "".join(f'<tr><td class="t">{e(p["ticker"])}</td><td>{e(L["long"] if p["direction"] == "long" else L["short"])}</td>'
                  f'<td>{e(p["entry_date"])}</td><td class="n {cls(p["open_R"])}">{sR(p["open_R"]) if p["open_R"] is not None else "—"}</td></tr>'
                  for p in b["positions"])
    head = "".join(f"<th>{e(h)}</th>" for h in L["pos_cols"])
    expo = L["exposure"].format(long=b.get("long_exposure_pct", "—"), short=b.get("short_exposure_pct", "—"))
    return (bar + f'<div class="code"><table class="grid pos"><thead><tr>{head}</tr></thead><tbody>{pos}</tbody></table></div>'
            + f'<p class="one">{rich(c["portfolio_note"])}</p><p class="src">{e(expo)} · {e(L["book_src"])}</p>')


# ------------------------------------------------------------------ education figure
def edu_figure(out: Path) -> Path:
    """Left side of the V → MAs coil → right side. Schematic, not price data.
    Three checks (spec §5): (1) price really makes lower highs that fail at the
    falling 20EMA, then a tight range, then a break above both lines; (2) the 20EMA
    sits ABOVE price on the left (resistance) and the 50 below it, the two converge
    in the coil, price breaks out ABOVE both; (3) each label sits on the thing it names."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Ellipse

    PAPER, INK, VIO, AMB, GRN, GRY = "#efece3", "#1b1b1b", "#5b5fd6", "#c98a1b", "#3f8f5a", "#8a857a"
    fig = plt.figure(figsize=(9.2, 4.6), dpi=200, facecolor=PAPER)
    ax = fig.add_axes([0.03, 0.06, 0.94, 0.72])
    ax.set_facecolor(PAPER)
    rng = np.random.default_rng(7)
    ax.imshow(rng.normal(0, 1, (120, 240)), extent=(0, 100, 0, 60), cmap="Greys", alpha=0.035,
              aspect="auto", zorder=0)
    # price zigzag: lower highs into the falling 20, tight coil, break up
    px = [2, 7, 11, 16, 20, 25, 29, 34, 38, 43, 47, 52, 56, 60, 64, 68, 72, 76, 80, 86, 92, 97]
    py = [50, 41, 45.5, 36, 39.3, 31, 35.2, 27.5, 30.6, 26.2, 29.3, 26.6, 28.9, 27.0, 28.6, 27.4, 28.8, 31.8, 30.6, 38.5, 36.8, 45]
    ax.plot(px, py, color=INK, lw=1.6, zorder=4, solid_joinstyle="miter")
    # 20EMA: arc falling from above price, flattening into the coil, curling up after the break.
    # Fitted so each pop high touches it from below (spec §5 check 2), not guessed.
    x = np.linspace(6, 97, 300)
    ema20 = 28.8 + 27.4 * np.exp(-(x - 2) / 20.6) + 0.017 * np.clip(x - 74, 0, None) ** 2
    sma50 = 28.4 + 2.5 * np.exp(-(x - 2) / 40.0) - 0.008 * (x - 2) + 0.003 * np.clip(x - 82, 0, None) ** 2
    ax.plot(x, ema20, color=VIO, lw=1.3, zorder=3)
    ax.plot(x, sma50, color=AMB, lw=1.3, zorder=3)
    ax.text(7.5, 53.2, "20 EMA · falling", color=VIO, fontsize=7.5, family="Menlo")
    ax.text(36, 24.6, "50 SMA", color=AMB, fontsize=7.5, family="Menlo")
    # check (1)+(2) as code: pops touch the falling 20 from below; the two lines diverge
    # on the left and converge in the coil; the last print clears both.
    ema_at = lambda xx: float(np.interp(xx, x, ema20))
    sma_at = lambda xx: float(np.interp(xx, x, sma50))
    for hx, hy in ((11, 45.5), (20, 39.3), (29, 35.2)):
        assert ema_at(hx) - 3.0 <= hy <= ema_at(hx) + 0.3, (hx, hy, ema_at(hx))
    assert all(py[i] < ema_at(px[i]) for i in range(1, 17)), "left side: price must stay under the 20"
    assert ema_at(11) - sma_at(11) > 10 and ema_at(68) - sma_at(68) < 2.5, "averages must coil"
    assert ema_at(20) < ema_at(11) and ema_at(40) < ema_at(29), "20 must be falling on the left"
    assert py[-1] > ema_at(97) and py[-1] > sma_at(97)
    def callout(cx, cy, w, h, tx, ty, label, color=GRY):
        ax.add_patch(Ellipse((cx, cy), w, h, fill=False, ec=GRY, lw=0.9, zorder=5))
        ax.annotate(label, xy=(cx, cy + h / 2 * (1 if ty > cy else -1)), xytext=(tx, ty), fontsize=7.6,
                    family="Menlo", color=color, ha="center",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=GRY), zorder=6)
    callout(20, 39.3, 5, 3.4, 24, 51.5, "pop sold at the 20")
    callout(29, 35.2, 5, 3.4, 40, 44.5, "lower high, sold again")
    callout(62, 28.0, 22, 5.6, 58, 17.5, "averages coil · range tightens", VIO)
    callout(86, 38.5, 6, 4, 80, 50.5, "right side of the V", GRN)
    ax.text(8, 13.5, "LEFT SIDE", fontsize=7, family="Menlo", color=GRY)
    ax.set_xlim(0, 100); ax.set_ylim(10, 60); ax.axis("off")
    fig.text(0.03, 0.93, "E D U C A T I O N  ·  S C H E M A T I C", fontsize=7.2, family="Menlo", color=GRY)
    fig.text(0.03, 0.845, "Pops get sold until the averages coil", fontsize=14, weight="bold", color=INK)
    fig.savefig(out, facecolor=PAPER)
    plt.close(fig)
    return out


# ------------------------------------------------------------------ page
CSS = """
@page { size: A4; margin: 2.15cm 1.7cm 1.9cm 1.7cm;
  @top-left { content: "FLUXUS CAPITAL"; font: 700 9pt "Hiragino Sans GB","Heiti SC",sans-serif; letter-spacing: .12em;
              color: #1d4ed8; text-decoration: underline; vertical-align: bottom; padding-bottom: 6pt; }
  @top-right { content: "DAILY MARKET RECAP"; font: 600 8pt "Hiragino Sans GB","Heiti SC",sans-serif; letter-spacing: .18em;
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
.ph { color: #6b7280; font-style: italic; }
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
.edu .opt { font-size: 7.6pt; color: #6b604b; margin: 0 0 6pt; }
.metrics { display: flex; background: #0b1220; border-radius: 5pt; padding: 7pt 4pt; margin-bottom: 7pt; }
.metrics > div { flex: 1; padding: 0 8pt; border-right: 1px solid #1f2937; }
.metrics > div:last-child { border-right: 0; }
.metrics span { display: block; color: #94a3b8; font-size: 6.6pt; letter-spacing: .12em; }
.metrics b { display: block; color: #60a5fa; font-family: Menlo,"Hiragino Sans GB",monospace; font-size: 12pt; }
table.pos { width: 60%; }
p.src, p.foot { font-size: 7pt; color: #9ca3af; margin-top: 4pt; }
.keep { page-break-inside: avoid; }
"""


def build_html(pack: dict, c: dict, fig: Path) -> str:
    L = c["labels"]
    fn = c.get("founders_note")
    note = (f'<div class="note"><span class="k">FOUNDERS NOTE</span>{rich(fn)}</div>' if fn
            else f'<div class="note"><span class="k">FOUNDERS NOTE</span><span class="ph">{e(L["founders_missing"])}</span></div>')
    edu = c["education"]
    opts = " · ".join(f'{o["key"]}: {e(o["title"])} — {e(o["why"])}' for o in edu["options"])
    i = iter(range(20))
    parts = [
        f'<div class="titlebar" style="--tone:{TONE[c["tone"]]}"><h1>{e(c["title"])}</h1><p>{e(c["subtitle"])}</p></div>',
        section(next(i), L["big_picture"], f'<p>{rich(c["big_picture"])}</p>'),
        section(next(i), L["index_action"], index_table(pack, c)),
        section(next(i), L["market_state"], state_strip(pack, c) + note, "keep"),
        section(next(i), L["conditions"], conditions_svg(pack, c) + groups_board(pack, c), "keep"),
        section(next(i), L["working"], ledger(c["led"])),
        section(next(i), L["laggards"], ledger(c["lagged"])),
    ]
    if c.get("sentiment"):
        parts.append(section(next(i), L["sentiment"], f'<p>{rich(c["sentiment"])}</p>'))
    parts += [
        section(next(i), L["tomorrow"], olist(c["tomorrow"])),
        section(next(i), L["rules"], olist(c["rules"]), "keep"),
        section(next(i), f'{L["education"]} · {edu["title"]}',
                f'<p class="opt">{e(L["edu_options"])} {opts} · <b>{e(L["edu_chosen"])} {e(edu["chosen"])}</b></p>'
                f'<p>{rich(edu["body"])}</p><img src="{fig.as_uri()}" alt="">'
                f'<p class="src">{e(edu["caption"])}</p>', "edu"),
        section(next(i), L["portfolio"], book_block(pack, c), "keep"),
        f'<p class="foot">{rich(c.get("footnote", ""))}</p>',
    ]
    return (f'<!doctype html><html lang="{"zh-Hans" if c["lang"] == "ZH" else "en"}"><head><meta charset="utf-8">'
            f'<title>{e(c["title"])}</title><style>{CSS}</style></head><body>{"".join(parts)}</body></html>')


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
    ap.add_argument("--date", required=True)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--langs", default="EN,ZH")
    a = ap.parse_args(argv)
    from weasyprint import HTML
    pdir = pack_dir(a.date, a.sample)
    pack = json.loads((pdir / "pack.json").read_text())
    fig = edu_figure(pdir / "edu_figure.png")
    status, report = 0, {}
    for lang in a.langs.split(","):
        t0 = time.time()
        c = json.loads((pdir / f"content_{lang}.json").read_text())
        doc = build_html(pack, c, fig)
        check_images(doc)
        (pdir / f"recap_{lang}.html").write_text(doc)
        partial = pdir / f"partial_{lang}.pdf"
        HTML(string=doc, base_url=str(pdir)).write_pdf(partial)
        g = run_gates(pdf_text(partial))
        final = month_dir(a.date, a.sample) / f"Market_Recap_{a.date}_{lang}.pdf"
        if g["ok"]:
            shutil.move(partial, final)
            subprocess.run(["pdftoppm", "-r", "60", "-png", str(final), str(pdir / f"preview_{lang}")], check=False)
            print(f"DELIVERED {final} · gates 0/0/0 · {time.time() - t0:.1f}s")
        else:
            blocked = pdir / f"blocked_{lang}.pdf"
            shutil.move(partial, blocked)
            status = 1
            print(f"BLOCKED {lang}: banned={len(g['banned'])} 领导力={g['leadership_zh']} money/shares={len(g['money_shares'])}",
                  file=sys.stderr)
            for h in g["banned"] + g["money_shares"]:
                print(f"   {h['gate_rule']}: {h['match']!r} … {h['context']}", file=sys.stderr)
        report[lang] = {"ok": g["ok"], "banned": len(g["banned"]), "leadership_zh": g["leadership_zh"],
                        "money_shares": len(g["money_shares"]), "seconds": round(time.time() - t0, 1)}
    (pdir / "gates_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(main())
