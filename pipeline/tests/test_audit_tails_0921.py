"""2026-09-21 self-made-number audit, small tails (Andy: 「小尾巴也清掉。」).

Each test pins one reading to its original author's text:
  1. Anticipation TI65 / MDT are strict '>' (Stockbee 2016-04 scan text).
  2. Asset-layer high_52w_dist reads the 52-week INTRADAY high, like the
     stock layer (Finviz '52W High'; yfinance fallback hist['High'].max()).
  3. VCP Layer 1 carries Minervini's Trend Template legs that the row can
     measure: 150-day (30-week) MA legs and RS ranking >= 70.
"""
import numpy as np
import pandas as pd

from pipeline.screeners import asset_signals as A
from pipeline.screeners.vcp_detector import layer1_finviz_filter
from pipeline.screeners.watchlist import PANELS


# ---------- 1. Anticipation: strict '>' on TI65 / MDT ----------

def _antic_row(**kw):
    r = {"ti65": 1.0, "c_low52w": 1.0, "mdt": 1.0, "change_pct": 0.0,
         "min_vol_3d_1": 200_000, "vcs": 70, "adr_pct": 4.0}
    r.update(kw)
    return r


def test_anticipation_ti65_boundary_is_strict():
    t = PANELS["anticipation"].test
    assert t(_antic_row(ti65=1.05)) is False          # avgc7/avgc65>1.05
    assert t(_antic_row(ti65=1.0501)) is True


def test_anticipation_mdt_boundary_is_strict():
    t = PANELS["anticipation"].test
    assert t(_antic_row(mdt=1.19)) is False           # c/avgc126>1.19
    assert t(_antic_row(mdt=1.1901)) is True


def test_anticipation_double_trouble_stays_inclusive():
    t = PANELS["anticipation"].test
    assert t(_antic_row(c_low52w=1.8)) is True        # c/minl252>=1.8


# ---------- 2. asset layer 52w high = highest HIGH ----------

def test_asset_high_52w_dist_reads_intraday_high():
    idx = pd.bdate_range("2026-01-02", periods=60)
    c = pd.Series(np.linspace(100, 110, 60), index=idx)
    h = c * 1.01
    h.iloc[30] = 150.0                                 # one intraday spike, close stays tame
    hist = pd.DataFrame({"Open": c, "High": h, "Low": c * 0.99, "Close": c,
                         "Volume": pd.Series([1e6] * 60, index=idx)})
    r = A.compute_row("GLD", hist, None)
    assert r["high_52w_dist"] == round(110.0 / 150.0 - 1, 4)


# ---------- 3. VCP L1 = Minervini Trend Template legs ----------

def _tt_row(**kw):
    # close 100; sma50 ~ 90.9, sma200 ~ 76.9, wk_sma30 (150-day) = 85
    r = {"ticker": "X", "close": 100.0, "market_cap": 5e9,
         "sma50_dist": 0.10, "sma200_dist": 0.30,
         "wk_sma30": 85.0, "wk_sma30_dist": 100.0 / 85.0 - 1,
         "low_52w": 0.50, "high_52w": -0.10, "perf_1w": 0.01, "perf_1m": 0.05,
         "rs_rating": 85}
    r.update(kw)
    return pd.DataFrame([r])


def test_trend_template_passes_when_all_legs_hold():
    assert len(layer1_finviz_filter(_tt_row())) == 1


def test_trend_template_rs_below_70_fails():
    assert len(layer1_finviz_filter(_tt_row(rs_rating=69))) == 0
    assert len(layer1_finviz_filter(_tt_row(rs_rating=70))) == 1   # "no less than 70"


def test_trend_template_price_below_150_fails():
    assert len(layer1_finviz_filter(_tt_row(wk_sma30=105.0, wk_sma30_dist=100.0 / 105.0 - 1))) == 0


def test_trend_template_150_below_200_fails():
    # sma200 ~ 76.9; a 150-day line at 75 is under it
    assert len(layer1_finviz_filter(_tt_row(wk_sma30=75.0, wk_sma30_dist=100.0 / 75.0 - 1))) == 0


def test_trend_template_50_below_150_fails():
    # sma50 ~ 97.1 (dist 0.03), 150-day line at 98 is above it, price still above both
    assert len(layer1_finviz_filter(_tt_row(sma50_dist=0.03, wk_sma30=98.0,
                                            wk_sma30_dist=100.0 / 98.0 - 1))) == 0
