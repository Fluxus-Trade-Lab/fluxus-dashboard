"""recap_cross.py: recap cross-asset sentences → Market State (Andy 2026-10-03 选B)."""
import importlib.util
import json
from pathlib import Path

_P = Path(__file__).resolve().parents[2] / ".claude/skills/focus-notes/scripts/recap_cross.py"
_spec = importlib.util.spec_from_file_location("recap_cross", _P)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


def test_asset_of_maps_every_recap_lead():
    leads = {"The dollar": "UUP", "Bonds": "TLT", "The ten-year": "10Y", "Gold and silver": "GLD",
             "Crude": "USO", "Bitcoin": "IBIT", "美元": "UUP", "债券": "TLT", "十年期": "10Y",
             "黄金与白银": "GLD", "原油": "USO", "比特币": "IBIT"}
    for lead, ticker in leads.items():
        assert rc.asset_of(f"<b>{lead}</b> did a thing.") == ticker, lead


def test_clean_strips_the_internal_marker_only():
    s = "<b>Bonds</b> handed back the reversal ◇, and the rest — stays."
    out = rc.clean(s)
    assert "◇" not in out
    assert out == "<b>Bonds</b> handed back the reversal, and the rest — stays."


def test_build_reads_both_languages(tmp_path):
    pack = tmp_path / "2026-10" / "2026-10-02" / "pack"
    pack.mkdir(parents=True)
    (pack / "content_EN.json").write_text(json.dumps({"cross_assets": ["<b>Crude</b> fell ◇."]}))
    (pack / "content_ZH.json").write_text(json.dumps({"cross_assets": ["<b>原油</b>回落 ◇。"]}))
    doc = rc.build("2026-10-02", tmp_path)
    assert doc == {"asof": "2026-10-02", "notes": {
        "en": [{"ticker": "USO", "text": "<b>Crude</b> fell."}],
        "zh": [{"ticker": "USO", "text": "<b>原油</b>回落。"}]}}
