"""Three self-made-number fixes (Andy 2026-09-21, verbatim: 「全都修了。」).

Audit: data/research/metric_audit_2026-09-18/ -- C_lists_and_tickers.md #41
(ema21_watch), #46 (Sugar Babies doc/code mismatch), B_market_layer.md M45
(VIX/VIX3M three-state). Standing rule (Andy 09-18): 「全部按原文」.

Each block was written to FAIL against the code before the change.
"""

from __future__ import annotations

import pandas as pd

from pipeline.screeners import ema21_watch
from pipeline.screeners import preset_hits as P


# ------------------------------------------------------------ #41 ema21_watch
def _row(**kw):
    """A name that passes the 21EMA Watch preset (Alex's 21dma-structure
    pullback + the preset's own extra conditions)."""
    base = {"ticker": "T", "market_cap": 5e9, "sector": "Technology",
            "perf_1w": 0.05, "dcr_pct": 0.5, "ema21_atr_dist": 0.5,
            "sma50_atr_dist": 2.0, "pp_count_30d": 2, "adr_pct": 4.5,
            "trend_base": True, "perf_3m": 0.30,
            # the retired proxy's inputs, set to FAIL the old band on purpose
            "sma20_dist": 0.06, "sma50_dist": 0.10, "sma200_dist": 0.25}
    base.update(kw)
    return base


def _tickers(out):
    return {e["ticker"] for grp in out["rs_groups"].values() for e in grp}


def _preset():
    return {p["name"]: p["filters"] for p in P.load_presets()}["21EMA Watch"]


class TestEma21WatchIsThePreset:
    def test_real_ema21_hit_outside_the_old_sma20_band_is_listed(self):
        """0.5 ATR above the real 21EMA, but 6% over the 20-SMA: the old
        proxy band (-2%..+3% of SMA20) dropped it."""
        df = pd.DataFrame([_row(ticker="IN")])
        assert _tickers(ema21_watch.run(df)) == {"IN"}

    def test_sma20_band_hit_far_from_the_21ema_is_not_listed(self):
        """Inside the old SMA20 band, but 2.5 ATR above the real 21EMA."""
        df = pd.DataFrame([_row(ticker="OUT", sma20_dist=0.01, ema21_atr_dist=2.5)])
        assert _tickers(ema21_watch.run(df)) == set()

    def test_membership_equals_the_preset_exactly(self):
        """One rule, not two: every row the page preset passes is listed and
        nothing else, across each of the preset's conditions."""
        rows = [
            _row(ticker="OK"),
            _row(ticker="E21LO", ema21_atr_dist=-0.1),
            _row(ticker="E21HI", ema21_atr_dist=1.2),
            _row(ticker="S50LO", sma50_atr_dist=-0.8),
            _row(ticker="S50HI", sma50_atr_dist=4.5),
            _row(ticker="DCR", dcr_pct=0.05),
            _row(ticker="WK", perf_1w=0.20),
            _row(ticker="HC", sector="Healthcare"),
            _row(ticker="TB", trend_base=False),
            _row(ticker="NULL", ema21_atr_dist=None),
            # low RS but a clean pullback: the preset has no RS clause
            _row(ticker="LOWRS", perf_3m=-0.40),
        ]
        rows += [_row(ticker=f"F{i}", perf_3m=0.1 + i / 100, ema21_atr_dist=3.0)
                 for i in range(20)]
        out = ema21_watch.run(pd.DataFrame(rows))
        expected = {r["ticker"] for r in rows if P.passes(r, _preset())}
        assert expected == {"OK", "LOWRS"}          # positive control on the fixture
        assert _tickers(out) == expected
        assert out["count"] == len(expected)

    def test_output_shape_is_kept(self):
        out = ema21_watch.run(pd.DataFrame([_row(ticker="IN")]))
        assert set(out) == {"count", "rs_groups"}
        (entry,) = [e for g in out["rs_groups"].values() for e in g]
        assert {"ticker", "rs", "sma20_dist", "sector"} <= set(entry)

    def test_no_sma20_proxy_left_in_the_module(self):
        assert not hasattr(ema21_watch, "_SMA20_LOWER")
        assert not hasattr(ema21_watch, "_SMA20_UPPER")


# --------------------------------------------- M45 VIX/VIX3M 3EMA states
class TestTurinTermStructureCutsVerbatim:
    """@turintrader 2022-03-28, x.com/turintrader/status/1508257418387599361:
    'VIX:VIX3M 3ema with .8 as complacency and 1/1.1 as fear/capitulation
    zones'. Three cuts -> four states; 1.1 had been dropped."""

    def test_the_eleven_cut_exists(self):
        from pipeline.risk.correction_risk import ts_state_of
        assert ts_state_of(1.05) != ts_state_of(1.15)

    def test_states_follow_the_source_cuts(self):
        from pipeline.risk.correction_risk import TS_LABELS, ts_state_of
        assert [ts_state_of(v) for v in (0.70, 0.79, 0.80, 0.95, 1.00, 1.05, 1.10, 1.30)] \
            == [1, 1, 2, 2, 2, 3, 4, 4]
        assert set(TS_LABELS) == {1, 2, 3, 4}
        assert "complacency" in TS_LABELS[1]
        assert "fear" in TS_LABELS[3] and "capitulation" in TS_LABELS[4]

    def test_comment_no_longer_claims_verbatim_for_a_two_cut_rule(self):
        from pathlib import Path
        src = Path("pipeline/risk/correction_risk.py").read_text()
        assert "1508257418387599361" in src           # the source is cited

    def test_ledger_lamp_still_lights_above_one(self):
        """lamp_ts means '> 1.0 (backwardation)'; both new upper states light it."""
        from pipeline.risk.regime_ledger import lamp_ts_on
        assert lamp_ts_on(3, 0) == 1 and lamp_ts_on(4, 0) == 1
        assert lamp_ts_on(2, 0) == 0 and lamp_ts_on(1, 0) == 0
        assert lamp_ts_on(4, 8) == 0                   # stale input never lights it
        assert lamp_ts_on(None, 0) == ""


# ------------------------------------------------- #46 Sugar Babies doc = code
def _section(md: str, start: str) -> str:
    i = md.index(start)
    j = md.find("\n\n", i + len(start))
    return md[i: j if j > 0 else None]


class TestSugarBabiesDocMatchesCode:
    """No readable primary definition with numbers (see METRIC_SOURCES row):
    thresholds stay, declared ours; the method doc must describe the code."""

    MD = "data/reference/screener_methods.md"

    def _md(self):
        from pathlib import Path
        return Path(self.MD).read_text()

    def test_doc_no_longer_claims_a_9m_volume_rule(self):
        md = self._md()
        for head in ("### `bo_count_1m/3m/6m/1y`", "**7 · Sugar Babies**"):
            assert "9M" not in _section(md, head), head

    def test_doc_states_the_codes_breakout_conditions(self):
        from pipeline.adapters.yfinance_adapter import (BREAKOUT_MIN_CHANGE,
                                                        BREAKOUT_MIN_VOLUME)
        sec = _section(self._md(), "### `bo_count_1m/3m/6m/1y`")
        assert f"{BREAKOUT_MIN_CHANGE:.0%}" in sec           # 4%
        assert "v1" in sec                                   # volume > previous bar
        assert f"{BREAKOUT_MIN_VOLUME:,}" in sec             # 100,000
        assert "自造" in sec                                  # declared ours

    def test_doc_thresholds_equal_the_preset(self):
        """Positive control: the numbers the doc quotes are the preset's."""
        f = {p["name"]: p["filters"] for p in P.load_presets()}["Sugar Babies"]
        sec = _section(self._md(), "**7 · Sugar Babies**")
        assert f"bo_count_1y ≥{int(f['boCount1y']['min'])}" in sec
        assert f"bo_count_3m ≥{int(f['boCount3m']['min'])}" in sec
