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
