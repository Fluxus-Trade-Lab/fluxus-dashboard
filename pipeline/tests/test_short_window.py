"""Five-rung theme ladder -- the short-window sensitivity (2026-08-28).

Andy wants the 2W..10W trajectory Clement_Ang17's board plots, as a canary:
"lagging 的开始更加多，这个是最重要的特征". These lock the SHAPE. The canary
CLAIM is deliberately not asserted here -- it is registered as underpowered
(claims.jsonl: canary-lagging-share) and a test that pinned it would be
pinning a number the evidence does not support.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.themes import short_window as SW


def _bars(spec, n=200, start="2025-01-01"):
    """spec: {ticker: daily_drift} -> deterministic bar frames."""
    idx = pd.bdate_range(start, periods=n)
    out = {}
    for t, drift in spec.items():
        c = 100 * np.cumprod(np.repeat(1 + drift, n))
        out[t] = pd.DataFrame({"Close": c, "High": c, "Low": c, "Open": c,
                               "Volume": np.ones(n)}, index=idx)
    return out


class TestClassify:
    def test_four_quadrants(self):
        assert SW.classify(0.01, 0.01) == "Leading"
        assert SW.classify(0.01, -0.01) == "Weakening"
        assert SW.classify(-0.01, 0.01) == "Improving"
        assert SW.classify(-0.01, -0.01) == "Lagging"

    def test_unmeasurable_is_none_not_lagging(self):
        """A missing reading must not be filed as the worst state -- that is
        how an outage becomes a market call."""
        assert SW.classify(np.nan, 0.01) is None
        assert SW.classify(0.01, np.nan) is None


class TestBasket:
    def test_equal_weighted_not_price_weighted(self):
        """A theme is a claim about its members, not about its priciest one.

        The basket rebalances daily to equal weight, so its daily return is the
        MEAN of the members' (0.5%/day here) -- not RICH's 0% (which is what a
        price-weighted or index-summed basket would return, RICH being 1000x
        the price)."""
        bars = _bars({"CHEAP": 0.01, "RICH": 0.0})
        bars["RICH"]["Close"] *= 1000
        nav = SW.basket_nav(bars, ["CHEAP", "RICH"], min_names=2)
        n = len(nav) - 1
        expected = 1.005 ** n - 1.0            # mean of +1%/day and 0%/day
        got = nav.iloc[-1] / nav.iloc[0] - 1
        assert got == pytest.approx(expected, rel=1e-6), "not the equal-weight mean"
        assert got > 1.0, "a price-weighted basket would have returned ~0 here"

    def test_too_few_constituents_is_none(self):
        bars = _bars({"A": 0.001, "B": 0.001})
        assert SW.basket_nav(bars, ["A", "B"], min_names=3) is None


class TestLadder:
    def test_all_five_rungs_present_and_ordered(self):
        assert SW.LADDER == ("2w", "4w", "6w", "8w", "10w")
        for w in SW.LADDER:
            assert w in SW.WINDOWS
        lens = [SW.WINDOWS[w][0] for w in SW.LADDER]
        assert lens == sorted(lens), "the ladder must go near -> far"

    def test_an_accelerating_outperformer_reads_leading_on_every_rung(self):
        """The momentum axis means ACCELERATION, not level. A theme pulling
        away faster and faster must read Leading at every lookback."""
        bars = _bars({"SPY": 0.001})
        n = len(bars["SPY"])
        idx = bars["SPY"].index
        ramp = np.cumprod(1 + np.linspace(0.0005, 0.008, n))   # speeding up
        for t in ("A", "B", "C"):
            c = 100 * ramp
            bars[t] = pd.DataFrame({"Close": c, "High": c, "Low": c, "Open": c,
                                    "Volume": np.ones(n)}, index=idx)
        traj = SW.build({"Hot": ["A", "B", "C"]}, bars)["themes"]["Hot"]
        assert set(traj.values()) == {"Leading"}, traj

    def test_a_decelerating_outperformer_reads_weakening(self):
        bars = _bars({"SPY": 0.001})
        n = len(bars["SPY"]); idx = bars["SPY"].index
        ramp = np.cumprod(1 + np.linspace(0.008, 0.0005, n))   # slowing down
        for t in ("A", "B", "C"):
            c = 100 * ramp
            bars[t] = pd.DataFrame({"Close": c, "High": c, "Low": c, "Open": c,
                                    "Volume": np.ones(n)}, index=idx)
        traj = SW.build({"Cooling": ["A", "B", "C"]}, bars)["themes"]["Cooling"]
        # Both deceleration states are correct here and which one appears is
        # the LEVEL axis talking: by the short rungs the ramp has slowed below
        # the benchmark (level < 0 -> Lagging), at the long ones it is still
        # ahead on the cumulative (level > 0 -> Weakening). The invariant this
        # test owns is the MOMENTUM axis: nothing decelerating may read as
        # Leading or Improving on any rung.
        assert set(traj.values()) <= {"Weakening", "Lagging"}, traj
        assert not {"Leading", "Improving"} & set(traj.values()), traj

    def test_a_tie_falls_to_the_weaker_state_not_the_stronger(self):
        """Exactly-flat momentum is float noise, not improvement."""
        assert SW.classify(0.01, 0.0) == "Weakening"
        assert SW.classify(-0.01, 0.0) == "Lagging"

    def test_shares_carry_their_denominator(self):
        """A count without `measurable` lies the day the theme list changes."""
        bars = _bars({"A": 0.002, "B": 0.002, "C": 0.002, "SPY": 0.001})
        b = SW.board({"T": ["A", "B", "C"]}, bars, window="2w")
        sh = SW.shares(b)
        assert "measurable" in sh.columns
        assert sh["measurable"].iloc[-1] == 1

    def test_payload_says_counts_are_not_cross_dashboard_comparable(self):
        """The one sentence that stops the next reader comparing our 20% to
        someone else's 48% as if they measured the same thing."""
        bars = _bars({"A": 0.002, "B": 0.002, "C": 0.002, "SPY": 0.001})
        p = SW.build({"T": ["A", "B", "C"]}, bars)
        assert "not comparable" in p["note"]
        assert p["rungs"]["2w"]["lagging_share"] is not None


class TestArchive:
    def test_rewrites_todays_rows_and_keeps_history(self, tmp_path):
        path = tmp_path / "ladder.csv"
        mk = lambda d, lag: {"as_of": d, "rungs": {
            "2w": {"Leading": 1, "Weakening": 2, "Improving": 3, "Lagging": lag,
                   "measurable": 6 + lag, "lagging_share": 0.1, "lagging_share_d5": 0.0}}}
        SW.archive_ladder(mk("2026-08-27", 4), path)
        SW.archive_ladder(mk("2026-08-28", 5), path)
        n = SW.archive_ladder(mk("2026-08-28", 9), path)     # same day again
        import csv
        rows = list(csv.DictReader(path.open()))
        assert n == len(rows) == 2, "a same-day rerun replaces, never duplicates"
        assert {r["date"] for r in rows} == {"2026-08-27", "2026-08-28"}
        assert [r["Lagging"] for r in rows if r["date"] == "2026-08-28"] == ["9"]
