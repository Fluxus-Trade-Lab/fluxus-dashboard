#!/usr/bin/env python3
"""圈外主题人数：数「真的在讲这个主题的人」，不数顺带提到它的人。

三次律升闸（09-18·1 · 09-19·2 · 09-20·1）。同一个形状三次都是同一件事：
一条帖把某个主题当**枚举项**提了一下（二十只票的清单帖、视频里的话题名单），
人数榜把它算成一票，于是主题过了 ≥3 人的闸，上页变成「⭐ 起量」。

这里只剔两类机器判得出来的：
  A 清单帖  —— 单条挂 >= LIST_TICKERS 个代码，对每只票每个主题都没给自己的话
  B 回复帖  —— 蹭位榜早就不算回复，主题人数没理由算

⚠️ 原始人数与过滤后人数**一律并排打印**。只给过滤后的数，下一班就没法发现
尺子在瞎剔——「没有先验证一个检查能报出阳性，就不该信它的阴性」。

本工具**不读也不写** scoring/mood_daily.csv 与 theme_events.csv，不碰
mood_index.py 的 OUT_THEME 词表（跑手禁区）。它是速报用的独立一把尺子。

用法：
    python3 data/content/x_watch/tools/theme_count.py data/content/x_watch/posts/2026-09-20.jsonl
    python3 ... --min-people 3 --list-tickers 6
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

# 速报口径的宽词表。与 mood_index.py 的 OUT_THEME 是两本账，别去对齐两边的数。
THEMES: dict[str, str] = {
    "贵金属": r"\bgold\b|\bsilver\b|\bbullion\b|\$GLD\b|\$SLV\b|\$GDX\b",
    "加密": r"\bbitcoin\b|\bbtc\b|\bethereum\b|\bcrypto\b|\$BTC\b|\$ETH\b|\$IBIT\b|\$COIN\b",
    "能源": r"\bcrude\b|\bwti\b|\bnatural gas\b|\buranium\b|\$XLE\b|\$USO\b|\$UNG\b",
    "债": r"\byields?\b|\btreasur\w+|\b10[- ]?year\b|\$TLT\b|\$TNX\b",
    "外汇": r"\bdxy\b|\byen\b|\beuro\b|\$DXY\b|\$UUP\b",
}

LIST_TICKERS = 6   # 单条挂到这个数就算清单帖
MIN_PEOPLE = 3     # 圈外主题起量的人数闸


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def drop_reason(post: dict, list_tickers: int) -> str | None:
    """这条帖为什么不该算进主题人数。None = 算。"""
    if post.get("is_reply"):
        return "回复帖"
    if len(post.get("tickers") or []) >= list_tickers:
        return f"清单帖({len(post['tickers'])} 个代码)"
    return None


def count(
    posts: list[dict],
    themes: dict[str, str] | None = None,
    list_tickers: int = LIST_TICKERS,
) -> dict[str, dict]:
    """每个主题返回 raw / kept 两套人名，以及每个被剔的人的理由。"""
    themes = themes or THEMES
    out: dict[str, dict] = {}
    for name, pattern in themes.items():
        rx = re.compile(pattern, re.I)
        raw: set[str] = set()
        kept: set[str] = set()
        dropped: dict[str, str] = {}
        for post in posts:
            if not rx.search(post.get("text") or ""):
                continue
            handle = post["h"]
            raw.add(handle)
            reason = drop_reason(post, list_tickers)
            if reason is None:
                kept.add(handle)
            else:
                dropped.setdefault(handle, reason)
        # 一个人只要有一条命中帖是真讲这个主题的，就算他讲了
        dropped = {h: r for h, r in dropped.items() if h not in kept}
        out[name] = {"raw": sorted(raw), "kept": sorted(kept), "dropped": dropped}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("posts", help="posts/<ET 日>.jsonl")
    ap.add_argument("--min-people", type=int, default=MIN_PEOPLE)
    ap.add_argument("--list-tickers", type=int, default=LIST_TICKERS)
    args = ap.parse_args(argv)

    result = count(load(args.posts), list_tickers=args.list_tickers)
    print(f"{args.posts} · 人数闸 >= {args.min_people} · 清单帖 >= {args.list_tickers} 个代码")
    for name, box in result.items():
        raw, kept = len(box["raw"]), len(box["kept"])
        flag = " ⭐ 过闸" if kept >= args.min_people else ""
        turned = " ⚠️ 原始数过闸、过滤后没过" if raw >= args.min_people > kept else ""
        print(f"  {name}: 原始 {raw} 人 → 过滤后 {kept} 人{flag}{turned}")
        for handle, reason in box["dropped"].items():
            print(f"      剔 @{handle} · {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
