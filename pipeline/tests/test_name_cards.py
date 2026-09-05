"""Card engine: deterministic verdicts, seat picking, archive."""
import json

import pandas as pd

from pipeline.screeners import name_cards as NC


def test_verdict_is_a_template():
    r = {"atr_from_sma50": 2.1, "liquid_leader": True, "change_pct": 0.02}
    v = NC.verdict(r, "Leading", True, ["episodic_pivot"], 0)
    assert v == "水域✓ · TML✓ · 建仓区(2.1 ATR) · 今日刀: episodic_pivot"
    v2 = NC.verdict({"atr_from_sma50": 9.6, "change_pct": 0.177}, "Improving", False, [], 6)
    assert "减仓区(9.6 ATR)" in v2 and "⚠当日≥15%不追" in v2 and "名册 6 连" in v2
    assert NC.verdict(r, "Leading", True, ["episodic_pivot"], 0) == v   # same input, same sentence


def _wl(panel_tickers):
    return {"zones": [{"key": "z", "panels": [
        {"key": k, "tickers": [dict(ticker=t, **extra) for t, extra in v]}
        for k, v in panel_tickers.items()]}]}


def test_pick_seats_v2_atr_gate_theme_preference_substitutes():
    wl = _wl({
        "true_market_leaders": {"NEW": {}, "OLD": {}}.items(),
        "episodic_pivot": {"EPX": {}}.items(),
        "ma_reclaim": {"DEEP": {}, "SHAL": {}}.items(),
        "vcs": {"COIL": {}}.items(),
        "bullish_4pct": {}.items(),
    })
    prev = _wl({"true_market_leaders": {"OLD": {}}.items()})
    by = {"NEW": {"h_score": 90, "atr_from_sma50": 3.0}, "OLD": {"atr_from_sma50": 2.0},
          "EPX": {"atr_from_sma50": 9.6, "rel_volume": 12.8},         # extended EP -> loses the seat
          "DEEP": {"high_52w": -0.40, "rs_3m": 80, "atr_from_sma50": 1.0},
          "SHAL": {"high_52w": -0.05, "rs_3m": 99, "atr_from_sma50": 1.0},
          "COIL": {"vcs": 80, "atr_from_sma50": 2.0},
          "HOT": {"atr_from_sma50": 11.9}, "WARM": {"atr_from_sma50": 3.0}}
    heat = [{"ticker": "HOT", "score": 12.0}, {"ticker": "WARM", "score": 9.0}]
    assets = [{"ticker": "GLD", "rs_line_pctl_21": 100.0, "hi20": True}]
    seats = NC.pick_seats(wl, prev, heat, assets, by, states={"NEW": "Leading"})
    got = {s["seat"]: s["ticker"] for s in seats}
    # HOT extended -> WARM; EPX extended -> entry falls through its chain to None here
    assert got["burning"] == "WARM" and got["new_leader"] == "NEW"
    # SHAL (-5% off its high, in the reclaim panel) is the fresh-high
    # pullback archetype and now OUTRANKS the deep V (Andy 2026-08-20)
    assert got["entry"] is None and got["v_reversal"] == "SHAL"
    assert got["coiling"] == "COIL" and got["asset"] == "GLD"
    # substitute: no NEW tml -> lowest-ATR existing TML
    seats2 = NC.pick_seats(wl, wl, heat, assets, by, states={})
    got2 = {s["seat"]: s["ticker"] for s in seats2}
    assert got2["new_leader"] == "OLD"
    # theme preference: two heat names both fine, Improving beats no-theme
    by3 = {"A": {"atr_from_sma50": 2}, "B": {"atr_from_sma50": 2}}
    s3 = NC.pick_seats(_wl({}), None, [{"ticker": "A"}, {"ticker": "B"}], [], by3, states={"B": "Improving"})
    assert {x["seat"]: x["ticker"] for x in s3}["burning"] == "B"
    # dry day: seats stay null with the chain named
    s4 = NC.pick_seats(_wl({}), None, [], [], {})
    assert sum(1 for x in s4 if x["ticker"] is None) == 6


def test_build_card_and_archive(tmp_path):
    idx = pd.bdate_range("2026-02-02", periods=140)
    c = pd.Series([50 + i * 0.3 for i in range(140)], index=idx)
    hist = pd.DataFrame({"Open": c * 0.99, "High": c * 1.01, "Low": c * 0.98,
                         "Close": c, "Volume": [1e6] * 140})
    ev = pd.DataFrame([{"date": "2026-08-18", "ticker": "T", "screener": "preset:sugar_babies"}])
    hits = pd.DataFrame([{"date": "2026-08-19", "ticker": "T", "panel": "true_market_leaders",
                          "chg_pct": 1.0, "atr_from_sma50": 2.0}])
    card = NC.build_card("T", row={"close": 91.7, "change_pct": 0.01, "atr_from_sma50": 2.0,
                                   "rs_1m": 90, "liquid_leader": True, "bar_date": "2026-08-19"},
                         group="G", state="Leading", hist=hist, spy_close=c * 0 + 100,
                         events=ev, panels=hits, heat={"score": 5.0, "confluence_days": 0},
                         heat_rank=10, source="auto", seat="burning")
    assert card["flags"]["tml"] is True and card["state"] == "Leading"
    assert len(card["series"]["c"]) == 130 and card["heat"]["rank"] == 10
    payload = {"date": "2026-08-19", "cards": [card]}
    p = tmp_path / "log.csv"
    assert NC.archive(payload, path=p) == 1
    NC.archive(payload, path=p)
    import csv
    assert len(list(csv.DictReader(p.open()))) == 1     # idempotent per date


def test_v_reversal_prefers_fresh_high_pullback(tmp_path=None):
    """Andy 2026-08-20: 'pullback 的 V 反也是要的！特别是出新52wh后回撤的' --
    the fresh-high pullback outranks the deep-bottom V when both qualify."""
    wl = _wl({
        "ma_reclaim": {"DEEPV": {}}.items(),
        "liquid_leader_pullback": {"FRESH": {}, "STALEHI": {}}.items(),
    })
    by = {"FRESH": {"high_52w": -0.08, "days_since_52wh": 12, "rs_3m": 85, "atr_from_sma50": 1.5},
          "STALEHI": {"high_52w": -0.08, "days_since_52wh": 200, "rs_3m": 99, "atr_from_sma50": 1.5},
          "DEEPV": {"high_52w": -0.40, "rs_3m": 80, "atr_from_sma50": 1.0}}
    seats = NC.pick_seats(wl, None, [], [], by)
    got = {s["seat"]: s for s in seats}
    assert got["v_reversal"]["ticker"] == "FRESH" and "新高后回踩" in got["v_reversal"]["why"]
    # without the fresh-high candidate, the deep V takes the seat
    by2 = dict(by); by2["FRESH"] = {**by["FRESH"], "high_52w": -0.30}
    seats2 = NC.pick_seats(wl, None, [], [], by2)
    got2 = {s["seat"]: s["ticker"] for s in seats2}
    assert got2["v_reversal"] in ("DEEPV", "FRESH")  # FRESH now deep too, rs_3m ties break
    # proxy path when days_since_52wh is absent (tonight's field): within 15% passes
    by3 = {"NOFLD": {"high_52w": -0.10, "rs_3m": 85, "atr_from_sma50": 1.5}}
    seats3 = NC.pick_seats(_wl({"liquid_leader_pullback": {"NOFLD": {}}.items()}), None, [], [], by3)
    assert {s["seat"]: s["ticker"] for s in seats3}["v_reversal"] == "NOFLD"


def test_coiling_seat_prefers_3wt_then_coil_then_vcs():
    """v3 (Andy): 3WT/COIL lead; VCS demoted to third but kept for comparison."""
    wl = _wl({"vcs": {"VCSX": {}}.items()})
    gate = dict(market_cap=5e9, avg_volume=5e6, close=100.0)
    by = {"TW": {"three_weeks_tight": True, "sma50_dist": 0.1, "high_52w": -0.05, "rs_3m": 90,
                 "atr_from_sma50": 2.0, **gate},
          "CO": {"range5_pct": 3.0, "dist_hi20_pct": -1.0, "sma50_dist": 0.1,
                 "atr_from_sma50": 2.0, **gate},
          "VCSX": {"vcs": 88, "atr_from_sma50": 2.0, **gate},
          "SMALL": {"three_weeks_tight": True, "sma50_dist": 0.1, "high_52w": -0.05, "rs_3m": 99,
                    "atr_from_sma50": 1.0, "market_cap": 5e8, "avg_volume": 5e6, "close": 100.0}}
    got = {x["seat"]: x for x in NC.pick_seats(wl, None, [], [], by)}
    assert got["coiling"]["ticker"] == "TW" and "3周紧" in got["coiling"]["why"]   # SMALL fails the gate
    by2 = dict(by); by2["TW"] = {**by["TW"], "three_weeks_tight": False}
    got2 = {x["seat"]: x for x in NC.pick_seats(wl, None, [], [], by2)}
    assert got2["coiling"]["ticker"] == "CO" and "coil" in got2["coiling"]["why"]
    by3 = dict(by2); by3["CO"] = {**by2["CO"], "range5_pct": 9.0}
    got3 = {x["seat"]: x for x in NC.pick_seats(wl, None, [], [], by3)}
    assert got3["coiling"]["ticker"] == "VCSX" and "对照" in got3["coiling"]["why"]
