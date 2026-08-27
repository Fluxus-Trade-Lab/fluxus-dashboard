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


class TestSaveKeepsTheTwoWritesTogether:
    """The defect this guards: the snapshot lived in `build_groups.main()`,
    the daily pipeline calls `run()` and wrote groups.json itself, so in
    production the archive never grew and the ten weeks it needs to become
    useful never started. Both writes now go through `save()`."""

    def test_save_writes_the_json_and_appends_the_archive(self, tmp_path):
        from pipeline.themes import build_groups
        archive = tmp_path / "archive.csv"
        out = build_groups.save(payload(), tmp_path, archive)
        assert out.exists()
        assert len(GH.read(archive)) == 2

    def test_a_snapshot_failure_does_not_cost_groups_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(GH, "record",
                            lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
        from pipeline.themes import build_groups
        out = build_groups.save(payload(), tmp_path, tmp_path / "a.csv")
        assert out.exists()

    def test_run_all_saves_groups_through_save(self):
        """Asserted on the source because the alternative is running the whole
        daily pipeline. A local write here is the exact regression."""
        import inspect
        from pipeline.screeners import run_all
        src = inspect.getsource(run_all.main)
        assert "save_groups(" in src
        assert "'groups.json'" not in src.split("save_groups(")[0][-400:]

    def test_the_cron_can_call_the_rotation_steps(self):
        """A module whose only entry point is `main()` is a module the cron
        cannot use — the same shape as the bug above."""
        from pipeline.rotation.fetch_baskets import fetch
        from pipeline.rotation.build_rotation import build
        assert callable(fetch) and callable(build)


class TestProjectionCarriesTheVerticalAxis:
    """DATA_CONTRACTS §七 [08-24], Andy's call: the four-state板's vertical
    axis is rs_accel. With `excess` alone the published history is
    one-dimensional and the Themes page cannot draw which quadrant a group
    came FROM -- and the direction it came from IS the rotation.
    """

    def _project(self, tmp_path, dates=("2026-08-09", "2026-08-10")):
        import json
        arch = tmp_path / "groups_archive.csv"
        out = tmp_path / "groups_history.json"
        for d in dates:
            GH.record(payload(date=d), path=arch)
        GH.project(path=arch, out=out)
        return json.loads(out.read_text())

    def test_every_group_carries_an_rs_accel_series(self, tmp_path):
        d = self._project(tmp_path)
        assert d["groups"], "no groups projected"
        for name, g in d["groups"].items():
            assert "rs_accel" in g, f"{name} has no rs_accel"
            assert len(g["rs_accel"]) == len(d["dates"]), "series must align with dates"

    def test_values_are_copied_verbatim_not_recomputed(self, tmp_path):
        """Same rule as excess/state: recomputing would apply today's window
        constants to an older session (see the module docstring)."""
        d = self._project(tmp_path)
        g = next(iter(d["groups"].values()))
        assert g["rs_accel"] == [-0.02, -0.02]

    def test_a_missing_reading_is_null_not_zero(self, tmp_path):
        """A group with no rs_accel that day must read as unmeasured -- zero
        is a position on the axis, absence is not."""
        import json
        arch = tmp_path / "a.csv"; out = tmp_path / "o.json"
        p = payload(date="2026-08-09")
        p["themes"][0]["rs_accel"] = None
        GH.record(p, path=arch)
        GH.project(path=arch, out=out)
        d = json.loads(out.read_text())
        assert d["groups"]["Thm0"]["rs_accel"] == [None]
