"""Schema snapshot -- three states, not two.

The gate exists because of the 2026-08-19 breadth blackout (top-level blocks
vanished and the run committed anyway). It then failed the opposite way on
2026-08-24: a quiet day with no EP fire and no panel hits read as "removed
[every field]" and blocked the whole night's commit.

So the shape of a collection has three states, and the tests below hold them
apart: POPULATED (keys), EMPTY (measured, held nothing -- informational), and
ABSENT (the path itself is gone -- fatal, the blackout signature).
"""
import json

from pipeline.tools.schema_snapshot import EMPTY, diff, main, shape


def _fatal(lines):
    return [l for l in lines if ": removed " in l or "FILE MISSING" in l]


class TestShape:
    def test_empty_list_is_recorded_not_skipped(self):
        s = shape({"tickers": []})
        assert s["tickers[]"] is EMPTY
        assert "tickers[]" in s, "an empty list must still occupy its path"

    def test_populated_list_records_the_union_of_keys(self):
        s = shape({"tickers": [{"ticker": "MU", "atr": 1.0}, {"ticker": "AA", "chg": 2.0}]})
        assert s["tickers[]"] == ["atr", "chg", "ticker"]

    def test_nested_empty_list_inside_rows(self):
        """shortlist.json's cards[].panels[] on a day nothing hit."""
        s = shape({"cards": [{"ticker": "MU", "panels": []}]})
        assert s["cards[]"] == ["panels", "ticker"]
        assert s["cards[].panels[]"] is EMPTY

    def test_dict_of_empty_lists(self):
        """The themes/industries shape when every group's list is empty."""
        payload = {"groups": {"a": [], "b": [], "c": [], "d": [], "e": []}}
        s = shape(payload)
        assert s["groups{}[]"] is EMPTY

    def test_rare_field_far_down_a_large_ticker_dict_is_not_sampled_away(self):
        """2026-09-04: ticker_events.json's events{} is keyed by ~5,000
        tickers; VCP only hits ~35 of them. A field that low-hit-rate
        screener contributes (num_contractions, pct_to_pivot) can have every
        one of its rows sit past a small, alphabetic-order sample window on
        any given night. That is not the collection being empty (the
        EMPTY-vs-removed bug the 08-24/08-25 tests above cover) -- the field
        is still being emitted, just outside the window the old code
        sampled (first 50 keys, first 20 items each)."""
        events = {}
        for i in range(80):  # past the old 50-key window
            events[f"T{i:03d}"] = [{"date": "2026-09-04", "screener": "gainer"}
                                    for _ in range(25)]  # past the old 20-item window
        events["ZZZZ"] = [{"date": "2026-09-04", "screener": "vcp", "num_contractions": 3}]
        s = shape({"events": events})
        assert "num_contractions" in s["events{}[]"]


class TestDiffThreeStates:
    def test_empty_today_is_not_a_removal(self):
        """THE 2026-08-24 regression: no EP fired, so tickers[] is empty."""
        old = {"episodic_pivot.json": {"top": ["tickers"], "tickers[]": ["ticker", "atr_ext"]}}
        new = {"episodic_pivot.json": {"top": ["tickers"], "tickers[]": EMPTY}}
        lines = diff(old, new)
        assert _fatal(lines) == [], f"an empty day must not fail the gate: {lines}"
        assert any("empty today" in l for l in lines), "but it must still be reported"

    def test_absent_path_is_still_fatal(self):
        """The blackout signature: the key itself vanished, not its rows."""
        old = {"breadth.json": {"top": ["regime", "verdict"], "regime.bands[]": ["hi", "lo"]}}
        new = {"breadth.json": {"top": ["verdict"]}}
        lines = diff(old, new)
        assert _fatal(lines), "a vanished path must keep failing the gate"
        assert any("top: removed ['regime']" in l for l in lines)

    def test_real_field_removal_is_still_fatal(self):
        old = {"universe.json": {"top": ["rows"], "rows[]": ["ticker", "atr", "close"]}}
        new = {"universe.json": {"top": ["rows"], "rows[]": ["ticker", "close"]}}
        assert _fatal(diff(old, new))

    def test_additions_stay_report_only(self):
        old = {"universe.json": {"top": ["rows"], "rows[]": ["ticker"]}}
        new = {"universe.json": {"top": ["rows"], "rows[]": ["atr_pctl_252", "ticker"]}}
        lines = diff(old, new)
        assert _fatal(lines) == []
        assert any("added ['atr_pctl_252']" in l for l in lines)

    def test_empty_to_empty_is_silent(self):
        old = {"f.json": {"top": ["x"], "x[]": EMPTY}}
        new = {"f.json": {"top": ["x"], "x[]": EMPTY}}
        assert diff(old, new) == []

    def test_populated_again_is_reported_not_flagged(self):
        """A snapshot taken on a quiet day must not turn the next real day
        into a wall of spurious 'added' lines."""
        old = {"f.json": {"top": ["x"], "x[]": EMPTY}}
        new = {"f.json": {"top": ["x"], "x[]": ["a", "b", "c"]}}
        lines = diff(old, new)
        assert _fatal(lines) == []
        assert any("populated again (3 field(s))" in l for l in lines)
        assert not any("added" in l for l in lines)


class TestCli:
    def _write(self, d, name, payload):
        (d / name).write_text(json.dumps(payload))

    def test_quiet_day_exits_zero(self, tmp_path):
        out = tmp_path / "output"; out.mkdir()
        snap = tmp_path / "snap.json"
        self._write(out, "episodic_pivot.json", {"tickers": [{"ticker": "MU", "atr_ext": 1.0}]})
        assert main(["--update", "--output", str(out), "--snapshot", str(snap)]) == 0
        # next night: nothing fired
        self._write(out, "episodic_pivot.json", {"tickers": []})
        assert main(["--check", "--output", str(out), "--snapshot", str(snap)]) == 0

    def test_blackout_still_exits_one(self, tmp_path):
        out = tmp_path / "output"; out.mkdir()
        snap = tmp_path / "snap.json"
        self._write(out, "breadth.json", {"regime": {"score": 1}, "verdict": {"x": 1},
                                          "conditions": {"y": 1}, "state_board": {"z": 1}})
        assert main(["--update", "--output", str(out), "--snapshot", str(snap)]) == 0
        self._write(out, "breadth.json", {"verdict": {"x": 1}})
        assert main(["--check", "--output", str(out), "--snapshot", str(snap)]) == 1


# ── the original 2026-08-19 regression, kept verbatim ─────────────────────
# (it predates this file's rewrite on 08-24; the addition/removal pair it
# locks is the reason the gate exists at all)

def _setup(tmp_path, payload):
    out = tmp_path / "output"; out.mkdir()
    (out / "breadth.json").write_text(json.dumps(payload))
    snap = tmp_path / "snap.json"
    return out, snap


def test_removed_field_fails_added_passes(tmp_path):
    out, snap = _setup(tmp_path, {"regime": {"score": 1}, "breadth": {"t2108": 5}})
    assert main(["--update", "--output", str(out), "--snapshot", str(snap)]) == 0
    # addition -> 0
    (out / "breadth.json").write_text(json.dumps(
        {"regime": {"score": 1}, "breadth": {"t2108": 5}, "new_block": 1}))
    assert main(["--check", "--output", str(out), "--snapshot", str(snap)]) == 0
    # removal of a top-level block (the 08-19 shape) -> 1
    (out / "breadth.json").write_text(json.dumps({"breadth": {"t2108": 5}}))
    assert main(["--check", "--output", str(out), "--snapshot", str(snap)]) == 1
