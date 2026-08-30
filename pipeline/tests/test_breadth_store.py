"""Tests for the canonical breadth archive store."""
import pytest
import pandas as pd


def _write_legacy_csv(path):
    """Legacy-format CSV: no source/net_advances/rana/13pct cols, dup + poisoned row."""
    path.write_text(
        "date,universe_size,spx_close,up_4pct,down_4pct,ratio_5d,ratio_10d,"
        "up_25pct_qtr,down_25pct_qtr,up_25pct_month,down_25pct_month,"
        "up_50pct_month,down_50pct_month,t2108,pct_above_200sma,pct_above_50sma,"
        "pct_above_20sma,advances,declines,new_highs,new_lows,ad_line,mcclellan_osc\n"
        "2026-07-24,2900,7400.0,100,50,1.5,1.4,300,200,80,60,20,10,45.0,46.0,47.0,38.0,1500,1300,40,20,1000,5.0\n"
        "2026-07-25,2950,7405.0,110,60,1.4,1.3,310,210,82,61,21,11,45.5,46.5,47.5,38.5,1550,1350,42,22,1200,6.0\n"
        "2026-07-26,3000,7411.0,178,454,0.96,1.07,2,4,0,1,0,0,0.27,0.47,0.3,0.2,1438,1437,11,6,12244,23.7\n"
        "2026-07-26,3000,7411.0,178,454,0.73,0.99,319,528,83,231,24,53,45.1,45.97,46.7,38.43,1438,1437,251,147,12245,11.7\n"
    )


class TestLoadArchive:
    def test_missing_file_returns_empty_frame_with_columns(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive, BREADTH_COLUMNS
        frame = load_archive(str(tmp_path / 'nope.csv'))
        assert list(frame.columns) == BREADTH_COLUMNS
        assert len(frame) == 0

    def test_legacy_csv_migrates_and_dedupes_keep_last(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive
        p = tmp_path / 'archive.csv'
        _write_legacy_csv(p)
        frame = load_archive(str(p))
        assert len(frame) == 3  # dup 07-26 collapsed
        last = frame.iloc[-1]
        assert last['date'] == '2026-07-26'
        assert float(last['t2108']) == 45.1  # keep-LAST kept the good row
        assert (frame['source'] == 'live').all()  # legacy rows marked live
        assert 'up_13pct_34d' in frame.columns    # missing cols added

    def test_sorted_ascending(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive
        p = tmp_path / 'archive.csv'
        _write_legacy_csv(p)
        frame = load_archive(str(p))
        assert list(frame['date']) == sorted(frame['date'])

    def test_corrupt_file_raises_loudly(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive, BreadthArchiveError
        p = tmp_path / 'archive.csv'
        p.write_text('\x00\x01 not a csv at all')
        with pytest.raises(BreadthArchiveError):
            load_archive(str(p))


class TestDerive:
    def _frame(self, advances, declines, up4=None, down4=None):
        import pandas as pd
        n = len(advances)
        return pd.DataFrame({
            'date': [f'2026-01-{i+1:02d}' for i in range(n)],
            'advances': advances,
            'declines': declines,
            'up_4pct': up4 if up4 is not None else [0] * n,
            'down_4pct': down4 if down4 is not None else [0] * n,
        })

    def test_ad_line_is_true_cumulative(self):
        from pipeline.screeners.breadth_store import derive
        frame = derive(self._frame([300, 100, 250], [100, 300, 50]))
        assert list(frame['net_advances']) == [200, -200, 200]
        assert list(frame['ad_line']) == [200, 0, 200]

    def test_rana_is_universe_size_invariant(self):
        from pipeline.screeners.breadth_store import derive
        # Same 2:1 breadth on a 300-name day and a 3000-name day → identical rana
        frame = derive(self._frame([200, 2000], [100, 1000]))
        assert frame['rana'].iloc[0] == frame['rana'].iloc[1] == pytest.approx(333.33, abs=0.01)

    def test_rana_zero_when_no_participants(self):
        from pipeline.screeners.breadth_store import derive
        frame = derive(self._frame([0], [0]))
        assert frame['rana'].iloc[0] == 0.0

    def test_mcclellan_exact_value_after_step(self):
        from pipeline.screeners.breadth_store import derive
        # 39 zero-rana days then one day of rana=1000:
        # ema19 alpha=2/20 → 100.0; ema39 alpha=2/40 → 50.0; osc = 50.0 exactly.
        adv = [0] * 39 + [1000]
        dec = [0] * 40   # rana: 0 for first 39 (0/0→0), then 1000*1000/1000
        frame = derive(self._frame(adv, dec))
        assert frame['mcclellan_osc'].iloc[-1] == pytest.approx(50.0, abs=0.01)
        assert frame['mcclellan_osc'].iloc[-2] == pytest.approx(0.0, abs=0.01)

    def test_ratios_rolling_window(self):
        from pipeline.screeners.breadth_store import derive
        up4 = [10, 20, 30, 40, 50, 60]
        down4 = [5, 5, 5, 5, 5, 5]
        frame = derive(self._frame([0] * 6, [0] * 6, up4, down4))
        # day 6 ratio_5d = (20+30+40+50+60)/(5*5) = 200/25 = 8.0
        assert frame['ratio_5d'].iloc[-1] == pytest.approx(8.0)
        # day 1 (window of 1): 10/5
        assert frame['ratio_5d'].iloc[0] == pytest.approx(2.0)

    def test_ratio_zero_downs_returns_up_sum(self):
        from pipeline.screeners.breadth_store import derive
        frame = derive(self._frame([0], [0], [7], [0]))
        assert frame['ratio_5d'].iloc[0] == pytest.approx(7.0)

    def test_pure_no_mutation(self):
        from pipeline.screeners.breadth_store import derive
        original = self._frame([300], [100])
        snapshot = original.copy(deep=True)
        derive(original)
        pd.testing.assert_frame_equal(original, snapshot)

    def test_prefix_consistency_for_replay(self):
        """derive(frame[:k]) must equal derive(frame)[:k] — Spec 3 depends on this."""
        from pipeline.screeners.breadth_store import derive
        frame = self._frame([300, 100, 250, 400], [100, 300, 50, 90],
                            [10, 20, 30, 40], [5, 6, 7, 8])
        full = derive(frame)
        prefix = derive(frame.iloc[:2].reset_index(drop=True))
        for col in ['net_advances', 'rana', 'ad_line', 'mcclellan_osc', 'ratio_5d', 'ratio_10d']:
            assert list(prefix[col]) == list(full[col].iloc[:2]), col


class TestUpsertAndWrite:
    def test_upsert_appends_new_date(self):
        from pipeline.screeners.breadth_store import load_archive, upsert_row
        frame = load_archive('/nonexistent/x.csv')
        frame = upsert_row(frame, {'date': '2026-07-28', 'source': 'live', 'advances': 100, 'declines': 50})
        assert len(frame) == 1

    def test_upsert_replaces_same_date(self):
        from pipeline.screeners.breadth_store import load_archive, upsert_row
        frame = load_archive('/nonexistent/x.csv')
        frame = upsert_row(frame, {'date': '2026-07-28', 'source': 'backfill', 'advances': 1, 'declines': 1})
        frame = upsert_row(frame, {'date': '2026-07-28', 'source': 'live', 'advances': 100, 'declines': 50})
        assert len(frame) == 1
        assert frame.iloc[0]['source'] == 'live'
        assert frame.iloc[0]['advances'] == 100

    def test_write_then_load_roundtrip(self, tmp_path):
        from pipeline.screeners.breadth_store import load_archive, upsert_row, write_archive
        p = str(tmp_path / 'a.csv')
        frame = upsert_row(load_archive(p), {'date': '2026-07-28', 'source': 'live',
                                             'advances': 100, 'declines': 50, 'up_4pct': 10, 'down_4pct': 5})
        write_archive(frame, p)
        again = load_archive(p)
        assert len(again) == 1
        assert again.iloc[0]['date'] == '2026-07-28'

    def test_write_is_atomic_no_partial_on_same_dir(self, tmp_path):
        from pipeline.screeners.breadth_store import write_archive, load_archive, upsert_row
        p = str(tmp_path / 'a.csv')
        frame = upsert_row(load_archive(p), {'date': '2026-07-28', 'source': 'live',
                                             'advances': 1, 'declines': 1})
        write_archive(frame, p)
        leftovers = [f for f in tmp_path.iterdir() if f.name != 'a.csv']
        assert leftovers == []  # temp file cleaned up by os.replace

    def test_written_archive_is_world_readable(self, tmp_path):
        """mkstemp defaults to 0600; the archive is committed data, not a secret."""
        import stat
        from pipeline.screeners.breadth_store import write_archive, load_archive, upsert_row
        p = tmp_path / 'a.csv'
        frame = upsert_row(load_archive(str(p)), {'date': '2026-07-28', 'source': 'live'})
        write_archive(frame, str(p))
        assert stat.S_IMODE(p.stat().st_mode) == 0o644


class TestQualityGuard:
    _TODAY = '2026-07-27'  # 2 calendar days after the frame's last row

    def _last_frame(self, pct200=46.0, date='2026-07-25'):
        import pandas as pd
        return pd.DataFrame({'date': [date], 'pct_above_200sma': [pct200]})

    def _good_snapshot(self):
        return {'universe_size': 3000, 'pct_above_200sma': 45.0}

    def test_accepts_good_row(self):
        from pipeline.screeners.breadth_store import check_quality
        ok, reason = check_quality(self._last_frame(), self._good_snapshot(),
                                   null_rate=0.02, today_iso=self._TODAY)
        assert ok and reason == ''

    def test_rejects_small_universe(self):
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'universe_size': 1400}
        ok, reason = check_quality(self._last_frame(), snap,
                                   null_rate=0.02, today_iso=self._TODAY)
        assert not ok and 'universe' in reason

    def test_rejects_high_null_rate(self):
        from pipeline.screeners.breadth_store import check_quality
        ok, reason = check_quality(self._last_frame(), self._good_snapshot(),
                                   null_rate=0.35, today_iso=self._TODAY)
        assert not ok and 'null' in reason

    def test_rejects_identical_spx_close(self):
        """2026-08-17: stale index bar filed under a new session scored 87.5."""
        import pandas as pd
        from pipeline.screeners.breadth_store import check_quality
        frame = pd.DataFrame({'date': ['2026-08-14'], 'pct_above_200sma': [51.9],
                              'spx_close': [7785.759765625]})
        ok, reason = check_quality(frame, self._good_snapshot(), null_rate=0.02,
                                   today_iso=self._TODAY, spx_close=7785.759765625)
        assert not ok and 'identical' in reason
        ok, _ = check_quality(frame, self._good_snapshot(), null_rate=0.02,
                              today_iso=self._TODAY, spx_close=7745.06)
        assert ok
        # no spx_close known -> the check is skipped, not tripped
        ok, _ = check_quality(frame, self._good_snapshot(), null_rate=0.02,
                              today_iso=self._TODAY, spx_close=None)
        assert ok

    def test_rejects_pct200_jump(self):
        """The 2026-07-26 poisoned row: 46.0 → 0.47 must be rejected."""
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'pct_above_200sma': 0.47}
        ok, reason = check_quality(self._last_frame(46.0), snap,
                                   null_rate=0.02, today_iso=self._TODAY)
        assert not ok and 'pct_above_200sma' in reason

    def test_first_ever_row_skips_delta_check(self):
        from pipeline.screeners.breadth_store import check_quality, load_archive
        empty = load_archive('/nonexistent/x.csv')
        ok, _ = check_quality(empty, self._good_snapshot(),
                              null_rate=0.02, today_iso=self._TODAY)
        assert ok

    def test_delta_check_skipped_when_previous_row_is_implausible(self):
        """A poisoned tail row must not wedge the guard shut forever."""
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'pct_above_200sma': 46.0}
        ok, reason = check_quality(self._last_frame(0.4), snap,
                                   null_rate=0.02, today_iso=self._TODAY)
        assert ok and reason == ''

    def test_delta_check_skipped_after_a_long_gap(self):
        """8 calendar days of staleness makes a 30-pt move legitimate."""
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'pct_above_200sma': 16.0}
        ok, reason = check_quality(self._last_frame(46.0, date='2026-07-19'), snap,
                                   null_rate=0.02, today_iso=self._TODAY)
        assert ok and reason == ''

    def test_delta_check_still_applies_one_day_later(self):
        from pipeline.screeners.breadth_store import check_quality
        snap = {**self._good_snapshot(), 'pct_above_200sma': 16.0}
        ok, reason = check_quality(self._last_frame(46.0, date='2026-07-26'), snap,
                                   null_rate=0.02, today_iso=self._TODAY)
        assert not ok and 'pct_above_200sma' in reason


class TestRecordHighPercent:
    """Record High Percent and the High-Low Index (StockCharts ChartSchool).

    RHP = new highs / (new highs + new lows). High-Low Index = its 10-day SMA.
    Adopted 2026-08-31 for one reason above all: they are RATIOS. The raw
    counts in this archive are not comparable across time, because the
    universe stepped from 3000 to 5614 names on 2026-08-14 -- a break that
    silently corrupted a 21-day comparison reported to Andy on 08-30.
    """

    def _frame(self, nh, nl, **over):
        import pandas as pd
        n = len(nh)
        base = {
            'date': pd.date_range('2026-01-01', periods=n, freq='B').strftime('%Y-%m-%d'),
            'advances': [100] * n, 'declines': [100] * n,
            'up_4pct': [1] * n, 'down_4pct': [1] * n,
            'new_highs_common': nh, 'new_lows_common': nl,
        }
        base.update(over)
        return pd.DataFrame(base)

    def test_exact_ratio(self):
        from pipeline.screeners.breadth_store import derive
        out = derive(self._frame([30], [10]))
        assert float(out['record_high_pct'].iloc[0]) == 75.0

    def test_immune_to_the_universe_doubling(self):
        """The reason this indicator exists here.

        Double every count -- as happened on 2026-08-14 when the universe went
        3000 -> 5614 -- and the ratio must not move. If this fails, the ratio
        has picked up a level dependence and the 08-14 break is back.
        """
        from pipeline.screeners.breadth_store import derive
        small = derive(self._frame([30], [10]))
        big = derive(self._frame([60], [20]))
        assert float(small['record_high_pct'].iloc[0]) == float(big['record_high_pct'].iloc[0])
        # ... while the raw difference the old readings used DOES move
        assert (60 - 20) != (30 - 10)

    def test_a_flat_day_is_fifty_not_missing(self):
        """Zero highs and zero lows is a real reading, not absent data."""
        from pipeline.screeners.breadth_store import derive
        out = derive(self._frame([0], [0]))
        assert float(out['record_high_pct'].iloc[0]) == 50.0

    def test_high_low_index_is_the_10_day_average(self):
        from pipeline.screeners.breadth_store import derive
        out = derive(self._frame([50] * 12, [50] * 12))   # RHP == 50 every day
        assert out['high_low_index'].iloc[:9].isna().all()   # not enough history
        assert float(out['high_low_index'].iloc[9]) == 50.0

    def test_null_when_the_common_counts_are_absent(self):
        """Archive rows predating the columns must not fall back to raw counts.

        Falling back would put a definition change INSIDE one series -- the
        exact failure mode this indicator was adopted to avoid.
        """
        from pipeline.screeners.breadth_store import derive
        f = self._frame([30], [10]).drop(columns=['new_highs_common', 'new_lows_common'])
        out = derive(f)
        assert out['record_high_pct'].isna().all()
        assert out['high_low_index'].isna().all()
