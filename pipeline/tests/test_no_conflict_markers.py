"""仓库里不许留 git 冲突标记。

2026-09-10 实测：`Fluxus_Brand/ops/material_inbox.md` 在 origin/main 上带着
`<<<<<<< HEAD` / `=======` / `>>>>>>> 1de511a7` 三行，从 2026-09-09 的
commit `986bb7a4` 起就在那里，没有任何检查报过它。

**为什么三道自检全放过它**：本仓治公箱的那条自检是
`git diff origin/main -- <file> | grep '^-'`（追加时不许有删除行）——
它量的是**删除**。冲突标记是**纯新增**，在那把尺子下长得和正常追加一模一样。
一把只朝一个方向看的尺子，对另一个方向永远是绿的。

（这次没丢内容：冲突块的 theirs 侧是空的，三条素材都在。
但同一个形状下一次可能吞掉真内容，而删除自检只在**你自己这次**的 diff 里报警——
标记一旦进了 main，后面所有人的 diff 都以它为基线，就再也不报了。）
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# `=======` 单独一行在 markdown 里是合法的 setext 二级标题下划线，
# 所以它只在与另外两个标记同现时才算数 —— 判据是 <<<<<<< 和 >>>>>>>。
MARKER = re.compile(r"^(<{7} |>{7} |<{7}$|>{7}$)", re.MULTILINE)

SKIP_DIR_PARTS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", "coverage",
}
# 本文件自己要写出这些标记来解释它们，所以自己豁免自己。
SELF = Path(__file__).resolve()

TEXT_SUFFIXES = {
    ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".jsonl",
    ".yml", ".yaml", ".css", ".html", ".txt", ".csv", ".sh",
}


def _candidate_files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.resolve() == SELF:
            continue
        if p.suffix not in TEXT_SUFFIXES:
            continue
        if SKIP_DIR_PARTS & set(p.relative_to(ROOT).parts):
            continue
        yield p


def _offenders():
    out = []
    for p in _candidate_files():
        try:
            body = p.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            continue
        m = MARKER.search(body)
        if m:
            line_no = body[: m.start()].count("\n") + 1
            out.append(f"{p.relative_to(ROOT)}:{line_no}: {m.group(0).strip()}")
    return out


def test_no_git_conflict_markers_anywhere():
    offenders = _offenders()
    assert not offenders, (
        "下面这些文件里留着 git 冲突标记（合并没化解干净就 commit 了）：\n  "
        + "\n  ".join(offenders)
        + "\n\n化解掉再提交。⚠️ 公箱（material_inbox / INBOX / DATA_CONTRACTS §七）"
        "尤其要人工确认冲突两侧的内容都还在——两侧都是别人的追加。"
    )


def test_the_detector_can_report_a_positive(tmp_path):
    """先证明它能报出阳性：真造一个带标记的文件，它必须点出来。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("m", SELF)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    bogus = tmp_path / "victim.md"
    bogus.write_text(
        "正常一行\n<<<<<<< HEAD\n我的\n=======\n别人的\n>>>>>>> abc1234 (msg)\n",
        encoding="utf-8",
    )
    m.ROOT = tmp_path
    m.SELF = bogus.parent / "not-this-one"
    found = m._offenders()
    assert len(found) == 1 and "victim.md:2" in found[0], found

    # 阴性对照：markdown 的 setext 标题下划线（一行 `=======`）不许被误报
    ok = tmp_path / "innocent.md"
    ok.write_text("标题\n=======\n\n正文\n", encoding="utf-8")
    bogus.unlink()
    assert m._offenders() == []
