"""mentions.csv 公箱自检：每一类错误注射一次，都必须报得出来。

它替代的是 `git diff | grep '^-'` —— 那条在有 stance 回填的日子必然报红（改行被数成删行），
09-09/10/11 连报三班，三次律升成脚本。一个只能报绿的检查器比没有更糟，所以这里每个
失败分支都有一条注射测试。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/check_mentions.py"
_spec = importlib.util.spec_from_file_location("check_mentions", _SRC)
cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cm)

HDR = "date,ticker,handle,post_id,views,bookmarks,stance\r\n"


def _rows(*lines):
    return cm.read_rows(HDR + "".join(l + "\r\n" for l in lines))


BASE = _rows("2026-09-10,MU,a,1,100,2,long", "2026-09-10,SNDK,b,2,50,1,")


def test_identical_is_clean():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,100,2,long", "2026-09-10,SNDK,b,2,50,1,"))
    assert r["ok"] and not any(r[k] for k in ("lost", "changed", "stance_changed", "added"))


def test_stance_backfill_is_allowed_and_counted():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,100,2,long", "2026-09-10,SNDK,b,2,50,1,recap"))
    assert r["ok"] and len(r["stance_filled"]) == 1


def test_new_rows_are_allowed_and_counted():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,100,2,long", "2026-09-10,SNDK,b,2,50,1,",
                               "2026-09-11,LITE,c,3,10,0,"))
    assert r["ok"] and len(r["added"]) == 1


def test_a_lost_row_is_reported():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,100,2,long"))
    assert not r["ok"] and len(r["lost"]) == 1


def test_a_changed_count_is_reported():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,999,2,long", "2026-09-10,SNDK,b,2,50,1,"))
    assert not r["ok"] and len(r["changed"]) == 1


def test_an_overwritten_stance_is_reported():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,100,2,recap", "2026-09-10,SNDK,b,2,50,1,"))
    assert not r["ok"] and len(r["stance_changed"]) == 1


def test_a_wiped_stance_is_reported():
    r = cm.compare(BASE, _rows("2026-09-10,MU,a,1,100,2,", "2026-09-10,SNDK,b,2,50,1,"))
    assert not r["ok"] and len(r["stance_changed"]) == 1


def test_crlf_versus_lf_is_not_a_change():
    lf = cm.read_rows(HDR.replace("\r\n", "\n") + "2026-09-10,MU,a,1,100,2,long\n"
                      "2026-09-10,SNDK,b,2,50,1,\n")
    assert cm.compare(BASE, lf)["ok"]
