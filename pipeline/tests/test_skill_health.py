from pathlib import Path
from pipeline.tools.skill_health import summarize


def _skill(root: Path, name: str, evals: bool, bench_delta=None):
    d = root / name; d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n")
    if evals:
        (d / "evals").mkdir(); (d / "evals" / "evals.json").write_text("{}")
    if bench_delta is not None:
        w = root.parent / f"{name}-workspace" / "iteration-1"; w.mkdir(parents=True)
        (w / "benchmark.json").write_text('{"delta": {"pass_rate": %s}}' % bench_delta)


def test_counts(tmp_path):
    skills = tmp_path / "skills"
    _skill(skills, "a", True, 0.4)
    _skill(skills, "b", False)
    s = summarize(skills)
    assert s["skills"] == 2 and s["with_evals"] == 1
    assert s["last_delta"] == {"a": 0.4}
