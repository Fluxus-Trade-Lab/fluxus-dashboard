"""L1 (Andy 09-13, final): non-lesson, non-book content ends by page 4, the book owns the last page,
the lesson may span pages 4–5, and no page opens mid-sentence."""
import pytest

from pipeline.content.recap.pages import check_layout, sentence_split_breaks

EDU, BOOK = "THE LESSON", "PORTFOLIO UPDATE"
FIT = [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["RULES", EDU], [BOOK]]          # 4+1, lesson fitted
SPILL = [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["RULES", EDU], [], [BOOK]]     # 5+1, lesson spilled
STRAY = [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["TOMORROW"], ["RULES", EDU], [BOOK]]  # rules pushed to p5
TEXT = "\f".join(["p1 body.", "p2 body.", "p3 body.", "The lesson opens here.", "A new sentence starts here.", "Book."]) + "\f"


def test_l1_green_when_the_lesson_fits_on_page_four():
    r = check_layout(TEXT, FIT, EDU, BOOK)
    assert r["ok"] and r["pages"] == 5 and r["book_page"] == 5 and r["edu_pages"] == [4]


def test_l1_green_when_the_lesson_spills_to_page_five():
    r = check_layout(TEXT, SPILL, EDU, BOOK)
    assert r["ok"] and r["pages"] == 6 and r["edu_pages"] == [4, 5]


def test_l1_red_when_any_other_section_reaches_page_five():
    r = check_layout(TEXT, STRAY, EDU, BOOK)
    assert not r["ok"] and "RULES" in r["hits"][0]


def test_l1_red_when_the_book_does_not_own_the_last_page():
    assert not check_layout(TEXT, [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["RULES", EDU], [BOOK, "EXTRA"]], EDU, BOOK)["ok"]
    assert not check_layout(TEXT, [["TITLE"], [BOOK], ["LEADERS"], [EDU], [BOOK]], EDU, BOOK)["ok"]


def test_l1_red_on_a_seven_page_daily_but_a_weekly_may_run_long():
    seven = [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["RULES", EDU], [], [], [BOOK]]
    assert not check_layout(TEXT, seven, EDU, BOOK)["ok"]
    assert check_layout(TEXT, [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["RULES"], [EDU], [BOOK]], EDU, BOOK, weekly=True)["ok"]


@pytest.mark.parametrize("prev, cur, red", [
    ("the averages have to stop diverging", "first, then price tightens", True),   # mid-sentence
    ("the averages have to stop diverging first.", "Price then tightens", False),  # sentence ended
    ("SWKS +19.4%", "Semis broad theme", False),                                   # table row, not prose
])
def test_sentence_split_control(prev, cur, red):
    text = "\f".join(["p1.", "p2.", "p3.", prev, cur, "Book."]) + "\f"
    assert bool(sentence_split_breaks(text, [5])) is red


def test_l1_red_when_the_lesson_breaks_inside_a_sentence():
    text = "\f".join(["p1.", "p2.", "p3.", "the 20 flattens, drifts into the 50, and price", "tightens between the two", "Book."]) + "\f"
    r = check_layout(text, SPILL, EDU, BOOK)
    assert not r["ok"] and "mid-sentence" in r["hits"][0]
