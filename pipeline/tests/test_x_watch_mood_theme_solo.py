"""mood 的圈外主题人数要并排给出「剔清单帖之后还剩几个人」。

取件账 09-18·1 → 09-19·2 → 09-22 第 3 次，三次律到期。形状每次一样：
一条挂几十个代码的扫描表/收盘综述把 `$IBIT` `$BTC` 甩出来，mood 照单全收，
主题过了 >=3 人的闸，日报第 3a 节就会把它当 ⭐ 起量置顶。09-22 实测 crypto
4 人里 3 个只出现在清单帖里，真正单独讲加密的只有 1 个。

这一版**只改报数，不改判定**：`out_*` 四列与过闸条件一个字没动，`CALC` 不升版，
`mood_daily.csv` 的老行仍然可比。闸的形式是「过闸时必须并排打印剔完的人数，
不足人数闸就拉警报并写进 theme_events.csv 的 note」——治的是读表的人看不见。

⚠️ 判据只有一份，在 `tools/theme_count.py` 的 `drop_reason`；本脚本 import 它，
不重抄。`test_gate_shares_one_ruler` 钉住这一点。

⭐ 阳性对照按「能坏的方式」分类造，两个方向各有测试报红：
  1. **漏改**（solo 就等于 raw，没剔）→ test_list_post_people_are_dropped 红
  2. **改了但接错**（solo 覆盖了 raw，或把真帖一起剔光）→
     test_raw_count_is_untouched 与 test_a_real_post_survives_among_list_posts 红
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "data/content/x_watch/scoring/mood_index.py"
_spec = importlib.util.spec_from_file_location("x_watch_mood_index", _SRC)
mood = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mood)


def _post(handle, text, tickers=(), is_reply=False):
    return {"h": handle, "text": text, "tickers": list(tickers), "is_reply": is_reply}


_LIST20 = [f"T{i}" for i in range(20)]


def test_gate_shares_one_ruler():
    """判据必须**来自** theme_count.py 那一份，不是本脚本自己抄的第二份。

    身份比较（`is`）在这里没用：两处各自 exec 一遍模块就是两个函数对象。
    真正要钉的是「这段代码住在哪个文件里」—— 谁把判据复制进 mood_index.py，
    co_filename 就会变成 mood_index.py，这条立刻红。
    """
    tc_src = _ROOT / "data/content/x_watch/tools/theme_count.py"
    assert Path(mood.drop_reason.__code__.co_filename).resolve() == tc_src.resolve()

    tc_spec = importlib.util.spec_from_file_location("x_watch_theme_count", tc_src)
    tc = importlib.util.module_from_spec(tc_spec)
    tc_spec.loader.exec_module(tc)
    assert mood.LIST_TICKERS == tc.LIST_TICKERS
    for post in (_post("a", "x"), _post("a", "x", is_reply=True),
                 _post("a", "x", tickers=_LIST20)):
        assert mood.drop_reason(post, mood.LIST_TICKERS) == \
               tc.drop_reason(post, tc.LIST_TICKERS)


def test_list_post_people_are_dropped():
    """漏改的阳性对照：只出现在清单帖里的人，不进 solo。"""
    rows = [
        _post("real_one", "$IBIT weekly base, first higher low"),
        _post("scanner", "watchlist $IBIT " + " ".join("$" + t for t in _LIST20),
              tickers=["IBIT", *_LIST20]),
        _post("recapper", "daily recap $MSTR " + " ".join("$" + t for t in _LIST20),
              tickers=["MSTR", *_LIST20]),
    ]
    _, raw, solo = mood.metrics(rows)
    assert raw["crypto"] == {"real_one", "scanner", "recapper"}
    assert solo["crypto"] == {"real_one"}


def test_raw_count_is_untouched():
    """接错方向一：solo 不许覆盖 raw —— out_* 四列是台账，改了老行就不可比。"""
    rows = [
        _post("scanner", "$IBIT " + " ".join("$" + t for t in _LIST20),
              tickers=["IBIT", *_LIST20]),
    ]
    m, raw, solo = mood.metrics(rows)
    assert m["out_crypto"] == 1, "过闸用的人数必须还是剔之前那个"
    assert raw["crypto"] == {"scanner"}
    assert solo["crypto"] == set()


def test_a_real_post_survives_among_list_posts():
    """接错方向二：不许把真帖一起剔光。同一个人发过清单帖也发过真帖，算他讲了。"""
    rows = [
        _post("both", "$IBIT " + " ".join("$" + t for t in _LIST20),
              tickers=["IBIT", *_LIST20]),
        _post("both", "$IBIT reclaimed the 50dma, watching for follow through"),
    ]
    _, raw, solo = mood.metrics(rows)
    assert raw["crypto"] == {"both"}
    assert solo["crypto"] == {"both"}


def test_reply_posts_do_not_carry_a_theme():
    """回复帖不算讲了这个主题 —— 和速报同一把尺子。"""
    rows = [
        _post("replier", "yeah $IBIT looks fine", is_reply=True),
        _post("real_one", "$IBIT base building above the 10wma"),
    ]
    _, raw, solo = mood.metrics(rows)
    assert raw["crypto"] == {"replier", "real_one"}
    assert solo["crypto"] == {"real_one"}


def test_other_themes_unaffected_by_crypto_list_posts():
    """一个主题的清单帖不该动到别的主题的读数。"""
    rows = [
        _post("scanner", "$IBIT " + " ".join("$" + t for t in _LIST20),
              tickers=["IBIT", *_LIST20]),
        _post("gold_one", "$GDX flag on the daily, stalking the breakout"),
    ]
    m, raw, solo = mood.metrics(rows)
    assert solo["gold"] == {"gold_one"}
    assert m["out_gold"] == 1
