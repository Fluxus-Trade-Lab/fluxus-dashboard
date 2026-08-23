"""Unpushed work -- the收工 check that the task books already assume exists.

Git 铁律一: "Commit 后立刻 push;会话结束前手上不留未 push 的 commit(没合进
main 的工作＝随时会死的工作)". The night-shift task book ends with "跑一次
`python -m pipeline.tools.audit_unpushed`" -- and until 08-23 that module did
not exist, so the check every night claimed to run had never run once.

It sweeps **every worktree**, not just the current one, because that is where
the work actually dies: 08-19's night branch, the 20 abandoned worktrees the
weekly sweep found 6 real fixes in, the scratchpad trees each session opens.
A session only sees its own; nothing looked at the set.

  U1  commits reachable from HEAD but from NO remote ref -- work that exists
      on this disk only, one `rm -rf` from gone
  U2  ahead of the configured upstream, but those commits ARE on some other
      remote ref (a branch pushed under a different name / no tracking set)
  U3  uncommitted changes to tracked files (a dirty tree is work that is not
      even a commit yet)
  U4  the worktree's directory is gone but git still lists it (stale admin)

Only U1 is a violation. The measure is deliberately "on a remote anywhere",
not "has an upstream configured": the first run of this tool called a branch
247 commits unpushed because it had no tracking branch, when every one of
those commits was already sitting on `origin/claude/friendly-chaplygin-b46c13`.
Measuring "is tracking configured" and reporting it as "is the work safe" is
the wrong relationship -- 铁律一 is about whether the work survives this
disk dying, and only the remote answers that. U2/U3/U4 are warnings.

    python -m pipeline.tools.audit_unpushed
    python -m pipeline.tools.audit_unpushed --json out.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

MAIN = "origin/main"


def _git(repo: Path, *args: str, timeout: int = 20) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                           text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:  # noqa: BLE001 -- a broken worktree must not kill the sweep
        return ""


def worktrees(repo: Path) -> List[Path]:
    out = _git(repo, "worktree", "list", "--porcelain")
    return [Path(l.split(" ", 1)[1]) for l in out.splitlines() if l.startswith("worktree ")]


def audit_worktree(wt: Path, main_ref: str = MAIN) -> Dict[str, Any]:
    rep: Dict[str, Any] = {"worktree": str(wt), "branch": None, "ahead": 0,
                           "violations": [], "warnings": []}
    if not wt.exists():
        rep["warnings"].append("U4 directory is gone, git still lists it (git worktree prune)")
        return rep

    branch = _git(wt, "rev-parse", "--abbrev-ref", "HEAD") or "(detached)"
    rep["branch"] = branch
    upstream = _git(wt, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")

    rep["upstream"] = upstream or None

    # The question 铁律一 actually asks: does this work exist anywhere but here?
    off = _git(wt, "rev-list", "--count", "HEAD", "--not", "--remotes")
    n = int(off) if off.isdigit() else 0
    rep["unpushed"] = n
    if n:
        rep["violations"].append(f"U1 {n} commit(s) on this disk only (no remote has them)")

    if upstream:
        ahead = _git(wt, "rev-list", "--count", "@{u}..HEAD")
        a = int(ahead) if ahead.isdigit() else 0
        rep["ahead"] = a
        if a and not n:
            rep["warnings"].append(f"U2 {a} commit(s) ahead of {upstream}, but they are on another remote ref")
    else:
        rep["ahead"] = n
        if not n:
            rep["warnings"].append("U2 no upstream configured (work is on a remote, tracking is not set)")

    dirty = [l for l in _git(wt, "status", "--porcelain").splitlines()
             if l and not l.startswith("??")]
    rep["dirty"] = len(dirty)
    if dirty:
        rep["warnings"].append(f"U3 {len(dirty)} uncommitted change(s) to tracked files")
    return rep


def run(repo: Path = Path("."), main_ref: str = MAIN,
        trees: Optional[List[Path]] = None) -> Dict[str, Any]:
    trees = trees if trees is not None else worktrees(repo)
    out: Dict[str, Any] = {"worktrees": [], "violations": 0, "warnings": 0}
    for wt in trees:
        rep = audit_worktree(wt, main_ref)
        out["worktrees"].append(rep)
        out["violations"] += len(rep["violations"])
        out["warnings"] += len(rep["warnings"])
    out["ok"] = out["violations"] == 0
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--main-ref", default=MAIN)
    ap.add_argument("--json", help="write the report here")
    args = ap.parse_args(argv)
    out = run(Path(args.repo), args.main_ref)

    for rep in out["worktrees"]:
        flag = "OK " if not rep["violations"] else "BAD"
        detail = "; ".join(rep["violations"] + rep["warnings"])
        print(f"{flag} {rep['branch'] or '?':34s} {detail or 'clean'}   [{rep['worktree']}]")
    print(f"\n{'OK' if out['ok'] else 'UNPUSHED WORK'}: {out['violations']} violation(s), "
          f"{out['warnings']} warning(s) over {len(out['worktrees'])} worktree(s)")
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
