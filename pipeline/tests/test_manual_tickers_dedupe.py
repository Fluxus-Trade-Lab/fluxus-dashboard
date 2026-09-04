import json
from pathlib import Path

from pipeline.screeners.name_cards import manual_tickers


def test_duplicate_in_sheet_yields_one_card_slot(tmp_path: Path):
    # 2026-09-03: the GAS pull delivered ABSI twice; two identical cards made
    # audit_archives I2 fail and the nightly publish exited 1.
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"tickers": ["absi", "ABSI", "NFG", "absi"]}))
    assert manual_tickers(p) == ["ABSI", "NFG"]


def test_cap_applies_after_dedupe(tmp_path: Path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"tickers": [f"T{i}" for i in range(25)] * 2}))
    assert len(manual_tickers(p)) == 20
