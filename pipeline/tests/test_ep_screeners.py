"""Episodic Pivot, two authors, two screeners (Andy 2026-09-18: 「12 注册 EP
Stockbee和 EP Qullamaggie 然后我们以后可以测试下」).

Stockbee, "My process flow for Episodic Pivots (EP)", 2014-07
(https://stockbee.blogspot.com/2014/07/my-process-flow-for-episodic-pivots-ep.html):
    "Run EP scan c/c1>1.04 and v>3*avgv50.1 and v>=300000"
Qullamaggie, "How to master a setup: Episodic Pivots"
(https://qullamaggie.com/how-to-master-a-setup-episodic-pivots/):
    "a gap up of 10% or more" ... "massive volume near the open, ideally the
    stock should trade the average daily volume the first 15-20 minutes"

The retired `episodic_pivot` (close +10%, rel_volume 3, cap $500M) matched
neither; its module is gone and nothing registers it any more.
"""
import numpy as np
import pandas as pd
import pytest

from pipeline.screeners import ep_qullamaggie, ep_stockbee


def _u(**cols):
    base = {"ticker": ["A"], "sector": ["Technology"], "market_cap": [2e9],
            "change_pct": [0.05], "volume": [1_000_000.0], "avg_vol50_prev": [200_000.0],
            "gap_pct": [0.12], "rel_volume": [5.0]}
    base.update({k: [v] for k, v in cols.items()})
    return pd.DataFrame(base)


# ── Stockbee: c/c1>1.04 and v>3*avgv50.1 and v>=300000 ──────────────────
class TestStockbee:
    def test_positive_all_three_legs(self):
        assert ep_stockbee.run(_u())["count"] == 1

    def test_c_over_c1_is_strictly_above_1_04(self):
        assert ep_stockbee.run(_u(change_pct=0.04))["count"] == 0
        assert ep_stockbee.run(_u(change_pct=0.0401))["count"] == 1

    def test_volume_is_strictly_above_three_times_yesterdays_avg50(self):
        assert ep_stockbee.run(_u(volume=600_000.0))["count"] == 0      # = 3x
        assert ep_stockbee.run(_u(volume=600_001.0))["count"] == 1

    def test_absolute_volume_floor_300k_inclusive(self):
        assert ep_stockbee.run(_u(volume=299_999.0, avg_vol50_prev=50_000.0))["count"] == 0
        assert ep_stockbee.run(_u(volume=300_000.0, avg_vol50_prev=50_000.0))["count"] == 1

    def test_no_market_cap_floor_in_the_original(self):
        # the retired recipe's $500M floor is not in Stockbee's scan
        assert ep_stockbee.run(_u(market_cap=1e8))["count"] == 1

    def test_unmeasured_average_never_fires(self):
        assert ep_stockbee.run(_u(avg_vol50_prev=None))["count"] == 0

    def test_old_recipe_is_not_what_fires(self):
        # +10% close on rel_volume 3 but only 2x the 50-day average: old EP yes, Stockbee no
        assert ep_stockbee.run(_u(change_pct=0.10, rel_volume=3.0, volume=400_000.0))["count"] == 0


# ── Qullamaggie: gap >= 10%, volume >= ADV on the day (necessary) ───────
class TestQullamaggie:
    def test_positive_gap_on_volume(self):
        out = ep_qullamaggie.run(_u())
        assert out["count"] == 1
        assert out["tickers"][0]["gap_pct"] == pytest.approx(0.12)

    def test_gap_is_open_vs_prior_close_not_close_vs_close(self):
        # closed +15% but opened only +5%: a rally, not a gap
        assert ep_qullamaggie.run(_u(change_pct=0.15, gap_pct=0.05))["count"] == 0

    def test_gap_ten_percent_inclusive(self):
        assert ep_qullamaggie.run(_u(gap_pct=0.10))["count"] == 1
        assert ep_qullamaggie.run(_u(gap_pct=0.0999))["count"] == 0

    def test_day_volume_below_one_adv_cannot_be_his_ep(self):
        # "trade the average daily volume the first 15-20 minutes" => the day's
        # volume is at least one ADV; below that the leg is failed, not unknown
        assert ep_qullamaggie.run(_u(volume=150_000.0))["count"] == 0

    def test_missing_gap_never_fires(self):
        assert ep_qullamaggie.run(_u(gap_pct=None))["count"] == 0

    def test_payload_says_what_it_cannot_measure(self):
        out = ep_qullamaggie.run(_u())
        assert "first 15-20 minutes" in out["unmeasured"]


# ── the fields both need come from the daily bars we already fetch ──────
def test_avg_vol50_prev_is_the_fifty_bars_before_today():
    from pipeline.adapters.yfinance_adapter import stockbee_ratios
    v = [1_000.0] * 10 + [100.0] * 50 + [9_999_999.0]        # today excluded
    hist = pd.DataFrame({"Close": np.linspace(1, 2, len(v)), "Low": 1.0, "Volume": v})
    assert stockbee_ratios(hist)["avg_vol50_prev"] == pytest.approx(100.0)


def test_avg_vol50_prev_null_under_51_bars():
    from pipeline.adapters.yfinance_adapter import stockbee_ratios
    hist = pd.DataFrame({"Close": [1.0] * 50, "Low": 1.0, "Volume": [1.0] * 50})
    assert stockbee_ratios(hist)["avg_vol50_prev"] is None


def test_retired_rows_replay_only_up_to_their_last_session():
    """History is not rewritten: a backfill replay still mines the retired
    screener's own days (positive), and never mines the compatibility file
    that carries the NEW union under the old name afterwards (negative)."""
    from pipeline.screeners.ticker_events import extract_events
    payload = {"tickers": [{"ticker": "OLD", "change_pct": 0.2, "rel_volume": 4.0}]}
    assert len(extract_events("episodic_pivot", payload, "2026-09-17")) == 1
    assert extract_events("episodic_pivot", payload, "2026-09-18") == []


def test_compat_file_is_the_union_in_the_old_shape():
    from pipeline.screeners.run_all import ep_compat_payload
    res = {"ep_stockbee": {"tickers": [{"ticker": "A", "change_pct": 0.05, "rel_volume": 4.0,
                                        "market_cap": 1e9, "sector": "X", "atr_ext": 1.0,
                                        "atr_color": "green"}]},
           "ep_qullamaggie": {"tickers": [{"ticker": "A", "change_pct": 0.05},
                                          {"ticker": "B", "change_pct": 0.30}]}}
    out = ep_compat_payload(res)
    assert out["count"] == 2 and [r["ticker"] for r in out["tickers"]] == ["B", "A"]
    a = out["tickers"][1]
    assert a["sources"] == ["ep_stockbee", "ep_qullamaggie"]
    assert {"ticker", "change_pct", "rel_volume", "market_cap", "sector", "atr_ext", "atr_color"} <= set(a)
    assert out["superseded_by"] == ["ep_stockbee", "ep_qullamaggie"]


def test_retired_episodic_pivot_is_not_registered():
    import importlib.util
    assert importlib.util.find_spec("pipeline.screeners.episodic_pivot") is None
    from pipeline.screeners.ticker_events import SCREENER_FILES
    assert "episodic_pivot" not in SCREENER_FILES
    assert SCREENER_FILES["ep_stockbee"] == "tickers"
    assert SCREENER_FILES["ep_qullamaggie"] == "tickers"
