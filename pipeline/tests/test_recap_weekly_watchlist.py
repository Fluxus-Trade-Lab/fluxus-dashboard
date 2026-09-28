"""T-0927-33 gave the weekly recap's next-week watchlist its own section.
T-0928-56 upgrades that again (Andy 2026-09-28「下次W40单独列出来，变成一份pdf」): it is no longer
folded into the Market_Recap PDF at all — it prints as its own Watchlist_<issue>_{EN,ZH}.pdf.
T-0928-58 fills three gaps branch review found in that PDF: a closing paragraph
(`weekly_watchlist_close`), marking a watchlist ticker already in the book, and refusing to
guess a transcript-garbled ticker code (`ticker: null` + `unclear`, printed as ⚠️)."""
import re
from pathlib import Path

from pipeline.content.recap.run import headings, watchlist_pdf_path
from pipeline.content.recap.visual import CHROME_LABELS

SKILL_MD = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "daily-recap" / "SKILL.md"
SCHEMA_MD = Path(__file__).resolve().parents[1] / "content" / "recap" / "CONTENT_SCHEMA.md"
RECAP_JS = Path(__file__).resolve().parents[1] / "content" / "recap" / "visual_assets" / "recap_page.js"

BASE_LABELS = {
    "big_picture": "大局", "index_action": "指数动向", "market_state": "市场状态",
    "conditions": "条件", "working": "领涨", "laggards": "落后",
    "tomorrow": "下周看什么", "rules": "纪律", "education": "教育", "portfolio": "组合更新",
}


def test_headings_never_folds_weekly_watchlist_into_the_recap_pdf():
    """Positive control (T-0928-56): on origin/main before this fix, weekly_watchlist still
    lands between tomorrow and rules when present — this must now be false, in every case."""
    labels = dict(BASE_LABELS, weekly_k="周线", weekly_watchlist="下周观察名单")
    content = {"lang": "ZH", "title": "T", "labels": labels,
               "weekly_watchlist": [{"group": "半导体", "items": [{"ticker": "SMCI", "note": "跌破 50 日均线 ◇"}]}]}
    keys = [k for k, _ in headings(content, weekly=True)]
    assert "weekly_watchlist" not in keys

    content_daily = {"lang": "ZH", "title": "T", "labels": BASE_LABELS}
    assert "weekly_watchlist" not in [k for k, _ in headings(content_daily, weekly=False)]


def test_watchlist_pdf_path_is_named_and_placed_beside_the_recap_pdf():
    p = watchlist_pdf_path(Path("/tmp/2026-W40/pdf"), "2026-W40", "ZH")
    assert p == Path("/tmp/2026-W40/pdf/Watchlist_2026-W40_ZH.pdf")
    p_en = watchlist_pdf_path(Path("/tmp/2026-W40/pdf"), "2026-W40", "EN")
    assert p_en.name == "Watchlist_2026-W40_EN.pdf"


def test_recap_page_js_has_its_own_layout_for_the_watchlist_and_no_longer_embeds_it():
    js = RECAP_JS.read_text(encoding="utf-8")
    assert "function layoutW(" in js
    state_wiring = js.index("state + wiring")
    layout_a = js[js.index("function layoutA("):js.index("function layoutB(")]
    layout_b = js[js.index("function layoutB("):state_wiring]
    assert "weeklyWatchlist" not in layout_a
    assert "weeklyWatchlist" not in layout_b
    assert 'layout === "W" ? layoutW' in js


def test_layout_w_prints_its_title_exactly_once():
    """Branch review (T-0928-56) caught a first draft that printed L.weekly_watchlist three times
    on one page (masthead + <h2> + sec() heading) — nothing in the render gates would have caught
    that before a human saw the W40 PDF. layoutW must use that exact label exactly once.
    T-0928-58 adds a distinct label, `L.weekly_watchlist_close`, for the closing paragraph —
    it must not be counted as a second use of the watchlist's own title."""
    js = RECAP_JS.read_text(encoding="utf-8")
    start = js.index("function layoutW(")
    body = js[start:js.index("\n  }", start)]
    assert len(re.findall(r"L\.weekly_watchlist\b(?!_close)", body)) == 1
    assert "<h2" not in body  # no separate headline duplicating the section title


def test_layout_w_renders_his_closing_paragraph_when_present_as_its_own_section():
    """T-0928-58: 「末页放他自己的收尾（指数与轮动那一段）」 — a second section, not folded into
    the grouped list, and only when the video actually had a closing read."""
    js = RECAP_JS.read_text(encoding="utf-8")
    start = js.index("function layoutW(")
    body = js[start:js.index("\n  }", start)]
    assert "c.weekly_watchlist_close" in body
    assert "L.weekly_watchlist_close" in body


def test_weekly_watchlist_marks_a_ticker_already_in_the_book():
    """Andy called this out live as useful (W39 hit HOOD/ARM/DELL) — a watchlist name that's
    already a position must be marked, checked against this issue's own book.pos."""
    js = RECAP_JS.read_text(encoding="utf-8")
    start = js.index("function weeklyWatchlist(")
    body = js[start:js.index("\n  }", start)]
    assert "is.book" in body and ".pos" in body
    assert "p_held" in body


def test_weekly_watchlist_marks_a_garbled_ticker_instead_of_guessing_it():
    """Andy:「字幕把代码听糊的…不许替它填代码：标⚠️并写他讲的特征，让 Andy 自己认」— a null ticker
    prints the warning plus the features he described, never a guessed code."""
    js = RECAP_JS.read_text(encoding="utf-8")
    start = js.index("function weeklyWatchlist(")
    body = js[start:js.index("\n  }", start)]
    assert "it.ticker" in body
    assert "unclear" in body
    assert "⚠" in body  # warning sign


def test_chrome_labels_carry_the_held_marker_in_both_languages():
    """Chrome, not issue labels (same reasoning as p_cost/leg_held) — an issue written before
    this existed still renders the marker."""
    for lang in ("EN", "ZH"):
        assert CHROME_LABELS[lang].get("p_held")


def test_skill_documents_weekly_watchlist_as_its_own_pdf():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "下周观察名单" in text
    assert "Watchlist_" in text
    idx = text.index("周模式")
    weekly_section = text[idx:]
    assert "下周观察名单" in weekly_section
    assert "Watchlist_" in weekly_section


def test_skill_documents_the_three_t_0928_58_writing_requirements():
    """Without a written rule, the writing session has no basis to do any of these three
    (T-0928-58 background: 「出片班没有依据照做」)."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "weekly_watchlist_close" in text
    assert "⚠" in text
    assert "听糊" in text or "unclear" in text
    assert "持仓" in text or "book.pos" in text


def test_content_schema_documents_the_watchlist_as_its_own_pdf_not_a_recap_section():
    text = SCHEMA_MD.read_text(encoding="utf-8")
    idx = text.index("weekly_watchlist")
    row = text[idx:text.index("\n", idx)]
    assert "Watchlist_" in row
    assert "Renders between" not in row


def test_content_schema_documents_the_three_t_0928_58_gaps():
    """The closing paragraph, the holdings cross-reference, and the garbled-ticker ⚠️ rule
    must each have a written spec, not just code — that's the acceptance bar for T-0928-58."""
    text = SCHEMA_MD.read_text(encoding="utf-8")
    assert "weekly_watchlist_close" in text
    assert re.search(r"`unclear`", text)
    assert "⚠" in text
    idx = text.index("weekly_watchlist")
    row = text[idx:text.index("weekly_watchlist_close", idx)]
    assert "book.pos" in row or "held" in row.lower()
