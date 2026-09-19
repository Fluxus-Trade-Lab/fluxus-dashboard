#!/usr/bin/env python3
"""蹭位榜 / 高收藏表选票：给一批 post id，从 posts/*.jsonl 查出 url/dt，直接出可贴日报的行。

取件账 09-16·1（README「给 Steve」表）：蹭位榜/高收藏表初稿手打 status id 和距今
小时数，09-16、09-17 两次都手打错过；算上更早的 09-10（工具截断靠 pbpaste 手工兜
底）、09-11（占位符 id 事故），同形状坑第 3、4 次，三次律触发——不再让人抄 id，
脚本直接从 posts/*.jsonl 取 url/dt 拼链接、算距今小时数（ET 口径）。

用法：
    python3 data/content/x_watch/tools/pick_links.py 2101036404528542104 2100999092289818833
    # 蹭位榜按原定跑点(而不是实跑时刻)算距今时(取件账 09-15·1)：
    python3 data/content/x_watch/tools/pick_links.py --as-of 2026-09-19T00:30:00-04:00 <ids...>

找不到的 id（打错了）原样报「未找到」并让退出码非 0——09-16/09-17 的错就是打错
了 id 却没人发现，找不到必须响，不能静默漏掉。
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")


def load_posts_by_id(posts_dir: Path | None = None) -> dict[str, dict]:
    """扫 posts/*.jsonl，按 id 建索引。同一 id 只会出现在一个按 et_date 分的文件里。"""
    posts_dir = posts_dir or (BASE / "posts")
    out: dict[str, dict] = {}
    for f in sorted(posts_dir.glob("*.jsonl")):
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            pid = row.get("id")
            if pid:
                out[pid] = row
    return out


def hours_ago(dt: datetime, as_of: datetime) -> float:
    return round((as_of - dt).total_seconds() / 3600, 1)


def pick(ids: list[str], posts_by_id: dict[str, dict], as_of: datetime) -> list[dict]:
    """按输入顺序查表，找不到的 id 原样标 found=False，不跳过、不猜。"""
    rows = []
    for pid in ids:
        row = posts_by_id.get(pid)
        if row is None:
            rows.append({"id": pid, "found": False})
            continue
        dt = datetime.fromisoformat(row["dt"])
        url = row.get("url") or f"https://x.com/{row.get('h', '')}/status/{pid}"
        rows.append({
            "id": pid,
            "found": True,
            "handle": row.get("h", ""),
            "dt_et": dt.astimezone(ET).strftime("%m-%d %H:%M"),
            "hours_ago": hours_ago(dt, as_of),
            "views": row.get("views", 0),
            "likes": row.get("likes", 0),
            "bookmarks": row.get("bookmarks", 0),
            "replies": row.get("replies", 0),
            "url": url,
            "text": (row.get("text") or "").replace("\n", " ").strip()[:80],
        })
    return rows


def format_line(r: dict) -> str:
    if not r["found"]:
        return f"{r['id']}\t未找到（检查 id 是否打错）"
    return (f"@{r['handle']}\t{r['hours_ago']}h\t曝光{r['views']}/回复{r['replies']}"
            f"\t收藏{r['bookmarks']}\t[链接]({r['url']})\t{r['text']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    ap.add_argument("ids", nargs="+", help="post id 列表（蹭位榜/高收藏表的候选帖）")
    ap.add_argument("--as-of", help="ISO 时间(带时区)，算距今的基准；默认现在。"
                                     "按原定跑点算时传这个（取件账 09-15·1）")
    args = ap.parse_args(argv)

    as_of = datetime.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc)
    rows = pick(args.ids, load_posts_by_id(), as_of)

    for r in rows:
        print(format_line(r))

    missing = [r["id"] for r in rows if not r["found"]]
    if missing:
        print(f"\n⚠️ {len(missing)} 个 id 未找到：{', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
