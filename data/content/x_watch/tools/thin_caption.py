#!/usr/bin/env python3
"""蹭位榜「前 8 名里挂得上的前 5」：剔掉纯图配短标题的空帖，不让它们占掉真信号的位置。

取件账 09-18·3（三次律，09-22·四格 / 09-23 速报·一格 / 09-23 主班·两格，第 4 次
撞上后 09-24 升机制）。三班都在前 5 里撞到「一张图、正文不比图里的标题多说
一句话」的帖子：09-22 是订阅导流广告，09-23 是 ConnorJBates 的 NYSE 新低标题图
（"NYSE New 52-Week Lows..."）。这类帖挤占了本该轮到的下一名。

⚠️ 自造口径（`data/reference/METRIC_SOURCES.md` 里没有「一条社媒帖算不算空帖」
这种标准，查过、无标准）：**去掉链接后剩下的正文里有没有任何数字**。选它是因为
这是唯一把两类帖机器可判地分开的信号——
  - 该剔的（"NYSE New 52-Week Lows..."）：去链接后没有具体点位/百分比，
    "52-Week" 只是术语里的数字，正则按"任意数字"算的话这条会漏判，所以判据
    看的是**有没有独立于标题之外的新数字**，而 52-Week 就是标题本身的一部分——
    这条边界案例本工具目前**判不准**（见下面「已知局限」），故不拿它做测试基线。
  - 不该剔的（Linda "Bonds: 106'27 key swing low."）：106'27 是一个具体点位，
    去掉链接后依然读得出来——这是本工具唯一保证接得住的正例，写进了测试。

**已知局限**：这把尺子只挡得住"正文里连一个数字都没有"的纯图/纯标题帖（比如
只有 "$MCD chart" 这种）。"正文有词但全是复述图里的标题，没有数字"这一类
（如上面 NYSE 的例子）挡不住——判它需要理解语义，不是这条尺子的活。跑手遇到
这类漏判，照旧在日报「给 Steve」里手记，不要因为这条闸没报红就以为帖子没问题。

用法：
    python3 data/content/x_watch/tools/thin_caption.py data/content/x_watch/posts/2026-09-23.jsonl
    # 只在候选按密度降序排好之后跑，不重新排序，只在前 pool 名里剔、取前 pick 名
"""
from __future__ import annotations

import argparse
import json
import re
import sys

_URL_RE = re.compile(r"https?://\S+")
_DIGIT_RE = re.compile(r"\d")

POOL = 8   # 只在密度前几名里找
PICK = 5   # 最终要凑够几个


def strip_urls(text: str) -> str:
    return _URL_RE.sub("", text or "").strip()


def is_thin_caption(text: str) -> bool:
    """去掉链接后的正文里一个数字都没有 = 图片自己说话，正文没有独立信息。
    自造口径，见模块 docstring；已知局限也在那里。"""
    return not _DIGIT_RE.search(strip_urls(text))


def top5_from_pool(
    rows: list[dict],
    text_key: str = "text",
    pool: int = POOL,
    pick: int = PICK,
) -> list[dict]:
    """rows 必须已按密度降序排好。从前 `pool` 名里剔掉空帖，取剩下的前 `pick` 个。

    不去动排序本身，也不去补第 pool+1 名——挂得上的不够 `pick` 个，就照实只
    返回剩下的那几个（跟人数榜「闸空了就报空」是同一条纪律）。
    """
    candidates = rows[:pool]
    kept = [r for r in candidates if not is_thin_caption(r.get(text_key, ""))]
    return kept[:pick]


def annotate(rows: list[dict], text_key: str = "text", pool: int = POOL) -> list[dict]:
    """给前 `pool` 名逐条标注 thin/kept，供并排打印——不给阳性也不给阴性单独的话语权。"""
    out = []
    for i, row in enumerate(rows[:pool]):
        thin = is_thin_caption(row.get(text_key, ""))
        out.append({**row, "rank_in_pool": i + 1, "thin_caption": thin})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("posts", help="posts/<ET 日>.jsonl，已按密度降序排好的候选清单同格式")
    ap.add_argument("--pool", type=int, default=POOL)
    ap.add_argument("--pick", type=int, default=PICK)
    args = ap.parse_args(argv)

    with open(args.posts, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

    marked = annotate(rows, pool=args.pool)
    kept = [r for r in marked if not r["thin_caption"]][: args.pick]
    print(f"{args.posts} · 前 {args.pool} 名里剔空帖 · 目标 {args.pick} 个")
    for r in marked:
        flag = "⛔ 空帖剔除" if r["thin_caption"] else "✅ 留"
        preview = strip_urls(r.get("text", ""))[:40]
        print(f"  #{r['rank_in_pool']} @{r.get('h', '?')} {flag} · {preview}")
    print(f"最终留下 {len(kept)} 个（目标 {args.pick}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
