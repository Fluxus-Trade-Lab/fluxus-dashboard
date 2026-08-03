#!/usr/bin/env python3
"""今天该不该出海报 —— 日历触发器。

    python3 scripts/poster_today.py

读 data/output/breadth.json + signals.json,按下面的阈值判断今天有没有「外部理由」发图。
有触发 → 打出情绪 → 候选视觉代码 → 现成的测量行 → 可直接跑的 make_poster 命令。
没触发 → 明说没有。**没有理由就不发**,这是这套日历的全部意义。

阈值是可编辑的默认值,不是回测出来的。它给数字和依据,发不发你定。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "Fluxus_Visual_Library.md"
BREADTH = ROOT / "data/output/breadth.json"

# 触发 → (情绪关键词,理由模板)。情绪关键词用来在视觉库索引表里查代码。
TRIGGERS = [
    ("超卖极值", lambda d: d["t2108"] < 20 or d["pct_above_20sma"] < 15,
     "黑天鹅", "T2108 {t2108} · >20SMA {pct_above_20sma}% —— 卖方在清仓"),
    ("超买极值", lambda d: d["t2108"] > 80 or d["pct_above_20sma"] > 85,
     "系统失控", "T2108 {t2108} · >20SMA {pct_above_20sma}% —— 所有人都在场内"),
    ("动能翻转", lambda d: d["ratio_5d"] > 2.0,
     "机会来了", "5日比 {ratio_5d} —— 买方接管"),
    ("动能塌陷", lambda d: d["ratio_5d"] < 0.4,
     "混乱中保持冷静", "5日比 {ratio_5d} —— 卖压主导"),
    ("趋势破位", lambda d: d["pct_above_200sma"] < 40,
     "等待", "只有 {pct_above_200sma}% 还在 200 日线上"),
    ("趋势修复", lambda d: d["pct_above_200sma"] > 70,
     "完全掌控", "{pct_above_200sma}% 在 200 日线上"),
]


def load_index(path: Path = LIBRARY) -> dict[str, list[str]]:
    """从视觉库底部的快速索引表里读 情绪 → 代码。"""
    index: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*((?:V\d+\s*)+)\|", line)
        if m:
            index[m.group(1).strip()] = re.findall(r"V\d+", m.group(2))
    return index


def codes_for(index: dict[str, list[str]], keyword: str) -> list[tuple[str, list[str]]]:
    return [(k, v) for k, v in index.items() if keyword in k]


def load_metrics() -> dict:
    if not BREADTH.exists():
        raise SystemExit(f"没有 {BREADTH.relative_to(ROOT)} —— 先跑一次 pipeline")
    raw = json.loads(BREADTH.read_text())
    d = {**raw.get("breadth", {}), **raw.get("mm", {})}
    d["spx_close"] = raw.get("spx_close")
    d["timestamp"] = raw.get("timestamp", "")
    return d


def meta_line(d: dict) -> str:
    bits = []
    if d.get("spx_close"):
        bits.append(f"SPX {d['spx_close']:.0f}")
    bits.append(f"T2108 {d['t2108']:.0f}")
    bits.append(f">20SMA {d['pct_above_20sma']:.0f}%")
    return " · ".join(bits)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="连没触发的规则也列出来")
    args = ap.parse_args()

    d = load_metrics()
    index = load_index()
    today = date.today()  # localtime-ok: poster label, not a trading date
    meta = meta_line(d)

    print(f"日期 {today:%Y-%m-%d}  ·  数据 {d['timestamp'][:10]}")
    print(f"测量行  {meta}\n")

    fired = []
    for name, test, keyword, why in TRIGGERS:
        try:
            hit = test(d)
        except KeyError as e:
            print(f"  {name}: 缺字段 {e},跳过")
            continue
        if hit:
            fired.append((name, keyword, why.format(**d)))
        elif args.all:
            print(f"  ─ {name}  未触发")

    if today.weekday() == 6:
        fired.append(("周日的信", "", "封面位,每周保底一张"))

    if not fired:
        print("今天没有触发。**不发。**")
        print("(周日的信是唯一的保底位;其余全部要行情给理由。)")
        return

    for name, keyword, why in fired:
        print(f"▸ {name} —— {why}")
        for emotion, codes in codes_for(index, keyword) if keyword else []:
            print(f"    {emotion}: {' '.join(codes)}")
        print()

    first = next((k for _, k, _ in fired if k), None)
    hits = codes_for(index, first) if first else []
    code = hits[0][1][0] if hits else "V01"
    print("现成命令(自己换 --en / --zh):\n")
    print(f'python3 scripts/make_poster.py --code {code} \\\n'
          f'    --en "..." --zh "..." \\\n'
          f'    --meta "{meta}"')


if __name__ == "__main__":
    main()
