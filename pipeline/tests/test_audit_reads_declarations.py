"""audit_reads_declarations 的测试。

⭐ 这套测试的重点不是「工具能跑」，是**它能不能报出阳性**——
坑账 pitfall_red_for_the_wrong_reason：注射 bug 才算阳性对照，
KeyError 式全红是假的；注射了却全绿＝那条断言是装饰。
所以每个 happy path 都配一个「把它弄坏、必须变红」的孪生用例。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import audit_reads_declarations as A  # noqa: E402

CONTRACT = """# ① 信号站 · Signal Scout

**owns**：选题决策。

**reads**：
- `Fluxus_Brand/brain/signals.md`（判据）
{extra}

**returns**：1 个取用信号。

**must not**：起草内容。
"""

DECLARER = """# signals.md — 判据

> 谁读：信号站（每晚第一站）。谁写：Steve 周报回填。

正文。
"""


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "x"], cwd=root, check=True)
    return root


def _run(root: Path) -> list[A.Finding]:
    return A.audit(root, "HEAD")


# ---------- 阴性：接对了就该全绿 ----------

def test_declared_and_registered_is_clean(tmp_path):
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    assert _run(root) == []


# ---------- 阳性：注射断裂，必须变红 ----------

def test_declared_but_missing_from_reads_is_caught(tmp_path):
    """注射的 bug＝把被声明的文件从 reads 段里拿掉。这是真事故的最小复刻。"""
    contract = CONTRACT.format(extra="").replace(
        "- `Fluxus_Brand/brain/signals.md`（判据）\n", ""
    )
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": contract,
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    found = _run(root)
    assert [f.kind for f in found] == ["broken"]
    assert found[0].declarer == "Fluxus_Brand/brain/signals.md"
    assert found[0].station == "信号站"


def test_mentioned_outside_reads_is_still_broken(tmp_path):
    """⭐ 09-10 真事故的形状：契约里提到了它，但**不在 reads 段**。绿不得。"""
    contract = CONTRACT.format(extra="").replace(
        "- `Fluxus_Brand/brain/signals.md`（判据）",
        "- `Fluxus_Brand/brain/other.md`（别的）",
    ).replace("**must not**：起草内容。",
              "**must not**：起草内容；参见 `Fluxus_Brand/brain/signals.md`。")
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": contract,
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    found = _run(root)
    assert [f.kind for f in found] == ["broken"]
    assert "不在 reads 段里" in found[0].detail


def test_multi_station_declaration_checks_every_station(tmp_path):
    """「谁读：A · B」漏了 B 也要红——09-10 那 5 条全是列表里的第二个站。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra="- `Fluxus_Brand/brain/two.md`"),
        f"{A.ROLES_DIR}/05_distribution.md": (
            "# ⑤ 分发站 · Distribution\n\n**reads**：\n- `Fluxus_Brand/BRAIN.md`\n\n"
            "**returns**：变体。\n"
        ),
        "Fluxus_Brand/brain/two.md": (
            "# two\n\n> 谁读：信号站（选题）· 分发站（选型）。谁写：Steve。\n"
        ),
    })
    found = _run(root)
    assert [(f.kind, f.station) for f in found] == [("broken", "分发站")]


def test_basename_only_reference_is_weak_not_green(tmp_path):
    """reads 里只写文件名不写路径 → 同名文件会误判为已登记，标弱引用。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra="").replace(
            "- `Fluxus_Brand/brain/signals.md`（判据）", "- `signals.md`（判据）"),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    found = _run(root)
    assert [f.kind for f in found] == ["weak"]


# ---------- 边界：别把讨论这条规矩的文档当成声明 ----------

def test_prose_mention_is_not_a_declaration(tmp_path):
    """维修单里写「任何文件写了『谁读：X』…」是在讨论规矩，不是声明。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
        "Fluxus_Brand/ops/campaigns/MAINTENANCE.md": (
            "# 维修单\n\n讲的是：任何文件头部写了「谁读：信号站」，"
            "信号站的 reads 里必须出现它。\n"
        ),
    })
    assert _run(root) == []


def test_declaration_below_header_region_is_ignored(tmp_path):
    """头部之外的引用块不算声明——否则正文引用会制造假阳性。"""
    body = "# x\n\n" + "\n".join(f"第 {i} 行" for i in range(A.HEADER_LINES + 3))
    body += "\n> 谁读：信号站。\n"
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
        "Fluxus_Brand/brain/late.md": body,
    })
    assert _run(root) == []


# ---------- 站名表是现读的，不是写死的 ----------

def test_station_table_is_read_from_roles_not_hardcoded(tmp_path):
    """新加一个站，工具不改代码就该认识它（白名单量的是我的词汇量）。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        f"{A.ROLES_DIR}/09_newstation.md": (
            "# ⑨ 考古站 · Archaeology\n\n**reads**：\n- `Fluxus_Brand/BRAIN.md`\n\n"
            "**returns**：无。\n"
        ),
        "Fluxus_Brand/brain/signals.md": DECLARER,
        "Fluxus_Brand/brain/dig.md": "# dig\n\n> 谁读：考古站。谁写：无。\n",
    })
    table = A.station_contracts(root, "HEAD")
    assert table["考古站"] == f"{A.ROLES_DIR}/09_newstation.md"
    found = _run(root)
    assert [(f.kind, f.station) for f in found] == [("broken", "考古站")]


def test_unknown_station_is_uncheckable_not_silently_green(tmp_path):
    """站名对不上任何契约 → 报 uncheckable，不许静默放行。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
        "Fluxus_Brand/brain/ghost.md": "# ghost\n\n> 谁读：幽灵站。谁写：无。\n",
    })
    found = _run(root)
    assert [f.kind for f in found] == ["uncheckable"]


def test_no_roles_dir_exits_2_rather_than_reporting_clean(tmp_path):
    """⭐ 找不到契约目录时必须显式失败——否则「什么都没查」会长得和「全绿」一样
    （坑账 pitfall_a_pathspec_that_matches_nothing_looks_clean）。"""
    root = _repo(tmp_path, {"Fluxus_Brand/brain/signals.md": DECLARER})
    with pytest.raises(SystemExit) as e:
        A.audit(root, "HEAD")
    assert e.value.code == 2


def test_worktree_mode_sees_uncommitted_changes(tmp_path):
    """⭐ 只能扫已提交版本的闸，用不成提交前的闸。
    改了工作区但没 commit：HEAD 还是绿的，WORKTREE 必须已经红了。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    assert A.audit(root, "HEAD") == []
    # 在工作区里把 reads 那行删掉，不提交
    p = root / A.ROLES_DIR / "01_signal.md"
    p.write_text(p.read_text(encoding="utf-8").replace(
        "- `Fluxus_Brand/brain/signals.md`（判据）\n", ""), encoding="utf-8")
    assert A.audit(root, "HEAD") == []                     # 已提交版仍是绿的
    found = A.audit(root, A.WORKTREE)
    assert [f.kind for f in found] == ["broken"]           # 工作区已经红了


def test_worktree_mode_sees_untracked_declarer(tmp_path):
    """新加一个还没 git add 的声明文件也要被查到——否则新文件天生免检。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    (root / "Fluxus_Brand/brain/brandnew.md").write_text(
        "# new\n\n> 谁读：信号站。谁写：无。\n", encoding="utf-8")
    assert A.audit(root, "HEAD") == []
    found = A.audit(root, A.WORKTREE)
    assert [(f.kind, f.declarer) for f in found] == [
        ("broken", "Fluxus_Brand/brain/brandnew.md")]


# ---------- main()：退出码与打印出来的那一行 ----------
#
# 2026-10-03（T-1003-10）：变异扫描 34/52 = 65%，18 个存活点，其中 8 个挤在
# `main()` 的报告与退出码上——上面 12 条测试**全部只调 `audit()`**，没有一条
# 进过「把判词报出去」那条路。而人拿来行动的是退出码和打印的那一行
# （同形：09-27 audit_event_agreement、10-02 audit_tml）。

def _main(root: Path, monkeypatch, rev: str = "HEAD") -> int:
    monkeypatch.setattr(sys, "argv",
                        ["audit_reads_declarations", "--root", str(root), "--rev", rev])
    return A.main()


def _basename_only_contract() -> str:
    """reads 段只写文件名的契约 —— 命中它会判 weak，不是 clean。"""
    return CONTRACT.format(extra="").replace(
        "- `Fluxus_Brand/brain/signals.md`（判据）", "- `signals.md`（判据）")


def _sub(tmp_path: Path, name: str) -> Path:
    """_repo 自己不建父目录，所以同一个用例要开第二个仓库得先把壳建出来。"""
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_main_exits_1_on_a_broken_declaration(tmp_path, monkeypatch, capsys):
    """退出码是这道闸唯一会被别的程序读到的东西。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/other.md": DECLARER,       # 契约 reads 里没有它
    })
    assert _main(root, monkeypatch) == 1
    assert "断裂 1 条" in capsys.readouterr().out


def test_main_exits_0_when_everything_lines_up(tmp_path, monkeypatch, capsys):
    """阴性腿：没有它，上一条可以靠「永远返回 1」通过。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    assert _main(root, monkeypatch) == 0
    assert "✅" in capsys.readouterr().out


def test_weak_and_uncheckable_alone_do_not_fail_the_build(tmp_path, monkeypatch, capsys):
    """只有 broken 拦路。弱引用与查不了要报出来，但不改退出码——
    否则这道闸会因为一个站名写错而变成每晚都红。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": _basename_only_contract(),
        "Fluxus_Brand/brain/signals.md": DECLARER,
        "Fluxus_Brand/brain/ghost.md": "# g\n\n> 谁读：不存在站。\n",
    })
    assert _main(root, monkeypatch) == 0
    out = capsys.readouterr().out
    assert "弱引用 1 条" in out and "查不了 1 条" in out


def test_each_kind_is_printed_under_its_own_heading(tmp_path, monkeypatch, capsys):
    """三个分组各报各的。把分组条件取反（kind == -> !=）会把别的类塞进
    「断裂」那一节，而总数不变——所以要按节查，不能只查总数。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": _basename_only_contract(),
        "Fluxus_Brand/brain/signals.md": DECLARER,      # weak（reads 只写文件名）
        "Fluxus_Brand/x/broke.md": "# b\n\n> 谁读：信号站。\n",   # broken
        "Fluxus_Brand/brain/ghost.md": "# g\n\n> 谁读：不存在站。\n",  # uncheckable
    })
    assert _main(root, monkeypatch) == 1
    out = capsys.readouterr().out
    broke_sec = out.split("❌ 断裂")[1].split("⚠️")[0]
    weak_sec = out.split("⚠️ 弱引用")[1].split("ⓘ")[0]
    unchk_sec = out.split("ⓘ 查不了")[1].split("—" * 60)[0]
    assert "broke.md" in broke_sec and "ghost.md" not in broke_sec
    assert "signals.md" in weak_sec and "broke.md" not in weak_sec
    assert "ghost.md" in unchk_sec and "signals.md" not in unchk_sec
    assert "断裂 1 · 弱引用 1 · 查不了 1" in out


def test_empty_groups_are_skipped_not_printed_as_headings(tmp_path, monkeypatch, capsys):
    """`if not group: continue` 反过来写（只印空的、跳过有内容的）会让一道
    报了断裂的闸印出三个空标题、一条明细都没有。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/other.md": DECLARER,
    })
    _main(root, monkeypatch)
    out = capsys.readouterr().out
    assert "❌ 断裂 1 条" in out
    assert "other.md" in out                 # 明细真的印了
    assert "⚠️ 弱引用" not in out             # 空分组不占屏
    assert "ⓘ 查不了" not in out


def test_the_all_clear_line_only_prints_when_there_is_nothing(tmp_path, monkeypatch, capsys):
    """`if not total` 丢掉 not，就会在有断裂的那一夜印出「✅ 每一条都登记了」。
    一条报错的闸印出放心话，比不报还坏。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/other.md": DECLARER,
    })
    _main(root, monkeypatch)
    assert "✅" not in capsys.readouterr().out


# ---------- 判据边界：两侧各探一次 ----------

def test_header_region_boundary_is_probed_from_both_sides(tmp_path, monkeypatch):
    """HEADER_LINES=10：第 10 行的声明算，第 11 行的不算。
    只探一侧的话，把 10 改成 11 或 9 都有一半概率绿着过去。"""
    def doc(at_line: int) -> str:
        lines = ["# d", ""]
        while len(lines) < at_line - 1:
            lines.append("填充。")
        lines.append("> 谁读：信号站。")
        return "\n".join(lines) + "\n"

    assert A.HEADER_LINES == 10
    inside = _repo(_sub(tmp_path, "a"), {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/other.md": doc(10),
    })
    assert [f.kind for f in A.audit(inside, "HEAD")] == ["broken"]

    outside = _repo(_sub(tmp_path, "b"), {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/other.md": doc(11),
    })
    assert A.audit(outside, "HEAD") == []


def test_station_name_without_the_station_suffix_is_still_read(tmp_path):
    """H1 里取不到「X站」时退回取第一个中文词——2026-09-11「日推」进 roles/
    就是这一条在接。把 `or` 改成 `and` 会让这类站名全部读不出来，
    于是声明它们的文件变成「查不了」而不是被真查一遍。"""
    contract = CONTRACT.replace("# ① 信号站 · Signal Scout", "# ⑧ 日推 · Daily Push")
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/08_daily_push.md": contract.format(extra=""),
        "Fluxus_Brand/brain/signals.md": "# s\n\n> 谁读：日推。\n",
    })
    table = A.station_contracts(root, "HEAD")
    assert table.get("日推") == f"{A.ROLES_DIR}/08_daily_push.md"
    assert A.audit(root, "HEAD") == []      # reads 段里有它，所以是绿的

    broken = _repo(_sub(tmp_path, "b"), {
        f"{A.ROLES_DIR}/08_daily_push.md": contract.format(extra=""),
        "Fluxus_Brand/brain/other.md": "# o\n\n> 谁读：日推。\n",
    })
    assert [f.kind for f in A.audit(broken, "HEAD")] == ["broken"]


def test_path_forms_go_from_full_path_down_to_bare_filename():
    """三档引用写法，按强到弱。`len(parts) >= 2` 改成 `> 2` 或 `>= 3`，
    两段路径就丢掉中间那一档，于是 `brain/signals.md` 这种写法认不出来。"""
    assert A.path_forms("a/b/c.md") == ["a/b/c.md", "b/c.md", "c.md"]
    assert A.path_forms("b/c.md") == ["b/c.md", "c.md"]      # 两段：中档==全路径，去重
    assert A.path_forms("c.md") == ["c.md"]


def test_two_segment_reference_is_accepted_as_a_real_path(tmp_path):
    """`brain/signals.md` 这种后两段写法算登记过，不算弱引用——
    弱引用只给**光写文件名**的那种留。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(
            extra="").replace("`Fluxus_Brand/brain/signals.md`（判据）",
                              "`brain/signals.md`（后两段）"),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    assert A.audit(root, "HEAD") == []


def test_basename_hit_on_a_single_segment_declarer_is_not_weak(tmp_path):
    """`hit != declarer and hit == basename` 的 `and` 改成 `or`，
    会把「全路径就是文件名」的根目录声明也判成弱引用——那是误报。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(
            extra="").replace("`Fluxus_Brand/brain/signals.md`（判据）",
                              "`ROOT.md`（根目录文件）"),
        "ROOT.md": DECLARER,
    })
    assert A.audit(root, "HEAD") == []


def test_worktree_listing_takes_md_files_only_and_only_real_files(tmp_path):
    """WORKTREE 模式的 `endswith('.md') and is_file()` 两个条件都要在：
    改成 `or` 会把一个叫 `x.md` 的**目录**和所有非 md 文件一起收进来。"""
    root = _repo(tmp_path, {
        f"{A.ROLES_DIR}/01_signal.md": CONTRACT.format(extra=""),
        "Fluxus_Brand/brain/signals.md": DECLARER,
    })
    (root / "notes.md.d").mkdir()                              # 目录，名字不以 .md 结尾
    (root / "decoy.md").mkdir()                                # 目录，名字以 .md 结尾
    (root / "decoy.md" / "inner.txt").write_text("x", encoding="utf-8")
    (root / "plain.txt").write_text("> 谁读：信号站。\n", encoding="utf-8")

    listed = A._git_ls(root, A.WORKTREE)
    assert "decoy.md" not in listed          # 目录不是文件
    assert "plain.txt" not in listed         # 不是 .md
    assert "Fluxus_Brand/brain/signals.md" in listed
    assert A.audit(root, A.WORKTREE) == []   # plain.txt 的那句声明不该被查
