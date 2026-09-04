"""周检的四个数里能在仓库里量的两个：有评估集的 skill 数、最近 benchmark 的 delta。
另两个（描述优化器触发率、/plugin Not-used-recently）从各自产物/交互终端取，写进周检。"""
from __future__ import annotations
import argparse, json
from pathlib import Path


def summarize(skills_root: Path) -> dict:
    # 约定：workspace 在仓库根，与 .claude/ 平级（不是 skills_root 的兄弟）。
    # skills_root 通常是 <repo>/.claude/skills，所以仓库根是 skills_root.parent.parent。
    repo_root = skills_root.parent.parent
    out = {"skills": 0, "with_evals": 0, "last_delta": {}}
    for d in sorted(p for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        if not (d / "SKILL.md").exists():
            continue
        out["skills"] += 1
        if (d / "evals" / "evals.json").exists():
            out["with_evals"] += 1
        ws = repo_root / f"{d.name}-workspace"
        if ws.exists():
            its = sorted(
                ws.glob("iteration-*/benchmark.json"),
                key=lambda p: int(p.parent.name.removeprefix("iteration-")),
            )
            if its:
                try:
                    out["last_delta"][d.name] = json.loads(its[-1].read_text())["delta"]["pass_rate"]
                except (KeyError, ValueError):
                    pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default=".claude/skills"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv); s = summarize(Path(a.root))
    print(json.dumps(s, ensure_ascii=False) if a.json else
          f"自建 skill {s['skills']} · 有评估集 {s['with_evals']} · 最近 delta {s['last_delta']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
