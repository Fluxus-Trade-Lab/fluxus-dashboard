"""Wording checks that are about how a reader parses the text, not about data.

W1 · "week" shorthand (Andy 09-13: 「最近的几个里面出现 theme week这样的词，其实是theme weak」).
     Notes like "theme week, the worst" / "IBIT week;" / "week −9.4%" meant "one-week change" but read
     as a typo for "weak". In EN content: red on `<Name> week` (theme / industry / sector / a capitalised
     name or ticker directly before "week") and on "week" opening a string or a clause followed by a space,
     ";" or a sign. Allowed: this / next / the / last / on the / over the week, week of, 1-week, 10-week.
     Write "−10.5% over the week (theme)" or "1-week −9.4%"; ZH writes 本周 / 一周.

week/weak review · auto-captions confuse the two words, so delivery.md lists every content sentence that
     contains week or weak, flagging the ones that closely match a transcript sentence.
"""
from __future__ import annotations

import difflib
import re

ALLOWED_BEFORE = {"this", "next", "the", "last", "that", "each", "every", "one", "a", "per", "on", "over", "of", "same", "prior", "whole"}
_NAMED = re.compile(
    r"(?<![\w-])(theme|industry|sector|[A-Z]{2,5}) week\b"          # the spec pattern
    r"|(?<![\w-])([A-Z][a-z]+) week(?=\s*[;,]|\s*[+−-]\d)")          # "Rare Earth week −10.5%"
_OPENING = re.compile(r"(?:^|(?<=[.!?;:·—]\s)|(?<=[.!?;:·—]))\s*week(?=\s|;|,|−|-|$)(?!\s+of\b)")


def _strings(o, skip=("labels", "x_posts")):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        if set(o) == {"j"} and isinstance(o["j"], list):
            yield "".join(o["j"])
        else:
            for k, v in o.items():
                if k not in skip:
                    yield from _strings(v, skip)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v, skip)


def w1_text_hits(text: str) -> list[str]:
    hits = []
    for m in _NAMED.finditer(text):
        if (m.group(1) or m.group(2)).lower() not in ALLOWED_BEFORE:
            hits.append(m.group(0))
    for m in _OPENING.finditer(text):
        hits.append(text[m.start(): m.end() + 3].strip())
    return hits


def w1_hits(content_en: dict) -> list[dict]:
    out = []
    for s in _strings(content_en):
        h = w1_text_hits(re.sub(r"<[^>]+>", "", s))
        if h:
            out.append({"text": s[:120], "matches": h})
    return out


# ------------------------------------------------------------------ week / weak review
_SENT = re.compile(r"(?<=[.!?])\s+")
_WW = re.compile(r"\bwee?k\w*|\bweak\w*", re.I)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(text) if s.strip()]


def transcript_sentences(md: str) -> list[str]:
    body = re.sub(r"\*\*\[\d+:\d+\]\*\*", " ", md)
    body = "\n".join(ln for ln in body.splitlines() if not ln.startswith(("#", "- ")))
    return _sentences(re.sub(r"\s+", " ", body))


def week_weak_review(content_en: dict, transcript_md: str | None) -> dict:
    trans = [s for s in transcript_sentences(transcript_md or "") if _WW.search(s)]
    words = lambda s: re.findall(r"[a-z0-9]+", s.lower())
    rows = []
    for s in _strings(content_en):
        for sent in _sentences(re.sub(r"<[^>]+>", "", s)):
            if not _WW.search(sent):
                continue
            w = words(sent)
            best = max((difflib.SequenceMatcher(None, w, words(t)).ratio() for t in trans), default=0.0)
            rows.append({"text": sent, "from_transcript": best >= 0.35, "match": round(best, 2)})
    return {"transcript_week_weak": len(trans), "content": rows}
