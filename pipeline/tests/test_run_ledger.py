import json
from pipeline.run_ledger import Ledger


def test_ledger_appends_one_line_per_run_and_never_raises(tmp_path):
    p = tmp_path / "run_ledger.jsonl"
    L = Ledger(session="2026-08-18", path=p)
    L.note("universe_quality", "degraded", degraded=["atr"], weird=object())
    L.wrote("universe.json"); L.error("breadth", "boom")
    L.write()
    L2 = Ledger(session="2026-08-18", path=p); L2.write()          # same-session re-run = second line
    lines = [json.loads(x) for x in p.read_text().splitlines()]
    assert len(lines) == 2 and lines[0]["session"] == "2026-08-18"
    assert lines[0]["guards"]["universe_quality"]["status"] == "degraded"
    assert lines[0]["finished_utc"] and lines[0]["errors"][0]["where"] == "breadth"
