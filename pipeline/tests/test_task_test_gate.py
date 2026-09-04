"""hook 丙：任务标完成前跑它点名的测试。守的是「绿」，不是「先红后绿」——
后者 hook 量不到，靠 writing-plans 的独立步骤 + SDD reviewer + TDD skill 预加载。"""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def gate():
    p = ROOT / ".claude" / "hooks" / "task_test_gate.py"
    spec = importlib.util.spec_from_file_location("task_test_gate", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_select_tests_finds_named_files_dedup_sorted(gate):
    text = "Test: pipeline/tests/test_b.py 和 pipeline/tests/test_a.py，再提一次 pipeline/tests/test_b.py"
    assert gate.select_tests(text) == ["pipeline/tests/test_a.py", "pipeline/tests/test_b.py"]


def test_no_named_tests_passes_without_running(gate):
    calls = []
    code, err = gate.verdict({"task_subject": "写事故档", "task_description": "只改 md"},
                             runner=lambda t: calls.append(t) or (0, ""))
    assert code == 0 and calls == []


def test_red_tests_block_with_exit_2_and_tail(gate):
    out = "\n".join(f"line{i}" for i in range(40)) + "\nFAILED x::y"
    code, err = gate.verdict({"task_subject": "T", "task_description": "Test: pipeline/tests/test_x.py"},
                             runner=lambda t: (1, out))
    assert code == 2 and "FAILED x::y" in err and "line0" not in err   # 只带尾巴


def test_green_tests_pass(gate):
    code, _ = gate.verdict({"task_subject": "T", "task_description": "Test: pipeline/tests/test_x.py"},
                           runner=lambda t: (0, "1 passed"))
    assert code == 0


def test_runner_crash_does_not_block(gate):
    """跑不起来（pytest 缺、超时）不等于测试红；失败模式是放行并在 stderr 留话。"""
    def boom(t): raise RuntimeError("no pytest")
    code, err = gate.verdict({"task_subject": "T", "task_description": "Test: pipeline/tests/test_x.py"}, runner=boom)
    assert code == 0 and "no pytest" in err
