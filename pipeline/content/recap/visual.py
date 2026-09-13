#!/usr/bin/env python3
"""Visual-line layout for the recap: data → one JS renderer → review page + A4 PDFs.

Library used by run.py (production) and, via --step, by the five-issue sample page.

  * Python gathers each issue's numbers (pack.json + origin/main archives as of the issue date) and the
    words (content_<LANG>.json) into one JSON document, formatted so no line exceeds 300 characters.
  * visual_assets/recap_page.js draws everything from that JSON — drop line, conditions chart, vote
    strip, bar panels, schematic — using the Visual line's CSS (recap_visual.css, verbatim) plus
    recap_local.css. Preview pages and PDFs come from the same JS; print mode drops the topic cards.
  * Headless Chrome runs with a fixed profile (~/.venvs/fluxus-recap/chrome-profile), one at a time;
    on timeout the whole process group is killed so no helper keeps the profile lock.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from pipeline.content.recap import pack_dir, month_dir
from pipeline.content.recap.build_pack import csv_rows, show
from pipeline.content.recap.constants import check_rules
from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.visual_figs import FIGS
from pipeline.content.recap.weeks import week_sessions
from pipeline.marketcal import is_trading_day

e = html.escape
ASSETS = Path(__file__).with_name("visual_assets")
FONT_DIR = Path.home() / ".venvs" / "fluxus-recap" / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_PROFILE = Path.home() / ".venvs" / "fluxus-recap" / "chrome-profile"
SAMPLE_ISSUES = [("W37", "2026-W37"), ("09-11", "2026-09-11"), ("09-10", "2026-09-10"), ("09-09", "2026-09-09"), ("09-08", "2026-09-08")]
MAX_LINE, MAX_BYTES = 300, 350 * 1024
PAGE_MARGIN_MM = (12.0, 12.0)  # left/right, must match @page in recap_local.css
FONTS_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600'
              '&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">')

CHROME_LABELS = {
    "EN": {"legend": ["counts for", "counts against", "inside its line", "not counted", "number = distance past each vote’s own line"],
           "units": {"ratio": "ratio", "names": "names", "points": "points", "warnings": "warnings", "": ""},
           "votes": "votes", "top3": "top 3 · bottom 3", "d1": "1 day", "w1": "1 week", "ll": "Leaders and Laggards",
           "rot_d": "Rotation · the session", "rot_w": "Rotation · the week", "board": "The Board",
           "b_votes": "Breadth votes", "b_cond": "Conditions", "b_led": "Led", "b_paid": "Paid",
           "pick_on_word": "chosen", "pick_off_word": "alternative",
           "schem": "Schematic — illustrates the concept, not price data.", "score": "Weekly Scorecard",
           "tape": "The Tape", "founders": "Founders Note", "sessions": "Session by session",
           "daily": "Daily Market Recap", "weekly": "Weekly Market Recap", "droparia": "SPX drop line, 21 sessions",
           "cond_aria": "Market Conditions score by session",
           "legal": "Nothing here is advice or a recommendation to buy or sell anything. Measure your own water.",
           "handle": "@Fluxus_Z", "site": "fluxus-capital.com",
           "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], "vlabels": {}},
    "ZH": {"legend": ["计入看多", "计入看空", "在线内", "未计入", "数字 = 离各自那条线的距离"],
           "units": {"ratio": "比值", "names": "只", "points": "点", "warnings": "条", "": ""},
           "votes": "票", "top3": "前 3 · 后 3", "d1": "1 日", "w1": "1 周", "ll": "领涨与落后",
           "rot_d": "轮动 · 当天", "rot_w": "轮动 · 本周", "board": "看板",
           "b_votes": "广度票板", "b_cond": "市场状况", "b_led": "领涨", "b_paid": "让位",
           "pick_on_word": "选用", "pick_off_word": "备选",
           "schem": "示意图——说明概念，不是真实价格。", "score": "周成绩单",
           "tape": "盘面", "founders": "Founders Note", "sessions": "逐日读数",
           "daily": "Daily Market Recap", "weekly": "Weekly Market Recap", "droparia": "SPX 掉落线，21 个交易日",
           "cond_aria": "市场状况分，逐日", "months": [f"{i}月" for i in range(1, 13)],
           "legal": "这里不给建议，也不劝人买卖。量好自己的水。",
           "handle": "@Fluxus_Z", "site": "fluxus-capital.com",
           "vlabels": {"5-day ratio": "5 日比", "10-day ratio": "10 日比", "Thrust": "推力", "Quarterly spread": "季度差",
                       "13%/34d spread": "13%/34 日差", "New highs vs lows": "新高对新低", "McClellan": "McClellan",
                       "% above 200-day": "站上 200 日线占比", "T2108 zone": "T2108 区间", "SPY warnings": "SPY 警示",
                       "QQQ warnings": "QQQ 警示", "Benchmark trend": "基准趋势"}},
}
CARD_WORDS = {"EN": ("chosen", "alternative"), "ZH": ("选用", "备选")}  # must never reach a member PDF


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


def pick_edu(education: dict, key: str) -> dict:
    """Content education block → what the page renders: the chosen option's title/body/figure + the cards."""
    opts = education.get("options") or []
    sel = next((o for o in opts if o.get("key") == key), None)
    if sel is None or not sel.get("body") or not sel.get("figure"):
        raise SystemExit(f"education option {key} is missing title/body/figure — see CONTENT_SCHEMA.md")
    return {"chosen": key, "title": sel["title"], "body": sel["body"], "figure": sel["figure"],
            "options": [{"key": o["key"], "title": o["title"], "why": o.get("why", "")} for o in opts]}


def issue_data(tag: str, label: str, pdir: Path, edu: str = "A") -> dict:
    weekly = "-W" in label
    D = week_sessions(label)[-1].isoformat() if weekly else label
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
            "led", "lagged", "sentiment", "tomorrow", "rules", "portfolio_note", "weekly_k_line", "labels")
    out["V"] = {}
    out["fig"] = {}
    for lang in ("EN", "ZH"):
        ed = pick_edu(content[lang]["education"], edu)
        out["V"][lang] = {**{k: content[lang].get(k) for k in keep}, "education": ed}
        out["fig"][lang] = FIGS[ed["figure"]](lang)
    out["_rules_check"] = {lang: check_rules(content[lang].get("rules"), lang, D) for lang in ("EN", "ZH")}
    out["_book_tickers"] = sorted({p[0] for p in (out["book"] or {}).get("pos", [])})
    return out


def public(iss: dict) -> dict:
    return {k: v for k, v in iss.items() if not k.startswith("_")}


# ------------------------------------------------------------------ page
def header_html(tags: list[str], layouts=("A", "B"), eyebrow="Fluxus Capital · Market Recap · 样张 · W37",
                h1="复盘样张 · Visual 版式",
                lede=("五期内容不变，换成 Visual 线 9/11 周刊的视觉系统。A 登记体、B 掉落体，中英各一套；",
                      "教育段加 A/B 选题，样张默认 A。")) -> str:
    issue_btns = "\n".join(f'      <button type="button" data-set="issue" data-val="{e(t)}" aria-pressed="{"true" if i == 0 else "false"}">{e(t)}</button>'
                           for i, t in enumerate(tags))
    layout_group = ""
    if len(layouts) > 1:
        names = {"A": "A · 登记体", "B": "B · 掉落体"}
        layout_group = ('    <div class="switch" role="group" aria-label="排版">\n' + "\n".join(
            f'      <button type="button" data-set="layout" data-val="{x}" aria-pressed="{"true" if i == 0 else "false"}">{names[x]}</button>'
            for i, x in enumerate(layouts)) + "\n    </div>\n")
    lede_html = "\n".join(f"    {e(x)}" for x in lede)
    return (f'<header class="top">\n  <p class="eyebrow">{e(eyebrow)}</p>\n  <h1>{e(h1)}</h1>\n  <p class="lede">\n{lede_html}\n  </p>\n'
            '  <div class="switches">\n    <div class="switch" role="group" aria-label="期数">\n' + issue_btns + "\n    </div>\n"
            '    <div class="switch" role="group" aria-label="语言">\n'
            '      <button type="button" data-set="lang" data-val="ZH" aria-pressed="true">中</button>\n'
            '      <button type="button" data-set="lang" data-val="EN" aria-pressed="false">EN</button>\n    </div>\n'
            + layout_group + "  </div>\n</header>")


def wrap_long_css(css: str) -> str:
    out = []
    for ln in css.splitlines():
        if len(ln) <= MAX_LINE:
            out.append(ln)
        else:
            out.extend(re.sub(r";\s*", ";\n  ", ln).splitlines())
    return "\n".join(out)


def page_html(data_json: str, fonts: str, header: str, title: str = "Fluxus Recap 样张") -> str:
    css = wrap_long_css((ASSETS / "recap_visual.css").read_text() + "\n" + (ASSETS / "recap_local.css").read_text())
    js = (ASSETS / "recap_page.js").read_text()
    return (f"<title>{e(title)}</title>\n{fonts}\n<style>\n{css}\n</style>\n{header}\n"
            '<main id="app">\n  <p class="prose">—</p>\n</main>\n'
            f'<script type="application/json" id="recap-data">\n{data_json}\n</script>\n<script>\n{js}\n</script>\n')


def page_shape(page: str) -> dict:
    longest, size = max(len(ln) for ln in page.splitlines()), len(page.encode())
    return {"bytes": size, "lines": page.count("\n"), "longest_line": longest, "ok": longest <= MAX_LINE and size <= MAX_BYTES}


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
def file_ready(path: Path, settle_s: float = 1.0):
    """done() for chrome(): the output file exists, is non-empty and its size held for settle_s."""
    last = {"size": -1, "since": 0.0}

    def done(_stdout: str) -> bool:
        if not path.exists():
            return False
        size, now = path.stat().st_size, time.time()
        if size > 0 and size == last["size"]:
            return now - last["since"] >= settle_s
        last["size"], last["since"] = size, now
        return False
    return done


def chrome(args: list[str], timeout: int = 120, done=None) -> subprocess.CompletedProcess:
    """One headless Chrome run on the fixed profile (~/.venvs/fluxus-recap/chrome-profile), never two at once.

    Measured 2026-09-13: with any --user-data-dir (fresh temp dir or this fixed one) Chrome writes its output —
    a complete screenshot, a complete PDF, the full DOM on stdout — and then does not exit; every run sat until
    the 90 s cap. So the caller passes `done`, the run ends as soon as the output is complete, and the whole
    process group is killed (a killed parent alone leaves helpers holding the profile lock, which is what made
    the following runs hang in the earlier attempts)."""
    import threading

    CHROME_PROFILE.mkdir(parents=True, exist_ok=True)
    args = [x for x in args if not x.startswith("--virtual-time-budget")]
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
           f"--user-data-dir={CHROME_PROFILE}", "--virtual-time-budget=8000", *args]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    buf: list[str] = []
    reader = threading.Thread(target=lambda: buf.extend(iter(p.stdout.readline, "")), daemon=True)
    reader.start()
    t0 = time.time()
    try:
        while p.poll() is None:
            if done is not None and done("".join(buf)):
                break
            if time.time() - t0 > timeout:
                raise subprocess.TimeoutExpired(cmd, timeout)
            time.sleep(0.25)
    finally:
        if p.poll() is None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        p.wait()
        reader.join(timeout=2)
    return subprocess.CompletedProcess(cmd, p.returncode, "".join(buf), "")


DRAWN = {"A": ('class="drop', 'class="chart"', 'class="votes', 'class="tell"'),
         "B": ('class="drop', 'class="chart"', 'class="votes', 'class="tell"', 'class="bpanel"')}


def check_dom(url: str, expect: str, layout: str, timeout: int = 90) -> dict:
    try:
        dom = chrome(["--dump-dom", url], timeout=timeout, done=lambda out: "</html>" in out).stdout
    except subprocess.TimeoutExpired:
        dom = ""
    m = re.search(r'<main id="app"[^>]*data-rendered="([^"]+)"[^>]*>(.*)</main>', dom, re.S)
    body = m.group(2) if m else ""
    drawn = bool(m) and m.group(1) == expect and all(x in body for x in DRAWN[layout])
    g = run_gates(html_text(body))
    dashes = body.count("—</p>")
    from pipeline.content.recap.figlayout import check_svg_labels
    f1 = check_svg_labels(body)  # F1: no two schematic labels overlap in the SVG Chrome drew
    return {"ok": drawn and g["ok"] and dashes == 0 and f1["ok"], "drawn": drawn, "banned": len(g["banned"]), "voice": len(g["voice"]),
            "money": len(g["money_shares"]), "leadership_zh": g["leadership_zh"], "dash_sections": dashes,
            "f1_overlaps": f1["overlaps"]}


def print_pdf(url: str, out: Path, timeout: int = 90) -> bool:
    out.unlink(missing_ok=True)
    try:
        chrome(["--no-pdf-header-footer", f"--print-to-pdf={out}", url], timeout=timeout, done=file_ready(out))
    except subprocess.TimeoutExpired:
        return False
    return out.exists() and out.stat().st_size > 0


# ------------------------------------------------------------------ five-issue sample page (review only)
def run_steps(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True, choices=["page", "dom"])
    ap.add_argument("--chrome-timeout", type=int, default=90)
    a = ap.parse_args(argv)
    out = month_dir("2026-09-11", True) / "visual"
    out.mkdir(parents=True, exist_ok=True)
    render = out / "_render.html"
    status = 0
    if a.step == "page":
        issues = [issue_data(tag, label, pack_dir(label, True)) for tag, label in SAMPLE_ISSUES]
        data = {"chrome": CHROME_LABELS, "layouts": ["A", "B"], "store_key": "fluxusRecapSamplesW37", "issues": [public(i) for i in issues]}
        page = page_html(jdump(data), FONTS_LINK, header_html([t for t, _ in SAMPLE_ISSUES]))
        shape = page_shape(page)
        status = 0 if shape["ok"] else 1
        (out / ("recap_samples.html" if status == 0 else "blocked_recap_samples.html")).write_text(page)
        render.write_text(local_wrapper(page))
        print("PAGE", shape)
    else:
        for tag, _ in SAMPLE_ISSUES:
            for lang in ("ZH", "EN"):
                for layout in ("A", "B"):
                    r = check_dom(f"{render.as_uri()}#issue={tag}&lang={lang}&layout={layout}", f"{tag}|{lang}|{layout}", layout, a.chrome_timeout)
                    status |= 0 if r["ok"] else 1
                    print("DOM", tag, lang, layout, r)
    return status


if __name__ == "__main__":
    sys.exit(run_steps())
