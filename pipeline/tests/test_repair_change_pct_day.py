"""Reconciliation and counting rules for the single-day change_pct repair."""

import pandas as pd

from pipeline.tools.repair_change_pct_day import counts_from_changes, reconcile


class TestReconcile:
    def test_agreeing_sources_pass_through_untouched(self):
        snap = pd.Series({'A': 0.05, 'B': -0.02, 'C': 0.0})
        adj = pd.Series({'A': 0.05, 'B': -0.02, 'C': 0.0})
        merged, stats = reconcile(snap, adj)
        assert merged.to_dict() == snap.to_dict()
        assert stats['flagged'] == 0
        assert stats['split_overrides'] == []

    def test_small_disagreement_keeps_the_snapshot_value(self):
        """The 2026-08-07 case: yfinance carried a stale flat bar for CHEC.

        A plainly real move in the point-in-time snapshots must not be
        overwritten by a validator that merely disagrees.
        """
        snap = pd.Series({'CHEC': -0.0901})
        adj = pd.Series({'CHEC': 0.0})
        merged, stats = reconcile(snap, adj)
        assert merged['CHEC'] == -0.0901
        assert stats['flagged'] == 1
        assert stats['split_overrides'] == []
        assert 'CHEC' in stats['flagged_names']

    def test_split_sized_gap_takes_the_adjusted_value(self):
        """A 2-for-1 halves the raw quote; only the adjusted source is right."""
        snap = pd.Series({'SPLIT': -0.50})
        adj = pd.Series({'SPLIT': 0.01})
        merged, stats = reconcile(snap, adj)
        assert merged['SPLIT'] == 0.01
        assert stats['split_overrides'] == ['SPLIT']

    def test_names_the_validator_lacks_are_kept_and_counted(self):
        """Delisted-since names still belong to that day's roster."""
        snap = pd.Series({'A': 0.05, 'GONE': -0.03})
        adj = pd.Series({'A': 0.05})
        merged, stats = reconcile(snap, adj)
        assert merged['GONE'] == -0.03
        assert stats['unverified'] == 1
        assert stats['overlap'] == 1

    def test_validator_only_names_are_dropped(self):
        """The roster is the snapshot's; yfinance cannot add members to it."""
        snap = pd.Series({'A': 0.05})
        adj = pd.Series({'A': 0.05, 'EXTRA': 0.09})
        merged, _ = reconcile(snap, adj)
        assert 'EXTRA' not in merged.index


class TestCounts:
    def test_predicates_match_compute_snapshot(self):
        """Same boundaries as breadth_metrics: >=4%, <=-4%, >0, <0."""
        chg = pd.Series({
            'up': 0.041, 'up_edge': 0.04, 'flat': 0.0,
            'dn_edge': -0.04, 'dn': -0.041, 'small_up': 0.001,
        })
        assert counts_from_changes(chg) == {
            'up_4pct': 2, 'down_4pct': 2, 'advances': 3, 'declines': 2,
        }

    def test_flat_names_count_as_neither(self):
        chg = pd.Series({'a': 0.0, 'b': 0.0})
        counts = counts_from_changes(chg)
        assert counts['advances'] == 0 and counts['declines'] == 0
