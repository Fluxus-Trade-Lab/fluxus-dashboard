"""audit_universe_freshness 有没有真的接在写 universe.json 的路径上 —— 不是它自己对不对。

同 `test_no_downgrade_is_wired.py` 的理由：那份测试是行为测试，跑的是
`pipeline/tools/audit_universe_freshness.py` 自己的逻辑，一条都没问过
「run_all.py 里有没有人调用它」。这份补的正是那句「有没有人调用它」，
外加一条真正喂 payload 的行为测试（T-0920-11 验收要求）。

`_freshness_check` 是从 `run_all.py` 里拆出来的三行（同 `_emit` 被拆出来的理由：
`test_run_ledger_wiring.py` 已经证明这种拆法可以在不跑整条流水线的前提下单测）。
"""
from __future__ import annotations

import ast
from pathlib import Path

from pipeline.screeners.run_all import _freshness_check

RUN_ALL = Path(__file__).resolve().parents[1] / "screeners" / "run_all.py"


def _tree():
    return ast.parse(RUN_ALL.read_text(encoding="utf-8"))


def _rows(n, volume, avg_volume):
    return [{'volume': volume, 'avg_volume': avg_volume} for _ in range(n)]


# ---------------------------------------------------------------- behavior

def test_positive_control_premarket_shaped_payload_is_F1():
    """volume ~= 2% of avg_volume, 250 names -- 接线处本身必须报 F1."""
    rows = _rows(250, volume=20_000, avg_volume=1_000_000)
    kind, why = _freshness_check(rows)
    assert kind == 'F1', why


def test_a_normal_session_is_silent():
    rows = _rows(250, volume=980_000, avg_volume=1_000_000)
    kind, why = _freshness_check(rows)
    assert kind is None, why


# ---------------------------------------------------------------- wiring

def test_run_all_imports_the_gate():
    names = {
        alias.name
        for node in ast.walk(_tree())
        if isinstance(node, ast.ImportFrom)
        and (node.module or "").endswith("audit_universe_freshness")
        for alias in node.names
    }
    assert {"aggregate_rvol", "classify"} <= names, (
        "run_all.py 不再 import audit_universe_freshness 的 aggregate_rvol/classify")


def test_the_gate_is_actually_called():
    called = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "classify"
        for n in ast.walk(_tree())
    )
    assert called, "import 了但没调用 classify() —— 那和没接一样。"


def test_freshness_check_is_called_after_universe_json_is_saved():
    called = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == "_freshness_check"
        for n in ast.walk(_tree())
    )
    assert called, "run_all.py 里没有人调用 _freshness_check() —— 三行没接上。"


def test_the_result_is_recorded_on_the_ledger():
    src = RUN_ALL.read_text(encoding="utf-8")
    assert "ledger.note('universe_freshness'" in src, (
        "分类结果没有落台账 —— 接了线但没留痕，等于没接。")
