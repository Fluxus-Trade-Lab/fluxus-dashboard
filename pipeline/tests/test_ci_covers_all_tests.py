"""CI 的 pytest 采集集合，必须覆盖仓库里的每一个测试文件。

2026-09-02 我（夜间组）交出了一份「1,302 条测试没有任何自动触发点」的交接包，
里面附了可直接 copy 的 `.github/workflows/tests.yml`，那句命令写的是
`python -m pytest pipeline/tests`。接的人照抄了，CI 从此是绿的。

2026-09-10 实测：仓库根还有一棵 `tests/`，**53 个文件 / 607 个 test 函数，CI 一次都没跑过**
（占全仓 test 函数的 27.7%）。里面 `tests/test_no_naive_clock.py` 已经红了两周没人看见。

判据没错，**枚举的集合把它排除在外**——而那个集合是我 09-02 数出来、又原样交出去的：
我数了 `pipeline/tests`，于是我交出的闸也只盖 `pipeline/tests`。
同形状第 3 次（09-02 CI 接线 / 09-09 audit_stranded 看不见没推过的分支 / 本条），
按三次律②升级为机制，不再记 memory。

这道闸是**棘轮**，不是「一次性把 CI 改宽」：
  1. 任何**新增**的测试文件若落在 CI 采集不到的地方 → 红；
  2. 已知欠账（`UNCOVERED_DEBT`）只许变小，不许变大。
两条合起来的意思是：欠账可以存在，但**不能再长**，而且每次跑测试都会把它念出来。

修法二选一：把该路径加进 `.github/workflows/tests.yml` 的 pytest 参数（首选），
或把它登记进下面的欠账表并写清理由。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"

# 目录级欠账登记：CI 现在采集不到、且已知的测试树。
# 值 = 为什么它还没被纳入（不是「豁免」，是「还没修」）。
UNCOVERED_DEBT = {
    "tests": (
        "仓库根的第二棵测试树。2026-09-02 的 CI 交接包只数了 pipeline/tests，"
        "于是 tests/ 从来没进过 CI 的 pytest 参数。纳入前要先解决 tests/gex/ 的 "
        "ib_async 可选依赖（fix/fbclock-rebased-2026-09-10 已修）与 jinja2 安装。"
    ),
}

# 登记当日（2026-09-10）实测的欠账文件数。只许降不许升。
UNCOVERED_DEBT_MAX = 53

# 不算测试树的地方：第三方、构建产物、前端自己的测试跑在 vitest 下。
SKIP_DIR_PARTS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", "frontend",
}


def _pytest_target_paths() -> list[str]:
    """从 tests.yml 里取出 `python -m pytest` 真正采集的路径参数。

    本仓已有的约定（见 tests.yml 头部注释与 audit_wiring._run_blocks）：
    YAML 解析器不在 pipeline/requirements.txt 里，本机常常没有，
    所以这里也走**正则**，不 import yaml —— 本机与 CI 跑的是同一条路径。
    """
    text = WORKFLOW.read_text(encoding="utf-8")
    targets: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if "pytest" not in stripped or stripped.startswith("#"):
            continue
        if not re.search(r"(python\s+-m\s+pytest|(?<![\w/-])pytest)\b", stripped):
            continue
        # 命令行里剩下的、不是 flag 也不是 flag 的值、且在仓库里存在的 token
        tokens = stripped.split()
        skip_next = False
        for tok in tokens:
            if skip_next:
                skip_next = False
                continue
            if tok.startswith("-"):
                # `-m "not slow"` 这类：值跟在后面
                if tok in {"-m", "-k", "-p", "--tb", "--deselect", "--ignore"}:
                    skip_next = True
                continue
            if tok in {"python", "python3", "-m", "pytest", "run:", "|"}:
                continue
            if (ROOT / tok).exists():
                targets.append(tok.rstrip("/"))
    return targets


_TEST_FUNC = re.compile(r"^\s*(?:async\s+)?def\s+test_", re.MULTILINE)


def _all_test_files() -> list[Path]:
    """真正会被 pytest 收集到用例的文件。

    ⚠️ 按文件名数会多算：`scripts/test_conditional_claim.py` 是个
    「test a claim」的 CLI 工具，名字以 test_ 开头但一个用例都没有
    （实测 `pytest scripts/test_conditional_claim.py` → no tests ran）。
    所以判据是**文件里有没有 test 函数**，不是文件叫什么。
    """
    out = []
    for p in ROOT.rglob("test_*.py"):
        if SKIP_DIR_PARTS & set(p.relative_to(ROOT).parts):
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not _TEST_FUNC.search(body):
            continue
        out.append(p)
    return sorted(out)


def _uncovered() -> list[str]:
    targets = _pytest_target_paths()
    assert targets, (
        f"没能从 {WORKFLOW} 里解析出任何 pytest 采集路径。"
        "\n⚠️ 解析不到时这道闸会把「全都没覆盖」当成结论——所以这里直接红，"
        "而不是安静地报一个假的 0。"
    )
    rel_targets = [Path(t) for t in targets]
    uncovered = []
    for f in _all_test_files():
        rel = f.relative_to(ROOT)
        if any(rel == t or t in rel.parents for t in rel_targets):
            continue
        uncovered.append(str(rel))
    return uncovered


def test_ci_pytest_targets_are_parseable():
    """先证明这把尺子读得到东西——读不到的话，下面两条断言的绿是假的。"""
    targets = _pytest_target_paths()
    assert "pipeline/tests" in targets, (
        f"解析出的采集路径是 {targets}，里面没有 pipeline/tests。"
        "要么 tests.yml 改了写法、要么这个解析器坏了。"
    )


def test_no_new_test_file_outside_ci_collection():
    """棘轮①：新增的测试文件不许落在 CI 采集不到的地方。"""
    stray = [
        u for u in _uncovered()
        if not any(u == d or u.startswith(d + "/") for d in UNCOVERED_DEBT)
    ]
    assert not stray, (
        "下面这些测试文件 CI 一次都不会跑到：\n  "
        + "\n  ".join(stray)
        + "\n\n二选一：①把它的路径加进 .github/workflows/tests.yml 的 pytest 参数（首选）；"
        "\n②登记进 pipeline/tests/test_ci_covers_all_tests.py 的 UNCOVERED_DEBT 并写清为什么还没修。"
    )


def test_uncovered_debt_does_not_grow():
    """棘轮②：已登记的欠账只许变小。"""
    uncovered = _uncovered()
    assert len(uncovered) <= UNCOVERED_DEBT_MAX, (
        f"CI 采集不到的测试文件从 {UNCOVERED_DEBT_MAX} 涨到了 {len(uncovered)}。"
        "\n欠账可以存在，但不能再长。\n  " + "\n  ".join(uncovered)
    )


def test_debt_is_reported_out_loud(capsys):
    """欠账每次跑测试都要被念出来——一个没人看见的欠账等于没有。"""
    uncovered = _uncovered()
    if uncovered:
        dirs = sorted({u.split("/")[0] for u in uncovered})
        print(
            f"\n[CI 采集缺口] {len(uncovered)} 个测试文件不在 CI 的 pytest 参数里，"
            f"分布在：{', '.join(dirs)}"
        )
    captured = capsys.readouterr().out
    if uncovered:
        assert "CI 采集缺口" in captured
    else:
        assert not uncovered
