"""I1/I2: Index Action placeholder-event and note-restatement gates (Andy 2026-09-24 ruling,
`.claude/skills/daily-recap/SKILL.md` "Index Action 的两列怎么填"). Every gate must first be
shown RED on an injected positive before its green on real content means anything, and each
failure mode (missed entirely / wired to the wrong column) gets its own check."""
import pytest

from pipeline.content.recap.index_checks import i1_placeholder_hits, i2_restatement_hits

# The real 09-23 issue content (copied verbatim from content_EN.json / content_ZH.json).
# All five index_notes rows and the UUP extra row are placeholders; TLT/GDX/USO are real
# events and must stay green (see test_i1_green_on_09_23_extra_rows_real_events below).
NINE_23_EN = {
    "index_notes": {
        "SPY": ["no new average event", "767.81, −0.72% on 1.24× · 1.14% over the 50-day, 1.30 ATR · 7,695 held twice ◇"],
        "QQQ": ["no new average event", "741.21, −0.84% on 0.91× · 4.29% over the 50-day, 3.19 ATR · 734 is the pivot to retest ◇"],
        "RSP": ["no new average event", "−0.64% · 2.34% under the 50-day, RS pctl 9.5 · 211 is the level in question ◇"],
        "DIA": ["no new average event", "−1.05% · 2.36% under the 50-day, −2.39 ATR · selling carried over from last week ◇"],
        "IWM": ["no new average event", "−1.84% · 4.07% under the 50-day · barely above the 150-day, 100-day lost Tuesday ◇"],
    },
    "extra_index_rows": [
        ["TLT", "80.46", "−1.58%", "1.67×", "lost the 21EMA", "the ten-year re-broke out after a failed breakout ◇"],
        ["UUP", "28.65", "+0.60%", "0.74×", "no new average event", "the dollar back through its breakout ◇ · the metals' pressure started here"],
        ["GDX", "93.56", "−4.36%", "1.24×", "lost the 21EMA", "worst corner of the tape: GLD lost the 50-day, SLV −4.23%"],
        ["USO", "148.83", "+3.30%", "1.01×", "reclaimed the 21EMA", "the third headwind · 10.73% over the 50-day"],
    ],
}
# 无新均线事件 (SPY/QQQ/RSP/DIA/IWM/UUP) is the ZH placeholder branch-review on T-0924-85
# caught the first cut missing entirely — "无事件" is not a substring of it.
NINE_23_ZH = {
    "index_notes": {
        "SPY": ["无新均线事件", "767.81，跌 0.72%，量比 1.24 · 高于 50 日线 1.14%，1.30 ATR · 标普 7,695 两次守住 ◇"],
        "QQQ": ["无新均线事件", "741.21，跌 0.84%，量比 0.91 · 高于 50 日线 4.29%，3.19 ATR · 734 是待回踩的整理支点 ◇"],
        "RSP": ["无新均线事件", "跌 0.64% · 低于 50 日线 2.34%，RS 分位 9.5 · 211 是当前的关键位 ◇"],
        "DIA": ["无新均线事件", "跌 1.05% · 低于 50 日线 2.36%，−2.39 ATR · 卖压从上周那个放量日延续下来 ◇"],
        "IWM": ["无新均线事件", "跌 1.84% · 低于 50 日线 4.07% · 勉强站在 150 日线上，100 日线在周二被拒后丢掉 ◇"],
    },
    "extra_index_rows": [
        ["TLT", "80.46", "−1.58%", "1.67×", "丢掉 21EMA", "十年期在一次失败突破之后再次突破 ◇——其余品种的定价都受它牵引"],
        ["UUP", "28.65", "+0.60%", "0.74×", "无新均线事件", "美元重新站回突破位之上 ◇ · 金属承压的起点在这里"],
        ["GDX", "93.56", "−4.36%", "1.24×", "丢掉 21EMA", "全场最差的一角：GLD 丢掉 50 日线，SLV 跌 4.23%"],
        ["USO", "148.83", "+3.30%", "1.01×", "收复 21EMA", "第三重逆风 · 高于 50 日线 10.73%，3.13 ATR"],
    ],
}


@pytest.mark.parametrize("content", [NINE_23_EN, NINE_23_ZH], ids=["EN", "ZH"])
def test_i1_red_on_09_23_five_rows_and_the_uup_extra_row(content):
    hits = i1_placeholder_hits(content)
    assert {h["row"] for h in hits} == {"SPY", "QQQ", "RSP", "DIA", "IWM", "UUP"}


@pytest.mark.parametrize("content", [NINE_23_EN, NINE_23_ZH], ids=["EN", "ZH"])
def test_i1_green_on_09_23_extra_rows_real_events(content):
    """09-23's TLT/GDX/USO rows had real events (lost/reclaimed the 21EMA) — must pass."""
    hits = i1_placeholder_hits(content)
    assert {h["row"] for h in hits}.isdisjoint({"TLT", "GDX", "USO"})


@pytest.mark.parametrize("event", [
    "no new average event", "No new event", "no new moving-average event",
    "无事件", "没有事件", "无新均线事件", "无新的均线事件", "均线无新事件", "—", "-",
])
def test_i1_red_on_placeholder_variants(event):
    hits = i1_placeholder_hits({"index_notes": {"SPY": [event, "still under the high ◇"]}})
    assert hits and hits[0]["row"] == "SPY"


@pytest.mark.parametrize("event", [
    "lost the 21EMA", "reclaimed 50-day", "rejected at 8/21", "站上 50 日线", "",
])
def test_i1_green_on_real_events_and_blank(event):
    hits = i1_placeholder_hits({"index_notes": {"SPY": [event, "note text"]}})
    assert hits == [], (event, hits)


def test_i1_only_checks_the_event_column_not_the_note_column():
    """A wiring bug that read the note column for I1 would false-positive here: the
    placeholder phrase sits in the note, the event column is a real event."""
    content = {"index_notes": {"SPY": ["reclaimed 50-day", "no new levels to watch ◇"]}}
    assert i1_placeholder_hits(content) == []


# ------------------------------------------------------------------ I2

@pytest.mark.parametrize("content", [NINE_23_EN, NINE_23_ZH], ids=["EN", "ZH"])
def test_i2_red_on_09_23_spy_qqq_notes(content):
    """SPY and QQQ's real 09-23 notes open with their own close and change% — the two
    rows the ruling's example ('767.81, −0.72% on 1.24×...') is drawn from."""
    pack = {"assets": {"rows": {
        "SPY": {"close": 767.81, "change_pct": -0.0072, "rel_volume": 1.24},
        "QQQ": {"close": 741.21, "change_pct": -0.0084, "rel_volume": 0.91},
    }}}
    hits = i2_restatement_hits(content, pack, weekly=False)
    assert {h["row"] for h in hits} == {"SPY", "QQQ"}


@pytest.mark.parametrize("content", [NINE_23_EN, NINE_23_ZH], ids=["EN", "ZH"])
def test_i2_green_on_09_23_extra_rows_clean_notes(content):
    """TLT/GDX/USO/UUP's real notes talk about the trade, never their own row's numbers."""
    assert i2_restatement_hits(content) == []


def test_i2_red_on_09_23_restated_note_extra_row():
    """The 09-23 example verbatim: note repeats close + change% (both land inside the
    first 20 characters) that are already printed in their own columns."""
    content = {"extra_index_rows": [
        ["Some Index", 767.81, "−0.72%", "1.24×", "rejected at the 8-day", "767.81, −0.72% on 1.24× · 7,695 held twice ◇"],
    ]}
    hits = i2_restatement_hits(content)
    assert hits and hits[0]["row"] == "Some Index"
    assert set(hits[0]["matched"]) >= {"767.81", "0.72"}


def test_i2_red_on_index_notes_row_using_pack_numbers():
    content = {"index_notes": {"SPY": ["reclaimed 50-day", "670.50 up 0.85% held twice ◇"]}}
    pack = {"assets": {"rows": {"SPY": {"close": 670.50, "change_pct": 0.0085, "rel_volume": 1.1}}}}
    hits = i2_restatement_hits(content, pack, weekly=False)
    assert hits and hits[0]["row"] == "SPY"


@pytest.mark.parametrize("note", [
    "7,695 held twice ◇",                       # one number only — allowed
    "stop under 7,580, watching the retest ◇",   # a level, not this row's own numbers
    "entry 2026-09-10, still holding ◇",         # a date, not this row's own numbers
])
def test_i2_green_single_or_unrelated_numbers(note):
    content = {"extra_index_rows": [["Some Index", 767.81, "−0.72%", "1.24×", "event", note]]}
    assert i2_restatement_hits(content) == []


def test_i2_only_looks_at_the_first_20_characters():
    """A wiring bug that scanned the whole note instead of just the first 20 characters
    would false-positive here: the row's own numbers only show up well past char 20,
    inside what reads as an unrelated aside."""
    long_note = ("waiting on the 21-day to confirm before adding, still early in the base " +
                 "(for reference, closed 767.81 on 1.24× volume) ◇")
    content = {"extra_index_rows": [["Some Index", 767.81, "−0.72%", "1.24×", "event", long_note]]}
    assert i2_restatement_hits(content) == []


def test_i2_only_checks_the_note_column_not_the_event_column():
    """A wiring bug that read the event column for I2 would false-positive here: the
    row's own numbers sit in the event column, the note column is clean."""
    content = {"extra_index_rows": [
        ["Some Index", 767.81, "−0.72%", "1.24×", "767.81, −0.72% recap", "waiting on the 50-day ◇"],
    ]}
    assert i2_restatement_hits(content) == []
