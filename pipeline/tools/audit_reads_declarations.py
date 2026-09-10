#!/usr/bin/env python3
"""双向声明对账闸 —— 「谁读：X」的另一头必须真的登记了它。

Andy 2026-09-10 批（原话「ok」，回应 MAINTENANCE_2026-09-10 §七的提案）。

**它管的那个 bug**：内容产线里，被读方在自己头部写「谁读：信号站」，
而信号站的契约 reads 清单里没有它。断裂方向永远是同一个，而且
**没有任何计数维度会因为它变红**——两份文件各自都读得通，清单看起来始终是满的。
09-10 全查一次逮到三处（performance.md / verdicts.jsonl / signals.md 优先级清单）。

**判据**：任何 markdown 在头部（前 HEADER_LINES 行）的引用块里写了「谁读：<站名>」，
那个站的角色契约的 **reads 段**里就必须出现这个文件的路径。

站名 → 契约文件的映射**从 roles/ 目录的 H1 现读**，不写死——
写死的表量的是我的词汇量，不是仓库的实际情况
（坑账 pitfall_a_handwritten_whitelist_measures_my_vocabulary）。

用法:
    python3 pipeline/tools/audit_reads_declarations.py            # 扫 origin/main 权威版
    python3 pipeline/tools/audit_reads_declarations.py --rev WORKTREE   # 提交前扫工作区
退出码: 0 = 全部对上; 1 = 有断裂; 2 = 工具自身没法跑（比如找不到 roles/）
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROLES_DIR = "Fluxus_Brand/ops/campaigns/roles"
HEADER_LINES = 10          # 只认头部声明；正文里讨论这个规矩的不算
DECL_RE = re.compile(r"谁读[：:]\s*(.+)")
# 站名之间的分隔符：中文间隔号、顿号、斜杠、加号
SPLIT_RE = re.compile(r"[·、/＋+]")
# reads 段：从 **reads** 到下一个 **xxx** 段标题
READS_RE = re.compile(r"\*\*reads\*\*[：:]?(.*?)(?=\n\*\*[^*]+\*\*[：:])", re.S)

# 不在 roles/ 里、因而本闸查不了的读者（留痕，不当成通过）
OUT_OF_REPO = {
    "日推": "~/.claude/scheduled-tasks/steve-content-daily-push/SKILL.md（repo 外）",
}
# H1 里取不到的别名 → 站名
ALIASES = {"Gate": "审查站", "审查站（Gate）": "审查站"}

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".venv", "venv",
    "code-cartography-workspace", "__pycache__", ".impeccable",
}


@dataclass
class Finding:
    kind: str          # "broken" | "weak" | "uncheckable"
    declarer: str
    station: str
    detail: str


WORKTREE = "WORKTREE"   # 特殊 rev：扫工作区，让它能当提交前的闸用


def _git_show(root: Path, rev: str, path: str) -> str | None:
    if rev == WORKTREE:
        f = root / path
        try:
            return f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
    try:
        return subprocess.run(
            ["git", "-C", str(root), "show", f"{rev}:{path}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None


def _git_ls(root: Path, rev: str) -> list[str]:
    if rev == WORKTREE:
        # 已跟踪 + 未跟踪（新加的声明文件也要查），不含被忽略的
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others",
             "--exclude-standard"],
            capture_output=True, text=True, check=True,
        ).stdout
        return sorted({p for p in out.splitlines()
                       if p.endswith(".md") and (root / p).is_file()})
    out = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "--name-only", rev],
        capture_output=True, text=True, check=True,
    ).stdout
    return [p for p in out.splitlines() if p.endswith(".md")]


def station_contracts(root: Path, rev: str) -> dict[str, str]:
    """从 roles/*.md 的 H1 现读站名，不写死。'# ① 信号站 · Signal Scout' → '信号站'"""
    table: dict[str, str] = {}
    for path in _git_ls(root, rev):
        if not path.startswith(ROLES_DIR + "/"):
            continue
        text = _git_show(root, rev, path)
        if not text:
            continue
        first = next((ln for ln in text.splitlines() if ln.startswith("# ")), "")
        # 去掉编号圈字与英文别名，取第一个中文站名
        m = re.search(r"([一-鿿]+站)", first)
        if m:
            table[m.group(1)] = path
    for alias, real in ALIASES.items():
        if real in table:
            table[alias] = table[real]
    return table


def declarations(root: Path, rev: str) -> list[tuple[str, list[str]]]:
    """返回 [(声明文件路径, [站名...])]，只认头部引用块里的声明。"""
    out: list[tuple[str, list[str]]] = []
    for path in _git_ls(root, rev):
        if any(seg in SKIP_DIRS for seg in Path(path).parts):
            continue
        text = _git_show(root, rev, path)
        if not text:
            continue
        for line in text.splitlines()[:HEADER_LINES]:
            if not line.lstrip().startswith(">"):
                continue          # 头部**引用块**才是声明；正文提到不算
            m = DECL_RE.search(line)
            if not m:
                continue
            tail = m.group(1)
            # 「谁读：A · B。谁写：…」——谁写之后的不要
            tail = re.split(r"谁写[：:]", tail)[0]
            names: list[str] = []
            for chunk in SPLIT_RE.split(tail):
                chunk = re.sub(r"[（(].*?[)）]", "", chunk)          # 去括号说明
                chunk = chunk.strip(" 。.，,；;**`")
                hit = re.search(r"([一-鿿]+站|Gate|日推)", chunk)
                if hit:
                    names.append(hit.group(1))
            if names:
                out.append((path, names))
            break
    return out


def reads_block(contract_text: str) -> str | None:
    m = READS_RE.search(contract_text)
    return m.group(1) if m else None


def path_forms(path: str) -> list[str]:
    """由强到弱的引用写法：全路径 → 后两段 → 文件名。"""
    parts = Path(path).parts
    forms = [path]
    if len(parts) >= 2:
        forms.append("/".join(parts[-2:]))
    forms.append(parts[-1])
    seen, out = set(), []
    for f in forms:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def audit(root: Path, rev: str) -> list[Finding]:
    table = station_contracts(root, rev)
    if not table:
        print(f"❌ 找不到任何角色契约（{ROLES_DIR}），工具没法跑", file=sys.stderr)
        sys.exit(2)

    findings: list[Finding] = []
    contract_cache: dict[str, str] = {}

    for declarer, stations in declarations(root, rev):
        if declarer.startswith(ROLES_DIR):
            continue                      # 契约自己不参与
        for station in stations:
            if station in OUT_OF_REPO:
                findings.append(Finding(
                    "uncheckable", declarer, station,
                    f"读者的契约在 {OUT_OF_REPO[station]}，本闸查不到——不算通过",
                ))
                continue
            contract = table.get(station)
            if contract is None:
                findings.append(Finding(
                    "uncheckable", declarer, station,
                    "roles/ 里没有这个站的契约（站名写错？还是这个站不存在？）",
                ))
                continue
            text = contract_cache.get(contract) or _git_show(root, rev, contract) or ""
            contract_cache[contract] = text
            block = reads_block(text)
            if block is None:
                findings.append(Finding(
                    "uncheckable", declarer, station,
                    f"{contract} 里找不到 **reads** 段",
                ))
                continue
            forms = path_forms(declarer)
            hit = next((f for f in forms if f in block), None)
            if hit is None:
                where = "（该契约别处也没提到它）"
                if any(f in text for f in forms):
                    where = "⚠️ 契约别处提到了它，但**不在 reads 段里**"
                findings.append(Finding(
                    "broken", declarer, station,
                    f"{contract} 的 reads 段里没有它 {where}",
                ))
            elif hit != declarer and hit == Path(declarer).name:
                findings.append(Finding(
                    "weak", declarer, station,
                    f"{contract} 的 reads 段只写了文件名 `{hit}`，没写路径——同名文件会误判为已登记",
                ))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="仓库根")
    ap.add_argument("--rev", default="origin/main",
                    help="查哪个版本：默认 origin/main 权威版；`WORKTREE` 扫未提交的工作区（提交前的闸）；也可给任意 commit")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    findings = audit(root, args.rev)
    broken = [f for f in findings if f.kind == "broken"]
    weak = [f for f in findings if f.kind == "weak"]
    unchk = [f for f in findings if f.kind == "uncheckable"]

    for label, group, mark in (
        ("断裂", broken, "❌"), ("弱引用", weak, "⚠️"), ("查不了", unchk, "ⓘ"),
    ):
        if not group:
            continue
        print(f"\n{mark} {label} {len(group)} 条：")
        for f in group:
            print(f"  {f.declarer}  声明「谁读：{f.station}」")
            print(f"      → {f.detail}")

    total = len(findings)
    print(f"\n{'—' * 60}")
    print(f"扫 {args.rev}：断裂 {len(broken)} · 弱引用 {len(weak)} · 查不了 {len(unchk)}")
    if not total:
        print("✅ 每一条「谁读：X」，X 的 reads 段里都登记了它。")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
