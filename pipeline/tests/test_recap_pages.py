"""Page-fill check + fixed rules: prove the check goes red on the real failure shape first."""
from pipeline.content.recap.constants import check_rules
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


GOOD_EN = [f"session rule {i}" for i in range(6)] + ["Never serious trouble until S&P breaks the 200-day — well above it"]
GOOD_ZH = [f"当天第 {i} 条" for i in range(6)] + ["标普不破 200 日线，谈不上真正的麻烦——离得还远"]


def test_rules_check_accepts_session_rules_with_fixed_rule7():
    assert check_rules(GOOD_EN, "EN") is None and check_rules(GOOD_ZH, "ZH") is None


def test_rules_check_red_on_wrong_count():
    assert check_rules(GOOD_EN[:6], "EN") and check_rules(GOOD_EN + ["extra"], "EN") and check_rules(None, "ZH")


def test_stale_gate_red_on_verbatim_0904_rules():
    from pipeline.content.recap.constants import STALE_0904
    for lang in ("EN", "ZH"):
        injected = list(STALE_0904[lang]) + [GOOD_EN[6] if lang == "EN" else GOOD_ZH[6]]
        assert "09-04" in check_rules(injected, lang, "2026-09-11")


def test_stale_gate_red_on_near_duplicate():
    near = ["7,800 is the S&P upside pivot; the declining tops line is the near term cap"] + GOOD_EN[1:]
    assert "09-04" in check_rules(near, "EN", "2026-09-10")
    near_zh = ["7,800 是标普往上的 pivot，下降趋势线是近处的顶部"] + GOOD_ZH[1:]
    assert "09-04" in check_rules(near_zh, "ZH", "2026-09-10")


def test_stale_gate_green_for_session_rules_and_exempts_0904_itself():
    from pipeline.content.recap.constants import STALE_0904
    session = ["QQQ has to hold 715; SPX has to get back above 7,650"] + GOOD_EN[1:]
    assert check_rules(session, "EN", "2026-09-09") is None
    assert check_rules(list(STALE_0904["EN"]) + [GOOD_EN[6]], "EN", "2026-09-04") is None


from pipeline.content.recap.pages import check_x_pages, page_sections  # noqa: E402

P_BODY = "\n".join(f"body line {i}" for i in range(20))


def test_x1_red_when_book_shows_on_page_4_en():
    book = P_BODY + "\n PORTFOLIO UPDATE\n RETURN        CASH       OPEN NAMES\n HOOD      long     2026-08-19    +4.26R\n"
    text = "\f".join([P_BODY, P_BODY, P_BODY, book, P_BODY]) + "\f"
    r = check_x_pages(text, "EN", ["HOOD"])
    assert not r["ok"] and 4 in r["x1_hits"]
    assert {"Portfolio Update", "cell:RETURN", "cell:CASH", "book row:HOOD"} <= set(r["x1_hits"][4])


def test_x1_red_zh_and_letter_spaced_heading():
    book = P_BODY + "\n组 合 更 新\n收益      现金      持仓名数\n浮动 R    已实现 R\n"
    r = check_x_pages("\f".join([P_BODY, book, P_BODY, P_BODY]) + "\f", "ZH")
    assert 2 in r["x1_hits"] and "组合更新" in r["x1_hits"][2]


def test_x1_green_on_prose_that_only_mentions_cash_or_return():
    prose = P_BODY + "\nHigh cash is still a good position into CPI; a return to the 50-day.\n10 年期收益率到了高点，高现金仍是好位置。\n"
    prose += "SWKS   +19.4%   week; +5.1% Friday\n"
    assert check_x_pages("\f".join([prose] * 5) + "\f", "EN", ["SWKS"])["x1_ok"]
    assert check_x_pages("\f".join([prose] * 5) + "\f", "ZH", ["SWKS"])["x1_ok"]


def test_x2_red_under_four_pages():
    r = check_x_pages("\f".join([P_BODY] * 3) + "\f", "EN")
    assert not r["x2_ok"] and not r["ok"]


def test_page_sections_are_case_and_spacing_tolerant():
    text = "T H E  B I G  P I C T U R E\nx\f组 合 更 新\ny\f"
    assert page_sections(text, ["The Big Picture", "组合更新"]) == [["The Big Picture"], ["组合更新"]]


# Positive controls, both failure modes (T-0930-28): a heading must be recognised when it genuinely
# opens a page, and must be ignored when its characters merely turn up inside a sentence elsewhere.
def test_page_sections_ignore_a_heading_word_embedded_in_prose():
    # 2026-09-29 real shape: 情绪 (the Sentiment heading) appeared mid-sentence in ZH body prose under
    # 交易纪律; the old substring-anywhere check misread the page as if Sentiment opened there too.
    text = "\f".join(["交易纪律\n区分这两个阶段的不是情绪，是几何。", "组 合 更 新\ny"]) + "\f"
    assert page_sections(text, ["情绪", "交易纪律", "组合更新"]) == [["交易纪律"], ["组合更新"]]


def test_page_sections_still_catch_a_heading_line_with_a_fused_note():
    # <h3> prints heading + note (a score, the lesson's own title) on the same line — the note must
    # not stop the heading itself from being recognised as opening the page.
    text = "教学 底部定风险，催化剂只定日子\n正文。\f"
    assert page_sections(text, ["教学"]) == [["教学"]]


def test_l1_reds_on_a_real_overflow_detected_via_page_sections():
    # Positive control, overflow direction: RULES genuinely opens page 5 as its own heading line —
    # the fix for the false-red above must not also swallow a real overflow.
    from pipeline.content.recap.pages import check_layout

    labels = ["TITLE", "CONDITIONS", "LEADERS", "TOMORROW", "RULES", "THE LESSON", "PORTFOLIO UPDATE"]
    text = "\f".join(["TITLE\np1.", "CONDITIONS\np2.", "LEADERS\np3.", "TOMORROW\np4.",
                      "RULES\n1 rule.", "THE LESSON\nbody.", "PORTFOLIO UPDATE\nbook."]) + "\f"
    sections = page_sections(text, labels)
    r = check_layout(text, sections, "THE LESSON", "PORTFOLIO UPDATE")
    assert not r["ok"] and any("RULES" in h for h in r["hits"])


def test_rules_check_red_when_rule7_loses_the_fixed_opening():
    bad = GOOD_EN[:6] + ["Crude staying weak matters most"]
    assert "rule 7" in check_rules(bad, "EN")
    assert "rule 7" in check_rules(GOOD_ZH[:6] + ["标普跌破 200 日线之前都还好"], "ZH")
