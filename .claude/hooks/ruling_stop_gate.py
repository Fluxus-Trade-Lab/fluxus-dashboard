#!/usr/bin/env python3
# .claude/hooks/ruling_stop_gate.py
"""hook 丙：Andy 说像裁决的话，本轮没记进耐久处就拦一次（spec §6.3）。

「裁决」＝ Andy 在窗口里说「以后这样做/不要再这样/定了」这类话——这类话不落盘，
下一个会话读不到，等于没定过（08-24 平行造稿、08-31 越权改宪法都源自这个形状的变体）。
本 hook 只查**留没留痕**，不查记得对不对——那是 andy/review 的事。

判定：
1. 从 transcript 尾部倒着找**最后一条真正由 Andy 亲手输入的话**（见 `_last_user_message`：
   新条目认 `origin.kind == "human"`；没有 origin 字段的旧条目，跳过 isMeta/isCompactSummary、
   跳过以 `<`/`Stop hook feedback`/`Another Claude` 开头的注入内容、跳过纯 tool_result 消息，
   content 是 list 时把里面的 text 块拼起来再判断——这样带图的裁决不会因为 content 是 list
   被整条跳过）。
2. 命中裁决**正则**（带上下文，09-22 复核三轮收紧：第 1 轮把单字词表换成带上下文正则，
   第 2 轮再排除「你记住了吗」「这个定了多少钱？」「别再下雨」「他们都这样说」
   「以后就知道了」这类句式，第 3 轮再排除问句结尾、「他/她/他们/它以后」、
   「就定了个大概」这类、并去掉 `> ` 引用行再判）才继续查，否则直接放行。
3. 放行条件：本轮回复（last_assistant_message）末尾有 `ruling-recorded: <...>` 或
   `ruling-none: <理由>`。
   09-22 复核第 3 轮删掉了「fluxus-ops 30 分钟内有 remember/andy 提交就放行」这条——
   它看的是整个仓库，任何一条线记一次，所有会话接下来 30 分钟都会被放行（真事故：
   Growth Gary 记账顺带放行了 Andy 窗口里的真裁决），而且让测试依赖真实仓库路径。
4. 都没有 → 拦一次。

放行是默认失败模式：stop_hook_active、字段缺失、transcript 读不到、任何异常——
一律放行。这个 hook 拦的是所有交互会话（含 Andy 自己在用的那个），卡死它比漏拦一次贵得多。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterator, Optional

REVERSE_READ_CHUNK = 1 << 20  # 1 MiB；真实 transcript 可到几百 MB，不整份读进内存

# 09-22 复核三轮收紧：
#   第 1 轮：单字词表 → 带上下文正则。
#   第 2 轮：「记住」只认句首 `记住[:：，]`；「定了」排除紧跟问句；「别再」只认后面紧跟
#            具体动词；「都这样」要求带出具体动作；「以后就」排除「以后就知道/明白/懂」。
#   第 3 轮：「不要再」和「别再」一样只认具体动词；「以后/今后」前面是「他/她/他们/它」时
#            不判；「就定了」排除后面紧跟「个/了个/大概」；判断前先去掉 `> ` 引用行、
#            整句以问号（？/?）结尾时不判。
RULING_PATTERNS = tuple(re.compile(p) for p in (
    r"(?<!他)(?<!她)(?<!它)(?<!他们)(以后|今后)(都|一律|每次|统一|别|不要|不许|就(?!(知道|明白|懂)))",
    r"都这样(做|办|写|画|弄|来)",
    r"写进(去|规矩|宪法|skill|记忆)",
    r"^记住[:：，]",
    r"(这个|就)定了(?!.{0,6}[？?])(?!(个|了个|大概))",
    r"(不要再|别再)(给|用|发|做|让|写|加)",
    r"(^|[，。\s])批(了|[，。！]|$)|都批|我批",
    r"不做了|这个不做(?!空|多)",
))

QUOTE_LINE = re.compile(r"^>\s")

# 没有 origin 字段的旧条目，靠内容前缀排除注入消息（Stop hook 反馈、跨会话消息、
# <system-reminder>/<cross-session-message> 等 XML 包裹的合成内容）。
INJECTED_PREFIXES = ("<", "Stop hook feedback", "Another Claude")

# Andy 真消息（origin.kind=="human"）可能带附件/引用标记，不算内容本身，判裁决词之前
# 先剥掉；这类消息**不**套用 INJECTED_PREFIXES（那条是给「不确定是不是人」的旧条目用的，
# 09-22 复核第 2 轮点名：human 来源的消息不该因为前缀像 `<` 就被整条跳过）。
ATTACH_MARKER = re.compile(r"^(?:\s*<!--\s*(?:attach|reply)\s*-->\s*)+")

RECORD_MARK = re.compile(r"^\s*(?:[-*>]\s*)?`?ruling-(recorded|none):", re.M)

REASON = (
    "Andy 这句像裁决：用 `taskboard.py remember`（或对应任务）记下，"
    "并在收尾正文末行写 `ruling-recorded: <任务号或 remember>`；"
    "不算裁决就写 `ruling-none: <理由>`；"
    "判断这句不是裁决，末行写 `ruling-none: 不是裁决` 即可放行——误拦的代价只是多写一行。"
)


def _iter_lines_reverse(path: Path, chunk_size: int = REVERSE_READ_CHUNK) -> Iterator[str]:
    """从文件尾部往前逐行 yield（不含结尾换行符），不整份读进内存。

    真实 transcript 可以到几百 MB；这条 hook 只需要「最后一条符合条件的消息」，
    绝大多数时候离文件尾很近，倒着读能早退出，不用整份 decode 一遍。
    """
    with path.open("rb") as fh:
        fh.seek(0, 2)
        remaining = fh.tell()
        tail = b""
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            remaining -= read_size
            fh.seek(remaining)
            chunk = fh.read(read_size)
            tail = chunk + tail
            parts = tail.split(b"\n")
            tail = parts[0]  # 可能是被这次切断的半行，留给上一轮（更靠前的内容）拼接
            for line in reversed(parts[1:]):
                if line:
                    yield line.decode("utf-8", errors="replace")
        if tail:
            yield tail.decode("utf-8", errors="replace")


def _extract_human_text(entry: Dict, origin_is_human: bool) -> Optional[str]:
    """从一条 user 条目里取「人打的文字」，content 是 list（带图/带 tool_result）也处理。

    含 tool_result 块的 list → 不是人打的，返回 None（跳过，继续往前找）。
    含 text 块的 list（比如带图裁决）→ 把 text 块拼起来。

    `origin_is_human`（即 `origin.kind == "human"`）时：先剥掉开头的附件/引用标记
    （`<!-- attach -->` / `<!-- reply -->`），剩下的原样当正文用，**不**做 INJECTED_PREFIXES
    排除——那条前缀过滤是给「不确定是不是人」的旧条目防注入用的，会误伤真消息。
    """
    message = entry.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        texts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
        text = "\n".join(t for t in texts if t)
    else:
        return None
    text = text.strip()
    if not text:
        return None

    if origin_is_human:
        text = ATTACH_MARKER.sub("", text).strip()
        return text or None

    if text.startswith(INJECTED_PREFIXES):
        return None
    return text


def _last_user_message(transcript_path: Optional[str]) -> Optional[str]:
    """从 transcript 倒着找最后一条真正由 Andy 亲手输入的话。

    - 有 `origin` 字段（新条目）：只认 `origin.kind == "human"`；peer/hook/其它一律跳过
      （task-notification、Stop hook feedback、跨会话消息都走这条被过滤掉）。
    - 没有 `origin` 字段（旧条目）：跳过 isMeta、isCompactSummary，跳过 `_extract_human_text`
      判定为注入/空/纯 tool_result 的内容。
    - isSidechain 一律跳过（子 agent 岔出去的分支，不是 Andy 本人在主线说的话）。
    读不到 / 坏 JSON / 任何异常 → None（放行）。
    """
    if not transcript_path:
        return None
    p = Path(transcript_path)
    if not p.is_file():
        return None
    try:
        for raw in _iter_lines_reverse(p):
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            if entry.get("type") != "user":
                continue
            if entry.get("isSidechain"):
                continue

            origin = entry.get("origin")
            origin_is_human = False
            if origin is not None:
                if not isinstance(origin, dict) or origin.get("kind") != "human":
                    continue
                origin_is_human = True
            else:
                if entry.get("isMeta") or entry.get("isCompactSummary"):
                    continue

            text = _extract_human_text(entry, origin_is_human)
            if text is None:
                continue
            return text
    except Exception:  # noqa: BLE001
        return None
    return None


def _strip_quote_lines(text: str) -> str:
    """去掉以 `> ` 开头的引用行——被引用/转述的话不算 Andy 现在自己说的。"""
    return "\n".join(line for line in text.splitlines() if not QUOTE_LINE.match(line))


def _hits_ruling_word(text: str) -> bool:
    text = _strip_quote_lines(text).strip()
    if not text:
        return False
    if text.endswith(("？", "?")):
        return False
    return any(p.search(text) for p in RULING_PATTERNS)


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
