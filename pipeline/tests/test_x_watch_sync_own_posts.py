"""posts.csv 的第二把尺子（Andy 2026-09-20 W38 结算台：「P1 批」）。

钉住的是 W38 那次失败的形状：`posts.csv` 只有人手工补录才会长，09-14 起漏了
4 条，而漏掉的那条 403 曝光是全周最好的帖。闸问的是「有没有一条帖在 X 上存在
而台账里没有」—— 不是「statuses_count 等不等于行数」（前者含回复与转发，
那个等式永远对不上，会退化成一个天天喊狼来了的闸）。

阳性对照按「能坏的方式」分两类造：漏改 / 改了但接错，两个方向都要报得出来。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SRC = (Path(__file__).resolve().parents[2]
        / "data/content/x_watch/tools/sync_own_posts.py")
_spec = importlib.util.spec_from_file_location("sync_own_posts", _SRC)
sy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sy)

FIELDS = ["post_id", "date", "bucket", "lang", "views", "likes", "replies",
          "reposts", "bookmarks", "follows", "note"]


def tweet(tid, created="Fri Sep 18 15:54:05 +0000 2026", **kw):
    t = {"id": tid, "createdAt": created, "text": "hello", "viewCount": 403,
         "likeCount": 4, "replyCount": 1, "retweetCount": 0, "bookmarkCount": 0}
    t.update(kw)
    return t


def row(tid, note="人写的字", **kw):
    r = {f: "" for f in FIELDS}
    r.update(post_id=tid, date="2026-09-19", bucket="VOICE", lang="EN",
             views="11", likes="0", replies="0", reposts="0", bookmarks="0",
             note=note)
    r.update(kw)
    return r


# --- 闸本体：X 上有、台账里没有 ------------------------------------------

def test_missing_id_is_reported():
    """W38 的真实形状：403 那条在 X 上，台账里没有。"""
    assert [t["id"] for t in sy.missing_ids([tweet("A")], [row("B")])] == ["A"]


def test_id_already_in_ledger_is_not_reported():
    """在册的不报 —— 否则闸天天红，等于没有闸。"""
    assert sy.missing_ids([tweet("A")], [row("A")]) == []


def test_pre_ledger_tweet_is_not_reported():
    """台账 2026-07-30 起记；五月那条 $APP 不该每次跑都报一次红。"""
    old = tweet("OLD", created="Thu May 28 06:55:31 +0000 2026")
    assert sy.missing_ids([old], [row("B")]) == []


# --- 补录与刷新 ------------------------------------------------------------

def test_refresh_never_overwrites_the_human_note():
    """读数可以覆盖，人写的字不行 —— 只在尾巴追一个复读戳。"""
    r = row("A", note="⭐ 本周最好 —— 队列 #5 原样发出")
    sy.refresh_row(r, tweet("A"), "09-21")
    assert r["note"].startswith("⭐ 本周最好 —— 队列 #5 原样发出")
    assert "09-21 复读" in r["note"]
    assert r["views"] == "403"


def test_refresh_is_idempotent_on_the_note():
    """同一天跑两次，不许追两个戳。"""
    r = row("A")
    sy.refresh_row(r, tweet("A"), "09-21")
    first = r["note"]
    sy.refresh_row(r, tweet("A"), "09-21")
    assert r["note"] == first


def test_new_row_flags_itself_for_human_review():
    """机器分不出 VOICE / LONGFORM，补录行必须自己承认这一点。"""
    r = sy.new_row(tweet("A"), "09-21", FIELDS)
    assert r["date"] == "2026-09-19"          # UTC 09-18 15:54 → JST 09-19
    assert "待人工复核" in r["note"]
    assert r["views"] == "403"


def test_bucket_is_inferred_from_structure():
    assert sy.bucket_of(tweet("A", text="RT @Fluxus_Z: ...")) == "RT"
    assert sy.bucket_of(tweet("A", isReply=True)) == "REPLY"
    assert sy.bucket_of(tweet("A", quoted_tweet={"id": "x"})) == "QT"
    assert sy.bucket_of(tweet("A")) == "ARC"
