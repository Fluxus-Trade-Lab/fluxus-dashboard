"""Tests for the nightly watchlist builder (pipeline/screeners/watchlist.py).

The Watchlist page is the morning briefing: zones = the questions a trader
asks after the close, panels = the signals that answer them, computed once a
night from universe.json so the browser renders instead of filtering. The
Screener page stays the workbench where recipes are edited. Where a panel and
a Screener preset are the same recipe, a test here pins them equal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.screeners import watchlist as W


def row(**kw):
    base = {"ticker": "T", "market_cap": 5e9, "avg_volume": 5e6, "sector": "Technology",
            "rs_1m": 90, "h_score": 85, "adr_pct": 4.5, "trend_base": True,
            "sp_setup": True, "sp_signal": None, "sp_days": 3, "pp_count_10d": 0,
            "vcs": 30.0, "atr_from_sma50": 2.0, "ti65": 1.0, "c_low52w": 1.2, "mdt": 1.0,
            "change_pct": 0.005, "perf_1w_pctile": 0.5, "perf_3m_pctile": 0.5,
            "perf_1w": 0.02, "rel_volume": 1.0, "from_open_pct": 0.0, "rs_21d": 90,
            "dcr_pct": 0.5, "min_vol_3d": 500_000, "ema21_atr_dist": 0.5,
            "pocket_pivot": False, "pp_count_30d": 0, "liquid_leader": False, "close": 100.0}
    base.update(kw)
    return base


class TestGate:
    def test_universe_gate_is_oratneks(self):
        """$1B cap and 1M average volume, like his 'Today's Watchlist' premise."""
        assert W.passes_gate(row()) is True
        assert W.passes_gate(row(market_cap=9e8)) is False
        assert W.passes_gate(row(avg_volume=9e5)) is False
        assert W.passes_gate(row(market_cap=None)) is False


class TestPanels:
    def test_structure_panels_read_sp_signal(self):
        assert W.PANELS["ll_hl_1st"].test(row(sp_signal="1st_break"))
        assert not W.PANELS["ll_hl_1st"].test(row(sp_signal="2nd_break"))
        assert W.PANELS["ll_hl_2nd"].test(row(sp_signal="2nd_break"))
        assert W.PANELS["ll_hl_trend_break"].test(row(sp_signal="counter_break"))

    def test_pp_panels(self):
        assert W.PANELS["pp_today"].test(row(pocket_pivot=True))
        assert not W.PANELS["pp_today"].test(row(pocket_pivot=False, pp_count_10d=3))
        assert W.PANELS["pp_2plus_10d"].test(row(pp_count_10d=2))
        assert not W.PANELS["pp_2plus_10d"].test(row(pp_count_10d=1))

    def test_vcs_panel_needs_the_adr_floor(self):
        """Pinned takeover names score VCS 90+ with ADR under 2 -- not
        compression. The panel carries the same floor as the anticipation
        tool."""
        assert W.PANELS["vcs"].test(row(vcs=75, adr_pct=4.0))
        assert not W.PANELS["vcs"].test(row(vcs=95, adr_pct=1.0))
        assert not W.PANELS["vcs"].test(row(vcs=65, adr_pct=4.0))

    def test_anticipation_panel(self):
        assert W.PANELS["anticipation"].test(row(vcs=65, ti65=1.06, change_pct=0.004))
        assert not W.PANELS["anticipation"].test(row(vcs=65, ti65=1.06, change_pct=0.03))   # not quiet
        assert not W.PANELS["anticipation"].test(row(vcs=65, ti65=1.0, c_low52w=1.2, mdt=1.0))  # not strong

    def test_trouble_panels(self):
        assert W.PANELS["stop_hit"].test(row(sp_signal="stop_hit"))
        assert W.PANELS["ll_break"].test(row(sp_signal="ll_break"))
        assert W.PANELS["extended"].test(row(atr_from_sma50=7.5))
        assert not W.PANELS["extended"].test(row(atr_from_sma50=6.9))

    def test_momentum_panels_match_the_screener_presets(self):
        """Weekly Momentum 97 / 4% Bullish / Weekly 20%+ Gainers are the same
        recipes as screener-presets.json. Assert the numbers, read from the
        file, so the two cannot drift silently."""
        presets = {p["name"]: p["filters"] for p in
                   json.loads(Path("frontend/public/data/screener-presets.json").read_text())}
        wm = presets["Weekly Momentum 97"]
        assert W.PANELS["weekly_momentum_97"].test(
            row(perf_1w_pctile=wm["perf1wPctile"]["min"], perf_3m_pctile=wm["perf3mPctile"]["min"],
                adr_pct=wm["adrPct"]["min"]))
        assert not W.PANELS["weekly_momentum_97"].test(
            row(perf_1w_pctile=wm["perf1wPctile"]["min"] - 0.01, perf_3m_pctile=0.9))
        b4 = presets["4% Bullish"]
        assert W.PANELS["bullish_4pct"].test(
            row(change_pct=b4["dailyPct"]["min"] / 100, rel_volume=b4["relVolume"]["min"],
                from_open_pct=0.0, rs_21d=b4["rs21d"]["min"], adr_pct=b4["adrPct"]["min"]))
        assert not W.PANELS["bullish_4pct"].test(row(change_pct=0.03, rel_volume=2, rs_21d=90))
        w20 = presets["Weekly 20%+ Gainers"]
        assert W.PANELS["weekly_20_gainers"].test(row(perf_1w=w20["weeklyPct"]["min"] / 100, adr_pct=4))
        assert not W.PANELS["weekly_20_gainers"].test(row(perf_1w=0.19, adr_pct=4))


class TestLeaders:
    def test_liquid_leader_pullback_is_the_course_recipe(self):
        """M2_L09 'Liquid Leader Pullback RS': liquid leader, weekly return
        < 12%, 0.5-1 ADR from the 21EMA, 0-3 ADR from the 50 (ADR ~ ATR here)."""
        good = row(liquid_leader=True, perf_1w=0.05, ema21_atr_dist=0.7, atr_from_sma50=1.5)
        assert W.PANELS["liquid_leader_pullback"].test(good)
        assert not W.PANELS["liquid_leader_pullback"].test(row(**{**good, "liquid_leader": False}))
        assert not W.PANELS["liquid_leader_pullback"].test(row(**{**good, "perf_1w": 0.15}))
        assert not W.PANELS["liquid_leader_pullback"].test(row(**{**good, "ema21_atr_dist": 1.5}))
        assert not W.PANELS["liquid_leader_pullback"].test(row(**{**good, "atr_from_sma50": 3.5}))

    def test_true_market_leader_needs_a_leading_group(self):
        """TML = liquid leader whose home theme/industry is Leading and rs_1m >= 80
        -- the theme dimension none of the four benchmarks have."""
        r = row(ticker="X", liquid_leader=True, rs_1m=90)
        out = W.build([r], date="2026-08-14", group_states={"X": ("Software", "Leading")})
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}
        assert [x["ticker"] for x in p["true_market_leaders"]["tickers"]] == ["X"]
        assert p["true_market_leaders"]["tickers"][0]["group"] == "Software"
        out2 = W.build([r], date="2026-08-14", group_states={"X": ("Software", "Weakening")})
        p2 = {pn["key"]: pn for z in out2["zones"] for pn in z["panels"]}
        assert p2["true_market_leaders"]["tickers"] == []
        # no group map at all -> unmeasured, not empty-and-false
        out3 = W.build([r], date="2026-08-14")
        p3 = {pn["key"]: pn for z in out3["zones"] for pn in z["panels"]}
        assert p3["true_market_leaders"]["measured"] is False

    def test_leaders_zone_comes_first(self):
        out = W.build([row()], date="2026-08-14")
        assert out["zones"][0]["key"] == "leaders"

    def test_leaders_archive_rows(self, tmp_path):
        r = row(ticker="X", liquid_leader=True, rs_1m=90, h_score=88, close=123.4)
        n = W.archive_leaders([r], date="2026-08-14", group_states={"X": ("Software", "Leading")},
                              path=tmp_path / "log.csv")
        assert n == 1
        import csv
        rows_ = list(csv.DictReader((tmp_path / "log.csv").open()))
        assert rows_[0]["ticker"] == "X" and rows_[0]["tml"] == "True" and rows_[0]["group_state"] == "Leading"
        # idempotent per date
        assert W.archive_leaders([r], date="2026-08-14", group_states={}, path=tmp_path / "log.csv") == 1
        assert len(list(csv.DictReader((tmp_path / "log.csv").open()))) == 1


class TestBuild:
    def _rows(self):
        return [
            row(ticker="A", sp_signal="1st_break", rs_1m=95, h_score=90),
            row(ticker="B", sp_signal="2nd_break", pp_count_10d=2, rs_1m=99, h_score=95),
            row(ticker="C", vcs=80, ti65=1.08, change_pct=0.002, rs_1m=70, h_score=60),
            row(ticker="D", perf_1w=0.25, perf_1w_pctile=0.99, perf_3m_pctile=0.9,
                change_pct=0.05, rel_volume=2.0, rs_21d=95, rs_1m=100, h_score=88),
            row(ticker="E", market_cap=5e8, sp_signal="1st_break"),      # under the gate
            row(ticker="F", sp_signal="stop_hit", rs_1m=40, h_score=50),
        ]

    def test_panels_carry_tickers_with_rs1m_sorted_by_hybrid_rs(self):
        out = W.build(self._rows(), date="2026-08-14")
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}
        assert [t["ticker"] for t in p["ll_hl_1st"]["tickers"]] == ["A"]        # E is under the gate
        assert p["ll_hl_1st"]["tickers"][0]["rs_1m"] == 95
        # D is in three 'moving' panels but they are ONE zone: cross-zone count 1
        assert [t["ticker"] for t in p["weekly_20_gainers"]["tickers"]] == ["D"]

    def test_cross_zone_count_counts_zones_not_panels(self):
        """'In 3+ watchlists' on oratnek's page mostly counts synonyms
        (Momentum 97 / 4% bullish / Weekly 20% all say 'moving'). Ours counts
        the ZONES a name is in -- entries x accumulation x compression x
        moving -- so a hit means different questions agree."""
        out = W.build(self._rows(), date="2026-08-14")
        cross = {c["ticker"]: c for c in out["cross_zone"]}
        assert cross["B"]["zones"] == ["entries", "accumulation"]     # 1st/2nd pivot + PP 2+
        assert cross["B"]["count"] == 2
        assert "D" not in cross          # three panels, ONE zone -> no cross-zone credit
        assert "E" not in cross

    def test_zone_order_and_keys_are_stable(self):
        out = W.build(self._rows(), date="2026-08-14")
        assert [z["key"] for z in out["zones"]] == ["leaders", "entries", "compression", "accumulation", "moving", "trouble"]
        for z in out["zones"]:
            for pn in z["panels"]:
                assert {"key", "label", "recipe", "count", "tickers"} <= set(pn)

    def test_missing_fields_are_unmeasured_not_false_positive(self):
        """Before the first cron with sp_* the column is absent: the structure
        panels must be empty and marked unmeasured, not silently zero."""
        rows = [{k: v for k, v in row(ticker="A").items() if not k.startswith("sp_")}]
        out = W.build(rows, date="2026-08-14")
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}
        assert p["ll_hl_1st"]["tickers"] == [] and p["ll_hl_1st"]["measured"] is False
        assert p["pp_today"]["measured"] is True

    def test_json_safe(self):
        out = W.build(self._rows(), date="2026-08-14")
        json.dumps(out)     # no NaN, no numpy
