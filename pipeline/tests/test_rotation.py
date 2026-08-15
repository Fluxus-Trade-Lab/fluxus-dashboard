"""Tests for the rotation engine: disjoint buckets, two horizons, the sentence."""

from __future__ import annotations

import pytest

from pipeline.rotation import baskets as B
from pipeline.rotation import engine as E


def series(*, n: int = 200, daily: float = 0.0) -> list[float]:
    """Geometric series of `n` closes compounding at `daily`."""
    out, px = [], 100.0
    for _ in range(n):
        out.append(px)
        px *= 1.0 + daily
    return out


def bumped(base: list[float], start: int, end: int, total: float) -> list[float]:
    """Copy of `base` whose return from index `start` to index `end` is `total`.

    Index-to-index, matching `_ret(closes, end, span)`, which measures from
    `end - span` to `end`. An off-by-one here silently shortens the window and
    makes a window assertion pass against the wrong span.
    """
    out = list(base)
    step = (1.0 + total) ** (1.0 / (end - start))
    for i in range(start + 1, len(out)):
        out[i] *= step ** (min(i, end) - start)
    return out


FLAT = series()


class TestBuckets:
    def test_anchors_are_one_step_apart_and_end_on_the_last_bar(self):
        a = E.anchors(200)
        assert a[-1] == 199
        assert all(b - a == E.STEP for a, b in zip(a, a[1:]))
        assert len(a) == E.STEPS

    def test_line_buckets_are_disjoint_not_cumulative(self):
        """A move confined to the oldest bucket must not appear in later ones."""
        oldest = E.anchors(200)[0]
        basket = bumped(FLAT, oldest - E.STEP, oldest, 0.10)
        line = E.line_series(basket, FLAT)
        assert line[0] == pytest.approx(0.10, abs=1e-9)
        assert all(v == pytest.approx(0.0, abs=1e-9) for v in line[1:])

    def test_excess_is_against_the_benchmark_not_absolute(self):
        bench = series(daily=0.001)
        basket = series(daily=0.001)
        assert E.line_series(basket, bench) == pytest.approx([0.0] * E.STEPS, abs=1e-9)

    def test_short_history_yields_none_not_zero(self):
        short = series(n=E.STEP * E.STEPS)
        assert E.line_series(short, short)[0] is None


class TestStateWindows:
    def test_the_near_window_is_longer_than_the_drawing_grid(self):
        """The design's central compromise, asserted directly: the ribbon is
        drawn on a fortnight grid, but the near window a state is computed from
        must stay month-scale. Every scheme with a near bucket of two weeks or
        less flipped sign between half samples (FOUR_STATE_DESIGN.md, section
        6), so shrinking NEAR toward STEP is the specific regression to catch."""
        assert E.NEAR > 2 * E.STEP
        assert E.LEVEL >= 3 * E.NEAR - 3

    def test_level_is_the_cumulative_three_month_excess(self):
        basket = bumped(FLAT, 199 - E.LEVEL, 199, 0.12)
        assert E.state_at(basket, FLAT, 199)["level"] == pytest.approx(0.12, abs=1e-6)

    def test_accel_is_the_last_month_against_the_two_before_it(self):
        """A move confined to the 1m..3m stretch is prior-bucket strength, so
        acceleration must come out negative even though the level is positive."""
        basket = bumped(FLAT, 199 - E.LEVEL, 199 - E.NEAR, 0.10)
        s = E.state_at(basket, FLAT, 199)
        assert s["level"] == pytest.approx(0.10, abs=1e-6)
        assert s["accel"] == pytest.approx(-0.10, abs=1e-6)

    def test_a_fading_leader_reads_weakening(self):
        # Strong over three months, flat in the last one.
        basket = bumped(FLAT, 199 - E.LEVEL, 199 - E.NEAR, 0.30)
        assert E.state_at(basket, FLAT, 199)["state"] == "Weakening"

    def test_ribbon_has_one_state_per_step(self):
        r = E.ribbon(FLAT, FLAT)
        assert len(r) == E.STEPS
        assert all(set(s) == {"state", "level", "accel"} for s in r)


class TestCutReading:
    def _closes(self, long_extra: float, month_extra: float = 0.0):
        n = 200
        base = series(n=n)
        last = n - 1
        long_leg = bumped(base, last - E.STEP, last, long_extra)
        if month_extra:
            long_leg = bumped(long_leg, last - E.NEAR, last - E.STEP, month_extra)
        return {"SPY": base, "L": long_leg, "S": base}

    CUT = {"key": "k", "label": "Test cut", "question": "q",
           "long": ["L"], "short": ["S"]}

    def test_positive_spread_votes_risk_on(self):
        c = self._closes(0.05)
        r = E.cut_reading(c, c["SPY"], self.CUT)
        assert r["vote"] == "risk_on"
        assert r["spread"] == pytest.approx(0.05, abs=1e-6)

    def test_month_horizon_can_disagree_with_the_fortnight(self):
        """The turn case: up hard in the last fortnight, down over the month."""
        c = self._closes(0.05, month_extra=-0.12)
        r = E.cut_reading(c, c["SPY"], self.CUT)
        assert r["vote"] == "risk_on"
        assert r["month_vote"] == "risk_off"

    def test_delta_measures_the_change_between_fortnights(self):
        c = self._closes(0.05)
        r = E.cut_reading(c, c["SPY"], self.CUT)
        assert r["delta"] == pytest.approx(0.05, abs=1e-6)

    def test_a_missing_leg_does_not_silently_halve_the_cut(self):
        """A cut whose short side is absent must not vote on its long leg
        alone -- that would read as agreement between sides that were never
        compared."""
        c = self._closes(0.05)
        del c["S"]
        r = E.cut_reading(c, c["SPY"], self.CUT)
        assert r["spread"] is None and r["vote"] is None


class TestVerdict:
    def _r(self, vote, month_vote, spread=0.01):
        return {"key": "k", "label": "Cut", "vote": vote,
                "month_vote": month_vote, "spread": spread}

    def test_unanimous_and_confirmed_is_a_regime(self):
        v = E.verdict([self._r("risk_on", "risk_on")] * 3)
        assert v["call"] == "risk_on" and v["phase"] == "established"
        assert "all 3 agree" in v["sentence"] and "the regime" in v["sentence"]

    def test_fortnight_ahead_of_the_month_is_a_turn(self):
        v = E.verdict([self._r("risk_on", "risk_off")] * 3)
        assert v["phase"] == "turning"
        assert "not yet a regime" in v["sentence"]

    def test_disagreeing_cuts_make_no_call(self):
        v = E.verdict([self._r("risk_on", "risk_on"), self._r("risk_off", "risk_off")])
        assert v["call"] is None and v["phase"] == "split"

    def test_majority_is_reported_as_a_count_not_a_confidence(self):
        v = E.verdict([self._r("risk_on", "risk_on"), self._r("risk_on", "risk_on"),
                       self._r("risk_off", "risk_off")])
        assert v["agree"] == 2 and v["of"] == 3
        assert "2 of 3" in v["sentence"]

    def test_magnitude_reaches_the_sentence(self):
        v = E.verdict([self._r("risk_on", "risk_on", 0.001),
                       self._r("risk_on", "risk_on", 0.067)])
        assert "+6.7pp" in v["sentence"]

    def test_no_votes_says_so_rather_than_guessing(self):
        v = E.verdict([self._r(None, None, None)])
        assert v["call"] is None and "not enough history" in v["sentence"]


class TestBasketTaxonomy:
    def test_every_cut_leg_is_a_known_basket(self):
        for cut in B.CUTS:
            for leg in (*cut["long"], *cut["short"]):
                assert leg in B.BASKETS, leg

    def test_cuts_are_long_risk_on_and_short_risk_off(self):
        """A cut whose sides sit on the same end of the axis is not a cut."""
        for cut in B.CUTS:
            assert all(B.BASKETS[t]["side"] == B.RISK_ON for t in cut["long"]), cut["key"]
            assert all(B.BASKETS[t]["side"] == B.RISK_OFF for t in cut["short"]), cut["key"]

    def test_required_covers_the_benchmark_and_every_basket(self):
        assert B.BENCHMARK in B.REQUIRED
        assert set(B.BASKETS) <= set(B.REQUIRED)


class TestFetchNeverReplacesBetterWithWorse:
    """A throttled batch returns a PARTIAL series, and overwriting turned a
    complete file into a holey one — SPLV lost three mid-July sessions Yahoo
    has, align refused the file, and the volatility cut silently lost its
    vote. Fresh-but-holey must lose to stale-but-complete."""

    def _bars(self, n):
        return [{"date": f"2026-01-{i+1:02d}", "close": 100.0 + i} for i in range(n)]

    def test_sparser_fetch_keeps_the_stored_file(self, tmp_path, monkeypatch):
        import json as J
        from pipeline.rotation import fetch_baskets as FB
        stored = tmp_path / "SPY.json"
        stored.write_text(J.dumps({"ticker": "SPY", "bars": self._bars(10)}))

        import pandas as pd
        idx = pd.to_datetime([f"2026-01-{i+1:02d}" for i in range(6)])
        frame = pd.DataFrame({"Close": [100.0 + i for i in range(6)]}, index=idx)

        class FakeData(dict):
            def __getitem__(self, k): return frame
        monkeypatch.setattr(FB, "required_tickers", lambda: ["SPY"])
        monkeypatch.setattr(FB.yf, "download",
                            lambda *a, **k: FakeData())
        out = FB.fetch(out_dir=tmp_path)
        kept = J.loads(stored.read_text())["bars"]
        assert len(kept) == 10, "a 6-bar partial response overwrote a 10-bar file"
        assert out["failed"] == 1

    def test_equal_or_longer_fetch_replaces(self, tmp_path, monkeypatch):
        import json as J
        from pipeline.rotation import fetch_baskets as FB
        stored = tmp_path / "SPY.json"
        stored.write_text(J.dumps({"ticker": "SPY", "bars": self._bars(6)}))

        import pandas as pd
        idx = pd.to_datetime([f"2026-01-{i+1:02d}" for i in range(10)])
        frame = pd.DataFrame({"Close": [200.0 + i for i in range(10)]}, index=idx)

        class FakeData(dict):
            def __getitem__(self, k): return frame
        monkeypatch.setattr(FB, "required_tickers", lambda: ["SPY"])
        monkeypatch.setattr(FB.yf, "download", lambda *a, **k: FakeData())
        FB.fetch(out_dir=tmp_path)
        kept = J.loads(stored.read_text())["bars"]
        assert len(kept) == 10 and kept[0]["close"] == 200.0
