#!/usr/bin/env python3
# .claude/hooks/zh_stop_gate.py
"""hook 丙：最后一条回复几乎没有中文，就打回一次，让它用中文重写。

起因：回 Andy 漂成英文，09-19、09-21、10-01 三次同形（memory
pitfall_drifted_to_english_after_compaction：「再犯第 3 次就上 Stop hook 查中文占比」）。
10-01 他的原话：「中文沟通」。宪法：默认中文回复，代码 / token / 度量名照抄英文。

算法：去掉代码块、行内代码、链接、引用块（英文草稿通常放在 > 里）与 skill 留痕行，
数 汉字 / (汉字 + 拉丁字母)。两者合计 < MIN_LETTERS 的短回复不查。
低于 THRESHOLD 打回。校准（bc794578 会话 25 条真实回复）：中文回复 0.48–0.88，
漂成英文的两条 0.00——门槛 0.25 两边都留了余量。

放行规则同 hook 乙（失败模式必须是放行）：stop_hook_active=true（已打回过一次）；
字段缺失；任何异常。它只能拦住忘记，冻不死会话。
"""
from __future__ import annotations

import json
import re
import sys
from typing import Dict, Tuple

THRESHOLD = 0.25
MIN_LETTERS = 80
REASON = ("这条回复几乎全是英文。按宪法默认中文回复（Andy 2026-10-01：「中文沟通」）："
          "用中文重写整条回复，代码、命令、字段名、度量名照抄英文。")

_STRIP = [
    (re.compile(r"```.*?```", re.S), ""),
    (re.compile(r"`[^`\n]*`"), ""),
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"https?://\S+"), ""),
    (re.compile(r"^\s*>.*$", re.M), ""),
    (re.compile(r"^\s*(?:[-*]\s*)?skill-(?:used|skipped|none):.*$", re.M), ""),
]
_CJK = re.compile(r"[㐀-䶿一-鿿]")
_LATIN = re.compile(r"[A-Za-z]")


def zh_share(text: str) -> Tuple[int, int, float]:
    for pat, rep in _STRIP:
        text = pat.sub(rep, text)
    cjk = len(_CJK.findall(text))
    lat = len(_LATIN.findall(text))
    total = cjk + lat
    return cjk, lat, (cjk / total if total else 1.0)


def verdict(payload: Dict) -> Dict:
    try:
        if payload.get("stop_hook_active"):
            return {}
        text = payload.get("last_assistant_message")
        if not isinstance(text, str):
            return {}
        cjk, lat, share = zh_share(text)
        if cjk + lat < MIN_LETTERS or share >= THRESHOLD:
            return {}
        return {"decision": "block", "reason": REASON}
    except Exception:  # noqa: BLE001 -- 卡死会话比漏一次英文贵
        return {}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    print(json.dumps(verdict(payload), ensure_ascii=False))


if __name__ == "__main__":
    main()
