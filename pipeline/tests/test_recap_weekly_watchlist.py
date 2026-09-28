"""T-0927-33 gave the weekly recap's next-week watchlist its own section.
T-0928-56 upgrades that again (Andy 2026-09-28「下次W40单独列出来，变成一份pdf」): it is no longer
folded into the Market_Recap PDF at all — it prints as its own Watchlist_<issue>_{EN,ZH}.pdf."""
from pathlib import Path

from pipeline.content.recap.run import headings, watchlist_pdf_path

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


def test_skill_documents_weekly_watchlist_as_its_own_pdf():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "下周观察名单" in text
    assert "Watchlist_" in text
    idx = text.index("周模式")
    weekly_section = text[idx:]
    assert "下周观察名单" in weekly_section
    assert "Watchlist_" in weekly_section


def test_content_schema_documents_the_watchlist_as_its_own_pdf_not_a_recap_section():
    text = SCHEMA_MD.read_text(encoding="utf-8")
    idx = text.index("weekly_watchlist")
    row = text[idx:text.index("\n", idx)]
    assert "Watchlist_" in row
    assert "Renders between" not in row
