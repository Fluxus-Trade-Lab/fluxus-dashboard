"""State board contract: evidence always present, unmeasurable stays None,
and the propagation current never resumes after it dies."""
from __future__ import annotations

import pandas as pd
import pytest

from pipeline.screeners.state_board import (
    LEVELS, build, propagation_chain, state_board,
)


def frame(**over) -> pd.DataFrame:
    base = dict(up_25pct_qtr=342, down_25pct_qtr=523, up_4pct=231, down_4pct=288,
                ratio_5d=0.9905, t2108=45.77, pct_above_20sma=40.7,
                pct_above_200sma=46.77, new_highs=29, new_lows=12, net_advances=-336)
    base.update(over)
    # six rows so the five-session peak window is populated
    rows = [dict(base, down_4pct=637) for _ in range(5)] + [base]
    return pd.DataFrame(rows)


def health(spy_up=True, qqq_up=False):
    def candles(up):
        flat = [{"c": 100.0} for _ in range(60)]
        flat[-1] = {"c": 120.0 if up else 80.0}
        return flat
    return {"spy": {"candles": candles(spy_up)}, "qqq": {"candles": candles(qqq_up)}}


def test_every_row_carries_evidence():
    for r in state_board(frame(), health()):
        assert r["evidence"], f"{r['key']} has no evidence string"
        assert r["level"] is None or 0 <= r["level"] < len(LEVELS)
        assert r["level_label"] == (None if r["level"] is None else LEVELS[r["level"]])


def test_rates_is_blank_not_zero():
    """The design's whole honesty claim rests on this one."""
    rates = next(r for r in state_board(frame(), health()) if r["key"] == "rates")
    assert rates["level"] is None
    assert rates["level_label"] is None
    assert "not wired" in rates["evidence"]


def test_missing_input_yields_none_not_a_guess():
    board = state_board(frame(pct_above_20sma=float("nan")), health())
    breadth = next(r for r in board if r["key"] == "breadth")
    assert breadth["level"] is None


def test_no_health_leaves_index_repair_unmeasured():
    board = state_board(frame(), None)
    idx = next(r for r in board if r["key"] == "index repair")
    assert idx["level"] is None


def test_index_repair_counts_benchmarks_above_their_50day():
    board = state_board(frame(), health(spy_up=True, qqq_up=False))
    idx = next(r for r in board if r["key"] == "index repair")
    assert idx["level"] == 3          # one of two
    assert "1 of 2" in idx["evidence"]
    both = next(r for r in state_board(frame(), health(True, True))
                if r["key"] == "index repair")
    assert both["level"] == len(LEVELS) - 1


def test_selling_pressure_is_relative_to_the_recent_peak():
    """288 against a 637 peak is easing; the same 288 with no prior spike is not."""
    easing = next(r for r in state_board(frame(), health()) if r["key"] == "selling pressure")
    assert easing["level"] == 3
    flat = pd.DataFrame([dict(up_25pct_qtr=342, down_25pct_qtr=523, up_4pct=231,
                              down_4pct=288, ratio_5d=1.0, t2108=45.0,
                              pct_above_20sma=40.0, pct_above_200sma=46.0,
                              new_highs=29, new_lows=12, net_advances=-1)
                         for _ in range(6)])
    steady = next(r for r in state_board(flat, health()) if r["key"] == "selling pressure")
    assert steady["level"] == 1


def test_chain_current_never_resumes_after_it_dies():
    board = [
        {"key": "index repair", "level": 4, "evidence": "x"},
        {"key": "thrust", "level": 2, "evidence": "x"},
        {"key": "breadth", "level": 0, "evidence": "x"},   # dies here
        {"key": "extremes", "level": 4, "evidence": "x"},  # measured high again
        {"key": "confirmation", "level": 3, "evidence": "x"},
    ]
    links = propagation_chain(board)
    carrying = [l["carrying"] for l in links]
    assert carrying == sorted(carrying, reverse=True), carrying
    assert links[2]["state"] == "unlit"
    assert links[3]["carrying"] == 0.0
    # the high reading downstream is kept, but flagged as not fed by the chain
    assert links[3]["measured"] == 1.0
    assert links[3]["fed"] is False


def test_chain_marks_unmeasured_links_without_breaking_the_run():
    links = propagation_chain([
        {"key": "index repair", "level": 4, "evidence": "x"},
        {"key": "thrust", "level": None, "evidence": "x"},
        {"key": "breadth", "level": 3, "evidence": "x"},
    ] )
    assert links[1]["state"] == "unmeasured"
    assert links[1]["carrying"] is None
    assert links[2]["carrying"] is not None


def test_build_block_shape():
    blk = build(frame(), health())
    assert blk["levels"] == LEVELS
    assert blk["total"] == len(blk["rows"]) == 9
    assert blk["measured"] == 8            # rates is the one blank
    assert len(blk["chain"]) == 5


def test_pure_no_peek_prefix_replays_identically():
    """Scoring a truncated frame must not read anything after it."""
    f = frame()
    long = pd.concat([f, pd.DataFrame([dict(f.iloc[-1], down_4pct=9999)])], ignore_index=True)
    assert state_board(f, health()) == state_board(long.iloc[:len(f)], health())


def test_empty_frame_returns_nothing_rather_than_crashing():
    assert state_board(pd.DataFrame(), health()) == []


@pytest.mark.parametrize("r5,net,expect", [
    (0.9905, -336, "needs to clear 1.0"),
    (1.7539, -286, "net advances"),      # ratio is fine; name the gate that is shut
    (1.3000,  120, "clear of 1.2"),
    # Regression: two gates, and net sitting at exactly zero used to fall through
    # to the ratio branch — printing "not yet clear of 1.2" beside a 2.07 reading.
    (2.0719,    0, "net advances"),
])
def test_confirmation_evidence_matches_its_own_number(r5, net, expect):
    """A caption reading 'needs to clear 1.0' under a 1.75 reading is a lie."""
    board = state_board(frame(ratio_5d=r5, net_advances=net), health())
    conf = next(r for r in board if r["key"] == "confirmation")
    assert expect in conf["evidence"], conf["evidence"]


def test_confirmation_never_denies_a_number_it_prints():
    """Whatever the caption says, it must not contradict the ratio beside it."""
    for r5 in (0.8, 1.05, 1.25, 2.07):
        for net in (-300, 0, 300):
            conf = next(r for r in state_board(frame(ratio_5d=r5, net_advances=net), health())
                        if r["key"] == "confirmation")
            ev = conf["evidence"]
            if r5 > 1.2:
                assert "not yet clear of 1.2" not in ev, (r5, net, ev)
            if r5 > 1.0:
                assert "needs to clear 1.0" not in ev, (r5, net, ev)
