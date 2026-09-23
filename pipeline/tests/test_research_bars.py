"""The alignment check that 2026-09-23's theme study went without."""
import pandas as pd
import pytest

from pipeline.tools import research_bars as RB


def _s(dates, vals=None):
    idx = pd.to_datetime(dates)
    return pd.Series(vals or range(len(idx)), index=idx, dtype=float)


THROUGH = "2026-09-22"


def test_align_report_sorts_symbols_into_four_buckets():
    series = {
        "OK": _s(["2026-09-19", "2026-09-22"]),
        "STALE": _s(["2026-09-18", "2026-09-21"]),
        "AHEAD": _s(["2026-09-22", "2026-09-23"]),
        "EMPTY": _s([]),
    }
    r = RB.align_report(series, THROUGH)
    assert r == {"ok": ["OK"], "stale": ["STALE"], "ahead": ["AHEAD"], "empty": ["EMPTY"]}


def test_require_through_raises_on_a_stale_benchmark():
    series = {"SPY": _s(["2026-09-21"]), "NVDA": _s(["2026-09-22"])}
    with pytest.raises(ValueError) as exc:
        RB.require_through(series, THROUGH, must=["SPY"])
    assert "SPY" in str(exc.value) and THROUGH in str(exc.value)


def test_require_through_passes_when_the_named_symbols_are_aligned():
    series = {"SPY": _s(["2026-09-22"]), "SMALL": _s(["2026-09-19"])}
    r = RB.require_through(series, THROUGH, must=["SPY"])
    assert r["stale"] == ["SMALL"]          # reported, not fatal


def test_merge_series_takes_the_fallback_only_for_short_symbols():
    primary = {"A": _s(["2026-09-19", "2026-09-21"]), "B": _s(["2026-09-22"], [7.0])}
    fallback = {"A": _s(["2026-09-19", "2026-09-22"], [1.0, 2.0]),
                "B": _s(["2026-09-22"], [99.0])}
    out = RB.merge_series(primary, fallback, THROUGH)
    assert str(out["A"].index[-1].date()) == THROUGH
    assert out["B"].iloc[-1] == 7.0, "aligned symbols keep the primary source"


def test_merge_series_trims_a_fallback_that_runs_past_the_session():
    primary = {"A": _s(["2026-09-21"])}
    fallback = {"A": _s(["2026-09-21", "2026-09-22", "2026-09-23"])}
    out = RB.merge_series(primary, fallback, THROUGH)
    assert str(out["A"].index[-1].date()) == THROUGH


def test_merge_series_leaves_a_symbol_the_fallback_cannot_fix():
    primary = {"A": _s(["2026-09-21"])}
    out = RB.merge_series(primary, {"A": _s(["2026-09-21"])}, THROUGH)
    assert str(out["A"].index[-1].date()) == "2026-09-21"
