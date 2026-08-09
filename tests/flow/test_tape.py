"""The tape contract — what the reader refuses, and why loudly."""
import pytest

from pipeline.flow import tape as T

BAR = {"time_bin": "2026-08-05T09:30:00", "side": "C", "strike": 7750.0,
       "premium_total": 1000.0, "bot_premium": 700.0, "sold_premium": 300.0,
       "net_premium": 400.0, "n_prints": 12}


def _write(tmp_path, *lines):
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(lines) + "\n")
    return p


def test_roundtrip(tmp_path):
    p = _write(tmp_path, T.line("bar", BAR))
    rows = T.read_tape(p)
    assert rows[0]["v"] == T.TAPE_VERSION and rows[0]["net_premium"] == 400.0


def test_writer_refuses_an_incomplete_bar():
    with pytest.raises(ValueError, match="missing"):
        T.line("bar", {"time_bin": "x"})


def test_an_unversioned_line_is_an_error_by_default(tmp_path):
    import json
    p = _write(tmp_path, json.dumps(BAR))
    with pytest.raises(ValueError, match="unversioned"):
        T.read_tape(p)
    # ...and readable only on explicit request, tagged v0 so downstream can see.
    rows = T.read_tape(p, allow_legacy=True)
    assert rows[0]["v"] == 0


def test_a_future_version_is_refused_not_guessed_at(tmp_path):
    import json
    p = _write(tmp_path, json.dumps({"v": 2, "kind": "bar", **BAR}))
    with pytest.raises(ValueError, match="version 2"):
        T.read_tape(p)


def test_errors_name_the_line_number(tmp_path):
    p = _write(tmp_path, T.line("bar", BAR), "{not json")
    with pytest.raises(ValueError, match=r"t\.jsonl:2"):
        T.read_tape(p)


def test_blank_lines_are_fine_because_append_only_files_end_with_one(tmp_path):
    p = _write(tmp_path, T.line("bar", BAR), "")
    assert len(T.read_tape(p)) == 1


def test_per_strike_premium_nets_across_bars():
    bars = [dict(BAR), {**BAR, "net_premium": -150.0, "n_prints": 3},
            {**BAR, "strike": 7800.0, "net_premium": 50.0}]
    acc = T.per_strike_premium(bars)
    assert acc[7750.0]["net_premium"] == pytest.approx(250.0)
    assert acc[7750.0]["n_prints"] == 15
    assert acc[7800.0]["net_premium"] == pytest.approx(50.0)


def test_a_bar_without_a_strike_is_skipped_not_pooled_into_strike_zero():
    b = {k: v for k, v in BAR.items() if k != "strike"}
    assert T.per_strike_premium([b]) == {}
