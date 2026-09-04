"""周检的四个数里能在仓库里量的两个：有评估集的 skill 数、最近 benchmark 的 delta。
另两个从仓库外取，写进周检：
  · `skill-used:` / `skill-skipped:` 的行数比 —— 过去 7 天各任务书回复里数（hook 乙强制留痕，
    数据天然在）。这一格原本是「描述优化器触发率」，R24 作废：模拟器有确定性缺陷，
    它的 4/8 永久标「仪器缺陷，不可用作评分」；真读数比模拟触发更贴近我们要管的事。
  · /plugin 的 Not-used-recently 清单 —— 交互终端里读。

⚠️ last_delta 是**裸数**，别裸着读：delta 的正确读法见 docs/superpowers/verdicts.md
（§七 契约行：9 比 0 读的是「照没照单子做」，不是「答案更好」）。CLI 会把这句附在输出里。"""
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


CAVEAT = ("delta 读法见 docs/superpowers/verdicts.md："
          "9 比 0 读的是照没照单子做，不是答案更好")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default=".claude/skills"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv); s = summarize(Path(a.root))
    if a.json:
        # summarize() 的已有键一个不动；caveat 只在输出层追加。
        print(json.dumps({**s, "caveat": CAVEAT}, ensure_ascii=False))
    else:
        print(f"自建 skill {s['skills']} · 有评估集 {s['with_evals']} · 最近 delta {s['last_delta']}")
        print(f"（{CAVEAT}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
