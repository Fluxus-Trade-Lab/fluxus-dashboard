"""这道闸有没有真的接在写盘路径上 —— 不是它自己对不对。

**为什么单开一个文件（2026-09-03，Nighty Zac）**

`test_no_downgrade.py` 有 269 行、全绿，它测的是 `pipeline/no_downgrade.py` 这个模块。
2026-08-31 14:03 的 `8e4a64ef`（commit message 写着「手工化解」冲突）把 `run_all.py` 里
调用它的那 27 行**整段删掉了**，同日早些时候 `4f2fe309` 才刚把它接上
（那次 commit 同时改了 3 个文件：模块 + 测试 + `run_all.py` 的接线）。

**269 行测试一条都没红**，因为它们从头到尾没有问过一句「有人调用它吗」。
从 08-31 到 09-03，Andy 08-31 亲裁的那道闸（原话方向：「比数据、不覆盖」，
事故档 `data/reference/incidents/2026-08-29_late_run_overwrote_healthy_data.md`）
**在生产里一次都没执行过**，而它防的正是「迟到的班拿更差的数据覆盖好数据」。

⚠️ **这是结构断言，不是行为断言**（`pitfall_read_the_source_took_it_for_the_behavior`）：
它证明的是「调用点写在源码里」，不是「它在夜里真的跑了」。
真行为断言要一次端到端跑，那是 `test_run_all_smoke` 的活。
**结构断言在这里够用，因为消失的正是源码里那一行。**

阳性对照：把这三条挂在 `8e4a64ef` 之后、`4f2fe309` 恢复之前的 `run_all.py` 上，
**三条全红**（09-03 实测，见当日晨报）。
"""
from __future__ import annotations

import ast
from pathlib import Path

RUN_ALL = Path(__file__).resolve().parents[1] / "screeners" / "run_all.py"


def _tree():
    return ast.parse(RUN_ALL.read_text(encoding="utf-8"))


def test_run_all_imports_the_gate():
    names = {
        alias.name
        for node in ast.walk(_tree())
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("no_downgrade")
        for alias in node.names
    }
    assert "check_overwrite" in names, (
        "run_all.py 不再 import no_downgrade.check_overwrite —— "
        "08-31 的 8e4a64ef 就是这样把这道闸从生产路径上摘掉的。")


def test_the_gate_is_actually_called():
    called = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "check_overwrite"
        for n in ast.walk(_tree())
    )
    assert called, "import 了但没调用 —— 那和没接一样。"


def test_writing_universe_json_sits_behind_the_gate():
    """写 universe.json 的那句，必须在一个由闸的结果决定的分支里。

    只断言 import + call 不够：把调用留下、把写盘挪到分支外面，闸就又只是装饰了。
    """
    tree = _tree()
    writes_outside_branch = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "write_text"):
            continue
        src = ast.get_source_segment(RUN_ALL.read_text(encoding="utf-8"), node) or ""
        if "universe.json" not in src:
            continue
        # 找它的祖先里有没有 If
        in_if = False
        for parent in ast.walk(tree):
            if isinstance(parent, ast.If) and any(n is node for n in ast.walk(parent)):
                in_if = True
                break
        if not in_if:
            writes_outside_branch.append(src[:60])
    assert not writes_outside_branch, (
        f"universe.json 的写盘不在任何分支里，闸拦不住它：{writes_outside_branch}")
