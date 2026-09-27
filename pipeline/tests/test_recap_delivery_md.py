"""T-0920-31: weekly delivery.md must not claim an x/ folder that never gets created (run.py write_delivery)."""
from pipeline.content.recap.run import write_delivery


class FakeIssue:
    def __init__(self, tmp_path, weekly):
        self.label = "2026-W38" if weekly else "2026-09-14"
        self.weekly = weekly
        self.dir = tmp_path

    def contents(self):
        opt = {"key": "A", "title": "t", "concept": "c", "why": "w"}
        edu = {"options": [opt]}
        return {"ZH": {"education": edu}, "EN": {"education": edu}}


def _rep():
    return {"r1": [], "r2": [], "rules": {}, "w1": []}


def _state():
    return {"ok": True, "pdf": {"EN": {"ok": True, "pages": 5, "path": "x.pdf"}}, "images": {}}


def test_weekly_delivery_md_has_no_x_image_line(tmp_path):
    iss = FakeIssue(tmp_path, weekly=True)
    write_delivery(iss, _state(), _rep())
    text = (tmp_path / "delivery.md").read_text()
    assert "X 配图" not in text


def test_daily_delivery_md_still_has_x_image_line(tmp_path):
    iss = FakeIssue(tmp_path, weekly=False)
    write_delivery(iss, _state(), _rep())
    text = (tmp_path / "delivery.md").read_text()
    assert "X 配图" in text


def test_delivery_md_reports_andy_coverage_numbers(tmp_path):
    """T-0927-35: 缺数据 (benign) and 有原话未上页 (the real problem) must show as separate lists."""
    iss = FakeIssue(tmp_path, weekly=False)
    state = _state()
    state["andy_coverage"] = {"n_covered": 3, "n_total": 5, "missing_dates": ["2026-09-23"],
                              "uncovered": ["2026-09-25"], "streak": 1}
    write_delivery(iss, state, _rep())
    text = (tmp_path / "delivery.md").read_text()
    assert "上页 3/5 场" in text
    assert "其中缺数据 2026-09-23" in text
    assert "有原话未上页 2026-09-25" in text
    assert "连续第" not in text  # streak 1 is a single occurrence, not yet flagged (Andy 09-27)


def test_delivery_md_flags_a_repeat_streak_for_ops(tmp_path):
    iss = FakeIssue(tmp_path, weekly=True)
    state = _state()
    state["andy_coverage"] = {"n_covered": 4, "n_total": 5, "missing_dates": [],
                              "uncovered": ["2026-09-25"], "streak": 2}
    write_delivery(iss, state, _rep())
    text = (tmp_path / "delivery.md").read_text()
    assert "连续第 2 期" in text
    assert "taskboard.py new" in text
