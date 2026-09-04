"""把四个来源的 skill / agent / command / 定时任务书列成一张表。
审计范围如果等于「我记得的地方」，漏掉的就永远是孤儿——所以来源写死成参数。"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List

_FM = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def read_description(path: Path) -> str:
    try:
        m = _FM.match(path.read_text(errors="replace"))
    except OSError:
        return ""
    if not m:
        return ""
    for line in m.group(1).splitlines():
        if line.strip().startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def _row(name: str, source: str, path: Path) -> Dict:
    return {"name": name, "source": source, "path": str(path),
            "description": read_description(path),
            "mtime": int(path.stat().st_mtime) if path.exists() else 0}


def _skill_dirs(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return [d for d in sorted(root.iterdir())
            if d.is_dir() and not d.name.startswith("_") and (d / "SKILL.md").exists()]


def inventory(roots: Dict[str, Path]) -> List[Dict]:
    rows: List[Dict] = []
    proj = roots.get("project")
    if proj:
        for d in _skill_dirs(proj / "skills"):
            rows.append(_row(d.name, "project-skill", d / "SKILL.md"))
        ag = proj / "agents"
        if ag.exists():
            rows += [_row(f.stem, "project-agent", f) for f in sorted(ag.glob("*.md"))]
        cm = proj / "commands"
        if cm.exists():
            rows += [_row(f.stem, "project-command", f) for f in sorted(cm.glob("*.md"))]
    for key, src in (("user-skills", "user-skill"), ("plugin-skills", "plugin-skill"),
                     ("scheduled", "scheduled-task")):
        root = roots.get(key)
        if root:
            rows += [_row(d.name, src, d / "SKILL.md") for d in _skill_dirs(root)]
    return rows


DEFAULT_ROOTS = {
    "project": Path(".claude"),
    "user-skills": Path(os.path.expanduser("~/.claude/skills")),
    "plugin-skills": Path(os.path.expanduser(
        "~/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills")),
    "scheduled": Path(os.path.expanduser("~/.claude/scheduled-tasks")),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = inventory(DEFAULT_ROOTS)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{r['source']:<16}{r['name']:<36}{r['description'][:60]}")
        print(f"\n共 {len(rows)} 项")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
