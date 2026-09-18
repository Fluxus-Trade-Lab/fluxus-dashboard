"""Author-named panels and presets follow the author's own text (2026-09-18).

Andy 2026-09-18, verbatim: 「全部按原文，9 用课程版，12 注册 EP Stockbee和 EP
Qullamaggie 然后我们以后可以测试下。」 -- every panel/preset that carries an
author's name, where the author gave an explicit definition that we had
changed, goes back to the author's text. Liquid Leaders (#9) uses Andy's own
course version. Audit: data/research/metric_audit_2026-09-18/C_lists_and_tickers.md.

Each block pins one item with at least one positive and one negative case,
and each was written to FAIL against the code before the change.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.screeners import preset_hits as P
from pipeline.screeners import watchlist as W


def _presets():
    return {p["name"]: p["filters"] for p in P.load_presets()}


def wrow(**kw):
    base = {"ticker": "T", "market_cap": 5e9, "avg_volume": 5e6, "close": 100.0,
            "sector": "Technology", "rs_1m": 90, "adr_pct": 4.5, "trend_base": True,
            "liquid_leader": True, "perf_1w": 0.05, "dcr_pct": 0.5,
            "ema21_atr_dist": 0.5, "atr_from_sma50": 2.0, "sma50_atr_dist": 2.0,
            "sma50_dist": 0.05, "sma200_dist": 0.15, "pp_count_10d": 0,
            "vcs": 65.0, "ti65": 1.06, "c_low52w": 1.2, "mdt": 1.0,
            "change_pct": 0.004, "min_vol_3d": 500_000, "min_vol_3d_1": 500_000}
    base.update(kw)
    return base


# ---------------------------------------------------------------- #8 9M
class TestStockbee9M:
    """stockbee.blogspot.com/2019/09/simple-scan-that-can-make-you-millions.html:
    '9 million breakout PCF / v>=8900000' -- TODAY's volume, nothing else."""

    def test_preset_is_todays_volume_only(self):
        f = _presets()["Stockbee 9M Setup"]
        assert f.get("volumeMin") == pytest.approx(8.9)
        assert "vol50dMin" not in f               # the 20-day average is not his quantity
        for k in ("relVolume", "dailyPct", "dcrPct"):
            assert k not in f, k
        assert not f.get("excludeHealthcare")

    def test_positive_quiet_average_big_day(self):
        f = _presets()["Stockbee 9M Setup"]
        r = {"ticker": "A", "market_cap": 5e9, "volume": 8.9e6, "avg_volume": 1e6,
             "change_pct": -0.02, "rel_volume": 8.9, "dcr_pct": 0.1, "sector": "Healthcare"}
        assert P.passes(r, f)

    def test_negative_big_average_small_day(self):
        f = _presets()["Stockbee 9M Setup"]
        r = {"ticker": "B", "market_cap": 5e9, "volume": 8.8e6, "avg_volume": 20e6,
             "change_pct": 0.08, "rel_volume": 1.6, "dcr_pct": 0.9, "sector": "Technology"}
        assert not P.passes(r, f)
        assert not P.passes({**r, "volume": None}, f)       # no reading, no hit


# ---------------------------------------------------------------- #9 Liquid Leaders (course)
class TestLiquidLeadersCourse:
    """SwingMasterclass M2_L09_Scanning_Routines.md:134 'ADV >= 2M shares,
    above 50 SMA, RS rank top 20%'. The behaviour already matched; what was
    wrong is the attribution -- the recipe claimed Alex's list, whose seven
    thresholds are different (TradersLab: $100M/day, 1M shares, ADR 3-15...)."""

    def test_recipe_cites_the_course_not_alex(self):
        rec = W.PANELS["liquid_leaders"].recipe
        assert "M2_L09" in rec
        assert "Alex" not in rec

    def test_course_thresholds(self):
        from pipeline.screeners.run_all import compute_universe_scores
        from pipeline.tests.test_derived_fields import _frame
        rows = pd.concat([_frame(ticker=f"F{i}", perf_3m=-0.5 + i * 0.01) for i in range(50)]
                         + [_frame(ticker="TOP", perf_3m=5.0, avg_volume=2e6, sma50_dist=0.01),
                            _frame(ticker="THIN", perf_3m=5.1, avg_volume=1.99e6, sma50_dist=0.01)],
                         ignore_index=True)
        out = compute_universe_scores(rows).set_index("ticker")
        assert bool(out.loc["TOP", "liquid_leader"]) is True
        assert bool(out.loc["THIN", "liquid_leader"]) is False


# ---------------------------------------------------------------- #10 LL Pullback / 21EMA Watch
class TestLiquidLeaderPullbackAlex:
    """traderslab.gitbook.io/primetrading/alexs-scans-and-workflow-traderslab,
    'Liquid Leaders 21dma-structure Pullback scan': Daily closing range > 10%,
    Weekly return < 15%, 0 to 1 x ATR from the 21ema, -0.5 to 4 x ATR from
    the 50sma, Advancing 21ema."""

    P = staticmethod(lambda r: W.PANELS["liquid_leader_pullback"].test(r))

    def test_positive_inside_alex_bands_outside_the_old_ones(self):
        # 0.2 ATR over the 21EMA (old floor was 0.5), 3.8 ATR over the 50SMA
        # (old cap 3, and read in B/A units), week +14% (old cap 12%)
        good = wrow(ema21_atr_dist=0.2, sma50_atr_dist=3.8, atr_from_sma50=4.3, perf_1w=0.14, dcr_pct=0.11)
        assert self.P(good)

    @pytest.mark.parametrize("kw", [
        {"dcr_pct": 0.10},            # > 10%, strict
        {"perf_1w": 0.15},            # < 15%, strict
        {"ema21_atr_dist": -0.01},    # under the 21EMA
        {"ema21_atr_dist": 1.01},
        {"sma50_atr_dist": 4.01},
        {"sma50_atr_dist": -0.51},
        {"liquid_leader": False},
        {"sma50_atr_dist": None},
    ])
    def test_negatives(self, kw):
        assert not self.P(wrow(**kw))

    def test_fifty_line_is_read_in_plain_atr_units(self):
        """Alex's 'x ATR from the 50sma' is price distance / ATR (his ATR
        extensions script: 'ATR-normalized distance'), not Jeff Sun's B/A."""
        from pipeline.screeners.run_all import compute_universe_scores
        from pipeline.tests.test_derived_fields import _frame
        out = compute_universe_scores(_frame(close=120.0, atr=4.0, sma50_dist=0.20))
        # SMA50 = 100, gap 20, 20/4 = 5.0 (B/A would read 0.20/(4/120) = 6.0)
        assert out["sma50_atr_dist"].iloc[0] == pytest.approx(5.0)
        assert out["atr_from_sma50"].iloc[0] == pytest.approx(6.0)

    def test_one_bar_advancing_21ema_is_close_above_it(self):
        """For an EMA, EMA_t - EMA_t-1 = a*(C_t - EMA_t-1), so the 21EMA rose
        today exactly when today's close sits above today's EMA. The 0..1 ATR
        band's floor already demands that -- the clause needs no extra column."""
        rng = np.random.default_rng(7)
        c = pd.Series(100 + rng.normal(0, 2, 300).cumsum())
        e = c.ewm(span=21, adjust=False).mean()
        rising = (e > e.shift(1)).iloc[1:]
        above = (c > e).iloc[1:]
        assert rising.any() and (~rising).any()
        assert (rising == above).all()

    def test_21ema_watch_preset_carries_alex_numbers(self):
        f = _presets()["21EMA Watch"]
        assert (f["ema21Atr"]["min"], f["ema21Atr"]["max"]) == (0, 1)
        assert (f["sma50AtrDist"]["min"], f["sma50AtrDist"]["max"]) == (-0.5, 4)
        assert "sma50Atr" not in f                     # the B/A column is not his unit
        assert f["dcrPct"]["min"] == 10
        assert f["weeklyPct"]["max"] == 15 and f["weeklyPct"].get("min") is None

    def test_preset_hits_reads_the_plain_fifty_line(self):
        f = {"sma50AtrDist": {"enabled": True, "min": -0.5, "max": 4}}
        assert P.passes({"sma50_atr_dist": 3.9}, f)
        assert not P.passes({"sma50_atr_dist": 4.1, "atr_from_sma50": 3.0}, f)


# ---------------------------------------------------------------- #13 Pocket Pivot
class TestPocketPivotMoralesKacher:
    """virtueofselfishinvesting.com/faqs/answer/Ten-Rules-for-Pocket-Pivots
    rule 7: 'Do not buy pocket pivots if the stock is under a critical moving
    average such as the 50-dma or 200-dma.' No count of pivots appears
    anywhere in the source -- the '3+ = his cluster' was ours."""

    def test_panel_one_pivot_above_both_lines(self):
        p = W.PANELS["morales_pp_10d"]
        assert p.test(wrow(pp_count_10d=1, trend_base=False))
        assert "3+" not in p.label

    @pytest.mark.parametrize("kw", [
        {"pp_count_10d": 0},
        {"pp_count_10d": 3, "sma200_dist": -0.01},
        {"pp_count_10d": 3, "sma50_dist": -0.01},
        {"pp_count_10d": 3, "sma200_dist": None},
    ])
    def test_panel_negatives(self, kw):
        assert not W.PANELS["morales_pp_10d"].test(wrow(**kw))

    def test_preset(self):
        f = _presets()["Pocket Pivot"]
        assert f.get("pocketPivotOnly") is True
        assert not f.get("trendBaseOnly") and "adrPct" not in f and not f.get("excludeHealthcare")
        r = {"ticker": "A", "market_cap": 5e9, "pocket_pivot": True, "sma50_dist": 0.02,
             "sma200_dist": 0.10, "trend_base": False, "adr_pct": 1.5, "sector": "Healthcare"}
        assert P.passes(r, f)
        assert not P.passes({**r, "sma200_dist": -0.02}, f)
        assert not P.passes({**r, "pocket_pivot": False}, f)


# ---------------------------------------------------------------- #14 Anticipation
class TestAnticipationLiquidity:
    """stockbee.blogspot.com/2019/10/anticipation-scans-that-can-make-you.html:
    'Liquidity = minv3.1>=100000'; Pradeep Bonde, comment 2021-05-27 on
    /2019/09/ultra-high-volume-moves-are-very.html: 'Minv3.1 is minimum
    volume in last 3 days calculates as of 1 day ago'."""

    def test_min_vol_3d_1_skips_today(self):
        from pipeline.adapters.yfinance_adapter import stockbee_ratios
        hist = pd.DataFrame({"Close": [10.0] * 5, "Low": [9.0] * 5,
                             "Volume": [50_000.0, 120_000.0, 150_000.0, 110_000.0, 10_000.0]})
        r = stockbee_ratios(hist)
        assert r["min_vol_3d_1"] == pytest.approx(110_000.0)   # bars -4..-2
        assert r["min_vol_3d"] == pytest.approx(10_000.0)      # unchanged, includes today

    def test_short_history_is_null(self):
        from pipeline.adapters.yfinance_adapter import stockbee_ratios
        hist = pd.DataFrame({"Close": [10.0] * 3, "Low": [9.0] * 3, "Volume": [2e5] * 3})
        assert stockbee_ratios(hist)["min_vol_3d_1"] is None

    def test_panel_positive_at_the_boundary(self):
        assert W.PANELS["anticipation"].test(wrow(min_vol_3d_1=100_000))

    @pytest.mark.parametrize("v", [99_999, None])
    def test_panel_negative(self, v):
        assert not W.PANELS["anticipation"].test(wrow(min_vol_3d_1=v))

    def test_cli_tool_uses_the_same_floor(self):
        from pipeline.tools.anticipation_scan import liquid
        assert liquid({"min_vol_3d_1": 100_000})
        assert not liquid({"min_vol_3d_1": 99_999, "avg_volume": 5e6})
        assert not liquid({"avg_volume": 5e6})               # no silent fallback
