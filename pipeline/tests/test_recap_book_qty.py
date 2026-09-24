"""Q1 — the book's two share counts must agree (T-0924-100).

2026-09-24, Andy: 「每日复盘里面出现的 ytd return 计算和我们在 dashboard 上面的
return% 不一样」. The two formulas turned out to be algebraically identical; what
split them was the Sheet. The recap holds a position at
``originalQty − Σtrims`` while the dashboard holds it at ``currentQty``, and
nothing in GAS checks that those agree — one hand edit to the ARM 09-17 row
(1 of 390) put the two products 0.86pp apart on YTD return, both looking healthy.

Positive controls by failure mode (the two ways this can be wrong):
  * not computed at all  → the mismatch tests below go red
  * computed but not wired → the run_check / delivery.md tests below go red
"""
import datetime as dt
import json

import pytest

from pipeline.content.recap import build_pack, run
from pipeline.portfolio.sheets_source import to_trades


def _row(ticker="ARM", entry="2026-09-17", qty=100, current=None, trims=()):
    return {"ticker": ticker, "direction": "long", "entryDate": entry, "entryPrice": 100.0,
            "originalQty": qty, "currentQty": qty if current is None else current,
            "stopPrice": 95.0, "initialStop": 95.0, "isClosed": False,
            "trims": [{"date": d, "price": p, "qty": q, "type": "trim"} for d, p, q in trims]}


# ------------------------------------------------------------------ _qty_mismatch (pure)
def test_no_mismatch_when_the_sheet_agrees_with_its_own_trim_log():
    rows = [_row(),
            _row("HOOD", "2026-09-10", qty=200, current=150, trims=[("2026-09-15", 110.0, 50)])]
    assert build_pack._qty_mismatch(to_trades(rows)) == []


def test_flags_the_hand_edited_row_and_says_which_way_it_leans():
    """The positive control: 20 of 200 were sold, but the Sheet still says 200."""
    rows = [_row("ARM", "2026-09-17", qty=200, current=200, trims=[("2026-09-22", 120.0, 20)])]
    hits = build_pack._qty_mismatch(to_trades(rows))
    assert len(hits) == 1
    assert hits[0]["ticker"] == "ARM" and hits[0]["entry_date"] == "2026-09-17"
    assert hits[0]["gap_pct_of_position"] == 10.0
    assert "more held" in hits[0]["sheet_says"]


def test_flags_the_other_direction_too():
    rows = [_row("ARM", "2026-09-17", qty=200, current=150)]
    hits = build_pack._qty_mismatch(to_trades(rows))
    assert hits[0]["gap_pct_of_position"] == -25.0
    assert "less held" in hits[0]["sheet_says"]


def test_never_reports_a_share_count():
    """Andy 2026-09-13「管线只做 R 和 %, 不写股数和美元」— the gap is a percent of
    the position, and no key in the row may carry a quantity."""
    rows = [_row("ARM", "2026-09-17", qty=200, current=200, trims=[("2026-09-22", 120.0, 20)])]
    hit = build_pack._qty_mismatch(to_trades(rows))[0]
    assert set(hit) == {"ticker", "direction", "entry_date", "gap_pct_of_position", "sheet_says"}
    assert 200 not in hit.values() and 180 not in hit.values() and 20 not in hit.values()


def test_a_trim_dated_after_the_issue_is_still_counted():
    """``currentQty`` is live: every logged trim is already out of it. Comparing
    against a T-window instead would invent a mismatch on every back-dated
    re-run — which is a gate that cries wolf, i.e. a gate nobody reads."""
    rows = [_row("ARM", "2026-09-17", qty=200, current=180, trims=[("2026-09-30", 120.0, 20)])]
    assert build_pack._qty_mismatch(to_trades(rows)) == []


# ------------------------------------------------------------------ book_block exposes it
def test_book_block_carries_qty_mismatch(monkeypatch):
    monkeypatch.setattr(build_pack, "_closes", lambda tickers, t: ({"ARM": 130.0}, []))
    rows = [_row("ARM", "2026-09-17", qty=200, current=200, trims=[("2026-09-22", 120.0, 20)])]
    out = build_pack.book_block("2026-09-23", {"stockTrades": rows, "meta": {"startingCapital": 100000}})
    assert [h["ticker"] for h in out["qty_mismatch"]] == ["ARM"]


def test_book_block_qty_mismatch_is_empty_on_a_clean_book(monkeypatch):
    monkeypatch.setattr(build_pack, "_closes", lambda tickers, t: ({"ARM": 130.0}, []))
    out = build_pack.book_block("2026-09-23", {"stockTrades": [_row()], "meta": {"startingCapital": 100000}})
    assert out["qty_mismatch"] == []


# ------------------------------------------------------------------ run.py check is red
class FakeIssue:
    """Enough of run.Issue for run_check; everything but Q1 is stubbed green."""
    label = "2026-09-23"
    T = "2026-09-23"
    weekly = False
    from_samples = True

    def __init__(self, tmp_path, book):
        self.dir = tmp_path
        self.src = tmp_path
        if book is not None:
            (tmp_path / "pack.json").write_text(json.dumps({"book": book}))

    def contents(self):
        edu = {"options": [{"key": "A", "title": "t", "concept": "c", "why": "w"}]}
        return {"ZH": {"education": edu}, "EN": {"education": edu}}


@pytest.fixture
def all_other_gates_green(monkeypatch):
    monkeypatch.setattr(run, "check_rules", lambda *a, **k: [])
    monkeypatch.setattr(run.dedupe, "seed", lambda *a, **k: {})
    monkeypatch.setattr(run.dedupe, "r1", lambda *a, **k: [])
    monkeypatch.setattr(run.dedupe, "r2", lambda *a, **k: [])
    from pipeline.content.recap import index_checks, wording
    monkeypatch.setattr(wording, "w1_hits", lambda *a, **k: [])
    monkeypatch.setattr(index_checks, "i1_placeholder_hits", lambda *a, **k: [])
    monkeypatch.setattr(index_checks, "i2_restatement_hits", lambda *a, **k: [])


def test_check_goes_red_on_a_split_row(tmp_path, all_other_gates_green):
    book = {"qty_mismatch": [{"ticker": "ARM", "direction": "long", "entry_date": "2026-09-17",
                              "gap_pct_of_position": 10.0, "sheet_says": "more held than the trim log implies"}]}
    rep = run.run_check(FakeIssue(tmp_path, book))
    assert rep["ok"] is False, "a split row must stop the issue — otherwise both products ship different return%"
    assert rep["q1"][0]["ticker"] == "ARM"
    assert json.loads((tmp_path / "check.json").read_text())["q1"]


def test_check_stays_green_on_a_clean_book(tmp_path, all_other_gates_green):
    assert run.run_check(FakeIssue(tmp_path, {"qty_mismatch": []}))["ok"] is True


def test_check_stays_green_for_a_pack_built_before_the_field_existed(tmp_path, all_other_gates_green):
    """Old issues must still re-render: no key, no verdict."""
    assert run.run_check(FakeIssue(tmp_path, {"return_pct": 1.2}))["ok"] is True


# ------------------------------------------------------------------ delivery.md names it
def _state():
    return {"ok": False, "pdf": {}, "images": {}}


def _rep(q1):
    return {"r1": [], "r2": [], "rules": {}, "w1": [], "q1": q1}


def test_delivery_md_names_the_ticker_when_q1_is_red(tmp_path):
    from pipeline.tests.test_recap_delivery_md import FakeIssue as DeliveryIssue
    iss = DeliveryIssue(tmp_path, weekly=False)
    run.write_delivery(iss, _state(), _rep([{"ticker": "ARM", "entry_date": "2026-09-17",
                                             "gap_pct_of_position": 10.0, "sheet_says": "x"}]))
    text = (tmp_path / "delivery.md").read_text()
    assert "报红" in text.split("Q1 持仓数量自洽")[1].splitlines()[0]
    assert "ARM" in text and "2026-09-17" in text


def test_delivery_md_reports_q1_pass_on_a_clean_book(tmp_path):
    from pipeline.tests.test_recap_delivery_md import FakeIssue as DeliveryIssue
    run.write_delivery(DeliveryIssue(tmp_path, weekly=False), _state(), _rep([]))
    text = (tmp_path / "delivery.md").read_text()
    assert "通过" in text.split("Q1 持仓数量自洽")[1].splitlines()[0]
    assert "ARM" not in text
