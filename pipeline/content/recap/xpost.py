"""X short-post drafts for daily issues (EN only — Andy 09-13「周复盘不发X, X一致对外用英文版本」) and gate P1.

Two variants per issue, taken from content_EN.json `x_posts` (written with the content):
  v1 · judgment first  — the day's character, one or two key readings, 2–4 leader cashtags
  v2 · structure first — the day's main structural event, what it means (only judgments already in the
                          content file), same cashtags
If `x_posts` is missing, a plain fallback is composed from the content fields and marked `auto`.

P1 (any hit → red): over 280 X characters · proprietary names · "Andy" · first person · dollar amounts
(cashtags are fine) · 「领导力」 · hashtags · emoji · links · calls to action · a number that does not
appear verbatim in the content file.
X counting: code points in the Latin/general-punctuation ranges weigh 1, everything else 2, a URL 23.
"""
from __future__ import annotations

import re

from pipeline.content.recap.gates import run_gates

LIMIT = 280
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
HASHTAG_RE = re.compile(r"(?<![\w&])#[A-Za-z_]\w*")
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]")
CTA_RE = re.compile(r"\b(link in bio|subscribe|sign up|join (?:us|now)|follow (?:us|me|for)|click|read more|check out|dm (?:me|us))\b", re.I)
NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
CASHTAG_RE = re.compile(r"(?<![\w$])\$[A-Z]{1,6}\b")


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
    source = "\n".join(_strings(content_en))
    missing = sorted({n for n in NUM_RE.findall(CASHTAG_RE.sub("", text)) if n not in source})
    if missing:
        hits.append("numbers not in content: " + ", ".join(missing))
    return {"ok": not hits, "chars": chars, "hits": hits}


def _tickers(content_en: dict, n: int = 4) -> list[str]:
    seen = []
    for row in content_en.get("led") or []:
        for tk in re.findall(r"\b[A-Z]{2,5}\b", " ".join(str(x) for x in row)):
            if tk not in seen and tk not in {"AI", "RS", "EMA", "SMA", "ETF", "CPI", "PPI", "RSP", "IWM", "QQQ", "SPY", "DIA"}:
                seen.append(tk)
    return seen[:n]


def compose(content_en: dict) -> dict:
    given = content_en.get("x_posts") or {}
    if given.get("v1") and given.get("v2"):
        return {k: {"text": given[k]["text"], "fields": given[k].get("fields", []), "source": "content"} for k in ("v1", "v2")}
    tags = " ".join("$" + t for t in _tickers(content_en))
    bp = re.sub(r"<[^>]+>", "", "".join(content_en["big_picture"]["j"]) if isinstance(content_en.get("big_picture"), dict)
                else content_en.get("big_picture", ""))
    first = re.split(r"(?<=[.!?])\s+", bp)[0]
    notes = content_en.get("index_notes") or {}
    ev = "; ".join(f"{tk} {notes[tk][0]}" for tk in ("SPY", "QQQ") if tk in notes)
    return {"v1": {"text": f"{first}\n\n{tags}".strip(), "fields": ["big_picture", "led"], "source": "auto"},
            "v2": {"text": f"{ev}. {content_en.get('state_line', '')}\n\n{tags}".strip(), "fields": ["index_notes", "state_line", "led"],
                   "source": "auto"}}


def to_markdown(label: str, posts: dict, results: dict) -> str:
    names = {"v1": "Variant 1 · judgment first", "v2": "Variant 2 · structure first"}
    out = [f"# X post drafts · {label} · EN", ""]
    for k in ("v1", "v2"):
        r = results[k]
        out += [f"## {names[k]}", "", posts[k]["text"], "",
                f"_{r['chars']} / {LIMIT} X characters · fields: {', '.join(posts[k]['fields'])} · source: {posts[k]['source']} · "
                f"P1: {'pass' if r['ok'] else 'RED — ' + '; '.join(r['hits'])}_", ""]
    return "\n".join(out)
