"""The gap check: missing is not the question, whether it is still reachable is."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from pipeline.reference import gaps as G

TUE = dt.date(2026, 8, 18)
# What the chain actually listed at 23:10 ET on 2026-08-18. 08-17 and 08-18 had
# already gone, which is the observation that replaced the day-count guess.
LISTED = {"20260819", "20260820", "20260821", "20260824", "20260918"}


def _tree(root, *present):
    root = Path(root)
    for ymd, kind in present:
        p = root / G.ARTIFACTS[kind]["path"].format(sym="SPX", ymd=ymd)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}")
    return root


def test_the_window_walks_trading_days_not_calendar_days():
    days = G.trading_days_back(5, dt.date(2026, 8, 14))
    assert days[-1] == dt.date(2026, 8, 14)
    assert all(d.weekday() < 5 for d in days)
    assert days[0] == dt.date(2026, 8, 10)


def test_a_complete_window_says_so_rather_than_printing_nothing(tmp_path):
    present = [(d.strftime("%Y%m%d"), k)
               for d in G.trading_days_back(2, TUE) for k in G.ARTIFACTS]
    r = G.scan(days=2, root=_tree(tmp_path, *present), today=TUE,
               listed_expiries=LISTED)
    assert r["missing"] == []
    assert "nothing missing" in r["note"]


# --- the correction: a deadline is looked up, never counted --------------

def test_an_expiry_the_chain_no_longer_lists_is_lost(tmp_path):
    """The real case. On 2026-08-18 the day-count version called 08-17's 0DTE
    `expiring` and 08-18's `recoverable`. Both expiries were already gone."""
    r = G.scan(days=3, root=tmp_path, today=TUE, listed_expiries=LISTED)
    for session in ("2026-08-17", "2026-08-18"):
        row = next(x for x in r["missing"]
                   if x["session"] == session and x["artifact"] == "flow_0dte")
        assert row["verdict"] == "lost"
        assert row["needs_expiry"] == session.replace("-", "")


def test_an_expiry_still_listed_for_a_past_session_is_expiring(tmp_path):
    """08-18's tenor 1 needs 08-19, which the chain still lists — and that was
    the one thing still rescuable that night."""
    r = G.scan(days=2, root=tmp_path, today=dt.date(2026, 8, 19),
               listed_expiries=LISTED)
    row = next(x for x in r["missing"]
               if x["session"] == "2026-08-18" and x["artifact"] == "flow_1dte")
    assert row["needs_expiry"] == "20260819"
    assert row["verdict"] == "expiring"


def test_todays_own_gap_is_recoverable_not_expiring(tmp_path):
    """The session that just closed still has all of today to be pulled. Calling
    it `expiring` would cry wolf on the one case that is never urgent."""
    r = G.scan(days=1, root=tmp_path, today=TUE, listed_expiries=LISTED)
    row = next(x for x in r["missing"] if x["artifact"] == "flow_1dte")
    assert row["needs_expiry"] == "20260819"
    assert row["verdict"] == "recoverable"


def test_tenor_one_skips_the_weekend():
    """A Friday's tenor-1 expiry is the Monday, not the Saturday."""
    assert G.ARTIFACTS["flow_1dte"]["needs_expiry"](
        dt.date(2026, 8, 14)) == dt.date(2026, 8, 17)


def test_without_the_chain_every_contract_gap_is_unknown(tmp_path):
    """Never silently downgraded to recoverable — that substitution cost 08-17."""
    r = G.scan(days=3, root=tmp_path, today=TUE)
    contract = [x for x in r["missing"] if x["artifact"].startswith("flow_")]
    assert contract and all(x["verdict"] == "unknown" for x in contract)
    assert r["chain_consulted"] is False
    assert "not assumed" in r["note"]
    assert "chain NOT consulted" in G.report(r)


def test_unknown_is_not_urgent(tmp_path):
    """We do not know of anything to do, which is not knowing there is nothing."""
    assert G.urgent(G.scan(days=3, root=tmp_path, today=TUE)) == []


# --- the artifacts that are not contracts -------------------------------

def test_bars_are_always_recoverable(tmp_path):
    r = G.scan(days=5, root=tmp_path, today=TUE, listed_expiries=LISTED)
    prof = [x for x in r["missing"] if x["artifact"] == "profile"]
    assert prof and all(x["verdict"] == "recoverable" for x in prof)


def test_a_past_open_interest_snapshot_cannot_be_retaken(tmp_path):
    r = G.scan(days=5, root=tmp_path, today=TUE, listed_expiries=LISTED)
    old = next(x for x in r["missing"]
               if x["artifact"] == "gex" and x["session"] == "2026-08-12")
    assert old["verdict"] == "lost"
    assert "snapshot with no history" in old["source"]
    today_gex = next(x for x in r["missing"]
                     if x["artifact"] == "gex" and x["session"] == TUE.isoformat())
    assert today_gex["verdict"] == "recoverable"


# --- reporting ----------------------------------------------------------

def test_every_gap_names_the_expiry_it_needs(tmp_path):
    r = G.scan(days=2, root=tmp_path, today=TUE, listed_expiries=LISTED)
    for x in r["missing"]:
        if x["artifact"].startswith("flow_"):
            assert x["needs_expiry"]
        assert x["source"]


def test_the_report_puts_expiring_first(tmp_path):
    txt = G.report(G.scan(days=3, root=tmp_path, today=dt.date(2026, 8, 19),
                          listed_expiries=LISTED))
    assert "[expiring]" in txt
    assert txt.index("[expiring]") < txt.index("[lost]")
    assert "still lists these expiries TODAY" in txt


def test_the_note_says_when_nothing_can_be_done(tmp_path):
    present = []
    for d in G.trading_days_back(3, TUE):
        ymd = d.strftime("%Y%m%d")
        present += [(ymd, "profile"), (ymd, "gex")]
    # 08-18's own tenor 1 needs 08-19, which IS listed, so it is genuinely
    # recoverable and belongs on disk for this fixture -- otherwise the case
    # under test is not "nothing can be done".
    present += [("20260818", "flow_1dte")]
    r = G.scan(days=3, root=_tree(tmp_path, *present), today=TUE,
               listed_expiries=LISTED)
    assert r["expiring"] == 0 and r["recoverable"] == 0 and r["lost"] > 0
    assert "should come out of the plan" in r["note"]


def test_no_verdict_outside_the_declared_set(tmp_path):
    r = G.scan(days=5, root=tmp_path, today=TUE, listed_expiries=LISTED)
    assert all(x["verdict"] in G.VERDICTS for x in r["missing"])
