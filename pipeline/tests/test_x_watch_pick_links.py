"""蹭位榜/高收藏表选票：按 id 查 posts/*.jsonl，链接与距今小时数不许再靠手打。

取件账 09-16·1：09-16、09-17 两班手打 status id 和距今小时数各错一次（09-17 还
按 UTC 算距今），算上 09-10/09-11 已是同形状坑第 3、4 次。钉住两件事：
* pick() 给已知 id 算出的 url 与距今小时数（ET 基准时刻）必须逐字对得上——不再
  由人心算时区换算。
* 打错的 id（不在 posts 里）必须报「未找到」，不能被静默漏掉或用占位符顶替
  （09-11 占位符 id 事故的同一种坑）。
"""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/pick_links.py"
_spec = importlib.util.spec_from_file_location("x_watch_pick_links", _SRC)
pl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pl)


def _post(pid, hour_utc, handle="ripster47", views=1000, replies=1, bookmarks=4,
          text="hello", url=None):
    row = {
        "id": pid, "h": handle,
        "dt": f"2026-09-18T{hour_utc:02d}:00:00+00:00",
        "et_date": "2026-09-18", "text": text, "views": views, "likes": 0,
        "bookmarks": bookmarks, "replies": replies, "reposts": 0, "is_reply": False,
        "tickers": [],
    }
    if url is not None:
        row["url"] = url
    return row


POSTS = {
    "1": _post("1", 12, url="https://x.com/ripster47/status/1"),
    "2": _post("2", 15, handle="Jake__Wujastyk"),  # 无 url 字段，测重建
}

AS_OF = datetime(2026, 9, 18, 23, 0, 0, tzinfo=timezone.utc)  # 12:00 后 11h


def test_hours_ago_matches_utc_delta():
    [r] = pl.pick(["1"], POSTS, AS_OF)
    assert r["found"] is True
    assert r["hours_ago"] == 11.0


def test_url_read_from_row_when_present():
    [r] = pl.pick(["1"], POSTS, AS_OF)
    assert r["url"] == "https://x.com/ripster47/status/1"


def test_url_rebuilt_from_handle_and_id_when_missing():
    [r] = pl.pick(["2"], POSTS, AS_OF)
    assert r["url"] == "https://x.com/Jake__Wujastyk/status/2"
    assert r["hours_ago"] == 8.0


def test_dt_et_is_et_not_utc():
    # 2026-09-18 12:00 UTC = 08:00 ET（EDT,UTC-4）
    [r] = pl.pick(["1"], POSTS, AS_OF)
    assert r["dt_et"] == "09-18 08:00"


def test_missing_id_is_reported_not_skipped():
    rows = pl.pick(["1", "does-not-exist"], POSTS, AS_OF)
    assert rows[1] == {"id": "does-not-exist", "found": False}


def test_order_is_preserved_and_matches_input():
    rows = pl.pick(["2", "1"], POSTS, AS_OF)
    assert [r["id"] for r in rows] == ["2", "1"]


def test_format_line_flags_missing_ids():
    line = pl.format_line({"id": "bad-id", "found": False})
    assert "未找到" in line
    assert "bad-id" in line


def test_load_posts_by_id_indexes_across_files(tmp_path: Path):
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    (posts_dir / "2026-09-17.jsonl").write_text(
        json.dumps(_post("10", 5)) + "\n", encoding="utf-8")
    (posts_dir / "2026-09-18.jsonl").write_text(
        json.dumps(_post("11", 6)) + "\n" + json.dumps(_post("12", 7)) + "\n",
        encoding="utf-8")

    idx = pl.load_posts_by_id(posts_dir)

    assert set(idx) == {"10", "11", "12"}
    assert idx["11"]["dt"].startswith("2026-09-18T06:00")


def test_main_exit_code_nonzero_when_any_id_missing(monkeypatch, capsys):
    monkeypatch.setattr(pl, "load_posts_by_id", lambda *a, **k: POSTS)

    code = pl.main(["1", "--as-of", "2026-09-18T23:00:00+00:00"])
    assert code == 0

    code = pl.main(["1", "typo-id", "--as-of", "2026-09-18T23:00:00+00:00"])
    assert code == 1
    assert "typo-id" in capsys.readouterr().err
