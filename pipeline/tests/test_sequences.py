"""Tests for sequence enumeration over the event archive."""
import pandas as pd
import pytest


def _events(rows):
    """rows: (date, ticker, screener) tuples."""
    return pd.DataFrame(
        [{'date': d, 'ticker': t, 'screener': s} for d, t, s in rows],
        columns=['date', 'ticker', 'screener'],
    )


# 10 consecutive archive sessions, deliberately NOT contiguous calendar days
DATES = ['2026-05-01', '2026-05-04', '2026-05-05', '2026-05-06', '2026-05-07',
         '2026-05-08', '2026-05-11', '2026-05-12', '2026-05-13', '2026-05-14']


def _archive(rows):
    """Events frame carrying the full 10-session archive universe.

    The real archive is dense — every session date has events — and
    session ordinals are derived from the frame itself. A marker row per
    session makes the sparse fixtures carry the same universe, so gaps
    are measured in archive-session index, never calendar days.
    """
    return _events([(d, '_MKT', '_session') for d in DATES] + list(rows))


class TestSessionIndex:
    def test_maps_dates_to_ordinals(self):
        from pipeline.research.sequences import session_index
        ev = _events([(d, 'ABC', 'vcp') for d in DATES])
        idx = session_index(ev)
        assert idx[DATES[0]] == 0 and idx[DATES[-1]] == 9

    def test_ignores_duplicates_and_sorts(self):
        from pipeline.research.sequences import session_index
        ev = _events([(DATES[3], 'A', 'vcp'), (DATES[1], 'B', 'vcp'),
                      (DATES[3], 'C', 'vcp')])
        assert session_index(ev) == {DATES[1]: 0, DATES[3]: 1}


class TestFindPairInstances:
    def test_finds_planted_sequence(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ABC', 'episodic_pivot'),
            (DATES[3], 'ABC', 'gainers_4pct'),
            (DATES[2], 'XYZ', 'vcp'),          # different screener, no match
        ])
        got = find_pair_instances(ev, 'episodic_pivot', 'gainers_4pct', window=10)
        assert len(got) == 1
        assert got[0]['ticker'] == 'ABC'
        assert got[0]['signal_date'] == DATES[3]
        assert got[0]['leg_dates'] == [DATES[0], DATES[3]]
        assert got[0]['gap'] == 3

    def test_window_boundary_inclusive_then_exclusive(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([(DATES[0], 'ABC', 'vcp'), (DATES[3], 'ABC', 'gainers_4pct')])
        assert len(find_pair_instances(ev, 'vcp', 'gainers_4pct', window=3)) == 1
        assert len(find_pair_instances(ev, 'vcp', 'gainers_4pct', window=2)) == 0

    def test_same_day_is_not_a_sequence(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([(DATES[2], 'ABC', 'vcp'), (DATES[2], 'ABC', 'gainers_4pct')])
        assert find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10) == []

    def test_only_first_qualifying_b_counts(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'gainers_4pct'),
            (DATES[4], 'ABC', 'gainers_4pct'),   # later b for the same a
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert len(got) == 1 and got[0]['signal_date'] == DATES[2]

    def test_separate_a_events_each_produce_an_instance(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'), (DATES[1], 'ABC', 'gainers_4pct'),
            (DATES[5], 'ABC', 'vcp'), (DATES[6], 'ABC', 'gainers_4pct'),
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert [g['signal_date'] for g in got] == [DATES[1], DATES[6]]

    def test_b_before_a_is_not_a_sequence(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([(DATES[0], 'ABC', 'gainers_4pct'), (DATES[3], 'ABC', 'vcp')])
        assert find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10) == []

    def test_tickers_are_independent(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([(DATES[0], 'ABC', 'vcp'), (DATES[1], 'XYZ', 'gainers_4pct')])
        assert find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10) == []

    def test_empty_and_unknown(self):
        from pipeline.research.sequences import find_pair_instances
        assert find_pair_instances(_events([]), 'vcp', 'gainers_4pct') == []
        ev = _archive([(DATES[0], 'ABC', 'vcp')])
        assert find_pair_instances(ev, 'vcp', 'nope') == []

    def test_sorted_by_signal_date_then_ticker(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ZZZ', 'vcp'), (DATES[2], 'ZZZ', 'gainers_4pct'),
            (DATES[0], 'AAA', 'vcp'), (DATES[2], 'AAA', 'gainers_4pct'),
            (DATES[0], 'MMM', 'vcp'), (DATES[1], 'MMM', 'gainers_4pct'),
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert [(g['signal_date'], g['ticker']) for g in got] == [
            (DATES[1], 'MMM'), (DATES[2], 'AAA'), (DATES[2], 'ZZZ')]


class TestFindTripleInstances:
    def test_finds_planted_triple(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'gainers_4pct'),
            (DATES[5], 'ABC', 'vol_up_gainers'),
        ])
        got = find_triple_instances(ev, 'vcp', 'gainers_4pct', 'vol_up_gainers',
                                    window=10)
        assert len(got) == 1
        assert got[0]['signal_date'] == DATES[5]
        assert got[0]['leg_dates'] == [DATES[0], DATES[2], DATES[5]]
        assert got[0]['gap'] == 5

    def test_each_leg_respects_the_window(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[1], 'ABC', 'gainers_4pct'),
            (DATES[6], 'ABC', 'vol_up_gainers'),   # 5 sessions after leg 2
        ])
        assert len(find_triple_instances(ev, 'vcp', 'gainers_4pct',
                                         'vol_up_gainers', window=5)) == 1
        assert find_triple_instances(ev, 'vcp', 'gainers_4pct',
                                     'vol_up_gainers', window=4) == []

    def test_missing_third_leg_yields_nothing(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _archive([(DATES[0], 'ABC', 'vcp'), (DATES[2], 'ABC', 'gainers_4pct')])
        assert find_triple_instances(ev, 'vcp', 'gainers_4pct',
                                     'vol_up_gainers', window=10) == []
