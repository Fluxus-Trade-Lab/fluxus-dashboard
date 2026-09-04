"""清单脚本：从四个来源把 skill/agent 列全。审计范围如果等于「我记得的地方」，
漏掉的就永远是孤儿。来源写死成参数，测试用临时目录造四种来源。"""
from pathlib import Path
from pipeline.tools.skill_inventory import inventory, read_description, superpowers_skills_root


def _mk(p: Path, body: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)


def test_reads_description_from_frontmatter(tmp_path):
    f = tmp_path / "SKILL.md"
    _mk(f, "---\nname: x\ndescription: 做某件事\n---\n正文")
    assert read_description(f) == "做某件事"


def test_description_missing_is_empty_not_crash(tmp_path):
    f = tmp_path / "SKILL.md"
    _mk(f, "# 没有 frontmatter\n")
    assert read_description(f) == ""


def test_inventory_covers_all_sources(tmp_path):
    _mk(tmp_path / "proj/skills/a/SKILL.md", "---\ndescription: A\n---")
    _mk(tmp_path / "proj/agents/b.md", "---\ndescription: B\n---")
    _mk(tmp_path / "proj/commands/c.md", "# c")
    _mk(tmp_path / "user/skills/d/SKILL.md", "---\ndescription: D\n---")
    _mk(tmp_path / "sched/e/SKILL.md", "---\ndescription: E\n---")
    rows = inventory({"project": tmp_path / "proj", "user-skills": tmp_path / "user/skills",
                      "scheduled": tmp_path / "sched"})
    names = {(r["source"], r["name"]) for r in rows}
    for k in [("project-skill", "a"), ("project-agent", "b"), ("project-command", "c"),
              ("user-skill", "d"), ("scheduled-task", "e")]:
        assert k in names
    assert all("mtime" in r and "path" in r for r in rows)


def test_retired_dirs_are_excluded(tmp_path):
    _mk(tmp_path / "user/skills/_retired/old/SKILL.md", "---\ndescription: old\n---")
    _mk(tmp_path / "user/skills/_gstack-command/SKILL.md", "---\ndescription: router\n---")
    _mk(tmp_path / "user/skills/live/SKILL.md", "---\ndescription: live\n---")
    rows = inventory({"project": tmp_path / "nope", "user-skills": tmp_path / "user/skills",
                      "scheduled": tmp_path / "nope"})
    assert [r["name"] for r in rows] == ["live"]


def test_superpowers_root_picks_highest_version_not_pinned(tmp_path):
    """写死版本号会让整包插件 skill 在升级当天静默消失（6.2.0→6.3.0 掉了 14 件）。
    也别按字典序：6.10.0 必须大于 6.9.0。"""
    for v in ("4.1.1", "6.9.0", "6.10.0"):
        (tmp_path / v / "skills").mkdir(parents=True)
    assert superpowers_skills_root(tmp_path) == tmp_path / "6.10.0" / "skills"


def test_missing_source_warns_on_stderr_instead_of_silently_empty(tmp_path, capsys):
    """审计范围如果等于「我记得的地方」，漏掉的就永远是孤儿——所以找不到要出声。"""
    assert superpowers_skills_root(tmp_path / "nope") is None
    inventory({"user-skills": tmp_path / "also-nope"})
    err = capsys.readouterr().err
    assert "nope" in err and "also-nope" in err
