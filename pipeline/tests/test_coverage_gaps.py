"""data/history/coverage_gaps.json must keep describing the real archive.

A declaration that drifts from the data is worse than none: it tells readers
the gap is somewhere it is not. So the ticker_events entry is re-measured here
(first/last/sessions/rows), and both neighbours must be healthy -- if someone
recomputes a session inside the window, this goes red and the file gets edited.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GAPS = REPO / "data" / "history" / "coverage_gaps.json"
EVENTS = REPO / "data" / "history" / "ticker_events.csv"


def _gap(archive):
    return next(g for g in json.loads(GAPS.read_text())["gaps"] if g["archive"] == archive)


def _after_l_share():
    by = defaultdict(list)
    with EVENTS.open(newline="") as fh:
        for r in csv.DictReader(fh):
            by[r["date"]].append(r["ticker"])
    return {d: (len(ts), sum(t[:1] > "L" for t in ts)) for d, ts in sorted(by.items())}


def test_every_entry_names_an_existing_archive_and_a_reason():
    blob = json.loads(GAPS.read_text())
    for g in blob["gaps"]:
        for a in g["archive"].split(" + "):
            assert (REPO / a).exists(), a
        assert g["first"] <= g["last"]
        assert g["cause"] and g["backfill"] and g["declared"]
    for b in blob["definition_breaks"]:
        assert b["field"] and b["changed"] and b["declared"] and b["note"]
        for a in b["archives"]:
            assert (REPO / a).exists(), a


def test_breadth_entry_agrees_with_the_read_time_flag():
    """The declaration and breadth_signals.universe_truncated must name the same sessions."""
    from pipeline.screeners.breadth_signals import universe_truncated
    g = _gap("data/history/breadth_archive.csv")
    with (REPO / g["archive"]).open(newline="") as fh:
        flagged = [r["date"] for r in csv.DictReader(fh) if universe_truncated(r)]
    assert (flagged[0], flagged[-1], len(flagged)) == (g["first"], g["last"], g["sessions"])


@pytest.mark.skipif(not EVENTS.exists(), reason="archive not in checkout")
def test_ticker_events_gap_matches_the_archive_exactly():
    g = _gap("data/history/ticker_events.csv")
    share = _after_l_share()
    days = list(share)
    inside = [d for d in days if g["first"] <= d <= g["last"]]
    assert len(inside) == g["sessions"]
    assert sum(share[d][0] for d in inside) == g["rows"]
    assert all(share[d][1] == 0 for d in inside), "a declared session now has M-Z rows"
    before = days[days.index(inside[0]) - 1]
    after = days[days.index(inside[-1]) + 1]
    for d in (before, after):                      # the edges are real edges
        n, mz = share[d]
        assert mz / n > 0.15, (d, n, mz)
