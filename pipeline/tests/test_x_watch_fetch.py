"""X 日调研抓取器：日归档只增不减 + 指标名不算代码。

fetch.py 住在 Fluxus_Brand/ops/tools/x_watch/（Marketing Steve 线的工具），按路径加载；
测试放在这里是因为 CI（tests.yml）只跑 pipeline/tests —— 放在工具旁边的测试没人调用。

钉住两件事：
* merge_day_posts —— 09-10 一轮短抓把 205 条的日归档写成 116 条残片。这类 bug 在
  所有计数检查下都是绿的：文件结构完好，只是少了。
* tickers —— 09-11 人数榜上的 $SMA/$RS 来自「50 SMA」「RS line」这类正文。RS/SMA
  是真代码，所以只拦裸词，带 $ 的必须照认。

两条都先把 bug 放回去、确认它们报得出阳性，才信它们的绿。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "Fluxus_Brand/ops/tools/x_watch/fetch.py"
_spec = importlib.util.spec_from_file_location("x_watch_fetch", _SRC)
fx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fx)


def _p(i, hour, views=100):
    return {"id": str(i), "h": "a", "dt": f"2026-09-10T{hour:02d}:00:00+00:00",
            "views": views, "bookmarks": 1}


def test_a_short_fetch_cannot_shrink_the_day():
    old = [_p(i, 10 + i) for i in range(5)]
    merged = fx.merge_day_posts(old, old[3:])   # API 只返回了后两条
    assert {r["id"] for r in merged} == {r["id"] for r in old}


def test_fresh_counts_win():
    [r] = fx.merge_day_posts([_p(1, 10, views=100)], [_p(1, 10, views=250)])
    assert r["views"] == 250


def test_new_posts_are_added_and_sorted_by_time():
    merged = fx.merge_day_posts([_p(1, 12), _p(2, 14)], [_p(2, 14), _p(3, 9)])
    assert [r["id"] for r in merged] == ["3", "1", "2"]


def test_first_write_is_just_the_fresh_rows():
    fresh = [_p(1, 10)]
    assert fx.merge_day_posts([], fresh) == fresh


def test_duplicate_ids_within_one_fetch_collapse():
    [r] = fx.merge_day_posts([], [_p(1, 10, views=1), _p(1, 10, views=2)])
    assert r["views"] == 2


@pytest.mark.parametrize("text", [
    "back above the 50 SMA", "RS line at new highs", "PPI tomorrow", "EMA 21 reclaim",
])
def test_bare_indicator_names_are_not_tickers(text):
    assert not ({"SMA", "RS", "PPI", "EMA"} & fx.tickers(text))


@pytest.mark.parametrize("text,sym", [
    ("$RS breaking out", "RS"), ("adding $SMA here", "SMA"), ("$MA into earnings", "MA"),
])
def test_dollar_prefixed_indicator_names_still_count(text, sym):
    assert sym in fx.tickers(text)


def test_ordinary_bare_tickers_still_count():
    assert "NVDA" in fx.tickers("NVDA looks strong")


# --------------------------------------------------------------------------
# own_account —— @Fluxus_Z 自己的粉丝数(Growth Gary 09-13 挂单)
# --------------------------------------------------------------------------

def test_own_account_maps_the_real_fields():
    resp = {"status": "success", "data": {"followers": 275, "following": 534, "statusesCount": 895}}
    r = fx.own_account_row(resp, "2026-09-12", "2026-09-13T03:10:00+00:00")
    assert (r["followers"], r["following"], r["tweets"]) == (275, 534, 895)
    assert r["source"] == fx.OWN_SRC


@pytest.mark.parametrize("resp", [{}, {"msg": "Credits is not enough"}, {"data": {}}, None])
def test_own_account_failure_writes_blank_with_reason_not_a_guess(resp):
    r = fx.own_account_row(resp, "2026-09-12", "t")
    assert r["followers"] == "" and r["source"].startswith("取不到")


def test_own_account_upsert_keeps_one_row_per_et_day_latest_last(tmp_path):
    p = tmp_path / "own.csv"
    mk = lambda d, n: {"date_et": d, "followers": n, "following": 1, "tweets": 1,
                       "fetched_utc": "t", "source": "s"}
    fx.upsert_own_account(p, mk("2026-09-12", 270))
    fx.upsert_own_account(p, mk("2026-09-11", 260))
    fx.upsert_own_account(p, mk("2026-09-12", 275))   # 同日第二班
    lines = p.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert lines[-1].startswith("2026-09-12,275,")
