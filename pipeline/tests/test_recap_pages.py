"""Page-fill check + fixed rules: prove the check goes red on the real failure shape first."""
from pipeline.content.recap.constants import RULES_EN, RULES_ZH
from pipeline.content.recap.pages import check_pages

HEAD = "FLUXUS CAPITAL                                   DAILY MARKET RECAP\n\n"
def foot(n, m): return f"\n\n                FLUXUS CAPITAL · CONFIDENTIAL · {n} / {m}\n"

FULL = HEAD + "\n".join(f"body line {i}" for i in range(40))


def test_healthy_document_passes():
    text = "\f".join([FULL + foot(1, 2), FULL + foot(2, 2)]) + "\f"
    r = check_pages(text)
    assert r["ok"] and r["pages"] == 2, r


def test_red_on_last_page_with_one_footnote_line():
    # the exact 2026-09-11 v1 shape: page 5 held a single footnote
    text = "\f".join([FULL + foot(1, 2), HEAD + "◇ = from outside our data layer" + foot(2, 2)]) + "\f"
    r = check_pages(text)
    assert not r["ok"] and r["thin_pages"] == [2], r


def test_red_on_a_blank_middle_page():
    text = "\f".join([FULL + foot(1, 3), HEAD + foot(2, 3), FULL + foot(3, 3)]) + "\f"
    assert check_pages(text)["thin_pages"] == [2]


def test_chrome_lines_are_not_counted_as_body():
    text = HEAD + "one\ntwo" + foot(1, 1)
    assert check_pages(text)["body_lines"] == [2]


def test_rules_are_seven_and_end_with_the_200_day():
    assert len(RULES_EN) == 7 and len(RULES_ZH) == 7
    assert "200-day" in RULES_EN[-1] and "200 日线" in RULES_ZH[-1]
