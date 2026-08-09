"""Tests for the daily group snapshot: idempotence, shape, what is stored."""

from __future__ import annotations

from pipeline.themes import group_history as GH


def payload(date="2026-08-09", industries=1, themes=1):
    def g(i, name):
        return {"group": f"{name}{i}", "members": 5, "excess_3m": 0.1,
                "rs_accel": -0.02, "state": "Weakening", "persistence": 3,
                "persistence_of": 5, "perf_1w": 0.01, "perf_1m": 0.02,
                "perf_3m": 0.03, "perf_6m": 0.04, "tickers": ["A", "B"]}
    return {"date": date,
            "industries": [g(i, "Ind") for i in range(industries)],
            "themes": [g(i, "Thm") for i in range(themes)]}


class TestRows:
    def test_kind_is_singular_and_spelled_out(self):
        """Regression: `kind[:-1]` on "industries" stored "industrie", and a
        stored value cannot be taken back."""
        kinds = {r["kind"] for r in GH.rows_from(payload())}
        assert kinds == {"industry", "theme"}

    def test_one_row_per_group(self):
        assert len(GH.rows_from(payload(industries=3, themes=2))) == 5

    def test_stores_the_published_state_not_the_inputs_alone(self):
        """The state is the record of what we said that day. Recomputing it
        later from perf columns would apply today's window constants to
        yesterday's data and silently rewrite history."""
        row = GH.rows_from(payload())[0]
        assert row["state"] == "Weakening"
        assert row["excess_3m"] == 0.1 and row["rs_accel"] == -0.02

    def test_constituents_are_not_archived(self):
        assert "tickers" not in GH.rows_from(payload())[0]

    def test_a_payload_without_a_date_stores_nothing(self):
        p = payload()
        del p["date"]
        assert GH.rows_from(p) == []


class TestAppend:
    def test_rerunning_a_date_replaces_rather_than_doubles(self, tmp_path):
        path = tmp_path / "g.csv"
        GH.record(payload(), path)
        out = GH.record(payload(), path)
        assert out["total"] == 2 and out["replaced"] == 2
        assert len(GH.read(path)) == 2

    def test_a_group_that_disappears_leaves_that_day(self, tmp_path):
        """Replacement is by date, not by (date, group) -- a per-key merge
        would strand a dropped group's last row in the archive forever."""
        path = tmp_path / "g.csv"
        GH.record(payload(industries=3), path)
        GH.record(payload(industries=1), path)
        groups = {r["group"] for r in GH.read(path)}
        assert "Ind2" not in groups

    def test_separate_dates_accumulate(self, tmp_path):
        path = tmp_path / "g.csv"
        GH.record(payload("2026-08-08"), path)
        GH.record(payload("2026-08-09"), path)
        assert {r["date"] for r in GH.read(path)} == {"2026-08-08", "2026-08-09"}
        assert len(GH.read(path)) == 4

    def test_rows_are_sorted_so_diffs_stay_readable(self, tmp_path):
        path = tmp_path / "g.csv"
        GH.record(payload("2026-08-09"), path)
        GH.record(payload("2026-08-08"), path)
        dates = [r["date"] for r in GH.read(path)]
        assert dates == sorted(dates)

    def test_empty_input_does_not_truncate_the_archive(self, tmp_path):
        path = tmp_path / "g.csv"
        GH.record(payload(), path)
        GH.append([], path)
        assert len(GH.read(path)) == 2

    def test_header_matches_the_declared_fields(self, tmp_path):
        path = tmp_path / "g.csv"
        GH.record(payload(), path)
        assert list(GH.read(path)[0]) == GH.FIELDS
