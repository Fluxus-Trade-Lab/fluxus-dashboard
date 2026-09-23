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

import pytest

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
                   "pct_of_position": 100.0, "R": 1.23, "R_scope": "trade", "held_sessions": 9}]}
    b.update(over)
    return b


def test_book_out_emits_the_ladder():
    out = book_out(_book(), "2026-09-22")
    assert out["pos"] == [["HOOD", "long", "2026-08-20", 1.96, 7.4]]
    assert out["legs"] == [["2026-09-22", "FSLY", "CLOSE", 100.0, 1.23, 9]]


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
        assert len(row) == 6, f"leg row is date/ticker/type/pct/R/held, got {row}"
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


# ---------- M1 · the one leak the row shape cannot catch ----------
# The shape guard above closes "a price arrives under a new field". What it
# cannot close is "a price arrives in a column that exists" — stop_R wired to
# stop_price. By the time that is page text it is a bare number under a header
# on another line, which reads exactly like the index closes the page prints on
# purpose. So it is checked where the numbers still have names, against the one
# relation a price cannot satisfy.

def test_M1_reddens_when_the_stop_column_holds_a_price():
    """漏改: the stop column was never converted, so the raw stop price is in it."""
    b = _book()
    b["positions"][0]["stop_R"] = 142.50   # the live stop, in dollars
    with pytest.raises(SystemExit, match="above the mark"):
        book_out(b, "2026-09-22")


def test_M1_reddens_when_a_leg_percent_holds_a_quantity():
    """改了但接错: pct_of_position wired to qty instead of qty/original_qty."""
    b = _book()
    b["legs"][0]["pct_of_position"] = 300
    with pytest.raises(SystemExit, match="not a share of the position"):
        book_out(b, "2026-09-22")


def test_M1_lets_a_stop_trailed_up_to_the_mark_through():
    """The negative half: a stop trailed right to the close is legal, and a
    position at 100% out is a legal percent. A gate that reddens on these would
    block the 09:00 出片班 for nothing."""
    b = _book()
    b["positions"][0]["stop_R"] = b["positions"][0]["open_R"]
    assert book_out(b, "2026-09-22")["pos"][0][3] == 7.4
    assert book_out(_book(), "2026-09-22")["legs"][0][3] == 100.0


def test_M1_does_not_fire_on_a_position_with_no_R():
    b = _book()
    b["positions"][0]["stop_R"] = None
    b["positions"][0]["open_R"] = None
    assert book_out(b, "2026-09-22")["pos"][0][3] is None


def test_M1_lets_a_breakeven_stop_through_when_open_R_wobbles_near_zero():
    """T-0923-58's review of the real 09-22 book: NBIS carried stop_R=0.00,
    open_R=+0.54 — a stop trailed to breakeven on a name that hasn't run far
    yet. If open_R drifts a little further down (or negative) before the stop
    is hit or the sheet is updated, that is still real price action, not a
    price leak, and must not SystemExit the whole PDF (T-0923-61)."""
    b = _book()
    b["positions"][0]["stop_R"] = 0.0
    for orr in (0.54, 0.0, -0.3, 0.6, -0.6):
        b["positions"][0]["open_R"] = orr
        assert book_out(b, "2026-09-22")["pos"][0][3] == 0.0


def test_M1_still_reddens_a_breakeven_stop_far_past_the_band():
    """The exemption is a narrow band, not a blank check: a breakeven stop
    against an open_R that has run far past it is exactly the kind of gap the
    gate exists to catch (either a stale stop that should have fired, or a
    genuine price leak), so it must still raise."""
    b = _book()
    b["positions"][0]["stop_R"] = 0.0
    b["positions"][0]["open_R"] = -2.0
    with pytest.raises(SystemExit, match="above the mark"):
        book_out(b, "2026-09-22")


# ---------- the cost point and the holding period ----------

def test_the_page_draws_all_three_points_of_the_ladder():
    """Andy 2026-09-23:「把 portfolio的cost和stop写进去」— cost 0R, stop, now.
    cost is 0R for every row, so it is drawn by the renderer rather than carried
    in the payload; this checks the renderer actually draws it."""
    import pathlib as _p
    from pipeline.content.recap import visual
    js = (_p.Path(visual.__file__).with_name("visual_assets") / "recap_page.js").read_text()
    book = js[js.index("function book(is, c, V)"):]
    book = book[:book.index("\n  function ", 1)]
    assert "V.p_cost" in book, "the cost header is not in the position table"
    assert '<td class="n">0R</td>' in book, "the cost cell is not drawn"
    assert "V.leg_held" in book, "a CLOSE line does not say how long the trade was held"
    for lang in ("EN", "ZH"):
        assert visual.CHROME_LABELS[lang]["p_cost"]
        assert "{n}" in visual.CHROME_LABELS[lang]["leg_held"]


def test_held_sessions_counts_both_ends_and_skips_non_sessions():
    from pipeline.content.recap.build_pack import _held_sessions
    # 2026-09-14 Mon .. 2026-09-16 Wed
    assert _held_sessions(dt.date(2026, 9, 14), dt.date(2026, 9, 16)) == 3
    # entered and closed the same session
    assert _held_sessions(dt.date(2026, 9, 16), dt.date(2026, 9, 16)) == 1
    # Fri .. Mon: the weekend is not held sessions
    assert _held_sessions(dt.date(2026, 9, 11), dt.date(2026, 9, 14)) == 2
