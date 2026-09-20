"""圈外主题人数：顺带提到一个主题的人，不算讲了这个主题。

取件账 09-18·1 → 09-19·2 → 09-20·1，同一个形状三次：一条清单帖把二十只票
甩出来、一条回复帖把「crypto」当视频话题名列一下，人数榜照单全收，主题就
过了 >=3 人的闸，上页变成「⭐ 起量」。

钉住三件事：
* 清单帖与回复帖被剔，raw 与 kept 两个数同时留在结果里（并排打印的前提）；
* 被剔的人附得出理由——静默丢行就是下一次没人发现尺子瞎了；
* 同一个人既发过清单帖又发过真帖时算他讲了，且不出现在 dropped 里。

⭐ 阳性对照按「能坏的方式」分类造，两个方向各一条：
  1. 漏改（drop_reason 永远返回 None）→ test_gate_must_actually_drop 红
  2. 改了但接错（kept 覆盖掉 raw，或剔得只剩空）→ test_raw_count_survives_filtering
     与 test_a_real_post_survives_a_list_post 红
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "data/content/x_watch/tools/theme_count.py"
_spec = importlib.util.spec_from_file_location("x_watch_theme_count", _SRC)
tc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tc)

THEMES = {"加密": r"\bbitcoin\b|\bbtc\b|\bcrypto\b|\$BTC\b"}


def _post(handle, text, tickers=(), is_reply=False):
    return {"h": handle, "text": text, "tickers": list(tickers), "is_reply": is_reply}


def test_gate_must_actually_drop():
    """漏改的阳性对照：清单帖与回复帖必须双双被剔。"""
    posts = [
        _post("real_one", "BTC weekly reversal above the rising 10wma"),
        _post("listy", "$AAPL $MSFT $NVDA $BTC $AMD $TSLA weekly setups",
              tickers=list("ABCDEF")),
        _post("replier", "I covered crypto, my portfolio and more in the video",
              is_reply=True),
    ]
    box = tc.count(posts, THEMES)["加密"]
    assert box["kept"] == ["real_one"]
    assert set(box["dropped"]) == {"listy", "replier"}


def test_raw_count_survives_filtering():
    """接错的阳性对照之一：过滤不许把原始人数一起抹掉。"""
    posts = [
        _post("real_one", "BTC weekly reversal"),
        _post("listy", "$BTC and twenty other names", tickers=list("ABCDEF")),
    ]
    box = tc.count(posts, THEMES)["加密"]
    assert len(box["raw"]) == 2, "原始人数必须原样留着，并排打印全靠它"
    assert len(box["kept"]) == 1


def test_dropped_carries_a_reason():
    """静默丢行＝下一班没法发现尺子瞎了。每个被剔的人必须带得出理由。"""
    posts = [_post("listy", "$BTC plus the rest", tickers=list("ABCDEFG"))]
    box = tc.count(posts, THEMES)["加密"]
    assert "清单帖" in box["dropped"]["listy"]
    assert "7" in box["dropped"]["listy"], "理由里要写清挂了几个代码"


def test_a_real_post_survives_a_list_post():
    """接错的阳性对照之二：同一个人发过清单帖也发过真帖，算他讲了，且不进 dropped。"""
    posts = [
        _post("mixed", "$BTC in a twenty-name list", tickers=list("ABCDEF")),
        _post("mixed", "Bitcoin just confirmed a weekly reversal"),
    ]
    box = tc.count(posts, THEMES)["加密"]
    assert box["kept"] == ["mixed"]
    assert box["dropped"] == {}


def test_untouched_theme_reports_zero_not_missing():
    """闸没命中的主题也要出一行——空结果和没算过长得不能一样。"""
    box = tc.count([_post("someone", "$AAPL breaking out")], THEMES)["加密"]
    assert box == {"raw": [], "kept": [], "dropped": {}}


def test_todays_shape_reproduces():
    """09-20 实况的形状：原始 3 人过闸、过滤后 2 人没过。"""
    posts = [
        _post("a", "Review: BTC and Ethereum ETF flows"),
        _post("b", "#BTC weekly chart, first weekly reversal confirmed"),
        _post("c", "I discussed $INTC, my favorite hyperscaler, crypto, and more here",
              is_reply=True),
    ]
    box = tc.count(posts, THEMES)["加密"]
    assert len(box["raw"]) == 3 and len(box["kept"]) == 2
