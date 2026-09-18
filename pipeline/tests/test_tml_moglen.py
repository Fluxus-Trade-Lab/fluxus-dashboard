"""True Market Leaders = Richard Moglen's 2020 definition (2026-09-18).

Andy 2026-09-18, verbatim: 「照 Moglen 2020（建议）可以，Stage 1 或 2 底部突破这类是
可以编写程序检测的，所以你可以搞定。steve jacobs就在做，还有很多人也在做。Deepvue也有。」

Source: https://x.com/RichardMoglen/status/1324813953474678787 (2020-11-06),
verbatim copy in data/research/tml_origin_2026-09-18/README.md.

and 「Stage Analysis本身就来自Weinstein，这点很重要。而本机pine脚本没有完全得到验证」
/「按Weinstein原书来验证」: the stage condition reads weinstein_stage (Weinstein
1988, quotes in stage_analysis.py). A Pine port was built and dropped; the last
test in this file pins that it is not shipped.

Every condition gets one positive and one negative case; the Pine port gets
bar-level checks against hand-computed Pine semantics; the Weinstein machine
gets one case per transition and per breakout-volume route (Ch.4 p.105).
"""

from __future__ import annotations

import csv

import numpy as np
import pandas as pd
import pytest

from pipeline.adapters import fundamentals_store as FS
from pipeline.screeners import stage_analysis as SA
from pipeline.screeners import tml_moglen as T
from pipeline.screeners import watchlist as W


# ------------------------------------------------------------------ helpers
def bars(closes, half_range=5.0, start="2025-09-01", volume=1_000_000):
    closes = np.asarray(closes, dtype=float)
    idx = pd.bdate_range(start, periods=len(closes))
    return pd.DataFrame({"Open": closes, "High": closes + half_range, "Low": closes - half_range,
                         "Close": closes, "Volume": np.full(len(closes), float(volume))}, index=idx)


def tml_row(**kw):
    """A row passing every hard Moglen condition and 5/5 fundamentals."""
    base = {"ticker": "T", "market_cap": 5e9, "avg_volume": 5e6, "close": 100.0,
            "sector": "Technology", "adr_pct": 4.5, "rs_1m": 90, "h_score": 80,
            "sb_avg_dollar_vol_20": 5e8, "rs_rating": 98,
            "wk_sma30_dist": 0.20, "wk_sma30_rising": True, "weinstein_stage": 2,
            "ema10": 95.0, "ema21": 92.0, "sma50_dist": 0.10,
            "ud_vol_ratio_50": 1.5,
            "revenue_growth": 0.40, "eps_growth_this_y": 0.50, "profit_margin": 0.25,
            "roe": 0.30, "eps_growth_next_y": 0.35, "industry_rank": 5}
    base.update(kw)
    return base


# ------------------------------------------------------------------ Pine primitives
class TestWeinstein:
    """Weinstein 1988 Ch.2, operationalized as a weekly state machine
    (stage_analysis docstring). Weekly = W-FRI of business-day bars."""

    def test_uptrend_is_stage_2_and_ma_rising(self):
        f = SA.weinstein_fields(bars(np.linspace(50, 150, 260)))
        assert f["wk_sma30_rising"] is True and f["wk_sma30_dist"] > 0
        assert f["weinstein_stage"] == 2

    def test_downtrend_is_stage_4(self):
        f = SA.weinstein_fields(bars(np.linspace(150, 50, 260)))
        assert f["wk_sma30_rising"] is False and f["wk_sma30_dist"] < 0
        assert f["weinstein_stage"] == 4

    def test_break_under_a_still_rising_ma_is_stage_3(self):
        c = list(np.linspace(50, 150, 255)) + [100.0] * 5
        f = SA.weinstein_fields(bars(c))
        assert f["wk_sma30_rising"] is True and f["wk_sma30_dist"] < 0
        assert f["weinstein_stage"] == 3

    def test_bear_rally_above_a_falling_ma_stays_stage_4(self):
        """Price above a still-FALLING MA is not a base yet: the book's
        Stage 1 needs the MA to flatten first."""
        c = list(np.linspace(150, 50, 255)) + [85.0] * 5    # above the MA (~78), under the week it drops (~110)
        f = SA.weinstein_fields(bars(c))
        assert f["wk_sma30_rising"] is False and f["wk_sma30_dist"] > 0
        assert f["weinstein_stage"] == 4

    @staticmethod
    def _base(n_flat=170):
        # decline, then a flat base long enough for the 30-week MA to flatten
        return list(np.linspace(100, 50, 100)) + [50.0] * n_flat

    def test_flattened_ma_after_decline_is_stage_1(self):
        f = SA.weinstein_fields(bars(self._base()))
        assert f["weinstein_stage"] == 1

    def test_breakout_on_volume_is_stage_2(self):
        """Close clears the prior 10 weeks' high (55) and the MA, on a week
        whose mean daily volume is 3x the prior 4 weeks' -> 1 -> 2."""
        h = bars(self._base() + [60.0] * 5)
        h.iloc[-5:, h.columns.get_loc("Volume")] = 3_000_000.0
        assert SA.weinstein_fields(h)["weinstein_stage"] == 2

    def test_breakout_without_volume_stays_stage_1(self):
        h = bars(self._base() + [60.0] * 5)          # same prices, volume unchanged
        assert SA.weinstein_fields(h)["weinstein_stage"] == 1

    def test_volume_route_a_one_week_spike(self):
        """Ch.4 p.105 (a): one week >= 2x the past month's average."""
        w = {"vol_d": np.array([1.0] * 8 + [2.0]), "day_spike": np.full(9, 1.0)}
        assert SA.breakout_volume_ok(w)[-1]
        w["vol_d"][-1] = 1.9
        assert not SA.breakout_volume_ok(w)[-1]

    def test_volume_route_b_build_up_with_an_increase_on_the_week(self):
        """(b): the last 4 weeks average >= 2x the 8 weeks before, AND the
        breakout week is up on the week before. 1.7 on the breakout week is
        under (a)'s 2x of the past month (avg 1.9)."""
        vd = np.array([1.0] * 8 + [2.5, 2.5, 1.6, 1.7])
        w = {"vol_d": vd, "day_spike": np.full(len(vd), 1.0)}
        assert SA.breakout_volume_ok(w)[-1]
        vd2 = vd.copy(); vd2[-1] = 1.5     # build-up still >= 2x, but no increase on the week
        assert not SA.breakout_volume_ok({"vol_d": vd2, "day_spike": w["day_spike"]})[-1]

    def test_volume_route_c_daily_footnote(self):
        """(c) footnote 5: a session > 2x the prior 5 sessions' average."""
        h = bars(TestWeinstein._base() + [60.0] * 5)
        h.iloc[-3, h.columns.get_loc("Volume")] = 2_100_000.0
        assert SA.weinstein_fields(h)["weinstein_stage"] == 2
        h.iloc[-3, h.columns.get_loc("Volume")] = 2_000_000.0     # "better than twice": strict
        assert SA.weinstein_fields(h)["weinstein_stage"] == 1

    def test_no_stage_2_entry_while_the_ma_still_declines(self):
        """Investor entry: the MA "must no longer be declining" -- a volume
        breakout above a still-falling MA is not Stage 2."""
        c = list(np.linspace(150, 50, 200)) + [50.0] * 60 + [90.0] * 5
        h = bars(c)
        h.iloc[-5:, h.columns.get_loc("Volume")] = 3_000_000.0
        wk = SA.weinstein_series(h)
        assert wk["breakout"].iloc[-1] and wk["falling"].iloc[-1]
        assert wk["stage"].iloc[-1] != 2

    def test_numpy_weekly_bars_equal_pandas_w_fri_resample(self):
        rng = np.random.default_rng(3)
        h = bars(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 252))), start="2025-09-17")
        h["Volume"] = rng.integers(1e5, 1e7, len(h)).astype(float)
        h = h.drop(h.index[[10, 11, 40]])          # holidays: short weeks
        w = SA._weekly(h)
        r = h.resample("W-FRI").agg({"Close": "last", "High": "max", "Low": "min", "Volume": "mean"}).dropna()
        for k, col in (("close", "Close"), ("high", "High"), ("low", "Low"), ("vol_d", "Volume")):
            assert w[k] == pytest.approx(r[col].to_numpy())

    def test_needs_31_weeks(self):
        f = SA.weinstein_fields(bars(np.linspace(50, 150, 100)))
        assert f["weinstein_stage"] is None and f["wk_sma30_rising"] is None


# ------------------------------------------------------------------ Up/Down volume
class TestUpDownVolume:
    def test_ibd_50_day_ratio(self):
        """IBD: volume on up days / volume on down days over the last 50
        sessions; an unchanged close counts in neither."""
        c = [100.0]
        v = [1.0]
        for i in range(50):            # 25 up days of 3, 20 down of 2, 5 flat
            if i < 25:
                c.append(c[-1] + 1); v.append(3.0)
            elif i < 45:
                c.append(c[-1] - 1); v.append(2.0)
            else:
                c.append(c[-1]); v.append(99.0)
        h = bars(c)
        h["Volume"] = v
        assert SA.up_down_vol_ratio(h, 50) == pytest.approx(75.0 / 40.0)

    def test_no_down_days_is_none(self):
        h = bars(np.arange(100.0, 160.0))
        assert SA.up_down_vol_ratio(h, 50) is None


# ------------------------------------------------------------------ fundamentals store: two more fields, same call
class TestFundamentalsExtra:
    def test_margin_and_roe_come_from_the_same_info_dict(self):
        m = FS.map_info({"profitMargins": 0.22, "returnOnEquity": 0.31, "revenueGrowth": 0.3})
        assert m["profit_margin"] == pytest.approx(0.22) and m["roe"] == pytest.approx(0.31)
        m2 = FS.map_info({})
        assert m2["profit_margin"] is None and m2["roe"] is None

    def test_apply_carries_them(self):
        uni = pd.DataFrame({"ticker": ["A", "B"]})
        store = {"A": {"revenue_growth": 0.3, "profit_margin": 0.21, "roe": 0.18, "asof": "2026-09-18"}}
        out = FS.apply(uni, store)
        assert out.loc[0, "profit_margin"] == pytest.approx(0.21) and out.loc[0, "roe"] == pytest.approx(0.18)
        assert pd.isna(out.loc[1, "profit_margin"])


# ------------------------------------------------------------------ the TML test, condition by condition
class TestHardConditions:
    def test_full_row_passes(self):
        assert T.passes(tml_row())

    @pytest.mark.parametrize("field,bad", [
        ("sb_avg_dollar_vol_20", 29e6),     # "Dollar Volume > $30 Million is essential"
        ("rs_rating", 96),                  # "RS Rating over 97 is ideal"
        ("wk_sma30_dist", -0.01),           # "Above a Rising 30 Week Moving Average" (above)
        ("wk_sma30_rising", False),         # ... (rising)
        ("weinstein_stage", 1),             # "Breaking out of a Stage 1 or Stage 2 Base"
        ("weinstein_stage", 3),
        ("weinstein_stage", 4),
        ("weinstein_stage", None),
        ("ema10", 101.0),                   # "Trending above Key Moving Averages (10, 21ema, 50sma)"
        ("ema21", 101.0),
        ("sma50_dist", -0.01),
        ("ud_vol_ratio_50", 1.2),           # "Up/Down Vol > 1.2" (strict)
    ])
    def test_each_hard_condition_can_fail_alone(self, field, bad):
        assert not T.passes(tml_row(**{field: bad}))

    def test_boundaries(self):
        assert T.passes(tml_row(rs_rating=97))                # >= 97
        assert not T.passes(tml_row(sb_avg_dollar_vol_20=30e6))  # > $30M strict
        assert T.passes(tml_row(ud_vol_ratio_50=1.21))

    def test_missing_hard_input_fails(self):
        assert not T.passes(tml_row(rs_rating=None))
        assert not T.passes(tml_row(ud_vol_ratio_50=None))


class TestFundamentalsMostOf:
    def test_three_of_five_passes(self):
        r = tml_row(profit_margin=0.10, roe=0.05)          # 3 met, 2 not met
        assert T.fundamentals(r) == (3, 5) and T.passes(r)

    def test_two_of_five_fails(self):
        r = tml_row(profit_margin=0.10, roe=0.05, eps_growth_next_y=0.1)
        assert T.fundamentals(r) == (2, 5) and not T.passes(r)

    def test_missing_is_out_of_the_denominator_but_three_are_still_needed(self):
        r3 = tml_row(profit_margin=None, roe=None)           # 3/3 known -> pass
        assert T.fundamentals(r3) == (3, 3) and T.passes(r3)
        r2 = tml_row(profit_margin=None, roe=None, eps_growth_next_y=None)   # 2/2 -> fail
        assert T.fundamentals(r2) == (2, 2) and not T.passes(r2)

    def test_strict_greater_than(self):
        r = tml_row(revenue_growth=0.25, eps_growth_this_y=0.25, profit_margin=0.20, roe=0.17,
                    eps_growth_next_y=0.26)
        assert T.fundamentals(r) == (1, 5)


class TestFlagsOnly:
    def test_top20_industry_is_a_flag_not_a_filter(self):
        assert T.passes(tml_row(industry_rank=80))
        assert T.flags(tml_row(industry_rank=20))["top20_industry"] is True
        assert T.flags(tml_row(industry_rank=21))["top20_industry"] is False
        assert T.flags(tml_row(industry_rank=None))["top20_industry"] is None


# ------------------------------------------------------------------ wired into the panel and leaders_log
class TestPanelWiring:
    def test_panel_uses_the_moglen_test(self):
        assert W.PANELS["true_market_leaders"].test is T.passes
        assert "Moglen" in W.PANELS["true_market_leaders"].recipe
        # no longer needs a Leading group or a liquid leader
        out = W.build([tml_row(ticker="X", liquid_leader=False)], date="2026-09-18")
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}["true_market_leaders"]
        assert p["measured"] is True and [t["ticker"] for t in p["tickers"]] == ["X"]
        assert p["tickers"][0]["top20_industry"] is True

    def test_unmeasured_before_the_fields_exist(self):
        r = tml_row(ticker="X")
        for k in ("weinstein_stage", "wk_sma30_rising", "ud_vol_ratio_50", "sb_avg_dollar_vol_20"):
            r.pop(k)
        out = W.build([r], date="2026-09-18")
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}["true_market_leaders"]
        assert p["measured"] is False and p["tickers"] == []

    def test_leaders_log_tml_equals_the_panel_and_logs_non_liquid_tmls(self, tmp_path):
        rs = [tml_row(ticker="TML_ONLY", liquid_leader=False),
              tml_row(ticker="LL_ONLY", liquid_leader=True, rs_rating=90),
              tml_row(ticker="NEITHER", liquid_leader=False, rs_rating=90),
              tml_row(ticker="QUIET", liquid_leader=True, adr_pct=1.5)]     # ADR floor, same as the page
        W.archive_leaders(rs, date="2026-09-18", path=tmp_path / "log.csv")
        logged = {r["ticker"]: (r["tml"] == "True", r["liquid_leader"] == "True")
                  for r in csv.DictReader((tmp_path / "log.csv").open())}
        assert logged == {"TML_ONLY": (True, False), "LL_ONLY": (False, True), "QUIET": (False, True)}
        out = W.build(rs, date="2026-09-18")
        shown = {t["ticker"] for pn in out["zones"][0]["panels"] if pn["key"] == "true_market_leaders"
                 for t in pn["tickers"]}
        assert {t for t, (tml, _) in logged.items() if tml} == shown


# ------------------------------------------------------------------ pipeline wiring
class TestPipelineWiring:
    def test_industry_rank_orders_industries_by_median_rs_3m(self):
        """Moglen's 'Top 20 Industry groups' flag reads industry_rank: 1 = the
        industry with the highest median rs_3m among tradeable members (the
        same quantity i_score ranks)."""
        from pipeline.screeners.run_all import compute_universe_scores
        rows = []
        for ind, p3 in (("Hot", 0.60), ("Warm", 0.20), ("Cold", -0.30)):
            for k in range(3):
                rows.append({"ticker": f"{ind}{k}", "close": 100.0, "atr": 3.0, "sma20_dist": 0.05,
                             "sma50_dist": 0.10, "sma200_dist": 0.20, "market_cap": 5e9,
                             "avg_volume": 5e6, "industry": ind, "perf_1w": 0.0, "perf_1m": 0.0,
                             "perf_3m": p3 + k * 0.01, "perf_6m": 0.1, "perf_1y": 0.2, "high_52w": 110.0})
        out = compute_universe_scores(pd.DataFrame(rows)).set_index("ticker")
        assert out.loc["Hot0", "industry_rank"] == 1
        assert out.loc["Warm2", "industry_rank"] == 2
        assert out.loc["Cold1", "industry_rank"] == 3

    def test_new_fields_are_exported_to_universe_json(self):
        import inspect
        from pipeline.screeners import run_all
        src = inspect.getsource(run_all)
        for f in ("sb_avg_dollar_vol_20", "wk_sma30", "wk_sma30_dist", "wk_sma30_rising",
                  "weinstein_stage", "ud_vol_ratio_50", "profit_margin", "roe",
                  "industry_rank"):
            assert f"'{f}'" in src, f

    def test_adapter_computes_the_bar_fields_from_the_bars_it_holds(self):
        import inspect
        from pipeline.adapters import yfinance_adapter
        assert "moglen_bar_fields(hist)" in inspect.getsource(yfinance_adapter)
        f = SA.moglen_bar_fields(bars(np.linspace(50, 150, 260)))
        assert set(f) == {"wk_sma30", "wk_sma30_dist", "wk_sma30_rising",
                          "weinstein_stage", "ud_vol_ratio_50"}


def test_the_unverified_pine_port_is_not_shipped():
    """Andy 2026-09-18: 「本机pine脚本没有完全得到验证」 -- Weinstein's book is the ruler.
    No stage_tdn field, no Pine-port code, no third-party copy in the repo."""
    import inspect
    from pathlib import Path
    from pipeline.screeners import run_all
    assert not hasattr(SA, "stage_tdn") and not hasattr(SA, "stage_tdn_series")
    assert "'stage_tdn'" not in inspect.getsource(run_all)
    root = Path(__file__).resolve().parents[2]
    assert not (root / "indicators/third_party/tradedudenyc_candles_stage_analysis_modified.pine").exists()
