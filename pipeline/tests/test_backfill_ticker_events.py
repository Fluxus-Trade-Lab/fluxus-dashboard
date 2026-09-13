"""Tests for the ticker-event git backfill (pure functions only — no git calls)."""
import pytest


class TestSnapshotDates:
    def test_parses_and_orders_oldest_first(self):
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = ("ccc 2026-05-06T22:10:00Z\nbbb 2026-05-05T22:10:00Z\n"
               "aaa 2026-05-04T22:10:00Z\n")
        assert snapshot_dates(log) == [('aaa', '2026-05-04'), ('bbb', '2026-05-05'),
                                       ('ccc', '2026-05-06')]

    def test_one_commit_per_date_keeps_last_of_day(self):
        """git log is newest-first, so the FIRST line for a date is that day's final state."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = ("late 2026-05-06T01:30:00Z\nearly 2026-05-05T22:10:00Z\n"
               "aaa 2026-05-04T22:10:00Z\n")
        assert snapshot_dates(log) == [('aaa', '2026-05-04'), ('late', '2026-05-05')]

    def test_ignores_blank_and_malformed_lines(self):
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = "\naaa 2026-05-04T22:10:00Z\ngarbage\nbbb not-a-time\n\n"
        assert snapshot_dates(log) == [('aaa', '2026-05-04')]

    def test_a_utc_evening_commit_is_the_et_session_before_it(self):
        """The 2026-08-07 bug: 69754ed3 committed 08-07 01:08 UTC = 08-06 21:08
        ET and held the 08-06 tape. --date=short stamped it 08-07; 72/72 of
        that day's preset change_pct matched the 08-06 bars."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        assert snapshot_dates("69754ed3 2026-08-07T01:08:23Z") == [('69754ed3', '2026-08-06')]

    def test_a_weekend_commit_is_friday(self):
        """Sunday 7c162f49 (13:29 ET) holds Friday 08-07's tape."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        assert snapshot_dates("7c162f49 2026-08-09T17:29:01Z") == [('7c162f49', '2026-08-07')]

    def test_a_next_premarket_or_daytime_commit_never_displaces_the_post_close_one(self):
        """Real 08-14 history, newest first: a Monday daytime dev commit and a
        Monday-premarket manual run both came AFTER the clean Friday cron
        snapshot. Newest-wins alone would have picked the dev commit."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        log = ("fbf2c0fb 2026-08-18T02:20:37+09:00\n"   # Mon 08-17 13:20 ET
               "65bbb080 2026-08-17T17:32:26+09:00\n"   # Mon 08-17 04:32 ET
               "38144f5a 2026-08-17T03:51:16Z\n"        # Sun 08-16 23:51 ET
               "09bfd0a2 2026-08-14T22:05:57Z\n")       # Fri 08-14 18:05 ET
        assert snapshot_dates(log) == [('38144f5a', '2026-08-14')]

    def test_a_bare_date_is_rejected_not_guessed(self):
        """A calendar day with no clock cannot name a session -- that was the bug."""
        from pipeline.tools.backfill_ticker_events import snapshot_dates
        assert snapshot_dates("aaa 2026-08-07\n") == []

    def test_both_backfills_ask_git_for_the_full_instant(self):
        """Wiring: a caller still passing --date=short would feed bare dates in
        and silently get nothing back."""
        from pathlib import Path
        tools = Path(__file__).resolve().parents[1] / 'tools'
        for name in ('backfill_ticker_events.py', 'backfill_preset_hits.py'):
            src = (tools / name).read_text()
            assert '--date=short' not in src, name
            assert 'GIT_LOG_FORMAT' in src, name


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
