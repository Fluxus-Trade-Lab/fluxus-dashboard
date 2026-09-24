"""I1/I2: Index Action placeholder-event and note-restatement gates (Andy 2026-09-24 ruling,
`.claude/skills/daily-recap/SKILL.md` "Index Action 的两列怎么填"). Every gate must first be
shown RED on an injected positive before its green on real content means anything, and each
failure mode (missed entirely / wired to the wrong column) gets its own check."""
import pytest

from pipeline.content.recap.index_checks import i1_placeholder_hits, i2_restatement_hits

# The actual 09-23 issue: all five index_notes rows read "no new average event" in the
# technical-event column (SKILL.md [2026-09-24]).
NINE_23_CONTENT = {
    "index_notes": {
        "SPY": ["no new average event", "still under the 7,816 high ◇"],
        "QQQ": ["no new average event", "consolidating near the highs, 734 pivot ◇"],
        "RSP": ["no new average event", "211 to watch as support ◇"],
        "DIA": ["no new average event", "watching last Wednesday's heavy-volume low ◇"],
        "IWM": ["no new average event", "could test the 200-day next ◇"],
    },
}


def test_i1_red_on_09_23_five_rows():
    hits = i1_placeholder_hits(NINE_23_CONTENT)
    assert {h["row"] for h in hits} == {"SPY", "QQQ", "RSP", "DIA", "IWM"}


@pytest.mark.parametrize("event", [
    "no new average event", "No new event", "no new moving-average event",
    "无事件", "没有事件", "—", "-",
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


def test_i1_green_on_09_23_extra_rows_real_events():
    """09-23's extra_index_rows had real events like 'lost the 21EMA' — must pass."""
    content = {"extra_index_rows": [
        ["MDY", 620.0, -0.008, 1.1, "lost the 21EMA", "watching for a retest ◇"],
        ["XLK", 250.0, 0.004, 0.9, "reclaimed the 8-day", "leadership intact ◇"],
    ]}
    assert i1_placeholder_hits(content) == []


def test_i1_only_checks_the_event_column_not_the_note_column():
    """A wiring bug that read the note column for I1 would false-positive here: the
    placeholder phrase sits in the note, the event column is a real event."""
    content = {"index_notes": {"SPY": ["reclaimed 50-day", "no new levels to watch ◇"]}}
    assert i1_placeholder_hits(content) == []


# ------------------------------------------------------------------ I2

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
