"""hook 乙只查留痕不查对错。失败模式一律放行——卡死会话比漏一行贵。"""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gate():
    p = ROOT / ".claude" / "hooks" / "skill_stop_gate.py"
    spec = importlib.util.spec_from_file_location("skill_stop_gate", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_blocks_when_no_receipt(gate):
    v = gate.verdict({"last_assistant_message": "干完了，收工。", "stop_hook_active": False})
    assert v.get("decision") == "block" and "skill-used" in v["reason"]


@pytest.mark.parametrize("line", [
    "skill-used: superpowers:brainstorming · 批",
    "skill-skipped: fable-voice · 本轮是英文",
    "skill-none: 本轮无适用 skill",
])
def test_any_receipt_passes(gate, line):
    assert gate.verdict({"last_assistant_message": f"收工。\n{line}", "stop_hook_active": False}) == {}


def test_stop_hook_active_passes(gate):
    """已经在补写循环里，再拦就是死锁。官方另有 8 次上限兜底，但别靠它。"""
    assert gate.verdict({"last_assistant_message": "没写", "stop_hook_active": True}) == {}


def test_missing_field_passes(gate):
    assert gate.verdict({}) == {}


def test_receipt_must_be_a_line_start_not_inside_code(gate):
    """正文里引用了规矩不算留痕；留痕是那一行本身。"""
    v = gate.verdict({"last_assistant_message": "规矩是要写 `skill-used:` 那一行，我下次写。", "stop_hook_active": False})
    assert v.get("decision") == "block"
