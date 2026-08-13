#!/usr/bin/env python3
"""把筛选台导出的 picks.json 落成正式图库。

    python3 scripts/apply_visual_picks.py ~/Downloads/picks.json

产出：
    visuals/selected/V08_a.jpg …        选中的图，按代码命名
    visuals/selected/INDEX.md           代码 → 文件 → 情绪标签 → 来源页
    visuals/selected/redo.md            标了「全都不行」的代码，待改搜索词
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "visuals"
SELECTED = OUT / "selected"
MANIFEST = OUT / "manifest.json"

SUFFIX = "abcdefghijklmnop"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("picks", nargs="?", default=str(OUT / "picks.json"),
                    help="筛选台导出的 picks.json 路径")
    ap.add_argument("--clean", action="store_true", help="先清空 visuals/selected/")
    args = ap.parse_args()

    picks_path = Path(args.picks).expanduser()
    if not picks_path.exists():
        raise SystemExit(f"找不到 {picks_path} — 在筛选台点「导出 picks.json」后把它放进 visuals/")

    picks_data = json.loads(picks_path.read_text(encoding="utf-8"))
    picks: dict[str, list[str]] = picks_data.get("picks", {})
    dead: list[str] = picks_data.get("dead", [])

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    meta = {e["code"]: e for e in manifest["entries"]}
    src_by_file = {im["file"]: im for e in manifest["entries"] for im in e["images"]}

    if args.clean and SELECTED.exists():
        shutil.rmtree(SELECTED)
    SELECTED.mkdir(parents=True, exist_ok=True)

    rows, n = [], 0
    for code in sorted(picks, key=lambda c: int(c[1:])):
        entry = meta.get(code, {})
        for i, rel in enumerate(picks[code]):
            src = OUT / rel
            if not src.exists():
                print(f"  缺文件：{rel}")
                continue
            tag = SUFFIX[i] if len(picks[code]) > 1 else ""
            dest = SELECTED / f"{code}{tag}{src.suffix}"
            shutil.copy2(src, dest)
            n += 1
            page = src_by_file.get(rel, {}).get("page", "")
            rows.append(f"| {code} | `{dest.name}` | {entry.get('title','')} | "
                        f"{entry.get('section','')} | {page} |")

    index = [
        "# Fluxus 视觉库 · 已选图",
        "",
        f"共 {n} 张,覆盖 {len(picks)} 条视觉代码。对应 `Fluxus_Visual_Library.md`。",
        "",
        "> 这些图是**筛选用样本**,来源是公开网络搜索,版权状态未核实。",
        "> 正式发布前按 `Fluxus_Content_Ops.md` 第 7 节处理:优先换成公有领域作品,",
        "> 或改用自制版本。",
        "",
        "| 代码 | 文件 | 情绪 / 场景 | 分类 | 来源页 |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]
    (SELECTED / "INDEX.md").write_text("\n".join(index), encoding="utf-8")

    if dead:
        redo = ["# 待重抓的视觉代码", "",
                "筛选时标了「全都不行」。改 `Fluxus_Visual_Library.md` 里的搜索词后:", "",
                "```bash", f"python3 scripts/fetch_visuals.py --refetch {','.join(sorted(dead))}",
                "python3 scripts/build_visual_gallery.py", "```", ""]
        for code in sorted(dead, key=lambda c: int(c[1:])):
            e = meta.get(code, {})
            redo.append(f"- **{code}** {e.get('title','')} — 现搜索词 `{e.get('query','')}`")
        (SELECTED / "redo.md").write_text("\n".join(redo) + "\n", encoding="utf-8")

    print(f"已选 {n} 张 → {SELECTED.relative_to(ROOT)}/")
    print(f"索引：{(SELECTED / 'INDEX.md').relative_to(ROOT)}")
    if dead:
        print(f"待重抓 {len(dead)} 条：{(SELECTED / 'redo.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
