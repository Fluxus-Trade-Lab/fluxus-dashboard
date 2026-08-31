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
    """`verdict(adr)` 里有 Zac 的关键词 adr，但它动的是宪法与公箱——路径说了算。

    行里没有箭头时两种语义应当同答：欠这件事的和做这件事的都是 OPS。
    （08-31 拆分前这条用的是两用的 `lane_for`。）"""
    s, p = "verdict(adr): Andy 拍板 ADR>=3.5 闸保留", ["CLAUDE.md"]
    assert board["lane_owed_to"](s, p) == "OPS Fable"
    assert board["lane_authored_by"](s, p) == "OPS Fable"


def test_unattributable_falls_through_to_the_federation(board):
    """路径、箭头、关键词全落空 -> 「联邦」，两种语义都一样。"""
    assert board["lane_owed_to"]("chore: bump something", []) == "联邦"
    assert board["lane_authored_by"]("chore: bump something", []) == "联邦"


# ---------- 「等你拍板」不许印假零 ----------
# 08-28 实测：控制台首页印着「现在没有等你的事」，而增长台账里 T1（Andy 原话
# 「这个是要处理的，提醒我」）、T5、T3 三条都还挂着 `status: 待办`。
# 那一列的全部价值就是「⚠️ 要 Andy 决定的事置顶拉响」——印零等于把它们藏起来。
# 这条是**跨源对照**：看板算不出台账的状态，台账也不知道看板存在，谁也骗不了谁。

def _run_board(tmp_path):
    """整脚本跑一次，返回 cards（约 5 秒，含真 git 调用）。"""
    import runpy
    old_argv = sys.argv
    sys.argv = ["federation_board.py", ROOT, str(tmp_path / "board.html")]
    try:
        return runpy.run_path(SCRIPT)["cards"]
    finally:
        sys.argv = old_argv


def _ledger_open_todos():
    """直接读增长台账最新一份的「⏳ 待办」节，数还挂着 status: 待办 的条目。"""
    import re
    import subprocess
    ls = subprocess.run(
        ["git", "-C", ROOT, "ls-tree", "-r", "--name-only", "origin/main", "data/growth/weekly/"],
        capture_output=True, text=True).stdout
    files = sorted(re.findall(r"weekly/(\S+\.md)", ls))
    if not files:
        return 0
    md = subprocess.run(
        ["git", "-C", ROOT, "show", "origin/main:data/growth/weekly/" + files[-1]],
        capture_output=True, text=True).stdout
    sec = re.search(r"^## [^\n]*⏳ 待办[^\n]*\n(.*?)(\n## |\Z)", md, re.S | re.M)
    if not sec:
        return 0
    n = 0
    for blk in re.split(r"\n### ", sec.group(1))[1:]:
        title = blk.splitlines()[0]
        if "~~" in title or "✅" in title:
            continue
        if re.search(r"status: *待办", blk[:400]):
            n += 1
    return n


@pytest.mark.slow
def test_the_waiting_on_andy_column_is_not_a_false_zero(tmp_path):
    """台账里还有 status: 待办 → 看板「等你拍板」必须非空。

    这是条**条件不变式**，不是钉死的期望值：Andy 全清完了，前置条件自然消失，测试转为跳过。
    阳性对照：把 `andy_todos(...)` 与增长台账那两个数据源删掉（= 08-28 之前的状态），本条报红。
    """
    open_todos = _ledger_open_todos()
    if open_todos == 0:
        pytest.skip("增长台账当前没有 status: 待办 的条目，前置条件不成立")
    blocked = [c for c in _run_board(tmp_path) if c["col"] == "blocked"]
    assert blocked, (
        "增长台账有 %d 条 status: 待办，而看板「等你拍板」是空的——"
        "这正是 08-28 查出的假零" % open_todos
    )


@pytest.mark.slow
def test_the_same_todo_registered_twice_shows_once(tmp_path):
    """同一件事在 INBOX 与增长台账各登记一次时，只出一张卡。"""
    blocked = [c for c in _run_board(tmp_path) if c["col"] == "blocked"]
    import re
    sigs = [re.sub(r"[^0-9A-Za-z一-鿿]", "", c["t"]) for c in blocked]
    for i, a in enumerate(sigs):
        for b in sigs[i + 1:]:
            common = any(a[k:k + 12] in b for k in range(max(0, len(a) - 11)))
            assert not common, "两张 blocked 卡说的是同一件事：\n  %s\n  %s" % (a[:40], b[:40])


# ---------- 「线」的两种语义（Andy 08-31 裁决）----------
# 裁决原文：看板上「线」的意思是**「谁欠这件事、谁该动手」**（收件人语义），
# **不是**「谁做了这件事」（作者语义）。
#
# 此前一个 `lane_for(text, paths)` 被两边共用——`done`/`doing` 列问「谁提交的」，
# `claim`/`blocked` 列问「谁该动手」。两名独立盲判 agent 的 7 处分歧全落在这里；
# Zac 08-28 原话：「没定义之前这部分准确率量不出来，不是量不出，是题目没答案。」
#
# ⚠️ 阳性对照（逐条注射实测过，别删这段）：
#
# | 注射 | 报红的用例 |
# |---|---|
# | ① `lane_authored_by` 改回「路径 > 箭头 > 关键词」（= 旧 lane_for） | 2 红：`…author_ignores_the_arrow`、`…two_functions_disagree…` |
# | ② `lane_owed_to` 把箭头降到路径之后 | 1 红：`…arrow_outranks_the_file_boundary` |
# | ③ 任一 `add()` 调用点把两个函数对调 | 1 红：`…every_add_call_site_declares_its_semantics` |
# | ④ 恢复 `add(..., lane=None)` 默认值 | 1 红：`…add_forces_the_call_site_to_choose` |

# 真例 58fd7ecf（origin/main，08-28）：Joe 提交的契约行 commit，箭头指向前端。
# 改动路径只有 DATA_CONTRACTS.md —— 公箱，弃权，于是全靠文本定线。
REAL_COMMIT = ("contracts(§7): -> 前端 P/L 1D 在当天建仓的票上把建仓前跳空算成盈亏"
               "(实测虚增 43,380/千股);YTD 与权益曲线不受影响,别过度修")
REAL_PATHS = ["data/reference/DATA_CONTRACTS.md"]


def test_owed_to_takes_the_recipient_not_the_author(board):
    """① 一条挂给某线的契约行：欠这件事的是箭头后面的收件人，不是写这条行的人。"""
    assert board["lane_owed_to"](REAL_COMMIT, REAL_PATHS) == "UI Claire"


def test_owed_to_arrow_outranks_the_file_boundary(board):
    """收件人语义里箭头是**最硬**的证据，压过文件边界。

    真形状：Joe 在自己的 `incidents/` 目录里写事故档，行里写明「→ DATA ALEX」。
    文件边界说这是 Joe 的地盘（前一条断言自证），但欠着动手的是 ALEX。"""
    line = "[08-27] Plumber Joe 转投递 → DATA ALEX: universe_gated 只数到流动性闸"
    assert board["lane_of_paths"](["data/reference/incidents/x.md"]) == "Plumber Joe"
    assert board["lane_owed_to"](line, ["data/reference/incidents/x.md"]) == "DATA ALEX"


def test_author_ignores_the_arrow_recipient(board):
    """② 同一条 commit 问「谁做的」：答案是 Joe。

    旧 `lane_for` 在这里把箭头当成了归属，于是「7 天完成排行」给 UI Claire
    记了一笔她没干的活、Joe 少了一笔（实测 14 天窗口内 3 条 commit 是这个形状）。"""
    assert board["lane_authored_by"](REAL_COMMIT, REAL_PATHS) == "Plumber Joe"


def test_author_still_respects_the_file_boundary(board):
    """作者语义没有放弃路径——只是不看箭头。"""
    assert board["lane_authored_by"]("fix: 收盘后 P/L 列", ["frontend/src/a.jsx"]) == "UI Claire"


def test_the_two_functions_disagree_on_the_same_input(board):
    """③ 前半：同一条输入，两个函数必须给出**不同**的答案。

    这条是整次拆分的存在理由——若两者永远一致，拆开就只是改名。"""
    owed = board["lane_owed_to"](REAL_COMMIT, REAL_PATHS)
    author = board["lane_authored_by"](REAL_COMMIT, REAL_PATHS)
    assert owed != author, "两个函数答案相同，语义没真的分开：%s" % owed
    assert (owed, author) == ("UI Claire", "Plumber Joe")


# ---------- ③ 后半：看板各列取的是对的那个 ----------
# 这里用 AST 查**调用点**而不是跑整个脚本：那 3 条形状特殊的 commit 不一定落在
# done 列的 24h 窗口里（08-31 实跑就没落进来），拿真数据断言会得到一个
# 「今天恰好没有反例」的假绿。查调用点则永远有效，且新增 add() 也自动受管。

EXPECTED_SEMANTICS = {
    "claim": "lane_owed_to",       # 待认领 · 挂单板 —— 谁该动手
    "blocked": "lane_owed_to",     # 等 Andy 拍板 —— 谁该动手
    "done": "lane_authored_by",    # 已完成 24h —— 谁提交的
    "doing": "lane_authored_by",   # 进行中 · 今日 —— 谁提交的
}


def _add_call_sites():
    """[(行号, 列名, 传给 lane 的函数名 or None)]；线名写死成字面量的调用点 fn=None。"""
    import ast
    tree = ast.parse(open(SCRIPT, encoding="utf-8").read(), SCRIPT)
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "add"):
            continue
        col = node.args[0].value
        lane = node.args[4] if len(node.args) > 4 else None
        fn = (lane.func.id if isinstance(lane, ast.Call)
              and isinstance(lane.func, ast.Name) else None)
        out.append((node.lineno, col, fn))
    return out


def test_every_add_call_site_declares_its_semantics():
    sites = _add_call_sites()
    assert sites, "一个 add() 调用点都没找到——脚本结构变了，测试需要同步更新"
    for lineno, col, fn in sites:
        if fn is None:
            continue           # lane 写死成字面量（如 "OPS Fable"），无歧义
        assert fn == EXPECTED_SEMANTICS[col], (
            "federation_board.py:%d 的 `%s` 列用了 %s()——面向行动的列一律 lane_owed_to，"
            "只有 done/doing 才用 lane_authored_by（Andy 08-31 裁决）" % (lineno, col, fn))


def test_both_semantics_are_actually_used():
    """两个函数都得有调用点。全用一个 = 又塌回一种语义，这次拆分白做。"""
    fns = {fn for _, _, fn in _add_call_sites() if fn}
    assert fns == {"lane_owed_to", "lane_authored_by"}, fns


def test_the_ambiguous_lane_for_is_gone():
    """`lane_for` 就是被拆掉的那个两用函数。它一复活，调用点又能不选语义了。"""
    src = open(SCRIPT, encoding="utf-8").read()
    assert "def lane_for(" not in src, "两用的 lane_for 回来了——语义又混在一起了"


def test_add_forces_the_call_site_to_choose():
    """④ `add()` 的 `lane` 不许有默认值：留个兜底 = 允许调用点不表态。"""
    import ast
    tree = ast.parse(open(SCRIPT, encoding="utf-8").read(), SCRIPT)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "add")
    names = [a.arg for a in fn.args.args]
    assert "lane" in names, names
    # 默认值从右往左对齐；lane 落在有默认值的尾段里就说明它可以省略
    first_defaulted = len(names) - len(fn.args.defaults)
    assert names.index("lane") < first_defaulted, "add() 的 lane 有默认值，调用点可以不选语义"
