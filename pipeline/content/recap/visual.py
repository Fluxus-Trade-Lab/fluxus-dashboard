#!/usr/bin/env python3
"""Visual-line layout for the recap samples: a data-driven review page + A4 PDFs, one renderer.

Usage (recap venv):
    ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.visual --sample

How it is built
  * Python gathers each issue's numbers (pack.json + origin/main archives as of the issue date) and the
    words (content_<LANG>.json) into one JSON document, formatted so no line exceeds 300 characters.
  * visual_assets/recap_page.js draws everything from that JSON in the browser — drop line, conditions
    chart, vote strip, bar panels, schematic — using the Visual line's CSS (recap_visual.css, verbatim)
    plus recap_local.css. The published page and the PDFs come from the same JS.
  * PDFs: headless Chrome prints the A layout (#…&print=1) from a local copy whose fonts are the files
    in ~/.venvs/fluxus-recap/fonts (never fetched at render time).

Delivery checks (any failure → blocked_* output, exit 1)
  page     size ≤ 350 KB, every line ≤ 300 chars; gates on the JSON words of every issue × language;
           gates again on the DOM Chrome actually rendered for all 20 variants, which must contain the
           drawn SVGs; two screenshots saved as _web_preview_*.png
  PDF      gates + rules check + page fill + text inside the type area (pages.check_margins)
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from pipeline.content.recap import month_dir, pack_dir
from pipeline.content.recap.build_pack import csv_rows, show
from pipeline.content.recap.constants import check_rules
from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.pages import check_margins, check_pages
from pipeline.content.recap.visual_figs import FIGS
from pipeline.content.recap.weeks import week_sessions
from pipeline.marketcal import is_trading_day

e = html.escape
ASSETS = Path(__file__).with_name("visual_assets")
FONT_DIR = Path.home() / ".venvs" / "fluxus-recap" / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ISSUES = [("W37", "2026-W37"), ("09-11", "2026-09-11"), ("09-10", "2026-09-10"), ("09-09", "2026-09-09"), ("09-08", "2026-09-08")]
MAX_LINE, MAX_BYTES = 300, 350 * 1024
PAGE_MARGIN_MM = (14.0, 14.0)  # left/right, must match @page in recap_local.css
FONTS_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600'
              '&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">')

CHROME_LABELS = {
    "EN": {"legend": ["counts for", "counts against", "inside its line", "not counted", "number = distance past each vote’s own line"],
           "units": {"ratio": "ratio", "names": "names", "points": "points", "warnings": "warnings", "": ""},
           "votes": "votes", "top3": "top 3 · bottom 3", "d1": "1 day", "w1": "1 week", "ll": "Leaders and Laggards",
           "rot_d": "Rotation · the session", "rot_w": "Rotation · the week", "board": "The Board",
           "b_votes": "Breadth votes", "b_cond": "Conditions", "b_led": "Led", "b_paid": "Paid",
           "pick_on": "A · sample default", "pick_off": "B · alternative",
           "schem": "Schematic — illustrates the concept, not price data.", "score": "Weekly Scorecard",
           "tape": "The Tape", "founders": "Founders Note", "sessions": "Session by session",
           "daily": "Daily Market Recap", "weekly": "Weekly Market Recap", "droparia": "SPX drop line, 21 sessions",
           "cond_aria": "Market Conditions score by session",
           "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "vlabels": {}},
    "ZH": {"legend": ["计入看多", "计入看空", "在线内", "未计入", "数字 = 离各自那条线的距离"],
           "units": {"ratio": "比值", "names": "只", "points": "点", "warnings": "条", "": ""},
           "votes": "票", "top3": "前 3 · 后 3", "d1": "1 日", "w1": "1 周", "ll": "领涨与落后",
           "rot_d": "轮动 · 当天", "rot_w": "轮动 · 本周", "board": "看板",
           "b_votes": "广度票板", "b_cond": "市场状况", "b_led": "领涨", "b_paid": "让位",
           "pick_on": "A · 样张默认", "pick_off": "B · 备选",
           "schem": "示意图——说明概念，不是真实价格。", "score": "周成绩单",
           "tape": "盘面", "founders": "Founders Note", "sessions": "逐日读数",
           "daily": "Daily Market Recap", "weekly": "Weekly Market Recap", "droparia": "SPX 掉落线，21 个交易日",
           "cond_aria": "市场状况分，逐日", "months": [f"{i}月" for i in range(1, 13)],
           "vlabels": {"5-day ratio": "5 日比", "10-day ratio": "10 日比", "Thrust": "推力", "Quarterly spread": "季度差",
                       "13%/34d spread": "13%/34 日差", "New highs vs lows": "新高对新低", "McClellan": "McClellan",
                       "% above 200-day": "站上 200 日线占比", "T2108 zone": "T2108 区间", "SPY warnings": "SPY 警示",
                       "QQQ warnings": "QQQ 警示", "Benchmark trend": "基准趋势"}},
}


# ------------------------------------------------------------------ JSON with short lines
def _jstr(s: str) -> str:
    return json.dumps(s, ensure_ascii=False).replace("</", "<\\/")


def jdump(o, ind: int = 0, width: int = 180, chunk: int = 140) -> str:
    """Indented JSON where long strings become {"j": [chunks]} and scalar arrays wrap, so every line stays short.
    The page's txt() joins chunks back; tests assert the round trip and the line cap."""
    pad, pad1 = " " * ind, " " * (ind + 1)
    if isinstance(o, str):
        if len(o) <= chunk:
            return _jstr(o)
        parts = [o[i:i + chunk] for i in range(0, len(o), chunk)]
        return '{"j": [\n' + ",\n".join(pad1 + _jstr(p) for p in parts) + "\n" + pad + "]}"
    if o is None or isinstance(o, bool) or isinstance(o, (int, float)):
        return json.dumps(o)
    if isinstance(o, dict):
        if not o:
            return "{}"
        return "{\n" + ",\n".join(pad1 + _jstr(str(k)) + ": " + jdump(v, ind + 1, width, chunk) for k, v in o.items()) + "\n" + pad + "}"
    if isinstance(o, (list, tuple)):
        if not o:
            return "[]"
        if all(x is None or isinstance(x, (bool, int, float)) or (isinstance(x, str) and len(x) <= 40) for x in o):
            lines, cur = [], ""
            for p in (jdump(x) for x in o):
                if cur and len(cur) + len(p) + 2 > width:
                    lines.append(cur)
                    cur = p
                else:
                    cur = p if not cur else cur + ", " + p
            lines.append(cur)
            if len(lines) == 1 and len(lines[0]) + ind < 120:
                return "[" + lines[0] + "]"
            return "[\n" + ",\n".join(pad1 + ln for ln in lines) + "\n" + pad + "]"
        return "[\n" + ",\n".join(pad1 + jdump(x, ind + 1, width, chunk) for x in o) + "\n" + pad + "]"
    raise TypeError(type(o))


def unjoin(o):
    """Python mirror of the page's txt(): {"j": [...]} → str (used by gates and tests)."""
    if isinstance(o, dict):
        if set(o) == {"j"} and isinstance(o["j"], list):
            return "".join(o["j"])
        return {k: unjoin(v) for k, v in o.items()}
    if isinstance(o, list):
        return [unjoin(x) for x in o]
    return o


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


# ------------------------------------------------------------------ archive reads (as of D)
def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def r5(x):
    return None if x is None else round(float(x), 5)


_json_cache: dict = {}


def jshow(path):
    if path not in _json_cache:
        _json_cache[path] = json.loads(show(path))
    return _json_cache[path]


def spx_segment(D):
    rows = sorted({(r["date"], float(r["spx_close"])) for r in csv_rows("data/history/breadth_archive.csv")
                   if r["date"] <= D and fl(r.get("spx_close")) and is_trading_day(dt.date.fromisoformat(r["date"]))})
    seg = rows[-21:]
    assert seg[-1][0] == D and len(seg) == 21, (D, seg[-1])
    return seg


def issue_data(tag: str, label: str, sample: bool) -> dict:
    weekly = "-W" in label
    D = week_sessions(label)[-1].isoformat() if weekly else label
    pdir = (month_dir(D, sample) / f"pack_{label}") if weekly else pack_dir(label, sample)
    pack = json.loads((pdir / "pack.json").read_text())
    content = {lang: json.loads((pdir / f"content_{lang}.json").read_text()) for lang in ("EN", "ZH")}
    seg = spx_segment(D)
    cond = [h for h in jshow("data/output/breadth.json")["conditions"]["history"] if h["date"] <= D]
    assert cond[-1]["date"] == D
    months, last = [], None
    for i, h in enumerate(cond):
        if h["date"][:7] != last:
            months.append([i, h["date"][:7]])
            last = h["date"][:7]
    verd = jshow("data/output/breadth_replay.json")["verdicts"][D]
    bk = defaultdict(list)
    for r in csv_rows("data/history/groups_archive.csv"):
        if r["date"] == D and fl(r["perf_1d"]) is not None and fl(r["perf_1w"]) is not None:
            bk[r["kind"]].append(r)
    groups = {}
    for kind in ("industry", "theme"):
        groups[kind] = {}
        for col, key in (("perf_1d", "d1"), ("perf_1w", "w1")):
            s = sorted(bk[kind], key=lambda r: fl(r[col]), reverse=True)
            groups[kind][key] = [[r["group"], r["state"], r5(r[col])] for r in s[:4] + s[-4:]]
    main = groups["theme"]["w1" if weekly else "d1"]
    idx = []
    for tk in ("SPY", "QQQ", "RSP", "DIA", "IWM"):
        a = pack["assets"]["rows"].get(tk)
        if not a:
            continue
        if weekly:
            idx.append({"t": tk, "last": r5(a["close_T"]), "chg": r5(a["week_pct"]), "days": [r5(x["change_pct"]) for x in a["daily"]]})
        else:
            idx.append({"t": tk, "last": r5(a["close"]), "chg": r5(a["change_pct"]), "vol": r5(a["rel_volume"])})
    d = dt.date.fromisoformat(D)
    out = {"tag": tag, "label": label, "weekly": weekly, "D": D, "D0": seg[0][0],
           "no": label.split("-")[-1] if weekly else D[5:].replace("-", ""),
           "spx": [round(p, 2) for _, p in seg],
           "cond": {"scores": [h["score"] for h in cond], "months": months},
           "verd": {"env": verd["env"], "score": verd["score"],
                    "votes": [[v["label"], v["side"], r5(v["margin"]), v["unit"], bool(v["measurable"])] for v in verd["vote_detail"]]},
           "groups": groups, "led": main[0][::2], "paid": main[-1][::2], "idx": idx}
    if weekly:
        first = week_sessions(label)[0]
        wk = label.split("W")[-1]
        out["when"] = {"EN": f"Week {wk} · {d:%B} {first.day}–{d.day} · {d.year}",
                       "ZH": f"{d.year} 年第 {wk} 周 · {d.month} 月 {first.day}–{d.day} 日"}
        days = pack["days"]["rows"]
        fri = days[-1]
        low = min(days[1:], key=lambda r: r["score"] or 0)
        out["state"] = {"env": verd["env"], "score": verd["score"], "cond": cond[-1]["score"],
                        "spy_week": r5(pack["assets"]["rows"]["SPY"]["week_pct"]),
                        "low": {"env": low["env"], "score": low["score"], "cond": low["conditions"]},
                        "fri": {"env": fri["env"], "score": fri["score"], "cond": fri["conditions"],
                                "up4": fri["up_4pct"], "down4": fri["down_4pct"]}}
        out["days"] = [[r["date"], r["is_base"], r["env"], r["score"], r["conditions"], r["up_4pct"], r["down_4pct"],
                        r["net_advances"], r["t2108"], r["mcclellan_osc"]] for r in days]
        out["scorecard"] = [[tk, r5(pack["assets"]["rows"][tk]["week_pct"])] for tk in ("SPY", "QQQ", "RSP", "IWM")]
        u = (pack.get("weekly_k") or {}).get("universe")
        if u:
            want = content["EN"].get("weekly_k_names") or []
            names = [[n["ticker"], r5(n["perf_1w"]), r5(n["vs_wk_ema10"]), r5(n["vs_wk_ema20"]), n["three_weeks_tight"],
                      None if n["rs_rating"] is None else int(n["rs_rating"])] for tk in want for n in u["named"] if n["ticker"] == tk]
            th = pack["weekly_k"].get("themes_rs_0_1w")
            out["weekly_k"] = {"names": names,
                               "summary": {"n3": u["three_weeks_tight_tradeable"], "nt": u["n_tradeable"], "p10": u["pct_tradeable_above_wk_ema10"]},
                               "rs01": None if not th else {"top": [[t["group"], r5(t["rs_0_1w"])] for t in th["top"]],
                                                           "bottom": [[t["group"], r5(t["rs_0_1w"])] for t in th["bottom"]]}}
    else:
        wd = "一二三四五六日"[d.weekday()]
        out["when"] = {"EN": f"{d:%A} · {d:%B} {d.day} · {d.year}", "ZH": f"{d.year} 年 {d.month} 月 {d.day} 日 · 周{wd}"}
        b = pack["breadth"]["T"]
        out["state"] = {"env": verd["env"], "score": verd["score"], "cond": cond[-1]["score"],
                        "up4": b["up_4pct_stockbee"], "down4": b["down_4pct_stockbee"], "net": b["net_advances"]}
    bkk = pack.get("book") or {}
    out["book"] = None if "open_names" not in bkk else {
        "ret": bkk["return_pct"], "cash": bkk["cash_pct"], "open": bkk["open_names"], "closed": bkk["closed_trades"],
        "openR": bkk["open_R_total"], "realR": bkk["realized_R_period"],
        "pos": [[p["ticker"], p["direction"], p["entry_date"], p["open_R"]] for p in bkk["positions"]]}
    keep = ("lang", "title", "subtitle", "big_picture", "index_notes", "extra_index_rows", "state_line", "founders_note",
            "led", "lagged", "sentiment", "tomorrow", "rules", "education", "portfolio_note", "weekly_k_line", "labels")
    out["V"] = {lang: {k: content[lang].get(k) for k in keep} for lang in ("EN", "ZH")}
    out["fig"] = {lang: FIGS[content[lang]["education"]["figure"]](lang) for lang in ("EN", "ZH")}
    out["_rules_check"] = {lang: check_rules(content[lang].get("rules"), lang, D) for lang in ("EN", "ZH")}
    return out


# ------------------------------------------------------------------ page
HEADER = """<header class="top">
  <p class="eyebrow">Fluxus Capital · Market Recap · 样张 · W37</p>
  <h1>复盘样张 · Visual 版式</h1>
  <p class="lede">
    五期内容不变，换成 Visual 线 9/11 周刊的视觉系统。A 登记体、B 掉落体，中英各一套；
    教育段加 A/B 选题，样张默认 A。
  </p>
  <div class="switches">
    <div class="switch" role="group" aria-label="期数">
{issues}
    </div>
    <div class="switch" role="group" aria-label="语言">
      <button type="button" data-set="lang" data-val="ZH" aria-pressed="true">中</button>
      <button type="button" data-set="lang" data-val="EN" aria-pressed="false">EN</button>
    </div>
    <div class="switch" role="group" aria-label="排版">
      <button type="button" data-set="layout" data-val="A" aria-pressed="true">A · 登记体</button>
      <button type="button" data-set="layout" data-val="B" aria-pressed="false">B · 掉落体</button>
    </div>
  </div>
</header>"""


def wrap_long_css(css: str) -> str:
    out = []
    for ln in css.splitlines():
        if len(ln) <= MAX_LINE:
            out.append(ln)
        else:
            out.extend(x for x in re.sub(r";\s*", ";\n  ", ln).splitlines())
    return "\n".join(out)


def header_html() -> str:
    btns = "\n".join(f'      <button type="button" data-set="issue" data-val="{t}" aria-pressed="{"true" if t == "W37" else "false"}">{t}</button>'
                     for t, _ in ISSUES)
    return HEADER.replace("{issues}", btns)


def page_html(data_json: str, fonts: str) -> str:
    css = wrap_long_css((ASSETS / "recap_visual.css").read_text() + "\n" + (ASSETS / "recap_local.css").read_text())
    js = (ASSETS / "recap_page.js").read_text()
    return (f"<title>Fluxus Recap 样张</title>\n{fonts}\n<style>\n{css}\n</style>\n{header_html()}\n"
            '<main id="app">\n  <p class="prose">—</p>\n</main>\n'
            f'<script type="application/json" id="recap-data">\n{data_json}\n</script>\n<script>\n{js}\n</script>\n')


def local_wrapper(page: str) -> str:
    return ('<!doctype html>\n<html lang="zh-Hans">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n</head>\n<body>\n' + page + "</body>\n</html>\n")


def local_fonts_css() -> str:
    faces = []
    fams = {"IBMPlexSans": "IBM Plex Sans", "IBMPlexSansCondensed": "IBM Plex Sans Condensed", "IBMPlexMono": "IBM Plex Mono"}
    for f in sorted(FONT_DIR.glob("IBMPlex*-*.woff")):
        fam, wt = f.stem.rsplit("-", 1)
        faces.append(f'@font-face {{ font-family: "{fams[fam]}"; font-weight: {wt}; src: url("{f.as_uri()}"); }}')
    if not faces:
        raise SystemExit(f"no IBM Plex fonts in {FONT_DIR} — PDFs must not fetch fonts at render time")
    return "<style>\n" + "\n".join(faces) + "\n</style>"


def html_text(fragment: str) -> str:
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</(p|div|li|tr|h\d|section|article)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s)


# ------------------------------------------------------------------ Chrome
def chrome(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    """One headless Chrome run, never in parallel with another.
    Measured 2026-09-13: a fresh --user-data-dir profile made dump-dom/screenshot hang past 60–120 s on this
    machine, while the default profile with a virtual-time budget finished a JS-page screenshot in 15.5 s."""
    args = [x for x in args if not x.startswith("--virtual-time-budget")]
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=8000", *args],
                          capture_output=True, text=True, timeout=timeout)


def dump_dom(url: str) -> str:
    return chrome(["--virtual-time-budget=6000", "--dump-dom", url]).stdout


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--skip-pdf", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    issues = [issue_data(tag, label, a.sample) for tag, label in ISSUES]
    out = month_dir(issues[1]["D"], a.sample) / "visual"
    out.mkdir(parents=True, exist_ok=True)
    report, status = {"page": {}, "dom": {}, "pdf": {}}, 0

    # words: gates on everything the page can show, per issue × language
    head_text = html_text(header_html())
    for iss in issues:
        for lang in ("ZH", "EN"):
            words = "\n".join(strings(unjoin([iss["V"][lang], iss["fig"][lang], CHROME_LABELS[lang], iss["when"][lang]])))
            g = run_gates(head_text + "\n" + words)
            bad = iss["_rules_check"][lang]
            ok = g["ok"] and not bad
            report["page"][f'{iss["tag"]}/{lang}'] = {"ok": ok, "rules": bad, "banned": len(g["banned"]), "voice": len(g["voice"]),
                                                     "money": len(g["money_shares"]), "leadership_zh": g["leadership_zh"]}
            if not ok:
                status = 1
                print(f'WORDS BLOCKED {iss["tag"]}/{lang}: {bad or ""} ' + "; ".join(f'{h["gate_rule"]}:{h["match"]!r}' for h in g["banned"] + g["money_shares"] + g["voice"]), file=sys.stderr)
    data = {"chrome": CHROME_LABELS, "issues": [{k: v for k, v in iss.items() if not k.startswith("_")} for iss in issues]}
    data_json = jdump(data)
    page = page_html(data_json, FONTS_LINK)
    longest = max(len(ln) for ln in page.splitlines())
    size = len(page.encode())
    report["page_stats"] = {"bytes": size, "lines": page.count("\n"), "longest_line": longest}
    if longest > MAX_LINE or size > MAX_BYTES:
        status = 1
        print(f"PAGE SHAPE BLOCKED: {size} bytes, longest line {longest}", file=sys.stderr)
    name = "recap_samples.html" if status == 0 else "blocked_recap_samples.html"
    (out / name).write_text(page)
    render = out / "_render.html"
    render.write_text(local_wrapper(page))
    print(f"PAGE {out / name} · {size / 1024:.0f} KB · {page.count(chr(10))} lines · longest {longest} · {time.time() - t0:.1f}s")

    # DOM Chrome actually rendered: all variants
    must = {"A": ('class="drop', 'class="chart"', 'class="votes', 'class="tell"'),
            "B": ('class="drop', 'class="chart"', 'class="votes', 'class="tell"', 'class="bpanel"')}
    for iss in issues:
        for lang in ("ZH", "EN"):
            for layout in ("A", "B"):
                dom = dump_dom(f'{render.as_uri()}#issue={iss["tag"]}&lang={lang}&layout={layout}')
                m = re.search(r'<main id="app"[^>]*data-rendered="([^"]+)"[^>]*>(.*)</main>', dom, re.S)
                drawn = bool(m) and m.group(1) == f'{iss["tag"]}|{lang}|{layout}' and all(x in m.group(2) for x in must[layout])
                g = run_gates(html_text(m.group(2))) if m else {"ok": False, "banned": [], "voice": [], "money_shares": [], "leadership_zh": 0}
                ok = drawn and g["ok"] and m.group(2).count("—</p>") == 0
                report["dom"][f'{iss["tag"]}/{lang}/{layout}'] = {"ok": ok, "drawn": drawn, "banned": len(g["banned"]),
                                                                 "voice": len(g["voice"]), "money": len(g["money_shares"]),
                                                                 "dash_sections": m.group(2).count("—</p>") if m else None}
                if not ok:
                    status = 1
                    print(f'DOM BLOCKED {iss["tag"]}/{lang}/{layout}: drawn={drawn} ' + "; ".join(f'{h["gate_rule"]}:{h["match"]!r}' for h in g["banned"] + g["money_shares"] + g["voice"]), file=sys.stderr)
    print(f"DOM checks {sum(v['ok'] for v in report['dom'].values())}/{len(report['dom'])} · {time.time() - t0:.1f}s")
    for tag, lang, layout, h in (("W37", "ZH", "A", 6200), ("09-11", "EN", "B", 6600)):
        shot = out / f"_web_preview_{tag}_{lang}_{layout}.png"
        chrome([f"--window-size=1200,{h}", "--virtual-time-budget=6000", f"--screenshot={shot}",
                f"{render.as_uri()}#issue={tag}&lang={lang}&layout={layout}&theme=light"])
        print("SHOT", shot, shot.exists() and shot.stat().st_size)

    if a.skip_pdf:
        (out / "visual_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
        return status
    printable = out / "_print.html"
    printable.write_text(local_wrapper(page_html(data_json, local_fonts_css())))
    for old in out.glob("_preview_*.png"):
        old.unlink()
    blocked = out / "_blocked"
    for iss in issues:
        for lang in ("EN", "ZH"):
            t1 = time.time()
            final = out / f'Market_Recap_{iss["label"]}_{lang}.pdf'
            tmp = out / f'.partial_{iss["label"]}_{lang}.pdf'
            chrome(["--no-pdf-header-footer", f"--print-to-pdf={tmp}",
                    f'{printable.as_uri()}#issue={iss["tag"]}&lang={lang}&layout=A&print=1'], timeout=180)
            if not tmp.exists():
                status = 1
                print(f"PDF NOT PRODUCED {final.name}", file=sys.stderr)
                continue
            text = subprocess.run(["pdftotext", "-layout", str(tmp), "-"], capture_output=True, text=True, check=True).stdout
            g, pg, mg = run_gates(text), check_pages(text), check_margins(tmp, *PAGE_MARGIN_MM)
            bad = iss["_rules_check"][lang]
            ok = g["ok"] and pg["ok"] and mg["ok"] and not bad
            report["pdf"][f'{iss["label"]}/{lang}'] = {"ok": ok, "pages": pg["pages"], "body_lines": pg["body_lines"], "thin": pg["thin_pages"],
                                                        "margin_overflow": mg["count"], "banned": len(g["banned"]), "voice": len(g["voice"]),
                                                        "money": len(g["money_shares"]), "leadership_zh": g["leadership_zh"], "rules": bad,
                                                        "seconds": round(time.time() - t1, 1)}
            if ok:
                shutil.move(tmp, final)
                subprocess.run(["pdftoppm", "-r", "50", "-png", str(final), str(out / f'_preview_{iss["label"]}_{lang}')], check=False)
                print(f"DELIVERED {final} · pages {pg['pages']} {pg['body_lines']} · margins ok · {time.time() - t1:.1f}s")
            else:
                status = 1
                blocked.mkdir(exist_ok=True)
                if final.exists():
                    shutil.move(final, blocked / f"previous_{final.name}")
                shutil.move(tmp, blocked / final.name)
                print(f"PDF BLOCKED {final.name}: thin={pg['thin_pages']} margin_overflow={mg['count']} {mg['overflow'][:3]} "
                      f"banned={len(g['banned'])} voice={len(g['voice'])} money={len(g['money_shares'])} rules={bad}", file=sys.stderr)
    (out / "visual_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return status


def run_steps(argv=None) -> int:
    """Same checks as main(), one step per invocation so each stays short in the foreground.
    Only --step page writes recap_samples.html; dom/shots/pdf read the page already on disk."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--step", required=True, choices=["page", "dom", "shots", "pdf"])
    ap.add_argument("--only", default="", help="dom: TAG/LANG/LAYOUT · pdf: LABEL/LANG (default: all)")
    ap.add_argument("--chrome-timeout", type=int, default=90)
    a = ap.parse_args(argv)
    t0 = time.time()
    out = month_dir("2026-09-11", a.sample) / "visual"
    out.mkdir(parents=True, exist_ok=True)
    rep_path = out / "visual_report.json"
    try:
        report = json.loads(rep_path.read_text())
    except (OSError, ValueError):
        report = {}
    for k in ("page", "dom", "pdf", "shots"):
        report.setdefault(k, {})
    status = 0
    render, printable = out / "_render.html", out / "_print.html"

    if a.step == "page":
        issues = [issue_data(tag, label, a.sample) for tag, label in ISSUES]
        head_text = html_text(header_html())
        for iss in issues:
            for lang in ("ZH", "EN"):
                words = "\n".join(strings(unjoin([iss["V"][lang], iss["fig"][lang], CHROME_LABELS[lang], iss["when"][lang]])))
                g = run_gates(head_text + "\n" + words)
                bad = iss["_rules_check"][lang]
                ok = g["ok"] and not bad
                report["page"][f'{iss["tag"]}/{lang}'] = {"ok": ok, "rules": bad, "banned": len(g["banned"]), "voice": len(g["voice"]),
                                                         "money": len(g["money_shares"]), "leadership_zh": g["leadership_zh"]}
                if not ok:
                    status = 1
                    print(f'WORDS BLOCKED {iss["tag"]}/{lang}: {bad or ""} ' + "; ".join(f'{h["gate_rule"]}:{h["match"]!r}' for h in g["banned"] + g["money_shares"] + g["voice"]), file=sys.stderr)
        data = {"chrome": CHROME_LABELS, "issues": [{k: v for k, v in iss.items() if not k.startswith("_")} for iss in issues]}
        data_json = jdump(data)
        page = page_html(data_json, FONTS_LINK)
        longest, size = max(len(ln) for ln in page.splitlines()), len(page.encode())
        report["page_stats"] = {"bytes": size, "lines": page.count("\n"), "longest_line": longest}
        if longest > MAX_LINE or size > MAX_BYTES:
            status = 1
        (out / ("recap_samples.html" if status == 0 else "blocked_recap_samples.html")).write_text(page)
        render.write_text(local_wrapper(page))
        printable.write_text(local_wrapper(page_html(data_json, local_fonts_css())))
        print(f"PAGE status={status} · {size / 1024:.0f} KB · {page.count(chr(10))} lines · longest {longest} · {time.time() - t0:.1f}s")

    elif a.step == "dom":
        must = {"A": ('class="drop', 'class="chart"', 'class="votes', 'class="tell"'),
                "B": ('class="drop', 'class="chart"', 'class="votes', 'class="tell"', 'class="bpanel"')}
        combos = [(t, lg, ly) for t, _ in ISSUES for lg in ("ZH", "EN") for ly in ("A", "B")]
        if a.only:
            combos = [c for c in combos if "/".join(c) == a.only]
        for tag, lang, layout in combos:
            t1 = time.time()
            try:
                dom = chrome(["--dump-dom", f"{render.as_uri()}#issue={tag}&lang={lang}&layout={layout}"],
                             timeout=a.chrome_timeout).stdout
            except subprocess.TimeoutExpired:
                dom = ""
            m = re.search(r'<main id="app"[^>]*data-rendered="([^"]+)"[^>]*>(.*)</main>', dom, re.S)
            body = m.group(2) if m else ""
            drawn = bool(m) and m.group(1) == f"{tag}|{lang}|{layout}" and all(x in body for x in must[layout])
            g = run_gates(html_text(body))
            dashes = body.count("—</p>")
            ok = drawn and g["ok"] and dashes == 0
            report["dom"][f"{tag}/{lang}/{layout}"] = {"ok": ok, "drawn": drawn, "banned": len(g["banned"]), "voice": len(g["voice"]),
                                                      "money": len(g["money_shares"]), "leadership_zh": g["leadership_zh"], "dash_sections": dashes}
            status |= 0 if ok else 1
            print(f"DOM {tag}/{lang}/{layout} ok={ok} drawn={drawn} gates={g['ok']} dashes={dashes} · {time.time() - t1:.1f}s")

    elif a.step == "shots":
        for tag, lang, layout, h in (("W37", "ZH", "A", 6200), ("09-11", "EN", "B", 6600)):
            shot = out / f"_web_preview_{tag}_{lang}_{layout}.png"
            t1 = time.time()
            chrome([f"--window-size=1100,{h}", f"--screenshot={shot}",
                    f"{render.as_uri()}#issue={tag}&lang={lang}&layout={layout}&theme=light"], timeout=a.chrome_timeout)
            report["shots"][shot.name] = shot.exists() and shot.stat().st_size
            print("SHOT", shot, report["shots"][shot.name], f"{time.time() - t1:.1f}s")

    elif a.step == "pdf":
        labels = {label: tag for tag, label in ISSUES}
        combos = [(label, lg) for _, label in ISSUES for lg in ("EN", "ZH")]
        if a.only:
            combos = [c for c in combos if "/".join(c) == a.only]
        blocked = out / "_blocked"
        for label, lang in combos:
            t1 = time.time()
            weekly = "-W" in label
            D = week_sessions(label)[-1].isoformat() if weekly else label
            pdir = (month_dir(D, a.sample) / f"pack_{label}") if weekly else pack_dir(label, a.sample)
            rules = json.loads((pdir / f"content_{lang}.json").read_text()).get("rules")
            final = out / f"Market_Recap_{label}_{lang}.pdf"
            tmp = out / f".partial_{label}_{lang}.pdf"
            tmp.unlink(missing_ok=True)
            try:
                chrome(["--no-pdf-header-footer", f"--print-to-pdf={tmp}",
                        f"{printable.as_uri()}#issue={labels[label]}&lang={lang}&layout=A&print=1"], timeout=a.chrome_timeout)
            except subprocess.TimeoutExpired:
                pass
            if not tmp.exists():
                status = 1
                report["pdf"][f"{label}/{lang}"] = {"ok": False, "error": "not produced"}
                print(f"PDF NOT PRODUCED {final.name} · {time.time() - t1:.1f}s")
                continue
            text = subprocess.run(["pdftotext", "-layout", str(tmp), "-"], capture_output=True, text=True, check=True).stdout
            g, pg, mg = run_gates(text), check_pages(text), check_margins(tmp, *PAGE_MARGIN_MM)
            bad = check_rules(rules, lang, D)
            mixed = lang == "ZH" and "bull/bear" in text
            ok = g["ok"] and pg["ok"] and mg["ok"] and not bad and not mixed
            report["pdf"][f"{label}/{lang}"] = {"ok": ok, "pages": pg["pages"], "body_lines": pg["body_lines"], "thin": pg["thin_pages"],
                                                "margin_overflow": mg["count"], "banned": len(g["banned"]), "voice": len(g["voice"]),
                                                "money": len(g["money_shares"]), "leadership_zh": g["leadership_zh"], "rules": bad,
                                                "zh_mixed_bull_bear": mixed}
            if ok:
                shutil.move(tmp, final)
                for old in out.glob(f"_preview_{label}_{lang}-*.png"):
                    old.unlink()
                subprocess.run(["pdftoppm", "-r", "50", "-png", str(final), str(out / f"_preview_{label}_{lang}")], check=False)
            else:
                status = 1
                blocked.mkdir(exist_ok=True)
                shutil.move(tmp, blocked / final.name)
            print(f"PDF {final.name} ok={ok} pages={pg['pages']} thin={pg['thin_pages']} margin_overflow={mg['count']} "
                  f"{[o['word'] for o in mg['overflow'][:3]]} gates={g['ok']} rules={bad} mixed={mixed} · {time.time() - t1:.1f}s")

    # steps may run side by side: re-read and replace only this step's section so none is lost
    section = {"page": ("page", "page_stats"), "dom": ("dom",), "shots": ("shots",), "pdf": ("pdf",)}[a.step]
    try:
        latest = json.loads(rep_path.read_text())
    except (OSError, ValueError):
        latest = {}
    for key in section:
        if key in report:
            if isinstance(report[key], dict) and isinstance(latest.get(key), dict) and key != "page_stats":
                latest[key].update(report[key])
            else:
                latest[key] = report[key]
    rep_path.write_text(json.dumps(latest, ensure_ascii=False, indent=1))
    return status


if __name__ == "__main__":
    sys.exit(run_steps() if "--step" in sys.argv else main())
