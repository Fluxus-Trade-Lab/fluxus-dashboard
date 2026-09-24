"""The portfolio book's columns (Andy 2026-09-23, reversed and settled 2026-09-24).

Settled shape — 「成本和止损要展示的是价格，而不是R，只有浮盈浮亏和实现的盈亏是R」:

    ticker · side · entry date · cost (price) · stop (price) · open R
    TRIM/CLOSE legs: date · ticker · type · % of position · R · held sessions

The 09-23 version printed cost as a constant 0R and the stop as an R. Andy killed
it the next morning ("上成本 0R 显然是愚蠢的"), and these tests were rewritten
rather than patched — every one of them had encoded the old premise.

Positive controls come in the two shapes this can fail in
(method_positive_controls_by_failure_mode):
  A. 漏改 — a dollar amount or share count reaches the page text
  B. 改了但接错 — a value lands in a column that exists, where pdftotext leaves it
     a bare number under a header and no regex can see it. That direction is M1's,
     and each control below is proven red before its green is trusted.
"""
from __future__ import annotations

import datetime as dt

import pytest

from pipeline.content.recap.gates import run_gates
from pipeline.content.recap.visual import book_out


# ---------- A. the text gate, on the two shapes that are still banned ----------

def test_money_gate_reddens_on_a_dollar_amount():
    g = run_gates("realised $12,400 on the trade")
    assert g["money_shares"] and not g["ok"]


def test_money_gate_reddens_on_share_counts():
    for leak in ("sold 1,200 shares", "减仓 1,200 股"):
        assert run_gates(leak)["money_shares"], leak


def test_money_gate_is_green_on_the_book_as_it_now_prints():
    page = ("Open position  Side  Entry  Cost  Stop  Open R\n"
            "HOOD long 2026-08-20 96.72 104.00 +5.59R\n"
            "ARM · 09-23 · TRIM 33.2% · +0.44R\n"
            "FSLY · 09-23 · CLOSE 100.0% · +1.23R · held 3 sessions\n")
    assert run_gates(page)["money_shares"] == []


# ---------- the payload ----------

def _book(**over):
    b = {"return_pct": 1.0, "cash_pct": 50.0, "open_names": 1, "closed_trades": 0,
         "open_R_total": 7.4, "realized_R_period": 2.17, "closes_stale": False,
         "positions": [{"ticker": "HOOD", "direction": "long", "entry_date": "2026-08-20",
                        "open_R": 7.4, "cost": 96.72, "size_pct": 2.6, "stop": 104.00}],
         "legs": [{"date": "2026-09-23", "ticker": "FSLY", "type": "CLOSE",
                   "pct_of_position": 100.0, "R": 1.23, "R_scope": "trade",
                   "held_sessions": 3}]}
    b.update(over)
    return b


def test_book_out_emits_price_cost_price_stop_and_an_R():
    out = book_out(_book(), "2026-09-23")
    assert out["pos"] == [["HOOD", "long", "2026-08-20", 96.72, 2.6, 104.00, 7.4]]
    assert out["legs"] == [["2026-09-23", "FSLY", "CLOSE", 100.0, 1.23, 3]]


def test_book_payload_shape_is_fixed():
    """Direction B, structural half: the row SHAPE is the guard, not the size of
    the numbers in it — a percent legitimately reaches 100.0 and a price legitimately
    reaches four figures, so "any value above N" is not a judgement this can make."""
    out = book_out(_book(), "2026-09-23")
    assert set(out) == {"ret", "cash", "open", "closed", "openR", "realR", "pos", "legs"}
    for row in out["pos"]:
        assert len(row) == 7, f"position row is ticker/side/entry/cost/size/stop/openR, got {row}"
    for row in out["legs"]:
        assert len(row) == 6, f"leg row is date/ticker/type/pct/R/held, got {row}"


def test_a_position_with_no_stop_on_the_sheet_prints_blank():
    """Andy 2026-09-23「initialStop 缺失的仓位 stop 栏留空不猜」— the same refusal to
    guess applies to a missing live stop."""
    b = _book()
    b["positions"][0]["stop"] = None
    assert book_out(b, "2026-09-23")["pos"][0][5] is None


def test_close_is_one_row_per_trade_not_one_per_tranche():
    """09-22's FSLY went out in three tranches on one day; it must print once."""
    out = book_out(_book(), "2026-09-23")
    closes = [L for L in out["legs"] if L[2] == "CLOSE"]
    assert len(closes) == 1 and closes[0][3] == 100.0


# ---------- B. M1, the render-time gate, each control proven red ----------

def _m1_raises(book):
    with pytest.raises(SystemExit) as e:
        book_out(book, "2026-09-23")
    return str(e.value)


@pytest.mark.parametrize("bad_stop", [-1.0, 0.0, 2.3])
def test_M1_reddens_when_an_R_is_wired_into_the_stop_column(bad_stop):
    """The 09-23 miswire, inverted: stop_R (−1.0 at entry, 0.0 trailed to
    breakeven, or a positive trail) reaching the column that now holds a price.
    All three collapse stop/cost far below the band; a price never can."""
    b = _book()
    b["positions"][0]["stop"] = bad_stop
    assert "carrying an R, not a price" in _m1_raises(b)


def test_M1_reddens_when_the_cost_column_is_empty_or_zero():
    for bad in (None, 0.0):
        b = _book()
        b["positions"][0]["cost"] = bad
        assert "is not a price" in _m1_raises(b)


def test_M1_reddens_when_a_leg_percent_holds_a_quantity():
    b = _book()
    b["legs"][0]["pct_of_position"] = 1772
    assert "not a share of the position" in _m1_raises(b)


@pytest.mark.parametrize("stop", [104.00, 93.00, 175.50, 307.92])
def test_M1_lets_real_stops_through(stop):
    """Real 09-22/09-23 book values: stops below cost (fresh), at cost (breakeven
    trail) and above it (locked in). The ratio band has to admit all of them —
    unlike the 09-23 relation, which needed a breakeven exemption."""
    b = _book()
    b["positions"][0].update(cost=178.20, stop=stop)
    assert book_out(b, "2026-09-23")["pos"][0][5] == stop


def test_M1_does_not_fire_when_there_is_no_stop_to_check():
    b = _book()
    b["positions"][0]["stop"] = None
    assert book_out(b, "2026-09-23") is not None


# ---------- the page draws what the payload carries ----------

def test_size_percent_reddens_when_it_is_not_a_share_of_the_book():
    """Andy 2026-09-24 added the column; M1 guards it the same way it guards a leg's
    percent — a quantity or a price landing there is out of range."""
    for bad in (0, -3.0, 1772):
        b = _book()
        b["positions"][0]["size_pct"] = bad
        assert "not a share of the book" in _m1_raises(b), bad


def test_the_page_prints_cost_and_stop_as_two_decimal_prices():
    from pathlib import Path
    js = Path("pipeline/content/recap/visual_assets/recap_page.js").read_text()
    book = js[js.index("function book(is, c, V)"):]
    assert "toFixed(2)" in book[:3000], "cost/stop must render as prices, not R"
    assert '<td class="n">0R</td>' not in book, "the constant 0R cost column is gone"


def test_held_sessions_reaches_the_leg_row():
    out = book_out(_book(), "2026-09-23")
    assert out["legs"][0][5] == 3
