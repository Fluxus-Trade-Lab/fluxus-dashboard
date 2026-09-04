"""vol_5d_50d computed from bars we already hold, instead of a second fetch.

The universe used to be downloaded twice a night: once at period=1y for the
enrichment columns, once at period=3mo for this one ratio. ~5,600 requests for
a number already sitting in the first panel. These tests pin the reuse:
the ratio must match the old path's arithmetic, names the panel cannot answer
must still reach the vendor, and a caller without a panel must behave exactly
as before.
"""
import pandas as pd
import pytest

from pipeline.screeners import volume_enrichment as ve


def _bars(volumes):
    """A frame shaped like the enrichment panel's per-ticker frame."""
    idx = pd.date_range("2026-01-01", periods=len(volumes), freq="B")
    return pd.DataFrame({
        "Open": [1.0] * len(volumes),
        "Close": [1.0] * len(volumes),
        "Volume": volumes,
    }, index=idx)


def test_ratio_from_panel_equals_ratio_from_series():
    """Reuse must not become a second, differently-rounded measurement."""
    vols = list(range(1, 121))
    panel = {"AAA": _bars(vols)}
    from_panel = ve.ratios_from_bars(["AAA"], panel)["AAA"]
    from_series = ve.ratio_from_volumes(pd.Series(vols, dtype=float))
    assert from_panel == from_series


def test_short_history_stays_unmeasured():
    """Fewer than fifty sessions has no fifty-day average -- None, not a ratio."""
    panel = {"NEW": _bars([100] * 12)}
    assert ve.ratios_from_bars(["NEW"], panel)["NEW"] is None


def test_names_absent_from_panel_are_not_answered():
    """A miss must fall through to the vendor, not silently become None.

    ratios_from_bars omits the key entirely; enrich_universe reads that
    omission as "still to fetch".
    """
    panel = {"AAA": _bars([100] * 60)}
    out = ve.ratios_from_bars(["AAA", "BBB"], panel)
    assert "AAA" in out and "BBB" not in out


def test_frame_without_volume_is_not_answered():
    panel = {"AAA": pd.DataFrame({"Close": [1.0] * 60})}
    assert ve.ratios_from_bars(["AAA"], panel) == {}


def test_enrich_universe_with_panel_makes_no_vendor_call(monkeypatch):
    """The whole point: a fully-covered panel means zero downloads."""
    calls = []
    monkeypatch.setattr(ve, "fetch_volume_ratios",
                        lambda names, **kw: calls.append(list(names)) or {})
    df = pd.DataFrame({"ticker": ["AAA", "BBB"]})
    panel = {"AAA": _bars(list(range(1, 61))),
             "BBB": _bars(list(range(1, 61)))}
    out = ve.enrich_universe(df, bars=panel)
    assert calls == []
    assert out["vol_5d_50d"].notna().all()


def test_enrich_universe_fetches_only_the_gap(monkeypatch):
    calls = []

    def fake_fetch(names, **kw):
        calls.append(list(names))
        return {t: 1.5 for t in names}

    monkeypatch.setattr(ve, "fetch_volume_ratios", fake_fetch)
    df = pd.DataFrame({"ticker": ["AAA", "BBB", "CCC"]})
    panel = {"AAA": _bars(list(range(1, 61)))}
    out = ve.enrich_universe(df, bars=panel)
    assert calls == [["BBB", "CCC"]]
    assert out.set_index("ticker")["vol_5d_50d"]["BBB"] == 1.5


def test_no_panel_behaves_exactly_as_before(monkeypatch):
    """The fallback universe path never runs the enrichment pass."""
    calls = []

    def fake_fetch(names, **kw):
        calls.append(list(names))
        return {t: 2.0 for t in names}

    monkeypatch.setattr(ve, "fetch_volume_ratios", fake_fetch)
    df = pd.DataFrame({"ticker": ["AAA", "BBB"]})
    out = ve.enrich_universe(df, bars=None)
    assert calls == [["AAA", "BBB"]]
    assert list(out["vol_5d_50d"]) == [2.0, 2.0]


def test_empty_universe_still_ships_the_column():
    out = ve.enrich_universe(pd.DataFrame(), bars={"AAA": _bars([1] * 60)})
    assert "vol_5d_50d" in out.columns
