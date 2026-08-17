"""Tests for the VCS v2 port (oratnek's Volatility Contraction Score).

Source of truth: indicators/third_party/oratnek_vcs_v2.pine (verbatim). This
is a FAITHFUL port -- the previous calculate_vcs was a modified port of an
older version (min(13,3) stdev, a Kaufman-ER quality term, .3/.3/.2/.2
weights) with no tests and no golden check. Every constant here is the
script's default.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.screeners import vcs as V


def frame(n, tr=2.0, std_amp=1.0, vol=1000.0, base=100.0, seed=1):
    """n bars of a noisy flat series with controllable range, dispersion and
    volume. Deterministic."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)
    close = base + std_amp * z
    high = close + tr / 2
    low = close - tr / 2
    opn = np.r_[close[0], close[:-1]]
    volume = np.full(n, vol)
    idx = pd.bdate_range("2025-01-01", periods=n)
    return pd.DataFrame({"Open": opn, "High": high, "Low": low, "Close": close, "Volume": volume}, index=idx)


def concat(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    b = b.copy(); b.index = pd.bdate_range(a.index[-1] + pd.Timedelta(days=1), periods=len(b))
    return pd.concat([a, b])


class TestComponents:
    def test_true_range_first_bar_uses_high_minus_low(self):
        """ta.tr(true): on the first bar (no prior close) TR = high - low."""
        df = frame(5)
        tr = V.true_range(df["High"], df["Low"], df["Close"])
        assert tr.iloc[0] == pytest.approx(df["High"].iloc[0] - df["Low"].iloc[0])

    def test_stdev_is_population(self):
        """ta.stdev is population (ddof=0), not sample."""
        s = pd.Series([1.0, 2.0, 3.0, 4.0])
        assert V.pine_stdev(s, 4).iloc[-1] == pytest.approx(np.std([1, 2, 3, 4], ddof=0))

    def test_warmup_uses_expanding_windows_like_min_barcount_len(self):
        """lenLong = math.min(barCount, 63): before 63 bars the SMA runs over
        the bars that exist, it is not na. rolling(min_periods=1) is that."""
        s = pd.Series(np.arange(1.0, 11.0))
        out = V.pine_sma(s, 63)
        assert out.iloc[4] == pytest.approx(np.mean([1, 2, 3, 4, 5]))
        assert not out.isna().any()


class TestScore:
    def test_compression_scores_high(self):
        """63 bars wide/dispersed/heavy volume, then 13 bars tight/quiet/dry:
        ratioATR, ratioStd and volRatio all fall well under 1 -> high score."""
        wide = frame(120, tr=4.0, std_amp=2.0, vol=2000.0)
        tight = frame(13, tr=0.4, std_amp=0.2, vol=500.0, base=float(wide["Close"].iloc[-1]), seed=2)
        df = concat(wide, tight)
        out = V.vcs(df)
        assert out.score >= 70

    def test_expansion_scores_low(self):
        quiet = frame(120, tr=0.5, std_amp=0.25, vol=500.0)
        loud = frame(13, tr=5.0, std_amp=2.5, vol=3000.0, base=float(quiet["Close"].iloc[-1]), seed=3)
        out = V.vcs(concat(quiet, loud))
        assert out.score < 20

    def test_bounded_zero_to_hundred(self):
        for seed in range(4):
            out = V.vcs(frame(200, seed=seed))
            assert 0.0 <= out.score <= 100.0

    def test_efficiency_filter_zeroes_a_straight_line(self):
        """13 bars of pure trend: |close - close[13]| == sum(TR) -> efficiency
        1 -> trendFactor 0 -> physics 0. A momentum pole is not compression."""
        base = frame(120, tr=1.0, std_amp=0.5, vol=1000.0)
        n = 14
        c = np.linspace(base["Close"].iloc[-1], base["Close"].iloc[-1] + 14, n)
        pole = pd.DataFrame({"Open": c - 1.0, "High": c, "Low": c - 1.0, "Close": c, "Volume": 1000.0})
        # each bar: high=close, low=close-1, prev close = close-1 -> TR = 1, sum over 13 = 13 = net change
        out = V.vcs(concat(base, pole))
        assert out.physics_last == pytest.approx(0.0, abs=1e-9)

    def test_lower_low_penalty(self):
        """isHigherLow = lowest(low,13) >= lowest(low,63)[13]; else x0.75."""
        base = frame(120, tr=1.0, std_amp=0.5)
        # tight tail, but one bar undercuts every low of the prior 63
        tail = frame(13, tr=0.3, std_amp=0.1, base=float(base["Close"].iloc[-1]), seed=5)
        tail_lo = tail.copy(); tail_lo.loc[tail_lo.index[3], "Low"] = base["Low"].min() - 5
        a = V.vcs(concat(base, tail))
        b = V.vcs(concat(base, tail_lo))
        assert a.higher_low is True and b.higher_low is False
        assert b.score == pytest.approx(b.total * 0.75, abs=1e-9)
        assert a.score == pytest.approx(a.total, abs=1e-9)

    def test_consistency_bonus_counts_consecutive_tight_days_and_caps_at_15(self):
        """daysTight increments while smoothPhysics >= 70 and resets otherwise;
        the bonus is min(15, daysTight); weightPhysics is 0.85."""
        wide = frame(120, tr=4.0, std_amp=2.0, vol=2000.0)
        tight = frame(40, tr=0.3, std_amp=0.15, vol=400.0, base=float(wide["Close"].iloc[-1]), seed=2)
        out = V.vcs(concat(wide, tight))
        assert out.days_tight >= 15
        assert out.consistency == 15
        assert out.total == pytest.approx(out.smooth_last * 0.85 + 15, abs=1e-9)

    def test_ema3_smoothing_is_pine_ema(self):
        """ta.ema(x, 3): alpha = 2/(3+1), seeded on the first value."""
        s = pd.Series([0.0, 100.0, 100.0])
        e = V.pine_ema(s, 3)
        assert e.iloc[1] == pytest.approx(50.0)
        assert e.iloc[2] == pytest.approx(75.0)


class TestContract:
    def test_short_history_is_none(self):
        """Port-only rule: under 76 bars (63 + 13) the score is warm-up noise;
        Pine prints a number from bar 1, we say unmeasured."""
        assert V.vcs(frame(50)).score is None

    def test_missing_volume_bar_does_not_poison(self):
        df = frame(120)
        df.loc[df.index[-3], "Volume"] = np.nan
        out = V.vcs(df)
        assert out.score is not None and np.isfinite(out.score)

    def test_adapter_entry_point_returns_rounded_float(self):
        from pipeline.adapters.yfinance_adapter import calculate_vcs
        v = calculate_vcs(frame(150))
        assert isinstance(v, float) and 0.0 <= v <= 100.0
        assert v == round(v, 1)


class TestGoldenAgainstTradingView:
    """AEHR and SMCI, daily bars to 2026-08-14, against oratnek's own VCS v2
    on TradingView (indicators/third_party/oratnek_vcs_probe.pine, Andy's
    screenshots). Components to 4 dp, final score within 0.02 -- the SMCI
    ratioATR delta of 3e-4 is a sub-penny high (32.585 vs 32.59) and the score
    delta is EMA3 carrying source micro-differences."""
    import json as _json
    from pathlib import Path as _Path
    _FX = _Path(__file__).parent / "fixtures"
    GOLD = _json.loads((_FX / "vcs_golden_2026-08-14.json").read_text())
    BARS = _json.loads((_FX / "vcs_bars_2026-08-14.json").read_text())

    @pytest.mark.parametrize("ticker", ["AEHR", "SMCI"])
    def test_matches_the_chart(self, ticker):
        b = self.BARS[ticker]
        df = pd.DataFrame({k: b[k] for k in ("Open", "High", "Low", "Close", "Volume")},
                          index=pd.to_datetime(b["date"]))
        r = V.vcs(df)
        g = self.GOLD[ticker]
        h, l, c, v = df["High"], df["Low"], df["Close"], df["Volume"].astype(float)
        tr = V.true_range(h, l, c)
        assert (V.pine_sma(tr, 13) / V.pine_sma(tr, 63)).iloc[-1] == pytest.approx(g["ratioATR"], abs=5e-4)
        assert (V.pine_stdev(c, 13) / V.pine_stdev(c, 63)).iloc[-1] == pytest.approx(g["ratioStd"], abs=5e-4)
        assert (V.pine_sma(v, 5) / V.pine_sma(v, 50)).iloc[-1] == pytest.approx(g["volRatio"], abs=1e-3)
        assert (abs(c - c.shift(13)) / V.pine_sum(tr, 13)).iloc[-1] == pytest.approx(g["efficiency"], abs=5e-4)
        assert r.physics_last == pytest.approx(g["physics"], abs=0.02)
        assert r.days_tight == g["daysTight"] and r.higher_low is g["isHigherLow"]
        assert r.score == pytest.approx(g["VCS"], abs=0.02)
