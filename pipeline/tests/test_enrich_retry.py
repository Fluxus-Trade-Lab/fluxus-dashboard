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
