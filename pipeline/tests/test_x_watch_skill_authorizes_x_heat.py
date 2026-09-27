"""T-0927-67: build_board.py 顺手写 data/output/x_heat.json，但 x-watch skill 只授权
git add data/content/x_watch/——09-24/09-25/09-26 三班都算出新值却都没提交，个股页
「X 热度」卡片(frontend/src/hooks/useXHeat.js)因此冻结在 09-23 窗口。修复是给 x-watch
skill 补一句窄口子授权；这份约定只活在 markdown 里，没有任何东西拦着下次编辑把它悄悄
改掉，所以钉一个内容断言（同类先例：test_daily_recap_skill_dryrun_guard.py）。
"""
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "x-watch" / "SKILL.md"


def _text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_landing_rights_exception_is_stated():
    text = _text()
    assert "只写 `data/content/x_watch/**`" in text
    assert "窄口子例外一个文件：`data/output/x_heat.json`" in text


def test_delivery_section_adds_x_heat_explicitly():
    text = _text()
    idx = text.index("# 送到")
    delivery = text[idx: idx + 1200]
    assert "git -C \"$WT\" add data/content/x_watch/ data/output/x_heat.json" in delivery


def test_landing_right_is_scoped_to_one_file_not_all_of_output():
    text = _text()
    assert "落地权只到这一个文件，不是整个 `data/output/`" in text
