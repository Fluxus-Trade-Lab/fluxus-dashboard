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


class TestDeduplication:
    """Many leg1 dates can map to the SAME confirmation date. Counting the
    identical outcome repeatedly inflates n without adding information."""

    def test_three_leg1_dates_one_confirmation_yields_one_instance(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[1], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'vcp'),
            (DATES[3], 'ABC', 'gainers_4pct'),   # the only confirmation
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert len(got) == 1
        assert got[0]['signal_date'] == DATES[3]

    def test_retained_instance_has_the_smallest_gap(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'),
            (DATES[1], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'vcp'),
            (DATES[3], 'ABC', 'gainers_4pct'),
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert got[0]['gap'] == 1                      # from DATES[2], not DATES[0]
        assert got[0]['leg_dates'] == [DATES[2], DATES[3]]

    def test_dedup_is_per_ticker(self):
        from pipeline.research.sequences import find_pair_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'), (DATES[1], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'gainers_4pct'),
            (DATES[0], 'XYZ', 'vcp'), (DATES[1], 'XYZ', 'vcp'),
            (DATES[2], 'XYZ', 'gainers_4pct'),
        ])
        got = find_pair_instances(ev, 'vcp', 'gainers_4pct', window=10)
        assert [(g['ticker'], g['gap']) for g in got] == [('ABC', 1), ('XYZ', 1)]

    def test_triples_dedupe_on_confirmation_too(self):
        from pipeline.research.sequences import find_triple_instances
        ev = _archive([
            (DATES[0], 'ABC', 'vcp'), (DATES[1], 'ABC', 'vcp'),
            (DATES[2], 'ABC', 'gainers_4pct'),
            (DATES[4], 'ABC', 'vol_up_gainers'),
        ])
        got = find_triple_instances(ev, 'vcp', 'gainers_4pct', 'vol_up_gainers',
                                    window=10)
        assert len(got) == 1
        assert got[0]['gap'] == 3                      # leg1 = DATES[1]
        assert got[0]['leg_dates'] == [DATES[1], DATES[2], DATES[4]]


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


def _outcome(excess_5=None, mfe=1.0, mae=-1.0, ret=0.01):
    return {'entry_date': '2026-05-05', 'entry_open': 100.0, 'atr': 2.0,
            'ret_5': ret, 'excess_5': excess_5, 'mfe_r_5': mfe, 'mae_r_5': mae}


class TestSummarize:
    def test_basic_statistics(self):
        from pipeline.research.sequences import summarize
        outs = [_outcome(excess_5=0.10, mfe=3.0, mae=-1.0),
                _outcome(excess_5=-0.02, mfe=1.0, mae=-2.0),
                _outcome(excess_5=0.04, mfe=2.0, mae=-0.5)]
        s = summarize(outs, horizons=(5,), lost=2)
        assert s['n'] == 3 and s['lost'] == 2
        assert s['median_excess_5'] == pytest.approx(0.04)
        assert s['mean_excess_5'] == pytest.approx((0.10 - 0.02 + 0.04) / 3)
        assert s['median_mfe_r_5'] == pytest.approx(2.0)
        assert s['median_mae_r_5'] == pytest.approx(-1.0)
        assert s['win_rate_5'] == pytest.approx(2 / 3)

    def test_none_excess_skipped_but_r_still_counted(self):
        from pipeline.research.sequences import summarize
        outs = [_outcome(excess_5=None, mfe=4.0, mae=-1.0),
                _outcome(excess_5=0.06, mfe=2.0, mae=-3.0)]
        s = summarize(outs, horizons=(5,))
        assert s['n'] == 2
        assert s['median_excess_5'] == pytest.approx(0.06)   # only the one
        assert s['win_rate_5'] == pytest.approx(1.0)
        assert s['median_mfe_r_5'] == pytest.approx(3.0)     # both counted

    def test_empty(self):
        from pipeline.research.sequences import summarize
        s = summarize([], horizons=(5,), lost=7)
        assert s['n'] == 0 and s['lost'] == 7
        assert s['median_excess_5'] is None and s['win_rate_5'] is None


class TestRandomInstances:
    def test_deterministic_for_a_seed(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B', 'C')])
        first = random_instances(ev, n=10, seed=42)
        second = random_instances(ev, n=10, seed=42)
        assert first == second
        assert len(first) == 10
        assert set(first[0]) == {'ticker', 'signal_date'}

    def test_different_seeds_differ(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B', 'C')])
        assert random_instances(ev, n=10, seed=1) != random_instances(ev, n=10, seed=2)

    def test_draws_come_from_the_archive_universe(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B')])
        for inst in random_instances(ev, n=20, seed=7):
            assert inst['ticker'] in {'A', 'B'}
            assert inst['signal_date'] in DATES

    def test_ticker_restriction(self):
        from pipeline.research.sequences import random_instances
        ev = _events([(d, t, 'vcp') for d in DATES for t in ('A', 'B', 'C')])
        for inst in random_instances(ev, n=15, seed=3, rng_tickers=['B']):
            assert inst['ticker'] == 'B'


class TestSplitAndStability:
    def test_split_dates_midpoint(self):
        from pipeline.research.sequences import split_dates
        ev = _events([(d, 'A', 'vcp') for d in DATES])
        mid, last = split_dates(ev)
        assert mid == DATES[4] and last == DATES[-1]

    def test_unstable_on_sign_disagreement(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 50, 'median_excess_10': 0.05}
        b = {'n': 50, 'median_excess_10': -0.03}
        assert is_unstable(a, b, 'median_excess_10') is True

    def test_stable_when_both_positive_and_powered(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 30, 'median_excess_10': 0.05}
        b = {'n': 25, 'median_excess_10': 0.02}
        assert is_unstable(a, b, 'median_excess_10') is False

    def test_unstable_when_a_half_is_underpowered(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 30, 'median_excess_10': 0.05}
        b = {'n': 3, 'median_excess_10': 0.04}
        assert is_unstable(a, b, 'median_excess_10') is True

    def test_unstable_when_a_half_has_no_value(self):
        from pipeline.research.sequences import is_unstable
        a = {'n': 30, 'median_excess_10': 0.05}
        b = {'n': 30, 'median_excess_10': None}
        assert is_unstable(a, b, 'median_excess_10') is True
