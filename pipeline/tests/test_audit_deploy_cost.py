"""audit_deploy_cost 的测试 —— 每条检查都先注入对应的坏状态,确认它会红。

一个从不报阳性的检查,它的阴性没有信息量（08-25 Gary 那条:「没有先验证一个
检查能报出阳性,就不该信它的阴性」）。D3 尤其:它的第一版在真实仓库上报
「无问题」,而 modelbooks 就在那儿——粒度不对时,被测的东西在物理上看不见。
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pipeline.tools import audit_deploy_cost as adc


GATE_SCRIPT = """#!/usr/bin/env bash
set -u
WATCH=(frontend data/output vercel.json)
if ! git rev-parse --verify HEAD^ >/dev/null 2>&1; then exit 1; fi
if git diff --quiet HEAD^ HEAD -- "${WATCH[@]}"; then exit 0; fi
exit 1
"""

VERCEL_JSON = {
    "buildCommand": "cp -r data/output frontend/public/data/output && cd frontend && npm run build",
    "outputDirectory": "frontend/dist",
    "ignoreCommand": "bash scripts/vercel_ignore_build.sh",
}


def _run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    (r / "scripts").mkdir(parents=True)
    (r / "data" / "output").mkdir(parents=True)
    (r / "frontend" / "public" / "fonts").mkdir(parents=True)

    (r / "vercel.json").write_text(json.dumps(VERCEL_JSON, indent=2))
    (r / "scripts" / "vercel_ignore_build.sh").write_text(GATE_SCRIPT)
    (r / "data" / "output" / "a.json").write_text("x" * 2048)
    (r / "frontend" / "public" / "fonts" / "f.woff").write_text("y" * 1024)

    _run(r, "init", "-q", "-b", "main")
    _run(r, "config", "user.email", "t@example.com")
    _run(r, "config", "user.name", "t")
    _run(r, "add", "-A")
    _run(r, "commit", "-qm", "init")
    # audit 读的是 origin/main;本地造一个同名 ref
    _run(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    return r


def test_clean_repo_has_no_violations(repo: Path) -> None:
    res = adc.audit(repo, days=7, budget_gb=100.0)
    assert res["violations"] == 0, res["findings"]
    assert res["gate"]["configured"] is True
    assert res["gate"]["watched"] == ["frontend", "data/output", "vercel.json"]


def test_missing_ignore_command_is_a_violation(repo: Path) -> None:
    """阳性对照 D1a:把闸拿掉,必须红。"""
    vj = json.loads((repo / "vercel.json").read_text())
    del vj["ignoreCommand"]
    (repo / "vercel.json").write_text(json.dumps(vj))
    res = adc.audit(repo, days=7, budget_gb=100.0)
    codes = [f["code"] for f in res["findings"]]
    assert "D1a" in codes
    assert res["violations"] >= 1


def test_missing_gate_script_is_a_violation(repo: Path) -> None:
    """阳性对照 D1b:vercel.json 指着一个不存在的脚本 —— Vercel 会当它失败并照常构建。"""
    (repo / "scripts" / "vercel_ignore_build.sh").unlink()
    res = adc.audit(repo, days=7, budget_gb=100.0)
    assert "D1b" in [f["code"] for f in res["findings"]]


def test_source_outside_the_gate_is_a_violation(repo: Path) -> None:
    """阳性对照 D1d:产物多了一个来源,而闸不看它 —— 它变了线上不会更新。

    这是最隐蔽的一种坏:部署照跑、构建照绿,只有内容悄悄停在旧版。
    """
    body = (repo / "scripts" / "vercel_ignore_build.sh").read_text()
    (repo / "scripts" / "vercel_ignore_build.sh").write_text(
        body.replace("WATCH=(frontend data/output vercel.json)", "WATCH=(frontend vercel.json)")
    )
    res = adc.audit(repo, days=7, budget_gb=100.0)
    d1d = [f for f in res["findings"] if f["code"] == "D1d"]
    assert d1d, res["findings"]
    assert d1d[0]["detail"]["path"] == "data/output"


def test_over_budget_is_a_violation(repo: Path) -> None:
    """阳性对照 D2:预算压到 0,必须红（且理由里带得出三个乘数）。"""
    res = adc.audit(repo, days=7, budget_gb=0.0)
    d2 = [f for f in res["findings"] if f["code"] == "D2"]
    assert d2
    assert "projected_gb" in d2[0]["detail"]


def test_stale_shipped_is_found_below_the_top_level(repo: Path, monkeypatch) -> None:
    """阳性对照 D3 + 回归:陈旧的大块在**子目录**里,父目录天天在变。

    这正是第一版漏掉 modelbooks 的形状 —— 父目录 mtime 新,子树 5 个月没动。
    """
    monkeypatch.setattr(adc, "STALE_MIN_MB", 0.001)
    monkeypatch.setattr(adc, "STALE_DAYS", 30)

    big = repo / "frontend" / "public" / "data" / "modelbooks"
    big.mkdir(parents=True)
    (big / "old.json").write_text("z" * 4096)
    _run(repo, "add", "-A")
    # 用一个 5 个月前的提交时间,让这个子树"陈旧"
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-qm", "old data"],
        check=True, capture_output=True,
        env={"GIT_AUTHOR_DATE": "2026-04-01T00:00:00", "GIT_COMMITTER_DATE": "2026-04-01T00:00:00",
             "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(repo)},
    )
    # 父目录里再放一个今天刚变的小文件 —— 它会把父目录的年龄"洗新"
    (repo / "frontend" / "public" / "data" / "fresh.json").write_text("{}")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "fresh today")
    _run(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    res = adc.audit(repo, days=7, budget_gb=100.0)
    d3 = [f for f in res["findings"] if f["code"] == "D3"]
    assert d3, "父目录是新的,但陈旧的子树必须被钻出来"
    assert d3[0]["detail"]["path"].endswith("modelbooks")


def test_deploy_rate_replays_the_gate(repo: Path) -> None:
    """构建/跳过的计数必须真的按闸的规则走,不是把 commit 数抄一遍。"""
    (repo / "notes.md").write_text("docs only")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "docs")
    (repo / "frontend" / "app.js").write_text("code")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "frontend change")
    _run(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    res = adc.audit(repo, days=7, budget_gb=100.0)
    r = res["deploy_rate"]
    assert r["commits"] == 3
    # init 是根 commit,拿不到父 —— 闸兜底构建,回放也必须这么算
    assert r["would_build"] == 2      # init（无父,兜底构建）+ frontend change
    assert r["would_skip"] == 1       # 纯 docs


def test_stale_checkout_is_flagged(repo: Path) -> None:
    """阳性对照 D0:检出的树落后 origin/main 时必须说清楚。

    否则在共享主树(常年落后一百多个 commit)上跑,会读到旧 vercel.json 并
    报「没有 ignoreCommand」——闸其实已经在 main 上了。真实发生过。
    """
    _run(repo, "checkout", "-q", "-b", "side", "HEAD~0")
    (repo / "later.md").write_text("main moved on")
    _run(repo, "add", "-A")
    _run(repo, "commit", "-qm", "main moves ahead")
    _run(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _run(repo, "reset", "-q", "--hard", "HEAD~1")

    res = adc.audit(repo, days=7, budget_gb=100.0)
    assert res["head_behind_main"] == 1
    assert "D0" in [f["code"] for f in res["findings"]]


def test_fresh_checkout_is_not_flagged(repo: Path) -> None:
    """反向对照:树和 main 一致时不许报 D0（否则这条警告会变成常年噪音）。"""
    res = adc.audit(repo, days=7, budget_gb=100.0)
    assert res["head_behind_main"] == 0
    assert "D0" not in [f["code"] for f in res["findings"]]
