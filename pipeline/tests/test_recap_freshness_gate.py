"""build_pack freshness gate: breadth_block already stops when T is missing,
but assets/groups/stocks/verdict quietly came back empty when their archive
had no T rows. The gate must turn each of those into a hard stop.
Positive controls are red per archive; the full-T case is green."""
import pytest

from pipeline.content.recap import build_pack

T, P = "2026-09-30", "2026-09-29"


def _rows(nT, nP, **extra):
    return [{"date": T, **extra}] * nT + [{"date": P, **extra}] * nP


def _fake(monkeypatch, *, assets=(26, 26), ind=(139, 139), theme=(56, 56),
          events=(900, 2400), leaders=(159, 150), verdict=True, cond=True):
    data = {
        "data/history/asset_signals.csv": _rows(*assets),
        "data/history/groups_archive.csv": _rows(*ind, kind="industry") + _rows(*theme, kind="theme"),
        "data/history/ticker_events.csv": _rows(*events),
        "data/history/leaders_log.csv": _rows(*leaders),
    }
    monkeypatch.setattr(build_pack, "csv_rows", lambda p: data[p])
    monkeypatch.setattr(build_pack, "_verdicts", lambda: (
        {T: {}, P: {}} if verdict else {P: {}}, {T: {}, P: {}} if cond else {P: {}}))


def test_full_day_passes(monkeypatch):
    _fake(monkeypatch)
    assert build_pack.freshness_problems(T, P) == []
    build_pack.freshness_gate(T, P)


def test_ticker_events_swing_is_not_flagged(monkeypatch):
    """09-21 real swing 2453 -> 1157: screener hits vary, only 'has rows' applies."""
    _fake(monkeypatch, events=(1157, 2453))
    assert build_pack.freshness_problems(T, P) == []


@pytest.mark.parametrize("kw,needle", [
    ({"assets": (0, 26)}, "asset_signals"),
    ({"ind": (0, 139)}, "groups_archive[industry]"),
    ({"theme": (0, 56)}, "groups_archive[theme]"),
    ({"events": (0, 900)}, "ticker_events"),
    ({"leaders": (0, 159)}, "leaders_log"),
    ({"verdict": False}, "breadth_replay.json"),
    ({"cond": False}, "breadth.json conditions"),
    ({"assets": (10, 26)}, "asset_signals: 2026-09-30 has 10 rows"),
    ({"ind": (60, 139)}, "groups_archive[industry]: 2026-09-30 has 60 rows"),
])
def test_missing_or_partial_t_stops(monkeypatch, kw, needle):
    _fake(monkeypatch, **kw)
    probs = build_pack.freshness_problems(T, P)
    assert any(needle in p for p in probs), probs
    with pytest.raises(SystemExit):
        build_pack.freshness_gate(T, P)
