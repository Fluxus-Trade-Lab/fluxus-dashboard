"""hook 丙：任务标完成前跑它点名的测试。守的是「绿」，不是「先红后绿」——
后者 hook 量不到，靠 writing-plans 的独立步骤 + SDD reviewer + TDD skill 预加载。"""
import importlib.util
import subprocess
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


def test_pytest_unavailable_passes_without_running(gate, monkeypatch):
    """pytest 没装时真实 `_run` **不抛异常**——它返回 (1, "No module named pytest")，
    和「2 个测试红了」在返回码上完全同形。所以放行不能靠 except，只能靠开跑前探一次。
    这条特意不传 runner：走的是真 `_run`，探测失灵就会真去跑 pytest 并挡住。"""
    monkeypatch.setattr(gate, "find_spec", lambda name: None, raising=False)
    code, err = gate.verdict({"task_subject": "T",
                              "task_description": "Test: pipeline/tests/test_x.py"})
    assert code == 0 and "pytest" in err


def test_timeout_does_not_block(gate):
    """超时是真 `_run` 唯一会抛的那条路（subprocess.run(timeout=) 抛 TimeoutExpired），异常放行分支保留。"""
    def slow(t): raise subprocess.TimeoutExpired(cmd="pytest", timeout=gate.TIMEOUT_S)
    code, err = gate.verdict({"task_subject": "T", "task_description": "Test: pipeline/tests/test_x.py"},
                             runner=slow)
    assert code == 0 and "没跑起来" in err


def test_rc5_no_tests_collected_passes(gate):
    """rc=5 = 一个都没收集到。文件在、里面没测试，不是红，放行并留话。"""
    code, err = gate.verdict({"task_subject": "T", "task_description": "Test: pipeline/tests/test_x.py"},
                             runner=lambda t: (5, "no tests ran"))
    assert code == 0 and err


def test_rc4_missing_file_still_blocks(gate):
    """rc=4 = 点名的测试文件不存在。R14 的手动验收动作依赖它挡住，别一起放行。"""
    code, err = gate.verdict({"task_subject": "T", "task_description": "Test: pipeline/tests/test_x.py"},
                             runner=lambda t: (4, "ERROR: file or directory not found"))
    assert code == 2
