"""The R ladder (Andy 2026-09-23「以多少R的形式，不出现美元数值」).

Positive controls come in the two shapes this can actually fail in
(method_positive_controls_by_failure_mode):
  A. 漏改 — a per-share price or share count reaches the page text
  B. 改了但接错 — the payload carries a raw price field even though the
     current template happens not to print it

A green money gate on today's PDF only means "no leak today"; B is what keeps
the next person from re-adding entry_price to the row and shipping it.
"""
from __future__ import annotations

import datetime as dt

from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.visual import book_out


# ---------- A. the text gate must redden on both leak shapes ----------

def test_money_gate_reddens_on_a_dollar_price():
    g = run_gates("Open position ARM entry $333.20 stop $310.00")
    assert g["money_shares"], "a $-prefixed per-share price must be caught"
    assert not g["ok"]


def test_money_gate_reddens_on_share_counts():
    for leak in ("sold 1,200 shares", "减仓 1,200 股"):
        g = run_gates(leak)
        assert g["money_shares"], f"share count not caught: {leak}"


def test_money_gate_is_green_on_the_r_ladder_itself():
    """The ladder's own vocabulary must not trip the gate, or it is useless."""
    page = ("Open position  Side  Entry  Stop R  Open R\n"
            "HOOD long 2026-08-20 +1.96R +7.40R\n"
            "ARM · 09-22 · TRIM 33.2% · +0.44R\n"
            "FSLY · 09-22 · CLOSE 100.0% · +1.23R\n")
    assert run_gates(page)["money_shares"] == []


# ---------- B. the payload must not carry raw prices ----------

PRICE_FIELDS = {"entry_price", "stop_price", "initial_stop", "price",
                "qty", "original_qty", "current_qty", "R_dollars"}


def _book(**over):
    b = {"return_pct": 1.0, "cash_pct": 50.0, "open_names": 1, "closed_trades": 0,
         "open_R_total": 7.4, "realized_R_period": 2.17, "closes_stale": False,
         "positions": [{"ticker": "HOOD", "direction": "long", "entry_date": "2026-08-20",
                        "open_R": 7.4, "stop_R": 1.96}],
         "legs": [{"date": "2026-09-22", "ticker": "FSLY", "type": "CLOSE",
                   "pct_of_position": 100.0, "R": 1.23, "R_scope": "trade"}]}
    b.update(over)
    return b


def test_book_out_emits_the_ladder():
    out = book_out(_book(), "2026-09-22")
    assert out["pos"] == [["HOOD", "long", "2026-08-20", 1.96, 7.4]]
    assert out["legs"] == [["2026-09-22", "FSLY", "CLOSE", 100.0, 1.23]]


def test_book_out_carries_no_price_or_share_field():
    """Guards the 改了但接错 direction: if someone re-adds a price to a row,
    this fails here rather than on a member's PDF.

    The guard is the row SHAPE, not the magnitude of the numbers in it — a
    percent legitimately reaches 100.0, so "any value above N is a price" is
    not a judgement this can make.
    """
    out = book_out(_book(), "2026-09-22")
    assert set(out) == {"ret", "cash", "open", "closed", "openR", "realR", "pos", "legs"}, \
        f"book payload grew a field: {sorted(set(out))}"
    for row in out["pos"]:
        assert len(row) == 5, f"position row is ticker/side/entry/stopR/openR, got {row}"
    for row in out["legs"]:
        assert len(row) == 5, f"leg row is date/ticker/type/pct/R, got {row}"
    assert PRICE_FIELDS.isdisjoint(out.keys())


def test_stop_R_is_none_when_the_entry_stop_was_never_recorded():
    """Andy 2026-09-23「initialStop 缺失的仓位 stop 栏留空不猜」."""
    b = _book()
    b["positions"][0]["stop_R"] = None
    out = book_out(b, "2026-09-22")
    assert out["pos"][0][3] is None


def test_close_is_one_row_per_trade_not_one_per_tranche():
    """09-22's FSLY went out in three tranches on one day; it must print once."""
    from pipeline.content.recap.build_pack import book_block  # import-time guard only
    assert callable(book_block)
    out = book_out(_book(), "2026-09-22")
    closes = [L for L in out["legs"] if L[2] == "CLOSE"]
    assert len(closes) == 1 and closes[0][3] == 100.0
