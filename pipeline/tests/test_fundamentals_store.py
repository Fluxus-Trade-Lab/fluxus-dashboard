"""F score source switch (2026-08-17): yfinance primary, Finviz backup, rolling refresh."""
from __future__ import annotations

import pandas as pd
import pytest

from pipeline.adapters import fundamentals_store as FS


class TestMapInfo:
    def test_eps_next_is_forward_over_trailing_only_for_earners(self):
        assert FS.map_info({"forwardEps": 12.0, "trailingEps": 10.0, "revenueGrowth": 0.3})["eps_growth_next_y"] == pytest.approx(0.2)
        assert FS.map_info({"forwardEps": 1.0, "trailingEps": -0.5})["eps_growth_next_y"] is None
        assert FS.map_info({"forwardEps": 1.0})["eps_growth_next_y"] is None

    def test_missing_and_nan_are_none(self):
        m = FS.map_info({"revenueGrowth": float("nan"), "earningsGrowth": "x"})
        assert m == {"eps_growth_next_y": None, "revenue_growth": None, "eps_growth_this_y": None}


class TestRefresh:
    def test_oldest_first_and_budget(self):
        store = {"A": {"asof": "2026-08-01"}, "B": {"asof": "2026-08-10"}, "C": {"last_attempt": "2026-08-05"}}
        assert FS.pick_due(store, ["A", "B", "C", "D"], budget=2) == ["D", "A"]

    def test_refresh_keeps_old_reading_on_failure_and_marks_attempt(self):
        store = {"A": {"eps_growth_next_y": 0.1, "revenue_growth": 0.2, "eps_growth_this_y": None,
                       "asof": "2026-08-01", "source": "yfinance"}}
        def fetch(t):
            if t == "A":
                raise RuntimeError("429")
            return {"eps_growth_next_y": 0.5, "revenue_growth": 0.4, "eps_growth_this_y": 0.3}
        out = FS.refresh(store, ["A", "B"], fetch=fetch, workers=1, asof="2026-08-17")
        assert out == {"due": 2, "ok": 1, "failed": 1, "walled": False,
                       "retries": 0, "store": 2}
        assert store["A"]["eps_growth_next_y"] == 0.1 and store["A"]["last_attempt"] == "2026-08-17"
        assert store["B"]["asof"] == "2026-08-17" and store["B"]["revenue_growth"] == 0.4
        # the failed one now sorts behind the fresh one? no -- behind nothing, but ahead of B
        assert FS.pick_due(store, ["A", "B"], budget=1) == ["A"]

    def test_stops_after_a_wall_of_failures(self, monkeypatch):
        monkeypatch.setattr(FS, "MAX_CONSECUTIVE_FAILURES", 3)
        calls = []
        def fetch(t):
            calls.append(t)
            return None
        store = {}
        out = FS.refresh(store, [f"T{i}" for i in range(20)], fetch=fetch, workers=1, asof="2026-08-17")
        assert out["ok"] == 0 and 3 <= out["failed"] <= 20 and out["walled"]
        # wall victims are NOT stamped: they stay at the front of the queue
        assert store == {}


class TestApply:
    def test_yfinance_first_finviz_backup(self):
        u = pd.DataFrame([
            {"ticker": "A", "eps_growth_next_y": 0.05, "revenue_growth": 0.06},   # both sources
            {"ticker": "B", "eps_growth_next_y": 0.07, "revenue_growth": None},   # finviz only
            {"ticker": "C", "eps_growth_next_y": None, "revenue_growth": None},   # yfinance only
            {"ticker": "D", "eps_growth_next_y": None, "revenue_growth": None},   # neither
        ])
        store = {"A": {"eps_growth_next_y": 0.5, "revenue_growth": None, "eps_growth_this_y": 0.1, "asof": "2026-08-17"},
                 "C": {"eps_growth_next_y": None, "revenue_growth": 0.9, "eps_growth_this_y": None, "asof": "2026-08-16"},
                 "D": {"last_attempt": "2026-08-17"}}
        out = FS.apply(u, store).set_index("ticker")
        assert out.loc["A", "eps_growth_next_y"] == 0.5          # yfinance wins
        assert out.loc["A", "revenue_growth"] == 0.06            # finviz fills the hole
        assert out.loc["A", "fund_source"] == "yfinance"
        assert out.loc["B", "fund_source"] == "finviz" and out.loc["B", "eps_growth_next_y"] == 0.07
        assert out.loc["C", "fund_source"] == "yfinance" and out.loc["C", "revenue_growth"] == 0.9
        assert pd.isna(out.loc["D", "fund_source"]) and pd.isna(out.loc["D", "revenue_growth"])
        assert out.loc["C", "fund_asof"] == "2026-08-16"

    def test_works_when_finviz_columns_are_absent(self):
        u = pd.DataFrame([{"ticker": "A"}, {"ticker": "B"}])
        out = FS.apply(u, {"A": {"revenue_growth": 0.2, "asof": "2026-08-17"}}).set_index("ticker")
        assert out.loc["A", "revenue_growth"] == 0.2 and pd.isna(out.loc["B", "fund_source"])


class TestWallRetry:
    """A rate-limit wall is transient, not a verdict.

    2026-08-27 the nightly run hit one, gave up with partial coverage, and the
    L2 ledger guard turned that into a blocked publish -- the whole night's
    data never shipped. A manual rerun 40 minutes later got 400/400, which is
    the evidence that one cooldown was all it needed.
    """

    def _fetcher(self, wall_after, recover=True):
        """Fails every call after `wall_after` successes, until retried."""
        state = {"n": 0, "pass_no": 0, "seen": set()}

        def fetch(t):
            state["n"] += 1
            if t in state["seen"] and recover:
                return {"eps_growth_next_y": 1.0}     # second pass succeeds
            state["seen"].add(t)
            if state["n"] > wall_after:
                return None
            return {"eps_growth_next_y": 1.0}
        return fetch, state

    def test_cooldown_retry_recovers_the_night(self, monkeypatch):
        import pipeline.adapters.fundamentals_store as F
        monkeypatch.setattr(F, "WALL_COOLDOWN_S", 0)      # no real sleeping
        fetch, _ = self._fetcher(wall_after=5)
        store = {}
        names = [f"T{i}" for i in range(60)]
        r = F.refresh(store, names, budget=60, fetch=fetch, workers=1)
        assert r["retries"] == 1, "a wall must buy one cooldown, not zero"
        assert r["ok"] > 5, f"the retry recovered nothing: {r}"

    def test_a_persistent_wall_is_still_reported(self, monkeypatch):
        """One retry, not a loop: if it walls again the limit is real."""
        import pipeline.adapters.fundamentals_store as F
        monkeypatch.setattr(F, "WALL_COOLDOWN_S", 0)
        fetch, _ = self._fetcher(wall_after=2, recover=False)
        r = F.refresh({}, [f"T{i}" for i in range(120)], budget=120, fetch=fetch, workers=1)
        assert r["walled"] is True
        assert r["retries"] == F.WALL_RETRIES

    def test_clean_run_uses_no_retry(self, monkeypatch):
        import pipeline.adapters.fundamentals_store as F
        r = F.refresh({}, ["A", "B", "C"], budget=10,
                      fetch=lambda t: {"eps_growth_next_y": 1.0}, workers=1)
        assert r["walled"] is False and r["retries"] == 0 and r["ok"] == 3
