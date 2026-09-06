"""部署成本审计 —— 让「存储要爆了」由我们自己发现,不靠厂商发邮件。

2026-09-06 事故本体:Vercel 来信说存储接近上限,一查是 **125.62 GB**(上限 10 GB)。
根因不是内容多,是**触发器比内容变得频繁**:14 天里 main 上 781 次 commit 触发了
781 次生产部署,其中 725 次(92%)改的是研究笔记/契约行/品牌稿/测试——一个字节
都不进产物,却每次照样存下约 75 MB。

没有任何一个环节量过这件事。每条 commit 单独看都是对的,每次部署单独看也是对的;
坏的是**乘积**,而乘积没有主人。这个工具就是那个主人。

三项检查:

  D1  闸还在不在,且看的是对的路径。`vercel.json` 的 ignoreCommand 与它调用的脚本
      可能被删、被改;更隐蔽的是**产物里多了一个闸不看的路径**——那一天起该路径
      变了也不会重新部署,线上就静默停在旧版。所以不是查「有没有闸」(那是个 bool),
      是查「闸的看管范围是否覆盖了产物的每一个来源」。
  D2  预算。产物大小 × 部署频次 × 保留天数 = 月度存储。任何一项翻倍都会撞线,
      而三项分别归三个人管,谁也看不见乘积。
  D3  陈旧却随车。产物里体积大、但很久没变过的路径——每次部署重存一遍不变的东西。
      09-06 实测:modelbooks/ohlcv 43 MB、1535 个文件,上次真正变更是 2026-03-31,
      占每次产物的 41%。

只读 git 与本地文件,不需要 Vercel 凭证(09-06 那次机上的 CLI token 已过期,
而这套检查本来就不该依赖厂商 API——依赖谁的 API,就会在谁挂掉时失明)。

    python -m pipeline.tools.audit_deploy_cost
    python -m pipeline.tools.audit_deploy_cost --days 14 --budget-gb 10 --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# 保留期(天)。与 Vercel 后台 Deployment Retention Policy 的 Production 值一致;
# 2026-09-06 由 30 天改为 2 周。改了后台就要改这里,否则预算算的是别人的策略。
RETENTION_DAYS = 14

# 陈旧判据:超过这么久没变过、又超过这么大,就该考虑搬出产物。
STALE_DAYS = 90
STALE_MIN_MB = 5.0


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=False,
    )
    return out.stdout


@dataclass
class Finding:
    code: str
    severity: str            # "violation" | "warning"
    message: str
    detail: Dict[str, Any] = field(default_factory=dict)


def _dir_bytes(root: Path) -> int:
    if not root.exists():
        return 0
    if root.is_file():
        return root.stat().st_size
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


def read_gate(repo: Path) -> Dict[str, Any]:
    """读出闸的状态与它看管的路径。

    看管路径从脚本里解析,不是从这里硬编码——硬编码会让工具永远同意自己。
    """
    vj_path = repo / "vercel.json"
    gate: Dict[str, Any] = {"configured": False, "script": None, "watched": [], "script_exists": False}
    if not vj_path.exists():
        return gate
    try:
        vj = json.loads(vj_path.read_text())
    except json.JSONDecodeError:
        gate["error"] = "vercel.json 解析失败"
        return gate
    cmd = vj.get("ignoreCommand")
    gate["build_command"] = vj.get("buildCommand", "")
    gate["output_directory"] = vj.get("outputDirectory", "")
    if not cmd:
        return gate
    gate["configured"] = True
    m = re.search(r"([\w./-]+\.sh)", cmd)
    if not m:
        return gate
    script = repo / m.group(1)
    gate["script"] = m.group(1)
    if not script.exists():
        return gate
    gate["script_exists"] = True
    body = script.read_text()
    wm = re.search(r"WATCH=\(([^)]*)\)", body)
    if wm:
        gate["watched"] = [w.strip().strip("\"'") for w in wm.group(1).split() if w.strip()]
    return gate


def artifact_sources(repo: Path, gate: Dict[str, Any]) -> Dict[str, int]:
    """产物由哪些仓库路径喂出来,各多少字节。

    两个来源:构建时从 buildCommand 拷进去的(如 data/output),以及
    outputDirectory 所属包的静态目录(frontend/public)。应用代码打包后的体积
    另算——它两位数 MB 以下且本来就该随每次部署走,不是本检查的对象。
    """
    sources: Dict[str, int] = {}
    build = gate.get("build_command", "") or ""
    for m in re.finditer(r"cp\s+-r\s+([\w./-]+)\s", build):
        src = m.group(1)
        sources[src] = _dir_bytes(repo / src)
    outdir = gate.get("output_directory", "") or ""
    pkg = Path(outdir).parts[0] if outdir else ""
    if pkg:
        public = repo / pkg / "public"
        if public.exists():
            for child in sorted(public.iterdir()):
                rel = str(child.relative_to(repo))
                # 构建时拷进来的那份会出现在 public 下,已在上面计过,别数两遍
                if any(rel.endswith(Path(s).name) and s in sources for s in list(sources)):
                    continue
                sources[rel] = _dir_bytes(child)
    return sources


def check_gate_covers_sources(gate: Dict[str, Any], sources: Dict[str, int]) -> List[Finding]:
    out: List[Finding] = []
    if not gate.get("configured"):
        out.append(Finding(
            "D1a", "violation",
            "vercel.json 没有 ignoreCommand —— 每一条 commit 都会触发一次生产部署",
        ))
        return out
    if not gate.get("script_exists"):
        out.append(Finding(
            "D1b", "violation",
            f"ignoreCommand 指向的脚本不存在: {gate.get('script')} —— Vercel 会当它失败并照常构建",
        ))
        return out
    watched: Sequence[str] = gate.get("watched") or []
    if not watched:
        out.append(Finding("D1c", "violation", "闸脚本里解析不到 WATCH 路径列表"))
        return out
    for src, size in sources.items():
        if size == 0:
            continue
        covered = any(src == w or src.startswith(w.rstrip("/") + "/") for w in watched)
        if not covered:
            out.append(Finding(
                "D1d", "violation",
                f"产物来源 {src} ({size/1048576:.1f} MB) 不在闸的看管范围内 —— "
                f"它变了也不会重新部署,线上会静默停在旧版",
                {"path": src, "mb": round(size / 1048576, 1), "watched": list(watched)},
            ))
    return out


def deploy_rate(repo: Path, days: int, watched: Sequence[str]) -> Dict[str, Any]:
    """按闸的规则回放:过去 days 天里真正会触发构建的 commit 有多少。

    一次 `git log --name-only` 拿全,不要每条 commit 起一个子进程——第一版
    在真实仓库(14 天 783 条 commit)上跑了两分钟还没完,而一个跑不完的检查
    等于没有这个检查。
    """
    since = f"{days} days ago"
    SEP = "\x1e"
    raw = _git(repo, "log", "origin/main", f"--since={since}",
               f"--format={SEP}%H %P", "--name-only")
    build = skip = 0
    for chunk in raw.split(SEP):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, _, rest = chunk.partition("\n")
        parents = head.split()[1:]
        if not parents:
            # 闸在拿不到父 commit 时兜底偏向构建;回放必须复刻这个分支,
            # 否则预测出来的是一个比闸更乐观的世界。
            build += 1
            continue
        names = [n for n in rest.split("\n") if n]
        if len(parents) > 1 and not names:
            # merge commit 的 --name-only 默认为空;当它没改动处理(Vercel 也只
            # 看这次 push 带来的树变化)
            skip += 1
            continue
        if any(any(n == w or n.startswith(w.rstrip("/") + "/") for w in watched) for n in names):
            build += 1
        else:
            skip += 1
    total = build + skip
    return {
        "days": days,
        "commits": total,
        "would_build": build,
        "would_skip": skip,
        "builds_per_day": round(build / days, 2) if days else 0.0,
    }


def _age_days(repo: Path, rel: str) -> Optional[int]:
    ts = _git(repo, "log", "origin/main", "-1", "--format=%ct", "--", rel).strip()
    if not ts:
        return None
    return int((time.time() - int(ts)) / 86400)


def stale_shipped(repo: Path, sources: Dict[str, int], max_depth: int = 3) -> List[Finding]:
    """产物里体积大、却很久没变的路径。

    ⚠️ 分辨率是这个检查的成败。第一版只看 sources 的那一层,而 09-06 那个真实
    案例（modelbooks 43 MB、上次变更 2026-03-31）住在 `frontend/public/data`
    **下一层**——父目录里有别的天天在变的小文件,把它的年龄压成了「今天」。
    检查报了「无问题」,而被测的东西在物理上无法被那个粒度看见。
    所以对超标的目录要往下钻,直到找到真正陈旧的那个子树。
    """
    out: List[Finding] = []
    seen: set[str] = set()

    def walk(rel: str, size: int, depth: int) -> None:
        mb = size / 1048576
        if mb < STALE_MIN_MB or rel in seen:
            return
        age = _age_days(repo, rel)
        if age is None:
            return
        if age > STALE_DAYS:
            seen.add(rel)
            last = _git(repo, "log", "origin/main", "-1", "--format=%ad", "--date=short", "--", rel).strip()
            out.append(Finding(
                "D3", "warning",
                f"{rel} 有 {mb:.1f} MB 但上次变更是 {last}（{age} 天前）—— "
                f"每次部署都在重存一份不变的东西",
                {"path": rel, "mb": round(mb, 1), "last_change": last, "age_days": age},
            ))
            return
        # 父目录看着"新",可能只是里面有个小文件天天在动;往下钻找真正不动的大块
        if depth >= max_depth:
            return
        d = repo / rel
        if not d.is_dir():
            return
        for child in sorted(d.iterdir()):
            if child.name.startswith("."):
                continue
            walk(str(child.relative_to(repo)), _dir_bytes(child), depth + 1)

    for src, size in sources.items():
        walk(src, size, 0)
    return out


def head_is_stale(repo: Path) -> Optional[int]:
    """检出的树落后 origin/main 多少个 commit(取不到返回 None)。

    ⚠️ 这个工具审的是**检出了什么**,而 Vercel 构建的是 **main**。共享主树常年
    停在某条落后一百多个 commit 的分支上(宪法主树保护第 3 条),在那里跑就会
    读到旧的 vercel.json 并报「没有 ignoreCommand」——闸明明已经在 main 上了。
    一个会对着旧副本喊狼来了的检查,几次之后就没人再信它的阳性。
    所以落后时要在读数上写明,别让它冒充 main 的状态。
    """
    out = _git(repo, "rev-list", "--count", "HEAD..origin/main").strip()
    try:
        return int(out)
    except ValueError:
        return None


def audit(repo: Path, days: int = 14, budget_gb: float = 10.0) -> Dict[str, Any]:
    gate = read_gate(repo)
    behind = head_is_stale(repo)
    sources = artifact_sources(repo, gate)
    findings: List[Finding] = []
    findings += check_gate_covers_sources(gate, sources)

    artifact_bytes = sum(sources.values())
    watched = gate.get("watched") or []
    rate = deploy_rate(repo, days, watched) if watched else {
        "days": days, "commits": 0, "would_build": 0, "would_skip": 0, "builds_per_day": 0.0,
    }
    # 没有闸时,每条 commit 都是一次部署
    if not gate.get("configured"):
        shas = [s for s in _git(repo, "log", "origin/main", f"--since={days} days ago", "--format=%H").split() if s]
        rate = {"days": days, "commits": len(shas), "would_build": len(shas),
                "would_skip": 0, "builds_per_day": round(len(shas) / days, 2) if days else 0.0}

    projected_gb = rate["builds_per_day"] * RETENTION_DAYS * artifact_bytes / 1024 ** 3
    if projected_gb > budget_gb:
        findings.append(Finding(
            "D2", "violation",
            f"预计月度部署存储 {projected_gb:.1f} GB 超预算 {budget_gb:.0f} GB "
            f"（每次产物 {artifact_bytes/1048576:.0f} MB × {rate['builds_per_day']}/天 × 保留 {RETENTION_DAYS} 天）",
            {"projected_gb": round(projected_gb, 1), "budget_gb": budget_gb},
        ))
    findings += stale_shipped(repo, sources)

    if behind:
        findings.insert(0, Finding(
            "D0", "warning",
            f"检出的树落后 origin/main {behind} 个 commit —— 以下读数反映的是这棵树,"
            f"不是 Vercel 实际构建的 main;先 `git fetch && git checkout origin/main` 再判",
            {"behind": behind},
        ))

    return {
        "gate": gate,
        "head_behind_main": behind,
        "artifact_mb": round(artifact_bytes / 1048576, 1),
        "sources_mb": {k: round(v / 1048576, 1) for k, v in sorted(sources.items(), key=lambda x: -x[1])},
        "deploy_rate": rate,
        "retention_days": RETENTION_DAYS,
        "projected_gb": round(projected_gb, 1),
        "budget_gb": budget_gb,
        "findings": [f.__dict__ for f in findings],
        "violations": sum(1 for f in findings if f.severity == "violation"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--days", default=14, type=int, help="回放窗口")
    ap.add_argument("--budget-gb", default=10.0, type=float)
    ap.add_argument("--json", type=Path, help="把完整结果写到这个文件")
    args = ap.parse_args(argv)

    res = audit(args.repo.resolve(), days=args.days, budget_gb=args.budget_gb)

    g = res["gate"]
    print(f"闸: {'在' if g.get('configured') else '缺失'}"
          + (f" ({g.get('script')}, 看管 {len(g.get('watched') or [])} 条路径)" if g.get("configured") else ""))
    print(f"每次产物: {res['artifact_mb']} MB")
    for k, v in list(res["sources_mb"].items())[:6]:
        print(f"    {v:>8.1f} MB  {k}")
    r = res["deploy_rate"]
    print(f"近 {r['days']} 天: commit {r['commits']} 次 -> 构建 {r['would_build']} / 跳过 {r['would_skip']}"
          f"  ({r['builds_per_day']}/天)")
    print(f"预计存储: {res['projected_gb']} GB (保留 {res['retention_days']} 天, 预算 {res['budget_gb']:.0f} GB)")
    if res["findings"]:
        print()
        for f in res["findings"]:
            mark = "✗" if f["severity"] == "violation" else "!"
            print(f"  {mark} [{f['code']}] {f['message']}")
    else:
        print("\n  无问题")

    if args.json:
        args.json.write_text(json.dumps(res, ensure_ascii=False, indent=2))

    return 1 if res["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
