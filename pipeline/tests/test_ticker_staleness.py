"""Tests for the ticker-store freshness guard (pure functions — no network, and
no assertions against the live data/output/tickers/, which would make the suite
fail simply because time passed)."""
import datetime as dt
import json

import pytest

from pipeline.tickers.staleness import (
    audit_freshness,
    last_bar_date,
    last_completed_session,
    main,
    trading_days_between,
)

# 2026-08-07 is a Friday; 08-08/08-09 are the weekend; 08-10 a Monday.
FRI = dt.date(2026, 8, 7)
SAT = dt.date(2026, 8, 8)
MON = dt.date(2026, 8, 10)


def _ticker(tmp_path, sym, last_date, *, key='ohlc_2y', bars=None):
    """Write a minimal ticker file whose newest bar is `last_date`."""
    if bars is None:
        bars = [] if last_date is None else [{
            'date': last_date, 'open': 1.0, 'high': 1.0,
            'low': 1.0, 'close': 1.0, 'volume': 1.0,
        }]
    (tmp_path / f'{sym}.json').write_text(json.dumps({'ticker': sym, key: bars}))


class TestLastCompletedSession:
    def test_skips_back_over_the_weekend(self):
        # As of Monday, the last completed session is Friday.
        assert last_completed_session(MON) == FRI

    def test_excludes_today(self):
        # Today's daily bar does not exist until the close, so a pipeline running
        # on Friday afternoon must not expect a Friday bar.
        assert last_completed_session(FRI) == dt.date(2026, 8, 6)

    def test_skips_holidays(self):
        # 2026-07-03 (observed Independence Day) and the weekend before it:
        # as of Monday 2026-07-06 the last session is Thursday 2026-07-02.
        assert last_completed_session(dt.date(2026, 7, 6)) == dt.date(2026, 7, 2)


class TestTradingDaysBetween:
    def test_zero_when_equal(self):
        assert trading_days_between(FRI, FRI) == 0

    def test_zero_when_end_before_start(self):
        assert trading_days_between(MON, FRI) == 0

    def test_weekend_counts_as_one_trading_day(self):
        assert trading_days_between(FRI, MON) == 1

    def test_counts_the_real_may_to_august_gap(self):
        # The actual staleness this guard exists to catch: 2026-05-22 → 2026-08-07.
        assert trading_days_between(dt.date(2026, 5, 22), FRI) == 52


class TestLastBarDate:
    def test_reads_ohlc_2y(self, tmp_path):
        _ticker(tmp_path, 'AAA', '2026-08-07')
        assert last_bar_date(tmp_path / 'AAA.json') == '2026-08-07'

    def test_falls_back_to_ohlc_1y(self, tmp_path):
        _ticker(tmp_path, 'BBB', '2026-05-22', key='ohlc_1y')
        assert last_bar_date(tmp_path / 'BBB.json') == '2026-05-22'

    def test_prefers_ohlc_2y_over_1y(self, tmp_path):
        (tmp_path / 'CCC.json').write_text(json.dumps({
            'ohlc_1y': [{'date': '2026-05-22'}],
            'ohlc_2y': [{'date': '2026-08-07'}],
        }))
        assert last_bar_date(tmp_path / 'CCC.json') == '2026-08-07'

    def test_empty_bars_is_none(self, tmp_path):
        _ticker(tmp_path, 'DDD', None)
        assert last_bar_date(tmp_path / 'DDD.json') is None

    def test_malformed_json_is_none(self, tmp_path):
        (tmp_path / 'EEE.json').write_text('{not json')
        assert last_bar_date(tmp_path / 'EEE.json') is None

    def test_missing_file_is_none(self, tmp_path):
        assert last_bar_date(tmp_path / 'nope.json') is None


class TestAuditFreshness:
    def test_all_fresh(self, tmp_path):
        for sym in ('AAA', 'BBB', 'CCC'):
            _ticker(tmp_path, sym, '2026-08-07')
        r = audit_freshness(tmp_path, as_of=SAT)
        assert (r.total, r.fresh, r.stale_count) == (3, 3, 0)
        assert r.stale_share == 0.0

    def test_flags_the_may_cohort(self, tmp_path):
        for sym in ('AAA', 'BBB'):
            _ticker(tmp_path, sym, '2026-08-07')
        _ticker(tmp_path, 'PLTR', '2026-05-22')
        r = audit_freshness(tmp_path, as_of=SAT)
        assert r.stale_count == 1
        assert r.stale[0].ticker == 'PLTR'
        assert r.stale[0].lag_trading_days == 52
        assert r.stale_share == pytest.approx(1 / 3)

    def test_weekend_lag_is_not_stale(self, tmp_path):
        # Friday bar, audited on Monday → 1 trading day behind, within tolerance.
        _ticker(tmp_path, 'AAA', FRI.isoformat())
        assert audit_freshness(tmp_path, as_of=MON).stale_count == 0

    def test_max_lag_boundary(self, tmp_path):
        _ticker(tmp_path, 'AAA', '2026-08-05')  # 2 trading days before 08-07
        assert audit_freshness(tmp_path, as_of=SAT, max_lag=2).stale_count == 0
        assert audit_freshness(tmp_path, as_of=SAT, max_lag=1).stale_count == 1

    def test_benchmarks_file_is_not_a_ticker(self, tmp_path):
        _ticker(tmp_path, 'AAA', '2026-08-07')
        (tmp_path / '_benchmarks.json').write_text(json.dumps({'benchmarks': {}}))
        assert audit_freshness(tmp_path, as_of=SAT).total == 1

    def test_file_with_no_ohlc_is_stale(self, tmp_path):
        (tmp_path / 'AAA.json').write_text(json.dumps({'ticker': 'AAA'}))
        r = audit_freshness(tmp_path, as_of=SAT)
        assert r.stale_count == 1
        assert r.stale[0].last_bar is None

    def test_unparseable_date_is_stale(self, tmp_path):
        _ticker(tmp_path, 'AAA', 'not-a-date')
        assert audit_freshness(tmp_path, as_of=SAT).stale_count == 1

    def test_stale_sorted_worst_first(self, tmp_path):
        _ticker(tmp_path, 'RECENT', '2026-07-31')
        _ticker(tmp_path, 'ANCIENT', '2026-05-22')
        r = audit_freshness(tmp_path, as_of=SAT)
        assert [s.ticker for s in r.stale] == ['ANCIENT', 'RECENT']

    def test_empty_dir_reports_no_stale_share(self, tmp_path):
        r = audit_freshness(tmp_path, as_of=SAT)
        assert (r.total, r.stale_share) == (0, 0.0)


class TestCli:
    def _store(self, tmp_path, n_fresh, n_stale):
        for i in range(n_fresh):
            _ticker(tmp_path, f'OK{i}', '2026-08-07')
        for i in range(n_stale):
            _ticker(tmp_path, f'OLD{i}', '2026-05-22')

    def test_clean_store_exits_zero(self, tmp_path):
        self._store(tmp_path, 10, 0)
        assert main(['--tickers-dir', str(tmp_path), '--as-of', SAT.isoformat(), '--fail']) == 0

    def test_breach_fails_with_flag(self, tmp_path):
        self._store(tmp_path, 5, 5)  # 50% stale
        assert main(['--tickers-dir', str(tmp_path), '--as-of', SAT.isoformat(), '--fail']) == 1

    def test_breach_only_warns_without_flag(self, tmp_path):
        self._store(tmp_path, 5, 5)
        assert main(['--tickers-dir', str(tmp_path), '--as-of', SAT.isoformat()]) == 0

    def test_one_stale_name_is_under_threshold(self, tmp_path):
        self._store(tmp_path, 99, 1)  # 1% — noise, not a broken refresh
        assert main(['--tickers-dir', str(tmp_path), '--as-of', SAT.isoformat(), '--fail']) == 0

    def test_threshold_is_configurable(self, tmp_path):
        self._store(tmp_path, 99, 1)
        assert main(['--tickers-dir', str(tmp_path), '--as-of', SAT.isoformat(), '--fail',
                     '--max-stale-share', '0.001']) == 1

    def test_missing_dir_exits_one(self, tmp_path):
        assert main(['--tickers-dir', str(tmp_path / 'nope'), '--as-of', SAT.isoformat()]) == 1
