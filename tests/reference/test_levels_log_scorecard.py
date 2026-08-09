"""The record and the score — the two pieces that make the brief falsifiable."""
import pytest

from pipeline.reference import levels_log as LL
from pipeline.reference.scorecard import score_level, score_session, summarise


# ---------------------------------------------------------------- levels log

def _row(ts, spot, call, put, flip="7440"):
    return {"symbol": "SPX", "generated_at": ts, "spot": spot,
            "call_wall": call, "put_wall": put, "zero_gamma_flip": float(flip)}


def test_append_and_read_roundtrip(tmp_path):
    p = tmp_path / "log.jsonl"
    LL.append({"symbol": "SPX", "generated_at": "2026-08-03T08:00:00-04:00"}, p)
    LL.append({"symbol": "SPX", "generated_at": "2026-08-03T12:00:00-04:00"}, p)
    assert [r["generated_at"][-14:-6] for r in LL.read(p)] == ["08:00:00", "12:00:00"]


def test_append_skips_an_already_recorded_observation(tmp_path):
    # Re-running the builder over the same GEX file is not a new observation.
    p = tmp_path / "log.jsonl"
    e = {"symbol": "SPX", "generated_at": "2026-08-03T08:00:00-04:00", "spot": 7400}
    assert LL.append(e, p) is True
    assert LL.append(e, p) is False          # skipped, not duplicated
    assert len(LL.read(p)) == 1
    # A genuinely different pull still writes.
    assert LL.append({**e, "generated_at": "2026-08-03T12:00:00-04:00"}, p) is True
    assert len(LL.read(p)) == 2


def test_read_survives_a_corrupt_line(tmp_path):
    p = tmp_path / "log.jsonl"
    LL.append({"symbol": "SPX", "generated_at": "a"}, p)
    p.write_text(p.read_text() + "{not json\n")
    LL.append({"symbol": "SPX", "generated_at": "b"}, p)
    # A truncated write must not destroy the whole record.
    assert [r["generated_at"] for r in LL.read(p)] == ["a", "b"]


def test_intraday_sequence_reports_movement_between_pulls():
    rows = [_row("2026-08-03T08:00:00-04:00", 7400, 7550, 7400),
            _row("2026-08-03T12:00:00-04:00", 7450, 7550, 7450)]
    seq = LL.intraday_sequence(rows, "2026-08-03")
    assert len(seq) == 2
    assert seq[0].get("moved") is None            # first pull has nothing to compare
    assert seq[1]["moved"] == {"put_wall": 50.0, "spot": 50.0}   # call wall unchanged


def test_intraday_sequence_isolates_the_requested_day_and_symbol():
    rows = [_row("2026-08-03T08:00:00-04:00", 7400, 7550, 7400),
            _row("2026-08-04T08:00:00-04:00", 7500, 7600, 7450),
            {**_row("2026-08-03T09:00:00-04:00", 1, 2, 3), "symbol": "QQQ"}]
    assert len(LL.intraday_sequence(rows, "2026-08-03", symbol="SPX")) == 1


def test_last_entry_per_day_keeps_the_final_state():
    rows = [_row("2026-08-03T08:00:00-04:00", 7400, 7550, 7400),
            _row("2026-08-03T15:50:00-04:00", 7480, 7575, 7425)]
    assert LL.last_entry_per_day(rows)["2026-08-03"]["put_wall"] == 7425


def test_entry_from_flattens_a_gex_doc():
    e = LL.entry_from({"generated_at": "t", "call_wall": 7550.0, "spot": 7435.0,
                       "regime": "negative"}, confluence=[7400.0, 7350.0])
    assert e["call_wall"] == 7550.0 and e["regime"] == "negative"
    assert e["confluence"] == [7350.0, 7400.0]


# ------------------------------------------------------------------ scoring

def test_support_verdicts():
    # touched and closed above -> held; closed below -> broke; never reached -> untested
    assert score_level(7400, "support", high=7500, low=7390, close=7450) == "held"
    assert score_level(7400, "support", high=7500, low=7380, close=7395) == "broke"
    assert score_level(7400, "support", high=7500, low=7420, close=7480) == "untested"


def test_resistance_verdicts():
    assert score_level(7550, "resistance", high=7560, low=7400, close=7500) == "held"
    assert score_level(7550, "resistance", high=7580, low=7400, close=7570) == "broke"
    assert score_level(7550, "resistance", high=7500, low=7400, close=7450) == "untested"


def test_flip_is_scored_by_where_spot_was_when_published():
    entry = {"zero_gamma_flip": 7440.0, "spot": 7400.0, "generated_at": "t"}
    bar = {"high": 7460, "low": 7390, "close": 7430, "date": "2026-08-04"}
    r = next(x for x in score_session(entry, bar) if x["level_name"] == "zero_gamma_flip")
    # spot was below the flip, so it was overhead -> resistance, tagged and held
    assert r["kind"] == "pivot" and r["verdict"] == "held"


def test_summarise_separates_untested_from_losses():
    res = [{"level_name": "put_wall", "verdict": v} for v in
           ("held", "held", "broke", "untested", "untested")]
    s = summarise(res)
    b = s["by_level"]["put_wall"]
    assert b["n"] == 5 and b["tested"] == 3
    # 2 of 3 TESTED, not 2 of 5 — folding untested in is how these get flattered.
    assert b["held_pct"] == pytest.approx(66.7)


def test_summarise_returns_none_rather_than_zero_when_nothing_was_tested():
    s = summarise([{"level_name": "call_wall", "verdict": "untested"}])
    assert s["by_level"]["call_wall"]["held_pct"] is None
    assert s["total"]["held_pct"] is None
