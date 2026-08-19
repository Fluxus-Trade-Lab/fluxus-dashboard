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
            "pocket_pivot": False, "pp_count_30d": 0, "liquid_leader": False, "close": 100.0,
            "vol10_green": False, "vol10_green_count_10d": 0, "perf_5d": 0.02, "rs_line_pctl_21": 60}
    base.update(kw)
    return base


class TestGate:
    def test_universe_gate_is_oratneks(self):
        """$1B cap and 1M average volume, like his 'Today's Watchlist' premise."""
        assert W.passes_gate(row()) is True
        assert W.passes_gate(row(market_cap=9e8)) is False
        # dollar volume, not shares: 862k x $58 = $50M passes; 1.1M x $2 = $2M does not
        assert W.passes_gate(row(avg_volume=862_000, close=58.0)) is True
        assert W.passes_gate(row(avg_volume=1_100_000, close=2.0)) is False
        assert W.passes_gate(row(close=None)) is False
        assert W.passes_gate(row(market_cap=None)) is False


class TestPanels:
    def test_structure_panels_read_sp_signal(self):
        assert W.PANELS["ll_hl_1st"].test(row(sp_signal="1st_break"))
        assert not W.PANELS["ll_hl_1st"].test(row(sp_signal="2nd_break"))
        assert W.PANELS["ll_hl_2nd"].test(row(sp_signal="2nd_break"))
        assert W.PANELS["ll_hl_trend_break"].test(row(sp_signal="counter_break"))

    def test_pp_panels(self):
        """oratnek's two PP panels read the vol10_green family (his definition);
        the Morales pocket pivot is its own panel."""
        assert W.PANELS["pp_today"].test(row(vol10_green=True))
        assert not W.PANELS["pp_today"].test(row(vol10_green=False, pocket_pivot=True))
        assert W.PANELS["pp_2plus_10d"].test(row(vol10_green_count_10d=2))
        assert not W.PANELS["pp_2plus_10d"].test(row(vol10_green_count_10d=1))
        # Morales: three pivots in ten sessions (his cluster), not one
        assert W.PANELS["morales_pp_10d"].test(row(pp_count_10d=3))
        assert not W.PANELS["morales_pp_10d"].test(row(pp_count_10d=2))
        assert not W.PANELS["morales_pp_10d"].test(row(pp_count_10d=0, vol10_green_count_10d=3))
        # context gate: no trend_base, no panel -- the study's loudest finding
        assert not W.PANELS["pp_today"].test(row(vol10_green=True, trend_base=False))
        assert not W.PANELS["morales_pp_10d"].test(row(pp_count_10d=3, trend_base=False))

    def test_vcs_panel_needs_the_adr_floor(self):
        """Pinned takeover names score VCS 90+ with ADR under 2 -- not
        compression. The panel carries the same floor as the anticipation
        tool."""
        # compression inside a leader: vcs>=60, rs_3m>=80, above SMA50, ADR floor
        assert W.PANELS["vcs"].test(row(vcs=62, adr_pct=4.0, rs_3m=88, sma50_dist=0.1))
        assert not W.PANELS["vcs"].test(row(vcs=95, adr_pct=1.0, rs_3m=88, sma50_dist=0.1))   # ADR floor
        assert not W.PANELS["vcs"].test(row(vcs=95, adr_pct=4.0, rs_3m=40, sma50_dist=0.1))   # not a leader
        assert not W.PANELS["vcs"].test(row(vcs=95, adr_pct=4.0, rs_3m=88, sma50_dist=-0.05)) # below SMA50
        assert not W.PANELS["vcs"].test(row(vcs=55, adr_pct=4.0, rs_3m=88, sma50_dist=0.1))

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
        # same threshold as the preset; the WINDOW is five sessions (perf_5d),
        # not Finviz's calendar week -- by design since 2026-08-18
        assert W.PANELS["weekly_20_gainers"].test(row(perf_5d=w20["weeklyPct"]["min"] / 100, adr_pct=4))
        assert not W.PANELS["weekly_20_gainers"].test(row(perf_5d=0.19, adr_pct=4))
        assert not W.PANELS["weekly_20_gainers"].test(row(perf_1w=0.5, adr_pct=4))   # perf_1w no longer read


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
            row(ticker="B", sp_signal="2nd_break", vol10_green_count_10d=2, vcs=90, adr_pct=4.0,
                rs_3m=90, sma50_dist=0.1, rs_1m=99, h_score=95),   # entries x accumulation x compression
            row(ticker="C", vcs=80, ti65=1.08, change_pct=0.002, rs_1m=70, h_score=60),
            row(ticker="D", perf_1w=0.25, perf_5d=0.25, perf_1w_pctile=0.99, perf_3m_pctile=0.9,
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
        assert cross["B"]["zones"] == ["entries", "compression", "accumulation"]   # 2nd pivot + VCS + PP 2+
        assert cross["B"]["count"] == 3
        assert "A" not in cross          # one zone
        assert "D" not in cross          # three panels, ONE zone -> no cross-zone credit
        assert out["cross_zone_rule"].endswith(">= 3 listed")
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


class TestRsHighDetection:
    def test_rs_high_is_a_flag_and_a_count_not_a_filter(self):
        rows = [row(ticker="A", sp_signal="1st_break", rs_line_pctl_21=100),
                row(ticker="B", sp_signal="1st_break", rs_line_pctl_21=81),
                row(ticker="C", sp_signal="1st_break", rs_line_pctl_21=None)]
        out = W.build(rows, date="2026-08-14")
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}["ll_hl_1st"]
        assert p["count"] == 3 and p["count_rs_high"] == 1          # nobody filtered out
        flags = {t["ticker"]: t["rs_high"] for t in p["tickers"]}
        assert flags == {"A": True, "B": False, "C": False}
        assert "rs_high_rule" in out


class TestTop3mDetection:
    def test_top_3m_is_a_flag_and_a_count_not_a_filter(self):
        rows = [row(ticker="A", sp_signal="1st_break", perf_3m_pctile=0.9),
                row(ticker="B", sp_signal="1st_break", perf_3m_pctile=0.5),
                row(ticker="C", sp_signal="1st_break", perf_3m_pctile=None)]
        out = W.build(rows, date="2026-08-14")
        p = {pn["key"]: pn for z in out["zones"] for pn in z["panels"]}["ll_hl_1st"]
        assert p["count"] == 3 and p["count_top_3m"] == 1
        assert {t["ticker"]: t["top_3m"] for t in p["tickers"]} == {"A": True, "B": False, "C": False}
        assert "top_3m_rule" in out


class TestMaReclaimAndChase:
    """2026-08-19, from the scanner validation playbook."""

    def test_ma_reclaim_needs_a_cross_and_volume(self):
        p = W.PANELS["ma_reclaim"]
        assert p.test(row(cross_ema21_up=True, rel_volume=1.0))
        assert p.test(row(cross_sma50_up=True, cross_ema21_up=False, rel_volume=1.4))
        assert not p.test(row(cross_ema21_up=True, rel_volume=0.7))
        assert not p.test(row(cross_ema21_up=False, cross_sma50_up=False, rel_volume=2.0))
        assert not p.test(row(cross_ema21_up=None, cross_sma50_up=None, rel_volume=2.0))

    def test_ma_reclaim_is_first_in_entries_and_unmeasured_without_fields(self):
        assert [z for z in W.ZONES if z["key"] == "entries"][0]["panels"][0] == "ma_reclaim"
        wl = W.build([row()], date="2026-08-19")   # row() has no cross_* keys
        panel = {p["key"]: p for z in wl["zones"] for p in z["panels"]}["ma_reclaim"]
        assert panel["measured"] is False and panel["count"] == 0

    def test_entries_carry_chg_pct_and_chase(self):
        wl = W.build([row(ticker="HOT", change_pct=0.171, rel_volume=1.2, from_open_pct=0.01),
                      row(ticker="OK", change_pct=0.052, rel_volume=1.2, from_open_pct=0.01)],
                     date="2026-08-19")
        panel = {p["key"]: p for z in wl["zones"] for p in z["panels"]}["bullish_4pct"]
        assert panel["count"] == 2 and panel["count_chase"] == 1
        by = {t["ticker"]: t for t in panel["tickers"]}
        assert by["HOT"]["chase"] is True and by["HOT"]["chg_pct"] == 17.1
        assert by["OK"]["chase"] is False and by["OK"]["chg_pct"] == 5.2
        assert by["OK"]["atr_from_sma50"] == 2.0
        assert "chase_rule" in wl

    def test_archive_panel_hits_logs_every_hit_idempotently(self, tmp_path):
        rows = [row(ticker=f"T{i}", change_pct=0.06, rel_volume=1.2, from_open_pct=0.01) for i in range(30)]
        wl = W.build(rows, date="2026-08-19")
        path = tmp_path / "hits.csv"
        n = W.archive_panel_hits(wl, rows, path=path)
        import csv
        got = list(csv.DictReader(path.open()))
        b4 = [r for r in got if r["panel"] == "bullish_4pct"]
        assert len(b4) == 30 > W.MAX_PER_PANEL          # whole list, not the page's 25
        assert b4[0]["zone"] == "moving" and b4[0]["chg_pct"] == "6.0"
        assert n == len(got)
        # same date again replaces, does not duplicate
        W.archive_panel_hits(wl, rows, path=path)
        assert len(list(csv.DictReader(path.open()))) == n
        # a second date appends
        wl2 = W.build(rows[:5], date="2026-08-20")
        W.archive_panel_hits(wl2, rows[:5], path=path)
        assert len(list(csv.DictReader(path.open()))) > n


class TestPresetTwinsExcludeHealthcare:
    """screener-presets.json carries excludeHealthcare on all three twins;
    08-18 vs oratnek: our Momentum 97 was five biotechs of seven, his eleven had none."""

    def test_three_twins_drop_healthcare(self):
        hot = dict(perf_1w_pctile=0.99, perf_3m_pctile=0.9, change_pct=0.05, rel_volume=1.2,
                   from_open_pct=0.01, perf_5d=0.25)
        for k in ("weekly_momentum_97", "bullish_4pct", "weekly_20_gainers"):
            assert W.PANELS[k].test(row(**hot)), k
            assert not W.PANELS[k].test(row(sector="Healthcare", **hot)), k


def test_momentum97_shadow_logs_both_recipes(tmp_path):
    rows = [row(ticker="A", perf_1w_pctile=0.99, perf_3m_pctile=0.9, rs_line_pctl_63=80.0),
            row(ticker="B", perf_1w_pctile=0.80, perf_3m_pctile=0.9, rs_line_pctl_63=98.4, perf_1w=0.03),
            row(ticker="H", sector="Healthcare", perf_1w_pctile=0.99, rs_line_pctl_63=100.0)]
    p = tmp_path / "s.csv"
    n = W.archive_momentum97_shadow(rows, date="2026-08-19", path=p)
    import csv
    got = {(r["recipe"], r["ticker"]) for r in csv.DictReader(p.open())}
    assert ("ours_1w97", "A") in got and ("rs63_97", "B") in got and ("rs63_97_green", "B") in got
    assert not any(t == "H" for _, t in got) and n == len(got)
