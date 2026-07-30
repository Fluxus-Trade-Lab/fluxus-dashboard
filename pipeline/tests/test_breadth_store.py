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
