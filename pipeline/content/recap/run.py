#!/usr/bin/env python3
"""Production entry for the daily / weekly market recap.

    python3 -m pipeline.content.recap.run fetch      --date 2026-09-14 | --week 2026-W38 [--video-id ID]
    python3 -m pipeline.content.recap.run check      --date … | --week …   [--from-samples]
    ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.run render --date … | --week … [--edu B] [--from-samples]
    python3 -m pipeline.content.recap.run ledger-add --date … | --week …   [--from-samples] [--from-content]

Writing content_EN.json / content_ZH.json is the scheduled session's job — see CONTENT_SCHEMA.md.
Production renders layout A only; education defaults to option A, `--edu B` re-renders from the same files.

Output per issue (never in git):
    RECAP_ROOT/YYYY-MM/<issue>/
      pdf/Market_Recap_<issue>_{EN,ZH}.pdf   member PDFs (no topic cards)
      img/{EN,ZH}/p1.png … pN.png            every page, 1460 px wide (≤ 5 MB each, else .jpg q90)
      x/img1–img4 (EN p1–p4), post_EN.md, post_ZH.md
      pack/  pack.json, transcript.md, content_{EN,ZH}.json, content.json, preview/print HTML
      preview.html · delivery.md · render_state.json · check.json
Checks before printing: rules (7, fixed rule 7 opening, no 09-04 repeat) · R1 topic ledger · R2 same-week text.
Checks on every PDF: gates (names, 领导力, $/shares, Andy, first person) · page fill · type area · ZH has no
bull/bear · no topic cards · X1 pages 1–4 carry no book · X2 at least 4 pages. DOM of the preview is gated too.
`--from-samples` reads content from samples/pack_<issue>/ (the five 2026-09 samples) and writes the same layout.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from pipeline.content.recap import dedupe, issue_dir, last_session, pack_dir
from pipeline.content.recap import visual as vis
from pipeline.content.recap.constants import check_rules
from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.pages import (check_layout, check_margins, check_pages, check_state_row, check_true_size_pdf, check_x_pages,
                                          page_sections)
from pipeline.content.recap.weeks import week_label, week_sessions

IMG_WIDTH = 1460
IMG_MAX_BYTES = 5 * 1024 * 1024


class Issue:
    def __init__(self, label: str, from_samples: bool = False):
        self.label = label
        self.weekly = "-W" in label
        self.T = last_session(label)
        self.tag = label.split("-", 1)[1] if self.weekly else label[5:]
        self.from_samples = from_samples
        self.src = pack_dir(label, sample=from_samples)
        self.dir = issue_dir(label)
        self.pack = self.dir / "pack"

    def contents(self) -> dict:
        return {lang: json.loads((self.src / f"content_{lang}.json").read_text()) for lang in ("EN", "ZH")}


def label_of(a) -> str:
    return a.week if a.week else a.date


# ------------------------------------------------------------------ fetch
def cmd_fetch(a) -> int:
    from pipeline.content.recap import build_pack, fetch_transcript as ft
    iss = Issue(label_of(a))
    iss.pack.mkdir(parents=True, exist_ok=True)
    if not iss.weekly:
        args = ["--date", iss.T] + (["--video-id", a.video_id] if a.video_id else [])
        rc = ft.main(args)
        if rc not in (0, 3):
            return rc
        return build_pack.main(["--date", iss.T])
    vid = a.video_id
    if not vid:
        end = (dt.date.fromisoformat(iss.T) + dt.timedelta(days=3)).isoformat().replace("-", "")
        for ent in ft.list_channel(20):
            if re.search(r"weekend", ent.get("title", ""), re.I):
                ud = ft.upload_date_of(ent["id"])
                if ud and iss.T.replace("-", "") < ud <= end:
                    vid = ent["id"]
                    break
    if vid:
        vtt = ft.download_vtt(vid, iss.pack)
        paras = ft.dedupe_vtt(vtt.read_text(encoding="utf-8"))
        meta = {"id": vid, "title": "", "duration": None, "upload_date": ft.upload_date_of(vid), "date": iss.label}
        (iss.pack / "transcript.md").write_text(ft.to_markdown(paras, meta), encoding="utf-8")
    else:
        print(f"[no-weekend-video] none found for {iss.label}", file=sys.stderr)
    return build_pack.main(["--week", iss.label])


# ------------------------------------------------------------------ check (R1, R2, rules)
def merged_options(contents: dict) -> list[dict]:
    en = {o["key"]: o for o in contents["EN"]["education"]["options"]}
    zh = {o["key"]: o for o in contents["ZH"]["education"]["options"]}
    return [{"key": k, "concept": en[k].get("concept") or zh[k].get("concept"), "title_en": en[k]["title"], "title_zh": zh[k]["title"]}
            for k in sorted(set(en) & set(zh))]


def week_priors(iss: Issue) -> list[tuple[str, bool, dict]]:
    dates = [d.isoformat() for d in week_sessions(week_label(dt.date.fromisoformat(iss.T)))]
    if not iss.weekly:
        dates = [d for d in dates if d < iss.T]
    out = []
    for d in dates:
        src = pack_dir(d, sample=iss.from_samples)
        files = [src / f"content_{lang}.json" for lang in ("EN", "ZH")]
        if all(f.exists() for f in files):
            out.append((d, False, {lang: json.loads(f.read_text()) for lang, f in zip(("EN", "ZH"), files)}))
    return out


def run_check(iss: Issue) -> dict:
    contents = iss.contents()
    rules = {lang: check_rules(contents[lang].get("rules"), lang, iss.T) for lang in ("EN", "ZH")}
    ledger = dedupe.seed()
    week_dates = [d.isoformat() for d in week_sessions(iss.label)] if iss.weekly else []
    r1 = dedupe.r1(iss.label, iss.T, iss.weekly, merged_options(contents), ledger, week_dates)
    r2 = dedupe.r2(contents, iss.weekly, week_priors(iss))
    from pipeline.content.recap.wording import w1_hits
    w1 = w1_hits(contents["EN"])
    rep = {"issue": iss.label, "rules": rules, "r1": r1, "r2": r2, "w1": w1,
           "ok": not any(rules.values()) and not r1 and not r2 and not w1}
    iss.dir.mkdir(parents=True, exist_ok=True)
    (iss.dir / "check.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    return rep


def print_check(rep: dict) -> None:
    print(f"CHECK {rep['issue']} ok={rep['ok']}")
    for lang, bad in rep["rules"].items():
        if bad:
            print(f"  rules {lang}: {bad}")
    for h in rep["r1"]:
        print(f"  R1 option {h['option']} ({h['concept']}, {h['title_en']!r}) vs {h['vs']['issue']} {h['vs']['concept']} "
              f"{h['vs']['title_en']!r}: {', '.join(h['why'])}")
    for h in rep["r2"]:
        print(f"  R2 {h['lang']} {h['item']} ~ {h['vs_issue']} {h['vs_item']} = {h['similarity']} (≥{h['threshold']}): {h['text'][:70]!r}")
    for h in rep.get("w1", []):
        print(f"  W1 {h['matches']} in {h['text'][:80]!r}")


def cmd_check(a) -> int:
    rep = run_check(Issue(label_of(a), a.from_samples))
    print_check(rep)
    return 0 if rep["ok"] else 2


# ------------------------------------------------------------------ render
def copy_pack(iss: Issue) -> None:
    iss.pack.mkdir(parents=True, exist_ok=True)
    if iss.src.resolve() != iss.pack.resolve():
        for name in ("pack.json", "transcript.md", "content_EN.json", "content_ZH.json"):
            if (iss.src / name).exists():
                shutil.copy2(iss.src / name, iss.pack / name)
    c = {lang: json.loads((iss.pack / f"content_{lang}.json").read_text()) for lang in ("EN", "ZH")}
    (iss.pack / "content.json").write_text(json.dumps(c, ensure_ascii=False, indent=1))


def to_images(pdf: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in list(out_dir.glob("p*.png")) + list(out_dir.glob("p*.jpg")) + list(out_dir.glob("_raw-*.png")):
        old.unlink()
    subprocess.run(["pdftoppm", "-png", "-scale-to-x", str(IMG_WIDTH), "-scale-to-y", "-1", str(pdf), str(out_dir / "_raw")], check=True)
    made = []
    for raw in sorted(out_dir.glob("_raw-*.png"), key=lambda p: int(p.stem.split("-")[-1])):
        n = int(raw.stem.split("-")[-1])
        dst = out_dir / f"p{n}.png"
        raw.rename(dst)
        if dst.stat().st_size > IMG_MAX_BYTES:
            from PIL import Image
            jpg = dst.with_suffix(".jpg")
            Image.open(dst).convert("RGB").save(jpg, quality=90)
            dst.unlink()
            dst = jpg
        made.append(dst)
    return made


def headings(content: dict, weekly: bool) -> list[tuple[str, str]]:
    L, V = content["labels"], vis.CHROME_LABELS[content["lang"]]
    pairs = [("title", content["title"]), ("big_picture", L["big_picture"]), ("index_action", L["index_action"])]
    if weekly:
        pairs.append(("scorecard", V["score"]))
    pairs += [("market_state", L["market_state"])]
    if weekly:
        pairs.append(("sessions", V["sessions"]))
    pairs += [("conditions", L["conditions"]), ("leaders_laggards", V["ll"]), ("working", L["working"]), ("laggards", L["laggards"])]
    if weekly:
        pairs.append(("weekly_k", L["weekly_k"]))
    if content.get("sentiment"):
        pairs.append(("sentiment", L["sentiment"]))
    pairs += [("tomorrow", L["tomorrow"]), ("rules", L["rules"]), ("education", L["education"]), ("portfolio", L["portfolio"])]
    if content.get("founders_note"):
        pairs.append(("founders_note", V["founders"]))
    return pairs


def cmd_render(a) -> int:
    t0 = time.time()
    iss = Issue(label_of(a), a.from_samples)
    rep = run_check(iss)
    print_check(rep)
    state = {"issue": iss.label, "edu": a.edu, "ok": False, "check": rep["ok"], "pdf": {}, "dom": {}, "images": {}, "page_map": {}}
    if not rep["ok"]:
        write_delivery(iss, state, rep)
        return 2
    copy_pack(iss)
    from pipeline.content.recap.wording import week_weak_review
    tr = iss.pack / "transcript.md"
    state["week_weak"] = week_weak_review(json.loads((iss.pack / "content_EN.json").read_text()),
                                          tr.read_text() if tr.exists() else None)
    state["week_weak"]["transcript_present"] = tr.exists()
    data_issue = vis.issue_data(iss.tag, iss.label, iss.pack, a.edu)
    data = {"chrome": vis.CHROME_LABELS, "layouts": ["A"], "store_key": f"fluxusRecap-{iss.label}", "issues": [vis.public(data_issue)]}
    data_json = vis.jdump(data)
    header = vis.header_html([iss.tag], ("A",), eyebrow=f"Fluxus Capital · Market Recap · 预览 · {iss.label}",
                             h1=f"复盘预览 · {iss.label}",
                             lede=("会员版 PDF 只出 A 登记体，不含选题卡；本页保留选题卡供审阅。",
                                   f"当前教育段：选项 {a.edu}。"))
    page = vis.page_html(data_json, vis.FONTS_LINK, header, title=f"Fluxus Recap {iss.label}")
    shape = vis.page_shape(page)
    state["page"] = shape
    (iss.dir / "preview.html").write_text(page)
    render_html = iss.pack / "_render.html"
    render_html.write_text(vis.local_wrapper(page))
    print_html = iss.pack / "_print.html"
    print_html.write_text(vis.local_wrapper(vis.page_html(data_json, vis.local_fonts_css(), header)))
    status = 0 if shape["ok"] else 1

    for lang in ("ZH", "EN"):
        r = vis.check_dom(f"{render_html.as_uri()}#issue={iss.tag}&lang={lang}&layout=A", f"{iss.tag}|{lang}|A", "A", a.chrome_timeout)
        state["dom"][lang] = r
        status |= 0 if r["ok"] else 1
        print(f"DOM {lang} {r}")

    pdf_dir, blocked = iss.dir / "pdf", iss.dir / "_blocked"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for lang in ("EN", "ZH"):
        t1 = time.time()
        final = pdf_dir / f"Market_Recap_{iss.label}_{lang}.pdf"
        tmp = pdf_dir / f".partial_{lang}.pdf"
        if not vis.print_pdf(f"{print_html.as_uri()}#issue={iss.tag}&lang={lang}&layout=A&print=1", tmp, a.chrome_timeout):
            state["pdf"][lang] = {"ok": False, "error": "not produced"}
            status = 1
            print(f"PDF {lang} NOT PRODUCED")
            continue
        text = subprocess.run(["pdftotext", "-layout", str(tmp), "-"], capture_output=True, text=True, check=True).stdout
        content = data_issue["V"][lang]
        g, pg, mg = run_gates(text), check_pages(text), check_margins(tmp, *vis.PAGE_MARGIN_MM)
        l2 = check_true_size_pdf(tmp, lang)  # L2: glyph font sizes read from the PDF, not line boxes
        # X (Andy 09-13「周复盘不发X, X一致对外用英文版本」): only daily EN pages 1–4 go to X
        x_applies = not iss.weekly and lang == "EN"
        xg = check_x_pages(text, lang, data_issue["_book_tickers"]) if x_applies else {"ok": True, "x1_hits": {}, "x2_ok": None}
        squash = re.sub(r"\s+", "", text)
        other = [o["title"] for o in content["education"]["options"] if o["key"] != a.edu]
        cards = [w for w in vis.CARD_WORDS[lang] if f"·{w}" in squash] + [t for t in other if re.sub(r"\s+", "", t) in squash]
        mixed = lang == "ZH" and "bull/bear" in text
        bad_rules = data_issue["_rules_check"][lang]
        hmap = headings(content, iss.weekly)
        sections = page_sections(text, [h for _, h in hmap])
        name_of = {h: k for k, h in hmap}
        # L1 (Andy 09-13, final): everything but the lesson and the book fits in the first 4 pages, the book
        # owns the last page, the lesson may spill onto page 5, and no page opens mid-sentence
        book_h = content["labels"]["portfolio"]
        edu_h = next((h for k, h in hmap if k == "education"), "")
        l1 = check_layout(text, sections, edu_h, book_h, iss.weekly)
        l3 = check_state_row(text)  # L3: the state row may not break across pages
        layout_ok = l1["ok"] and l3["ok"]
        ok = g["ok"] and pg["ok"] and mg["ok"] and xg["ok"] and not cards and not mixed and not bad_rules and layout_ok and l2["ok"]
        if not iss.weekly:  # the page → section table is for dailies (checks the book sits on its own page)
            state["page_map"][lang] = [[name_of.get(h, h) for h in sec] for sec in sections]
        state["pdf"][lang] = {"ok": ok, "path": str(final), "pages": pg["pages"], "thin": pg["thin_pages"], "margin_overflow": mg["count"],
                              "gates": {"banned": len(g["banned"]), "leadership_zh": g["leadership_zh"], "money": len(g["money_shares"]),
                                        "voice": len(g["voice"])},
                              "x1_hits": xg["x1_hits"], "x2_ok": xg["x2_ok"], "cards_leaked": cards, "zh_mixed": mixed, "rules": bad_rules,
                              "layout_ok": layout_ok, "l1": l1, "l2": l2, "l3": l3,
                              "seconds": round(time.time() - t1, 1)}
        print(f"PDF {lang} ok={ok} L1={l1['ok']}{'' if l1['ok'] else ' ' + str(l1['hits'])} L3={l3['ok']}{'' if l3['ok'] else ' ' + str(l3['split'] or 'row missing')} edu_p={l1['edu_pages']} L2 body={l2['body_pt']} table={l2['table_pt']} {'ok' if l2['ok'] else 'RED ' + '; '.join(l2['hits'])} pages={pg['pages']} thin={pg['thin_pages']} margins={mg['count']} x1={xg['x1_hits']} "
              f"x2={xg['x2_ok']} cards={cards} gates={g['ok']} · {time.time() - t1:.1f}s")
        if ok:
            shutil.move(tmp, final)
            imgs = to_images(final, iss.dir / "img" / lang)
            state["images"][lang] = [{"file": str(p.relative_to(iss.dir)), "bytes": p.stat().st_size} for p in imgs]
        else:
            status = 1
            blocked.mkdir(exist_ok=True)
            shutil.move(tmp, blocked / final.name)

    if iss.weekly and (iss.dir / "x").exists():
        shutil.rmtree(iss.dir / "x")
    if state["images"].get("EN") and not iss.weekly:
        xdir = iss.dir / "x"
        xdir.mkdir(parents=True, exist_ok=True)
        for old in list(xdir.glob("img*.png")) + list(xdir.glob("img*.jpg")):
            old.unlink()
        for i, rec in enumerate(state["images"]["EN"][:4], start=1):
            src = iss.dir / rec["file"]
            shutil.copy2(src, xdir / f"img{i}{src.suffix}")
        zh_post = xdir / "post_ZH.md"
        if zh_post.exists() and zh_post.stat().st_size == 0:
            zh_post.unlink()
    if not iss.weekly and state["pdf"].get("EN", {}).get("ok"):
        from pipeline.content.recap import xpost
        c_en = json.loads((iss.pack / "content_EN.json").read_text())
        post = xpost.compose(c_en)
        r1 = xpost.p1(post["text"], c_en)
        r2 = xpost.p2(post["lead"], c_en.get("big_picture"))
        r3 = xpost.p3(post["cashtags"], c_en)
        state["x_post"] = {"source": post["source"], "lead": post["lead"], "why": post["why"], "text": post["text"],
                           "p1": r1, "p2": r2, "p3": r3}
        xdir = iss.dir / "x"
        xdir.mkdir(parents=True, exist_ok=True)
        good = r1["ok"] and r2["ok"] and r3["ok"]
        (xdir / ("post_EN.md" if good else "post_EN.blocked.md")).write_text(xpost.to_markdown(iss.label, post, r1, r2, r3))
        if (xdir / ("post_EN.blocked.md" if good else "post_EN.md")).exists():
            (xdir / ("post_EN.blocked.md" if good else "post_EN.md")).unlink()
        print("X POST", r1["chars"], "P1", r1["ok"], r1["hits"], "P2", r2, "P3", r3, "lead", "omitted" if not post["lead"] else "kept")
        status |= 0 if good else 1
    state["ok"] = status == 0
    if state["ok"] and blocked.exists():
        shutil.rmtree(blocked)  # a passing render supersedes earlier blocked attempts
    state["chosen"] = {"key": a.edu, **{f"title_{lang.lower()}": data_issue["V"][lang]["education"]["title"] for lang in ("EN", "ZH")},
                       "concept": next(o["concept"] for o in iss.contents()["EN"]["education"]["options"] if o["key"] == a.edu)}
    state["seconds"] = round(time.time() - t0, 1)
    (iss.dir / "render_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1))
    write_delivery(iss, state, rep)
    print(f"RENDER {iss.label} ok={state['ok']} · {state['seconds']}s → {iss.dir}")
    return status


def write_delivery(iss: Issue, state: dict, rep: dict) -> None:
    contents = iss.contents()
    lines = [f"# 交付说明 · {iss.label}", ""]
    lines.append(f"- 状态：{'通过，已出片' if state.get('ok') else '未通过，未交付'} · 教育段选项 {state.get('edu', 'A')}（默认 A，`--edu B` 可重出）")
    lines.append("")
    lines.append("## 教育选题")
    zh = {o["key"]: o for o in contents["ZH"]["education"]["options"]}
    en = {o["key"]: o for o in contents["EN"]["education"]["options"]}
    for k in sorted(zh):
        lines.append(f"- **{k}** {zh[k]['title']} / {en[k]['title']} · `{zh[k].get('concept')}` — {zh[k].get('why', '')}")
    lines.append("")
    lines.append("## 重复检查")
    lines.append(f"- R1 教育选题台账：{'通过' if not rep['r1'] else '报红'}")
    for h in rep["r1"]:
        lines.append(f"  - 选项 {h['option']} `{h['concept']}` 撞 {h['vs']['issue']} `{h['vs']['concept']}`：{', '.join(h['why'])}")
    lines.append(f"- R2 同周文本：{'通过' if not rep['r2'] else '报红'}")
    for h in rep["r2"]:
        lines.append(f"  - {h['lang']} {h['item']} ≈ {h['vs_issue']} {h['vs_item']}（{h['similarity']} ≥ {h['threshold']}）")
    bad_rules = {k: v for k, v in rep["rules"].items() if v}
    lines.append(f"- 纪律格式：{'通过' if not bad_rules else bad_rules}")
    lines.append(f"- W1 week 缩写：{'通过' if not rep.get('w1') else '报红'}")
    for h in rep.get("w1", []):
        lines.append(f"  - {h['matches']}：{h['text']}")
    ww = state.get("week_weak")
    if ww:
        lines.append("")
        lines.append("## week / weak 人工扫一眼（字幕会把两个词听混）")
        if not ww.get("transcript_present"):
            lines.append("- 本期材料包没有字幕文件，无法比对来源")
        lines.append(f"- 字幕里含 week/weak 的句子：{ww['transcript_week_weak']} 条；正文里含 week/weak 的句子：{len(ww['content'])} 条"
                     f"（其中与字幕句子接近的 {sum(r['from_transcript'] for r in ww['content'])} 条，标 ★）")
        for r in ww["content"]:
            lines.append(f"  - {'★ ' if r['from_transcript'] else ''}{r['text']}")
    if state.get("pdf"):
        lines.append("")
        lines.append("## PDF 与图片")
        for lang, p in state["pdf"].items():
            lines.append(f"- {lang}：{'通过' if p.get('ok') else '拦截'} · {p.get('pages', '—')} 页 · `{p.get('path', '')}`")
        jpgs = [r["file"] for recs in state.get("images", {}).values() for r in recs if r["file"].endswith(".jpg")]
        lines.append(f"- 图片宽 {IMG_WIDTH}px；超过 5MB 改 JPG 的：{', '.join(jpgs) if jpgs else '无'}")
        lines.append("- X 配图：`x/img1–img4` = 英文版第 1–4 页")
    xp = state.get("x_post")
    if xp:
        from pipeline.content.recap.xpost import LIMIT, P2_MAX
        lines.append("")
        lines.append("## X 长帖（EN，`x/post_EN.md`：结构句 + Big Picture 全文 + cashtag）")
        lines.append(f"- {xp['p1']['chars']}/{LIMIT} 字符 · lead {'省略' if not xp['lead'] else '保留'}：{xp['why']} · 来源 {xp['source']}")
        p2 = xp["p2"]
        lines.append(f"- P1 {'通过' if xp['p1']['ok'] else '报红：' + '；'.join(xp['p1']['hits'])} · P2 "
                     + ("不适用（lead 为空）" if p2["similarity"] is None else f"{'通过' if p2['ok'] else '报红'}（相似度 {p2['similarity']}，红线 {P2_MAX}）")
                     + (f" · P3 {'通过' if xp['p3']['ok'] else '报红：复盘里没有 ' + '、'.join(xp['p3']['missing'])}" if xp.get("p3") else ""))
    if state.get("page_map"):
        lines.append("")
        lines.append("## 每页对应的节（该页开始的节；空 = 续上一页）")
        for lang, pages in state["page_map"].items():
            lines.append(f"- {lang}：" + " · ".join(f"p{i + 1} {'/'.join(s) or '（续）'}" for i, s in enumerate(pages)))
    lines.append("")
    iss.dir.mkdir(parents=True, exist_ok=True)
    (iss.dir / "delivery.md").write_text("\n".join(lines))


# ------------------------------------------------------------------ ledger
def cmd_ledger_add(a) -> int:
    iss = Issue(label_of(a), a.from_samples)
    if a.from_content:
        opts = merged_options(iss.contents())
        key = iss.contents()["EN"]["education"].get("chosen", "A")
        o = next(x for x in opts if x["key"] == key)
        entry = {"date": iss.T, "issue": iss.label, "key": key, "title_zh": o["title_zh"], "title_en": o["title_en"], "concept": o["concept"]}
    else:
        sp = iss.dir / "render_state.json"
        if not sp.exists():
            print("no render_state.json — render first (or --from-content)", file=sys.stderr)
            return 2
        st = json.loads(sp.read_text())
        if not st.get("ok"):
            print("last render did not pass — nothing written to the ledger", file=sys.stderr)
            return 2
        c = st["chosen"]
        entry = {"date": iss.T, "issue": iss.label, "key": c["key"], "title_zh": c["title_zh"], "title_en": c["title_en"], "concept": c["concept"]}
    dedupe.add_entry(entry)
    print("LEDGER +", json.dumps(entry, ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="recap")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--date")
        g.add_argument("--week")
        p.add_argument("--from-samples", action="store_true")
        return p

    p = common(sub.add_parser("fetch"))
    p.add_argument("--video-id")
    common(sub.add_parser("check"))
    p = common(sub.add_parser("render"))
    p.add_argument("--edu", choices=["A", "B"], default="A")
    p.add_argument("--chrome-timeout", type=int, default=90)
    p = common(sub.add_parser("ledger-add"))
    p.add_argument("--from-content", action="store_true")
    a = ap.parse_args(argv)
    return {"fetch": cmd_fetch, "check": cmd_check, "render": cmd_render, "ledger-add": cmd_ledger_add}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
