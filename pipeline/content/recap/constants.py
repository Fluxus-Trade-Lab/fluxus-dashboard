"""Fixed text for the recap.

THE RULES — seven per issue. Rules 1–6 are written for the session; rule 7 always opens with
Andy's fixed sentence and may be followed by the session's read. Evidence (OPS 2026-09-13, from
Andy's hand-made 09-01/09-02/09-03 EN PDFs): 1–6 change daily, only rule 7's opening repeats —
matching spec §3 item 10「最后一条通常是……除非 S&P 跌破 200 日线」. An earlier revision pinned all
seven to the 09-04 text; that was a misreading and is withdrawn.

Voice (Andy 2026-09-13「正文里不出现Andy 说这样的字眼，也不用第一人称」): rules included — no name,
no first person. Enforced as delivery gates in gates.py.
"""

import difflib
import re

RULE7_PREFIX = {
    "EN": "Never serious trouble until S&P breaks the 200-day",
    "ZH": "标普不破 200 日线，谈不上真正的麻烦",
}

# Comparison reference ONLY — the 2026-09-04 session's rules 1–6 (pdftotext of the approved PDFs).
# A later issue that repeats them (verbatim or near-verbatim) is printing stale levels/names, which
# happened once (09-13, withdrawn) and is now a gate. Never rendered.
STALE_0904 = {
    "EN": (
        "Uptrend intact — weekly close above the 21 EMA — but bifurcated: big-cap AI leads, breadth lags",
        "Good news is bad news: strong data = higher hike odds = pressure; CPI/PPI decide next week",
        "7,800 is the S&P upside pivot; the declining-tops line is the near-term cap",
        "Trade leaders with buyable closes (DELL, CRCL, HOOD) — volume + a strong close",
        "Memory + the semi snapback is the constructive AI tell; NVDA holding its 8/21 is the key",
        "Software is two-tone — buy the reclaims, avoid the fails",
    ),
    "ZH": (
        "趋势还在——周线收在 21 EMA 上——但盘是劈的：大盘 AI 领涨，广度没跟",
        "好消息就是坏消息：数据强＝加息概率高＝压力；下周 CPI/PPI 说了算",
        "7,800 是标普往上的 pivot；下降趋势线是近处的顶",
        "只做收得强的龙头（DELL、CRCL、HOOD）——放量，收盘要硬",
        "Memory 加半导体回弹，是 AI 这条线还活着的证据；NVDA 守住 8/21 是钥匙",
        "软件两张脸——收回均线的可以买，破位的躲开",
    ),
}
NEAR_DUP = 0.75


def _norm(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.lower())


def stale_hits(rules, issue_date: str | None = None) -> list[tuple[int, int, float]]:
    """(rule index 1-6, 9/4 rule index, similarity) for every near-duplicate of the 09-04 set.
    The 09-04 issue itself is exempt."""
    if issue_date == "2026-09-04":
        return []
    ref = [_norm(x) for lang in STALE_0904 for x in STALE_0904[lang]]
    hits = []
    for i, r in enumerate(rules[:6], start=1):
        n = _norm(r)
        for j, x in enumerate(ref):
            ratio = difflib.SequenceMatcher(None, n, x).ratio()
            if ratio >= NEAR_DUP:
                hits.append((i, j % 6 + 1, round(ratio, 2)))
    return hits


def check_rules(rules, lang: str, issue_date: str | None = None):
    """Return None if the rules block is well-formed, else a reason string."""
    if not isinstance(rules, (list, tuple)) or len(rules) != 7:
        return f"THE RULES must be exactly 7 items (got {0 if not isinstance(rules, (list, tuple)) else len(rules)})"
    if not all(isinstance(r, str) and r.strip() for r in rules):
        return "THE RULES contain an empty item"
    if not rules[6].startswith(RULE7_PREFIX[lang]):
        return f"rule 7 must open with the fixed sentence: {RULE7_PREFIX[lang]!r}"
    hits = stale_hits(rules, issue_date)
    if hits:
        return "rules 1–6 repeat the 09-04 set (rule, 9/4 rule, similarity): " + ", ".join(map(str, hits))
    return None
