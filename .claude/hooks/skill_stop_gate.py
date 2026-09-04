#!/usr/bin/env python3
# .claude/hooks/skill_stop_gate.py
"""hook 乙：收工前查最后一条正文有没有留痕行。没有就打回。

查三种行之一（行首，允许缩进与列表符）：
    skill-used: <名> · <裁决/无>
    skill-skipped: <名> · <原因>
    skill-none: 本轮无适用 skill

不查用得对不对——那是裁决的事。只保证「用没用」被写下来：
这个项目栽过三次「闸对、测试对、没人调用」，缺的从来不是判断，是留痕。

放行规则（失败模式必须是放行）：stop_hook_active=true；字段缺失；任何异常。
官方 Stop 输入直接带 last_assistant_message，不用解析 transcript。
"""
from __future__ import annotations

import json
import re
import sys
from typing import Dict

MARK = re.compile(r"^\s*(?:[-*>]\s*)?`?skill-(used|skipped|none):", re.M)
REASON = ("收工前补一行（行首）：`skill-used: <名> · <裁决/无>`，"
          "或 `skill-skipped: <名> · <原因>`，或 `skill-none: 本轮无适用 skill`。")


def verdict(payload: Dict) -> Dict:
    try:
        if payload.get("stop_hook_active"):
            return {}
        text = payload.get("last_assistant_message")
        if not isinstance(text, str):
            return {}
        if MARK.search(text):
            return {}
        return {"decision": "block", "reason": REASON}
    except Exception:  # noqa: BLE001 -- 卡死会话比漏一行贵
        return {}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    print(json.dumps(verdict(payload), ensure_ascii=False))


if __name__ == "__main__":
    main()
