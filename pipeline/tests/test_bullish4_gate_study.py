"""Tests for the 4% Bullish gate study (pipeline/tools/bullish4_gate_study.py).

The study's only original arithmetic is the as-of feature block; the forward
returns and the baseline come from scanner_event_study, which has its own
tests. So these pin the as-of readings against bars whose answers are known by
construction, and pin the cohort split to the gate values in summary.md §三.2.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.tools import bullish4_gate_study as B


def bars(closes, *, start="2026-01-02"):
    """Daily bars from a close series; high/low straddle the close by 1%."""
    idx = pd.bdate_range(start, periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99,
                         "Close": c, "Volume": 1e6}, index=idx)


def test_needs_a_full_sma50_window():
    b = bars([100.0] * 40)
    assert B.asof_features(b, b.index[-1]) == {}


def test_flat_tape_sits_on_its_own_line():
    """close == SMA50 -> the ATR multiple is 0, not None: a real reading."""
    b = bars([100.0 + (i % 2) * 0.5 for i in range(80)])
    f = B.asof_features(b, b.index[-1])
    assert f["atr_from_sma50"] == pytest.approx(0.0, abs=1.5)


def test_the_multiple_is_signed():
    up = bars(list(np.linspace(50, 100, 80)))
    down = bars(list(np.linspace(100, 50, 80)))
    assert B.asof_features(up, up.index[-1])["atr_from_sma50"] > 0
    assert B.asof_features(down, down.index[-1])["atr_from_sma50"] < 0


def test_bar_change_is_close_over_previous_close():
    closes = [100.0] * 79 + [110.0]
    b = bars(closes)
    assert B.asof_features(b, b.index[-1])["bar_change"] == pytest.approx(0.10)


def test_high_20d_window_is_twenty_sessions_not_all_history():
    """An 80 spike at bar 55 blocks a 60 five bars later, but not a 70 that
    reads it 24 bars later -- by then the spike has left the window."""
    closes = [50.0] * 55 + [80.0] + [60.0] * 23 + [70.0]
    b = bars(closes)
    assert B.asof_features(b, b.index[60])["high_20d"] is False   # spike still in view
    assert B.asof_features(b, b.index[-1])["high_20d"] is True    # spike aged out


def test_rs_high_needs_spy_and_compares_the_ratio_not_the_price():
    """A name up 10% while SPY is up 20% is at a 21-day RS LOW, not a high."""
    n = 80
    name = bars([100.0] * (n - 1) + [110.0])
    spy = bars([100.0] * (n - 21) + list(np.linspace(101, 120, 21)))
    f = B.asof_features(name, name.index[-1], spy["Close"])
    assert f["rs_high_21"] is False
    # without SPY the field is unknown, not False
    assert B.asof_features(name, name.index[-1])["rs_high_21"] is None
    # and a name outrunning a flat SPY is a high
    flat = bars([100.0] * n)
    assert B.asof_features(name, name.index[-1], flat["Close"])["rs_high_21"] is True


def test_gate_values_are_the_ones_the_report_proposed():
    assert (B.ATR_GATE, B.CHG_GATE, B.CHASE) == (4.0, 0.08, 0.15)


def test_cohorts_split_on_both_gates_and_are_complementary():
    n = 80
    near = bars([100.0] * (n - 1) + [104.0])          # ~0 ATR from SMA50
    far = bars(list(np.linspace(20, 100, n)))         # far above SMA50
    b = {"near": near, "far": far, "SPY": bars([100.0] * n)}
    d = str(near.index[-1].date())
    hits = [(d, "near", 0.05), (d, "near", 0.20), (d, "far", 0.05)]
    # the duplicate (d, near) is the caller's problem; feed distinct rows
    ev, detail = B.cohorts([(d, "near", 0.05), (d, "far", 0.05)], b)
    assert [t for _, t in ev["gated"]] == ["near"]
    assert [t for _, t in ev["dropped"]] == ["far"]
    # gated + dropped partitions everything measured
    assert len(ev["gated"]) + len(ev["dropped"]) == len(ev["all"]) == len(detail)
    # a chase-sized move on the same near name is dropped by the change gate
    ev2, _ = B.cohorts([(d, "near", 0.20)], b)
    assert ev2["gated"] == [] and [t for _, t in ev2["chg_ge15"]] == ["near"]


def test_load_hits_dedupes_a_repeated_date_ticker(tmp_path):
    p = tmp_path / "events.csv"
    p.write_text(
        "date,ticker,screener,change_pct\n"
        "2026-05-01,AAA,preset:4_bullish,0.05\n"
        "2026-05-01,AAA,preset:4_bullish,0.09\n"
        "2026-05-01,BBB,other,0.05\n"
        "2026-05-02,AAA,preset:4_bullish,\n"
    )
    hits = B.load_hits(p)
    assert [(d, t) for d, t, _ in hits] == [("2026-05-01", "AAA"), ("2026-05-02", "AAA")]
    assert hits[0][2] == pytest.approx(0.05)   # first row wins
    assert np.isnan(hits[1][2])                # a blank change_pct is nan, not 0
