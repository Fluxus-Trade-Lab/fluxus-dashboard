#!/usr/bin/env python3
"""hook 丙：任务标完成前，跑它点名的测试；红了就不许标完成。

官方契约（hooks 参考页）：TaskCompleted 在 TaskUpdate 标 completed 时触发，
输入带 task_subject / task_description；阻止靠 **exit 2 + stderr**，
stderr 原文回给模型。官方示例就是「跑测试，不过 exit 2」——这里照抄，
只加一条：只跑任务文本里点名的测试文件。全套光收集就超两分钟，每次
标完成都全跑会把执行拖死。

它守的是「绿」，不是「先红后绿」。先写会红的测试那一步 hook 看不见——
只能看完成那一刻。别把它说成 TDD 闸。

失败模式：跑不起来（没 pytest、超时、一个都没收集到）＝放行并留话，不＝红。
⚠️ 「没 pytest」这条**探不到异常**：`python3 -m pytest` 在 pytest 缺失时返回
rc=1，和「2 个测试红了」在返回码上完全同形。云端无人值守容器里若没装 pytest，
任何在描述里点名了测试的任务将永远标不了完成、没人在旁边解锁——所以开跑前先
`find_spec` 探一次，探不到直接放行。返回码同理分档：rc=5（一个都没收集到）放行，
rc=4（点名的文件不存在）保持挡住（R14 的手动验收动作依赖它挡）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from importlib.util import find_spec  # 模块级导入，测试可 monkeypatch 掉
from typing import Callable, Dict, List, Tuple

_TEST = re.compile(r"pipeline/tests/test_[\w\-]+\.py")
TAIL = 15
TIMEOUT_S = 540
RC_FILE_MISSING = 4   # pytest: usage error / 点名的文件不存在 —— 仍然挡
RC_NO_TESTS = 5       # pytest: no tests collected —— 放行


def select_tests(text: str) -> List[str]:
    return sorted(set(_TEST.findall(text or "")))


def _run(tests: List[str]) -> Tuple[int, str]:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", *tests],
                       capture_output=True, text=True, timeout=TIMEOUT_S)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def verdict(payload: Dict, runner: Callable[[List[str]], Tuple[int, str]] = _run) -> Tuple[int, str]:
    text = f"{payload.get('task_subject', '')}\n{payload.get('task_description', '')}"
    tests = select_tests(text)
    if not tests:
        return 0, ""
    if find_spec("pytest") is None:
        return 0, "task_test_gate: 本机没有 pytest，没跑，请人工看一眼"
    try:
        code, out = runner(tests)
    except Exception as e:  # noqa: BLE001 -- 跑不起来不等于红
        return 0, f"task_test_gate: 测试没跑起来（{e}），放行但请人工看一眼"
    if code == 0:
        return 0, ""
    if code == RC_NO_TESTS:
        return 0, f"task_test_gate: 点名的测试一个都没收集到（rc=5），放行但请人工看一眼：{tests}"
    tail = "\n".join(out.splitlines()[-TAIL:])
    why = "点名的测试文件不存在（rc=4）" if code == RC_FILE_MISSING else "测试没过"
    return 2, f"{why}，不能标完成：{payload.get('task_subject', '')}\n{tail}"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    code, err = verdict(payload)
    if err:
        print(err, file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
