"""Corruption in the middle of a bar history, which the endpoint check misses.

`bar_consistency` compared only the NEWEST close against the vendor's. MNST on
2026-09-03 passed it: its newest bar agreed with Finviz while its history
oscillated between ~$48 and ~$94 (2026-07-30 closed 97.65, 07-31 closed 48.19,
08-03 closed 93.55) -- identical in the adjusted and unadjusted feeds, so the
usual adjusted-vs-unadjusted check could not see it either. Three names in a
5,630-row universe carried the flag, and MNST's ATR read 13.22% against a true
intraday 2.37%.

The middle of the series feeds every rolling column: ATR, all moving averages,
52-week extremes, perf_1m/3m/6m, the self-percentiles. So the guard has to
look at the whole history, not its last point.
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.adapters.yfinance_adapter import scale_jumps, bar_consistency


def frame(closes, band=0.01):
    c = np.asarray(closes, dtype=float)
    return pd.DataFrame({"Close": c, "High": c * (1 + band), "Low": c * (1 - band)},
                        index=pd.date_range("2026-06-01", periods=len(c), freq="B"))


# The bars as Yahoo served them on 2026-09-04, recorded before the vendor
# repaired the series. Kept as a fixture because THE POSITIVE CONTROL IS GONE
# FROM LIVE DATA: re-pulled on 2026-09-05, MNST comes back clean (2026-07-30
# closes 48.83, not 97.65; 08-03 closes 46.78, not 93.55). The corruption was
# real and is in the 09-04 report, but it is no longer reproducible from the
# vendor, so this file is the only place the guard can still be shown to fire
# on observed data rather than on a shape we invented.
#
# That the feed healed itself overnight is the argument for the guard, not
# against it: for at least one session every rolling column on this name was
# computed on those numbers and nothing said a word.
MNST_2026_09_04 = [
    # date          close
    ("2026-07-20", 47.72), ("2026-07-21", 47.23), ("2026-07-22", 47.83),
    ("2026-07-23", 93.56), ("2026-07-24", 93.49), ("2026-07-27", 95.33),
    ("2026-07-28", 97.74), ("2026-07-29", 97.23), ("2026-07-30", 97.65),
    ("2026-07-31", 48.19), ("2026-08-03", 93.55), ("2026-08-04", 94.18),
]


class TestItSeesTheShapeThatGotThrough:
    def test_the_recorded_mnst_history_is_caught(self):
        """The observed 2026-09-04 bars, not a shape we made up."""
        f = frame([c for _, c in MNST_2026_09_04])
        assert scale_jumps(f) >= 3

    def test_the_repaired_mnst_history_is_clean(self):
        """The same window after the vendor fixed it, re-pulled 2026-09-05.

        Pins the other direction: the guard must not fire on the corrected
        series, or it would null a healthy name every night.
        """
        repaired = [47.72, 47.23, 47.83, 46.78, 46.74, 47.67,
                    48.87, 48.62, 48.83, 48.19, 46.78, 47.09]
        assert scale_jumps(frame(repaired)) == 0

    def test_a_genuine_split_is_not_corruption(self):
        """Negative control. A real 2:1 moves the level ONCE and stays.

        If this ever fails the guard has become a split detector and would
        null every legitimately split stock's rolling columns.
        """
        f = frame([100, 101, 99, 50.2, 50.5, 49.8, 51, 50.4, 50.9, 51.2])
        assert scale_jumps(f) == 1

    def test_ordinary_history_is_clean(self):
        assert scale_jumps(frame([100, 101, 102, 101, 103, 104, 103, 105])) == 0

    def test_a_real_100_percent_gap_does_not_count(self):
        """A biotech that truly doubles trades through the move.

        The day's own range spans it, so the ratio being near 2.0 is not
        enough on its own -- that second condition is what separates a real
        gap from a half-adjusted bar.
        """
        c = [10.0, 10.1, 20.4, 20.6, 20.2]
        f = pd.DataFrame({
            "Close": c,
            # the doubling day traded from near yesterday's close up to 20.4
            "High": [10.1, 10.2, 20.8, 20.9, 20.5],
            "Low":  [9.9, 10.0, 10.05, 20.1, 19.9],
        }, index=pd.date_range("2026-06-01", periods=5, freq="B"))
        assert scale_jumps(f) == 0


class TestWiring:
    """The scan has to reach the verdict, not just exist. 2026-08-31's lesson:
    a guard that nothing calls reports nothing."""

    def _hist(self, closes, last_date="2026-09-03"):
        f = frame(closes)
        f.index = pd.date_range(end=pd.Timestamp(last_date), periods=len(closes), freq="B")
        return f

    def test_a_clean_history_whose_endpoint_agrees_is_ok(self):
        h = self._hist([100, 101, 102, 101, 103])
        status, _ = bar_consistency(h, pd.Timestamp("2026-09-03").date(), 103.0)
        assert status == "ok"

    def test_a_corrupt_history_whose_endpoint_agrees_is_flagged(self):
        """Exactly MNST: the last bar matches the vendor, the middle does not."""
        closes = [c for _, c in MNST_2026_09_04] + [44.08]
        h = self._hist(closes)
        status, _ = bar_consistency(h, pd.Timestamp("2026-09-03").date(), 44.08)
        assert status == "scale_history", (
            "the endpoint check passed it -- the history scan did not run")

    def test_stale_still_wins(self):
        """Order matters: a missing newest bar is the more urgent verdict."""
        h = self._hist([47.7, 93.6, 48.2, 93.5], last_date="2026-08-20")
        status, _ = bar_consistency(h, pd.Timestamp("2026-09-03").date(), 93.5)
        assert status == "stale"
