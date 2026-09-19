"""Keep the recap from repeating itself (Andy 2026-09-13「保证每周内容不会太重复」).

R1 · education topics — a new issue's A and B are compared with the local topic ledger
     (~/Documents/Trading/01_Market_Reports_Daily/_ledger/edu_topics.jsonl, never in git):
       red if a concept equals, or a title is ≥ 0.6 similar (same language), to any entry used in
       the last 20 sessions before the issue. The 8 topics spec §5 lists as already used carry no
       date and always count as recent. A weekly issue's A may not share a concept with any daily A
       of the same week.
     An option carrying `picked_by_andy` (his words, verbatim) is exempt: the topic is his call
     (Andy 2026-09-19「新的教育选题 用 neWS FailIure，我在discord里面讲过了」); R1 stops the machine
     from repeating itself, not him from choosing.
R2 · same-week text — rules 1–6, rule 7 minus its fixed opening, every "next session" item and the
     Big Picture's first sentence are compared item by item with the issues already written this ISO
     week (Monday on): red at ≥ 0.75 similarity between dailies, ≥ 0.85 when a weekly is involved
     (a weekly is meant to sum up its week). EN and ZH are compared separately.
Similarity is difflib.SequenceMatcher on characters after lower-casing and dropping punctuation/space.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import re
from pathlib import Path

from pipeline.content.recap import RECAP_ROOT
from pipeline.content.recap.constants import RULE7_PREFIX
from pipeline.marketcal import is_trading_day

LEDGER = RECAP_ROOT / "_ledger" / "edu_topics.jsonl"
TITLE_SIM = 0.6
R2_DAILY, R2_WEEKLY = 0.75, 0.85
WINDOW_SESSIONS = 20

SPEC_USED = [  # Daily_Recap_Workflow_Spec §5「已用过的 education 题材」— dates unknown
    ("vcp", "VCP — Volatility Contraction Pattern", "VCP（波动收缩）"),
    ("failed_breakout_swing_failure", "Failed Breakout / Swing Failure", "失败突破 / 摆动失败"),
    ("ma_ping_pong", "MA Ping-Pong", "均线乒乓"),
    ("news_failure", "News Failure", "利空失灵"),
    ("leadership_rotation", "Leadership Rotation", "龙头轮动"),
    ("hyperscaler_capex", "Hyperscaler Capex", "云巨头资本开支"),
    ("gap_down_reclaim", "Gap-Down Reclaim", "跳空低开后收复"),
    ("stage_1_to_2", "Stage 1 → 2 Base Breakout", "一阶段到二阶段的底部突破"),
]


def norm(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"[\W_]+", "", s.lower())


def sim(a: str, b: str) -> float:
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ------------------------------------------------------------------ ledger
def load_ledger(path: Path = LEDGER) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def _write(entries: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries))


def seed(path: Path = LEDGER) -> list[dict]:
    entries = load_ledger(path)
    have = {e.get("concept") for e in entries if e.get("issue") == "spec§5"}
    for concept, en, zh in SPEC_USED:
        if concept not in have:
            entries.append({"date": None, "issue": "spec§5", "key": "A", "title_zh": zh, "title_en": en, "concept": concept})
    _write(entries, path)
    return entries


def add_entry(entry: dict, path: Path = LEDGER) -> list[dict]:
    entries = [e for e in seed(path) if not (e.get("issue") == entry["issue"] and e.get("key") == entry["key"])]
    entries.append(entry)
    _write(entries, path)
    return entries


def sessions_between(a: str, b: str) -> int:
    """NYSE sessions in (a, b]."""
    d, end, n = dt.date.fromisoformat(a), dt.date.fromisoformat(b), 0
    while d < end:
        d += dt.timedelta(days=1)
        n += is_trading_day(d)
    return n


# ------------------------------------------------------------------ R1
def r1(issue: str, date: str, weekly: bool, options: list[dict], ledger: list[dict], week_dates: list[str] = ()) -> list[dict]:
    hits = []
    for opt in options:
        if opt.get("picked_by_andy"):
            continue
        for ent in ledger:
            if ent.get("issue") == issue:
                continue
            d = ent.get("date")
            same_week_daily = weekly and d in set(week_dates) and "-W" not in str(ent.get("issue"))
            if d is None:
                recent = True
            elif d < date:
                recent = sessions_between(d, date) <= WINDOW_SESSIONS
            else:
                recent = False
            if not (recent or same_week_daily):
                continue
            why = []
            if opt.get("concept") and opt["concept"] == ent.get("concept"):
                if recent or (same_week_daily and opt["key"] == "A"):
                    why.append("concept")
            if recent:
                for lang in ("en", "zh"):
                    s = sim(opt.get(f"title_{lang}", ""), ent.get(f"title_{lang}", ""))
                    if s >= TITLE_SIM:
                        why.append(f"title_{lang} {s:.2f}")
            if why:
                hits.append({"option": opt["key"], "concept": opt.get("concept"), "title_en": opt.get("title_en"),
                             "vs": {"issue": ent.get("issue"), "date": d, "concept": ent.get("concept"), "title_en": ent.get("title_en")},
                             "why": why})
    return hits


# ------------------------------------------------------------------ R2
def first_sentence(text: str) -> str:
    t = re.sub(r"<[^>]+>", "", text or "").strip()
    parts = re.split(r"(?<=[.!?。！？])\s*", t, maxsplit=1)
    return parts[0] if parts else t


def r2_items(content: dict, lang: str) -> list[tuple[str, str]]:
    items = []
    rules = content.get("rules") or []
    for i, r in enumerate(rules[:6], start=1):
        items.append((f"rule {i}", r))
    if len(rules) >= 7:
        tail = rules[6]
        if tail.startswith(RULE7_PREFIX[lang]):
            tail = tail[len(RULE7_PREFIX[lang]):]
        tail = tail.strip(" —-–:：，,")
        if norm(tail):
            items.append(("rule 7 tail", tail))
    for i, t in enumerate(content.get("session_commentary") or [], start=1):
        items.append((f"commentary {i}", t))
    for i, t in enumerate(content.get("tomorrow") or [], start=1):
        items.append((f"next {i}", t))
    bp = content.get("big_picture")
    if isinstance(bp, dict):
        bp = "".join(bp.get("j", []))
    if bp:
        items.append(("big picture first sentence", first_sentence(bp)))
    return items


def r2(current: dict, cur_weekly: bool, priors: list[tuple[str, bool, dict]],
       daily_thr: float = R2_DAILY, weekly_thr: float = R2_WEEKLY) -> list[dict]:
    """current: {lang: content}; priors: [(issue, weekly, {lang: content})]."""
    hits = []
    for lang, content in current.items():
        mine = r2_items(content, lang)
        for issue, p_weekly, p_contents in priors:
            if lang not in p_contents:
                continue
            thr = weekly_thr if (cur_weekly or p_weekly) else daily_thr
            theirs = r2_items(p_contents[lang], lang)
            for lab, text in mine:
                best = max(((sim(text, t2), lab2, t2) for lab2, t2 in theirs), default=(0.0, "", ""))
                if best[0] >= thr:
                    hits.append({"lang": lang, "item": lab, "text": text, "vs_issue": issue, "vs_item": best[1],
                                 "vs_text": best[2], "similarity": round(best[0], 2), "threshold": thr})
    return hits
