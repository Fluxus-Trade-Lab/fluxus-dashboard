#!/usr/bin/env python3
# .claude/hooks/ruling_stop_gate.py
"""hook 丙：Andy 说像裁决的话，本轮没记进耐久处就拦一次（spec §6.3）。

「裁决」＝ Andy 在窗口里说「以后这样做/不要再这样/定了」这类话——这类话不落盘，
下一个会话读不到，等于没定过（08-24 平行造稿、08-31 越权改宪法都源自这个形状的变体）。
本 hook 只查**留没留痕**，不查记得对不对——那是 andy/review 的事。

判定：
1. 取本轮最后一条 Andy 的话（transcript 里最后一条 role=user 且内容是纯字符串的消息，
   跳过 tool_result 注入的 user 消息）。
2. 命中裁决词（保守词表，宁可漏判不可乱判）才继续查，否则直接放行。
3. 放行条件（任一即可）：
   - 本轮回复（last_assistant_message）末尾有 `ruling-recorded: <...>` 或 `ruling-none: <理由>`；
   - fluxus-ops origin/main 最近 30 分钟内有落盘裁决的提交（`memory: remember` / `andy ruled`）。
4. 都没有 → 拦一次。

放行是默认失败模式：stop_hook_active、字段缺失、transcript 读不到、git 读不到、
读 git 超时（5 秒）、任何异常——一律放行。这个 hook 拦的是所有交互会话（含 Andy
自己在用的那个），卡死它比漏拦一次贵得多。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional

GIT_TIMEOUT_SEC = 5
SINCE_MINUTES = 30
FLUXUS_OPS = Path.home() / "Documents" / "fluxus-ops"

# 保守词表：命中才继续查，宁可漏拦。
RULING_WORDS = (
    "以后", "今后", "都这样", "写进去", "记住", "定了", "不要再", "批", "不做",
)

RECORD_MARK = re.compile(r"^\s*(?:[-*>]\s*)?`?ruling-(recorded|none):", re.M)

REASON = (
    "Andy 这句像裁决：用 `taskboard.py remember`（或对应任务）记下，"
    "并在收尾正文末行写 `ruling-recorded: <任务号或 remember>`；"
    "不算裁决就写 `ruling-none: <理由>`。"
)


def _last_user_message(transcript_path: Optional[str]) -> Optional[str]:
    """从 transcript JSONL 里取本轮最后一条 Andy 亲手打的话。

    跳过 tool_result 注入的 user 条目（那些 message.content 是 list，
    不是 str）；跳过空行/坏 JSON。读不到就返回 None（放行）。
    """
    if not transcript_path:
        return None
    p = Path(transcript_path)
    if not p.is_file():
        return None
    last_text: Optional[str] = None
    try:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "user":
                    continue
                if entry.get("isSidechain"):
                    continue
                message = entry.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    last_text = content
    except Exception:  # noqa: BLE001
        return None
    return last_text


def _hits_ruling_word(text: str) -> bool:
    return any(word in text for word in RULING_WORDS)


def _recent_ruling_commit() -> bool:
    """fluxus-ops origin/main 过去 30 分钟内有没有落盘裁决的提交。

    读不到仓库/网络、超时、任何异常 → False（不代表拦，只是这一条放行理由不成立，
    还有 ruling-recorded/ruling-none 那条路）。
    """
    if not FLUXUS_OPS.is_dir():
        return False
    try:
        result = subprocess.run(
            [
                "git", "-C", str(FLUXUS_OPS), "log",
                "origin/main", f"--since={SINCE_MINUTES}.minutes",
                "--pretty=%s",
            ],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SEC,
        )
    except Exception:  # noqa: BLE001 -- 超时/找不到 git 都算读不到
        return False
    if result.returncode != 0:
        return False
    for subject in result.stdout.splitlines():
        if "memory: remember" in subject or "andy ruled" in subject:
            return True
    return False


def verdict(payload: Dict) -> Dict:
    try:
        if payload.get("stop_hook_active"):
            return {}

        user_text = payload.get("last_user_message")
        if not isinstance(user_text, str):
            user_text = _last_user_message(payload.get("transcript_path"))
        if not isinstance(user_text, str) or not _hits_ruling_word(user_text):
            return {}

        assistant_text = payload.get("last_assistant_message")
        if isinstance(assistant_text, str) and RECORD_MARK.search(assistant_text):
            return {}

        if _recent_ruling_commit():
            return {}

        return {"decision": "block", "reason": REASON}
    except Exception:  # noqa: BLE001 -- 卡死交互会话比漏拦一次贵
        return {}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    print(json.dumps(verdict(payload), ensure_ascii=False))


if __name__ == "__main__":
    main()
