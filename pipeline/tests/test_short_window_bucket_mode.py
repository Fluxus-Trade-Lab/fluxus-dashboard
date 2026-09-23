"""TSF-replication bucket mode (2026-09-23, branch feat/alex-theme-tsf-replication).

Andy 2026-09-22: 「关键是我们旧的那套和新的那套离 TSF 的准确度有多少。我们是要去靠近复刻它。」
His board is five non-overlapping two-week buckets; momentum is this bucket's
excess minus the previous bucket's, not the plain recent excess. Flag is OFF
until Andy adopts it (09-23: 「最后采纳不采纳我来确定」).
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.themes import short_window as SW


def _series(vals):
    idx = pd.bdate_range("2026-01-01", periods=len(vals))
    return pd.Series(vals, index=idx, dtype=float)


def _flat_bench(n):
    return _series(np.ones(n) * 100.0)


def test_flag_is_off_by_default():
    assert SW.BUCKET_MODE is False


def test_bucket_momentum_is_this_bucket_minus_the_one_before(monkeypatch):
    monkeypatch.setattr(SW, "BUCKET_MODE", True)
    n = 40
    # flat for the first bucket, then a steady climb: level positive and this
    # bucket beat the prior one -> Leading
    nav = _series(np.concatenate([np.ones(20) * 100, np.linspace(100, 120, 20)]))
    st = SW.state_series(nav, _flat_bench(n), "2w")
    assert st.iloc[-1] == "Leading"


def test_decelerating_outperformer_reads_weakening(monkeypatch):
    monkeypatch.setattr(SW, "BUCKET_MODE", True)
    n = 40
    # big move in the PRIOR bucket, a smaller one now: still above the
    # benchmark (level > 0) but this bucket is weaker -> Weakening
    nav = _series(np.concatenate([np.ones(20) * 100, np.linspace(100, 140, 10),
                                  np.linspace(140, 140.2, 10)]))
    st = SW.state_series(nav, _flat_bench(n), "2w")
    assert st.iloc[-1] == "Weakening"


def test_shipping_mode_reads_the_plain_recent_excess():
    # control: with the flag off the same flat-then-climb series is Leading too,
    # but for a different reason -- it must not raise or return None.
    n = 40
    nav = _series(np.concatenate([np.ones(20) * 100, np.linspace(100, 120, 20)]))
    st = SW.state_series(nav, _flat_bench(n), "2w")
    assert st.iloc[-1] in SW.STATES


def test_bucket_mode_needs_two_full_buckets(monkeypatch):
    monkeypatch.setattr(SW, "BUCKET_MODE", True)
    nav = _series(np.linspace(100, 110, 25))
    st = SW.state_series(nav, _flat_bench(25), "2w")
    assert pd.isna(st.iloc[19]) and st.iloc[-1] in SW.STATES
