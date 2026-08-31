"""The two controls the no-downgrade gate has to pass before its silence means anything.

Standing rule (Growth Gary, 2026-08-25): *no check whose positive has not been
verified is entitled to be believed when it says negative.* So this file is
built around two named controls, and both print the numbers they judged:

* POSITIVE -- replay the real 2026-08-27 overwrite (the incident table in
  `data/reference/incidents/2026-08-29_late_run_overwrote_healthy_data.md`).
  The gate must block it, and must say why in terms of both sides' numbers.
* NEGATIVE -- the same session with the night-to-night jitter of a healthy
  rerun. The gate must stay out of the way. A gate that fires here is a gate
  that gets switched off within a week.

The rest are the boundary cases those two imply: a genuine repair run must not
be mistaken for damage, a different session must never be compared at all, and
each half of the two-part D2 threshold must be shown to be load-bearing (a
relative-only rule and an absolute-only rule each block something they should
not).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.no_downgrade import (
    DEGRADED_GROWTH,
    FORCE_ENV,
    check_overwrite,
    compare,
    readings,
    session_of,
)

SESSION = "2026-08-27"


def universe(session=SESSION, *, status="ok", n_rows=5627, bars_missing=64,
             bars_stale=0, tradeable=2562, unmeasurable=75, degraded=()):
    """A universe.json-shaped payload with the readings dialled in.

    Built by materialising real rows rather than by hand-writing the reading
    vector: `bars_missing` and `bars_stale` are COUNTED off the rows in
    production, so a fixture that just asserts the number would be testing a
    code path the pipeline never takes.
    """
    rows = []
    for i in range(n_rows):
        rows.append({
            "ticker": f"T{i:05d}",
            "bar_date": None if i < bars_missing else session,
            "bars_stale": True if bars_missing <= i < bars_missing + bars_stale else False,
        })
    fields = {"close": {"status": "ok"}, "market_cap": {"status": "ok"}}
    for name in degraded:
        fields[name] = {"status": "degraded"}
    return {
        "timestamp": f"{session}T21:30:00+00:00",
        "count": n_rows,
        "quality": {
            "status": status,
            "fields": fields,
            "runs_in_baseline": 12,
            "tradeable": {"tradeable": tradeable,
                          "excluded": n_rows - tradeable - unmeasurable,
                          "unmeasurable": unmeasurable},
        },
        "rows": rows,
    }


def _on_disk(tmp_path: Path, payload) -> Path:
    p = tmp_path / "universe.json"
    p.write_text(json.dumps(payload))
    return p


def _show(title, out):
    """Print the gate's verdict and both sides' numbers -- the evidence itself."""
    print(f"\n--- {title} ---")
    print(f"blocked={out['blocked']}  status={out['status']}")
    print(f"reason: {out['reason']}")
    d = out.get("detail") or {}
    if "stored" in d and "candidate" in d:
        keys = ["status", "rows", "tradeable", "unmeasurable", "bars_missing",
                "bars_stale", "degraded_fields"]
        print(f"{'reading':<16}{'stored':>28}{'candidate':>28}")
        for k in keys:
            print(f"{k:<16}{str(d['stored'].get(k)):>28}{str(d['candidate'].get(k)):>28}")


# ---------------------------------------------------------------- POSITIVE --

# The 2026-08-27 incident table, verbatim. `bars_stale` is not in the table as
# a count (it appears as a newly-degraded COLUMN name), so it is left at the
# healthy value: the gate has to block on the numbers we actually recorded.
HEALTHY_0827 = dict(status="ok", n_rows=5627, bars_missing=64, tradeable=2562,
                    unmeasurable=75, degraded=("perf_ytd",))
OVERWROTE_0827 = dict(status="degraded", n_rows=5627, bars_missing=266, tradeable=2465,
                      unmeasurable=277,
                      degraded=("bar_date", "bar_scale_mismatch", "bars_stale",
                                "perf_ytd", "vol_5d_50d"))


def test_positive_control_the_real_0827_overwrite_is_blocked(tmp_path):
    """The late run that actually happened must not be able to happen again."""
    path = _on_disk(tmp_path, universe(**HEALTHY_0827))
    out = check_overwrite(path, universe(**OVERWROTE_0827), candidate_session=SESSION)
    _show("POSITIVE CONTROL — replay of the 485-minute-late 2026-08-27 run", out)

    assert out["blocked"] is True
    assert out["status"] == "blocked"

    rules = {f["rule"] for f in out["detail"]["findings"]}
    assert "D1" in rules, "the status downgrade ok -> degraded must be caught"
    assert "D2" in rules, "the missingness blowout must be caught"

    # The reason has to carry the numbers, not just a verdict: a gate that
    # blocks without saying what moved sends the reader to the wrong place
    # (the 08-30 backstop printed a confident, false reason and cost an hour).
    assert "64 -> 266" in out["reason"], out["reason"]
    assert "75 -> 277" in out["reason"], out["reason"]
    assert "ok -> degraded" in out["reason"], out["reason"]

    # And the file on disk is untouched -- check_overwrite never writes.
    assert json.loads(path.read_text())["quality"]["status"] == "ok"


def test_positive_control_degraded_to_degraded_still_blocks_on_columns(tmp_path):
    """D3 alone: same status word, but four healthy columns went bad."""
    path = _on_disk(tmp_path, universe(status="degraded", degraded=("perf_ytd",)))
    out = check_overwrite(
        path,
        universe(status="degraded",
                 degraded=("perf_ytd", "bar_date", "bar_scale_mismatch", "vol_5d_50d")),
        candidate_session=SESSION)
    _show("POSITIVE CONTROL — degraded -> degraded, +3 newly degraded columns", out)
    assert out["blocked"] is True
    assert {f["rule"] for f in out["detail"]["findings"]} == {"D3"}


# ---------------------------------------------------------------- NEGATIVE --

def test_negative_control_normal_jitter_is_not_blocked(tmp_path):
    """A healthy same-session rerun moves these numbers a little. Let it through."""
    path = _on_disk(tmp_path, universe(**HEALTHY_0827))
    jitter = dict(HEALTHY_0827,
                  n_rows=5620,          # -7 rows, -0.1%
                  bars_missing=70,      # +6 names, +9% -- over no relative tolerance
                  tradeable=2540,       # -22, -0.9%
                  unmeasurable=81)      # +6, +8%
    out = check_overwrite(path, universe(**jitter), candidate_session=SESSION)
    _show("NEGATIVE CONTROL — healthy same-session rerun, ordinary jitter", out)

    assert out["blocked"] is False, out["reason"]
    assert out["status"] == "ok"
    assert out["detail"]["findings"] == []


def test_negative_control_a_repair_run_is_never_blocked(tmp_path):
    """The 2026-08-19 shape: the rerun FIXED the day. Blocking it would be the bug."""
    path = _on_disk(tmp_path, universe(status="degraded", bars_missing=266,
                                       unmeasurable=277, tradeable=2465,
                                       degraded=("bar_date", "vol_5d_50d")))
    out = check_overwrite(path, universe(**HEALTHY_0827), candidate_session=SESSION)
    _show("NEGATIVE CONTROL — a genuine repair (degraded -> ok)", out)
    assert out["blocked"] is False, out["reason"]


def test_a_different_session_is_never_compared(tmp_path):
    """Yesterday vs today is the market moving. The gate must not have an opinion."""
    path = _on_disk(tmp_path, universe(session="2026-08-26", **HEALTHY_0827))
    out = check_overwrite(path, universe(session="2026-08-27", **OVERWROTE_0827),
                          candidate_session="2026-08-27")
    assert out["blocked"] is False
    assert out["status"] == "no-baseline"
    assert "different day" in out["reason"]


# ------------------------------------------- both halves of D2 are load-bearing

def test_relative_tolerance_alone_would_block_a_four_name_move(tmp_path):
    """10 -> 20 bars_missing is +100% and ten names. The absolute floor saves it."""
    path = _on_disk(tmp_path, universe(bars_missing=10))
    out = check_overwrite(path, universe(bars_missing=20), candidate_session=SESSION)
    assert out["blocked"] is False, out["reason"]
    # ...and the same relative move, once it is big enough to matter, does block:
    # +190 names off the same baseline of 10 clears the 25-row floor.
    big = check_overwrite(path, universe(bars_missing=200), candidate_session=SESSION)
    assert big["blocked"] is True, big["reason"]


def test_absolute_floor_alone_would_block_a_half_percent_move(tmp_path):
    """tradeable 2562 -> 2510 is 52 rows but only -2%. Ordinary. Must pass."""
    path = _on_disk(tmp_path, universe(tradeable=2562))
    out = check_overwrite(path, universe(tradeable=2510), candidate_session=SESSION)
    assert out["blocked"] is False, out["reason"]


def test_improvement_never_trips_a_directional_rule(tmp_path):
    """Every rule is directional: a better candidate cannot be 'different enough'."""
    path = _on_disk(tmp_path, universe(bars_missing=266, unmeasurable=277, tradeable=2400))
    out = check_overwrite(path, universe(bars_missing=10, unmeasurable=12, tradeable=2600),
                          candidate_session=SESSION)
    assert out["blocked"] is False, out["reason"]
    assert out["detail"]["findings"] == []


# --------------------------------------------------------------- fail-open --

def test_missing_file_allows_the_write(tmp_path):
    out = check_overwrite(tmp_path / "nope.json", universe(**OVERWROTE_0827),
                          candidate_session=SESSION)
    assert out["blocked"] is False
    assert out["status"] == "no-baseline"


def test_unparsable_file_allows_the_write(tmp_path):
    p = tmp_path / "universe.json"
    p.write_text("{not json")
    out = check_overwrite(p, universe(**OVERWROTE_0827), candidate_session=SESSION)
    assert out["blocked"] is False
    assert out["status"] == "no-baseline"


def test_force_env_lets_a_human_override(tmp_path, monkeypatch):
    monkeypatch.setenv(FORCE_ENV, "1")
    path = _on_disk(tmp_path, universe(**HEALTHY_0827))
    out = check_overwrite(path, universe(**OVERWROTE_0827), candidate_session=SESSION)
    assert out["blocked"] is False
    assert out["status"] == "forced"
    assert "WORSE" in out["reason"]


# ------------------------------------------------------------------ pieces --

def test_session_is_the_modal_bar_date_not_the_timestamp(tmp_path):
    """The 08-27 overwrite carried an 08-28 timestamp. The rows knew better."""
    doc = universe(session="2026-08-27")
    doc["timestamp"] = "2026-08-28T05:36:00+00:00"
    doc["rows"][5]["bar_date"] = "2026-07-17"     # a few stale names, as in production
    doc["rows"][6]["bar_date"] = "2026-08-21"
    assert session_of(doc) == "2026-08-27"


def test_readings_counts_both_sides_through_one_function():
    r = readings(universe(bars_missing=64, bars_stale=9, tradeable=2562, unmeasurable=75))
    assert r["bars_missing"] == 64
    assert r["bars_stale"] == 9
    assert r["tradeable"] == 2562
    assert r["unmeasurable"] == 75
    assert r["degraded_fields"] == []


def test_unpopulated_columns_do_not_count_as_degraded():
    """A column that has never carried data has not broken -- quality.py's rule."""
    doc = universe()
    doc["quality"]["fields"]["eps_growth_next_y"] = {"status": "unpopulated"}
    assert readings(doc)["degraded_fields"] == []


@pytest.mark.parametrize("n", [DEGRADED_GROWTH - 1, DEGRADED_GROWTH])
def test_d3_threshold_is_where_it_says_it_is(n):
    stored = readings(universe(degraded=("perf_ytd",)))
    cand = readings(universe(degraded=("perf_ytd", *[f"c{i}" for i in range(n)])))
    rep = compare(stored, cand)
    assert rep["worse"] is (n >= DEGRADED_GROWTH)
