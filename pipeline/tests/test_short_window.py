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

    def test_a_recent_outperformer_reads_leading_on_every_rung(self):
        """The momentum axis is the RS line's SLOPE (first order): a theme
        that is both ahead cumulatively and still gaining reads Leading."""
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

    def test_giving_back_ground_never_reads_leading(self):
        bars = _bars({"SPY": 0.001})
        n = len(bars["SPY"]); idx = bars["SPY"].index
        ramp = np.cumprod(1 + np.linspace(0.008, 0.0005, n))   # slowing down
        for t in ("A", "B", "C"):
            c = 100 * ramp
            bars[t] = pd.DataFrame({"Close": c, "High": c, "Low": c, "Open": c,
                                    "Volume": np.ones(n)}, index=idx)
        traj = SW.build({"Cooling": ["A", "B", "C"]}, bars)["themes"]["Cooling"]
        # Which of the two weak states appears is the LEVEL axis talking; the
        # invariant this test owns is the MOMENTUM axis: a theme losing ground
        # against the benchmark right now may never read Leading or Improving.
        assert set(traj.values()) <= {"Weakening", "Lagging"}, traj
        assert not {"Leading", "Improving"} & set(traj.values()), traj

    def test_a_tie_falls_to_the_weaker_state_not_the_stronger(self):
        """Exactly-flat momentum is float noise, not improvement."""
        assert SW.classify(0.01, 0.0) == "Weakening"
        assert SW.classify(-0.01, 0.0) == "Lagging"

    def test_equal_lookbacks_would_collapse_the_board(self):
        """Level and momentum must read different lookbacks. With L == M they
        are the same number, every theme lands on a diagonal, and the two
        transition quadrants go empty -- measured 31/0/0/25 on real data
        before this was understood. Guard the WINDOWS table itself."""
        for w, (L, M) in SW.WINDOWS.items():
            assert M < L, f"{w}: momentum lookback {M} must be shorter than level {L}"

    def test_shares_carry_their_denominator(self):
        """A count without `measurable` lies the day the theme list changes."""
        bars = _bars({"A": 0.002, "B": 0.002, "C": 0.002, "SPY": 0.001})
        b = SW.board({"T": ["A", "B", "C"]}, bars, window="2w")
        sh = SW.shares(b)
        assert "measurable" in sh.columns
        assert sh["measurable"].iloc[-1] == 1

    def test_a_day_without_bars_is_not_measurable(self):
        """NaN is TRUTHY in Python, so `if v` counted a theme with no bar that
        day as measurable while it contributed to no state. A mid-session run
        on 2026-08-28 had 9 of 56 themes printed and the last row read
        `measurable 56 / 0+0+0+0` -- a fetch artefact wearing the costume of a
        market reading."""
        import pandas as _pd
        b = _pd.DataFrame({"A": ["Leading", None], "B": ["Lagging", float("nan")]},
                          index=_pd.to_datetime(["2026-08-27", "2026-08-28"]))
        sh = SW.shares(b)
        assert sh["measurable"].iloc[0] == 2
        assert sh["measurable"].iloc[1] == 0, "a day nobody printed is not 2 measurable"
        assert sh.iloc[1][["Leading", "Weakening", "Improving", "Lagging"]].sum() == 0

    def test_payload_says_counts_are_not_cross_dashboard_comparable(self):
        """The one sentence that stops the next reader comparing our 20% to
        someone else's 48% as if they measured the same thing."""
        bars = _bars({"A": 0.002, "B": 0.002, "C": 0.002, "SPY": 0.001})
        p = SW.build({"T": ["A", "B", "C"]}, bars)
        assert "not comparable" in p["note"]
        assert p["rungs"]["2w"]["lagging_share"] is not None


class TestFluxSeries:
    """The Rotation page's Flux line and the Terrain card's per-theme history
    ride on the ladder payload (brief §18.22): a relative index per theme on
    one shared calendar, and the two-week state on the same dates as the
    aggregate counts."""

    def _payload(self):
        bars = _bars({"A": 0.002, "B": 0.002, "C": 0.002, "SPY": 0.001})
        return SW.build({"T": ["A", "B", "C"]}, bars), bars

    def test_rel_is_on_the_shared_calendar_and_starts_at_one(self):
        p, bars = self._payload()
        assert len(p["series_dates"]) == SW.FLUX_DAYS + SW.R2W_LAG
        rel = p["series"]["T"]["rel"]
        assert len(rel) == len(p["series_dates"])
        assert rel[0] == 1.0
        # the basket drifts 0.1%/day faster than the benchmark: the index rises
        assert rel[-1] > rel[0]
        assert p["series_dates"][-1] == p["as_of"]

    def test_two_week_strength_from_rel_matches_the_board_axis(self):
        """rel[t]/rel[t-10]-1 is the level axis of the 2w board -- same
        arithmetic, so the line and the counts cannot disagree."""
        p, bars = self._payload()
        rel = p["series"]["T"]["rel"]
        r2w = rel[-1] / rel[-1 - SW.R2W_LAG] - 1
        nav = SW.basket_nav(bars, ["A", "B", "C"]); bench = bars["SPY"]["Close"]
        level = SW._excess(nav, bench, len(nav) - 1, 10)
        # excess of returns vs ratio of indices differ at second order only
        assert abs(r2w - level) < 1e-3

    def test_states_2w_align_with_the_aggregate_history(self):
        p, _ = self._payload()
        h = p["history"]["2w"]
        st = p["series"]["T"]["states_2w"]
        assert len(st) == len(h["dates"])
        assert st[-1] == p["themes"]["T"]["2w"]
        # the counts on the last day are the per-theme states on the last day
        assert sum(1 for s in st[-1:] if s == "Leading") == h["Leading"][-1]


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
