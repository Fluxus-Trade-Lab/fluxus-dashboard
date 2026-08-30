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


def test_a_rate_limit_wall_warns_and_does_not_block_the_night(tmp_path):
    """2026-08-27, live: `fundamentals status='walled'` exited 1, `Commit and
    push` was skipped, and the dashboard sat on a four-day-old session because
    an OPTIONAL enrichment hit a rate limit. `walled` is the fundamentals
    guard's own word for partial coverage; `partial` was already a warning.
    Only the vocabulary disagreed."""
    row = _row("2026-08-27", guards=_guards(
        fundamentals={"status": "walled", "due": 400, "ok": 138, "failed": 0,
                      "walled": True, "store": 5634}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done="2026-08-27")
    assert out["ok"], out["runs"][0]["violations"]     # the night still ships
    assert any("L2 fundamentals walled" in x for x in out["runs"][0]["warnings"])
    # and it is not silent: a warning still prints and still lands in the JSON
    assert not out["runs"][0]["violations"]


def test_an_unknown_status_word_is_still_fatal(tmp_path):
    """The list is a list, not a shrug. A word nobody has classified must stop
    the publish -- that is what caught the 08-27 gap in the first place."""
    row = _row("2026-08-21", guards=_guards(
        fundamentals={"status": "wedged", "due": 400, "ok": 400, "failed": 0, "store": 5630}))
    out = L.run(_write(tmp_path, [row]), window=0, last_done=LAST)
    assert not out["ok"]
    assert any("L2 fundamentals status='wedged'" in x for x in out["runs"][0]["violations"])


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


class TestSupersededAttempts:
    """A recorded failure is history, not a current defect.

    2026-08-29 the workflow started committing the ledger line of runs a gate
    had stopped (`if: failure()`) -- the change that finally made failed
    nights visible. It immediately made THIS auditor fail every session that
    contained a caught-and-recovered failure, blocking the very publish the
    recovery had earned. The gate worked, a later attempt succeeded, and the
    data on main is the good one; judging the session by its worst attempt
    turns a working plan B into an outage.
    """

    def _ledger(self, tmp_path, rows):
        import json
        p = tmp_path / "led.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return p

    def _run(self, session, *, ok, sha="abc1234"):
        """A ledger line that either passes or trips an L2 guard."""
        return {"session": session, "code_sha": sha, "trigger": "schedule",
                "universe_rows": 5600,
                "guards": {"universe_quality": {"status": "ok" if ok else "severe",
                                                "rows": 5600},
                           "breadth": {"status": "ok", "regime_score": 50,
                                       "enriched": ["regime", "state_board",
                                                    "verdict", "conditions"]}}}

    def test_a_failed_attempt_followed_by_a_good_one_is_not_a_violation(self, tmp_path):
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=False), self._run(s, ok=True)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert rep["violations"] == 0, rep
        assert rep["ok"] is True

    def test_the_failure_is_still_reported_as_a_warning(self, tmp_path):
        """Demoted, never swallowed -- the record is the whole point."""
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=False), self._run(s, ok=True)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert rep["warnings"] >= 1
        text = " ".join(w for r in rep["runs"] for w in r["warnings"])
        assert "superseded attempt" in text
        assert any(r.get("superseded") for r in rep["runs"])

    def test_the_LAST_attempt_failing_is_still_a_violation(self, tmp_path):
        """The positive control: if the newest attempt of the session is the
        broken one, nothing was recovered and the gate must still bite."""
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=True), self._run(s, ok=False)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert rep["violations"] >= 1, "a session whose last run failed must fail"
        assert rep["ok"] is False

    def test_every_run_report_keeps_its_violations_key(self, tmp_path):
        """Demotion emptied the list; an earlier version popped the key and
        crashed the printer (KeyError: 'violations')."""
        import datetime as dt
        from pipeline.tools.audit_ledger import run
        s = "2026-08-28"
        led = self._ledger(tmp_path, [self._run(s, ok=False), self._run(s, ok=True)])
        rep = run(led, last_done=dt.date(2026, 8, 28))
        assert all("violations" in r for r in rep["runs"])
