"""Asset-layer signals: same definitions as the stock enrichment."""
import numpy as np
import pandas as pd

from pipeline.screeners import asset_signals as A


def _hist(closes, vols=None):
    idx = pd.bdate_range("2026-01-02", periods=len(closes))
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"Open": c.shift(1).bfill(), "High": c * 1.01, "Low": c * 0.99,
                         "Close": c, "Volume": pd.Series(vols if vols is not None else [1e6] * len(c), index=idx)})


def test_compute_row_signals():
    up = list(np.linspace(100, 90, 60)) + list(np.linspace(90, 130, 40))   # dip then rally
    spy = pd.Series(np.linspace(100, 110, 100), index=pd.bdate_range("2026-01-02", periods=100))
    r = A.compute_row("GLD", _hist(up), spy)
    assert r["ticker"] == "GLD" and r["category"] == "metals"
    assert r["hi20"] is True and r["rs_line_pctl_21"] == 100.0
    assert r["cross_ema21_up"] is False        # crossed long ago, not today
    assert r["atr_from_sma50"] is not None and r["sma50_dist"] > 0


def test_spy_has_no_rs_line_and_short_history_returns_none():
    spy_hist = _hist(list(np.linspace(100, 120, 100)))
    r = A.compute_row("SPY", spy_hist, spy_hist["Close"])
    assert r["rs_line_pctl_21"] is None
    assert A.compute_row("GLD", _hist([1, 2, 3]), None) is None


def test_build_and_archive_idempotent(tmp_path):
    h = _hist(list(np.linspace(50, 80, 120)))
    payload = A.build({"SPY": h, "GLD": h, "IBIT": h}, "2026-08-19")
    assert payload["count"] == 3 and {r["ticker"] for r in payload["rows"]} == {"SPY", "GLD", "IBIT"}
    p = tmp_path / "a.csv"
    assert A.archive(payload, path=p) == 3
    A.archive(payload, path=p)                       # same date -> replace
    import csv
    assert len(list(csv.DictReader(p.open()))) == 3
    payload2 = dict(payload, date="2026-08-20")
    A.archive(payload2, path=p)
    assert len(list(csv.DictReader(p.open()))) == 6
