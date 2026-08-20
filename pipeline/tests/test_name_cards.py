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


def test_pick_seats_deterministic_and_empty_seats_stay_empty():
    wl = _wl({
        "true_market_leaders": {"NEW": {}, "OLD": {}}.items(),
        "episodic_pivot": {"EPX": {}}.items(),
        "ma_reclaim": {"DEEP": {}, "SHAL": {}}.items(),
        "vcs": {"COIL": {}}.items(),
        "bullish_4pct": {}.items(),
    })
    prev = _wl({"true_market_leaders": {"OLD": {}}.items()})
    by = {"NEW": {"h_score": 90}, "DEEP": {"high_52w": -0.40, "rs_3m": 80},
          "SHAL": {"high_52w": -0.05, "rs_3m": 99}, "COIL": {"vcs": 80}}
    heat = [{"ticker": "HOT", "score": 12.0, "confluence_days": 1}]
    assets = [{"ticker": "GLD", "rs_line_pctl_21": 100.0, "hi20": True}]
    seats = NC.pick_seats(wl, prev, heat, assets, by)
    got = {s["seat"]: s["ticker"] for s in seats}
    assert got == {"burning": "HOT", "new_leader": "NEW", "entry": "EPX",
                   "v_reversal": "DEEP", "coiling": "COIL", "asset": "GLD"}
    # no qualifiers -> seats empty, never invented
    seats2 = NC.pick_seats(_wl({}), None, [], [], {})
    assert all(s["ticker"] is None for s in seats2) and len(seats2) == 6


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
