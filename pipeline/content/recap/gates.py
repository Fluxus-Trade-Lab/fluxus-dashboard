"""Delivery gates for the recap PDF — run on pdftotext output, all must be 0.

Three gates (Daily_Recap_Workflow_Spec §4/§8 + Andy 2026-09-13 privacy ruling
「管线只做R 和%, 不写股数和美元」):
  1. banned   — source-proprietary names (channel, products, hosts, contacts)
  2. leadership_zh — 「领导力」 (leadership → 龙头)
  3. money_shares  — any dollar amount, share count, or labelled price

Pure functions, no I/O, so each gate can be proven red on an injected positive
(pipeline/tests/test_recap_gates.py) before its green is trusted.
"""
from __future__ import annotations

import re

# ASCII-letter lookarounds instead of \b: CJK characters count as \w, so
# \bTed\b misses "Ted说" in the Chinese PDF.
def _word(w: str, flags: int = 0) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z]){w}(?![A-Za-z])", flags)

BANNED: dict[str, re.Pattern] = {
    "Revere": _word("Revere", re.I),
    "Rever/Revier (caption misspellings)": _word("Rev(?:i?er)", re.I),
    "Growction caption variants": re.compile(r"(?<![A-Za-z])gr[eo]w?t?e?ction", re.I),
    "proprietary list names": re.compile(r"21\s*over\s*21|Sweet\s*17|(?<![A-Za-z])RG\s?8(?![0-9])", re.I),
    "River Asset": re.compile(r"River\s+Asset", re.I),
    "River AI 100 / AI 100": re.compile(r"(?:River\s+)?AI\s*100(?:\s+Index)?", re.I),
    "Turboction": _word("Turboction", re.I),
    "Growction": _word("Growction", re.I),
    "Turbo": re.compile(r"(?<![A-Za-z])Turbo", re.I),
    # host names — case-sensitive so ordinary words survive; Don't ≠ Don
    "Ted": _word("Ted"),
    "Dan": _word("Dan"),
    "Connor": _word("Connor"),
    "Todd": _word("Todd"),
    "Don": re.compile(r"(?<![A-Za-z])Don(?![A-Za-z'’])"),
    "Jackson": _word("Jackson"),
    "Naidik": _word("Naidik", re.I),
    # host surnames / nicknames and contact lines seen in the 09-08..09-12 captions
    "Toddzilla": re.compile(r"Todd\s?zilla", re.I),
    # trend-gauge state name from the source (Andy 09-13「"Grow"也是专有词，也屏蔽」); growth / grow pass
    "Grow": re.compile(r"(?<![A-Za-z])Grow(?![A-Za-z])"),
    "Zhang": _word("Zhang"),
    "Bates": _word("Bates"),
    "Grok Tasha (caption variant)": re.compile(r"Grok\s?Tasha", re.I),
    "Real Wealth line": re.compile(r"real\s?-?\s?wealth", re.I),
    "company domain": re.compile(r"rever\w*asset|river\w*asset", re.I),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"\(?\b\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
}

LEADERSHIP_ZH = "领导力"

# A per-share price carries no account size, but Andy's 2026-09-23 ruling on the
# book ladder is 「不出现美元数值」 in the portfolio section, and the shape that
# leaks there is a *labelled* price: the cost or the stop printed as the number
# it is instead of as an R. Adjacency is the whole gate — `stop 142.50` is the
# leak, `stop under 7,580` is an index level in prose and must still pass, and a
# number already wearing R / % / -day is by definition not a price.
#
# This only reaches prose. A price that leaks into a *table cell* arrives in
# pdftotext as a bare number under a header on another line, which no regex can
# tell from the index closes the page prints on purpose — that shape is gated at
# the data seam instead, by `visual._book_money_gate` (M1).
# `(?![\d,.])` first: without it the number backtracks a digit at a time until
# the exemption lookahead happens to pass, which reads "entry 2026-09-10" as a
# price of 202. `-\d` then exempts the ISO date itself.
_PRICE_TAIL = r"\d[\d,]*(?:\.\d+)?(?![\d,.])(?!\s*(?:[R%]|-day|-\d|日线|日))"

MONEY_SHARES: dict[str, re.Pattern] = {
    "dollar sign amount": re.compile(r"(?:US)?[$＄]\s?\d"),
    "amount + currency word": re.compile(
        r"\d[\d,.]*\s?(?:[kKmMbB万千亿]\s?)?(?:USD|美元|美金|美刀|dollars?(?![A-Za-z])|bucks(?![A-Za-z]))", re.I),
    "share count (en)": re.compile(r"(?<![\w.])\d[\d,]*\s?(?:shares?|shs|sh)(?![A-Za-z])", re.I),
    "share count (zh)": re.compile(r"\d[\d,]*\s?股(?![票价指市本份东息权利])"),
    "labelled price (en)": re.compile(rf"(?<![A-Za-z])(?:cost|entry|stop)s?\s*[:：]?\s*{_PRICE_TAIL}", re.I),
    "labelled price (zh)": re.compile(rf"(?:成本|进场价|入场价|止损)\s*[:：]?\s*{_PRICE_TAIL}"),
}


def _hits(text: str, pats: dict[str, re.Pattern]) -> list[dict]:
    out = []
    for name, p in pats.items():
        for m in p.finditer(text):
            a, b = max(0, m.start() - 20), min(len(text), m.end() + 20)
            out.append({"gate_rule": name, "match": m.group(0),
                        "context": text[a:b].replace("\n", " ")})
    return out


# Andy 2026-09-13「正文里不出现Andy 说这样的字眼，也不用第一人称」
VOICE: dict[str, re.Pattern] = {
    "names Andy": re.compile(r"Andy", re.I),
    "first person (en)": re.compile(r"(?<![A-Za-z’'])(?:I|I'm|I’m|I've|I’ve|I'll|I’ll|I'd|I’d|me|my|mine|we|We|we're|we’re|"
                                    r"we've|we’ve|we'll|we’ll|our|Our|ours|us)(?![A-Za-z’'])"),
    "first person (zh)": re.compile(r"我"),
}


def run_gates(text: str) -> dict:
    banned = _hits(text, BANNED)
    lead = text.count(LEADERSHIP_ZH)
    money = _hits(text, MONEY_SHARES)
    voice = _hits(text, VOICE)
    return {
        "banned": banned,
        "leadership_zh": lead,
        "money_shares": money,
        "voice": voice,
        "ok": not banned and lead == 0 and not money and not voice,
    }
