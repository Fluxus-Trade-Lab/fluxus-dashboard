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
