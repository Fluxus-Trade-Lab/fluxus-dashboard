"""Tests for the ticker-event git backfill (pure functions only — no git calls)."""
import pytest


class TestSnapshotDates:
    def test_parses_and_orders_oldest_first(self):
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "ccc 2026-05-06\nbbb 2026-05-05\naaa 2026-05-04\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04'), ('bbb', '2026-05-05'),
                                       ('ccc', '2026-05-06')]

    def test_one_commit_per_date_keeps_last_of_day(self):
        """git log is newest-first, so the FIRST line for a date is that day's final state."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "late 2026-05-05\nearly 2026-05-05\naaa 2026-05-04\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04'), ('late', '2026-05-05')]

    def test_ignores_blank_and_malformed_lines(self):
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "\naaa 2026-05-04\ngarbage\n\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04')]


class TestRowsFromSnapshot:
    def test_concatenates_all_screeners(self):
        from pipeline.tools.backfill_ticker_events import rows_from_snapshot
        payloads = {
            'gainers_4pct': {'tickers': [{'ticker': 'ABC', 'change_pct': 0.05}]},
            'vcp': {'results': [{'ticker': 'DEF', 'num_contractions': 2}]},
            'momentum_97': {'buckets': {'97': [{'ticker': 'GHI'}]}},
        }
        rows = rows_from_snapshot(payloads, '2026-05-04')
        assert len(rows) == 3
        assert {r['screener'] for r in rows} == {'gainers_4pct', 'vcp', 'momentum_97'}
        assert all(r['date'] == '2026-05-04' for r in rows)

    def test_missing_payload_is_skipped(self):
        from pipeline.tools.backfill_ticker_events import rows_from_snapshot
        rows = rows_from_snapshot({'vcp': None, 'gainers_4pct': {'tickers': []}}, '2026-05-04')
        assert rows == []


class TestPlanPurge:
    def test_archived_skipped_and_mined_is_purged(self):
        from pipeline.tools.backfill_ticker_events import plan_purge
        result = plan_purge(existing_dates={'2026-05-04'},
                             skipped_dates={'2026-05-04'},
                             mined_dates={'2026-05-04'})
        assert result == {'2026-05-04'}

    def test_archived_and_skipped_but_not_mined_is_protected(self):
        """The renamed-file protection: a date the run never looked at
        (e.g. lost history from a rename without --follow) must never be
        purged, even if it happens to be archived and skipped."""
        from pipeline.tools.backfill_ticker_events import plan_purge
        result = plan_purge(existing_dates={'2026-05-04'},
                             skipped_dates={'2026-05-04'},
                             mined_dates=set())
        assert result == set()

    def test_archived_and_mined_but_not_skipped_is_not_purged(self):
        from pipeline.tools.backfill_ticker_events import plan_purge
        result = plan_purge(existing_dates={'2026-05-04'},
                             skipped_dates=set(),
                             mined_dates={'2026-05-04'})
        assert result == set()

    def test_skipped_and_mined_but_not_archived_is_not_purged(self):
        from pipeline.tools.backfill_ticker_events import plan_purge
        result = plan_purge(existing_dates=set(),
                             skipped_dates={'2026-05-04'},
                             mined_dates={'2026-05-04'})
        assert result == set()

    def test_empty_inputs(self):
        from pipeline.tools.backfill_ticker_events import plan_purge
        assert plan_purge(set(), set(), set()) == set()


class TestSummarize:
    def test_counts(self):
        from pipeline.tools.backfill_ticker_events import summarize
        rows = [
            {'date': '2026-05-04', 'ticker': 'ABC', 'screener': 'vcp'},
            {'date': '2026-05-04', 'ticker': 'DEF', 'screener': 'vcp'},
            {'date': '2026-06-02', 'ticker': 'ABC', 'screener': 'gainers_4pct'},
        ]
        s = summarize(rows)
        assert s['total'] == 3
        assert s['by_screener'] == {'vcp': 2, 'gainers_4pct': 1}
        assert s['by_month'] == {'2026-05': 2, '2026-06': 1}
        assert s['tickers'] == 2

    def test_empty(self):
        from pipeline.tools.backfill_ticker_events import summarize
        assert summarize([]) == {'total': 0, 'by_screener': {}, 'by_month': {}, 'tickers': 0}
