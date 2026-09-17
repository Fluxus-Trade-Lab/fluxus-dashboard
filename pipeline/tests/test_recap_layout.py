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


# 2026-09-16 EN: the lesson started at the TOP of page 5, the rules ended on page 4 — a legal 6-page daily.
# L1 used to assume "a page that doesn't open with the last active section continues it", and read page 5
# as still carrying the rules. A page continues the previous section only if its first body line is not
# a section heading. Headings print upper-case (CSS), prose does not — so a paragraph that merely starts
# with a heading's word still counts as continuation.
TOP = [["TITLE"], ["CONDITIONS"], ["LEADERS"], ["RULES"], [EDU], [BOOK]]


def _pages(p5_first_line):
    return "\f".join(["p1.", "p2.", "p3.", "RULES\n1 Know the priced range.",
                      f"FLUXUS CAPITAL · DAILY MARKET RECAP\n{p5_first_line}\nMore lesson text.", "Book."]) + "\f"


def test_l1_green_when_the_lesson_starts_at_the_top_of_page_five():
    r = check_layout(_pages("T H E  L E S S O N      A Midweek Break Is a Draft"), TOP, EDU, BOOK)
    assert r["ok"], r["hits"]
    assert r["pages"] == 6 and r["edu_pages"] == [5]


@pytest.mark.parametrize("first", [
    "7 Never serious trouble until the 200-day.",   # rules text ran over, lesson heading further down
    "The lesson learned here is simple.",          # prose that merely starts with the heading's words
])
def test_l1_red_when_page_five_opens_with_carried_over_text(first):
    r = check_layout(_pages(first), TOP, EDU, BOOK)
    assert not r["ok"] and "RULES" in r["hits"][0]


def test_l1_matches_a_title_case_label_against_its_upper_case_print():
    # content labels are title case ("Education"); the PDF prints them upper-case
    sections = [["Title"], ["Conditions"], ["Leaders"], ["The Rules"], ["Education"], ["Portfolio Update"]]
    text = "\f".join(["p1.", "p2.", "p3.", "THE RULES\n1 rule.", "E D U C A T I O N   A lesson\nbody.", "Book."]) + "\f"
    assert check_layout(text, sections, "Education", "Portfolio Update")["ok"]
