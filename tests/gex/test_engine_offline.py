# tests/gex/test_engine_offline.py
import json
from pathlib import Path
from pipeline.gex.engine import run

def test_offline_end_to_end(tmp_path):
    out = run(out_dir=tmp_path, offline_fixture="tests/gex/fixtures/chain_es_20260710.csv",
              offline_spot=7570.0, do_git=False)
    latest = json.loads((tmp_path / "latest.json").read_text())
    assert latest["version"] == 1
    assert latest["stale"] is False
    spx = latest["instruments"]["SPX"]
    assert spx["tenors"]["swing"]["net_gex_mm"] is not None
    assert (tmp_path / "latest.html").exists()
    dated = list(tmp_path.glob("gex_*.json"))
    assert len(dated) == 1
    assert out["ok"] is True

def test_offline_stale_on_missing_fixture(tmp_path):
    # First produce a good run, then force a failure → stale copy of last good
    run(out_dir=tmp_path, offline_fixture="tests/gex/fixtures/chain_es_20260710.csv",
        offline_spot=7570.0, do_git=False)
    out = run(out_dir=tmp_path, offline_fixture="tests/gex/fixtures/DOES_NOT_EXIST.csv",
              offline_spot=7570.0, do_git=False)
    latest = json.loads((tmp_path / "latest.json").read_text())
    assert latest["stale"] is True and latest["stale_reason"]
    assert out["ok"] is False
