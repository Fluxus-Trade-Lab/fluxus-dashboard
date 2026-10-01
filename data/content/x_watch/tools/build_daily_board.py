#!/usr/bin/env python3
"""X 日调研七节日报 → kanban-page 标准看板（Andy 2026-10-01 定的默认页面形态）。

用法:
    python3 build_daily_board.py data/content/x_watch/daily/<ET 日>.md [out.html] [--check]

- 只用标准库；样式/脚本/结构来自同目录 daily_board_template.html（kanban-page 模板的 CSS 原样 +
  一个通用列渲染），本脚本只生成 `<script type="application/json" id="data">` 那块。
- 节按关键词认（「蹭位」「候选」「别追」「走势」「墙后」「选题」「圈内」「Steve」），
  阿拉伯数字 / 中文数字 / 「——」「：」各种写法都认；**认不出的节照样出一列（通用渲染），不丢**。
- 卡面＝要点（CSS 截三行），卡背＝该条原文全文（表格行逐字段、列表逐条、链接可点）。
- `--check` 打印每节 md 条目数 vs 卡片数，并做逐行覆盖核对（md 每一行正文都必须出现在 JSON 里）。
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "daily_board_template.html"

# ── 列定义：顺序＝页面从左到右。key 用来认 H2 标题；认不出的节追加在「给 Steve」之前。 ──
COLUMNS = [
    # (id, 关键词正则, 列名, lucide 图标)
    ("spot", r"蹭位", "蹭位榜 · 回复方向", "message-circle-reply"),
    ("cand", r"候选|还没跑", "明天的候选", "crosshair"),
    ("done", r"别追|已经跑完", "已经跑完 · 别追", "ban"),
    ("trend", r"走势", "接下来的走势", "trending-up"),
    ("wall", r"墙后|jfsrev", "Jeff 墙后 vs 墙外", "lock"),
    ("topic", r"选题", "选题候选（发 X 用）", "pen-line"),
    ("chat", r"圈内", "圈内人在聊什么", "messages-square"),
    ("steve", r"Steve", "给 Steve · 回执 · 收工", "wrench"),
]
FOOTER_PREFIX = re.compile(r"^(本窗口|窗口[:：]|mood[:：]|看板[:：]|名单[:：]|stance[:：]|落盘并集)")
NUM_HEAD = re.compile(r"^\*\*\s*(\d+)\s*[·（(]")  # **1 · …** / **1（第 2 次）…**

# ───────────────────────────── markdown 小工具 ─────────────────────────────
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def links_of(s: str) -> list[dict]:
    out = []
    for t, u in LINK.findall(s):
        t = plain(t) or u
        if u.startswith("http"):
            out.append({"text": t, "href": u})
        else:  # 仓库相对路径：留文字，不给假链接
            out.append({"text": t, "href": None, "path": u})
    return out


def plain(s: str) -> str:
    s = LINK.sub(lambda m: m.group(1), s)
    s = re.sub(r"</?(details|summary)>", "", s)
    s = s.replace("**", "").replace("`", "")
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)\*(?!\w)", r"\1", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # 单元格里可能有转义的 \|
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


def is_sep(line: str) -> bool:
    return bool(re.match(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", line.strip()))


# ───────────────────────────── 分块 ─────────────────────────────
def blocks_of(lines: list[str]) -> list[dict]:
    """把一节正文切成块：h3 / table / list / para / quote / details。hr 丢掉（无内容）。"""
    out: list[dict] = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s or re.match(r"^-{3,}$|^\*{3,}$", s):
            i += 1
            continue
        if s.startswith("<details"):
            body = []
            if re.sub(r"<details>|<summary>.*?</summary>", "", s).strip():
                body.append(re.sub(r"<details>|<summary>.*?</summary>", "", s))
            summ = re.search(r"<summary>(.*?)</summary>", s)
            i += 1
            while i < n and "</details>" not in lines[i]:
                body.append(lines[i])
                i += 1
            if i < n:
                tail = lines[i].replace("</details>", "").strip()
                if tail:
                    body.append(tail)
                i += 1
            out.append({"type": "details", "summary": plain(summ.group(1)) if summ else "", "lines": body})
            continue
        if re.match(r"^#{3,6}\s", s):
            out.append({"type": "h3", "text": s.lstrip("#").strip(), "raw": s})
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and is_sep(lines[i + 1]):
            head = split_row(s)
            rows = []
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            out.append({"type": "table", "head": head, "rows": rows})
            continue
        if s.startswith(">"):
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append({"type": "quote", "lines": q})
            continue
        if re.match(r"^([-*+]|\d+[.)])\s", s):
            items: list[dict] = []
            while i < n:
                cur = lines[i]
                cs = cur.strip()
                if not cs:
                    # 列表里的空行：下一行若还是列表项/缩进续行就继续
                    if i + 1 < n and (re.match(r"^([-*+]|\d+[.)])\s", lines[i + 1].strip())
                                      or lines[i + 1].startswith("   ")):
                        i += 1
                        continue
                    break
                indent = len(cur) - len(cur.lstrip())
                m = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", cs)
                if m and indent < 2:
                    items.append({"text": m.group(2), "subs": []})
                elif m and items:
                    items[-1]["subs"].append(m.group(2))
                elif items and (indent >= 2 or not re.match(r"^(#|\||>|\*\*\d)", cs)):
                    # 续行
                    if items[-1]["subs"]:
                        items[-1]["subs"][-1] += " " + cs
                    else:
                        items[-1]["text"] += " " + cs
                else:
                    break
                i += 1
            out.append({"type": "list", "items": items})
            continue
        # 段落：直到空行/表/列表/标题；以 **N · 开头的行另起一段
        para = [s]
        i += 1
        while i < n:
            t = lines[i].strip()
            if (not t or t.startswith(("|", "#", ">", "<details")) or re.match(r"^([-*+]|\d+[.)])\s", t)
                    or NUM_HEAD.match(t) or re.match(r"^-{3,}$", t)):
                break
            para.append(t)
            i += 1
        out.append({"type": "para", "lines": para})
    return out


# ───────────────────────────── 卡片工具 ─────────────────────────────
def head_rest(text: str) -> tuple[str, str]:
    """「**粗体头**：其余」→ (头, 其余)；没有粗体头就按第一个句号切。"""
    m = re.match(r"^\*\*(.+?)\*\*\s*[：:]?\s*(.*)$", text.strip(), re.S)
    if m and len(plain(m.group(1))) <= 90:
        return plain(m.group(1)).rstrip("：:"), plain(m.group(2)).lstrip("—– ").strip()
    p = plain(text)
    m2 = re.match(r"^(.{6,70}?[。！？])(.+)$", p, re.S)
    if m2:
        return m2.group(1), m2.group(2).strip()
    return p, ""


def flag_label(text: str):
    p = plain(text)
    if p.startswith(("🚩", "⚠️", "⛔")):
        return ["要注意", "hot"]
    if p.startswith("⭐"):
        return ["重点", "amb"]
    return None


def first_http(links):
    for l in links:
        if l.get("href"):
            return l
    return None


def back_links(links):
    parts = []
    for l in links:
        if l.get("href"):
            parts.append({"a": {"text": l["text"], "href": l["href"]}})
        elif l.get("path"):
            parts.append({"t": f"仓库文件：{l['path']}"})
    return parts


TITLE_HEADS = ["ticker", "主题", "看法", "读法", "卡点", "票", "墙后", "谁"]
DESC_HEADS = ["说了什么", "讲的是什么", "他在讲什么", "原话", "要点", "内容", "依据", "角度", "公开区那一票", "备注", "组"]
LABEL_SKIP = {"谁"}


def row_card(head, row, group=None, col_id=""):
    row = row + [""] * (len(head) - len(row))
    cells = [plain(c) for c in row]
    hl = [plain(h) for h in head]
    links = [l for c in row for l in links_of(c)]

    def find(keys):
        for k in keys:
            for j, h in enumerate(hl):
                if k.lower() in h.lower() and cells[j]:
                    return j
        return None

    ti = find(TITLE_HEADS)
    if ti is None:
        ti = next((j for j, c in enumerate(cells) if c and not re.fullmatch(r"[\d.,%×x+−\-/ ]+", c)), 0)
    di = find(DESC_HEADS)
    if di is None or di == ti:
        rest = [(len(c), j) for j, c in enumerate(cells) if j != ti]
        di = max(rest)[1] if rest else None
    labels = []
    if group:
        labels.append([group, "blu"])
    for j, c in enumerate(cells):
        if j in (ti, di) or not c or hl[j] in LABEL_SKIP:
            continue
        if "墙后" in hl[j] and j != ti:
            km = re.search(r"\b(Focus|Stalk|Update|Note)\b", c)
            if km:
                labels.insert(0, [f"Jeff {km.group(1)}", "hot" if km.group(1) == "Focus" else "amb"])
            continue
        if len(c) <= 16 and len(labels) < 4:
            tone = "blu"
            if hl[j].lower() == "kind":
                tone = "hot" if "Focus" in c else ("amb" if "Stalk" in c else "blu")
                labels.insert(0, [c, tone])
                continue
            if "新面孔" in hl[j]:
                tone = "ok"
            labels.append([f"{hl[j]} {c}" if hl[j] else c, tone])
    title = cells[ti] or "（无标题）"
    who = find(["谁"])
    if who is not None and who not in (ti, di) and col_id != "spot":
        desc_extra = cells[who]
    else:
        desc_extra = ""
    desc = cells[di] if di is not None else ""
    back = [{"row": [hl[j] or "·", c]} for j, c in enumerate(cells) if c]
    back += back_links(links)
    if col_id == "done":
        labels.insert(0, ["别追", "hot"])
    card = {"labels": labels, "title": title, "desc": desc, "back": back}
    if desc_extra:
        card["meta"] = desc_extra
        card["meta_icon"] = "user"
    lk = first_http(links)
    if lk:
        card["link"] = {"text": "原帖" if "x.com" in lk["href"] else lk["text"][:18], "href": lk["href"]}
    return card


def text_card(text, subs=None, label=None, group=None):
    title, rest = head_rest(text)
    labels = []
    fl = flag_label(text)
    if label:
        labels.append(label)
    if group:
        labels.append([group, "blu"])
    if fl:
        labels.append(fl)
    nth = re.search(r"第\s*(\d+)\s*次", plain(title))
    if nth:
        k = int(nth.group(1))
        labels.append([f"第 {k} 次", "hot" if k >= 3 else ("amb" if k == 2 else "blu")])
    if re.search(r"已开单|可闭|已落地|✅", plain(title)):
        labels.append(["已办", "ok"])
    links = links_of(text) + [l for s in (subs or []) for l in links_of(s)]
    back = [{"t": plain(text)}] + [{"li": plain(s)} for s in (subs or [])] + back_links(links)
    card = {"labels": labels, "title": title, "desc": rest, "back": back}
    if subs:
        card["dirs"] = [plain(s) for s in subs]
    lk = first_http(links)
    if lk:
        card["link"] = {"text": "原帖" if "x.com" in lk["href"] else lk["text"][:18], "href": lk["href"]}
    return card


def generic_cards(blocks, col_id=""):
    """通用：表格每行一张卡 · 列表每项一张卡 · 段落一张卡（粗体头段落+紧跟的列表合成一张）。
    出现在第一张表/列表之前、且没有旗标的段落＝口径说明，收进列头 note。"""
    cards, notes, footers = [], [], []
    group = None
    seen_content = False
    i = 0
    while i < len(blocks):
        b = blocks[i]
        t = b["type"]
        if t == "h3":
            group = re.sub(r"^[⭐\s]*(\d+[a-z]?\.)?\s*", "", plain(b["text"]))
            group = re.sub(r"[（(][^）)]*[）)]", "", group).strip()[:20]
            seen_content = False
        elif t == "table":
            for r in b["rows"]:
                cards.append(row_card(b["head"], r, group, col_id))
            seen_content = True
        elif t == "list":
            for it in b["items"]:
                cards.append(text_card(it["text"], it["subs"], group=group))
            seen_content = True
        elif t in ("quote", "details"):
            cards.extend(quote_cards(b))
        elif t == "para":
            txt = "\n".join(b["lines"])
            p = plain(txt)
            if FOOTER_PREFIX.match(p):
                footers.extend(plain(x) for x in b["lines"])
            elif (txt.startswith("**") and i + 1 < len(blocks) and blocks[i + 1]["type"] == "table"
                  and len(b["lines"]) == 1 and plain(txt).endswith(("：", ":"))):
                cap, _ = head_rest(txt)
                cap = re.sub(r"[（(][^）)]*[）)]", "", cap).strip("：: ")[:16]
                for r in blocks[i + 1]["rows"]:
                    c = row_card(blocks[i + 1]["head"], r, cap, col_id)
                    c["back"].append({"k": "表头说明", "t": p})
                    cards.append(c)
                i += 1
                seen_content = True
            elif (txt.startswith("**") and i + 1 < len(blocks) and blocks[i + 1]["type"] == "list"
                  and len(b["lines"]) <= 3):
                nxt = blocks[i + 1]
                subs = [it["text"] + ("；" + "；".join(it["subs"]) if it["subs"] else "") for it in nxt["items"]]
                cards.append(text_card(txt, subs, group=group))
                i += 1
                seen_content = True
            elif not seen_content and not flag_label(txt) and not txt.startswith("**") and not group:
                notes.append(p)
            else:
                cards.append(text_card(txt, group=group))
        i += 1
    return cards, notes, footers


def quote_cards(b):
    if b["type"] == "details":
        lines = b["lines"]
        txt = "\n".join(lines)
        chunks = re.split(r"\n(?=\s*(?:\*\*)?\s*[①②③④⑤])", "\n" + txt)
        out = []
        for ch in chunks:
            ch = ch.strip()
            if not ch:
                continue
            ls = [l for l in ch.splitlines() if l.strip()]
            title, rest = head_rest(ls[0])
            body = [plain(l) for l in ls]
            out.append({"labels": [[b.get("summary") or "折叠块", "blu"]], "title": title,
                        "desc": rest or (plain(ls[1]) if len(ls) > 1 else ""),
                        "back": [{"t": x} for x in body]})
        return out
    # 引用块（回执）：列表项各一张，前导段落一张
    inner = blocks_of(b["lines"])
    out = []
    for ib in inner:
        if ib["type"] == "list":
            for it in ib["items"]:
                out.append(text_card(it["text"], it["subs"], label=["回执", "ok"]))
        elif ib["type"] == "para":
            p = "\n".join(ib["lines"])
            if plain(p) in ("回执",):
                continue
            # 「**回执**\n任务板…」：去掉标题行
            ls = [l for l in ib["lines"] if plain(l) != "回执"]
            if ls:
                out.append(text_card("\n".join(ls), label=["回执", "ok"]))
        elif ib["type"] == "table":
            for r in ib["rows"]:
                out.append(row_card(ib["head"], r))
    return out


# ───────────────────────────── 节级特化 ─────────────────────────────
def spot_cards(blocks):
    """蹭位榜：表格行 + 「回复方向」里同编号的块合成一张卡；09-24 那种无表格写法（粗体头块）也认。"""
    rows, dir_blocks, other = {}, {}, []
    order = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        if b["type"] == "table" and any(plain(h) == "#" for h in b["head"]):
            hi = [plain(h) for h in b["head"]].index("#")
            for r in b["rows"]:
                k = plain(r[hi]) if hi < len(r) else ""
                rows[k] = (b["head"], r)
                order.append(k)
        elif b["type"] == "para" and NUM_HEAD.match(b["lines"][0]):
            k = NUM_HEAD.match(b["lines"][0]).group(1)
            subs = []
            if i + 1 < len(blocks) and blocks[i + 1]["type"] == "list":
                subs = [it["text"] + ("；" + "；".join(it["subs"]) if it["subs"] else "") for it in blocks[i + 1]["items"]]
                i += 1
            dir_blocks[k] = ("\n".join(b["lines"]), subs)
            if k not in order:
                order.append(k)
        else:
            other.append(b)
        i += 1
    cards = []
    for k in order:
        if k in rows:
            head, r = rows[k]
            c = row_card(head, r, None, "spot")
            hl = [plain(h) for h in head]
            cells = {hl[j]: plain(r[j]) for j in range(min(len(hl), len(r)))}
            who = cells.get("谁", "")
            say = cells.get("他在讲什么", c["desc"])
            c["title"] = f"{who}：{say}" if who else say
            c["desc"] = ""
            c["labels"] = [[f"#{k}", "blu"]] + [[f"{h} {cells[h]}", "blu"] for h in ("密度", "距今") if cells.get(h)]
        else:
            txt = dir_blocks[k][0]
            title, rest = head_rest(txt)
            c = text_card(txt)
            head = re.sub(r"^\d+\s*·\s*", "", title)
            who = re.search(r"@\w+", head)
            c["labels"] = [[f"#{k}", "blu"]]
            for pat, fmt in ((r"密度\s*([\d,]+)", "密度 {}"), (r"([\d.]+)\s*小时前", "距今 {}h")):
                mm = re.search(pat, head)
                if mm:
                    c["labels"].append([fmt.format(mm.group(1)), "blu"])
            if who and rest:
                # 09-24 写法：粗体头只有密度/时刻/@谁，正文第一行才是「他在讲什么」
                c["title"], c["desc"] = f"{who.group(0)}：{rest}", ""
            else:
                c["title"], c["desc"] = head, rest
            c["dirs"] = []
        if k in dir_blocks:
            dtxt, subs = dir_blocks[k]
            dhead, drest = head_rest(dtxt)
            skip = "跳过" in plain(dtxt) and not subs
            # 卡背先放回复方向（这一列的正题），再放榜单字段
            dparts = [{"k": "回复方向（只给方向，字由你写）"}, {"t": plain(dtxt)}] + [{"li": plain(s)} for s in subs]
            dparts += back_links([l for s in subs for l in links_of(s)] + links_of(dtxt))
            c["back"] = dparts + [{"k": "榜单这一行"}] + c["back"]
            if skip:
                c["labels"].insert(0, ["跳过", "amb"])
                c["ask"] = re.sub(r"^.*?跳过", "跳过", plain(dtxt))[:40]
            elif subs:
                c["labels"].insert(0, [f"方向 ×{len(subs)}", "ok"])
                c["dirs"] = [plain(s) for s in subs]
                if drest and drest not in c["title"]:
                    c["desc"] = drest
        elif k in rows:
            c["labels"].insert(0, ["无方向", "amb"])
        cards.append(c)
    more, notes, footers = generic_cards(other, "spot")
    # 「回复方向」小标题本身不成卡
    more = [m for m in more if m["title"]]
    return cards + more, notes, footers


# ───────────────────────────── 主流程 ─────────────────────────────
def parse(md: str):
    lines = md.splitlines()
    h1 = next((l for l in lines if l.startswith("# ")), "# X 日调研")
    sec_idx = [j for j, l in enumerate(lines) if re.match(r"^##\s", l)]
    pre = lines[1: sec_idx[0]] if sec_idx else lines[1:]
    sections = []
    for a, j in enumerate(sec_idx):
        end = sec_idx[a + 1] if a + 1 < len(sec_idx) else len(lines)
        sections.append((lines[j][2:].strip(), lines[j + 1: end]))
    return h1, pre, sections


CLASSIFY_ORDER = ["spot", "topic", "wall", "done", "cand", "trend", "chat", "steve"]  # 先认窄的：「选题候选」不能落进「候选」


def classify(title: str):
    t = plain(title)
    for cid, pat, *_ in sorted(COLUMNS, key=lambda c: CLASSIFY_ORDER.index(c[0])):
        if re.search(pat, t, re.I):
            return cid
    return None


def build(md_path: Path):
    md = md_path.read_text(encoding="utf-8")
    h1, pre, sections = parse(md)
    h1p = plain(h1[2:])
    m = re.search(r"(\d{4}-\d{2}-\d{2})", h1p)
    et_date = m.group(1) if m else md_path.stem
    m = re.search(r"[（(](.+)[)）]\s*$", h1p)
    tag = m.group(1) if m else "主班日报"

    cols: dict[str, dict] = {}
    extra: list[dict] = []
    sources: list[str] = []
    counts = []  # (节标题, 列 id, md 条目数, 卡片数)

    # 开头：窗口行 / 落盘行进出处，回执进「给 Steve」列
    pre_blocks = blocks_of(pre)
    pre_cards = []
    window_line = ""
    for b in pre_blocks:
        if b["type"] == "para":
            for l in b["lines"]:
                p = plain(l)
                sources.append(p)
                if p.startswith("窗口"):
                    window_line = p
        elif b["type"] == "quote":
            pre_cards.extend(quote_cards(b))
        else:
            pre_cards.extend(generic_cards([b])[0])

    for title, body in sections:
        cid = classify(title)
        blocks = blocks_of(body)
        if cid == "spot":
            cards, notes, footers = spot_cards(blocks)
        else:
            cards, notes, footers = generic_cards(blocks, cid or "")
        sources.extend(footers)
        md_items = count_md_items(blocks)
        if cid:
            spec = next(c for c in COLUMNS if c[0] == cid)
            col = cols.setdefault(cid, {"id": cid, "title": spec[2], "icon": spec[3], "cards": [], "notes": [], "sec": []})
        else:
            col = {"id": "x%d" % len(extra), "title": re.sub(r"^[\d一二三四五六七八九十]+[.、]\s*", "", plain(title))[:20],
                   "icon": "layout-list", "cards": [], "notes": [], "sec": []}
            extra.append(col)
        col["cards"].extend(cards)
        col["notes"].extend(notes)
        col["sec"].append(plain(title))
        counts.append((plain(title), col["title"], md_items, len(cards), len(notes), len(footers)))

    if pre_cards:
        col = cols.setdefault("steve", {"id": "steve", "title": COLUMNS[-1][2], "icon": COLUMNS[-1][3],
                                        "cards": [], "notes": [], "sec": []})
        col["cards"] = pre_cards + col["cards"]
        counts.append(("（开头回执）", col["title"], count_md_items(pre_blocks), len(pre_cards), 0, 0))

    ordered = [cols[c[0]] for c in COLUMNS[:-1] if c[0] in cols] + extra + ([cols["steve"]] if "steve" in cols else [])
    columns = []
    for c in ordered:
        note = " ".join(c["notes"])
        cards = c["cards"]
        if note:
            # 口径段落也要能点开读全：放一张「口径」卡在列尾，列头只留一行
            cards = cards + [{"labels": [["口径", "blu"]], "title": "本节口径", "desc": note,
                              "back": [{"t": n} for n in c["notes"]]}]
        columns.append({"id": c["id"], "title": c["title"], "icon": c["icon"], "cards": cards,
                        "count": sum(1 for x in cards if x["title"] != "本节口径"),
                        "note": (note[:44] + "…") if len(note) > 44 else note,
                        "empty": "今天这一节是空的。"})

    # ── 状态条与一句话 ──
    status, headline = summarize(md, cols, window_line)
    now = datetime.now(ZoneInfo("Asia/Tokyo")) if ZoneInfo else datetime.now()
    nyt = now.astimezone(ZoneInfo("America/New_York")) if ZoneInfo else now
    eyebrow = f"X 日调研 · 数据 ET {et_date} · 生成 {now:%m-%d %H:%M} JST（ET {nyt:%m-%d %H:%M}）"
    sources.append(f"本页由 build_daily_board.py 从 data/content/x_watch/daily/{md_path.name} 生成；卡背是该条原文全文。")
    data = {"date": et_date, "eyebrow": eyebrow, "tag": tag, "headline": headline,
            "status": status, "columns": columns, "sources": sources}
    return data, counts


def find_cards(cols, cid):
    return cols.get(cid, {}).get("cards", [])


def summarize(md, cols, window_line):
    status = []
    m = re.search(r"(\d+)\s*帖\s*/\s*(\d+)\s*人", window_line or md)
    if m:
        status.append({"icon": "file-text", "label": "帖 / 人", "value": f"{m.group(1)} / {m.group(2)}", "tone": ""})
    cov = re.search(r"coverage\s*`?(\w+)`?", window_line or md)
    if cov:
        status.append({"icon": "radar", "label": "覆盖", "value": cov.group(1), "tone": "ok" if cov.group(1) == "full" else "hot"})

    # 用 md 直接数第 1 节第一张表，最稳
    sec1 = re.search(r"^##\s.*(候选|还没跑).*$([\s\S]*?)^##\s", md, re.M)
    n_cand, cand_names = 0, []
    if sec1:
        bl = blocks_of(sec1.group(2).splitlines())
        tb = next((b for b in bl if b["type"] == "table" and "ticker" in plain(b["head"][0]).lower()), None)
        if tb:
            n_cand = len(tb["rows"])
            cand_names = [plain(r[0]).replace(" ", "") for r in tb["rows"]]
    status.append({"icon": "crosshair", "label": "明天候选", "value": f"{n_cand} 只", "tone": "ok" if n_cand else ""})

    # 圈外主题：第 3 节里第一处「圈外主题起量」
    theme = "—"
    mt = re.search(r"圈外主题起量[^：:\n]*[：:]\s*([^\n]+)", md)
    if mt:
        th = plain(mt.group(1))
        th = re.sub(r"[，,]\s*mood 脚本判定", "", th)
        th = re.sub(r"[（(]\s*mood 脚本判定\s*[）)]", "", th)
        th = re.sub(r"[（(]脚本判定.*$", "", th)
        theme = th.strip(" *：:。")[:18] or "—"
        if re.match(r"^(无|脚本判定无|没有)", theme):
            theme = "无"
    elif re.search(r"圈外主题起量", md):
        theme = "无"
    hot_theme = theme not in ("—", "无") and not theme.startswith("无")
    status.append({"icon": "globe", "label": "圈外主题", "value": theme, "tone": "hot" if hot_theme else ""})

    # Jeff 墙后 Focus
    focus = []
    sec5 = re.search(r"^##\s.*(墙后|jfsrev).*$([\s\S]*?)^##\s", md, re.M)
    if sec5:
        for b in blocks_of(sec5.group(2).splitlines()):
            if b["type"] == "table":
                hl = [plain(h).lower() for h in b["head"]]
                if "kind" in hl and hl[0] == "et":
                    ki = hl.index("kind")
                    ti = next((j for j, h in enumerate(hl) if "票" in h), None)
                    for r in b["rows"]:
                        if ki < len(r) and plain(r[ki]) == "Focus" and ti is not None:
                            focus.append(re.split(r"→| via ", plain(r[ti]))[0].strip())
    status.append({"icon": "lock", "label": "Jeff 墙后 Focus", "value": f"{len(focus)} 张", "tone": "hot" if focus else ""})

    # 一句话：报告若有「**一句话**：」就用它；没有就由各节拼
    one = re.search(r"^\s*>?\s*\*\*一句话\*\*\s*[：:]\s*(.+)$", md, re.M)
    if one:
        return status, plain(one.group(1))
    parts = []
    if n_cand:
        parts.append(f"明天候选 {n_cand} 只，{'、'.join(cand_names[:3])}{' 等' if n_cand > 3 else ''}")
    else:
        parts.append("明天候选：空")
    if hot_theme:
        parts.append(f"圈外主题起量：{theme}")
    if focus:
        parts.append(f"Jeff 墙后 Focus：{'、'.join(focus)}")
    elif sec5:
        parts.append("Jeff 墙后今天没出 Focus")
    return status, "；".join(parts) + "。"


def count_md_items(blocks):
    n = 0
    for b in blocks:
        if b["type"] == "table":
            n += len(b["rows"])
        elif b["type"] == "list":
            n += len(b["items"])
        elif b["type"] == "para":
            n += 1
        elif b["type"] in ("quote", "details"):
            n += 1
    return n


# ───────────────────────────── 输出与核对 ─────────────────────────────
def render(data) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    assert "__DATA_JSON__" in tpl
    return tpl.replace("__DATA_JSON__", blob)


def coverage(md: str, data) -> list[str]:
    """md 里每一行正文（去 markdown）都必须在 JSON 文本里出现；返回漏掉的行。"""
    hay = json.dumps(data, ensure_ascii=False)
    hay = json.loads(json.dumps(hay))  # 同一转义口径
    hay_norm = re.sub(r"\s+", "", hay)
    missing = []
    for l in md.splitlines():
        s = l.strip()
        if not s or re.match(r"^(#|-{3,}|\|?\s*:?-{2,})", s) or s in ("<details>", "</details>"):
            continue
        if s.startswith("|"):
            pieces = [plain(c) for c in split_row(s)]
        else:
            s2 = re.sub(r"^(>\s*)?(([-*+]|\d+[.)])\s+)?", "", s)
            pieces = [plain(s2)]
        for p in pieces:
            p = re.sub(r"\s+", "", p)
            if len(p) < 2 or p in ("·", "—"):
                continue
            if p not in hay_norm and json.dumps(p, ensure_ascii=False)[1:-1] not in hay_norm:
                missing.append(p[:80])
    return missing


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    md_path = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else md_path.with_suffix(".board.html")
    data, counts = build(md_path)
    out.write_text(render(data), encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size:,} bytes, {sum(len(c['cards']) for c in data['columns'])} cards, "
          f"{len(data['columns'])} columns)")
    if "--check" in argv:
        print(f"\n{'md 节':<34} {'→ 列':<20} {'md条目':>6} {'卡片':>5} {'口径段':>6} {'进出处':>6}")
        for t, ct, mi, nc, nn, nf in counts:
            print(f"{t[:32]:<34} {ct[:18]:<20} {mi:>6} {nc:>5} {nn:>6} {nf:>6}")
        miss = coverage(md_path.read_text(encoding="utf-8"), data)
        print(f"\n逐行覆盖：漏 {len(miss)} 处")
        for m in miss[:30]:
            print("  ✗", m)
        return 1 if miss else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
