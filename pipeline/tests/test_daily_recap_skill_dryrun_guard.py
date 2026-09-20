"""T-0920-30: 09-19 一次「试跑」没重定向输出目录，直接写进了生产期号目录，锁死幂等判断，
把 09-20 的正班闸空转了一整轮。修复是把重定向规矩写进 daily-recap skill 正文——这份约定
只活在 markdown 里，没有任何东西拦着下次编辑把它悄悄改掉，所以钉一个内容断言。"""
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "daily-recap" / "SKILL.md"


def _text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_trial_run_rule_present():
    text = _text()
    assert "试跑铁律" in text
    assert 'export FLUXUS_RECAP_ROOT="$HOME/Documents/Trading/01_Market_Reports_Daily/_dryrun_$(date +%m%d)"' in text


def test_weekly_idempotency_check_is_dryrun_aware():
    text = _text()
    idx = text.index("### 第 0 步 · 时钟与幂等")
    step0 = text[idx: idx + 600]
    assert "${FLUXUS_RECAP_ROOT:-$HOME/Documents/Trading/01_Market_Reports_Daily}" in step0
    assert "若 `~/Documents/Trading/01_Market_Reports_Daily/" not in step0
