from pathlib import Path
from pipeline.tools.skill_health import summarize


def _skill(root: Path, name: str, evals: bool, bench_deltas=None):
    """root 是 skills 目录（真实布局：<repo>/.claude/skills）。
    workspace 与 .claude/ 平级，即 <repo>/{name}-workspace。
    bench_deltas: dict[iteration_suffix] = delta，例如 {"1": 0.4} 或 {"2": 0.1, "10": 0.9}。
    """
    d = root / name; d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n")
    if evals:
        (d / "evals").mkdir(); (d / "evals" / "evals.json").write_text("{}")
    if bench_deltas:
        repo_root = root.parent.parent
        for suffix, delta in bench_deltas.items():
            w = repo_root / f"{name}-workspace" / f"iteration-{suffix}"
            w.mkdir(parents=True)
            (w / "benchmark.json").write_text('{"delta": {"pass_rate": %s}}' % delta)


def test_counts(tmp_path):
    skills = tmp_path / ".claude" / "skills"
    _skill(skills, "a", True, {"1": 0.4})
    _skill(skills, "b", False)
    s = summarize(skills)
    assert s["skills"] == 2 and s["with_evals"] == 1
    assert s["last_delta"] == {"a": 0.4}


def test_last_delta_picks_newest_iteration(tmp_path):
    skills = tmp_path / ".claude" / "skills"
    _skill(skills, "c", True, {"2": 0.1, "10": 0.9})
    s = summarize(skills)
    assert s["last_delta"].get("c") == 0.9
