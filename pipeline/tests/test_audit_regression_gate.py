"""Positive controls for the regression gate.

The gate exists because a real run overwrote a healthy one and every guard we
owned stayed silent. So the tests that matter most are the two real pairs out
of `run_ledger.jsonl` -- 2026-08-27 (the incident) and 2026-08-19 (a re-run
that genuinely repaired the session). One must go red, the other must stay
green, and a gate that cannot tell them apart is not measuring damage, it is
measuring change.
"""
from __future__ import annotations

import json

import pytest

from pipeline.tools import audit_regression_gate as arg


def row(session="2026-08-27", run_id="r1", finished="2026-08-28T01:00:00+00:00", **guards):
    return {"session": session, "run_id": run_id, "finished_utc": finished,
            "guards": guards}


def uq(status="ok", rows=5630, bars_missing=64, bars_stale=143,
       tradeable=2562, unmeasurable=75, degraded=None):
    return {"status": status, "rows": rows, "bars_missing": bars_missing,
            "bars_stale": bars_stale,
            "tradeable": {"tradeable": tradeable, "excluded": 2871,
                          "unmeasurable": unmeasurable},
            "degraded": list(degraded if degraded is not None else ["perf_ytd"])}


# --------------------------------------------------------------------------
# The two real pairs. These are the numbers from the autopsy, typed from
# `data/history/run_ledger.jsonl`, not invented.
# --------------------------------------------------------------------------

INCIDENT_BASELINE = row(run_id="33141646318",
                        finished="2026-08-28T04:40:00+00:00",
                        universe_quality=uq(status="ok", bars_missing=64,
                                            unmeasurable=75, tradeable=2562,
                                            degraded=["perf_ytd"]),
                        ticker_events={"status": "ok", "rows_today": 2169},
                        breadth={"status": "ok", "regime_score": 43.8})

INCIDENT_CANDIDATE = row(run_id="33145206555",
                         finished="2026-08-28T05:36:00+00:00",
                         universe_quality=uq(status="degraded", bars_missing=266,
                                             unmeasurable=277, tradeable=2465,
                                             degraded=["bar_date", "bar_scale_mismatch",
                                                       "bars_stale", "perf_ytd",
                                                       "vol_5d_50d"]),
                         ticker_events={"status": "ok", "rows_today": 2133},
                         breadth={"status": "ok", "regime_score": 34.4})

# 2026-08-19: the first run was degraded, the re-run repaired it. A gate that
# flags this is unusable -- every genuine fix would have to fight it.
REPAIR_BASELINE = row(session="2026-08-19", run_id="32306056351",
                      finished="2026-08-20T01:00:00+00:00",
                      universe_quality=uq(status="degraded", rows=5622,
                                          degraded=["a", "b", "c"]),
                      ticker_events={"status": "ok", "rows_today": 2506})
REPAIR_CANDIDATE = row(session="2026-08-19", run_id="32327291391",
                       finished="2026-08-20T06:00:00+00:00",
                       universe_quality=uq(status="ok", rows=5622,
                                           degraded=["a"]),
                       ticker_events={"status": "ok", "rows_today": 2520})


def test_the_incident_is_reported():
    rep = arg.compare(INCIDENT_BASELINE, INCIDENT_CANDIDATE)
    assert not rep["ok"]
    assert any("R1 universe_quality: ok -> degraded" in v for v in rep["violations"])


def test_the_incident_names_the_numbers_from_the_autopsy():
    rep = arg.compare(INCIDENT_BASELINE, INCIDENT_CANDIDATE)
    blob = " ".join(rep["warnings"])
    assert "bars_missing: 64 -> 266" in blob
    assert "unmeasurable: 75 -> 277" in blob
    # the four fields that newly went degraded, by name, none of them perf_ytd
    r3 = [f for f in rep["findings"] if f["rule"] == "R3"][0]
    assert sorted(r3["new_fields"]) == ["bar_date", "bar_scale_mismatch",
                                        "bars_stale", "vol_5d_50d"]


def test_a_repair_run_stays_green():
    rep = arg.compare(REPAIR_BASELINE, REPAIR_CANDIDATE)
    assert rep["ok"], rep["violations"]
    assert not rep["warnings"], rep["warnings"]


def test_two_healthy_runs_of_the_same_session_stay_green():
    a = row(run_id="33138813133", finished="2026-08-28T03:40:00+00:00",
            universe_quality=uq(bars_missing=64, unmeasurable=75))
    b = row(run_id="33141646318", finished="2026-08-28T04:40:00+00:00",
            universe_quality=uq(bars_missing=64, unmeasurable=75))
    rep = arg.compare(a, b)
    assert rep["ok"] and not rep["warnings"]


# --------------------------------------------------------------------------
# R1 -- the status ladder
# --------------------------------------------------------------------------

@pytest.mark.parametrize("before,after,expect_violation", [
    ("ok", "ok", False),
    ("ok", "degraded", True),
    ("ok", "severe", True),
    ("ok", "fail", True),
    ("degraded", "severe", True),
    ("degraded", "ok", False),      # repair
    ("severe", "degraded", False),  # partial repair
    ("severe", "severe", False),    # already bad, no *new* damage
    ("degraded", "stale", False),   # same rank, different word
])
def test_status_ladder(before, after, expect_violation):
    rep = arg.compare(row(universe_quality={"status": before}),
                      row(universe_quality={"status": after}))
    assert bool(rep["violations"]) is expect_violation


def test_unknown_status_word_is_not_guessed_at():
    rep = arg.compare(row(universe_quality={"status": "banana"}),
                      row(universe_quality={"status": "ok"}))
    assert rep["ok"] and not rep["warnings"]


def test_status_comparison_is_case_insensitive():
    rep = arg.compare(row(universe_quality={"status": "OK"}),
                      row(universe_quality={"status": "Degraded"}))
    assert rep["violations"]


def test_every_watched_guard_carries_its_own_ladder():
    for guard in arg.STATUS_FIELDS:
        rep = arg.compare(row(**{guard: {"status": "ok"}}),
                          row(**{guard: {"status": "severe"}}))
        assert rep["violations"], f"{guard} downgrade went unreported"


# --------------------------------------------------------------------------
# R2 -- direction, which is the whole point
# --------------------------------------------------------------------------

def test_up_metric_flags_a_drop_and_ignores_a_rise():
    dropped = arg.compare(row(universe_quality=uq(tradeable=2562)),
                          row(universe_quality=uq(tradeable=2000)))
    assert any("tradeable" in w for w in dropped["warnings"])
    grew = arg.compare(row(universe_quality=uq(tradeable=2562)),
                       row(universe_quality=uq(tradeable=3000)))
    assert not [w for w in grew["warnings"] if "R2 tradeable" in w]


def test_down_metric_flags_a_rise_and_ignores_a_drop():
    rose = arg.compare(row(universe_quality=uq(bars_missing=64)),
                       row(universe_quality=uq(bars_missing=266)))
    assert any("bars_missing" in w for w in rose["warnings"])
    fell = arg.compare(row(universe_quality=uq(bars_missing=266)),
                       row(universe_quality=uq(bars_missing=64)))
    assert not [w for w in fell["warnings"] if "bars_missing" in w]


def test_both_direction_metric_flags_either_way():
    te = {"status": "ok", "rows_today": 2000}
    up = arg.compare(row(ticker_events=te),
                     row(ticker_events={"status": "ok", "rows_today": 5810}))
    down = arg.compare(row(ticker_events=te),
                       row(ticker_events={"status": "ok", "rows_today": 100}))
    assert any("ticker_events rows" in w for w in up["warnings"])
    assert any("ticker_events rows" in w for w in down["warnings"])


def test_movement_inside_tolerance_is_silent():
    # 64 -> 67 is +4.7%, under the 5% tolerance
    rep = arg.compare(row(universe_quality=uq(bars_missing=64)),
                      row(universe_quality=uq(bars_missing=67)))
    assert not rep["warnings"], rep["warnings"]


def test_movement_just_past_tolerance_is_reported():
    # 64 -> 68 is +6.25%
    rep = arg.compare(row(universe_quality=uq(bars_missing=64)),
                      row(universe_quality=uq(bars_missing=68)))
    assert any("bars_missing" in w for w in rep["warnings"])


def test_regime_score_is_not_treated_as_a_quality_metric():
    """43.8 -> 34.4 is the market moving, not our data rotting."""
    rep = arg.compare(row(breadth={"status": "ok", "regime_score": 43.8}),
                      row(breadth={"status": "ok", "regime_score": 34.4}))
    assert rep["ok"] and not rep["warnings"]


def test_zero_baseline_reports_a_rise_on_a_down_metric_without_dividing():
    rep = arg.compare(row(universe_quality=uq(bars_missing=0)),
                      row(universe_quality=uq(bars_missing=300)))
    assert any("bars_missing: 0 -> 300" in w for w in rep["warnings"])


def test_zero_baseline_on_an_up_metric_is_an_improvement_not_a_finding():
    rep = arg.compare(row(universe_quality=uq(tradeable=0)),
                      row(universe_quality=uq(tradeable=2500)))
    assert not [w for w in rep["warnings"] if "R2 tradeable" in w]


def test_booleans_are_not_counted_as_numbers():
    rep = arg.compare(row(fundamentals={"status": "ok", "ok": True}),
                      row(fundamentals={"status": "ok", "ok": False}))
    assert not rep["warnings"]


def test_a_missing_metric_on_either_side_is_skipped_not_assumed_zero():
    rep = arg.compare(row(universe_quality={"status": "ok"}),
                      row(universe_quality=uq(bars_missing=9999)))
    assert rep["ok"] and not rep["warnings"]


# --------------------------------------------------------------------------
# R3 and --strict
# --------------------------------------------------------------------------

def test_r3_lists_only_the_newly_degraded_fields():
    rep = arg.compare(row(universe_quality=uq(degraded=["perf_ytd"])),
                      row(universe_quality=uq(degraded=["perf_ytd", "atr"])))
    r3 = [f for f in rep["findings"] if f["rule"] == "R3"][0]
    assert r3["new_fields"] == ["atr"]


def test_r3_silent_when_the_degraded_set_shrinks():
    rep = arg.compare(row(universe_quality=uq(degraded=["perf_ytd", "atr"])),
                      row(universe_quality=uq(degraded=["perf_ytd"])))
    assert not [f for f in rep["findings"] if f["rule"] == "R3"]


def test_r3_truncates_a_long_list_but_says_how_many_it_hid():
    new = [f"f{i}" for i in range(20)]
    rep = arg.compare(row(universe_quality=uq(degraded=[])),
                      row(universe_quality=uq(degraded=new)))
    msg = [w for w in rep["warnings"] if w.startswith("R3")][0]
    assert "+12 more" in msg and "degraded +20" in msg


def test_strict_promotes_counts_and_sets_to_violations():
    loose = arg.compare(INCIDENT_BASELINE, INCIDENT_CANDIDATE)
    strict = arg.compare(INCIDENT_BASELINE, INCIDENT_CANDIDATE, strict=True)
    assert loose["warnings"] and not strict["warnings"]
    assert len(strict["violations"]) == len(loose["violations"]) + len(loose["warnings"])


def test_strict_does_not_invent_findings():
    strict = arg.compare(REPAIR_BASELINE, REPAIR_CANDIDATE, strict=True)
    assert strict["ok"]


# --------------------------------------------------------------------------
# audit() -- ordering, pairing, and what it admits it cannot see
# --------------------------------------------------------------------------

def test_runs_are_ordered_by_finish_time_not_file_order():
    late = row(run_id="late", finished="2026-08-28T05:36:00+00:00",
               universe_quality=uq(status="degraded"))
    early = row(run_id="early", finished="2026-08-28T04:40:00+00:00",
                universe_quality=uq(status="ok"))
    out = arg.audit([late, early])          # the good run appears second in the file
    assert out["pairs"][0]["baseline_run"] == "early"
    assert out["pairs"][0]["candidate_run"] == "late"
    assert not out["ok"]


def test_a_single_run_session_is_no_baseline_not_clean():
    out = arg.audit([row(session="2026-08-20", run_id="only")])
    assert out["no_baseline"] == ["2026-08-20"]
    assert out["pairs"] == []
    assert out["ok"]  # nothing to report, but the session is named as unchecked


def test_three_runs_produce_two_consecutive_pairs():
    rows = [row(run_id=f"r{i}", finished=f"2026-08-28T0{i}:00:00+00:00")
            for i in (1, 2, 3)]
    out = arg.audit(rows)
    assert [(p["baseline_run"], p["candidate_run"]) for p in out["pairs"]] == \
        [("r1", "r2"), ("r2", "r3")]


def test_sessions_are_never_compared_against_each_other():
    out = arg.audit([row(session="2026-08-20", run_id="a"),
                     row(session="2026-08-21", run_id="b",
                         universe_quality=uq(status="severe"))])
    assert out["pairs"] == []
    assert sorted(out["no_baseline"]) == ["2026-08-20", "2026-08-21"]


def test_session_filter_narrows_the_walk():
    rows = [row(session="2026-08-27", run_id="a", finished="...1"),
            row(session="2026-08-27", run_id="b", finished="...2"),
            row(session="2026-08-28", run_id="c", finished="...3"),
            row(session="2026-08-28", run_id="d", finished="...4")]
    out = arg.audit(rows, session="2026-08-28")
    assert len(out["pairs"]) == 1
    assert out["pairs"][0]["candidate_run"] == "d"


def test_run_missing_a_finish_time_still_pairs_by_start_time():
    a = {"session": "s", "run_id": "a", "started_utc": "2026-08-28T01:00:00+00:00",
         "guards": {"universe_quality": uq(status="ok")}}
    b = {"session": "s", "run_id": "b", "started_utc": "2026-08-28T02:00:00+00:00",
         "guards": {"universe_quality": uq(status="severe")}}
    out = arg.audit([b, a])
    assert out["pairs"][0]["baseline_run"] == "a"
    assert not out["ok"]


# --------------------------------------------------------------------------
# I/O and the CLI contract
# --------------------------------------------------------------------------

def test_load_ledger_skips_blank_and_broken_lines(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_text('{"session":"a"}\n\n{not json}\n{"session":"b"}\n')
    assert [r["session"] for r in arg.load_ledger(p)] == ["a", "b"]


def test_load_ledger_on_a_missing_file_is_empty_not_an_exception(tmp_path):
    assert arg.load_ledger(tmp_path / "nope.jsonl") == []


def _write(tmp_path, rows):
    p = tmp_path / "ledger.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_main_exits_1_on_the_real_incident(tmp_path, capsys):
    p = _write(tmp_path, [INCIDENT_BASELINE, INCIDENT_CANDIDATE])
    assert arg.main(["--ledger", str(p)]) == 1
    assert "REGRESSION" in capsys.readouterr().out


def test_main_exits_0_on_a_repair(tmp_path, capsys):
    p = _write(tmp_path, [REPAIR_BASELINE, REPAIR_CANDIDATE])
    assert arg.main(["--ledger", str(p)]) == 0
    assert "REGRESSION" not in capsys.readouterr().out


def test_main_exits_0_when_only_warnings_fire(tmp_path, capsys):
    a = row(run_id="a", finished="...1", universe_quality=uq(bars_missing=64))
    b = row(run_id="b", finished="...2", universe_quality=uq(bars_missing=266))
    p = _write(tmp_path, [a, b])
    assert arg.main(["--ledger", str(p)]) == 0
    assert "WARN" in capsys.readouterr().out


def test_strict_turns_a_warning_only_pair_fatal(tmp_path):
    a = row(run_id="a", finished="...1", universe_quality=uq(bars_missing=64))
    b = row(run_id="b", finished="...2", universe_quality=uq(bars_missing=266))
    p = _write(tmp_path, [a, b])
    assert arg.main(["--ledger", str(p), "--strict"]) == 1


def test_main_exits_2_on_an_unreadable_ledger(tmp_path):
    assert arg.main(["--ledger", str(tmp_path / "gone.jsonl")]) == 2


def test_json_report_is_written_and_round_trips(tmp_path):
    p = _write(tmp_path, [INCIDENT_BASELINE, INCIDENT_CANDIDATE])
    out = tmp_path / "sub" / "report.json"
    arg.main(["--ledger", str(p), "--json", str(out)])
    got = json.loads(out.read_text())
    assert got["violations"] == 1 and got["ok"] is False
    assert got["pairs"][0]["session"] == "2026-08-27"


def test_render_names_the_unchecked_sessions(tmp_path):
    out = arg.audit([row(session="2026-08-20", run_id="only")])
    assert "2026-08-20" in arg.render(out)
    assert "no-baseline" in arg.render(out)


def test_render_survives_an_empty_ledger():
    assert "nothing to compare" in arg.render(arg.audit([]))


# --------------------------------------------------------------------------
# _dig -- the accessor everything else stands on
# --------------------------------------------------------------------------

@pytest.mark.parametrize("obj,path,expect", [
    ({"a": {"b": 1}}, "a.b", 1),
    ({"a": {"b": 1}}, "a.c", None),
    ({"a": 1}, "a.b", None),
    ({}, "a", None),
    ({"a": None}, "a.b", None),
    ({"a": {"b": 0}}, "a.b", 0),
])
def test_dig(obj, path, expect):
    assert arg._dig(obj, path) is expect or arg._dig(obj, path) == expect
