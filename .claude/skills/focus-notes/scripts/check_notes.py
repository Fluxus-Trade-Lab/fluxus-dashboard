#!/usr/bin/env python3
"""Gate for focus notes: every number a sentence prints must be on that ticker's
own fact card, no sentence may tell the reader to buy or sell, and (Andy
2026-10-01 「B1」) no sentence may repeat the group: the page prints the group's
name, state and acceleration in its own column, so the clause is about the
stock alone -- the group's name and the four state words are refused.

Accepts either
  - the daily file   {"setups": ..., "notes": {TICKER: {"zh": s, "en": s}}, ...}
  - or two files     cards.json  notes.json   (notes = {TICKER: "zh sentence"})

Numbers: a card number matches at 0/1/2 dp, sign ignored. Rule names are allowed
constants (21EMA, 50SMA, 52-week, §11.1 and its 25% line, the 4-ATR band edge,
"one month", "three steps"). Cross-ticker comparisons ("lowest of the four
refiners") are NOT checked -- the writer must verify those by hand.

Positive control (2026-10-01): STX 0.84->0.48, RNG -33.6->-3.6, and MPC's
sentence on VLO's card are all flagged; an injected 「建议买入」 is flagged.

exit 1 when anything is flagged.
"""
import json
import re
import sys

ALLOWED = {25, 4, 21, 50, 52, 1, 0, 3, 10, 20}
ADVICE = re.compile(r"建议|应该|买入|卖出|加仓|减仓|止损|\bbuy\b|\bsell\b|\bshould\b|\brecommend|\bentry\b|\bstop[- ]loss",
                    re.I)


def numbers_in(card):
    out = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            for d in (0, 1, 2):
                out.add(round(abs(x), d))

    walk(card)
    return out


STATE_WORDS = ("Leading", "Improving", "Weakening", "Lagging")


def group_words(card):
    words = list(STATE_WORDS)
    for k in ("theme", "ind"):
        g = card.get(k) or {}
        if g.get("name"):
            words.append(g["name"])
    return words


def check_sentence(card, s):
    bad = []
    for w in group_words(card):
        if w in s:
            bad.append(("group", w))
    have = numbers_in(card)
    for m in re.findall(r"\d+(?:\.\d+)?", s.replace("§11.1", "")):
        v = float(m)
        if v not in ALLOWED and v not in have:
            bad.append(("number", m))
    a = ADVICE.search(s)
    if a:
        bad.append(("advice", a.group(0)))
    return bad


# Chinese notes speak the site's Chinese (Andy 2026-10-03: 「整个网页需要有完整的
# 中文和英文界面」). These English vocabulary words have approved Chinese twins
# in frontend/src/i18n (收着做 / 多空分歧 / 受损 / 减仓 / 领先 …), and 转弱 is not
# the glossary word for Weakening (走弱). Caught on the 10-02 _market note.
ZH_FORBIDDEN = re.compile(r"\b(full|dim|avoid|BULLISH|BEARISH|MIXED|OVERBOUGHT|OVERSOLD|Damaged|Healthy|Reduced|selective|Leading|Weakening|Improving|Lagging|score|Regime)\b|转弱")


def check_zh_vocab(s):
    return [("zh-vocab", m.group(0)) for m in ZH_FORBIDDEN.finditer(s)]


def check(cards_by_ticker, notes):
    flagged = []
    for t, val in notes.items():
        if isinstance(val, dict) and isinstance(val.get("zh"), str):
            for b in check_zh_vocab(val["zh"]):
                flagged.append((t, "zh", b))
    for t, val in notes.items():
        if t.startswith("_"):
            continue
        if t not in cards_by_ticker:
            flagged.append((t, "-", ("no card", t)))
            continue
        langs = val if isinstance(val, dict) else {"zh": val}
        for lang, s in langs.items():
            for b in check_sentence(cards_by_ticker[t], s):
                flagged.append((t, lang, b))
    return flagged


def _cards(doc):
    return {r["t"]: r for k in doc["setups"] for r in doc["setups"][k]["rows"]}


if __name__ == "__main__":
    first = json.load(open(sys.argv[1]))
    if len(sys.argv) > 2:
        notes = json.load(open(sys.argv[2]))
    else:
        notes = first["notes"]
    bad = check(_cards(first), notes)
    print("flagged:", bad)
    sys.exit(1 if bad else 0)
