"""T-0927-34: Andy「「A，不是 B」这个形状全页 12 处，那适量更改可以的」——两条可数闸
（对比收尾式 ≤4 处、破折号 ≤4/千字）目前只活在这份 markdown 里，没有代码盯着它，钉一个
内容断言防止下次编辑悄悄改掉（同 test_daily_recap_skill_dryrun_guard.py 的做法）。"""
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "daily-recap" / "SKILL.md"


def _text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_style_gate_thresholds_are_pinned():
    text = _text()
    idx = text.index("### [2026-09-27] 文风自查：两条可数闸")
    section = text[idx: idx + 1600]
    assert "对比收尾式（含变体）≤4 处" in section
    assert "破折号 `——` ≤4 个/千字" in section
    assert "`The Rules` 与 `Education` 两节允许各留一处对比句" in section


def test_style_gate_is_documented_as_manual_not_render_gate():
    text = _text()
    idx = text.index("闸含：专名（含 Grow）")
    line = text[idx: idx + 700]
    assert "文风自查" in line
    assert "人工检查项，不在上面这套 render 自动闸里" in line


def test_the_figure_echo_ruling_is_pinned():
    """T-0930-30: Andy 2026-09-30 retired half of the 2026-09-24 figure judgement."""
    text = _text()
    idx = text.index("### [2026-09-30] 图承担结构，正文不复述图上标注")
    section = text[idx: idx + 2400]
    assert "「教学图和教学好像有点重复。」" in section
    assert "「备选B也不是很好。」" in section
    assert "正文不得逐条复述图上标注" in section
    assert "「正文里出现过」这一条**作废**" in section
