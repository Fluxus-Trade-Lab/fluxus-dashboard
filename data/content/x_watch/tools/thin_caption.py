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

判据 09-27 已改（T-0927-63，反方向第 4 次三次律到期）：单看「有没有数字」在
反方向系统性误剔——**判断句里天然没有数字**（盘评、季节性、方法对照）。现在是
**无数字 且 去链接后短于 `MIN_SUBSTANTIVE_LEN` 字**才算空帖。阈值 60 是从取件账
09-24d·2 → 09-26d·2 那一串反方向误剔案例现场量出来的：Jake `$SMCI`「Could be
interesting here if this breaks out」90 字、Linda 的期货图评（Copper/SPs 各
80/107 字）、ConnorJBates 季节性 82 字、Muninn 的 Zanger/Qullamaggie 对照 149 字、
wey_how12640 的 `$DELL` 波段低点 107 字——全部 ≥80 字；本工具测试基线里的真空帖
（"MCD chart update" 一类）全部 ≤43 字。两簇之间有 37 字的空档，60 落在正中间。

**已知局限（两个方向都在自造口径里，缺一个方向就是没查清楚偏离在哪）**：
1. **漏判方向**（原有）——这把尺子只挡得住"正文里连一个数字都没有、且短"的
   纯图/纯标题帖。"正文有词但全是复述图里的标题，没有数字，但写得比较长"这一类
   （如上面 NYSE 的例子，去链接后长度够不上被长度闸放过）挡不住——判它需要
   理解语义，不是这条尺子的活。
2. **误剔方向**（09-27 补，此前一次都没记）——长度阈值是从 6 个反方向案例的
   分布里画的一条线，不是语义边界；一条恰好写得很短（<60 字）的真判断句仍会
   被误判成空帖，只是目前的样本里还没见到这种案例。
跑手遇到这两类漏判/误剔，照旧在日报「给 Steve」里手记，不要因为闸没报红/报红
就以为帖子没问题/有问题。**这把尺子报的阳性（⛔ 空帖剔除）可以信，报的阴性
（✅ 留）不能信**——跑手自己得出的判词（取件账 09-26d·2）。

**per-handle 上限（09-24n·a → 09-25n·2，三次律到期）**：空帖闸剔完之后，
同一 handle 在前 `pool` 名里最多留 `PER_HANDLE_CAP` 条——同一个人连发的帖
会把蹭位榜前排占满，挤掉别的账号。第三条起算「挤出」，顺延给池里下一名顶上。
这跟空帖剔除是两件事，不共用一个标记——`annotate()` 并排输出里分开标。

用法：
    python3 data/content/x_watch/tools/thin_caption.py data/content/x_watch/posts/2026-09-23.jsonl
    # 只在候选按密度降序排好之后跑，不重新排序，只在前 pool 名里剔、取前 pick 名
    # 排位前必看 annotate() 的并排输出，不是可选步骤——见两班任务书「蹭位榜与回复方向」节
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
MIN_SUBSTANTIVE_LEN = 60   # 去链接后短于这个字数、且无数字，才算空帖（见模块 docstring 判据说明）
PER_HANDLE_CAP = 2   # 同一 handle 在前 pool 名里最多留几条，第三条起挤出（09-25n·2 口径）


def strip_urls(text: str) -> str:
    return _URL_RE.sub("", text or "").strip()


def is_thin_caption(text: str) -> bool:
    """空帖 = 去掉链接后无数字 且 短于 MIN_SUBSTANTIVE_LEN 字。
    自造口径，见模块 docstring；两个方向的已知局限也在那里。"""
    stripped = strip_urls(text)
    if _DIGIT_RE.search(stripped):
        return False
    return len(stripped) < MIN_SUBSTANTIVE_LEN


def top5_from_pool(
    rows: list[dict],
    text_key: str = "text",
    handle_key: str = "h",
    pool: int = POOL,
    pick: int = PICK,
    per_handle_cap: int = PER_HANDLE_CAP,
) -> list[dict]:
    """rows 必须已按密度降序排好。从前 `pool` 名里剔掉空帖、同 handle 超过
    `per_handle_cap` 条的挤出，取剩下的前 `pick` 个。

    不去动排序本身，也不去补第 pool+1 名——挂得上的不够 `pick` 个，就照实只
    返回剩下的那几个（跟人数榜「闸空了就报空」是同一条纪律）。
    """
    candidates = rows[:pool]
    kept: list[dict] = []
    handle_counts: dict = {}
    for r in candidates:
        if len(kept) >= pick:
            break
        if is_thin_caption(r.get(text_key, "")):
            continue
        h = r.get(handle_key)
        if handle_counts.get(h, 0) >= per_handle_cap:
            continue
        kept.append(r)
        handle_counts[h] = handle_counts.get(h, 0) + 1
    return kept


def annotate(
    rows: list[dict],
    text_key: str = "text",
    handle_key: str = "h",
    pool: int = POOL,
    pick: int = PICK,
    per_handle_cap: int = PER_HANDLE_CAP,
) -> list[dict]:
    """给前 `pool` 名逐条标注 thin_caption/handle_capped，供并排打印——
    两个标记不共用：空帖剔除管的是帖子本身没信息，handle_capped 管的是同一
    个人占太多格，挤出去的那条不该被读成「这帖子本身是空帖」。"""
    out = []
    handle_counts: dict = {}
    kept_count = 0
    for i, row in enumerate(rows[:pool]):
        thin = is_thin_caption(row.get(text_key, ""))
        capped = False
        if not thin:
            h = row.get(handle_key)
            if handle_counts.get(h, 0) >= per_handle_cap:
                capped = True
            elif kept_count < pick:
                handle_counts[h] = handle_counts.get(h, 0) + 1
                kept_count += 1
        out.append({**row, "rank_in_pool": i + 1, "thin_caption": thin, "handle_capped": capped})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("posts", help="posts/<ET 日>.jsonl，已按密度降序排好的候选清单同格式")
    ap.add_argument("--pool", type=int, default=POOL)
    ap.add_argument("--pick", type=int, default=PICK)
    args = ap.parse_args(argv)

    with open(args.posts, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

    marked = annotate(rows, pool=args.pool, pick=args.pick)
    kept = [r for r in marked if not r["thin_caption"] and not r["handle_capped"]][: args.pick]
    print(f"{args.posts} · 前 {args.pool} 名里剔空帖 + per-handle 上限 · 目标 {args.pick} 个")
    for r in marked:
        if r["thin_caption"]:
            flag = "⛔ 空帖剔除"
        elif r["handle_capped"]:
            flag = "🚫 挤出（同 handle 已超上限）"
        else:
            flag = "✅ 留"
        preview = strip_urls(r.get("text", ""))[:40]
        print(f"  #{r['rank_in_pool']} @{r.get('h', '?')} {flag} · {preview}")
    print(f"最终留下 {len(kept)} 个（目标 {args.pick}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
