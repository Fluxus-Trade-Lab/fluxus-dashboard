"""X long post for daily issues (EN only — Andy 09-13「周复盘不发X, X一致对外用英文版本」) and gates P1 / P2.

Andy 09-13: 「X短文结构先行，不过太短了，我是会员，可以写更多。直接用the big picture的文字可以吗？」 → on the rule
"Big Picture's first sentence already states the structure → use Big Picture as is; otherwise put one structure
sentence in front": 「是好主意。」

Post:
    <lead>          optional structure sentence; null when Big Picture's first sentence already states the day's
                    structural event (which average was reclaimed / lost, which index split from which)
    <Big Picture>   verbatim content_EN.json big_picture, <b></b> removed, ◇ removed with the space before it
    $T1 $T2 …       2–4 leader cashtags
content_EN.json: x_posts = {"lead": str | null, "cashtags": ["HPE", …], "why": optional one-line reason}.
If x_posts is missing: Big Picture only, cashtags from the led table, marked `auto`.

P1 (any hit → red): over 1,500 X characters (guards against a runaway post; member long posts allow 25,000) ·
proprietary names · "Andy" · first person · dollar amounts (cashtags are fine) · 「领导力」 · hashtags · emoji ·
links · calls to action · a number that does not appear verbatim in the content file · leftover <b> or ◇ ·
fewer than 2 or more than 4 cashtags.
P2 (no double opening): lead present and SequenceMatcher(lead, Big Picture first sentence) ≥ 0.4 → red; set lead to null.
P3 (Andy 09-13「X挑选不用禁止cash出现当前持仓，就挑当天复盘里出现的个股，Substack帖子末尾就不用出现。」): every cashtag
must appear as a stand-alone word in the issue's big_picture / index_notes / led / lagged / tomorrow / rules; book
tickers are not avoided. "Substack" anywhere in the post is a P1 hit (no link or pointer at the end).
X counting: code points in the Latin/general-punctuation ranges weigh 1, everything else 2, a URL 23.
"""
from __future__ import annotations

import difflib
import re

from pipeline.content.recap.gates import run_gates

LIMIT = 1500
P2_MAX = 0.4
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
HASHTAG_RE = re.compile(r"(?<![\w&])#[A-Za-z_]\w*")
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]")
CTA_RE = re.compile(r"\b(link in bio|subscribe|sign up|join (?:us|now)|follow (?:us|me|for)|click|read more|check out|dm (?:me|us))\b", re.I)
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
CASHTAG_RE = re.compile(r"(?<![\w$])\$[A-Z]{1,6}\b")
LEFTOVER_RE = re.compile(r"</?b>|◇")
SUBSTACK_RE = re.compile(r"substack", re.I)
P3_FIELDS = ("big_picture", "index_notes", "led", "lagged", "tomorrow", "rules")


def x_length(text: str) -> int:
    n = 0
    rest = text
    for url in URL_RE.findall(text):
        n += 23
        rest = rest.replace(url, "", 1)
    for ch in rest:
        cp = ord(ch)
        n += 1 if (cp <= 4351 or 8192 <= cp <= 8205 or 8208 <= cp <= 8223 or 8242 <= cp <= 8247) else 2
    return n


def _strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        if set(o) == {"j"} and isinstance(o["j"], list):
            yield "".join(o["j"])
        else:
            for k, v in o.items():
                if k != "x_posts":
                    yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)


def clean_big_picture(bp) -> str:
    text = "".join(bp["j"]) if isinstance(bp, dict) else (bp or "")
    text = re.sub(r"</?b>", "", text)
    return re.sub(r"\s*◇", "", text).strip()


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", text.strip())[0]


def p1(text: str, content_en: dict) -> dict:
    hits = []
    chars = x_length(text)
    if chars > LIMIT:
        hits.append(f"length {chars} > {LIMIT}")
    g = run_gates(CASHTAG_RE.sub("", text))
    hits += [f"{h['gate_rule']}: {h['match']}" for h in g["banned"] + g["voice"] + g["money_shares"]]
    if g["leadership_zh"]:
        hits.append("领导力")
    if HASHTAG_RE.search(text):
        hits.append("hashtag")
    if EMOJI_RE.search(text):
        hits.append("emoji")
    if URL_RE.search(text):
        hits.append("link")
    if CTA_RE.search(text):
        hits.append("call to action")
    if LEFTOVER_RE.search(text):
        hits.append("leftover <b> or ◇")
    if SUBSTACK_RE.search(text):
        hits.append("substack")
    n_tags = len(CASHTAG_RE.findall(text))
    if not 2 <= n_tags <= 4:
        hits.append(f"{n_tags} cashtags (need 2–4)")
    source = "\n".join(_strings(content_en))
    missing = sorted({n for n in NUM_RE.findall(CASHTAG_RE.sub("", text)) if n not in source})
    if missing:
        hits.append("numbers not in content: " + ", ".join(missing))
    return {"ok": not hits, "chars": chars, "hits": hits}


def p2(lead: str | None, big_picture: str) -> dict:
    if not lead:
        return {"ok": True, "similarity": None}
    s = round(difflib.SequenceMatcher(None, lead, first_sentence(clean_big_picture(big_picture))).ratio(), 3)
    return {"ok": s < P2_MAX, "similarity": s}


def p3(cashtags: list[str], content_en: dict) -> dict:
    source = "\n".join(_strings({k: content_en.get(k) for k in P3_FIELDS if content_en.get(k) is not None}))
    source += "\n" + " ".join(content_en.get("index_notes") or {})  # the index rows are keyed by ticker
    missing = [t for t in (c.lstrip("$") for c in cashtags)
               if not re.search(rf"(?<![A-Za-z0-9$]){re.escape(t)}(?![A-Za-z0-9])", source)]
    return {"ok": not missing, "missing": missing}


def _tickers(content_en: dict, n: int = 4) -> list[str]:
    seen = []
    for row in content_en.get("led") or []:
        for tk in re.findall(r"\b[A-Z]{2,5}\b", " ".join(str(x) for x in row)):
            if tk not in seen and tk not in {"AI", "RS", "EMA", "SMA", "ETF", "CPI", "PPI", "RSP", "IWM", "QQQ", "SPY", "DIA"}:
                seen.append(tk)
    return seen[:n]


def compose(content_en: dict) -> dict:
    given = content_en.get("x_posts") or {}
    bp = clean_big_picture(content_en.get("big_picture"))
    if "lead" in given and given.get("cashtags"):
        lead, tags, why, source = given["lead"], given["cashtags"], given.get("why"), "content"
    else:
        lead, tags, why, source = None, _tickers(content_en), "x_posts missing: Big Picture only", "auto"
    tags = ["$" + t.lstrip("$") for t in tags]
    if not why:
        why = "Big Picture 第一句已在讲结构事件" if not lead else "Big Picture 第一句没讲结构事件，前面补一句结构句"
    text = "\n\n".join(p for p in (lead, bp, " ".join(tags)) if p)
    return {"text": text, "lead": lead, "cashtags": tags, "why": why, "source": source}


def to_markdown(label: str, post: dict, r1: dict, r2: dict, r3: dict | None = None) -> str:
    gate = f"P1 {'通过' if r1['ok'] else '报红：' + '；'.join(r1['hits'])} · P2 " + (
        "不适用（lead 为空）" if r2["similarity"] is None else f"{'通过' if r2['ok'] else '报红'}（与 Big Picture 第一句相似度 {r2['similarity']}，红线 {P2_MAX}）")
    if r3 is not None:
        gate += " · P3 " + ("通过" if r3["ok"] else "报红：复盘里没有 " + "、".join(r3["missing"]))
    return "\n".join([f"# X post · {label} · EN", "", post["text"], "", "---", "",
                      f"- 字符数：{r1['chars']} / {LIMIT}（X 计数）",
                      f"- lead：{'省略' if not post['lead'] else '保留'}",
                      f"- 理由：{post['why']}",
                      f"- 闸：{gate} · 来源 {post['source']}", ""])
