"""focus-notes skill：事实卡生成器 + 核对闸。Andy 2026-10-01「那 27 句候选，写法ok」。"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SK = ROOT / ".claude" / "skills" / "focus-notes"
FIXTURE = ROOT / "data" / "research" / "screener_redesign" / "focus" / "2026-09-29.json"


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, SK / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def gate():
    return _mod("check_notes")


@pytest.fixture(scope="module")
def doc():
    return json.loads(FIXTURE.read_text())


def test_approved_day_passes(gate, doc):
    assert gate.check(gate._cards(doc), doc["notes"]) == []


def test_every_focus_card_has_both_languages(doc):
    focus = {r["t"] for k in doc["setups"] for r in doc["setups"][k]["rows"] if r["focus"]}
    assert focus and focus == {t for t in doc["notes"] if not t.startswith("_")}
    for t, v in doc["notes"].items():
        assert v["zh"] and v["en"], t


@pytest.mark.parametrize("ticker,mutate,kind", [
    ("STX", lambda s: s.replace("0.84", "0.48"), "number"),
    ("RNG", lambda s: s.replace("0.33", "0.38"), "number"),
    ("STX", lambda s: s + "建议回踩买入。", "advice"),
])
def test_gate_catches_planted_errors(gate, doc, ticker, mutate, kind):
    bad = gate.check(gate._cards(doc), {ticker: {"zh": mutate(doc["notes"][ticker]["zh"])}})
    assert any(b[2][0] == kind for b in bad), bad


def test_gate_catches_sentence_on_wrong_card(gate, doc):
    # MPC 的句子（21EMA 0.15）放到 VLO 的卡上必须报红
    assert gate.check(gate._cards(doc), {"VLO": {"zh": doc["notes"]["MPC"]["zh"]}})


def test_builder_focus_means_gate_and_four_of_four():
    out = ROOT / "data" / "output"
    if not (out / "universe.json").exists():
        pytest.skip("no data/output in this checkout")
    cards = _mod("build_cards").build(out)
    rows = [r for k in cards["setups"] for r in cards["setups"][k]["rows"]]
    assert rows
    for r in rows:
        assert r["focus"] == (r["tight"] and r["qn"] == 4), r["t"]
    assert "s111_unchecked" in cards["rule"]


@pytest.mark.parametrize("ticker,sentence", [
    ("MPC", "Oil & Gas Refining & Marketing 在减速；离 21EMA 只剩 0.15 ATR。"),
    ("RNG", "Weakening group; 99th percentile in its group."),
])
def test_gate_refuses_repeating_the_group(gate, doc, ticker, sentence):
    # Andy 2026-10-01「B1」：组的方向页面另印一栏，句子只说个股
    bad = gate.check(gate._cards(doc), {ticker: {"zh": sentence}})
    assert any(b[2][0] == "group" for b in bad), bad


def test_notes_follow_b1(doc):
    assert doc.get("note_style", "").startswith("B1")
