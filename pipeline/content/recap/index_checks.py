"""Index Action table gates (Andy 2026-09-24 ruling, `.claude/skills/daily-recap/SKILL.md`
"Index Action 的两列怎么填"): two red flags on the two note columns of the Index Action
table — `index_notes[ticker] = [event, note]` and `extra_index_rows[i] = [name, close,
chg, vol, event, note]`. Run in the check phase (before render), not on rendered PDF text
like gates.py.

I1 · placeholder event — 09-23's five rows were all literally "no new average event".
     The rule is "only write an event if one happened, leave it blank otherwise" — a
     sentence that says there is no event is the same mistake as writing one on the
     wrong side of a moving average, just spelled out instead of guessed.
I2 · note restates the row — the note column repeating the close / change% / volume
     that are already printed in their own columns a few cells to the left.
"""
from __future__ import annotations

import re

INDEX_TICKERS = ("SPY", "QQQ", "RSP", "DIA", "IWM")

# "no new ..." anywhere in the sentence, or 无/没有 within a few characters of 事件
# (real production wording varies — 无事件/没有事件/无新均线事件/无新的均线事件/均线无新事件
# all showed up across 2026-09; branch-review on T-0924-85 caught the first cut only
# matching the literal substring "无事件", which missed all 18 of the "无新...事件" cells
# in that month), or the whole cell being nothing but a lone dash —
# SKILL.md [2026-09-24]: 「事件列出现 no new/无事件/— 这类占位＝红」
_PLACEHOLDER_SUBSTRING = re.compile(r"no\s+new\b|(?:无|没有).{0,6}?事件", re.I)
_BARE_DASH = re.compile(r"^[—-]$")
_TAGS = re.compile(r"<[^>]+>")


def _clean(s) -> str:
    if not isinstance(s, str):
        return ""
    return _TAGS.sub("", s).replace("◇", "").strip()


def _is_placeholder(e: str) -> bool:
    return bool(_PLACEHOLDER_SUBSTRING.search(e) or _BARE_DASH.match(e))


def _event_note_pairs(content: dict) -> list[tuple[str, str, str]]:
    """(row label, event text, note text) for every Index Action row in this content."""
    out = []
    for t, pair in (content.get("index_notes") or {}).items():
        pair = pair or ["", ""]
        out.append((t, pair[0] if len(pair) > 0 else "", pair[1] if len(pair) > 1 else ""))
    for i, r in enumerate(content.get("extra_index_rows") or []):
        label = r[0] if r else f"extra[{i}]"
        out.append((label, r[4] if len(r) > 4 else "", r[5] if len(r) > 5 else ""))
    return out


def i1_placeholder_hits(content: dict) -> list[dict]:
    """Red when the technical-event column says there was no event instead of being blank."""
    out = []
    for row, event, _note in _event_note_pairs(content):
        e = _clean(event)
        if e and _is_placeholder(e):
            out.append({"row": row, "col": "event", "text": e})
    return out


def _row_numbers_from_pack(pack: dict, ticker: str, weekly: bool) -> list[str]:
    a = ((pack or {}).get("assets") or {}).get("rows") or {}
    row = a.get(ticker)
    if not row:
        return []
    last = row.get("close_T") if weekly else row.get("close")
    chg = row.get("week_pct") if weekly else row.get("change_pct")
    # The weekly Index Action table has no volume column at all (indexTable renders the
    # week's five daily %-change figures instead, via `is.weekly` -> `a.days`) — vol=None
    # here is not a gap to backfill, it reflects what is actually printed next to the note.
    vol = None if weekly else row.get("rel_volume")
    return _digits(last, chg, vol)


def _row_numbers_from_extra(r: list) -> list[str]:
    close = r[1] if len(r) > 1 else None
    chg = r[2] if len(r) > 2 else None
    vol = r[3] if len(r) > 3 else None
    return [n for v in (close, chg, vol) for n in _extract_numeric_tokens(v)]


def _digits(last, chg, vol) -> list[str]:
    nums = []
    if isinstance(last, (int, float)):
        nums.append(f"{abs(last):.2f}")
    if isinstance(chg, (int, float)):
        nums.append(f"{abs(chg) * 100:.2f}")
    if isinstance(vol, (int, float)):
        nums.append(f"{abs(vol):.2f}")
    return nums


_NUM_TOKEN = re.compile(r"\d[\d,]*\.?\d*")


def _extract_numeric_tokens(v) -> list[str]:
    if isinstance(v, (int, float)):
        return [f"{abs(v):.2f}"]
    if isinstance(v, str):
        return [m.group(0).replace(",", "") for m in _NUM_TOKEN.finditer(v)]
    return []


def i2_restatement_hits(content: dict, pack: dict | None = None, weekly: bool = False) -> list[dict]:
    """Red when the note column's first 20 characters repeat >= 2 of the row's own numbers.

    Commas are stripped from the note head before matching (not just from the source
    numbers) — an index point like 7,695 written with a thousands separator in the note
    would otherwise never line up with the comma-free `7695` token pulled from the data.
    """
    out = []
    index_notes = content.get("index_notes") or {}
    for t, pair in index_notes.items():
        pair = pair or ["", ""]
        note = _clean(pair[1] if len(pair) > 1 else "")
        nums = _row_numbers_from_pack(pack or {}, t, weekly)
        head = note[:20].replace(",", "")
        matched = [n for n in nums if n and n in head]
        if len(matched) >= 2:
            out.append({"row": t, "col": "note", "text": note, "matched": matched})
    for i, r in enumerate(content.get("extra_index_rows") or []):
        if len(r) < 6:
            continue
        label = r[0] if r else f"extra[{i}]"
        note = _clean(r[5])
        nums = _row_numbers_from_extra(r)
        head = note[:20].replace(",", "")
        matched = [n for n in nums if n and n in head]
        if len(matched) >= 2:
            out.append({"row": label, "col": "note", "text": note, "matched": matched})
    return out
