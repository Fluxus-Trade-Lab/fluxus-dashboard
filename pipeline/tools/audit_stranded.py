"""Stranded work -- is the branch's content ON main, or only pushed somewhere?

`audit_unpushed` already answers 铁律一: "does this work survive the disk
dying?" -- its measure is "is the commit on any remote". That is a real
question and it is NOT this one. 宪法's definition of done is stricter:

    "完成的定义：合进 main 且 Andy 能点开看到，才算完成。"

Between "pushed" and "on main" sits a gap nothing measured, and every morning
report for three nights ran the same line -- "待合分支 fbclock · 建议合 y" --
without any way to check whether that sentence was still true. 有备份/有推送
is a bool; the gap lives in the set.

⚠️ Why this file exists at all: five git commands, five different answers.

On 2026-09-07 the same seven branches were measured five ways:

  git rev-list --count main..B    "ahead by N"     entangles ahead with behind
  git diff --stat main...B        three-dot        885-file false alarms (记忆在案)
  git diff --stat main B          two-dot          dominated by how far BEHIND
  git cherry main B               patch-id         '+' on rebased-but-landed work
  git merge-tree --write-tree     merge result     5/7 branches: "conflict", no verdict

Four of the five disagreed with each other on `night-20260903`, whose content
turned out to be fully on main. None of them answers the question a human
means. So this module asks it directly, at the line:

    base = merge-base(main, branch)
    for every file the branch changed relative to base:
        every line the branch ADDED must be findable in main's version

Added-lines-present is deliberately asymmetric. The three append-only public
boxes (INBOX.md / material_inbox.md / DATA_CONTRACTS.md §七) are the files that
strand most often, and on those main legitimately holds the branch's lines PLUS
everybody else's. A symmetric equality test calls that "undelivered" forever;
tree equality calls it "conflict" and declines to answer. Containment is the
relationship we actually care about: **is my line on main.**

⚠️ The trap this module is built to not repeat.

The first draft of this check ran in zsh:

    files=$(git log main..B --name-only --format='')
    for f in $files; do git diff --quiet main B -- "$f" && ...

zsh does not word-split unquoted expansions. `$files` arrived as ONE pathspec
containing every filename joined by newlines, matched no file at all, and
`git diff --quiet` returned 0 -- "no difference". The check printed ✅ DELIVERED
for all five stranded branches. **A pathspec that matches nothing is
indistinguishable from a clean diff**, and the failure mode points at green.

So `_added_lines` refuses to trust a pathspec that resolves to no blob on
either side, and raises instead of returning "clean". 没有先验证一个检查能报出
阳性,就不该信它的阴性 -- here the positive control is structural, not just a test.

⚠️ The second trap, found the same night, pointing the other way.

"55 lines of this branch are not on main" is true and says nothing about
whether they SHOULD be. `fix/alex-stockbee-s2-prev-volume` had 8 test lines
absent from main; reading the diff as "main is missing this" got the direction
backwards. Main had *replaced* that test on 2026-09-05 with a stronger one --
the branch's version grepped `run_all.py` source text for `'prev_volume'`, and
main's docstring says why that was wrong: "it passed for weeks while the column
did not exist ... Grepping the manifest is not checking the truck." Merging the
branch would have been a REGRESSION, recommended by a green-looking measure.

So absence is only evidence of stranding when main has NOT touched that file
since the fork. `main_touched` is computed per file (`git log base..main -- f`)
and any file main moved on is reported SUPERSEDED, never "建议合". Of the seven
live branches on 2026-09-07, exactly one -- `fbclock` -- had untouched files.
The other six were stale, and three nights of morning reports could not tell
the two apart, because "ahead by N commits" cannot.

Violations:

  S1  a branch has undelivered lines and its newest such commit is older than
      --max-age days (default 2) -- work quietly rotting on a branch
  S2  a branch is fully delivered but still exists -- the "建议合 y" line in
      tonight's report is about work that already landed; the branch is litter
      and reporting it wastes a human's attention every morning
  S3  a branch carries undelivered lines in files OUTSIDE the producer's
      safe-merge whitelist -- these are the ones that genuinely need a human,
      and the report should say so instead of lumping them with S1
  S4  a branch's missing lines sit only in files main has MOVED ON since the
      fork -- stale, not stranded. Reported so nobody writes "建议合 y" about
      it, which is the mistake this module was built after making.

    python -m pipeline.tools.audit_stranded
    python -m pipeline.tools.audit_stranded --json out.json
    python -m pipeline.tools.audit_stranded --repo /path/to/repo --max-age 3
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

MAIN = "origin/main"

# 宪法 safe-merge 白名单：只碰这些路径的分支，产出者自己就能合。
SAFE_PREFIXES: Tuple[str, ...] = (
    "data/research/",
    "data/reference/incidents/",
    "pipeline/tests/",
    "data/growth/",
    "Fluxus_Brand/ops/material_inbox.md",
)
SAFE_GLOBS: Tuple[str, ...] = ("pipeline/tools/audit_",)

# 归档分支不参与考核：它们本来就是存档，不是「待合」。
IGNORED_PREFIXES: Tuple[str, ...] = ("archive/",)


class GitError(RuntimeError):
    pass


def _git(repo: Path, *args: str, timeout: int = 60) -> str:
    p = subprocess.run(("git", "-C", str(repo)) + args,
                       capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout


def _git_ok(repo: Path, *args: str, timeout: int = 60) -> Optional[str]:
    try:
        return _git(repo, *args, timeout=timeout)
    except GitError:
        return None


def is_safe_path(path: str) -> bool:
    """Is this path inside the producer's own safe-merge authority?"""
    if any(path.startswith(p) for p in SAFE_PREFIXES):
        return True
    return any(Path(path).name.startswith(g.rsplit("/", 1)[-1])
               and path.startswith(g.rsplit("/", 1)[0] + "/")
               for g in SAFE_GLOBS)


def _blob_exists(repo: Path, ref: str, path: str) -> bool:
    return _git_ok(repo, "cat-file", "-e", f"{ref}:{path}") is not None


def _lines(repo: Path, ref: str, path: str) -> Optional[List[str]]:
    out = _git_ok(repo, "show", f"{ref}:{path}")
    return None if out is None else out.splitlines()


def added_lines(repo: Path, base: str, branch: str, path: str) -> List[str]:
    """Lines the branch ADDED to `path` relative to `base`.

    Raises if `path` names no blob on either side -- a pathspec that matches
    nothing must never be reported as "nothing was added".
    """
    if not _blob_exists(repo, base, path) and not _blob_exists(repo, branch, path):
        raise GitError(f"pathspec matches no blob on either side: {path}")
    out = _git(repo, "diff", "--no-color", "-U0", base, branch, "--", path)
    return [ln[1:] for ln in out.splitlines()
            if ln.startswith("+") and not ln.startswith("+++")]


def main_moved_on(repo: Path, main: str, base: str, path: str) -> int:
    """Commits main made to `path` AFTER the fork point.

    Nonzero means absence-from-main is ambiguous: main may have deliberately
    replaced the branch's lines. That is not a branch waiting to be merged.
    """
    out = _git_ok(repo, "log", f"{base}..{main}", "--format=%h", "--", path)
    return len([l for l in (out or "").splitlines() if l.strip()])


def undelivered(repo: Path, main: str, branch: str,
                path: str) -> Tuple[int, int, int]:
    """(added_by_branch, missing_from_main, commits_main_made_since_fork)."""
    base = _git(repo, "merge-base", main, branch).strip()
    added = added_lines(repo, base, branch, path)
    moved = main_moved_on(repo, main, base, path)
    if not added:
        return 0, 0, moved
    main_ver = _lines(repo, main, path)
    if main_ver is None:                      # file absent from main entirely
        return len(added), len(added), moved
    have: Set[str] = set(main_ver)
    missing = [ln for ln in added if ln.strip() and ln not in have]
    return len(added), len(missing), moved


def branch_report(repo: Path, branch: str, main: str = MAIN) -> Dict[str, Any]:
    base = _git(repo, "merge-base", main, branch).strip()
    files = sorted({f for f in _git(
        repo, "log", f"{main}..{branch}", "--name-only", "--format=",
    ).splitlines() if f.strip()})
    per_file: List[Dict[str, Any]] = []
    for f in files:
        try:
            n_add, n_missing, moved = undelivered(repo, main, branch, f)
        except GitError:
            per_file.append({"path": f, "added": 0, "missing": 0, "moved": 0,
                             "superseded": False,
                             "unreadable": True, "safe": is_safe_path(f)})
            continue
        if n_add:
            per_file.append({"path": f, "added": n_add, "missing": n_missing,
                             "moved": moved, "superseded": bool(moved),
                             "unreadable": False, "safe": is_safe_path(f)})
    missing_files = [x for x in per_file if x["missing"] > 0]
    # 真缺 = main 自分叉后一次都没碰过这个文件。碰过的，缺失是二义的。
    stranded = [x for x in missing_files if not x["superseded"]]
    superseded = [x for x in missing_files if x["superseded"]]
    newest = _git(repo, "log", "-1", "--format=%cI", branch).strip()
    oldest_unmerged = _git_ok(
        repo, "log", f"{main}..{branch}", "--reverse", "--format=%cI")
    oldest = (oldest_unmerged.splitlines() or [newest])[0] if oldest_unmerged else newest
    return {
        "branch": branch,
        "base": base[:12],
        "commits_ahead": len(_git(
            repo, "rev-list", f"{main}..{branch}").split()),
        "files_changed": len(per_file),
        "lines_added": sum(x["added"] for x in per_file),
        "lines_missing": sum(x["missing"] for x in per_file),
        "stranded_files": stranded,
        "superseded_files": superseded,
        "lines_stranded": sum(x["missing"] for x in stranded),
        "missing_share": round(sum(x["missing"] for x in per_file)
                               / max(sum(x["added"] for x in per_file), 1), 4),
        "all_safe": bool(stranded) and all(x["safe"] for x in stranded),
        "oldest_unmerged": oldest,
        "newest_commit": newest,
        "delivered": not missing_files,
        "stale_only": bool(superseded) and not stranded,
    }


def _age_days(iso: str, now: Optional[datetime] = None) -> float:
    now = now or datetime.now(timezone.utc)
    return (now - datetime.fromisoformat(iso)).total_seconds() / 86400.0


def check(repo: Path, main: str = MAIN, max_age: float = 2.0,
          now: Optional[datetime] = None) -> Dict[str, Any]:
    refs = [r.strip() for r in _git(
        repo, "for-each-ref", "--format=%(refname:short)",
        "refs/remotes/origin").splitlines() if r.strip()]
    branches = [r for r in refs
                if r not in (main, "origin/HEAD")
                and not any(r[len("origin/"):].startswith(p)
                            for p in IGNORED_PREFIXES)
                and _git(repo, "rev-list", "--count", f"{main}..{r}").strip() != "0"]
    reports = [branch_report(repo, b, main) for b in branches]
    v: List[Tuple[str, str]] = []
    for r in reports:
        age = _age_days(r["oldest_unmerged"], now)
        r["age_days"] = round(age, 2)
        if r["delivered"]:
            v.append(("S2", f"{r['branch']}: 内容已全在 main，分支是垃圾，可删"))
        elif r["stale_only"]:
            v.append(("S4", f"{r['branch']}: {r['lines_missing']} 行不在 main，但全部"
                            f"落在 main 自分叉后改过的文件里 —— 是过期不是滞留，"
                            f"别写「建议合」；要合先人工比对"))
        elif not r["all_safe"]:
            outside = sorted({x["path"] for x in r["stranded_files"]
                              if not x["safe"]})
            v.append(("S3", f"{r['branch']}: {r['lines_stranded']} 行真未送到"
                            f"（main 自分叉后没碰过这些文件），"
                            f"且在白名单外（需人合）：" + ", ".join(outside[:3])))
        elif age > max_age:
            v.append(("S1", f"{r['branch']}: {r['lines_stranded']} 行真未送到，"
                            f"已放 {age:.1f} 天，且全在白名单内（产出者本可自合）"))
    return {"violations": v, "branches": reports,
            "scanned": len(branches), "refs_seen": len(refs),
            "max_age": max_age}


def render(res: Dict[str, Any]) -> str:
    L = ["未送到的活 —— 推出去了，但不在 main 上", ""]
    L.append(f"  扫了 {res['scanned']} 条有未合 commit 的分支"
             f"（origin 共 {res['refs_seen']} 个 ref；archive/* 不计）")
    L.append(f"  判据：分支相对 merge-base 加的每一行，能不能在 main 的同名文件里找到")
    L.append("")
    for r in sorted(res["branches"], key=lambda x: -x.get("age_days", 0)):
        tag = ("✅ 已送到" if r["delivered"]
               else "🟡 过期（main 已走远）" if r["stale_only"] else "🔴 真未送到")
        L.append(f"  {tag}  {r['branch']}")
        L.append(f"      {r['commits_ahead']} commit · 改 {r['files_changed']} 个文件 · "
                 f"加 {r['lines_added']} 行 · {r['lines_missing']} 行不在 main "
                 f"({100 * r['missing_share']:.1f}%) · 其中真未送到 {r['lines_stranded']} 行 · "
                 f"最老未合 commit {r.get('age_days', '?')} 天前")
        for x in r["stranded_files"][:4]:
            mark = "白名单内" if x["safe"] else "⚠️ 白名单外"
            L.append(f"        🔴 {x['missing']:>4}/{x['added']:<5} 行缺  {x['path']}  "
                     f"[{mark}·main 没碰过]")
        for x in r["superseded_files"][:3]:
            L.append(f"        🟡 {x['missing']:>4}/{x['added']:<5} 行缺  {x['path']}  "
                     f"[main 自分叉后改过 {x['moved']} 次 —— 二义]")
        extra = max(len(r["stranded_files"]) - 4, 0) + max(len(r["superseded_files"]) - 3, 0)
        if extra:
            L.append(f"        ... 另有 {extra} 个文件")
    L.append("")
    if res["violations"]:
        L.append("  违规:")
        for code, msg in res["violations"]:
            L.append(f"    [{code}] {msg}")
    else:
        L.append("  no violations")
    L.append("")
    L.append("推出去了不算送到；合进 main 才算。")
    L.append("🟡 是过期不是滞留 —— 缺的那几行落在 main 自己改过的文件里，合它可能是回退。")
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--main", default=MAIN)
    ap.add_argument("--max-age", type=float, default=2.0,
                    help="白名单内的活放多少天算违规（默认 2）")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    res = check(a.repo, a.main, a.max_age)
    print(render(res))
    if a.json:
        a.json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    return 1 if res["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
