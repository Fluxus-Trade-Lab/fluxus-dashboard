"""The gap check: missing is not the question, how long you have is."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from pipeline.reference import gaps as G

# A Friday, so the window walks back over a real trading week.
FRI = dt.date(2026, 8, 14)


def _tree(root, *present):
    """Create only the artifacts named as (ymd, kind)."""
    root = Path(root)
    for ymd, kind in present:
        p = root / G.ARTIFACTS[kind]["path"].format(sym="SPX", ymd=ymd)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}")
    return root


def test_the_window_walks_trading_days_not_calendar_days():
    days = G.trading_days_back(5, FRI)
    assert days[-1] == FRI
    assert all(d.weekday() < 5 for d in days)
    # Five trading days back from a Friday reaches the previous Monday.
    assert days[0] == dt.date(2026, 8, 10)


def test_a_complete_window_says_so_rather_than_printing_nothing(tmp_path):
    present = [(d.strftime("%Y%m%d"), k)
               for d in G.trading_days_back(2, FRI) for k in G.ARTIFACTS]
    r = G.scan(days=2, root=_tree(tmp_path, *present), today=FRI)
    assert r["missing"] == []
    assert "nothing missing" in r["note"]
    assert "complete" in G.report(r)


# --- the three verdicts --------------------------------------------------

def test_a_bar_derived_artifact_is_always_recoverable(tmp_path):
    """Bars persist for years. A profile missing from last month can be rebuilt
    today exactly as it would have been."""
    r = G.scan(days=5, root=tmp_path, today=FRI)
    profiles = [x for x in r["missing"] if x["artifact"] == "profile"]
    assert profiles and all(x["verdict"] == "recoverable" for x in profiles)


def test_todays_own_perishable_gap_is_recoverable_not_expiring(tmp_path):
    """The session that just closed still has its expiry on the chain."""
    r = G.scan(days=1, root=tmp_path, today=FRI)
    today_rows = [x for x in r["missing"] if x["session"] == FRI.isoformat()]
    assert all(x["verdict"] == "recoverable" for x in today_rows)


def test_yesterdays_perishable_gap_is_expiring(tmp_path):
    r = G.scan(days=2, root=tmp_path, today=FRI)
    thu = [x for x in r["missing"]
           if x["session"] == "2026-08-13" and x["artifact"] == "flow_0dte"]
    assert thu and thu[0]["verdict"] == "expiring"


def test_an_older_perishable_gap_is_lost_not_a_backlog_item(tmp_path):
    """The real case: 08-12's 0DTE. A to-do that can never be closed is worse
    than an admission."""
    r = G.scan(days=5, root=tmp_path, today=FRI)
    old = [x for x in r["missing"]
           if x["session"] == "2026-08-11" and x["artifact"] == "flow_0dte"]
    assert old and old[0]["verdict"] == "lost"


def test_lost_and_recoverable_are_never_folded_together(tmp_path):
    r = G.scan(days=5, root=tmp_path, today=FRI)
    assert r["lost"] > 0 and r["recoverable"] > 0
    assert set(x["verdict"] for x in r["missing"]) >= {"lost", "recoverable"}


# --- what the report leads with -----------------------------------------

def test_the_urgent_list_holds_only_what_can_still_be_acted_on(tmp_path):
    r = G.scan(days=5, root=tmp_path, today=FRI)
    u = G.urgent(r)
    assert u and all(x["verdict"] == "expiring" for x in u)
    assert all(x["session"] == "2026-08-13" for x in u)


def test_the_note_leads_with_the_deadline_when_there_is_one(tmp_path):
    r = G.scan(days=5, root=tmp_path, today=FRI)
    assert "TODAY and not" in r["note"]


def test_the_note_says_when_nothing_can_be_done(tmp_path):
    """Only lost gaps: no deadline to lead with, and saying 'act now' would be
    a lie that costs someone an afternoon."""
    # Give every recoverable and every recent artifact, leaving only old
    # perishables missing.
    present = []
    for d in G.trading_days_back(5, FRI):
        ymd = d.strftime("%Y%m%d")
        for k, spec in G.ARTIFACTS.items():
            age = (FRI - d).days
            if not spec["perishable"] or age <= G.PERISHABLE_DAYS:
                present.append((ymd, k))
    r = G.scan(days=5, root=_tree(tmp_path, *present), today=FRI)
    assert r["expiring"] == 0 and r["recoverable"] == 0 and r["lost"] > 0
    assert "should come out of the plan" in r["note"]


def test_every_gap_names_what_its_source_was(tmp_path):
    """A verdict without its reason cannot be argued with."""
    r = G.scan(days=3, root=tmp_path, today=FRI)
    assert all(x["source"] for x in r["missing"])
    gex = next(x for x in r["missing"] if x["artifact"] == "gex")
    assert "snapshot with no history" in gex["source"]


def test_the_report_puts_expiring_first(tmp_path):
    txt = G.report(G.scan(days=5, root=tmp_path, today=FRI))
    assert txt.index("[expiring]") < txt.index("[lost]")
    assert "pull these now" in txt
