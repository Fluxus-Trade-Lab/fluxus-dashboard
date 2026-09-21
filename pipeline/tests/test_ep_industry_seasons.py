"""Tests for pipeline/tools/ep_industry_seasons.py."""
from __future__ import annotations

from datetime import date

from pipeline.tools.ep_industry_seasons import (
    Season,
    aggregate_season,
    recent_complete_seasons,
    rotation_delta,
    season_defs_for_year,
)


class TestSeasonWindows:
    def test_four_windows_for_a_regular_year(self):
        seasons = season_defs_for_year(2026)
        ids = [s.season_id for s in seasons]
        assert ids == ["2025Q4", "2026Q1", "2026Q2", "2026Q3"]

    def test_q1_window_matches_apr15_may31(self):
        seasons = season_defs_for_year(2026)
        q1 = next(s for s in seasons if s.season_id == "2026Q1")
        assert q1.start == date(2026, 4, 15)
        assert q1.end == date(2026, 5, 31)

    def test_q4_window_feb_end_respects_leap_year(self):
        leap = next(s for s in season_defs_for_year(2028) if s.season_id == "2027Q4")
        non_leap = next(s for s in season_defs_for_year(2026) if s.season_id == "2025Q4")
        assert leap.end == date(2028, 2, 29)
        assert non_leap.end == date(2026, 2, 28)


class TestRecentCompleteSeasons:
    def test_picks_the_two_most_recently_finished_seasons(self):
        # 2026-09-21: Q2 2026 season (07-15..08-31) just finished, Q1 2026
        # (04-15..05-31) before it; Q3 2026 (10-15..11-30) hasn't started.
        seasons = recent_complete_seasons(date(2026, 9, 21), n=2)
        assert [s.season_id for s in seasons] == ["2026Q1", "2026Q2"]

    def test_excludes_a_season_still_in_progress(self):
        # Mid-season: 2026Q3 (10-15..11-30) is running on 2026-11-01, so it
        # must not appear even though its start date has passed.
        seasons = recent_complete_seasons(date(2026, 11, 1), n=2)
        assert "2026Q3" not in [s.season_id for s in seasons]
        assert seasons[-1].season_id == "2026Q2"


class TestAggregateSeason:
    SEASON = Season("2026Q1", date(2026, 4, 15), date(2026, 5, 31))

    def test_counts_hits_and_dedups_tickers_within_the_window(self):
        events = [
            {"date": "2026-04-20", "ticker": "AAA", "screener": "ep_stockbee"},
            {"date": "2026-05-01", "ticker": "AAA", "screener": "episodic_pivot"},  # same ticker, 2nd hit
            {"date": "2026-04-22", "ticker": "BBB", "screener": "ep_qullamaggie"},
            {"date": "2026-06-05", "ticker": "CCC", "screener": "ep_stockbee"},  # outside window
        ]
        industry_map = {"AAA": "Software - Application", "BBB": "Software - Application", "CCC": "Biotechnology"}
        out = aggregate_season(events, self.SEASON, industry_map)
        assert out["total_hits"] == 3
        assert out["unique_tickers"] == 2
        assert out["unmapped_tickers"] == []
        sw = next(x for x in out["industries"] if x["industry"] == "Software - Application")
        assert sw == {"industry": "Software - Application", "tickers": 2, "hits": 3}

    def test_unmapped_ticker_counted_separately_not_dropped(self):
        events = [{"date": "2026-04-20", "ticker": "ZZZ", "screener": "ep_stockbee"}]
        out = aggregate_season(events, self.SEASON, industry_map={})
        assert out["unmapped_tickers"] == ["ZZZ"]
        assert out["total_hits"] == 1
        assert any(x["industry"] == "UNKNOWN" for x in out["industries"])

    def test_industries_sorted_by_ticker_count_descending(self):
        events = [
            {"date": "2026-04-20", "ticker": "A1", "screener": "ep_stockbee"},
            {"date": "2026-04-20", "ticker": "A2", "screener": "ep_stockbee"},
            {"date": "2026-04-20", "ticker": "A3", "screener": "ep_stockbee"},
            {"date": "2026-04-21", "ticker": "B1", "screener": "ep_stockbee"},
        ]
        industry_map = {"A1": "Biotechnology", "A2": "Biotechnology", "A3": "Biotechnology", "B1": "Semiconductors"}
        out = aggregate_season(events, self.SEASON, industry_map)
        assert [x["industry"] for x in out["industries"]] == ["Biotechnology", "Semiconductors"]


class TestRotationDelta:
    def test_entered_and_dropped_top5(self):
        prev = {"season_id": "2026Q1", "industries": [
            {"industry": "Biotechnology", "tickers": 10, "hits": 12},
            {"industry": "Semiconductors", "tickers": 8, "hits": 8},
        ]}
        cur = {"season_id": "2026Q2", "industries": [
            {"industry": "Semiconductors", "tickers": 9, "hits": 9},
            {"industry": "Software - Application", "tickers": 7, "hits": 7},
        ]}
        d = rotation_delta(prev, cur, top_n=5)
        assert d["entered_top5"] == ["Software - Application"]
        assert d["dropped_from_top5"] == ["Biotechnology"]
