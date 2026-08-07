"""The daily smile store — what it refuses, and what it never invents."""
import pytest

from pipeline.reference import skew_log as SK
from pipeline.reference.context import percentile_of

C = {"strike": 560.0, "delta": 0.25, "iv": 0.1350}
P = {"strike": 531.0, "delta": -0.25, "iv": 0.1460}


def _row(**kw):
    base = dict(date="2026-08-05", symbol="DIA", expiry="20260904", dte=30,
                spot=544.5, forward=545.8, atm_iv=0.1376, source="feed_greeks")
    base.update(kw)
    return SK.entry(**base)


def test_skews_are_derived_not_supplied():
    r = _row(call_25d=C, put_25d=P)
    assert r["call_skew"] == pytest.approx(0.1350 - 0.1376)
    assert r["put_skew"] == pytest.approx(0.1460 - 0.1376)
    assert r["risk_reversal"] == pytest.approx(0.1350 - 0.1460)


def test_a_missing_wing_stays_none_and_does_not_become_zero():
    # An unmeasured wing and a flat wing are different facts.
    r = _row(call_25d=None, put_25d=P)
    assert r["call_skew"] is None and r["risk_reversal"] is None
    assert r["put_skew"] is not None


def test_rejects_an_unknown_measurement_source():
    with pytest.raises(ValueError, match="source"):
        _row(source="vibes", call_25d=C)


def test_rejects_an_iv_that_is_secretly_a_percentage():
    # 13.76 instead of 0.1376 would silently poison every percentile drawn later.
    with pytest.raises(ValueError, match="ATM IV"):
        _row(atm_iv=13.76, call_25d=C)


def test_append_is_idempotent_per_day_and_symbol(tmp_path):
    p = tmp_path / "skew.jsonl"
    r = _row(call_25d=C, put_25d=P)
    assert SK.append(r, p) is True
    assert SK.append(r, p) is False          # re-running the collector must not double-count
    assert len(SK.read(p)) == 1


def test_a_different_expiry_on_the_same_day_is_a_separate_row(tmp_path):
    p = tmp_path / "skew.jsonl"
    SK.append(_row(call_25d=C, expiry="20260904"), p)
    assert SK.append(_row(call_25d=C, expiry="20261016"), p) is True
    assert len(SK.read(p)) == 2


def test_series_is_chronological_and_drops_unmeasured_days():
    rows = [_row(date="2026-08-05", call_25d=C), _row(date="2026-08-03", call_25d=None),
            _row(date="2026-08-04", call_25d={**C, "iv": 0.1300})]
    s = SK.series(rows, "DIA", "call_skew")
    assert len(s) == 2                                   # the unmeasured day is absent
    assert s[0] == pytest.approx(0.1300 - 0.1376)        # 08-04 before 08-05


def test_series_ignores_other_symbols():
    rows = [_row(symbol="DIA", call_25d=C), _row(symbol="SPY", call_25d=C)]
    assert len(SK.series(rows, "SPY")) == 1


def test_percentile_of_a_thin_series_says_it_is_thin():
    # The whole point of the store is answering percentile questions honestly;
    # on day one the honest answer carries a warning, not a number alone.
    rows = [_row(date=f"2026-08-{d:02d}", call_25d={**C, "iv": 0.13 + d / 1000})
            for d in range(1, 6)]
    s = SK.series(rows, "DIA")
    pc = percentile_of(s[-1], s)
    assert pc["n"] == 5 and pc["thin"] is True


def test_the_measurement_time_is_recorded_because_skew_moves_intraday():
    # A series mixing a 12:37 reading with a 15:00 one is partly measuring the
    # clock. The row must say when, or the contamination is invisible.
    r = _row(call_25d=C, measured_at="2026-08-06T15:02:11-04:00")
    assert r["measured_at"].endswith("-04:00")


def test_a_row_without_a_measurement_time_keeps_none_rather_than_guessing():
    assert _row(call_25d=C)["measured_at"] is None
