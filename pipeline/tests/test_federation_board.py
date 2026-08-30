"""联邦控制台解析器的测试（`pipeline/tools/federation_board.py`）。

这个文件存在的理由，是 08-31 审计出的六处问题里有四处**同一个形状**：
解析器悄悄返回空，页面把「我没读懂」显示成「没有这件事」。所以每个告警这里都有
一个**阳性对照**——先证明它报得出阳性，才有资格相信它的阴性。
（`pitfall_a_stricter_test_can_be_blind` / Growth Gary 08-25 的总纲。）

federation_board.py 是一个从头跑到尾的脚本（import 即执行 git），所以这里按
`# --- PARSERS BEGIN/END ---` 标记切出纯函数区来 exec，不触发任何 git 调用。
"""
import datetime
import re
from pathlib import Path

import pytest

BOARD = Path(__file__).resolve().parents[1] / "tools" / "federation_board.py"


def _parsers():
    src = BOARD.read_text(encoding="utf-8")
    a = src.index("# --- PARSERS BEGIN")
    b = src.index("# --- PARSERS END ---")
    ns = {"re": re, "datetime": datetime}
    exec(src[a:b], ns)
    return ns


P = _parsers()


# ── 门铃解析：表格与 bullet 两种格式都要认 ──────────────────────────────────

TABLE_REPORT = """## 六、别的

正文里顺带提到「门铃待按」这四个字，不该被当成节标题。

| 收件人 | 事项 |
|---|---|
| **不该被抓的行** | 这张表在正文里，不在门铃节 |

## 七、门铃待按（只列不按）

| 收件人 | 事项 |
|---|---|
| **DATA ALEX** | universe_gated 只数到流动性闸 |

## 八、没动的大件
"""

BULLET_REPORT = """## ⑤ 门铃待按（只列不按）

- ⚠️ **OPS Fable / Andy** · **合 `origin/fix/joe-backstop-gate-date`**。
  main 上仍是旧写法，bug 是活的且已发作一次。
- **Plumber Joe** · 回归闸已交付，可接进晨检当量尺。

## ⑥ 收工三问
"""


def test_bell_section_is_heading_anchored():
    """标题锚定：正文里出现「门铃待按」四个字的段落不该被当成节。"""
    body = P["bell_section"](TABLE_REPORT)
    assert body is not None
    assert "不该被抓的行" not in body
    assert "universe_gated" in body


def test_bell_parses_table_format():
    items = P["parse_bell"](P["bell_section"](TABLE_REPORT))
    assert [w for w, _ in items] == ["DATA ALEX"]


def test_bell_parses_bullet_format():
    """08-27～08-30 四晚的真实形状：bullet + ⚠️ 前缀 + 跨行续写。

    旧解析器只认表格，这四晚 claim 列 0 张来自晨报——本测试就是那个假零的回归闸。
    """
    items = P["parse_bell"](P["bell_section"](BULLET_REPORT))
    who = [w for w, _ in items]
    assert who == ["OPS Fable / Andy", "Plumber Joe"], who
    # 跨行续写要并进同一条，不是丢掉
    assert "bug 是活的" in items[0][1]


def test_bell_alarm_fires_on_unknown_format():
    """阳性对照：节非空但一条都解析不出来时，调用方必须能看出「解析了 0 条」。"""
    unknown = "## 七、门铃待按\n\n1. DATA ALEX -- 换成有序列表了\n2. UI Claire -- 也换了\n\n## 八、别的\n"
    body = P["bell_section"](unknown)
    assert body is not None and body.strip()
    assert P["parse_bell"](body) == []   # <- 告警条件成立


# ── 关卡解析：跨行 + 失败时不静默 ──────────────────────────────────────────

def test_gate_reads_number_below_the_heading():
    """读数不在标题那一行——旧的 `[^\\n]*?` 写法在这里恒返回 None。"""
    md = "## 🎮 本周关卡（周日 24:00 结算）\n\n发布 5 件过关。\n**当前 3 / 5**\n\n## 今天的一件事\n"
    assert P["parse_gate"](md)[0] == 3


def test_gate_does_not_borrow_last_weeks_number_as_this_weeks():
    """周一刚翻周：本周节里没有读数，上周结算写着 6/5。
    这时必须返回 None + 一句说明，绝不能把上周的 6 当成本周进度。"""
    md = ("## 🏁 上周结算\n\n**🎮 关卡 6/5 —— 首次过关。**\n\n"
          "## 🎮 本周关卡（周日 24:00 结算）\n\n发布 5 件过关。进度看每早日推。\n\n## 今天的一件事\n")
    n, note = P["parse_gate"](md)
    assert n is None
    assert "上周结算 6/5" in note
    assert not note.startswith("⚠️")     # 这是正常状态，不是解析故障


def test_gate_alarm_fires_when_section_is_gone():
    """阳性对照：NOW.md 改版把节名换掉时必须报 ⚠️，而不是让面板消失。"""
    n, note = P["parse_gate"]("## 本周目标\n\n什么都没有\n")
    assert n is None and note.startswith("⚠️")


# ── cron 新鲜度：按交易日算，不是「窗口内有过就绿」 ──────────────────────────

def _weekday_only(d):
    return d.weekday() < 5


def test_cron_green_only_when_data_is_current():
    # 周五 08-28 收盘是最近完成 session；数据落到 08-30 → 不落后
    assert P["sessions_behind"]("2026-08-30", datetime.date(2026, 8, 28), _weekday_only) == 0
    assert P["cron_state"](0) == "ok"


def test_cron_ignores_weekends_when_counting_lag():
    # 数据停在周五 08-28，最近完成 session 是下周一 08-31 → 只落后 1 个交易日
    assert P["sessions_behind"]("2026-08-28", datetime.date(2026, 8, 31), _weekday_only) == 1
    assert P["cron_state"](1) == "ok"


def test_cron_alarm_fires_when_cron_dies():
    """阳性对照：旧写法「14 天窗口内有过任意一条就 🟢」在这里照样满绿。"""
    behind = P["sessions_behind"]("2026-08-14", datetime.date(2026, 8, 28), _weekday_only)
    assert behind == 10
    assert P["cron_state"](behind) == "red"
    assert P["cron_state"](2) == "warn"
    assert P["cron_state"](3) == "red"


# ── 核销：已被拍板的待办不该再上「等你拍板」 ────────────────────────────────

LEDGER = """### T1 · ~~回收两个 Discord 付费角色~~ **⏸ 已否决暂缓（Andy 08-28）**

`status: deferred` · Andy 08-28 原话：「否定。还不做这件事。」

### T5 · `#welcome` 加升级入口（Andy 08-26：「要做！」）

`status: 待办` · 归属：Andy
"""


def test_settled_item_is_struck_from_the_board():
    """KB388 的实测形状：INBOX 里的指针还挂着，权威源里 T1 已被拍板否决。"""
    idx = P["settled_sigs"]([LEDGER])
    assert P["is_settled"]("回收两个 Discord 付费角色。 Andy 08-25 原话：「这个是要处理的，提醒我。」", idx)


def test_open_item_survives_the_settlement_check():
    """阴性对照：没被核销的 T5 必须留在板上——核销不能变成一把无差别的扫帚。"""
    idx = P["settled_sigs"]([LEDGER])
    assert not P["is_settled"]("T5 · #welcome 加升级入口（Andy 08-26：「要做！」）", idx)


def test_settlement_needs_a_real_overlap():
    """短标题不参与核销（<12 字指纹），免得靠几个字就误杀。"""
    assert not P["is_settled"]("清库存", P["settled_sigs"]([LEDGER]))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
