"""Mike Webster's Power Trend -- ON/OFF state machine.

Source of truth for the conditions asserted here:
`data/research/videos_2026-08/webster_21ema_wro9_GxQpyUfZv4U.txt` (the inventor,
in his own voice, on the 21-day EMA and on Chuck's "flat or on an incline, not a
decline" 50-day rule) plus the two written write-ups that credit him by name --
TradingSim "Riding the Power Trend" and Deepvue "Mike Webster Indicators".
The full citation trail lives in
`data/research/ops/recap_vocab_sources_2026-09-06.md` section 7.
"""

import pandas as pd
import pytest

from pipeline.macro.calc_signals import (
    EMA21_ABOVE_SMA50_DAYS,
    LOW_ABOVE_EMA21_DAYS,
    calculate_ma_structure,
    calculate_power_trend,
)


def _bars(closes, *, green=True, low_gap=0.004):
    """Build an OHLC frame from a close path.

    ``green`` controls condition (4): close > open.  ``low_gap`` sets how far
    the daily low sits under the close, which is what decides condition (1).
    """
    rows = []
    for i, c in enumerate(closes):
        o = c * (0.995 if green else 1.005)
        lo = min(o, c) * (1 - low_gap)
        hi = max(o, c) * 1.002
        rows.append({"Open": o, "High": hi, "Low": lo, "Close": c})
    return pd.DataFrame(rows, index=pd.date_range("2024-01-01", periods=len(closes), freq="B"))


def _trend_series():
    """A path that is flat, then rallies hard, then breaks down.

    Flat base (120 bars) keeps EMA21 pinned to SMA50 so the trend cannot be on.
    The rally is steep and steady enough that the daily low clears EMA21 for far
    more than 10 sessions and EMA21 clears SMA50 for far more than 5.  The
    collapse is deep enough to drag EMA21 back under SMA50, which is the
    published OFF condition.
    """
    base = [100.0] * 120
    rally = [100.0 * (1.012 ** (i + 1)) for i in range(60)]
    peak = rally[-1]
    bust = [peak * (1 - 0.030 * (i + 1)) for i in range(40)]
    return base + rally + bust


def test_power_trend_turns_on_during_the_rally():
    closes = _trend_series()
    # 30 bars into the rally every published condition has had time to mature.
    hist = _bars(closes[:150])
    pt = calculate_power_trend(hist)

    assert pt["low_gt_ema21_10d"] is True
    assert pt["ema21_gt_sma50_5d"] is True
    assert pt["sma50_rising"] is True
    assert pt["close_gt_open"] is True
    assert pt["is_power_trend"] is True


def test_power_trend_is_off_in_the_flat_base():
    hist = _bars(_trend_series()[:120])
    pt = calculate_power_trend(hist)

    assert pt["is_power_trend"] is False
    assert pt["low_gt_ema21_10d"] is False


def test_power_trend_turns_off_when_ema21_loses_sma50():
    """The published OFF condition: EMA21 crosses back below SMA50."""
    closes = _trend_series()
    hist = _bars(closes)

    ema21 = hist["Close"].ewm(span=21).mean()
    sma50 = hist["Close"].rolling(50).mean()
    assert ema21.iloc[-1] < sma50.iloc[-1], "fixture must actually cross back down"

    assert calculate_power_trend(hist)["is_power_trend"] is False


def test_state_persists_through_a_red_day():
    """Once on, the trend stays on -- a single red candle is not an OFF condition.

    This is the whole point of the state machine, and the thing our previous
    five-bool recompute could not express.
    """
    closes = _trend_series()[:150]
    on = calculate_power_trend(_bars(closes))
    assert on["is_power_trend"] is True

    # Same path, but today prints a red candle: condition (4) fails, yet EMA21
    # is still comfortably above SMA50, so the published OFF condition has not
    # fired and the trend must remain on.
    hist = _bars(closes)
    last = hist.index[-1]
    hist.loc[last, "Open"] = hist.loc[last, "Close"] * 1.005

    pt = calculate_power_trend(hist)
    assert pt["close_gt_open"] is False
    assert pt["is_power_trend"] is True


def test_streak_thresholds_are_the_published_ones():
    assert LOW_ABOVE_EMA21_DAYS == 10
    assert EMA21_ABOVE_SMA50_DAYS == 5


def test_low_not_close_is_what_gates_condition_one():
    """Webster's condition is the *low* above the 21-day, not the close.

    A path whose closes ride above EMA21 but whose lows keep dipping through it
    must not qualify -- that distinction is the reason he prefers the low.
    """
    # A gentle rally, so EMA21 tracks close behind price: at 0.15%/day the close
    # sits roughly 1.5% over the 21-day, and a 3% daily low reaches through it.
    # (The main fixture climbs 1.2%/day, which leaves EMA21 ~12% adrift -- far
    # too much room for any believable low to puncture.)
    closes = [100.0] * 120 + [100.0 * (1.0015 ** (i + 1)) for i in range(60)]
    deep = _bars(closes, low_gap=0.03)

    assert (deep["Close"] > deep["Close"].ewm(span=21).mean()).iloc[-1], "closes ride above"
    assert (deep["Low"] < deep["Close"].ewm(span=21).mean()).iloc[-1], "lows do not"

    pt = calculate_power_trend(deep)
    assert pt["low_gt_ema21_10d"] is False
    assert pt["is_power_trend"] is False


def test_short_history_is_all_false_not_an_exception():
    pt = calculate_power_trend(_bars([100.0] * 10))
    assert pt["is_power_trend"] is False
    assert all(v is False for v in pt.values())


def test_ma_structure_is_reported_separately_from_power_trend():
    """Our three extra checks survive, but under their own name.

    They are not Webster's and must never be rendered as Power Trend rows.
    """
    hist = _bars(_trend_series()[:150])
    sma50 = float(hist["Close"].rolling(50).mean().iloc[-1])
    sma200 = float(hist["Close"].rolling(200).mean().iloc[-1])

    ms = calculate_ma_structure(hist, sma50, sma200)
    assert set(ms) == {"3d_gt_50sma", "3d_gt_200sma", "50sma_gt_200sma"}

    pt = calculate_power_trend(hist)
    assert not set(pt) & set(ms), "the two groups must not share keys"


@pytest.mark.parametrize("key", [
    "3d_gt_20sma", "20sma_gt_50sma", "3d_gt_50sma", "3d_gt_200sma", "50sma_gt_200sma",
])
def test_power_trend_no_longer_reports_the_old_non_standard_keys(key):
    hist = _bars(_trend_series()[:150])
    assert key not in calculate_power_trend(hist)


def test_the_adapter_actually_calls_this_and_not_its_own_copy():
    """The gate has to be on the chain, not just correct.

    `calculate_power_trend` sat in this module unused for its whole life: the
    adapter kept its own inline copy of the five old booleans, so fixing the
    module alone would have changed nothing that reaches the page.
    """
    from pathlib import Path

    import pipeline.adapters.yfinance_adapter as adapter

    src = Path(adapter.__file__).read_text()
    assert "'power_trend': calculate_power_trend(hist)" in src
    assert "'ma_structure': calculate_ma_structure(hist, sma50, sma200)" in src
    assert "3d_gt_20sma" not in src, "the old inline copy must be gone, not shadowed"
