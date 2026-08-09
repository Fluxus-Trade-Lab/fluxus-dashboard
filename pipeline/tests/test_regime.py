"""Tests for the regime score: coverage honesty, bands, evidence."""

from __future__ import annotations

import pytest

from pipeline.screeners import regime
from pipeline.screeners.state_board import LEVELS

MAX = len(LEVELS) - 1


def board(*levels):
    return [{"key": f"d{i}", "level": lv} for i, lv in enumerate(levels)]


class TestScore:
    def test_all_top_is_one_hundred(self):
        assert regime.score(board(*[MAX] * 5))["score"] == 100.0

    def test_all_bottom_is_zero(self):
        assert regime.score(board(*[0] * 5))["score"] == 0.0

    def test_is_the_mean_of_measured_levels(self):
        s = regime.score(board(4, 2, 0))
        assert s["score"] == pytest.approx(round(2 / MAX * 100, 1))

    def test_nothing_measurable_returns_none(self):
        assert regime.score(board(None, None)) is None


class TestUnmeasuredIsNotZero:
    def test_missing_dimensions_leave_the_denominator_alone(self):
        """The board's central rule, carried into the score: a dimension the
        pipeline cannot compute must not drag the average down as if it had
        been measured and found bad."""
        assert regime.score(board(4, 4, None))["score"] == \
            regime.score(board(4, 4))["score"]

    def test_coverage_is_published_with_the_score(self):
        s = regime.score(board(4, 4, None))
        assert (s["measured"], s["of"]) == (2, 3)
        assert "2 of 3" in s["evidence"]


class TestBands:
    @pytest.mark.parametrize("pts,key", [
        (0, "damaged"), (46.9, "damaged"),
        (47, "mixed"), (62.9, "mixed"),
        (63, "healthy"), (74.9, "healthy"),
        (75, "extended"), (100, "extended"),
    ])
    def test_thresholds(self, pts, key):
        assert regime.band_for(pts)["key"] == key

    def test_bands_tile_the_scale_without_gap_or_overlap(self):
        edges = [(b["min"], b["max"]) for b in regime.BANDS]
        assert edges[0][0] == 0 and edges[-1][1] > 100
        assert all(a[1] == b[0] for a, b in zip(edges, edges[1:]))

    def test_no_band_name_prescribes_an_action(self):
        """The forward test was null and mildly contrarian, so a band may
        describe the tape and must never imply a trade. A name like 'tactical
        bull' would be a claim the sample does not support."""
        banned = {"bull", "bear", "buy", "sell", "tactical", "defensive", "risk"}
        for b in regime.BANDS:
            assert not (banned & set(b["label"].lower().split())), b["label"]


class TestEvidence:
    def test_names_the_dimensions_at_full_strength(self):
        s = regime.score([{"key": "trend", "level": MAX},
                          {"key": "breadth", "level": 2}])
        assert s["strong"] == ["trend"] and "trend" in s["evidence"]

    def test_names_the_weak_dimensions(self):
        s = regime.score([{"key": "thrust", "level": 1},
                          {"key": "trend", "level": MAX}])
        assert s["weak"] == ["thrust"] and "thrust" in s["evidence"]

    def test_every_payload_carries_both_findings(self):
        """The number must never travel without what qualifies it — and the two
        findings point opposite ways, so one flag cannot carry both. Flat
        against the mean, monotone against the left tail."""
        s = regime.score(board(4, 3))
        assert s["predicts_return"] is False
        assert s["separates_tail"] is True
        assert "did not predict" in s["caveat"]
        assert "drawdown" in s["caveat"] and "ten independent" in s["caveat"]


class TestBuild:
    def test_ships_bands_for_the_ui_to_draw_the_scale(self):
        out = regime.build(board(4, 3))
        assert out["bands"] == regime.BANDS
        assert out["score"] is not None

    def test_unmeasurable_board_still_ships_a_shaped_payload(self):
        out = regime.build(board(None))
        assert out["score"] is None and "no dimension" in out["evidence"]
