# 专职编队 v2（本机常驻编排器）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 8 个专职 agent 从「要人打开的聊天会话」改成「私有仓库里的目录 + 本机守护进程按需起的一次性 `claude -p` 工人」，agent 之间只经任务板交接，Andy 只做花钱、对外发布和一个字的裁决。

**Architecture:** 新建私有仓库 `fluxus-ops`（任务板、agent 目录、时刻表、账本、心跳），纯标准库 Python 工具；守护进程由 launchd 常驻，每 60 秒拉任务板、按时刻表投任务、起工人、记账；工人流程固定（领取 → 临时工作树 → 测试 → 按 gate 过审核子 agent → 合并或留分支 → 写回状态）；每日页由本机 App 定时任务读任务板生成。代码仓库 `fluxus-dashboard` 只增 skill 壳、改 CLAUDE.md、退役旧机制。

**Tech Stack:** Python 3.14 标准库（`json`、`subprocess`、`argparse`、`dataclasses`、`datetime`、`zoneinfo`、`threading`、`pytest`）· git · `claude` CLI 2.1.260（`-p --output-format json --model --permission-mode --allowedTools --disallowedTools --max-turns`）· macOS launchd · `gh` CLI（已登录 org `Fluxus-Trade-Lab`）

**Spec:** `docs/superpowers/specs/2026-09-18-agent-fleet-v2-design.md`（186604a4，Andy 2026-09-18 批「可以，我直接批了。」）

## Global Constraints

- 私有仓库路径固定 `~/Documents/fluxus-ops/`；代码仓库 `~/Documents/AI-Trading-System`（远端 `Fluxus-Trade-Lab/fluxus-dashboard`，公开）。
- fluxus-ops 只用 Python 标准库，无第三方依赖。**与 spec 的一处偏差**：spec 写 `config.yml` / `schedule.yml`，本计划用 `config.json` / `schedule.json`，理由是标准库无 YAML 解析器；字段一致。
- 八个 agent 名：`alex claire linda q mia vera steve gary`，外加 `ops`。
- 状态机：`open → claimed → done / needs_andy / blocked / closed`；claimed 超 3 小时回收；attempts ≥ 2 → blocked。
- gate 路径规则（spec §8）：andy > reviewer > none。andy：花钱、对外发布、删数据（`data/` 下的删除）、会员相关目录；reviewer：`.github/workflows/`、`frontend/`、`pipeline/screeners|tickers|adapters/`、任何 `ROLE.md`、`.claude/skills/`、`CLAUDE.md`；其余 none。
- 并发：全局 ≤ 3 工人，每 agent ≤ 1，有 P0 open 时不起 P2。工人时长上限 45 分钟。
- 模型：判断型 `claude-opus-5`，执行型 `claude-sonnet-5`，机械型 `claude-haiku-4-5-20251001`，审 Opus 产出的审核员 `claude-fable-5-1`。Sonnet 当量：opus ×5、fable ×5、sonnet ×1、haiku ×0.3。水位线 80% / 95%。周预算初值 **20,000,000 Sonnet 当量 token**（假设值，第一周实测后改，见 Task 14）。
- ROLE.md ≤ 120 行，工具超限拒合。CLAUDE.md 目标 ≤ 40 行。
- 时间戳一律 ISO 8601 带时区（`2026-09-18T14:06:32+09:00`）。
- 任何写入 fluxus-ops 的提交都推到远端 `origin/main`；push 被拒即视为并发失败（这是任务板的锁）。
- 工人在代码仓库里的所有改动走临时工作树，永不在共享主树 commit。
- 禁止清单（工人 `--disallowedTools`）：`Bash(rm -rf*)`、`Bash(git push --force*)`、`Bash(git reset --hard*)`（工作树内除外，由 prompt 约束）、`Bash(vercel*)`、`Bash(gh release*)`、`WebFetch`、`mcp__*send*`、`mcp__*trash*`、`mcp__*delete*`；任何往代码仓库写会员个人信息的操作由 gate=andy 兜底。
- 测试：fluxus-ops 用 `python3 -m pytest -q tests/`；代码仓库两个根 `pipeline/tests` 与 `tests`。

---

## File Structure

**新仓库 `~/Documents/fluxus-ops/`**

```
tools/
  taskfile.py        任务文件的读写与校验（front matter + 正文），无 git
  gitops.py          fetch/reset/commit/push 与「带重试的原子改动」
  taskboard.py       CLI：new list claim done needs-andy block close handoff reap review gate
  gate.py            按改动路径判 none/reviewer/andy
  ledger.py          token 账本、Sonnet 当量、周用量、水位档
  cronmatch.py       5 字段 cron 匹配（标准库实现）
  worker.py          组工人 prompt、起 claude -p、超时、解析 JSON
  daemon.py          主循环：pull → 时刻表 → reap → 挑任务 → 起工人 → 记账 → 心跳
  dailypage.py       从任务板/心跳/账本/项目生成每日页数据
  metrics.py         第一周三个数
  rolecheck.py       ROLE.md ≤120 行校验
agents/<name>/       ROLE.md config.json memory/ runs/
agents/_worker_protocol.md   工人流程（塞进每个工人的 prompt）
tasks/               任务板
projects/            项目层
schedule.json        时刻表
config/budget.json   周预算与水位线
ledger/              YYYY-Www.jsonl
state/               heartbeat.json、schedule_last.json、daemon.lock
launchd/com.fluxus.ops-daemon.plist
tests/               每个 tools/*.py 一份测试
```

**代码仓库 `~/Documents/AI-Trading-System`**

```
FLUXUS_OPS.md                         一行指针
.claude/skills/<9 个新壳>/SKILL.md    Task 6
CLAUDE.md                             Task 13 重写
pipeline/tools/doorbells.py           Task 13 删除
pipeline/tools/federation_board.py    Task 13 删除
```

---

### Task 1: 建私有仓库与任务文件读写

**Files:**
- Create: `~/Documents/fluxus-ops/tools/__init__.py`（空）
- Create: `~/Documents/fluxus-ops/tools/taskfile.py`
- Create: `~/Documents/fluxus-ops/tests/test_taskfile.py`
- Create: `~/Documents/fluxus-ops/.gitignore`（`state/daemon.lock`、`__pycache__/`、`.pytest_cache/`）
- Create: `~/Documents/AI-Trading-System/FLUXUS_OPS.md`

**Interfaces:**
- Produces: `taskfile.Task`（`meta: dict[str,str]`，`body: str`，`path: Path|None`）；`parse(text) -> Task`；`dump(task) -> str`；`load(path) -> Task`；`save(task)`；`validate(task) -> list[str]`；`acceptance(task) -> list[tuple[bool,str]]`；常量 `OWNERS`、`STATUSES`、`PRIORITIES`、`GATES`、`RUNTIMES`。

- [ ] **Step 1: 建仓库**

```bash
mkdir -p ~/Documents/fluxus-ops && cd ~/Documents/fluxus-ops
git init -q -b main
mkdir -p tools tests agents tasks projects ledger state config launchd
touch tools/__init__.py tests/__init__.py
printf 'state/daemon.lock\n__pycache__/\n.pytest_cache/\n' > .gitignore
gh repo create Fluxus-Trade-Lab/fluxus-ops --private --source=. --remote=origin --description "Fluxus 专职编队：任务板 / agent 目录 / 守护进程"
```

预期：`gh repo view Fluxus-Trade-Lab/fluxus-ops --json visibility` 打印 `"PRIVATE"`。

- [ ] **Step 2: 写失败测试**

```python
# tests/test_taskfile.py
import pathlib, pytest
from tools import taskfile as tf

SAMPLE = """---
id: T-0918-03
title: 五张筛子单加 $1B 市值闸
owner: alex
type: data_fix
project: dashboard
status: open
priority: P1
gate: none
runtime: local
created_by: linda
created_at: 2026-09-18T05:41:00+09:00
claimed_at:
closed_at:
attempts: 0
result:
andy: 「哦市值这个闸是要加上的。」
review:
---
## 要做什么
gainers_4pct 等五张单加 ≥$1B 市值闸。

## 验收
- [ ] 断点后样本里 <$1B 占比为 0，附一条能报红的测试
- [x] 全套测试通过
"""

def test_parse_roundtrip():
    t = tf.parse(SAMPLE)
    assert t.meta["id"] == "T-0918-03"
    assert t.meta["owner"] == "alex"
    assert t.meta["claimed_at"] == ""
    assert tf.dump(t) == SAMPLE

def test_acceptance_items():
    t = tf.parse(SAMPLE)
    assert tf.acceptance(t) == [(False, "断点后样本里 <$1B 占比为 0，附一条能报红的测试"), (True, "全套测试通过")]

def test_validate_rejects_bad_values():
    t = tf.parse(SAMPLE)
    t.meta["owner"] = "joe"
    t.meta["status"] = "pending"
    t.meta["priority"] = "P9"
    errs = tf.validate(t)
    assert any("owner" in e for e in errs)
    assert any("status" in e for e in errs)
    assert any("priority" in e for e in errs)

def test_validate_requires_every_field():
    t = tf.parse(SAMPLE)
    del t.meta["gate"]
    assert any("gate" in e for e in tf.validate(t))

def test_parse_rejects_missing_frontmatter():
    with pytest.raises(ValueError):
        tf.parse("no front matter here")

def test_save_and_load(tmp_path):
    t = tf.parse(SAMPLE)
    p = tmp_path / "T-0918-03.md"
    t.path = p
    tf.save(t)
    assert tf.load(p).meta == t.meta
```

- [ ] **Step 3: 跑测试确认失败**

Run: `cd ~/Documents/fluxus-ops && python3 -m pytest -q tests/test_taskfile.py`
Expected: FAIL，`ModuleNotFoundError: No module named 'tools.taskfile'`

- [ ] **Step 4: 实现 taskfile.py**

```python
# tools/taskfile.py
"""任务文件 = '---' 包住的 key: value 头 + Markdown 正文。只做读写与校验，不碰 git。"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path

FIELDS = ["id", "title", "owner", "type", "project", "status", "priority", "gate", "runtime",
          "created_by", "created_at", "claimed_at", "closed_at", "attempts", "result", "andy", "review"]
OWNERS = {"alex", "claire", "linda", "q", "mia", "vera", "steve", "gary", "ops"}
STATUSES = ["open", "claimed", "done", "needs_andy", "blocked", "closed"]
PRIORITIES = ["P0", "P1", "P2"]
GATES = ["none", "reviewer", "andy"]
RUNTIMES = ["local", "app"]
_CHECK = re.compile(r"^- \[( |x)\] (.*)$")


@dataclass
class Task:
    meta: dict[str, str]
    body: str
    path: Path | None = None


def parse(text: str) -> Task:
    if not text.startswith("---\n"):
        raise ValueError("task file must start with '---'")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated front matter")
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip()
    return Task(meta=meta, body=text[end + 5:])


def dump(task: Task) -> str:
    head = "\n".join(f"{k}: {task.meta.get(k, '')}".rstrip() for k in FIELDS)
    return f"---\n{head}\n---\n{task.body}"


def load(path: Path) -> Task:
    t = parse(Path(path).read_text(encoding="utf-8"))
    t.path = Path(path)
    return t


def save(task: Task) -> None:
    if task.path is None:
        raise ValueError("task.path is not set")
    task.path.write_text(dump(task), encoding="utf-8")


def acceptance(task: Task) -> list[tuple[bool, str]]:
    out = []
    in_section = False
    for line in task.body.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## 验收"
            continue
        m = _CHECK.match(line)
        if in_section and m:
            out.append((m.group(1) == "x", m.group(2)))
    return out


def validate(task: Task) -> list[str]:
    errs = []
    for k in FIELDS:
        if k not in task.meta:
            errs.append(f"missing field: {k}")
    m = task.meta
    if m.get("owner") not in OWNERS:
        errs.append(f"owner must be one of {sorted(OWNERS)}, got {m.get('owner')!r}")
    if m.get("status") not in STATUSES:
        errs.append(f"status must be one of {STATUSES}, got {m.get('status')!r}")
    if m.get("priority") not in PRIORITIES:
        errs.append(f"priority must be one of {PRIORITIES}, got {m.get('priority')!r}")
    if m.get("gate") not in GATES:
        errs.append(f"gate must be one of {GATES}, got {m.get('gate')!r}")
    if m.get("runtime") not in RUNTIMES:
        errs.append(f"runtime must be one of {RUNTIMES}, got {m.get('runtime')!r}")
    if not re.fullmatch(r"T-\d{4}-\d{2}", m.get("id", "")):
        errs.append(f"id must look like T-MMDD-NN, got {m.get('id')!r}")
    if not m.get("attempts", "").isdigit():
        errs.append("attempts must be an integer")
    if "## 验收" not in task.body:
        errs.append("body must contain a '## 验收' section")
    return errs
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd ~/Documents/fluxus-ops && python3 -m pytest -q tests/test_taskfile.py`
Expected: `6 passed`

- [ ] **Step 6: 代码仓库加指针文件**

```bash
cd ~/Documents/AI-Trading-System && git fetch origin
export WT=$(mktemp -d)/wt-ptr && git worktree add -q --detach "$WT" origin/main
printf '# fluxus-ops\n\n任务板、agent 目录、守护进程在私有仓库 `Fluxus-Trade-Lab/fluxus-ops`，本机路径 `~/Documents/fluxus-ops/`。设计：`docs/superpowers/specs/2026-09-18-agent-fleet-v2-design.md`。\n' > "$WT/FLUXUS_OPS.md"
git -C "$WT" add FLUXUS_OPS.md && git -C "$WT" commit -q -m "docs: pointer to the private fluxus-ops repo (agent fleet v2, Andy 09-18 批)" && git -C "$WT" push -q origin HEAD:main
git worktree remove --force "$WT"
```

- [ ] **Step 7: 提交 fluxus-ops**

```bash
cd ~/Documents/fluxus-ops && git add -A && git commit -q -m "feat(taskfile): task file parse/dump/validate with tests" && git push -q -u origin main
```

---

### Task 2: git 原子改动与 gate 判路径

**Files:**
- Create: `tools/gitops.py`
- Create: `tools/gate.py`
- Create: `tests/test_gitops.py`
- Create: `tests/test_gate.py`

**Interfaces:**
- Produces: `gitops.sync(repo: Path) -> None`（fetch + reset --hard origin/main）；`gitops.commit_push(repo, paths: list[Path], msg: str) -> bool`（push 被拒返回 False，不重试）；`gitops.atomic(repo, path: Path, mutate: Callable[[Task], None], msg: str, retries=3) -> bool`（sync → load → mutate → save → commit_push；被拒则重来；mutate 抛 `Conflict` 则返回 False）；`gitops.Conflict(Exception)`；`gitops.is_on_main(repo, sha) -> bool`；`gitops.changed_paths(repo, base="origin/main") -> list[tuple[str,str]]`（`(status, path)`）。
- Produces: `gate.decide(changes: list[tuple[str,str]]) -> str`（`none|reviewer|andy`）。

- [ ] **Step 1: 写失败测试（gitops，用裸仓库 + 两个克隆模拟两个工人）**

```python
# tests/test_gitops.py
import subprocess, pathlib
from tools import gitops, taskfile as tf

SAMPLE = pathlib.Path(__file__).parent / "fixtures" / "T-0918-03.md"

def _git(*a, cwd):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout

def _make(tmp_path):
    bare = tmp_path / "origin.git"; _git("init", "-q", "--bare", "-b", "main", str(bare), cwd=tmp_path)
    a = tmp_path / "a"; b = tmp_path / "b"
    _git("clone", "-q", str(bare), str(a), cwd=tmp_path)
    (a / "tasks").mkdir(); (a / "tasks" / "T-0918-03.md").write_text(SAMPLE.read_text(), encoding="utf-8")
    _git("-c", "user.name=t", "-c", "user.email=t@t", "add", "-A", cwd=a)
    _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "seed", cwd=a)
    _git("push", "-q", "origin", "main", cwd=a)
    _git("clone", "-q", str(bare), str(b), cwd=tmp_path)
    for r in (a, b):
        _git("config", "user.name", "t", cwd=r); _git("config", "user.email", "t@t", cwd=r)
    return a, b

def _claim(task):
    if task.meta["status"] != "open":
        raise gitops.Conflict("not open")
    task.meta["status"] = "claimed"

def test_only_one_of_two_claims_wins(tmp_path):
    a, b = _make(tmp_path)
    ok_a = gitops.atomic(a, a / "tasks" / "T-0918-03.md", _claim, "claim by a")
    ok_b = gitops.atomic(b, b / "tasks" / "T-0918-03.md", _claim, "claim by b")
    assert ok_a is True and ok_b is False
    gitops.sync(b)
    assert tf.load(b / "tasks" / "T-0918-03.md").meta["status"] == "claimed"

def test_atomic_retries_after_rejected_push(tmp_path):
    a, b = _make(tmp_path)
    # b 先改 title 并推，a 的本地副本落后；a 的 atomic 必须先 sync 再改，push 一次成功
    def retitle(t): t.meta["title"] = "changed by b"
    assert gitops.atomic(b, b / "tasks" / "T-0918-03.md", retitle, "b")
    def bump(t): t.meta["attempts"] = str(int(t.meta["attempts"]) + 1)
    assert gitops.atomic(a, a / "tasks" / "T-0918-03.md", bump, "a")
    gitops.sync(b)
    t = tf.load(b / "tasks" / "T-0918-03.md")
    assert t.meta["title"] == "changed by b" and t.meta["attempts"] == "1"

def test_is_on_main_and_changed_paths(tmp_path):
    a, _ = _make(tmp_path)
    sha = _git("rev-parse", "HEAD", cwd=a).strip()
    assert gitops.is_on_main(a, sha)
    (a / "tasks" / "new.md").write_text("x"); (a / "tasks" / "T-0918-03.md").unlink()
    _git("add", "-A", cwd=a)
    assert sorted(gitops.changed_paths(a)) == [("A", "tasks/new.md"), ("D", "tasks/T-0918-03.md")]
```

把 Task 1 的 `SAMPLE` 文本存为 `tests/fixtures/T-0918-03.md`。

- [ ] **Step 2: 写失败测试（gate）**

```python
# tests/test_gate.py
from tools import gate

def test_none_for_data_and_docs():
    assert gate.decide([("M", "data/output/breadth.json"), ("A", "data/research/x.md")]) == "none"

def test_reviewer_for_code_workflow_skill_role_constitution():
    for p in [".github/workflows/daily-data-update.yml", "frontend/src/App.jsx",
              "pipeline/screeners/watchlist.py", "pipeline/tickers/x.py", "pipeline/adapters/y.py",
              "agents/alex/ROLE.md", ".claude/skills/daily-recap/SKILL.md", "CLAUDE.md"]:
        assert gate.decide([("M", p)]) == "reviewer", p

def test_andy_for_deletion_under_data_and_member_paths():
    assert gate.decide([("D", "data/history/2026-09-16.json")]) == "andy"
    assert gate.decide([("M", "frontend/src/auth/Login.jsx")]) == "andy"
    assert gate.decide([("M", "frontend/src/members/x.jsx")]) == "andy"
    assert gate.decide([("M", "api/billing.py")]) == "andy"

def test_highest_gate_wins():
    assert gate.decide([("M", "data/output/a.json"), ("M", "frontend/src/App.jsx")]) == "reviewer"
    assert gate.decide([("M", "frontend/src/App.jsx"), ("D", "data/output/a.json")]) == "andy"

def test_empty_change_is_none():
    assert gate.decide([]) == "none"
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_gitops.py tests/test_gate.py`
Expected: FAIL，两个模块都不存在

- [ ] **Step 4: 实现 gitops.py**

```python
# tools/gitops.py
"""任务板的锁就是 push：先 sync 到 origin/main，改一个文件，commit，push；被拒就重来。"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Callable
from tools import taskfile as tf


class Conflict(Exception):
    """mutate 发现任务状态已经不允许这次改动。"""


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check)


def sync(repo: Path) -> None:
    _run(repo, "fetch", "-q", "origin")
    _run(repo, "reset", "-q", "--hard", "origin/main")


def commit_push(repo: Path, paths: list[Path], msg: str) -> bool:
    _run(repo, "add", "--", *[str(p) for p in paths])
    if _run(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
        return True  # nothing to commit counts as success
    _run(repo, "commit", "-q", "-m", msg)
    return _run(repo, "push", "-q", "origin", "HEAD:main", check=False).returncode == 0


def atomic(repo: Path, path: Path, mutate: Callable[[tf.Task], None], msg: str, retries: int = 3) -> bool:
    for _ in range(retries):
        sync(repo)
        task = tf.load(path)
        try:
            mutate(task)
        except Conflict:
            return False
        errs = tf.validate(task)
        if errs:
            raise ValueError("refusing to write invalid task: " + "; ".join(errs))
        tf.save(task)
        if commit_push(repo, [path], msg):
            return True
    return False


def is_on_main(repo: Path, sha: str) -> bool:
    _run(repo, "fetch", "-q", "origin", check=False)
    return _run(repo, "merge-base", "--is-ancestor", sha, "origin/main", check=False).returncode == 0


def changed_paths(repo: Path, base: str = "origin/main") -> list[tuple[str, str]]:
    out = _run(repo, "diff", "--cached", "--name-status", base, check=False).stdout
    if not out.strip():
        out = _run(repo, "diff", "--name-status", base, check=False).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0][0], parts[-1]))
    return rows
```

- [ ] **Step 5: 实现 gate.py**

```python
# tools/gate.py
"""按改动路径判 gate。andy > reviewer > none。规则来自 spec §8。"""
from __future__ import annotations

ANDY_PREFIXES = ("frontend/src/auth/", "frontend/src/members/", "api/", "billing/")
REVIEWER_PREFIXES = (".github/workflows/", "frontend/", "pipeline/screeners/", "pipeline/tickers/",
                     "pipeline/adapters/", ".claude/skills/")
REVIEWER_NAMES = ("CLAUDE.md", "ROLE.md")


def _level(status: str, path: str) -> int:
    if path.startswith(ANDY_PREFIXES):
        return 2
    if status == "D" and path.startswith("data/"):
        return 2
    if path.startswith(REVIEWER_PREFIXES) or path.split("/")[-1] in REVIEWER_NAMES:
        return 1
    return 0


def decide(changes: list[tuple[str, str]]) -> str:
    level = max((_level(s, p) for s, p in changes), default=0)
    return ("none", "reviewer", "andy")[level]
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m pytest -q tests/`
Expected: `14 passed`

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -q -m "feat(gitops,gate): push-as-lock atomic mutation; gate by changed paths" && git push -q
```

---

### Task 3: taskboard CLI（new / list / claim / reap / handoff）

**Files:**
- Create: `tools/taskboard.py`
- Create: `tests/test_taskboard.py`

**Interfaces:**
- Consumes: `taskfile.*`、`gitops.atomic/sync/commit_push`。
- Produces: 库函数 `new(repo, *, owner, type, title, priority="P1", project="", runtime="local", created_by, body, andy="") -> Task`（写文件、commit、push，返回带 id 的任务）；`list_tasks(repo, *, owner=None, status=None, runtime=None, priority=None) -> list[Task]`；`claim(repo, task_id, by) -> bool`；`reap(repo, max_hours=3.0, now=None) -> list[str]`（回收的 id）；`handoff(repo, from_id, **new_kwargs) -> Task`；`next_id(repo, now) -> str`；`now_iso() -> str`。CLI 同名子命令，`--repo` 默认 `~/Documents/fluxus-ops`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_taskboard.py
import subprocess, datetime as dt, pathlib
from tools import taskboard as tb, taskfile as tf, gitops

def _repo(tmp_path):
    bare = tmp_path / "o.git"; subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    r = tmp_path / "r"; subprocess.run(["git", "clone", "-q", str(bare), str(r)], check=True)
    for k, v in (("user.name", "t"), ("user.email", "t@t")):
        subprocess.run(["git", "-C", str(r), "config", k, v], check=True)
    (r / "tasks").mkdir(); (r / "tasks" / ".keep").write_text("")
    subprocess.run(["git", "-C", str(r), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "seed"], check=True)
    subprocess.run(["git", "-C", str(r), "push", "-q", "origin", "main"], check=True)
    return r

BODY = "## 要做什么\n做点事。\n\n## 验收\n- [ ] 有测试\n"

def test_new_assigns_sequential_ids_per_day(tmp_path):
    r = _repo(tmp_path)
    now = dt.datetime(2026, 9, 18, 14, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    a = tb.new(r, owner="alex", type="data_fix", title="a", created_by="ops", body=BODY, now=now)
    b = tb.new(r, owner="alex", type="data_fix", title="b", created_by="ops", body=BODY, now=now)
    assert (a.meta["id"], b.meta["id"]) == ("T-0918-01", "T-0918-02")
    assert a.meta["status"] == "open" and a.meta["created_at"] == "2026-09-18T14:00:00+09:00"
    assert gitops.is_on_main(r, subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())

def test_list_filters(tmp_path):
    r = _repo(tmp_path)
    tb.new(r, owner="alex", type="x", title="a", created_by="ops", body=BODY)
    tb.new(r, owner="claire", type="x", title="b", created_by="ops", body=BODY, priority="P0")
    assert [t.meta["title"] for t in tb.list_tasks(r, owner="claire")] == ["b"]
    assert [t.meta["title"] for t in tb.list_tasks(r, priority="P0")] == ["b"]
    assert len(tb.list_tasks(r, status="open")) == 2

def test_claim_sets_claimed_and_is_exclusive(tmp_path):
    r = _repo(tmp_path)
    t = tb.new(r, owner="alex", type="x", title="a", created_by="ops", body=BODY)
    assert tb.claim(r, t.meta["id"], by="alex-worker-1") is True
    assert tb.claim(r, t.meta["id"], by="alex-worker-2") is False
    got = tb.list_tasks(r, status="claimed")[0]
    assert got.meta["claimed_at"] != ""

def test_reap_returns_stale_claims_and_blocks_after_two(tmp_path):
    r = _repo(tmp_path)
    t = tb.new(r, owner="alex", type="x", title="a", created_by="ops", body=BODY)
    tb.claim(r, t.meta["id"], by="w")
    later = dt.datetime.fromisoformat(tb.list_tasks(r)[0].meta["claimed_at"]) + dt.timedelta(hours=4)
    assert tb.reap(r, now=later) == [t.meta["id"]]
    got = tb.list_tasks(r)[0]
    assert got.meta["status"] == "open" and got.meta["attempts"] == "1"
    tb.claim(r, t.meta["id"], by="w")
    later2 = dt.datetime.fromisoformat(tb.list_tasks(r)[0].meta["claimed_at"]) + dt.timedelta(hours=4)
    tb.reap(r, now=later2)
    assert tb.list_tasks(r)[0].meta["status"] == "blocked"

def test_handoff_creates_task_with_created_by_source(tmp_path):
    r = _repo(tmp_path)
    src = tb.new(r, owner="linda", type="x", title="found bug", created_by="ops", body=BODY)
    t = tb.handoff(r, src.meta["id"], owner="claire", type="frontend_fix", title="fix it", body=BODY)
    assert t.meta["created_by"] == src.meta["id"] and t.meta["owner"] == "claire"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_taskboard.py`
Expected: FAIL，`No module named 'tools.taskboard'`

- [ ] **Step 3: 实现 taskboard.py（本任务只做这五个动作，其余在 Task 4 追加）**

```python
# tools/taskboard.py
"""任务板 CLI。所有状态改动只经这里；改一个文件 = 一次 atomic。"""
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path
from tools import gitops, taskfile as tf

JST = dt.timezone(dt.timedelta(hours=9))
DEFAULT_REPO = Path.home() / "Documents" / "fluxus-ops"


def now_iso(now: dt.datetime | None = None) -> str:
    return (now or dt.datetime.now(JST)).replace(microsecond=0).isoformat()


def next_id(repo: Path, now: dt.datetime) -> str:
    stem = f"T-{now:%m%d}-"
    used = [int(p.stem[len(stem):]) for p in (repo / "tasks").glob(f"{stem}*.md")]
    return f"{stem}{(max(used) + 1) if used else 1:02d}"


def new(repo: Path, *, owner: str, type: str, title: str, created_by: str, body: str,
        priority: str = "P1", project: str = "", runtime: str = "local", andy: str = "",
        now: dt.datetime | None = None) -> tf.Task:
    gitops.sync(repo)
    now = now or dt.datetime.now(JST)
    tid = next_id(repo, now)
    meta = {k: "" for k in tf.FIELDS}
    meta.update(id=tid, title=title, owner=owner, type=type, project=project, status="open",
                priority=priority, gate="none", runtime=runtime, created_by=created_by,
                created_at=now_iso(now), attempts="0", andy=andy)
    task = tf.Task(meta=meta, body=body, path=repo / "tasks" / f"{tid}.md")
    errs = tf.validate(task)
    if errs:
        raise ValueError("; ".join(errs))
    tf.save(task)
    if not gitops.commit_push(repo, [task.path], f"task: new {tid} → {owner} · {title}"):
        raise RuntimeError("push rejected while creating task; rerun")
    return task


def list_tasks(repo: Path, *, owner=None, status=None, runtime=None, priority=None) -> list[tf.Task]:
    out = []
    for p in sorted((repo / "tasks").glob("T-*.md")):
        t = tf.load(p)
        m = t.meta
        if owner and m["owner"] != owner: continue
        if status and m["status"] != status: continue
        if runtime and m["runtime"] != runtime: continue
        if priority and m["priority"] != priority: continue
        out.append(t)
    return out


def claim(repo: Path, task_id: str, by: str) -> bool:
    def mutate(t: tf.Task):
        if t.meta["status"] != "open":
            raise gitops.Conflict(t.meta["status"])
        t.meta["status"] = "claimed"
        t.meta["claimed_at"] = now_iso()
        t.meta["result"] = ""
    return gitops.atomic(repo, repo / "tasks" / f"{task_id}.md", mutate, f"task: claim {task_id} by {by}")


def reap(repo: Path, max_hours: float = 3.0, now: dt.datetime | None = None) -> list[str]:
    gitops.sync(repo)
    now = now or dt.datetime.now(JST)
    reaped = []
    for t in list_tasks(repo, status="claimed"):
        claimed = dt.datetime.fromisoformat(t.meta["claimed_at"])
        if (now - claimed).total_seconds() < max_hours * 3600:
            continue
        def mutate(x: tf.Task):
            x.meta["attempts"] = str(int(x.meta["attempts"]) + 1)
            x.meta["status"] = "blocked" if int(x.meta["attempts"]) >= 2 else "open"
            x.meta["claimed_at"] = ""
        if gitops.atomic(repo, t.path, mutate, f"task: reap {t.meta['id']} (stale claim)"):
            reaped.append(t.meta["id"])
    return reaped


def handoff(repo: Path, from_id: str, **kw) -> tf.Task:
    return new(repo, created_by=from_id, **kw)


def _cli(argv=None):
    ap = argparse.ArgumentParser(prog="taskboard")
    ap.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    for f in ("owner", "type", "title", "created-by"): n.add_argument(f"--{f}", required=True)
    n.add_argument("--priority", default="P1"); n.add_argument("--project", default="")
    n.add_argument("--runtime", default="local"); n.add_argument("--andy", default="")
    n.add_argument("--body-file", type=Path, required=True)
    l = sub.add_parser("list")
    for f in ("owner", "status", "runtime", "priority"): l.add_argument(f"--{f}")
    l.add_argument("--json", action="store_true")
    c = sub.add_parser("claim"); c.add_argument("id"); c.add_argument("--by", required=True)
    r = sub.add_parser("reap"); r.add_argument("--max-hours", type=float, default=3.0)
    h = sub.add_parser("handoff"); h.add_argument("--from", dest="from_id", required=True)
    for f in ("owner", "type", "title"): h.add_argument(f"--{f}", required=True)
    h.add_argument("--priority", default="P1"); h.add_argument("--body-file", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "new":
        t = new(a.repo, owner=a.owner, type=a.type, title=a.title, created_by=a.created_by,
                body=a.body_file.read_text(encoding="utf-8"), priority=a.priority, project=a.project,
                runtime=a.runtime, andy=a.andy)
        print(t.meta["id"])
    elif a.cmd == "list":
        ts = list_tasks(a.repo, owner=a.owner, status=a.status, runtime=a.runtime, priority=a.priority)
        if a.json:
            print(json.dumps([t.meta for t in ts], ensure_ascii=False))
        else:
            for t in ts:
                m = t.meta; print(f"{m['id']} {m['status']:<10} {m['priority']} {m['owner']:<7} {m['title']}")
    elif a.cmd == "claim":
        sys.exit(0 if claim(a.repo, a.id, a.by) else 1)
    elif a.cmd == "reap":
        print("\n".join(reap(a.repo, a.max_hours)))
    elif a.cmd == "handoff":
        t = handoff(a.repo, a.from_id, owner=a.owner, type=a.type, title=a.title, priority=a.priority,
                    body=a.body_file.read_text(encoding="utf-8"))
        print(t.meta["id"])


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest -q tests/`
Expected: `19 passed`

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -q -m "feat(taskboard): new/list/claim/reap/handoff with push-as-lock" && git push -q
```

---

### Task 4: taskboard 收口动作（done 检查项、needs-andy、block、close、review、gate）

**Files:**
- Modify: `tools/taskboard.py`（追加函数与子命令）
- Modify: `tests/test_taskboard.py`（追加测试）

**Interfaces:**
- Consumes: `gitops.is_on_main`、`gitops.changed_paths`、`gate.decide`、`taskfile.acceptance`。
- Produces: `done(repo, task_id, *, result_sha, code_repo: Path, tests_passed: bool) -> tuple[bool, list[str]]`（返回 `(ok, reasons)`；ok 时若 `type != "material"` 自动 `new(..., owner="steve", type="material", priority="P2", created_by=task_id)`）；`needs_andy(repo, task_id, question: str) -> bool`；`block(repo, task_id, reason) -> bool`；`close(repo, task_id, by, note="") -> bool`；`review(repo, task_id, verdict: str, evidence: str) -> bool`（verdict 为 `PASS` 或 `FAIL`；FAIL 且 attempts ≥ 1 则 blocked，否则回 open 并 attempts+1）；`set_gate(repo, task_id, code_worktree: Path) -> str`（算 gate 写回，返回值）。

- [ ] **Step 1: 追加失败测试**

```python
# 追加到 tests/test_taskboard.py
def _code_repo(tmp_path):
    """一个假的代码仓库：有 origin/main，一个提交在 main 上，一个不在。"""
    bare = tmp_path / "code.git"; subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    c = tmp_path / "code"; subprocess.run(["git", "clone", "-q", str(bare), str(c)], check=True)
    for k, v in (("user.name", "t"), ("user.email", "t@t")):
        subprocess.run(["git", "-C", str(c), "config", k, v], check=True)
    (c / "a.txt").write_text("1"); subprocess.run(["git", "-C", str(c), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(c), "commit", "-q", "-m", "on main"], check=True)
    subprocess.run(["git", "-C", str(c), "push", "-q", "origin", "main"], check=True)
    on_main = subprocess.run(["git", "-C", str(c), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (c / "b.txt").write_text("2"); subprocess.run(["git", "-C", str(c), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(c), "commit", "-q", "-m", "local only"], check=True)
    local_only = subprocess.run(["git", "-C", str(c), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return c, on_main, local_only

BODY_OK = "## 要做什么\nx\n\n## 验收\n- [x] 一\n- [x] 二\n"

def test_done_refuses_when_sha_not_on_main_or_tests_failed_or_acceptance_open(tmp_path):
    r = _repo(tmp_path); c, on_main, local_only = _code_repo(tmp_path)
    t = tb.new(r, owner="alex", type="data_fix", title="a", created_by="ops", body=BODY)  # BODY 有一条未打勾
    tb.claim(r, t.meta["id"], by="w")
    ok, why = tb.done(r, t.meta["id"], result_sha=local_only, code_repo=c, tests_passed=False)
    assert ok is False
    assert any("main" in w for w in why) and any("测试" in w for w in why) and any("验收" in w for w in why)

def test_done_passes_and_spawns_material_task(tmp_path):
    r = _repo(tmp_path); c, on_main, _ = _code_repo(tmp_path)
    t = tb.new(r, owner="alex", type="data_fix", title="a", created_by="ops", body=BODY_OK)
    tb.claim(r, t.meta["id"], by="w")
    ok, why = tb.done(r, t.meta["id"], result_sha=on_main, code_repo=c, tests_passed=True)
    assert ok, why
    got = {x.meta["id"]: x for x in tb.list_tasks(r)}
    assert got[t.meta["id"]].meta["status"] == "done" and got[t.meta["id"]].meta["closed_at"] != ""
    mats = [x for x in got.values() if x.meta["type"] == "material"]
    assert len(mats) == 1 and mats[0].meta["owner"] == "steve" and mats[0].meta["created_by"] == t.meta["id"]

def test_done_with_reviewer_gate_requires_pass_review(tmp_path):
    r = _repo(tmp_path); c, on_main, _ = _code_repo(tmp_path)
    t = tb.new(r, owner="claire", type="frontend_fix", title="a", created_by="ops", body=BODY_OK)
    tb.claim(r, t.meta["id"], by="w")
    def set_reviewer(x): x.meta["gate"] = "reviewer"
    gitops.atomic(r, t.path, set_reviewer, "gate")
    ok, why = tb.done(r, t.meta["id"], result_sha=on_main, code_repo=c, tests_passed=True)
    assert not ok and any("review" in w for w in why)
    assert tb.review(r, t.meta["id"], "PASS", "test_x 改动前红改动后绿；未删可执行行")
    ok, _ = tb.done(r, t.meta["id"], result_sha=on_main, code_repo=c, tests_passed=True)
    assert ok

def test_review_fail_reopens_then_blocks(tmp_path):
    r = _repo(tmp_path)
    t = tb.new(r, owner="claire", type="x", title="a", created_by="ops", body=BODY_OK)
    tb.claim(r, t.meta["id"], by="w")
    tb.review(r, t.meta["id"], "FAIL", "删了 3 行闸接线没说明")
    x = tb.list_tasks(r)[0]; assert x.meta["status"] == "open" and x.meta["attempts"] == "1"
    tb.claim(r, t.meta["id"], by="w")
    tb.review(r, t.meta["id"], "FAIL", "仍然")
    assert tb.list_tasks(r)[0].meta["status"] == "blocked"

def test_needs_andy_block_close(tmp_path):
    r = _repo(tmp_path)
    t = tb.new(r, owner="ops", type="x", title="a", created_by="ops", body=BODY_OK)
    assert tb.needs_andy(r, t.meta["id"], "合不合 feat/x？")
    assert tb.list_tasks(r)[0].meta["status"] == "needs_andy"
    assert tb.close(r, t.meta["id"], by="andy", note="不做")
    assert tb.list_tasks(r)[0].meta["status"] == "closed"
    u = tb.new(r, owner="ops", type="x", title="b", created_by="ops", body=BODY_OK)
    assert tb.block(r, u.meta["id"], "触到禁止项 rm -rf")
    assert [x.meta["status"] for x in tb.list_tasks(r, status="blocked")] == ["blocked"]

def test_set_gate_reads_code_worktree_diff(tmp_path):
    r = _repo(tmp_path); c, _, _ = _code_repo(tmp_path)
    (c / "frontend").mkdir(); (c / "frontend" / "App.jsx").write_text("x")
    subprocess.run(["git", "-C", str(c), "add", "-A"], check=True)
    t = tb.new(r, owner="claire", type="x", title="a", created_by="ops", body=BODY_OK)
    assert tb.set_gate(r, t.meta["id"], c) == "reviewer"
    assert tb.list_tasks(r)[0].meta["gate"] == "reviewer"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_taskboard.py`
Expected: 新增 6 条 FAIL，`AttributeError: module 'tools.taskboard' has no attribute 'done'`

- [ ] **Step 3: 追加实现**

```python
# 追加到 tools/taskboard.py（放在 handoff 之后、_cli 之前）
from tools import gate as gatemod


def done(repo: Path, task_id: str, *, result_sha: str, code_repo: Path, tests_passed: bool) -> tuple[bool, list[str]]:
    gitops.sync(repo)
    t = tf.load(repo / "tasks" / f"{task_id}.md")
    why = []
    if not gitops.is_on_main(code_repo, result_sha):
        why.append(f"提交 {result_sha[:8]} 不在代码仓库 origin/main 上")
    if not tests_passed:
        why.append("测试未通过（tests_passed=False）")
    open_items = [text for ok, text in tf.acceptance(t) if not ok]
    if open_items:
        why.append("验收未全部打勾：" + "；".join(open_items))
    if t.meta["gate"] == "reviewer" and not t.meta["review"].startswith("PASS"):
        why.append("gate=reviewer 但 review 字段不是 PASS")
    if t.meta["gate"] == "andy" and not t.meta["andy"]:
        why.append("gate=andy 但没有 Andy 原话")
    if why:
        return False, why
    def mutate(x: tf.Task):
        if x.meta["status"] not in ("claimed", "needs_andy"):
            raise gitops.Conflict(x.meta["status"])
        x.meta["status"] = "done"; x.meta["result"] = result_sha; x.meta["closed_at"] = now_iso()
    if not gitops.atomic(repo, t.path, mutate, f"task: done {task_id} @ {result_sha[:8]}"):
        return False, ["状态已被别人改动，done 未写入"]
    if t.meta["type"] != "material":
        new(repo, owner="steve", type="material", priority="P2", created_by=task_id,
            title=f"素材：{t.meta['title']}",
            body=f"## 要做什么\n从 {task_id}（{t.meta['title']}，{result_sha[:8]}）提一行可发布素材追进 material_inbox。\n\n## 验收\n- [ ] material_inbox 多了一行且带出处\n")
    return True, []


def _set_status(repo: Path, task_id: str, status: str, field: str = "", value: str = "", msg: str = "") -> bool:
    def mutate(x: tf.Task):
        x.meta["status"] = status
        if status in ("done", "closed"):
            x.meta["closed_at"] = now_iso()
        if field:
            x.meta[field] = value
    return gitops.atomic(repo, repo / "tasks" / f"{task_id}.md", mutate, msg or f"task: {status} {task_id}")


def needs_andy(repo: Path, task_id: str, question: str) -> bool:
    return _set_status(repo, task_id, "needs_andy", "review", f"ASK {question}", f"task: needs_andy {task_id}")


def block(repo: Path, task_id: str, reason: str) -> bool:
    return _set_status(repo, task_id, "blocked", "review", f"BLOCKED {reason}", f"task: blocked {task_id}")


def close(repo: Path, task_id: str, by: str, note: str = "") -> bool:
    return _set_status(repo, task_id, "closed", "andy" if by == "andy" else "review",
                       note or f"closed by {by}", f"task: closed {task_id} by {by}")


def review(repo: Path, task_id: str, verdict: str, evidence: str) -> bool:
    if verdict not in ("PASS", "FAIL"):
        raise ValueError("verdict must be PASS or FAIL")
    def mutate(x: tf.Task):
        x.meta["review"] = f"{verdict} {evidence}".replace("\n", " ")
        if verdict == "FAIL":
            x.meta["attempts"] = str(int(x.meta["attempts"]) + 1)
            x.meta["status"] = "blocked" if int(x.meta["attempts"]) >= 2 else "open"
            x.meta["claimed_at"] = ""
    return gitops.atomic(repo, repo / "tasks" / f"{task_id}.md", mutate, f"task: review {verdict} {task_id}")


def set_gate(repo: Path, task_id: str, code_worktree: Path) -> str:
    g = gatemod.decide(gitops.changed_paths(code_worktree))
    def mutate(x: tf.Task): x.meta["gate"] = g
    gitops.atomic(repo, repo / "tasks" / f"{task_id}.md", mutate, f"task: gate {task_id} = {g}")
    return g
```

并在 `_cli` 里追加子命令：

```python
    d = sub.add_parser("done"); d.add_argument("id"); d.add_argument("--result", required=True)
    d.add_argument("--code-repo", type=Path, default=Path.home() / "Documents" / "AI-Trading-System")
    d.add_argument("--tests-passed", action="store_true")
    na = sub.add_parser("needs-andy"); na.add_argument("id"); na.add_argument("--question", required=True)
    b = sub.add_parser("block"); b.add_argument("id"); b.add_argument("--reason", required=True)
    cl = sub.add_parser("close"); cl.add_argument("id"); cl.add_argument("--by", required=True); cl.add_argument("--note", default="")
    rv = sub.add_parser("review"); rv.add_argument("id"); rv.add_argument("--verdict", required=True); rv.add_argument("--evidence-file", type=Path, required=True)
    g = sub.add_parser("gate"); g.add_argument("id"); g.add_argument("--worktree", type=Path, required=True)
```

以及分派：

```python
    elif a.cmd == "done":
        ok, why = done(a.repo, a.id, result_sha=a.result, code_repo=a.code_repo, tests_passed=a.tests_passed)
        print("\n".join(why)); sys.exit(0 if ok else 1)
    elif a.cmd == "needs-andy": sys.exit(0 if needs_andy(a.repo, a.id, a.question) else 1)
    elif a.cmd == "block": sys.exit(0 if block(a.repo, a.id, a.reason) else 1)
    elif a.cmd == "close": sys.exit(0 if close(a.repo, a.id, a.by, a.note) else 1)
    elif a.cmd == "review": sys.exit(0 if review(a.repo, a.id, a.verdict, a.evidence_file.read_text(encoding="utf-8")) else 1)
    elif a.cmd == "gate": print(set_gate(a.repo, a.id, a.worktree))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest -q tests/`
Expected: `25 passed`

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -q -m "feat(taskboard): done checks, needs-andy/block/close, review verdicts, gate from worktree diff" && git push -q
```

---

### Task 5: agent 目录、ROLE.md、config.json、行数闸

**Files:**
- Create: `agents/<name>/ROLE.md`、`agents/<name>/config.json`、`agents/<name>/memory/.keep`、`agents/<name>/runs/.keep`，name ∈ alex claire linda q mia vera steve gary ops
- Create: `tools/rolecheck.py`
- Create: `tests/test_rolecheck.py`

**Interfaces:**
- Produces: `rolecheck.check(path) -> list[str]`（超 120 行、缺必需节、条目无出处各报一条）；config.json 形状：

```json
{
  "models": {"default": "claude-sonnet-5", "judgment": "claude-opus-5", "mechanical": "claude-haiku-4-5-20251001"},
  "type_models": {"data_recovery": "judgment", "research": "judgment", "material": "mechanical", "archive": "mechanical"},
  "max_parallel": 1,
  "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Agent"],
  "disallowed_tools": ["Bash(rm -rf*)", "Bash(git push --force*)", "Bash(vercel*)", "Bash(gh release*)", "WebFetch"],
  "skills_by_type": {"data_recovery": ["data-recovery", "failure-triage"], "*": ["fable-voice"]}
}
```

- [ ] **Step 1: 写失败测试**

```python
# tests/test_rolecheck.py
from tools import rolecheck

GOOD = "# alex\n\n## 职责\n数据管道。（TEAM.md 08-22）\n\n## 文件边界\n- pipeline/screeners/（TEAM.md 08-22）\n\n## 能直接合的路径\n- data/output/（spec §8）\n\n## 必读 skill\n- data_recovery: data-recovery（spec 附录）\n"

def test_good_role_passes(tmp_path):
    p = tmp_path / "ROLE.md"; p.write_text(GOOD, encoding="utf-8")
    assert rolecheck.check(p) == []

def test_too_long_fails(tmp_path):
    p = tmp_path / "ROLE.md"; p.write_text(GOOD + "\n".join("- 条（x）" for _ in range(120)), encoding="utf-8")
    assert any("120" in e for e in rolecheck.check(p))

def test_missing_section_fails(tmp_path):
    p = tmp_path / "ROLE.md"; p.write_text(GOOD.replace("## 必读 skill", "## 别的"), encoding="utf-8")
    assert any("必读 skill" in e for e in rolecheck.check(p))

def test_bullet_without_source_fails(tmp_path):
    p = tmp_path / "ROLE.md"; p.write_text(GOOD + "- 没有出处的条目\n", encoding="utf-8")
    assert any("出处" in e for e in rolecheck.check(p))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_rolecheck.py`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 rolecheck.py**

```python
# tools/rolecheck.py
"""ROLE.md 闸：≤120 行；四个节齐全；每条 '- ' 条目末尾带括号出处。"""
from __future__ import annotations
import re, sys
from pathlib import Path

MAX_LINES = 120
REQUIRED = ["## 职责", "## 文件边界", "## 能直接合的路径", "## 必读 skill"]
_SOURCE = re.compile(r"[（(][^()（）]+[）)]\s*$")


def check(path: Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    errs = []
    if len(lines) > MAX_LINES:
        errs.append(f"{path}: {len(lines)} 行，超过 {MAX_LINES} 行上限")
    for sec in REQUIRED:
        if sec not in lines:
            errs.append(f"{path}: 缺节 {sec}")
    for i, ln in enumerate(lines, 1):
        if ln.startswith("- ") and not _SOURCE.search(ln):
            errs.append(f"{path}:{i}: 条目无出处（末尾要有括号注明事故编号或 Andy 原话日期）")
    return errs


if __name__ == "__main__":
    problems = [e for p in sys.argv[1:] for e in check(Path(p))]
    print("\n".join(problems))
    sys.exit(1 if problems else 0)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest -q tests/test_rolecheck.py`
Expected: `4 passed`

- [ ] **Step 5: 写 9 份 ROLE.md 与 config.json**

每份 ROLE.md 四节，内容从 `git -C ~/Documents/AI-Trading-System show origin/main:TEAM.md` 花名册行原样抄，每条末尾注 `（TEAM.md 08-22）`；「能直接合的路径」按 spec §8 gate=none 的路径填，注 `（spec §8）`；「必读 skill」按 Task 6 的 skill 名填，注 `（spec 附录）`。alex 的 ROLE.md 额外含 Joe 晨检职责（注 `（TEAM.md Plumber Joe 行，spec §6.1 并入）`），linda 的额外含 Zac 夜班的研究复盘（同法），steve 的额外含收藏夹整理。示例（alex）：

```markdown
# alex · 数据

## 职责
- 数据管道与数据契约；`data/output`、`data/history` 的唯一写入方（TEAM.md 08-22）
- 每日晨检：核 cron、全页面盘查、失败班次分诊与修复（TEAM.md Plumber Joe 行，spec §6.1 并入）
- Dashboard 数据死线 JST 08:30，出错即 P0（CLAUDE.md 09-17，Andy「Dashboard出现错误，一定要马上紧急修补」）

## 文件边界
- pipeline/screeners/、pipeline/tickers/、pipeline/adapters/（TEAM.md 08-22）
- data/output/、data/history/、data/reference/DATA_CONTRACTS.md、DATA_RELIABILITY.md（TEAM.md 08-22）
- .github/workflows/daily-data-update.yml（gate=reviewer）（spec §8）

## 能直接合的路径
- data/output/、data/history/、data/research/、pipeline/tests/（spec §8）

## 必读 skill
- data_recovery: data-recovery（spec 附录）
- failure_triage: failure-triage（spec 附录）
- *: fable-voice（spec §6.6）
```

config.json 按 Interfaces 里的形状，每个 agent 的 `type_models` 与 `skills_by_type` 按其 ROLE.md 填；ops 的 `models.judgment` 用 `claude-opus-5`，`review_model` 字段：`{"claude-sonnet-5": "claude-opus-5", "claude-opus-5": "claude-fable-5-1"}` 放在 `agents/ops/config.json`，供 worker 查表。

- [ ] **Step 6: 跑行数闸**

Run: `python3 tools/rolecheck.py agents/*/ROLE.md`
Expected: 无输出，退出码 0

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -q -m "feat(agents): 9 ROLE.md + config.json; rolecheck gate (≤120 lines, sourced bullets)" && git push -q
```

---

### Task 6: skill 壳（代码仓库）与工人流程文件

**Files:**
- Create（代码仓库）: `.claude/skills/{data-recovery,failure-triage,branch-review,x-watch,chart-for-andy,incident-report,daily-page,data-gap-study,task-protocol}/SKILL.md` 与各自 `evals/evals.json`
- Modify（代码仓库）: `.claude/skills/daily-recap/SKILL.md`（头部加 `owner: ops`；追加「周模式」节，内容从 `~/.claude/scheduled-tasks/recap-weekly/SKILL.md` 搬）
- Create（fluxus-ops）: `agents/_worker_protocol.md`

**Interfaces:**
- Produces: 每个 SKILL.md 头部 front matter 含 `name`、`description`、`owner`；`branch-review` 的正文就是审核员四问；`_worker_protocol.md` 是工人 prompt 的固定部分。

- [ ] **Step 1: 搬正文**

每个壳的正文从现有任务书原样搬：`data-recovery` ← 云端哨兵 prompt 第 4 条（`RemoteTrigger get trig_01QCuAfFpqtYivKM5bbHwEws`）；`failure-triage` ← 同 prompt 第 1–3 条；`x-watch` ← `~/.claude/scheduled-tasks/steve-x-daily-watch/SKILL.md` 与 `steve-x-nightcap/SKILL.md`；`chart-for-andy` ← 记忆 `method_charts_andy_accepts.md`；`incident-report` ← `data/reference/incidents/` 里最完整一份的结构；`daily-page` ← 云端每日页 prompt（`trig_01RTGvUGRfr9Uvj3mYPBP3UP`）；`data-gap-study` ← 记忆 `method_audit_which_studies_a_data_gap_touched.md`。头部：

```markdown
---
name: data-recovery
description: 数据班被闸拦下（C_gate）后，从 GitHub artifact 恢复 data/output 与 data/history，不重抓。凡任务 type=data_recovery、或哨兵分诊结果为 C_gate、或 Andy 说「dashboard 停在前一天/数据没落地」都用本 skill。
owner: alex
---
```

- [ ] **Step 2: 写 branch-review**

```markdown
---
name: branch-review
description: 审核员。工人改动的 gate=reviewer 时，在同一进程里由只读子 agent 按本 skill 核查改动并给 PASS/FAIL 判词。凡任务 gate=reviewer、或有人说「审一下这个分支」都用本 skill。
owner: ops
---
你是审核员，只读，不改文件。输入：分支名、`git diff origin/main...HEAD --stat` 与全文、测试输出、任务文件的验收节。逐问给证据，缺一问不许 PASS：

1. **删了 main 上已有的可执行行吗？** 跑 `git diff origin/main...HEAD | grep '^-' | grep -v '^---'`，逐行判是否可执行（代码、配置、workflow 步骤算；注释、空行不算）。删了的，任务说明里必须写明删的是什么、为什么；没写明 → FAIL。（Andy 2026-09-05 批的 safe-merge 判据）
2. **哪个测试改动前红、改动后绿？** 指出文件与测试名。指不出 → FAIL。
3. **越过 owner 的文件边界了吗？** 对照 `agents/<owner>/ROLE.md` 的「文件边界」。越了 → FAIL。
4. **验收逐条对得上吗？** 每条写「对上/没对上 + 证据」。

输出格式（最后一行必须是这个）：
`VERDICT: PASS|FAIL · Q1 … · Q2 … · Q3 … · Q4 …`
```

- [ ] **Step 3: 写 task-protocol（给交互会话用）与 _worker_protocol.md（给工人用）**

`_worker_protocol.md`：

```markdown
# 工人流程（每个工人的 prompt 固定部分）

你是 agents/{agent}，本次只做任务 {task_id}。任务文件、你的 ROLE.md、必读 skill 已在下方。规矩只有这一页。

1. 任务已由守护进程替你领取（status=claimed）。不要再 claim。
2. 在代码仓库建临时工作树：`export WT=$(mktemp -d)/wt-{task_id} && git -C ~/Documents/AI-Trading-System fetch -q origin && git -C ~/Documents/AI-Trading-System worktree add -q --detach "$WT" origin/main`。所有改动只在 $WT 里。永不在 ~/Documents/AI-Trading-System 主树 commit。
3. 干活。只 `git add` 你改的文件；提交前 `git -C "$WT" diff --cached --name-only` 数一遍。
4. 跑两个测试根：`~/Documents/AI-Trading-System/.venv/bin/python -m pytest -q pipeline/tests tests --deselect pipeline/tests/test_content_processor.py`（在 $WT 里）。红了就修，修不了走第 8 步。
5. 算 gate：`python3 ~/Documents/fluxus-ops/tools/taskboard.py gate {task_id} --worktree "$WT"`。
6. gate=none：`git -C "$WT" push -q origin HEAD:main`（被拒则 fetch + rebase 一次，再推）。
   gate=reviewer：先推分支 `agent/{agent}/{task_id}`，再用 Agent 工具派一个只读子 agent（模型 {review_model}，subagent_type=Explore），prompt 是 .claude/skills/branch-review/SKILL.md 全文 + 分支名 + 测试输出 + 验收节；把它最后一行 VERDICT 写进 `taskboard.py review {task_id} --verdict PASS|FAIL --evidence-file <文件>`。PASS 才 push 到 main；FAIL 就停在分支，第 9 步收工。
   gate=andy：推分支，`taskboard.py needs-andy {task_id} --question "<一句话>"`，第 9 步收工。
7. 合进 main 后：`taskboard.py done {task_id} --result <sha> --tests-passed`。它拒绝就按它打印的原因补（验收没打勾就在任务文件里打勾并推 fluxus-ops）。
8. 做不了：`taskboard.py block {task_id} --reason "<一句话>"`。要转给别人：`taskboard.py handoff --from {task_id} --owner <名> --type <type> --title <一句话> --body-file <文件>`。
9. 收工前：把本次做了什么、结论、下一步写进 `~/Documents/fluxus-ops/agents/{agent}/runs/{started_at}-{task_id}.md`；`git -C "$WT" worktree remove --force "$WT"` 前先确认没有未推的提交；在 fluxus-ops 里 `git add agents/{agent}/runs && git commit -q -m "run: {agent} {task_id}" && git push -q`。
10. 禁止：rm -rf、force push、reset --hard 主树、vercel deploy、对外发送任何东西、把会员个人信息写进代码仓库。触到就走第 8 步。
```

`task-protocol` skill（给 Andy 打开的交互会话）：description 写「任何会话开工、Andy 派活、Andy 说以后这样做、Andy 回 y/n/加/不做 时用」，正文：开工先 `taskboard.py list --owner <自己> --status open`；领活用 `claim --by chat`；Andy 说「以后这样做」→ 逐字写进自己 ROLE.md 或 memory 并 push fluxus-ops，收工前 `git -C ~/Documents/fluxus-ops diff --stat HEAD~5` 自查本轮裁决是否落盘；Andy 回一个字 → `close/done/needs-andy` 对应命令；派活给别人 → `new`。

- [ ] **Step 4: 每个新壳写 3 条 eval**

`evals/evals.json` 形状（沿用 `.claude/skills/vercel-ops/evals/evals.json` 的现有格式）：

```json
[
  {"prompt": "dashboard 停在 09-16，run 35160482205 被 schema 闸拦了，恢复一下", "should_trigger": true, "skill": "data-recovery"},
  {"prompt": "帮我看看 breadth.json 今天的读数", "should_trigger": false, "skill": "data-recovery"},
  {"prompt": "C_gate，artifact 还在，怎么放回去", "should_trigger": true, "skill": "data-recovery"}
]
```

- [ ] **Step 5: 提交到代码仓库（gate=reviewer 路径，走临时工作树 + 直推；Andy 已批 spec，提交信息引原话）**

```bash
cd ~/Documents/AI-Trading-System && git fetch -q origin
export WT=$(mktemp -d)/wt-skills && git worktree add -q --detach "$WT" origin/main
# 把 9 个壳目录与 daily-recap 的改动放进 $WT/.claude/skills/
git -C "$WT" add .claude/skills && git -C "$WT" diff --cached --name-only
git -C "$WT" commit -q -F - <<'M'
skills: 9 个 skill 壳（正文从任务书原样搬，各 3 条 eval，标 owner）+ daily-recap 并入周模式

Andy 2026-09-18 批 agent fleet v2 spec：「可以，我直接批了。」（spec 附录：首批 skill 壳）
M
git -C "$WT" push -q origin HEAD:main && git worktree remove --force "$WT"
cd ~/Documents/fluxus-ops && git add agents/_worker_protocol.md && git commit -q -m "feat(agents): worker protocol" && git push -q
```

---

### Task 7: 工人启动器（worker.py）

**Files:**
- Create: `tools/worker.py`
- Create: `tests/test_worker.py`
- Create: `tests/fixtures/claude_json_output.json`（把本计划验证过的真实输出存进去：键 `result`、`session_id`、`total_cost_usd`、`usage.input_tokens`、`usage.output_tokens`、`usage.cache_creation_input_tokens`、`usage.cache_read_input_tokens`、`modelUsage`、`is_error`、`num_turns`、`permission_denials`）

**Interfaces:**
- Consumes: `taskfile.Task`、`agents/<a>/config.json`、`agents/<a>/ROLE.md`、`agents/_worker_protocol.md`、代码仓库 `.claude/skills/<s>/SKILL.md`。
- Produces: `worker.build_prompt(ops_repo, code_repo, task, agent_cfg) -> str`；`worker.pick_model(agent_cfg, task_type) -> str`；`worker.review_model_for(ops_repo, model) -> str`；`worker.run(ops_repo, code_repo, task, timeout_s=2700, claude_bin="claude") -> WorkerResult`（`ok: bool, model: str, usage: dict, cost_usd: float, session_id: str, timed_out: bool, stdout_tail: str`）；`worker.parse_output(text) -> dict`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_worker.py
import json, pathlib, subprocess, sys
from tools import worker, taskfile as tf

FIX = pathlib.Path(__file__).parent / "fixtures"

def _ops(tmp_path):
    (tmp_path / "agents" / "alex" / "memory").mkdir(parents=True)
    (tmp_path / "agents" / "alex" / "ROLE.md").write_text("# alex\n## 必读 skill\n- data_recovery: data-recovery（x）\n", encoding="utf-8")
    (tmp_path / "agents" / "alex" / "config.json").write_text(json.dumps({
        "models": {"default": "claude-sonnet-5", "judgment": "claude-opus-5", "mechanical": "claude-haiku-4-5-20251001"},
        "type_models": {"data_recovery": "judgment", "material": "mechanical"},
        "skills_by_type": {"data_recovery": ["data-recovery"], "*": ["fable-voice"]},
        "allowed_tools": ["Bash", "Read"], "disallowed_tools": ["Bash(rm -rf*)"]}), encoding="utf-8")
    (tmp_path / "agents" / "ops").mkdir()
    (tmp_path / "agents" / "ops" / "config.json").write_text(json.dumps({"review_model": {"claude-sonnet-5": "claude-opus-5", "claude-opus-5": "claude-fable-5-1"}}), encoding="utf-8")
    (tmp_path / "agents" / "_worker_protocol.md").write_text("PROTOCOL {agent} {task_id} {review_model}", encoding="utf-8")
    code = tmp_path / "code"; (code / ".claude" / "skills" / "data-recovery").mkdir(parents=True)
    (code / ".claude" / "skills" / "data-recovery" / "SKILL.md").write_text("SKILL data-recovery", encoding="utf-8")
    (code / ".claude" / "skills" / "fable-voice").mkdir(); (code / ".claude" / "skills" / "fable-voice" / "SKILL.md").write_text("SKILL voice", encoding="utf-8")
    return tmp_path, code

def _task():
    return tf.parse((FIX / "T-0918-03.md").read_text(encoding="utf-8").replace("type: data_fix", "type: data_recovery"))

def test_pick_model_by_type_falls_back_to_default(tmp_path):
    ops, _ = _ops(tmp_path); cfg = json.loads((ops / "agents/alex/config.json").read_text())
    assert worker.pick_model(cfg, "data_recovery") == "claude-opus-5"
    assert worker.pick_model(cfg, "material") == "claude-haiku-4-5-20251001"
    assert worker.pick_model(cfg, "whatever") == "claude-sonnet-5"

def test_review_model_lookup(tmp_path):
    ops, _ = _ops(tmp_path)
    assert worker.review_model_for(ops, "claude-sonnet-5") == "claude-opus-5"
    assert worker.review_model_for(ops, "claude-opus-5") == "claude-fable-5-1"

def test_build_prompt_contains_protocol_role_task_and_skills(tmp_path):
    ops, code = _ops(tmp_path); cfg = json.loads((ops / "agents/alex/config.json").read_text())
    p = worker.build_prompt(ops, code, _task(), cfg)
    assert "PROTOCOL alex T-0918-03 claude-fable-5-1" in p
    assert "# alex" in p and "SKILL data-recovery" in p and "SKILL voice" in p
    assert "五张筛子单加 $1B 市值闸" in p

def test_parse_output_extracts_usage():
    d = worker.parse_output((FIX / "claude_json_output.json").read_text())
    assert d["usage"]["output_tokens"] > 0 and "total_cost_usd" in d and d["is_error"] is False

def test_run_uses_fake_claude_and_reports_timeout(tmp_path):
    ops, code = _ops(tmp_path)
    fake = tmp_path / "claude"; fake.write_text("#!/bin/sh\ncat " + str(FIX / "claude_json_output.json") + "\n"); fake.chmod(0o755)
    r = worker.run(ops, code, _task(), claude_bin=str(fake))
    assert r.ok and r.model == "claude-opus-5" and r.usage["output_tokens"] > 0
    slow = tmp_path / "slow"; slow.write_text("#!/bin/sh\nsleep 5\n"); slow.chmod(0o755)
    r2 = worker.run(ops, code, _task(), timeout_s=1, claude_bin=str(slow))
    assert r2.timed_out and not r2.ok
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_worker.py`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 worker.py**

```python
# tools/worker.py
"""起一个一次性工人：组 prompt → claude -p → 解析 JSON。不碰任务板状态（那是工人自己在 prompt 里做的）。"""
from __future__ import annotations
import json, subprocess
from dataclasses import dataclass, field
from pathlib import Path
from tools import taskfile as tf


@dataclass
class WorkerResult:
    ok: bool
    model: str
    usage: dict = field(default_factory=dict)
    cost_usd: float = 0.0
    session_id: str = ""
    timed_out: bool = False
    stdout_tail: str = ""


def load_cfg(ops_repo: Path, agent: str) -> dict:
    return json.loads((ops_repo / "agents" / agent / "config.json").read_text(encoding="utf-8"))


def pick_model(cfg: dict, task_type: str) -> str:
    tier = cfg.get("type_models", {}).get(task_type, "default")
    return cfg["models"].get(tier, cfg["models"]["default"])


def review_model_for(ops_repo: Path, model: str) -> str:
    table = load_cfg(ops_repo, "ops").get("review_model", {})
    return table.get(model, "claude-opus-5")


def _skills_for(cfg: dict, task_type: str) -> list[str]:
    by = cfg.get("skills_by_type", {})
    return list(dict.fromkeys(by.get(task_type, []) + by.get("*", [])))


def build_prompt(ops_repo: Path, code_repo: Path, task: tf.Task, cfg: dict) -> str:
    agent = task.meta["owner"]
    model = pick_model(cfg, task.meta["type"])
    proto = (ops_repo / "agents" / "_worker_protocol.md").read_text(encoding="utf-8")
    proto = proto.replace("{agent}", agent).replace("{task_id}", task.meta["id"]).replace("{review_model}", review_model_for(ops_repo, model))
    role = (ops_repo / "agents" / agent / "ROLE.md").read_text(encoding="utf-8")
    parts = [proto, "\n\n# ROLE.md\n", role, "\n\n# 任务文件\n", tf.dump(task)]
    for s in _skills_for(cfg, task.meta["type"]):
        p = code_repo / ".claude" / "skills" / s / "SKILL.md"
        if p.exists():
            parts += [f"\n\n# skill: {s}\n", p.read_text(encoding="utf-8")]
    return "".join(parts)


def parse_output(text: str) -> dict:
    return json.loads(text[text.index("{"):])


def run(ops_repo: Path, code_repo: Path, task: tf.Task, timeout_s: int = 2700, claude_bin: str = "claude") -> WorkerResult:
    cfg = load_cfg(ops_repo, task.meta["owner"])
    model = pick_model(cfg, task.meta["type"])
    prompt = build_prompt(ops_repo, code_repo, task, cfg)
    cmd = [claude_bin, "-p", prompt, "--model", model, "--output-format", "json",
           "--permission-mode", "bypassPermissions", "--max-turns", "200"]
    if cfg.get("allowed_tools"):
        cmd += ["--allowedTools", *cfg["allowed_tools"]]
    if cfg.get("disallowed_tools"):
        cmd += ["--disallowedTools", *cfg["disallowed_tools"]]
    try:
        cp = subprocess.run(cmd, cwd=str(code_repo), capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return WorkerResult(ok=False, model=model, timed_out=True, stdout_tail=(e.stdout or "")[-2000:] if isinstance(e.stdout, str) else "")
    try:
        d = parse_output(cp.stdout)
    except (ValueError, json.JSONDecodeError):
        return WorkerResult(ok=False, model=model, stdout_tail=(cp.stdout + cp.stderr)[-2000:])
    return WorkerResult(ok=not d.get("is_error", False) and cp.returncode == 0, model=model,
                        usage=d.get("usage", {}), cost_usd=float(d.get("total_cost_usd", 0.0)),
                        session_id=d.get("session_id", ""), stdout_tail=str(d.get("result", ""))[-2000:])
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest -q tests/test_worker.py`
Expected: `5 passed`

- [ ] **Step 5: 用真 claude 跑一次冒烟（花几分钱额度）**

```bash
cd ~/Documents/fluxus-ops && python3 - <<'PY'
from pathlib import Path
from tools import worker, taskfile as tf
t = tf.parse(Path("tests/fixtures/T-0918-03.md").read_text())
t.meta["type"] = "material"   # 走 haiku
t.body = "## 要做什么\n只回一句「工人流程已读」，不做任何文件改动。\n\n## 验收\n- [x] 无\n"
r = worker.run(Path.home()/"Documents/fluxus-ops", Path.home()/"Documents/AI-Trading-System", t, timeout_s=300)
print(r.ok, r.model, r.usage.get("output_tokens"), r.cost_usd)
PY
```

Expected：`True claude-haiku-4-5-20251001 <正整数> <小数>`

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -q -m "feat(worker): prompt assembly, model by type, claude -p runner with timeout" && git push -q
```

---

### Task 8: 账本与水位线（ledger.py）

**Files:**
- Create: `tools/ledger.py`、`config/budget.json`、`tests/test_ledger.py`

**Interfaces:**
- Produces: `ledger.equiv(model, usage) -> float`（Sonnet 当量：`(input + output + cache_creation + cache_read) × 系数`）；`ledger.record(ops_repo, *, agent, task_id, model, usage, cost_usd, now=None) -> None`（追加到 `ledger/YYYY-Www.jsonl`）；`ledger.weekly_total(ops_repo, now=None) -> float`；`ledger.tier(ops_repo, now=None) -> str`（`full|reduced|floor`）；`budget.json` 形状 `{"weekly_sonnet_equiv": 20000000, "reduced_at": 0.80, "floor_at": 0.95, "coeff": {"claude-opus-5": 5.0, "claude-fable-5-1": 5.0, "claude-sonnet-5": 1.0, "claude-haiku-4-5-20251001": 0.3}}`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_ledger.py
import json, datetime as dt
from tools import ledger

U = {"input_tokens": 100, "output_tokens": 50, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 0}

def _ops(tmp_path):
    (tmp_path / "config").mkdir(); (tmp_path / "ledger").mkdir()
    (tmp_path / "config" / "budget.json").write_text(json.dumps({"weekly_sonnet_equiv": 10000, "reduced_at": 0.8, "floor_at": 0.95,
        "coeff": {"claude-opus-5": 5.0, "claude-sonnet-5": 1.0, "claude-haiku-4-5-20251001": 0.3}}))
    return tmp_path

def test_equiv_applies_coefficient(tmp_path):
    ops = _ops(tmp_path)
    assert ledger.equiv(ops, "claude-sonnet-5", U) == 1150
    assert ledger.equiv(ops, "claude-opus-5", U) == 5750
    assert ledger.equiv(ops, "claude-haiku-4-5-20251001", U) == 345

def test_record_and_weekly_total_and_tiers(tmp_path):
    ops = _ops(tmp_path)
    now = dt.datetime(2026, 9, 18, 10, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    ledger.record(ops, agent="alex", task_id="T-0918-01", model="claude-sonnet-5", usage=U, cost_usd=0.01, now=now)
    assert ledger.weekly_total(ops, now) == 1150 and ledger.tier(ops, now) == "full"
    for _ in range(6):
        ledger.record(ops, agent="alex", task_id="T", model="claude-sonnet-5", usage=U, cost_usd=0.01, now=now)
    assert ledger.weekly_total(ops, now) == 8050 and ledger.tier(ops, now) == "reduced"
    ledger.record(ops, agent="alex", task_id="T", model="claude-sonnet-5", usage=U, cost_usd=0.01, now=now)
    ledger.record(ops, agent="alex", task_id="T", model="claude-sonnet-5", usage=U, cost_usd=0.01, now=now)
    assert ledger.tier(ops, now) == "floor"

def test_next_week_starts_fresh(tmp_path):
    ops = _ops(tmp_path)
    now = dt.datetime(2026, 9, 18, tzinfo=dt.timezone.utc)
    ledger.record(ops, agent="a", task_id="T", model="claude-sonnet-5", usage=U, cost_usd=0, now=now)
    assert ledger.weekly_total(ops, now + dt.timedelta(days=7)) == 0
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_ledger.py`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 ledger.py 与 budget.json**

```python
# tools/ledger.py
"""token 账本：每个工人一行 JSONL，按 ISO 周分文件；水位档由周用量 / 周预算决定。"""
from __future__ import annotations
import datetime as dt, json
from pathlib import Path

JST = dt.timezone(dt.timedelta(hours=9))


def _budget(ops_repo: Path) -> dict:
    return json.loads((ops_repo / "config" / "budget.json").read_text(encoding="utf-8"))


def _week_file(ops_repo: Path, now: dt.datetime) -> Path:
    y, w, _ = now.astimezone(JST).isocalendar()
    return ops_repo / "ledger" / f"{y}-W{w:02d}.jsonl"


def equiv(ops_repo: Path, model: str, usage: dict) -> float:
    tokens = sum(int(usage.get(k, 0)) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    return tokens * float(_budget(ops_repo)["coeff"].get(model, 5.0))


def record(ops_repo: Path, *, agent: str, task_id: str, model: str, usage: dict, cost_usd: float, now: dt.datetime | None = None) -> None:
    now = now or dt.datetime.now(JST)
    row = {"at": now.isoformat(timespec="seconds"), "agent": agent, "task": task_id, "model": model,
           "usage": {k: int(usage.get(k, 0)) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")},
           "equiv": equiv(ops_repo, model, usage), "cost_usd": cost_usd}
    p = _week_file(ops_repo, now); p.parent.mkdir(exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def weekly_total(ops_repo: Path, now: dt.datetime | None = None) -> float:
    p = _week_file(ops_repo, now or dt.datetime.now(JST))
    if not p.exists():
        return 0.0
    return sum(json.loads(l)["equiv"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip())


def tier(ops_repo: Path, now: dt.datetime | None = None) -> str:
    b = _budget(ops_repo)
    frac = weekly_total(ops_repo, now) / float(b["weekly_sonnet_equiv"])
    if frac >= b["floor_at"]:
        return "floor"
    if frac >= b["reduced_at"]:
        return "reduced"
    return "full"
```

`config/budget.json`：

```json
{"weekly_sonnet_equiv": 20000000, "reduced_at": 0.80, "floor_at": 0.95,
 "coeff": {"claude-opus-5": 5.0, "claude-fable-5-1": 5.0, "claude-sonnet-5": 1.0, "claude-haiku-4-5-20251001": 0.3}}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest -q tests/test_ledger.py`
Expected: `3 passed`

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -q -m "feat(ledger): weekly token ledger in sonnet-equivalents; full/reduced/floor tiers" && git push -q
```

---

### Task 9: 守护进程、时刻表、心跳、launchd

**Files:**
- Create: `tools/cronmatch.py`、`tools/daemon.py`、`schedule.json`、`launchd/com.fluxus.ops-daemon.plist`
- Create: `tests/test_cronmatch.py`、`tests/test_daemon.py`

**Interfaces:**
- Consumes: `taskboard.list_tasks/claim/reap/new`、`worker.run`、`ledger.record/tier`、`gitops.sync`。
- Produces: `cronmatch.matches(expr: str, when: datetime) -> bool`；`daemon.tick(ops_repo, code_repo, now, runner=worker.run, state: DaemonState) -> list[str]`（本轮起的任务 id）；`daemon.pick(tasks, running: dict[str,int], tier: str, now) -> list[Task]`；`daemon.fire_schedule(ops_repo, now, last: dict) -> list[str]`；`daemon.write_heartbeat(ops_repo, running, tier, now)`；`daemon.main()` 主循环（60 秒）。`schedule.json` 形状：

```json
[
  {"id": "alex-sentinel", "cron": "0 */2 * * *", "owner": "alex", "type": "failure_triage", "priority": "P0", "title": "数据哨兵巡检", "body": "## 要做什么\n按 failure-triage skill 巡检；健康就 done。\n\n## 验收\n- [ ] runs 日志里有 dashboard 数据日期\n"},
  {"id": "alex-deadline-0700", "cron": "0 7 * * 2-6", "owner": "alex", "type": "failure_triage", "priority": "P0", "title": "死线班 07:00", "body": "..."},
  {"id": "alex-deadline-0800", "cron": "0 8 * * 2-6", "owner": "alex", "type": "failure_triage", "priority": "P0", "title": "死线班 08:00", "body": "..."}
]
```

cron 时刻按 JST 解释。`reduced` 档：只投 owner ∈ {alex, ops} 或 type ∈ {daily_recap, daily_page} 的任务；其余 open 任务只在 09:00 与 21:00 那两轮起。`floor` 档：只起 P0 且 owner=alex，以及 type=daily_page。

- [ ] **Step 1: 写失败测试（cronmatch）**

```python
# tests/test_cronmatch.py
import datetime as dt
from tools.cronmatch import matches
J = dt.timezone(dt.timedelta(hours=9))
def t(h, m, d=18, wd=None): return dt.datetime(2026, 9, d, h, m, tzinfo=J)

def test_star_and_step_and_list_and_range():
    assert matches("0 */2 * * *", t(4, 0)) and not matches("0 */2 * * *", t(5, 0))
    assert matches("0 7,8 * * 2-6", t(7, 0)) and matches("0 7,8 * * 2-6", t(8, 0))
    assert not matches("0 7,8 * * 2-6", t(9, 0))
    assert matches("30 4 * * *", t(4, 30)) and not matches("30 4 * * *", t(4, 31))

def test_weekday_range_uses_cron_numbering():
    # 2026-09-20 是周日 → 0
    assert matches("0 10 * * 0", dt.datetime(2026, 9, 20, 10, 0, tzinfo=J))
    assert not matches("0 10 * * 1-5", dt.datetime(2026, 9, 20, 10, 0, tzinfo=J))
```

- [ ] **Step 2: 写失败测试（daemon）**

```python
# tests/test_daemon.py
import json, datetime as dt, subprocess
from tools import daemon, taskboard as tb, taskfile as tf, worker
from tests.test_taskboard import _repo, BODY

J = dt.timezone(dt.timedelta(hours=9))

def _prep(tmp_path):
    r = _repo(tmp_path)
    (r / "config").mkdir(); (r / "ledger").mkdir(); (r / "state").mkdir()
    (r / "config" / "budget.json").write_text(json.dumps({"weekly_sonnet_equiv": 1000, "reduced_at": 0.8, "floor_at": 0.95, "coeff": {"claude-sonnet-5": 1.0}}))
    for a in ("alex", "claire", "ops"):
        (r / "agents" / a).mkdir(parents=True)
        (r / "agents" / a / "config.json").write_text(json.dumps({"models": {"default": "claude-sonnet-5"}, "max_parallel": 1}))
    (r / "schedule.json").write_text(json.dumps([{"id": "s1", "cron": "0 7 * * *", "owner": "alex", "type": "x", "priority": "P0", "title": "七点班", "body": BODY}]))
    return r

def test_pick_respects_priority_global_and_per_agent_limits(tmp_path):
    r = _prep(tmp_path)
    a1 = tb.new(r, owner="alex", type="x", title="a1", created_by="ops", body=BODY, priority="P2")
    a2 = tb.new(r, owner="alex", type="x", title="a2", created_by="ops", body=BODY, priority="P0")
    c1 = tb.new(r, owner="claire", type="x", title="c1", created_by="ops", body=BODY, priority="P2")
    picked = daemon.pick(tb.list_tasks(r, status="open"), running={}, tier="full", now=dt.datetime.now(J), max_global=3)
    titles = [t.meta["title"] for t in picked]
    assert titles[0] == "a2" and "a1" not in titles          # 每 agent ≤1，P0 先
    assert "c1" not in titles                                 # 有 P0 open 时不起 P2

def test_fire_schedule_creates_task_once_per_minute(tmp_path):
    r = _prep(tmp_path)
    now = dt.datetime(2026, 9, 18, 7, 0, 10, tzinfo=J); last = {}
    assert daemon.fire_schedule(r, now, last) == ["s1"]
    assert daemon.fire_schedule(r, now + dt.timedelta(seconds=30), last) == []
    assert [t.meta["title"] for t in tb.list_tasks(r)] == ["七点班"]

def test_tick_claims_runs_records_and_writes_heartbeat(tmp_path):
    r = _prep(tmp_path); code = tmp_path / "code"; code.mkdir()
    tb.new(r, owner="alex", type="x", title="a", created_by="ops", body=BODY)
    calls = []
    def fake_run(ops_repo, code_repo, task, **kw):
        calls.append(task.meta["id"]); return worker.WorkerResult(ok=True, model="claude-sonnet-5", usage={"output_tokens": 10}, cost_usd=0.0)
    st = daemon.DaemonState()
    started = daemon.tick(r, code, dt.datetime.now(J), runner=fake_run, state=st)
    st.join()
    assert started == calls and tb.list_tasks(r)[0].meta["status"] == "claimed"
    hb = json.loads((r / "state" / "heartbeat.json").read_text())
    assert "at" in hb and hb["tier"] == "full"
    assert (r / "ledger").glob("*.jsonl")

def test_floor_tier_only_runs_alex_p0(tmp_path):
    r = _prep(tmp_path)
    tb.new(r, owner="claire", type="x", title="c", created_by="ops", body=BODY, priority="P0")
    tb.new(r, owner="alex", type="x", title="a", created_by="ops", body=BODY, priority="P1")
    tb.new(r, owner="alex", type="x", title="a0", created_by="ops", body=BODY, priority="P0")
    picked = daemon.pick(tb.list_tasks(r, status="open"), running={}, tier="floor", now=dt.datetime.now(J), max_global=3)
    assert [t.meta["title"] for t in picked] == ["a0"]
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_cronmatch.py tests/test_daemon.py`
Expected: FAIL，模块不存在

- [ ] **Step 4: 实现 cronmatch.py**

```python
# tools/cronmatch.py
"""5 字段 cron 匹配：分 时 日 月 周（0=周日）。支持 * , - */n。"""
from __future__ import annotations
import datetime as dt


def _field_ok(expr: str, value: int, lo: int, hi: int) -> bool:
    for part in expr.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/"); step = int(s)
        if part == "*":
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-"); start, end = int(a), int(b)
        else:
            start = end = int(part)
        if start <= value <= end and (value - start) % step == 0:
            return True
    return False


def matches(expr: str, when: dt.datetime) -> bool:
    m, h, dom, mon, dow = expr.split()
    cron_dow = (when.weekday() + 1) % 7  # python Mon=0 → cron Sun=0
    return (_field_ok(m, when.minute, 0, 59) and _field_ok(h, when.hour, 0, 23) and _field_ok(dom, when.day, 1, 31)
            and _field_ok(mon, when.month, 1, 12) and _field_ok(dow, cron_dow, 0, 6))
```

- [ ] **Step 5: 实现 daemon.py**

```python
# tools/daemon.py
"""主循环：pull → 时刻表 → reap → 挑任务 → 起工人（线程）→ 记账 → 心跳。自己不调用模型。"""
from __future__ import annotations
import datetime as dt, json, os, sys, threading, time
from pathlib import Path
from tools import cronmatch, gitops, ledger, taskboard as tb, taskfile as tf, worker

JST = dt.timezone(dt.timedelta(hours=9))
OPS = Path.home() / "Documents" / "fluxus-ops"
CODE = Path.home() / "Documents" / "AI-Trading-System"
PRIO = {"P0": 0, "P1": 1, "P2": 2}
BATCH_HOURS = (9, 21)


class DaemonState:
    def __init__(self):
        self.running: dict[str, int] = {}      # agent → count
        self.threads: list[threading.Thread] = []
        self.lock = threading.Lock()
        self.last_fired: dict[str, str] = {}

    def join(self):
        for t in self.threads: t.join()


def fire_schedule(ops_repo: Path, now: dt.datetime, last: dict) -> list[str]:
    fired = []
    minute = now.strftime("%Y-%m-%dT%H:%M")
    for entry in json.loads((ops_repo / "schedule.json").read_text(encoding="utf-8")):
        if last.get(entry["id"]) == minute or not cronmatch.matches(entry["cron"], now):
            continue
        tb.new(ops_repo, owner=entry["owner"], type=entry["type"], title=entry["title"], created_by="schedule",
               body=entry["body"], priority=entry.get("priority", "P1"), runtime=entry.get("runtime", "local"), now=now)
        last[entry["id"]] = minute; fired.append(entry["id"])
    return fired


def _allowed(task: tf.Task, tier: str, now: dt.datetime) -> bool:
    m = task.meta
    if m["runtime"] != "local":
        return False
    if tier == "floor":
        return (m["owner"] == "alex" and m["priority"] == "P0") or m["type"] == "daily_page"
    if tier == "reduced":
        if m["owner"] in ("alex", "ops") or m["type"] in ("daily_recap", "daily_page"):
            return True
        return now.hour in BATCH_HOURS
    return True


def pick(tasks: list[tf.Task], running: dict[str, int], tier: str, now: dt.datetime, max_global: int = 3) -> list[tf.Task]:
    tasks = [t for t in tasks if t.meta["status"] == "open" and _allowed(t, tier, now)]
    tasks.sort(key=lambda t: (PRIO[t.meta["priority"]], t.meta["created_at"]))
    p0_open = any(t.meta["priority"] == "P0" for t in tasks)
    picked, used = [], dict(running)
    for t in tasks:
        if len(picked) + sum(running.values()) >= max_global:
            break
        if used.get(t.meta["owner"], 0) >= 1:
            continue
        if p0_open and t.meta["priority"] == "P2":
            continue
        picked.append(t); used[t.meta["owner"]] = used.get(t.meta["owner"], 0) + 1
    return picked


def write_heartbeat(ops_repo: Path, running: dict, tier: str, now: dt.datetime) -> None:
    (ops_repo / "state").mkdir(exist_ok=True)
    (ops_repo / "state" / "heartbeat.json").write_text(json.dumps(
        {"at": now.isoformat(timespec="seconds"), "tier": tier, "running": running, "pid": os.getpid()}, ensure_ascii=False))


def _run_one(ops_repo: Path, code_repo: Path, task: tf.Task, runner, state: DaemonState):
    agent = task.meta["owner"]
    try:
        res = runner(ops_repo, code_repo, task)
        ledger.record(ops_repo, agent=agent, task_id=task.meta["id"], model=res.model, usage=res.usage, cost_usd=res.cost_usd)
        if res.timed_out:
            tb.reap(ops_repo, max_hours=0)   # 立刻回收这件
    finally:
        with state.lock:
            state.running[agent] = max(0, state.running.get(agent, 0) - 1)


def tick(ops_repo: Path, code_repo: Path, now: dt.datetime, runner=worker.run, state: DaemonState | None = None) -> list[str]:
    state = state or DaemonState()
    gitops.sync(ops_repo)
    fire_schedule(ops_repo, now, state.last_fired)
    tb.reap(ops_repo)
    tier = ledger.tier(ops_repo, now)
    with state.lock:
        running = dict(state.running)
    started = []
    for task in pick(tb.list_tasks(ops_repo, status="open"), running, tier, now):
        if not tb.claim(ops_repo, task.meta["id"], by=f"daemon/{task.meta['owner']}"):
            continue
        with state.lock:
            state.running[task.meta["owner"]] = state.running.get(task.meta["owner"], 0) + 1
        task = tf.load(task.path)
        th = threading.Thread(target=_run_one, args=(ops_repo, code_repo, task, runner, state), daemon=True)
        th.start(); state.threads.append(th); started.append(task.meta["id"])
    with state.lock:
        write_heartbeat(ops_repo, dict(state.running), tier, now)
    return started


def main():
    lock = OPS / "state" / "daemon.lock"; lock.parent.mkdir(exist_ok=True)
    if lock.exists() and (time.time() - lock.stat().st_mtime) < 180:
        print("another daemon is alive", file=sys.stderr); sys.exit(1)
    state = DaemonState()
    while True:
        lock.write_text(str(os.getpid()))
        try:
            tick(OPS, CODE, dt.datetime.now(JST), state=state)
        except Exception as e:  # 一轮出错不许死；写进心跳
            (OPS / "state" / "last_error.txt").write_text(f"{dt.datetime.now(JST).isoformat()} {e!r}")
        time.sleep(60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python3 -m pytest -q tests/`
Expected: 全部通过（`25 + 5 + 3 + 2 + 4 = 39 passed`）

- [ ] **Step 7: 写 launchd plist 并装载**

`launchd/com.fluxus.ops-daemon.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.fluxus.ops-daemon</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/caffeinate</string><string>-i</string>
    <string>/usr/bin/env</string><string>python3</string>
    <string>/Users/taolezhu/Documents/fluxus-ops/tools/daemon.py</string>
  </array>
  <key>WorkingDirectory</key><string>/Users/taolezhu/Documents/fluxus-ops</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/Users/taolezhu/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>PYTHONPATH</key><string>/Users/taolezhu/Documents/fluxus-ops</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/taolezhu/Documents/fluxus-ops/state/daemon.out.log</string>
  <key>StandardErrorPath</key><string>/Users/taolezhu/Documents/fluxus-ops/state/daemon.err.log</string>
</dict></plist>
```

```bash
cp launchd/com.fluxus.ops-daemon.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.fluxus.ops-daemon.plist
sleep 70 && cat state/heartbeat.json
```

Expected：heartbeat.json 存在，`at` 在 70 秒内，`tier` 为 `full`。

- [ ] **Step 8: 验收 spec §12 第 2 步：假任务 60 秒内被领；kill 后 10 秒内拉起**

```bash
cd ~/Documents/fluxus-ops
printf '## 要做什么\n只回一句「守护进程验收」，不改文件。\n\n## 验收\n- [x] 无\n' > /tmp/body.md
ID=$(python3 tools/taskboard.py new --owner ops --type material --title "守护进程验收" --created-by ops --body-file /tmp/body.md)
sleep 65 && python3 tools/taskboard.py list --status claimed | grep "$ID"
PID=$(cat state/daemon.lock); kill "$PID"; sleep 10; test "$(cat state/daemon.lock)" != "$PID" && echo RESTARTED
```

Expected：第一行打印该任务为 claimed；第二段打印 `RESTARTED`。记录两次实测秒数，写进 `state/acceptance-step2.txt`。

- [ ] **Step 9: 提交**

```bash
git add -A && git commit -q -m "feat(daemon): 60s loop, schedule, reap, pick with tiers, worker threads, heartbeat, launchd" && git push -q
```

---

### Task 10: ALEX 试点一天（spec §12 第 3 步）

**Files:**
- Modify: `schedule.json`（alex 全部时刻表条目）
- Create: `tasks/`（首日真活）
- Modify（云端）: routine `trig_01QCuAfFpqtYivKM5bbHwEws` 设 `enabled:false`

**Interfaces:**
- Consumes: Task 9 的守护进程、Task 6 的 `data-recovery`/`failure-triage` skill。

- [ ] **Step 1: 写 alex 时刻表**

`schedule.json` 加入：哨兵 `0 */2 * * *`（type failure_triage，P0）；死线班 `0 7 * * 2-6` 与 `0 8 * * 2-6`（同上，title 注「死线班」）；晨检 `20 7 * * 2-6`（type morning_check，P1，正文从 `~/.claude/scheduled-tasks/joe-morning-check/SKILL.md` 搬）；Vercel 周检 `20 9 * * 1`（type vercel_check，P2，正文从 `vercel-storage-weekly/SKILL.md` 搬）。每条 body 的验收节至少一条可打勾项。

- [ ] **Step 2: 停用云端哨兵，停用本机 joe-morning-check 与 vercel-storage-weekly**

在 OPS 会话里：`RemoteTrigger update trig_01QCuAfFpqtYivKM5bbHwEws {"enabled": false}`；`mcp__scheduled-tasks__update_scheduled_task joe-morning-check enabled=false`；同法 `vercel-storage-weekly`。记录停用时刻。

- [ ] **Step 3: 投两件真活**

甲（gate=none）：`coverage_gaps.json` 补记 regime_ledger 缺 09-16 那一场（Zac 09-18 晨报回执节提到）。乙（gate=reviewer）：`pipeline/screeners/breadth_signals.py:405/:420` 两句写死「300+」的散文改按宇宙缩放（Zac 09-18 门铃 ②）。两件都 `taskboard.py new --owner alex ...`，正文验收各两条。同时在 DATA ALEX 聊天会话留一句：这两件归工人，别碰。

- [ ] **Step 4: 观察 24 小时，不开任何会话，不发消息**

09-19 同一时刻核：

```bash
cd ~/Documents/fluxus-ops && git pull -q && python3 tools/taskboard.py list --json | python3 -c "
import json,sys; ts=json.load(sys.stdin)
for t in ts: print(t['id'], t['status'], t['gate'], t['result'][:8], t['created_at'][11:16], t['claimed_at'][11:16])"
ls ledger/ && tail -3 ledger/*.jsonl
git -C ~/Documents/AI-Trading-System log origin/main --since='24 hours ago' --format='%h %ad %s' --date=format-local:%H:%M | grep -i "chore: market data"
```

验收：正班 09-19 数据 08:30 JST 前落 main（上面最后一行时刻 < 08:30）；甲 `done` 且 result 在 main；乙停在分支、状态 `needs_andy` 或 `done`（若审核员 PASS）且 review 字段有四问证据；每件任务 claimed_at − created_at < 70 分钟；账本有每个工人一行。把这五项的实际值写进 `state/acceptance-step3.txt` 并提交。任一不过：停在这里，把卡点原样报给 Andy，不进 Task 11。

---

### Task 11: 其余 7 个 agent 接入，App 定时任务逐个停用（spec §12 第 4 步）

**Files:**
- Modify: `schedule.json`
- Modify（App）: `~/.claude/scheduled-tasks/*` 经 `update_scheduled_task enabled=false`
- Modify（云端）: `trig_01RTGvUGRfr9Uvj3mYPBP3UP`、`trig_01Lfdqys2SthcT7tzjSQzHBw`、`trig_01VBba7MqbetRfctJ6iq711W`、`trig_01UwhQA2SaEWSFEDkyK7dtTZ` 设 `enabled:false`

- [ ] **Step 1: 按下表逐条加入 schedule.json，每加一条先在守护进程下跑成一次，再停对应旧任务**

| 旧任务 | 新条目 owner / type / cron(JST) | 停用方式 |
|---|---|---|
| zac-night-study | linda / night_research / `30 4 * * *` | update_scheduled_task |
| recap-daily | ops / daily_recap / `0 9 * * 2-6` | update_scheduled_task |
| recap-weekly | ops / weekly_recap / `0 10 * * 0` | update_scheduled_task |
| ops-vault-daily-question | ops / vault_question / `10 9 * * *` | update_scheduled_task |
| steve-content-daily-push | steve / content_daily / `25 9 * * *` | update_scheduled_task |
| steve-content-weekly-batch | steve / content_weekly / `0 20 * * 0` | update_scheduled_task |
| growth-weekly-ledger | gary / growth_ledger / `40 9 * * 1` | update_scheduled_task |
| 云端 INBOX 月度归档 | ops / archive / `30 12 1 * *` | RemoteTrigger enabled:false |
| 云端仓库周检 | ops / weekly_check / `0 8 * * 1` | RemoteTrigger enabled:false |
| 云端 Discord→X 草稿 | steve / discord_to_x / `40 5 * * 2-6` | RemoteTrigger enabled:false |
| 云端每日页 | 见 Task 12（runtime=app） | RemoteTrigger enabled:false |
| （新增，spec §10.3）| ops / board_patrol / `0 10 * * *`，type_models 里映射 mechanical（Haiku）；正文：列出 blocked 任务与 owner 和改动路径明显不符的任务，用 `taskboard.py handoff` 改派，needs_andy 超 3 天的在 runs 日志里点名 | 无旧任务 |

留在 App 不动：`steve-x-daily-watch`、`steve-x-nightcap`（runtime=app，产出后由该任务自己 `taskboard.py done`）、`personal-*`、`remind-3d-effects-direction`。

- [ ] **Step 2: 每停一个，记录 `state/acceptance-step4.txt`：旧任务名、新条目 id、首次在守护进程下 done 的任务 id 与时刻**

- [ ] **Step 3: 提交 schedule.json**

```bash
git add schedule.json state/acceptance-step4.txt && git commit -q -m "feat(schedule): all eight agents on the daemon; app tasks disabled" && git push -q
```

---

### Task 12: 每日页读任务板；项目层四个文件（spec §12 第 6 步）

**Files:**
- Create: `tools/dailypage.py`、`tests/test_dailypage.py`
- Create: `projects/{course,dashboard-membership,marketing,growth}.md`
- Create（App 定时任务）: `fable-daily-page-local`，10:07 JST，runtime=app，prompt 固定：读 `~/Documents/fluxus-ops/state/dailypage.json`，按 `daily-page` skill 渲染成 artifact 并发到 Andy 面前

**Interfaces:**
- Produces: `dailypage.build(ops_repo, now) -> dict`，形状：

```json
{"heartbeat": {"ok": true, "age_min": 1, "tier": "full", "week_pct": 12.4, "slowest_claim_min_yesterday": 3},
 "dashboard": {"data_date": "2026-09-18", "landed_before_0830": true},
 "projects": [{"name": "课程", "days_left": 2, "done": 5, "open": 3, "metric": {"name": "首周付费人数", "value": null}}],
 "agents": [{"agent": "alex", "done_yesterday": 6, "blocked": 0}],
 "needs_andy": [{"id": "T-0918-07", "question": "合不合 feat/x？", "days": 1}]}
```

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dailypage.py
import json, datetime as dt
from tools import dailypage, taskboard as tb
from tests.test_daemon import _prep, BODY
J = dt.timezone(dt.timedelta(hours=9))

def test_build_reports_heartbeat_age_needs_andy_and_slowest_claim(tmp_path):
    r = _prep(tmp_path)
    now = dt.datetime(2026, 9, 19, 10, 7, tzinfo=J)
    (r / "state" / "heartbeat.json").write_text(json.dumps({"at": (now - dt.timedelta(minutes=3)).isoformat(), "tier": "full", "running": {}}))
    (r / "projects").mkdir(); (r / "projects" / "course.md").write_text("---\nname: 课程\ndeadline: 2026-09-21\nmetric: 首周付费人数\n---\n")
    y = now - dt.timedelta(days=1)
    t = tb.new(r, owner="alex", type="x", title="a", created_by="ops", body=BODY, now=y.replace(hour=5, minute=0))
    tb.claim(r, t.meta["id"], by="w")   # claimed_at = 现在，测试里用 now 覆盖不了；改用 meta 直接写
    def fix(x): x.meta["claimed_at"] = y.replace(hour=5, minute=42).isoformat(timespec="seconds"); x.meta["project"] = "course"
    from tools import gitops; gitops.atomic(r, t.path, fix, "fix")
    u = tb.new(r, owner="ops", type="x", title="合不合", created_by="ops", body=BODY, now=now - dt.timedelta(days=2))
    tb.needs_andy(r, u.meta["id"], "合不合 feat/x？")
    d = dailypage.build(r, now)
    assert d["heartbeat"]["ok"] and d["heartbeat"]["age_min"] == 3
    assert d["heartbeat"]["slowest_claim_min_yesterday"] == 42
    assert d["needs_andy"][0]["question"] == "合不合 feat/x？" and d["needs_andy"][0]["days"] == 2
    assert d["projects"][0]["name"] == "课程" and d["projects"][0]["days_left"] == 2 and d["projects"][0]["open"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_dailypage.py`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 dailypage.py**

```python
# tools/dailypage.py
"""每日页的数据：只从任务板、心跳、账本、projects/ 算，不读收件箱。写 state/dailypage.json。"""
from __future__ import annotations
import datetime as dt, json, subprocess, sys
from pathlib import Path
from tools import ledger, taskboard as tb, taskfile as tf

JST = dt.timezone(dt.timedelta(hours=9))
CODE = Path.home() / "Documents" / "AI-Trading-System"


def _projects(ops_repo: Path, tasks: list[tf.Task], now: dt.datetime) -> list[dict]:
    out = []
    for p in sorted((ops_repo / "projects").glob("*.md")) if (ops_repo / "projects").exists() else []:
        meta = tf.parse(p.read_text(encoding="utf-8")).meta
        mine = [t for t in tasks if t.meta["project"] == p.stem]
        deadline = dt.date.fromisoformat(meta["deadline"])
        out.append({"name": meta["name"], "days_left": (deadline - now.date()).days,
                    "done": sum(t.meta["status"] == "done" for t in mine),
                    "open": sum(t.meta["status"] in ("open", "claimed") for t in mine),
                    "metric": {"name": meta.get("metric", ""), "value": meta.get("metric_value") or None}})
    return out


def _dashboard(now: dt.datetime) -> dict:
    try:
        log = subprocess.run(["git", "-C", str(CODE), "log", "origin/main", "--grep=chore: market data", "-1", "--format=%s|%cI"],
                             capture_output=True, text=True, check=True).stdout.strip()
        subject, ci = log.split("|")
        data_date = subject.split("market data")[1].strip()[:10]
        landed = dt.datetime.fromisoformat(ci).astimezone(JST)
        before = landed.date() < now.date() or landed.time() <= dt.time(8, 30)
        return {"data_date": data_date, "landed_at": landed.isoformat(timespec="minutes"), "landed_before_0830": before}
    except Exception as e:
        return {"data_date": None, "error": repr(e)}


def build(ops_repo: Path, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(JST)
    tasks = tb.list_tasks(ops_repo)
    hb_path = ops_repo / "state" / "heartbeat.json"
    hb = json.loads(hb_path.read_text()) if hb_path.exists() else {}
    age = (now - dt.datetime.fromisoformat(hb["at"])).total_seconds() / 60 if hb else 1e9
    yday = (now - dt.timedelta(days=1)).date()
    lat = [(dt.datetime.fromisoformat(t.meta["claimed_at"]) - dt.datetime.fromisoformat(t.meta["created_at"])).total_seconds() / 60
           for t in tasks if t.meta["claimed_at"] and dt.datetime.fromisoformat(t.meta["created_at"]).date() == yday]
    budget = json.loads((ops_repo / "config" / "budget.json").read_text())
    agents = {}
    for t in tasks:
        a = agents.setdefault(t.meta["owner"], {"agent": t.meta["owner"], "done_yesterday": 0, "blocked": 0})
        if t.meta["status"] == "done" and t.meta["closed_at"] and dt.datetime.fromisoformat(t.meta["closed_at"]).date() == yday:
            a["done_yesterday"] += 1
        if t.meta["status"] == "blocked":
            a["blocked"] += 1
    needs = [{"id": t.meta["id"], "question": t.meta["review"].removeprefix("ASK ").strip(),
              "days": (now - dt.datetime.fromisoformat(t.meta["created_at"])).days}
             for t in tasks if t.meta["status"] == "needs_andy"][:5]
    return {"heartbeat": {"ok": age <= 10, "age_min": round(age), "tier": hb.get("tier", "?"),
                          "week_pct": round(100 * ledger.weekly_total(ops_repo, now) / budget["weekly_sonnet_equiv"], 1),
                          "slowest_claim_min_yesterday": round(max(lat)) if lat else None},
            "dashboard": _dashboard(now), "projects": _projects(ops_repo, tasks, now),
            "agents": sorted(agents.values(), key=lambda x: x["agent"]), "needs_andy": needs}


if __name__ == "__main__":
    ops = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Documents" / "fluxus-ops"
    d = build(ops)
    (ops / "state" / "dailypage.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(d, ensure_ascii=False, indent=1))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m pytest -q tests/test_dailypage.py`
Expected: `1 passed`

- [ ] **Step 5: 写四个项目文件**

`projects/course.md`：`name: 课程` `deadline: 2026-09-20` `rule: 到期未发就降级，PDF 照发，交互课件后补` `metric: 首周付费人数`（Andy NOW.md 09-17）。`dashboard-membership.md`：`name: dashboard 会员化` `deadline:`（Andy 定，先写 `2026-12-31` 并在正文标明「待 Andy 定」不是占位，是显式默认值）`metric: 付费会员数`。`marketing.md`：`name: 市场营销` `deadline: 2026-09-30` `metric: 每周发布件数`（关卡制 5/周）。`growth.md`：`name: 会员增长` `deadline: 2026-12-31` `metric: 付费会员数`（gary 的 metrics.csv 是数字权威）。

- [ ] **Step 6: 加 schedule.json 条目 `ops / daily_page / "5 10 * * *"`（跑 `python3 tools/dailypage.py` 写 dailypage.json），并创建 App 定时任务 `fable-daily-page-local`（10:07 JST，prompt：读 `state/dailypage.json`，按 daily-page skill 渲染成 artifact 更新到既有每日页 URL）。验收：10:07 出的页面顶部四行全部来自 dailypage.json。**

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -q -m "feat(dailypage): data from taskboard/heartbeat/ledger/projects; four project files" && git push -q
```

---

### Task 13: 宪法重写与旧机制退役（spec §12 第 7 步）

**Files:**
- Modify（代码仓库）: `CLAUDE.md`（整体重写，≤40 行）
- Delete（代码仓库）: `pipeline/tools/doorbells.py`、`pipeline/tools/federation_board.py`、`pipeline/tests/test_doorbells.py`、对应 board 测试
- Modify（代码仓库）: `data/research/night_reports/INBOX.md` 顶部加一段「本箱自 2026-09-xx 起只收晨报与事故报告；派活去任务板」
- Modify（代码仓库）: `TEAM.md` 花名册改为 8 个职能 agent + ops，班次名删除，指向 fluxus-ops 的 ROLE.md
- Modify（共享记忆）: `~/.claude/projects/-Users-taolezhu-Documents-AI-Trading-System/memory/`：删除 `project_data_side_claimed.md`、`user_identity_this_session_is_linda.md`、`pitfall_shared_memory_hijacks_identity.md` 里的身份断言；`pitfall_*` 与 `index_pitfalls.md`、`pitfalls.md` 移入 `_archive/`；MEMORY.md 重写为 30 行以内（项目概览、Key Files、方法索引、指向 fluxus-ops）

**Interfaces:**
- Consumes: Task 3–12 全部就位并跑过一周（Task 14 的三个数已有读数）才执行本任务。

- [ ] **Step 1: 写新 CLAUDE.md（全文，40 行）**

```markdown
# 全会话必守（Fluxus，2026-09 v2）

**你是谁**：看会话标题；对应 `~/Documents/fluxus-ops/agents/<name>/ROLE.md`。开工第一动作：读它，再 `python3 ~/Documents/fluxus-ops/tools/taskboard.py list --owner <name> --status open`。

**活只在任务板上**：派活、接活、转交、完成，全部经 `taskboard.py`；不写门铃、不发消息、不在收件箱派活。收件箱只收晨报与事故报告。

**Andy 的话当场落盘**：他说「以后这样做」→ 同一轮逐字写进你的 ROLE.md 或 memory 并 push fluxus-ops；关于公共 skill 的纠正 → 开任务给该 skill 的 owner。他回「y / 加 / 不做」→ 对应 `done / close`。

**改代码仓库**：永不在共享主树 commit；一律临时工作树；只 add 你改的文件；提交前 `git diff --cached --name-only` 数一遍。gate 由 `taskboard.py gate` 按路径判：none 直接合，reviewer 过审核员（`.claude/skills/branch-review`），andy 停下。

**归 Andy 的**：花钱、对外发布（X / Substack / vercel --prod）、删数据、会员数据。工人触到就 `taskboard.py needs-andy`。

**数据死线**：最近完成交易日的数据 JST 08:30 前落 main 并上线；出错即 P0，谁发现谁修（Andy 09-17「Dashboard出现错误，一定要马上紧急修补」）。修好后归档补齐、复盘重跑、核线上，三件都做完才 done。

**仓库是公开的**：会员名、股数、金额、字幕、PDF 永不进代码仓库；敏感的东西在 fluxus-ops（私有）。

**语言与交付**：中文回复；先一句结论；要 Andy 拍板的事走任务板 needs_andy，出现在每日页；给他看的是页面、图、PDF，不是 .md 链接。

**时间**：交易日用 `pipeline.marketcal`（ET）；说时刻先 `date`；给 Andy 的时刻双标 JST+ET。

**改本文件**：只有 commit message 逐字引 Andy 原话才可直接合；否则写任务给 ops，gate=reviewer。

**完成的定义**：`taskboard.py done` 放行。别的都不算。

**收工**：把本次做了什么、结论、下一步写进 `agents/<name>/runs/`；未推的提交不许留。

设计与理由：`docs/superpowers/specs/2026-09-18-agent-fleet-v2-design.md`。旧宪法（236 行）存档：`data/reference/proposals/2026-09-18_constitution_v1_archived.md`。
```

- [ ] **Step 2: 旧宪法存档 + 删除两个工具 + INBOX 顶注 + TEAM.md 改写，一个提交，走临时工作树，gate=reviewer，提交信息引 Andy 原话**

```bash
cd ~/Documents/AI-Trading-System && git fetch -q origin
export WT=$(mktemp -d)/wt-constitution && git worktree add -q --detach "$WT" origin/main
git -C "$WT" show origin/main:CLAUDE.md > "$WT/data/reference/proposals/2026-09-18_constitution_v1_archived.md"
# 写入新 CLAUDE.md、改 TEAM.md、INBOX 顶注；git rm 两个工具及其测试
git -C "$WT" rm -q pipeline/tools/doorbells.py pipeline/tools/federation_board.py pipeline/tests/test_doorbells.py
grep -rl "doorbells\|federation_board" "$WT/pipeline" "$WT/.claude" "$WT/tests" || true   # 引用处逐个清
cd "$WT" && ~/Documents/AI-Trading-System/.venv/bin/python -m pytest -q pipeline/tests tests --deselect pipeline/tests/test_content_processor.py | tail -2
wc -l CLAUDE.md   # 必须 ≤ 40
git add -A && git commit -q -F - <<'M'
constitution v2: 40 行；任务板取代门铃/看板/契约行派活；旧宪法存档

Andy 2026-09-18 批 agent fleet v2 spec，原话：「可以，我直接批了。」
删除：pipeline/tools/doorbells.py、federation_board.py 及测试（spec §11 退役清单）。
M
git push -q origin HEAD:main && git worktree remove --force "$WT"
```

审核员：本提交 gate=reviewer，由 ops 工人按 Task 6 的 branch-review 流程审（在任务板上开一件 type=constitution 的任务，让工人执行本步而不是手工推）。

- [ ] **Step 3: 共享记忆归档**

```bash
M=~/.claude/projects/-Users-taolezhu-Documents-AI-Trading-System/memory
mkdir -p "$M/_archive" && git -C "$M" init -q 2>/dev/null || true
mv "$M"/pitfall_*.md "$M/index_pitfalls.md" "$M/pitfalls.md" "$M/_archive/"
rm "$M/project_data_side_claimed.md" "$M/user_identity_this_session_is_linda.md"
```

重写 `MEMORY.md`（≤30 行）：项目概览、Key Files、方法索引（`method_*` 保留）、一行「身份与规矩在 fluxus-ops/agents/<name>/」。有价值的坑由各 agent 在 Task 11 之后自己挑进 ROLE.md 或 skill，不在本步集中搬。

- [ ] **Step 4: 验收**

`wc -l ~/Documents/AI-Trading-System/CLAUDE.md` ≤ 40；一周后 `grep -c '^🔔' data/research/night_reports/INBOX.md` 与本步前相同（零新门铃）。

---

### Task 14: 第一周三个数（spec §13）

**Files:**
- Create: `tools/metrics.py`、`tests/test_metrics.py`
- Modify: `tools/dailypage.py`（heartbeat 节加 `reviewer_reject_pct`）

**Interfaces:**
- Produces: `metrics.week(ops_repo, now) -> dict`：`{"slowest_claim_min": int, "weekly_equiv": float, "budget_pct": float, "reviewer_total": int, "reviewer_fail": int, "reviewer_reject_pct": float}`；`python3 tools/metrics.py` 打印并写 `state/metrics-YYYY-Www.json`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_metrics.py
import datetime as dt
from tools import metrics, taskboard as tb, gitops
from tests.test_daemon import _prep, BODY
J = dt.timezone(dt.timedelta(hours=9))

def test_week_metrics(tmp_path):
    r = _prep(tmp_path); now = dt.datetime(2026, 9, 25, 10, 0, tzinfo=J)
    t1 = tb.new(r, owner="claire", type="x", title="a", created_by="ops", body=BODY, now=now - dt.timedelta(days=1))
    t2 = tb.new(r, owner="claire", type="x", title="b", created_by="ops", body=BODY, now=now - dt.timedelta(days=2))
    for t, mins in ((t1, 7), (t2, 61)):
        def fix(x, mins=mins): x.meta["claimed_at"] = (dt.datetime.fromisoformat(x.meta["created_at"]) + dt.timedelta(minutes=mins)).isoformat(timespec="seconds"); x.meta["gate"] = "reviewer"
        gitops.atomic(r, t.path, fix, "fix")
    tb.review(r, t1.meta["id"], "PASS", "ok"); tb.review(r, t2.meta["id"], "FAIL", "no")
    m = metrics.week(r, now)
    assert m["slowest_claim_min"] == 61 and m["reviewer_total"] == 2 and m["reviewer_fail"] == 1 and m["reviewer_reject_pct"] == 50.0
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m pytest -q tests/test_metrics.py`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 metrics.py**

```python
# tools/metrics.py
from __future__ import annotations
import datetime as dt, json, sys
from pathlib import Path
from tools import ledger, taskboard as tb

JST = dt.timezone(dt.timedelta(hours=9))


def week(ops_repo: Path, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(JST)
    since = now - dt.timedelta(days=7)
    tasks = [t for t in tb.list_tasks(ops_repo) if dt.datetime.fromisoformat(t.meta["created_at"]) >= since]
    lat = [(dt.datetime.fromisoformat(t.meta["claimed_at"]) - dt.datetime.fromisoformat(t.meta["created_at"])).total_seconds() / 60
           for t in tasks if t.meta["claimed_at"]]
    reviewed = [t for t in tasks if t.meta["gate"] == "reviewer" and t.meta["review"][:4] in ("PASS", "FAIL")]
    fails = sum(t.meta["review"].startswith("FAIL") for t in reviewed)
    budget = json.loads((ops_repo / "config" / "budget.json").read_text())["weekly_sonnet_equiv"]
    total = ledger.weekly_total(ops_repo, now)
    return {"slowest_claim_min": round(max(lat)) if lat else None, "weekly_equiv": total,
            "budget_pct": round(100 * total / budget, 1), "reviewer_total": len(reviewed), "reviewer_fail": fails,
            "reviewer_reject_pct": round(100 * fails / len(reviewed), 1) if reviewed else 0.0}


if __name__ == "__main__":
    ops = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Documents" / "fluxus-ops"
    now = dt.datetime.now(JST); m = week(ops, now)
    y, w, _ = now.isocalendar()
    (ops / "state" / f"metrics-{y}-W{w:02d}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
    print(json.dumps(m, ensure_ascii=False))
```

- [ ] **Step 4: 跑测试确认通过；在 dailypage.build 的 heartbeat 节加 `"reviewer_reject_pct": metrics.week(ops_repo, now)["reviewer_reject_pct"]`**

Run: `python3 -m pytest -q tests/`
Expected: 全部通过

- [ ] **Step 5: 一周后（Task 11 完成 + 7 天）跑并校准预算**

```bash
cd ~/Documents/fluxus-ops && python3 tools/metrics.py
```

判据：`slowest_claim_min` < 60（Andy 可接受上限）；`budget_pct` 按实测把 `config/budget.json` 的 `weekly_sonnet_equiv` 改成「实测周用量 ÷ 实际到达 80% 时的用量比例」得到的真实预算，提交并在提交信息里写明实测数；`reviewer_reject_pct` 记录，不设阈值。任一量不出：写 `state/metrics-note.md` 说明原因，回到 spec 改设计。

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -q -m "feat(metrics): first-week numbers; budget calibrated from measured usage" && git push -q
```

---

## Self-Review

**Spec coverage**
- §4 私有仓库 → Task 1。§5 任务板字段/状态机/done 定义/工具/旧信箱 → Task 1、3、4、13。§6 agent 目录/身份/裁决落盘/ROLE 上限/记忆三层/skill → Task 5、6、13（裁决落盘的收工比对在 task-protocol skill 里是文字约定，未做成 hook；spec §6.3 说「工具比对」——**gap**：补一条到 Task 6 Step 3 的 task-protocol：收工前跑 `git -C ~/Documents/fluxus-ops diff --stat HEAD~5` 自查，并在 Task 14 后视需要升级为 Stop hook）。§7 守护进程/工人/并发/失效/App 任务 → Task 7、9、11。§8 审核员 → Task 2（gate）、6（branch-review）、7（review_model 交叉）、4（review 动作）。§9 账本/三档/模型 → Task 8、5、7。§10 每日页/项目层/OPS 巡检 → Task 12（每日页、项目）；**OPS 每日巡检**（回收、改派错 owner、needs_andy 天数）→ 回收在 daemon.tick 每轮做，天数在 dailypage；「改派错 owner」未覆盖——**gap**：加入 Task 11 的 schedule.json 一条 `ops / board_patrol / "0 10 * * *"`（Haiku，正文：列 blocked 与 owner 明显不符的任务，用 handoff 改派）。§11 退役 → Task 11、13。§12 七步 → Task 1–13 逐步对应。§13 三个数 → Task 14。§14 会员路径 gate=andy → Task 2 的 `ANDY_PREFIXES`；禁止会员信息入库 → 工人 protocol 第 10 条（文字约定，spec 说「要变成工具拒绝」——第一版靠 gate=andy 的路径前缀兜底，Task 14 后评估是否加内容扫描）。

**Placeholder scan**：`dashboard-membership.md` 的 deadline 用显式默认值 `2026-12-31` 并标明待 Andy 定；无 TBD/TODO。

**Type consistency**：`taskboard.new(..., now=)` 参数在 Task 3 定义、Task 9/12/14 使用一致；`worker.WorkerResult` 字段 `ok/model/usage/cost_usd/session_id/timed_out/stdout_tail` 在 Task 7、9 一致；`gitops.atomic` 签名一致；`ledger.record(ops_repo, *, agent, task_id, model, usage, cost_usd, now)` 在 8、9 一致；`review()` 的 FAIL 逻辑与 `reap()` 的 attempts 逻辑同为「≥2 → blocked」。

**已按 self-review 修正**：Task 6 Step 3 的 task-protocol 加收工自查一句；Task 11 表加 `ops / board_patrol` 一行。
