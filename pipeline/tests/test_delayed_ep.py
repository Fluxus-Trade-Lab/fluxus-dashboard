"""Tests for the Delayed Reaction EP classifier (pipeline/tools/delayed_ep_scan.py)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.tools.delayed_ep_scan import classify


def bars(rows):
    """rows: list of (open, high, low, close, volume); dates are business days."""
    idx = pd.bdate_range("2026-07-01", periods=len(rows))
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"], index=idx)


BASE = [(100, 101, 99, 100, 1_000_000)] * 30
EP = (120, 130, 118, 125, 8_000_000)          # gap day: wide range, big volume
EP_DATE = pd.bdate_range("2026-07-01", periods=31)[-1].strftime("%Y-%m-%d")


class TestStages:
    def test_basing_when_held_and_contracting(self):
        post = [(124, 126, 122, 124, 900_000)] * 5           # tight, above EP low, no breakout
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "basing" and d.held and d.contracting and not d.breakout
        assert d.days_since == 5

    def test_breaking_when_today_clears_the_post_ep_high_on_volume(self):
        post = [(124, 126, 122, 124, 900_000)] * 4 + [(125, 132, 124, 131, 2_500_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "breaking" and d.breakout
        assert d.base_high == 126

    def test_failed_when_the_ep_low_is_undercut(self):
        post = [(124, 126, 122, 124, 900_000)] * 3 + [(121, 122, 117, 118, 1_200_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "failed" and not d.held

    def test_drifting_when_held_but_still_wide(self):
        post = [(124, 131, 119, 125, 3_000_000)] * 5        # wide bars, no contraction
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.stage == "drifting"

    def test_breakout_needs_a_green_close_and_volume(self):
        # closes above base high but red (open > close) -> not a breakout
        post = [(124, 126, 122, 124, 900_000)] * 4 + [(133, 134, 126, 127, 2_500_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert not d.breakout
        # green above base high but on dead volume -> not a breakout
        post = [(124, 126, 122, 124, 900_000)] * 4 + [(125, 132, 124, 131, 200_000)]
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert not d.breakout

    def test_near_flag_and_vs_ep_close(self):
        post = [(124, 126, 122, 124, 900_000)] * 5
        d = classify(bars(BASE + [EP] + post), EP_DATE)
        assert d.vs_ep_close_pct == pytest.approx(124 / 125 - 1)
        assert d.near is True

    def test_ep_day_must_be_in_bars_and_not_last(self):
        assert classify(bars(BASE), EP_DATE) is None
        assert classify(bars(BASE + [EP]), EP_DATE) is None
