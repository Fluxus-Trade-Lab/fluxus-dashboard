"""preset_hits is a port of frontend/src/lib/screenerFilter.js; the presets
file the page reads is the fixture, so the two cannot drift silently."""

from __future__ import annotations

import math

import numpy as np

from pipeline.screeners import preset_hits as P
from pipeline.screeners.ticker_events import EVENT_COLUMNS


def row(**kw):
    base = {"ticker": "T", "market_cap": 5e9, "avg_volume": 12e6, "sector": "Technology",
            "change_pct": 0.05, "rel_volume": 1.6, "from_open_pct": 0.01, "rs_21d": 98,
            "adr_pct": 4.5, "trend_base": True, "pocket_pivot": True, "pp_count_30d": 3,
            "perf_1w": 0.12, "perf_1w_pctile": 0.98, "perf_3m_pctile": 0.9, "h_score": 90,
            "dcr_pct": 0.8, "ema21_atr_dist": 0.5, "atr_from_sma50": 1.5,
            "bo_count_1y": 12, "bo_count_3m": 3, "volume": 20e6}
    base.update(kw)
    return base


def test_presets_file_loads_and_slugs_are_stable():
    ps = P.load_presets()
    names = {p["name"] for p in ps}
    assert {"Sugar Babies", "Monthly Leader 97", "Vol Up Gainers", "Stockbee 9M Setup"} <= names
    assert P.slug("Weekly 20%+ Gainers") == "preset:weekly_20_gainers"
    assert P.slug("Stockbee 9M Setup") == "preset:stockbee_9m_setup"


# One strong row nearly fits every preset; the two that disagree on the weekly
# move (21EMA Watch caps it at 15%, Weekly 20%+ needs 20%) get the override.
_FIT = {"Weekly 20%+ Gainers": {"perf_1w": 0.25}}


def test_every_shipped_preset_matches_a_strong_row_and_rejects_healthcare():
    ps = {p["name"]: p["filters"] for p in P.load_presets()}
    for name, f in ps.items():
        fit = _FIT.get(name, {})
        assert P.passes(row(**fit), f), name
        assert not P.passes(row(sector="Healthcare", **fit), f), name


def test_range_semantics_mirror_the_page():
    f = {"dailyPct": {"enabled": True, "min": 4, "max": 999}}   # page compares whole %
    assert P.passes(row(change_pct=0.04), f)
    assert not P.passes(row(change_pct=0.039), f)
    assert not P.passes(row(change_pct=None), f)               # null fails an enabled range
    assert P.passes(row(change_pct=None), {"dailyPct": {"enabled": False, "min": 4}})
    f = {"marketCapMin": 1.0}
    assert not P.passes(row(market_cap=9e8), f)
    assert P.passes(row(market_cap=9e8), {"marketCapMin": 1.0, "marketCapEnabled": False})
    f = {"vol50dMin": 9.0}
    assert P.passes(row(avg_volume=9e6), f) and not P.passes(row(avg_volume=8.9e6), f)
    f = {"ppCount": {"enabled": True, "min": 3, "max": 999}}
    assert P.passes(row(pp_count_30d=3), f) and not P.passes(row(pp_count_30d=2), f)


def test_flags_accept_numpy_bools_and_reject_nan():
    f = {"trendBaseOnly": True}
    assert P.passes(row(trend_base=np.bool_(True)), f)
    assert not P.passes(row(trend_base=np.bool_(False)), f)
    assert not P.passes(row(trend_base=float("nan")), f)
    assert not P.passes(row(trend_base=None), f)
    # NaN numerics fail an enabled range instead of comparing
    assert not P.passes(row(change_pct=math.nan), {"dailyPct": {"enabled": True, "min": 4}})


def test_extract_events_shape():
    ps = [{"name": "Sugar Babies", "filters": {"boCount1y": {"enabled": True, "min": 10}}}]
    ev = P.extract_preset_events([row(ticker="A"), row(ticker="B", bo_count_1y=2)], ps, "2026-08-19")
    assert [e["ticker"] for e in ev] == ["A"]
    assert ev[0]["screener"] == "preset:sugar_babies" and ev[0]["date"] == "2026-08-19"
    assert set(ev[0]) == set(EVENT_COLUMNS)


def test_backfill_merge_replaces_only_preset_rows_for_the_date():
    import pandas as pd
    from pipeline.tools.backfill_preset_hits import merge_preset_rows
    frame = pd.DataFrame([
        {"date": "2026-08-01", "ticker": "A", "screener": "gainers_4pct"},
        {"date": "2026-08-01", "ticker": "A", "screener": "preset:sugar_babies"},
        {"date": "2026-07-31", "ticker": "B", "screener": "preset:sugar_babies"},
    ]).reindex(columns=EVENT_COLUMNS)
    out = merge_preset_rows(frame, [{"date": "2026-08-01", "ticker": "C", "screener": "preset:pp_count"}])
    keys = set(zip(out.date, out.ticker, out.screener))
    assert ("2026-08-01", "A", "gainers_4pct") in keys          # core row kept
    assert ("2026-08-01", "A", "preset:sugar_babies") not in keys  # that date's presets replaced
    assert ("2026-08-01", "C", "preset:pp_count") in keys
    assert ("2026-07-31", "B", "preset:sugar_babies") in keys   # other date untouched
