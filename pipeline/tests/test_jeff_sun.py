"""Jeff Sun's scanner specs are DATA copied from primary sources; these tests
pin that they stay verbatim and that the local replication stays honest about
what it cannot express."""
import pandas as pd
import pytest

from pipeline.screeners import jeff_sun as J


class TestSpecsAreVerbatim:
    def test_thirteen_tradingview_and_seven_finviz_scans(self):
        assert len(J.TV_SCANS) == 13 and len(J.FINVIZ_SCANS) == 7

    def test_momentum_thresholds_match_the_notebook(self):
        want = {"1W": 20, "1M": 30, "3M": 70, "6M": 100}
        for tf, thr in want.items():
            for size in ("Small", "Large"):
                s = J.TV_SCANS[f"Mom_{tf}_{size}"]
                perf = [c for c in s.clauses if c.field.startswith("Perf.")]
                assert len(perf) == 1 and perf[0].op == ">" and perf[0].value == thr

    def test_large_caps_relax_float_and_drop_volatility(self):
        """The notebook's two cap groups differ exactly here and nowhere else."""
        small, large = J.TV_SCANS["Mom_1M_Small"], J.TV_SCANS["Mom_1M_Large"]
        f = lambda s, fld: next((c for c in s.clauses if c.field == fld), None)
        assert f(small, "float_shares_outstanding").value == 50_000_000
        assert f(large, "float_shares_outstanding").value == 150_000_000
        assert f(small, "Volatility.M").value == 3 and f(large, "Volatility.M") is None
        assert small.post[-1].endswith("0.80") and large.post[-1].endswith("0.90")

    def test_finviz_mover_codes_match_jeffs_urls(self):
        """From tweet 1659786288067928064: ta_perf_1w20o / ta_volatility_wo4,
        ta_perf_4w30o / mo5, ta_perf_13w50o, ta_perf_26w100o."""
        get = lambda k, fld: next(c.value for c in J.FINVIZ_SCANS[k].clauses if c.field == fld)
        assert get("FV_Mover_1W_20", "ta_perf_1w") == 20 and get("FV_Mover_1W_20", "ta_volatility_w") == 4
        assert get("FV_Mover_1M_30", "ta_perf_4w") == 30 and get("FV_Mover_1M_30", "ta_volatility_m") == 5
        assert get("FV_Mover_3M_50", "ta_perf_13w") == 50
        assert get("FV_Mover_6M_100", "ta_perf_26w") == 100
        assert get("FV_Qullamaggie_TASR", "sh_short") == 30 and get("FV_Qullamaggie_TASR", "sh_float") == 100_000_000


class TestPostFiltersVerbatim:
    def test_apply_post_uses_the_notebooks_expressions(self):
        s = J.TV_SCANS["4_Strongest_Stock_JK"]
        df = pd.DataFrame({"name": ["A", "B", "C"], "close": [100.0, 100.0, 100.0],
                           "price_52_week_low": [50.0, 70.0, 50.0],   # B fails 1.70x low
                           "SMA10": [95.0, 95.0, 85.0]})              # C fails SMA10 >= 0.90*close
        out = J.apply_post(df, s)
        assert list(out["name"]) == ["A"]

    def test_scans_without_post_pass_through(self):
        s = J.TV_SCANS["1_Fundamental_Growth"]
        df = pd.DataFrame({"name": ["A"]})
        assert J.apply_post(df, s) is df


class TestLocalMaskIsHonest:
    def _uni(self):
        return pd.DataFrame({
            "ticker": ["HIT", "SLOW", "TINY"],
            "market_cap": [2e9, 2e9, 1e8],
            "volume": [500_000, 500_000, 500_000],
            "perf_1m": [0.45, 0.10, 0.45],          # fraction; TV Perf.1M is %
            "adr_pct": [5.0, 5.0, 5.0],
            "revenue_growth": [0.3, 0.3, 0.3],
            # close / 52w-low - 1; the notebook's "close >= low * 1.50" post-filter
            # is exactly "low_52w >= 0.5", so it IS expressible and is applied.
            "low_52w": [0.9, 0.9, 0.9],
        })

    def test_expressible_clauses_are_applied(self):
        m, _ = J.local_mask(J.TV_SCANS["Mom_1M_Small"], self._uni())
        assert list(self._uni().loc[m, "ticker"]) == ["HIT"]

    def test_inexpressible_clauses_are_reported_not_dropped_silently(self):
        _, skipped = J.local_mask(J.TV_SCANS["Mom_1M_Small"], self._uni())
        joined = " | ".join(skipped)
        for must in ("average_volume_60d_calc", "float_shares_outstanding", "post:"):
            assert must in joined, f"{must} was silently dropped"

    def test_missing_columns_do_not_pass(self):
        """A universe without the column must not match everything."""
        u = self._uni().drop(columns=["perf_1m"])
        m, _ = J.local_mask(J.TV_SCANS["Mom_1M_Small"], u)
        assert not m.any()
