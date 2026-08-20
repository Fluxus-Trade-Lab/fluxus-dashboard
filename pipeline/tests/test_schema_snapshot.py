"""schema_snapshot: removals fail, additions pass (2026-08-19 breadth loss)."""
import json

from pipeline.tools import schema_snapshot as S


def _setup(tmp_path, payload):
    out = tmp_path / "output"; out.mkdir()
    (out / "breadth.json").write_text(json.dumps(payload))
    snap = tmp_path / "snap.json"
    return out, snap


def test_removed_field_fails_added_passes(tmp_path):
    out, snap = _setup(tmp_path, {"regime": {"score": 1}, "breadth": {"t2108": 5}})
    assert S.main(["--update", "--output", str(out), "--snapshot", str(snap)]) == 0
    # addition -> 0
    (out / "breadth.json").write_text(json.dumps(
        {"regime": {"score": 1}, "breadth": {"t2108": 5}, "new_block": 1}))
    assert S.main(["--check", "--output", str(out), "--snapshot", str(snap)]) == 0
    # removal of a top-level block (the 08-19 shape) -> 1
    (out / "breadth.json").write_text(json.dumps({"breadth": {"t2108": 5}}))
    assert S.main(["--check", "--output", str(out), "--snapshot", str(snap)]) == 1
