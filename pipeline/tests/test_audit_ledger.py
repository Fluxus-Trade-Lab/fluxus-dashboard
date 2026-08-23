"""Run-ledger invariants (pipeline/tools/audit_ledger.py).

The fixtures are the real shapes out of data/history/run_ledger.jsonl: the
08-19 blackout line (breadth ok / regime_score null / no enriched blocks) and
the healthy re-run of that same session four hours later.
"""
from __future__ import annotations

import datetime as dt
import json

from pipeline.tools import audit_ledger as L

LAST = dt.date(2026, 8, 21)


def _guards(**over):
    g = {
        "fundamentals":     {"status": "ok", "due": 400, "ok": 400, "failed": 0, "walled": False, "store": 5630},
        "breadth":          {"status": "ok", "reason": None, "regime_score": 71.9,
                             "enriched": ["conditions", "regime", "state_board", "verdict"]},
        "ticker_events":    {"status": "ok", "reason": None, "rows_today": 2303, "event_date": "2026-08-21"},
        "asset_signals":    {"status": "ok", "count": 26},
        "universe_quality": {"status": "ok", "rows": 5627, "degraded": ["perf_ytd"]},
        "watchlist":        {"status": "ok", "gated": 2053, "panels": {"true_market_leaders": 58}},
        "shortlist":        {"status": "ok", "cards": 6},
        "site_quality":     {"status": "ok", "sources": {"etf_data": "ok", "signals": "ok"}},
        "screeners":        {"status": "ok", "counts": {"momentum_97": 169}},
    }
    g.update(over)
    return g


def _row(session, **over):
    r = {"session": session, "started_utc": f"{session}T21:52:55+00:00",
         "finished_utc": f"{session}T22:10:42+00:00", "code_sha": "c637fe1",
         "trigger": "schedule", "run_id": "1", "guards": _guards(), "wrote": [], "errors": []}
    r.update(over)
    return r


def _write(tmp_path, rows):
    p = tmp_path / "run_ledger.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def test_healthy_run_passes(tmp_path):
    out = L.run(_write(tmp_path, [_row("2026-08-20"), _row("2026-08-21")]), window=0, last_done=LAST)
    assert out["ok"] and out["violations"] == 0, out["runs"]


def test_the_0819_blackout_line_is_an_L3_violation(tmp_path):
    """status ok + null evidence: the shape nothing read on the night."""
    blackout = _row("2026-08-21", guards=_guards(
        breadth={"status": "ok", "reason": None, "regime_score": None}))
    out = L.run(_write(tmp_path, [blackout]), window=0, last_done=LAST)
    assert not out["ok"]
    v = out["runs"][0]["violations"]
    assert any(x.startswith("L3 breadth") and "regime_score" in x for x in v), v
    assert any(x.startswith("L3 breadth") and "enriched" in x for x in v), v


def test_partial_enriched_blocks_still_fail(tmp_path):
    """three of the four blocks is not four -- ok has to mean all of them."""
    row = _row("2026-08-21", guards=_guards(
        breadth={"status": "ok", "regime_score": 71.9, "enriched": ["conditions", "regime", "verdict"]}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    assert not out["ok"]
    assert any("enriched" in x for x in out["runs"][0]["violations"])


def test_missing_session_is_L1(tmp_path):
    """no line for the last completed session = the run never happened."""
    out = L.run(_write(tmp_path, [_row("2026-08-20")]), window=0, last_done=LAST)
    assert not out["ok"]
    assert any(t.startswith("L1") and "2026-08-21" in t for t in out["top"]), out["top"]


def test_empty_ledger_is_L1(tmp_path):
    p = tmp_path / "run_ledger.jsonl"
    p.write_text("", encoding="utf-8")
    out = L.run(p, window=0, last_done=LAST)
    assert not out["ok"] and any(t.startswith("L1") for t in out["top"])


def test_non_ok_status_and_errors(tmp_path):
    row = _row("2026-08-21",
               guards=_guards(breadth={"status": "fail", "reason": "stale store"},
                              universe_quality={"status": "degraded", "rows": 5627}),
               errors=[{"where": "screeners", "msg": "yfinance 429"}])
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    rep = out["runs"][0]
    assert any(x.startswith("L2 breadth status='fail'") for x in rep["violations"]), rep["violations"]
    assert any(x.startswith("L4 error in screeners") for x in rep["violations"]), rep["violations"]
    assert any(x.startswith("L2 universe_quality degraded") for x in rep["warnings"]), rep["warnings"]
    # a failed guard is not asked for evidence -- L2 already said it
    assert not any(x.startswith("L3 breadth") for x in rep["violations"])


def test_guard_dropout_is_a_warning(tmp_path):
    g = _guards()
    g.pop("shortlist")
    out = L.run(_write(tmp_path, [_row("2026-08-20"), _row("2026-08-21", guards=g)]),
                window=0, last_done=LAST)
    assert out["ok"]                       # a dropout is a warning, not a violation
    assert any("L5" in x and "shortlist" in x for x in out["runs"][-1]["warnings"])


def test_same_session_rerun_is_reported_not_fatal(tmp_path):
    out = L.run(_write(tmp_path, [_row("2026-08-21"), _row("2026-08-21", code_sha="894fccc")]),
                window=0, last_done=LAST)
    assert out["ok"]
    assert any(t.startswith("L6") and "2 lines" in t for t in out["top"])


def test_fundamentals_failure_rate_warns(tmp_path):
    row = _row("2026-08-21", guards=_guards(
        fundamentals={"status": "ok", "due": 400, "ok": 277, "failed": 123, "store": 5630}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    assert out["ok"]                                   # a warning, not a gate
    assert out["runs"][0]["fund_fail_rate"] == 0.307                # 123/400 = 0.3075, banker's rounding
    assert any("L6 fundamentals failed 123/400" in x for x in out["runs"][0]["warnings"])


def test_window_limits_what_is_audited(tmp_path):
    bad = _row("2026-08-19", guards=_guards(breadth={"status": "ok", "regime_score": None}))
    p = _write(tmp_path, [bad, _row("2026-08-20"), _row("2026-08-21")])
    assert L.run(p, window=0, last_done=LAST)["violations"] == 2      # sees the old bad line
    assert L.run(p, window=1, last_done=LAST)["ok"]                   # newest session only
