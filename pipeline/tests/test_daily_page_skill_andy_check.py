from pathlib import Path

SKILL_PATH = (
    Path(__file__).resolve().parents[2] / ".claude" / "skills" / "daily-page" / "SKILL.md"
)


def test_daily_page_requires_live_check_before_needs_andy_ages_past_3_days():
    text = SKILL_PATH.read_text()
    assert "挂满 3 天的 needs_andy，上页前必须现场核过" in text
    assert "checked:" in text
    assert "无法现场核" in text
    assert "只读 status 字段就上页 = 违规" in text
