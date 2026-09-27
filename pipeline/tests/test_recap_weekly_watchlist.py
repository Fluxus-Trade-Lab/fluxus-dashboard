"""T-0927-33: weekly recap's next-week watchlist is its own section, never folded into
led / lagged / tomorrow (Andy 2026-09-27「下次周复盘里单独分开出这个，不合并到一起」)."""
from pathlib import Path

from pipeline.content.recap.run import headings

SKILL_MD = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "daily-recap" / "SKILL.md"

BASE_LABELS = {
    "big_picture": "大局", "index_action": "指数动向", "market_state": "市场状态",
    "conditions": "条件", "working": "领涨", "laggards": "落后",
    "tomorrow": "下周看什么", "rules": "纪律", "education": "教育", "portfolio": "组合更新",
}


def test_headings_places_weekly_watchlist_between_tomorrow_and_rules_when_present():
    labels = dict(BASE_LABELS, weekly_k="周线", weekly_watchlist="下周观察名单")
    content = {"lang": "ZH", "title": "T", "labels": labels,
               "weekly_watchlist": [{"group": "半导体", "items": [{"ticker": "SMCI", "note": "跌破 50 日均线 ◇"}]}]}
    keys = [k for k, _ in headings(content, weekly=True)]
    assert "weekly_watchlist" in keys
    assert keys.index("tomorrow") < keys.index("weekly_watchlist") < keys.index("rules")


def test_headings_omits_weekly_watchlist_for_dailies_or_when_empty():
    content = {"lang": "ZH", "title": "T", "labels": BASE_LABELS}
    assert "weekly_watchlist" not in [k for k, _ in headings(content, weekly=False)]

    weekly_labels = dict(BASE_LABELS, weekly_k="周线")
    empty = {"lang": "ZH", "title": "T", "labels": weekly_labels, "weekly_watchlist": []}
    assert "weekly_watchlist" not in [k for k, _ in headings(empty, weekly=True)]

    no_field = {"lang": "ZH", "title": "T", "labels": weekly_labels}
    assert "weekly_watchlist" not in [k for k, _ in headings(no_field, weekly=True)]


def test_skill_documents_weekly_watchlist_as_its_own_section():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "下周观察名单" in text
    assert "weekly_watchlist" in text
    idx = text.index("周模式")
    weekly_section = text[idx:]
    assert "下周观察名单" in weekly_section
    assert "不合并" in weekly_section or "不并入" in weekly_section or "单独分开" in weekly_section
