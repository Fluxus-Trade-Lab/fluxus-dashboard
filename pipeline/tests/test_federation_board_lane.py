# -*- coding: utf-8 -*-
"""联邦看板的 lane 归属：路径优先，文本只当兜底。

为什么用 exec 而不是 import：`pipeline/tools/federation_board.py` 是单文件脚本，
模块级就把整块报表跑完（要 git、要写 HTML）。这里只 exec 它的**头部**
（到 `# ---------- git 数据 ----------` 为止），拿到 ROSTER / PATH_RULES / lane_* 四个函数，
不触发任何 git 调用。

⚠️ 阳性对照（实测过，别删这段注释）。直接拿本文件去跑 v4 旧版是 **17/17 全红，但红的是
KeyError**——那只证明函数不存在，不证明断言能抓住答错。真对照是把三个 bug 逐个注射回本版：

| 注射 | 报红的用例 |
|---|---|
| ① `lane_of` 退回「按花名册顺序首个命中」（v4 的真实写法） | 1 红：`…earliest_mention_not_the_roster_order` |
| ② 公箱不再弃权（`DATA_CONTRACTS` 等照常投票） | 4 红：`…shared_mailboxes_cast_no_vote` 四个参数 |
| ③ `lane_of_arrow` 拿整行找别名而不是只看箭头后 40 字 | 1 红：`…only_reads_what_comes_after_the_arrow` |

注射 ③ 第一版**全绿**——当时那条箭头用例里收件人恰好排在发件人前面，取最早位置两种写法答案一样。
补了「箭头之前有转投递人」的用例才报红。**没先验证一个检查能报出阳性，就不该信它的阴性。**
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "pipeline", "tools", "federation_board.py")
MARKER = "# ---------- git 数据 ----------"


@pytest.fixture(scope="module")
def board(tmp_path_factory):
    with open(SCRIPT, encoding="utf-8") as fh:
        src = fh.read()
    assert MARKER in src, "脚本结构变了：找不到 git 数据分界线，测试需要同步更新"
    head = src[: src.index(MARKER)]
    ns = {"__name__": "federation_board_head"}
    old_argv = sys.argv
    sys.argv = ["federation_board.py", ROOT, str(tmp_path_factory.mktemp("b") / "o.html")]
    try:
        exec(compile(head, SCRIPT, "exec"), ns)
    finally:
        sys.argv = old_argv
    return ns


# ---------- 路径投票 ----------

def test_frontend_paths_go_to_claire(board):
    assert board["lane_of_paths"](["frontend/src/pages/WatchlistPage.jsx"]) == "UI Claire"


def test_screener_paths_go_to_alex(board):
    assert board["lane_of_paths"](["pipeline/screeners/watchlist.py"]) == "DATA ALEX"


def test_research_paths_go_to_zac(board):
    assert board["lane_of_paths"](["data/research/adr_floor_2026-08/results.md"]) == "Nighty Zac"


def test_regime_ledger_beats_the_generic_history_rule(board):
    """`data/history/` 归数据端，但 regime_ledger.csv 是风险线唯一写入方——具体规则必须先命中。"""
    assert board["lane_of_paths"](["data/history/regime_ledger.csv"]) == "RND Linda"
    assert board["lane_of_paths"](["data/history/breadth_last.csv"]) == "DATA ALEX"


@pytest.mark.parametrize(
    "shared",
    [
        "data/reference/DATA_CONTRACTS.md",
        "data/reference/DATA_RELIABILITY.md",
        "data/research/night_reports/INBOX.md",
        "Fluxus_Brand/ops/material_inbox.md",
    ],
)
def test_shared_mailboxes_cast_no_vote(board, shared):
    """三个 append-only 公箱各线都能写，光看路径定不了线——必须弃权，交给文本兜底。"""
    assert board["lane_of_paths"]([shared]) is None


def test_a_tie_is_not_a_verdict(board):
    """两条线各一票 = 说不清，返回 None 而不是让规则表顺序替你拍板。"""
    assert board["lane_of_paths"](["frontend/src/a.jsx", "pipeline/screeners/b.py"]) is None


def test_majority_wins(board):
    got = board["lane_of_paths"](["frontend/src/a.jsx", "frontend/src/b.jsx", "pipeline/screeners/c.py"])
    assert got == "UI Claire"


# ---------- 箭头收件人 ----------

def test_arrow_takes_the_recipient_not_the_sender(board):
    """契约行真例（§七 08-27）：收件人是风险线，而「数据端」只是发件人自称。"""
    line = "→ 风险线(模型 R&D):两盏灯是「变体幸存者」,请裁决(数据端研究协议回填时发现)"
    assert board["lane_of_arrow"](line) == "RND Linda"


def test_arrow_handles_the_ascii_form_and_parenthesised_alias(board):
    assert board["lane_of_arrow"]("-> 前端(UI Claire):P/L 1D 两列把跳空算成盈亏") == "UI Claire"


def test_arrow_only_reads_what_comes_after_the_arrow(board):
    """箭头**之前**的线名是转投递人，不是收件人。
    真形状：`contracts(§12): Joe 转投递 -- ... → DATA ALEX: ...`。
    （阳性对照：把 lane_of_arrow 改成拿整行去找别名，本用例立刻报红。）"""
    line = "[08-27] Plumber Joe 转投递 → DATA ALEX: universe_gated 只数到流动性闸"
    assert board["lane_of_arrow"](line) == "DATA ALEX"


def test_no_arrow_means_no_opinion(board):
    assert board["lane_of_arrow"]("night(08-28): 晨报骨架") is None


# ---------- 关键词兜底 ----------

def test_keyword_fallback_takes_the_earliest_mention_not_the_roster_order(board):
    """真例：OPS 派的活里顺带写了「建议 Joe 认领」。归属是派活的人，不是被点名的人。"""
    s = "task(挂单): Gate 声明制+封顶三行制 —— polydao loop 对账后仅存的缺口;建议 Joe 认领"
    assert board["lane_of"](s) == "OPS Fable"


def test_paths_outrank_text(board):
    """`verdict(adr)` 里有 Zac 的关键词 adr，但它动的是宪法与公箱——路径说了算。"""
    assert board["lane_for"]("verdict(adr): Andy 拍板 ADR>=3.5 闸保留", ["CLAUDE.md"]) == "OPS Fable"


def test_unattributable_falls_through_to_the_federation(board):
    assert board["lane_for"]("chore: bump something", []) == "联邦"
