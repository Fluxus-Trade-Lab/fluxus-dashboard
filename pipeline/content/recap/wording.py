"""Wording checks that are about how a reader parses the text, not about data.

W1 · "week" shorthand (Andy 09-13: 「最近的几个里面出现 theme week这样的词，其实是theme weak」).
     Notes like "theme week, the worst" / "IBIT week;" / "week −9.4%" meant "one-week change" but read
     as a typo for "weak". In EN content: red on `<Name> week` (theme / industry / sector / a capitalised
     name or ticker directly before "week") and on "week" opening a string or a clause followed by a space,
     ";" or a sign. Allowed: this / next / the / last / on the / over the week, week of, 1-week, 10-week.
     Write "−10.5% over the week (theme)" or "1-week −9.4%"; ZH writes 本周 / 一周.

week/weak review · auto-captions confuse the two words, so delivery.md lists every content sentence that
     contains week or weak, flagging the ones that closely match a transcript sentence.

Andy coverage review (T-0927-35, Andy 09-27「周五缺一格，是这周的个例，那 ok，每周如此，那就是问题」)
     · pack.json's `andy.messages` carry a `session` (date) per live-commentary line; `andy.missing_dates`
     is the export gap (benign — no thread file that day). A session with messages but none of them echoed
     in `session_commentary` is the shape Andy called a problem: real material that never made the page.
     Coverage is word-overlap (SequenceMatcher on lower-cased word tokens, same method as week_weak_review)
     between each session's raw messages and every session_commentary sentence — a heuristic, not a claim
     that the meaning necessarily carried over, but sensitive enough to catch "this session got nothing".
"""
from __future__ import annotations

import difflib
import json
import re

from pipeline.content.recap import RECAP_ROOT

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


# ------------------------------------------------------------------ Andy coverage (T-0927-35)
COVERAGE_LEDGER = RECAP_ROOT / "_ledger" / "andy_coverage.jsonl"
_COV_MIN_RATIO = 0.30


def _covered(messages: list[str], commentary_words: list[set]) -> bool:
    for text in messages:
        w = set(re.findall(r"[a-z0-9]+", text.lower()))
        if not w:
            continue
        for cw in commentary_words:
            if not cw:
                continue
            ratio = difflib.SequenceMatcher(None, sorted(w), sorted(cw)).ratio()
            if ratio >= _COV_MIN_RATIO:
                return True
    return False


def andy_coverage_review(pack: dict, content_en: dict) -> dict:
    """Per session in pack['andy']: did any of its messages get echoed in session_commentary?
    missing_dates (no export that day) are recorded separately — Andy 09-27: that half is not the problem."""
    andy = pack.get("andy") or {}
    messages = andy.get("messages") or []
    missing = sorted(andy.get("missing_dates") or [])
    by_session: dict[str, list[str]] = {}
    for m in messages:
        by_session.setdefault(m["session"], []).append(m["text"])
    commentary = [re.sub(r"<[^>]+>", "", s) for s in (content_en.get("session_commentary") or [])]
    commentary_words = [set(re.findall(r"[a-z0-9]+", s.lower())) for s in commentary]
    sessions = []
    for date in sorted(by_session):
        texts = by_session[date]
        sessions.append({"date": date, "count": len(texts), "covered": _covered(texts, commentary_words)})
    uncovered = [s["date"] for s in sessions if s["count"] > 0 and not s["covered"]]
    n_total = len(sessions) + len(missing)
    n_covered = sum(1 for s in sessions if s["covered"])
    return {"sessions": sessions, "missing_dates": missing, "uncovered": uncovered,
            "n_total": n_total, "n_covered": n_covered}


def load_coverage_ledger(path=COVERAGE_LEDGER) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def record_coverage(label: str, uncovered: list[str], path=COVERAGE_LEDGER) -> None:
    """Updates in place when the issue was already recorded (a re-render), so a retry never jumps
    the entry to the end of the ledger and corrupts the chronological order coverage_streak relies on."""
    entries = load_coverage_ledger(path)
    for e in entries:
        if e["issue"] == label:
            e["uncovered"] = uncovered
            break
    else:
        entries.append({"issue": label, "uncovered": uncovered})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n")


def coverage_streak(prior_entries: list[dict], uncovered: list[str]) -> int:
    """Andy 09-27「周五缺一格，是这周的个例，那 ok，每周如此，那就是问题」— one issue is not a problem,
    the same shape (real messages, nothing on the page) two issues running is. Returns the streak length
    ending at (and including) the current issue; 0 when the current issue has nothing uncovered."""
    if not uncovered:
        return 0
    streak = 1
    for e in reversed(prior_entries):
        if not e.get("uncovered"):
            break
        streak += 1
    return streak


def _is_weekly(label: str) -> bool:
    return "-W" in label


def coverage_streak_for_issue(entries: list[dict], label: str, uncovered: list[str]) -> int:
    """The two things a caller must get right, wrapped so run.py can't skip them (T-0927-35 review,
    branch agent/ops/T-0927-35, both confirmed):
    1. Exclude this issue's own ledger entry — a re-render (an L2 gate retry, `--edu B`) must not
       count itself twice, or a first-time individual issue prints as "streak 2" on its own retry.
    2. Only compare same-cadence issues — Andy's ruling is「每周如此」(week after week); a clean
       daily sitting between two dirty weeklies must not reset the weekly streak, and a dirty daily
       must not inflate it either."""
    same_kind = [e for e in entries if e["issue"] != label and _is_weekly(e["issue"]) == _is_weekly(label)]
    return coverage_streak(same_kind, uncovered)
