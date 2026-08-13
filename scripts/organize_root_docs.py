#!/usr/bin/env python3
"""One-shot: move the 38 loose root .md files into typed subfolders and repoint
every reference to them.

    python scripts/organize_root_docs.py --dry-run    # show the plan, touch nothing
    python scripts/organize_root_docs.py              # do it

Why a script and not `mv`: ~90 cross-references live in other markdown files, and
each one needs a path relative to ITS OWN directory, not the repo root. Doing that
by hand is where links get silently broken.

Deliberately NOT moved (repo-infrastructure files that belong at root, and the
ones code writes or reads by root-relative path):
    plan.md  PERFORMANCE_TRUTH.md  performance_truth.json  TODOS.md  DESIGN.md
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# destination -> files. Basenames are unique across the repo, which is what makes
# the reference rewrite safe.
LAYOUT = {
    "Fluxus_Brand/voice": [
        "Fluxus_Voice_Bible.md",
        "Fluxus_Voice_Audit_Discord.md",
        "Fluxus_Own_Lines.md",
        "Fluxus_Ammo_150.md",
        "Fluxus_Ammo_Library.md",
        "Fluxus_Swipe_File.md",
        "Fluxus_LiDan_Borrowings.md",
    ],
    "Fluxus_Brand/ops": [
        "Fluxus_Action_Plan.md",
        "Fluxus_Content_Ops.md",
        "Fluxus_Week_Plan.md",
        "Fluxus_X_Playbook.md",
    ],
    "Fluxus_Brand/templates": [
        "Fluxus_Letter_Template.md",
        "Fluxus_Daily_Recap_Format.md",
    ],
    "Fluxus_Brand/record": [
        "Fluxus_H1_2026_Timeline.md",
        "Fluxus_H1_Review_Template.md",
    ],
    "Fluxus_Brand/research": [
        "Fluxus_TSF_Teardown.md",
        "Fluxus_JB_Teardown_3way.md",
        "Fluxus_Quartr_Teardown.md",
        "Fluxus_X_Competitor_Teardown.md",
        "Fluxus_Substack_Research.md",
        "Fluxus_Substack_Top10.md",
        "Fluxus_Fintwit_100_Census.md",
        "Fluxus_Fintwit_100_Research_Design.md",
        "Fluxus_Fintwit_Voice_Codes.md",
        "Fluxus_Piggyback_List.md",
        "Fluxus_China_Market_Research.md",
    ],
    "Fluxus_Brand/visual": [
        "Fluxus_Visual_Library.md",
        "Fluxus_Image_Method.md",
        "Fluxus_Poster_System.md",
    ],
    "Fluxus_Brand/site": [
        "Fluxus_Homepage_Copy.md",
        "Fluxus_Masterclass_Page.md",
    ],
    "Fluxus_Brand/copybook": [
        "Fluxus_Copybook_Spec.md",
        "Fluxus_Copybook_Roster.md",
        "Fluxus_Copybook_Ledger.md",
    ],
    "docs": [
        "research.md",
        "Position_Sizing_Knowledge_Index.md",
        "Notion_Workspace_Audit_Report.md",
    ],
}

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__",
             ".claude", "openclaw_workspace", "PrimeTrading_Obsidian"}

# Memory lives outside the repo but names these files; if it isn't repointed,
# a future session looks for them at the old path and finds nothing.
MEMORY_DIR = Path.home() / ".claude/projects/-Users-taolezhu-Documents-AI-Trading-System/memory"


def build_mapping() -> dict[str, str]:
    m = {}
    for dest, files in LAYOUT.items():
        for f in files:
            m[f] = f"{dest}/{f}"
    return m


def scan_text_files() -> list[Path]:
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".md", ".mdx")):
                out.append(Path(root) / f)
    return out


def rewrite(path: Path, mapping: dict[str, str], new_home: dict[str, Path],
            dry: bool) -> int:
    """Repoint references inside `path`, relative to path's own directory."""
    try:
        text = original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0
    base = new_home.get(str(path), path).parent
    # Files outside the repo (the memory store) get repo-relative paths -- a
    # relpath from ~/.claude/... would be a six-deep ../ chain that helps nobody.
    outside = REPO not in base.parents and base != REPO
    hits = 0
    # Longest basenames first so e.g. Fluxus_Ammo_Library.md is not clipped by a
    # shorter overlapping name.
    for old in sorted(mapping, key=len, reverse=True):
        if old not in text:
            continue
        target = REPO / mapping[old]
        rel = mapping[old] if outside else os.path.relpath(target, base)
        if rel == old:            # same directory after the move: leave it bare
            continue
        out, i = [], 0
        while True:
            j = text.find(old, i)
            if j < 0:
                out.append(text[i:])
                break
            # Already carries a path prefix -> leave it alone.
            if j > 0 and text[j - 1] in "/\\":
                out.append(text[i:j + len(old)])
                i = j + len(old)
                continue
            out.append(text[i:j])
            out.append(rel)
            hits += 1
            i = j + len(old)
        text = "".join(out)
    if text != original and not dry:
        path.write_text(text, encoding="utf-8")
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    mapping = build_mapping()

    missing = [f for f in mapping if not (REPO / f).exists()]
    if missing:
        print("MISSING at repo root, aborting:", ", ".join(missing), file=sys.stderr)
        return 1

    collisions = [d for f, d in mapping.items() if (REPO / d).exists()]
    if collisions:
        print("DESTINATION already exists, aborting:", ", ".join(collisions), file=sys.stderr)
        return 1

    print(f"{'[dry-run] ' if dry else ''}moving {len(mapping)} files\n")
    for dest in LAYOUT:
        print(f"  {dest}/  <- {len(LAYOUT[dest])} files")

    # Where each file will live, so its own internal links resolve from the new spot.
    new_home = {str(REPO / old): REPO / new for old, new in mapping.items()}

    docs = scan_text_files()
    if MEMORY_DIR.exists():
        docs += sorted(MEMORY_DIR.glob("*.md"))
    print(f"\nscanning {len(docs)} markdown files for references")

    if not dry:
        for dest in LAYOUT:
            (REPO / dest).mkdir(parents=True, exist_ok=True)

    total, touched = 0, []
    for d in docs:
        n = rewrite(d, mapping, new_home, dry)
        if n:
            total += n
            touched.append((str(d.relative_to(REPO)) if REPO in d.parents
                            else f"[memory] {d.name}", n))

    print(f"\n{total} references repointed across {len(touched)} files:")
    for name, n in sorted(touched, key=lambda x: -x[1]):
        print(f"  {n:3d}  {name}")

    if not dry:
        for old, new in mapping.items():
            shutil.move(str(REPO / old), str(REPO / new))
        manifest = REPO / "Fluxus_Brand/_MOVED.json"
        manifest.write_text(json.dumps(
            {"moved_on": "2026-08-03", "old_path -> new_path": mapping},
            indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {manifest.relative_to(REPO)}")

    print("\n" + ("nothing changed (dry run)" if dry else "done"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
