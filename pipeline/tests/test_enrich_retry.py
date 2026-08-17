"""The enrichment retry: throttled batches get asked again, dead symbols don't.

Yahoo throttles the GitHub runner's shared egress, and when it does the misses
arrive in blocks — whole batches empty, not scattered names. One pass shipped
2.0% missing from a residential IP and 22.4% from CI, and the 22.4% night
took three screeners down at once.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.adapters import yfinance_adapter as YA


def _frame(tickers):
    """A plausible multi-ticker OHLC frame for `tickers`."""
    idx = pd.date_range("2026-01-01", periods=60, freq="B")
    cols = pd.MultiIndex.from_product(
        [tickers, ["Open", "High", "Low", "Close", "Volume"]])
    df = pd.DataFrame(100.0, index=idx, columns=cols)
    for t in tickers:
        df[(t, "Volume")] = 1e6
    return df.swaplevel(axis=1).sort_index(axis=1).swaplevel(axis=1) \
        if False else df


class _ThrottledYahoo:
    """First call per symbol-set fails for `throttled`; retries succeed."""

    def __init__(self, throttled, dead=()):
        self.throttled = set(throttled)
        self.dead = set(dead)
        self.calls = 0

    def download(self, batch, **kw):
        self.calls += 1
        batch = list(batch)
        serve = []
        for t in batch:
            if t in self.dead:
                continue                       # never has data
            if t in self.throttled:
                self.throttled.discard(t)      # fails once, then recovers
                continue
            serve.append(t)
        if not serve:
            return pd.DataFrame()
        return _frame(serve)


class TestEnrichRetry:
    def _run(self, fake, tickers, monkeypatch):
        monkeypatch.setattr(YA, "yf", fake)
        monkeypatch.setattr(YA.time, "sleep", lambda s: None)
        # These fakes are dated 2026-01; the bar-consistency stale retry is
        # a separate concern (TestBarConsistency), so disable it here.
        monkeypatch.setattr(YA, "_expected_session", lambda: None)
        universe = pd.DataFrame({
            "ticker": tickers,
            "sector": "Technology", "industry": "Software",
            "market_cap": 1e9, "close": None, "change_pct": None,
            "volume": None,
        })
        return YA.YfinanceAdapter().enrich_universe(universe, batch_size=4)

    def test_throttled_block_is_recovered_on_retry(self, monkeypatch):
        """A whole batch failing once — the CI signature — must not ship as
        22% missing when the same names answer a minute later."""
        tickers = [f"T{i}" for i in range(12)]
        fake = _ThrottledYahoo(throttled=tickers[:8])
        out = self._run(fake, tickers, monkeypatch)
        assert out["avg_volume"].notna().all(), (
            f"still missing: {out.loc[out.avg_volume.isna(), 'ticker'].tolist()}")

    def test_dead_symbols_do_not_cause_infinite_retries(self, monkeypatch):
        """Delisted names never return data; the loop must stop when a round
        recovers nothing rather than hammering Yahoo forever."""
        tickers = [f"T{i}" for i in range(10)] + ["DEAD1", "DEAD2"]
        fake = _ThrottledYahoo(throttled=(), dead=("DEAD1", "DEAD2"))
        out = self._run(fake, tickers, monkeypatch)
        assert out.loc[out.ticker.str.startswith("T"), "avg_volume"].notna().all()
        assert out.loc[out.ticker.str.startswith("DEAD"), "avg_volume"].isna().all()
        assert fake.calls <= 3 + 4   # first sweep (3 batches) + bounded retries

    def test_a_clean_first_pass_never_retries(self, monkeypatch):
        tickers = [f"T{i}" for i in range(8)]
        fake = _ThrottledYahoo(throttled=())
        self._run(fake, tickers, monkeypatch)
        assert fake.calls == 2       # ceil(8/4) batches, no retry rounds


class TestBarConsistency:
    """A batch download sometimes returns a ticker WITHOUT its newest bar, so
    every bar-derived column (sma*_dist, atr, ema21, vcs, sp_*...) lags the
    Finviz close by a session while looking perfectly populated (FIRY/FBRX,
    3% off on 2026-08-14). And a split can leave yfinance history on the old
    scale while Finviz's close is on the new one (BYND). Neither is visible
    to a null-rate guard. The check compares the newest bar's date with the
    session the run is labelled with, and the newest bar's close with the
    vendor close."""

    def _hist(self, last_date, close=100.0):
        import pandas as pd
        idx = pd.bdate_range(end=last_date, periods=30, tz="America/New_York")
        return pd.DataFrame({"Close": [close] * 30}, index=idx)

    def test_ok_when_bar_matches_session_and_scale(self):
        import datetime as dt
        from pipeline.adapters.yfinance_adapter import bar_consistency
        st, d = bar_consistency(self._hist("2026-08-14"), dt.date(2026, 8, 14), 100.5)
        assert st == "ok" and d == "2026-08-14"

    def test_stale_when_newest_bar_is_before_the_session(self):
        import datetime as dt
        from pipeline.adapters.yfinance_adapter import bar_consistency
        st, d = bar_consistency(self._hist("2026-08-13"), dt.date(2026, 8, 14), 100.0)
        assert st == "stale" and d == "2026-08-13"

    def test_scale_mismatch_when_closes_disagree_by_more_than_20pct(self):
        import datetime as dt
        from pipeline.adapters.yfinance_adapter import bar_consistency
        # yfinance still on pre-split scale ($0.55), Finviz on post-split ($13.47)
        st, _ = bar_consistency(self._hist("2026-08-14", close=0.55), dt.date(2026, 8, 14), 13.47)
        assert st == "scale_mismatch"

    def test_no_vendor_close_skips_the_scale_check(self):
        import datetime as dt
        from pipeline.adapters.yfinance_adapter import bar_consistency
        st, _ = bar_consistency(self._hist("2026-08-14"), dt.date(2026, 8, 14), None)
        assert st == "ok"

    def test_a_bar_dated_after_the_session_is_still_ok(self):
        """A run during a session may see today's partial bar; that is not stale."""
        import datetime as dt
        from pipeline.adapters.yfinance_adapter import bar_consistency
        st, _ = bar_consistency(self._hist("2026-08-17"), dt.date(2026, 8, 14), 100.0)
        assert st == "ok"
