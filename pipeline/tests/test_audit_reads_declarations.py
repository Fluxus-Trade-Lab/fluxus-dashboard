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
