#!/usr/bin/env python3
"""posts.csv 的第二把尺子 —— 别再靠「有人记得」。

Andy 2026-09-20 W38 结算台原话：「P1 批」。

起因（W38）：`posts.csv` 只有人手工补录才会长。09-14 起它漏了 4 条，其中
ET 09-18 那条 403 曝光是全周最好的帖。上一周的 Gate 子 agent 照着这本账
复核，查得一丝不苟，报「本周仅 2 帖」—— **复核账里的数，证明不了这本账是全的。**
而拆穿它的计数（`own_account.csv` 的 tweets，898→909）一直在同一个目录里。

两个模式：
  --check   只报不写。`last_tweets` 里有、`posts.csv` 里没有的帖 → 列出来，退出码 1。
  --sync    把缺的补进去、把在册的读数刷新一遍（note 只追加复读戳，永不覆盖）。

⚠️ 不拿 statuses_count 和 posts.csv 行数做等式：前者含回复与转发，后者不一定收。
   闸判的是「有没有一条帖在 X 上存在而台账里没有」，这个问题没有口径歧义。
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[4]
POSTS = ROOT / "data/content/posts.csv"
API = "https://api.twitterapi.io"
HANDLE = "Fluxus_Z"
# 台账从 2026-07-30 起记。更早的帖（五月那条 $APP）不补，不然每次跑都报一次红。
LEDGER_START = "2026-07-30"


def key() -> str:
    """env 优先，再落到仓库根 .env —— 和 fetch.py 同一套（.env 被 gitignore，
    临时 worktree 里没有它，那里只能靠 env 变量，不该抛一脸 traceback）。"""
    k = os.environ.get("TWITTERAPI_KEY")
    if not k:
        env = ROOT / ".env"
        m = re.search(r"TWITTERAPI_KEY=(\S+)", env.read_text()) if env.exists() else None
        k = m.group(1).strip().strip("\"'") if m else None
    if not k:
        sys.exit(f"缺 TWITTERAPI_KEY：设环境变量，或写进 {ROOT}/.env")
    return k


def fetch_live(k: str, handle: str = HANDLE) -> list[dict]:
    req = Request(f"{API}/twitter/user/last_tweets?userName={handle}",
                  headers={"X-API-Key": k})
    with urlopen(req, timeout=45) as r:
        d = json.loads(r.read())
    return d.get("data", {}).get("tweets") or d.get("tweets") or []


def created_utc(tweet: dict) -> datetime:
    return datetime.strptime(tweet["createdAt"], "%a %b %d %H:%M:%S %z %Y")


def jst_date(tweet: dict) -> str:
    from datetime import timedelta
    return (created_utc(tweet) + timedelta(hours=9)).strftime("%Y-%m-%d")


def bucket_of(tweet: dict) -> str:
    """机器只分得出结构，分不出 VOICE / LONGFORM —— 那两个要人看正文。"""
    if (tweet.get("text") or "").startswith("RT @"):
        return "RT"
    if tweet.get("isReply"):
        return "REPLY"
    if tweet.get("quoted_tweet"):
        return "QT"
    return "ARC"


def missing_ids(live: list[dict], rows: list[dict],
                since: str = LEDGER_START) -> list[dict]:
    """X 上有、台账里没有的帖（按台账起始日之后）。这就是闸判的那件事。"""
    have = {r["post_id"] for r in rows}
    return [t for t in live
            if t["id"] not in have and jst_date(t) >= since]


def stamp(day: str) -> str:
    return f"｜{day} 复读(sync_own_posts)"


def refresh_row(row: dict, tweet: dict, day: str) -> bool:
    """刷新读数。note 只追加一次复读戳，**永不覆盖人写的字**。返回有没有动过。"""
    before = dict(row)
    row["views"] = str(tweet.get("viewCount") or "")
    row["likes"] = str(tweet.get("likeCount") or 0)
    row["replies"] = str(tweet.get("replyCount") or 0)
    row["reposts"] = str(tweet.get("retweetCount") or 0)
    if tweet.get("bookmarkCount") is not None:
        row["bookmarks"] = str(tweet["bookmarkCount"])
    s = stamp(day)
    if s not in row["note"]:
        row["note"] += s
    return row != before


def new_row(tweet: dict, day: str, fields: list[str]) -> dict:
    row = {f: "" for f in fields}
    text = (tweet.get("text") or "").replace("\n", " ").strip()
    row.update(
        post_id=tweet["id"], date=jst_date(tweet), bucket=bucket_of(tweet),
        lang="EN", views=str(tweet.get("viewCount") or ""),
        likes=str(tweet.get("likeCount") or 0),
        replies=str(tweet.get("replyCount") or 0),
        reposts=str(tweet.get("retweetCount") or 0),
        bookmarks=str(tweet.get("bookmarkCount") or 0), follows="",
        note=(f"{text[:120]}｜UTC {tweet['createdAt']}｜⚠️ sync_own_posts {day} 自动补录 —— "
              f"bucket 由结构推断（VOICE/LONGFORM 机器分不出），lang 默认 EN，**待人工复核**"),
    )
    return row


def load() -> tuple[list[dict], list[str]]:
    rows = list(csv.DictReader(POSTS.open()))
    return rows, list(rows[0].keys())


def save(rows: list[dict], fields: list[str]) -> None:
    rows.sort(key=lambda r: (r["date"], r["post_id"]))
    with POSTS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync", action="store_true", help="补录 + 刷新读数（默认只 check）")
    ap.add_argument("--handle", default=HANDLE)
    a = ap.parse_args()

    rows, fields = load()
    live = fetch_live(key(), a.handle)
    day = datetime.now(timezone.utc).strftime("%m-%d")
    miss = missing_ids(live, rows)

    print(f"X 上最近 {len(live)} 条 · 台账 {len(rows)} 行 · 台账起始日 {LEDGER_START}")
    if miss:
        print(f"\n⛔ {len(miss)} 条在 X 上、不在 posts.csv：")
        for t in miss:
            print(f"  {t['id']} {jst_date(t)} {bucket_of(t):5s} "
                  f"{t.get('viewCount')} 曝光 · {(t.get('text') or '')[:60]}")
    else:
        print("\n✅ 台账没有缺口（last_tweets 窗口内）")

    if not a.sync:
        return 1 if miss else 0

    touched = sum(refresh_row(r, t, day)
                  for r in rows for t in live if r["post_id"] == t["id"])
    rows += [new_row(t, day, fields) for t in miss]
    save(rows, fields)
    print(f"\n已写入：补录 {len(miss)} 行 · 刷新 {touched} 行 → {POSTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
