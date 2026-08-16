"""The Sheet reader must agree with the CSV reader, and must not leak the token.

Equivalence was checked once against the real 2026-08-16 book — 355 trades,
identical Trade records from both readers — but that book cannot live in the
repo. These tests pin the rules that check proved, on synthetic rows.
"""
from __future__ import annotations

from datetime import date

import pytest

from pipeline.portfolio.sheets_source import (
    SheetsUnavailable, fetch_trades, to_trades,
)

ROW = {
    'ticker': 'ABCD', 'direction': 'long', 'sector': 'Technology',
    'entryDate': '2026-01-05T15:00:00.000Z', 'entryPrice': 100.0,
    'originalQty': 300, 'currentQty': 200,
    'stopPrice': 95.0, 'initialStop': 90.0, 'isClosed': False,
    'trims': [{'date': '2026-02-01', 'price': 120.0, 'qty': 100, 'type': 'trim_1_3'}],
}


def one(**over):
    return to_trades([{**ROW, **over}])


def test_a_row_becomes_a_trade():
    t, = one()
    assert (t.ticker, t.direction, t.entry_date) == ('ABCD', 'long', date(2026, 1, 5))
    assert (t.entry_price, t.stop_price, t.initial_stop) == (100.0, 95.0, 90.0)
    assert t.closed is False and len(t.trims) == 1


def test_trims_come_back_oldest_first():
    """The CSV enforced order by column position; a JSON array does not, and
    exit_date, the ladder and the R attribution all assume oldest first."""
    t, = one(trims=[
        {'date': '2026-03-01', 'price': 130.0, 'qty': 50, 'type': 'trim_1_3'},
        {'date': '2026-02-01', 'price': 120.0, 'qty': 100, 'type': 'trim_1_3'},
    ])
    assert [x.date for x in t.trims] == [date(2026, 2, 1), date(2026, 3, 1)]


def test_a_blank_initial_stop_leaves_the_trade_without_an_R(caplog):
    """Andy trails stops in the tracker, so the live stop is not the stop the
    position was sized against. Substituting it would divide that trade's R by
    the wrong number and still look like an R."""
    with caplog.at_level('WARNING'):
        t, = one(initialStop=None)
    assert t.initial_stop is None
    assert t.R_dollars is None and t.realized_R is None
    # getMessage() applies the lazy %-args; r.message alone is the raw template.
    assert any('initialStop' in r.getMessage() for r in caplog.records)


def test_a_known_initial_stop_still_yields_an_R():
    t, = one()          # entry 100, initial stop 90, 300 shares
    assert t.R_dollars == pytest.approx(10.0 * 300)


def test_blank_stop_falls_back_the_same_way_the_csv_reader_does():
    t, = one(stopPrice=None, initialStop=None)
    assert t.stop_price == pytest.approx(95.0)  # entry * 0.95


@pytest.mark.parametrize('bad', [
    {'ticker': ''}, {'direction': 'sideways'}, {'entryPrice': None},
    {'originalQty': None}, {'entryDate': ''},
])
def test_unusable_rows_are_skipped_not_guessed(bad):
    assert to_trades([{**ROW, **bad}]) == []


def test_a_malformed_trim_drops_only_that_trim():
    t, = one(trims=[
        {'date': '2026-02-01', 'price': 120.0, 'qty': 100, 'type': 'trim_1_3'},
        {'date': '2026-03-01', 'price': None, 'qty': 50, 'type': 'trim_1_3'},
    ])
    assert len(t.trims) == 1


def test_missing_credentials_name_the_variables_not_the_values(monkeypatch):
    monkeypatch.delenv('FLUXUS_GAS_URL', raising=False)
    monkeypatch.delenv('FLUXUS_SYNC_TOKEN', raising=False)
    with pytest.raises(SheetsUnavailable) as e:
        fetch_trades()
    assert 'FLUXUS_GAS_URL' in str(e.value) and 'FLUXUS_SYNC_TOKEN' in str(e.value)


def test_a_transport_failure_never_quotes_the_url(monkeypatch):
    """requests puts the full URL — token and all — in its exception strings,
    and CI logs are not a place to put a bearer credential."""
    import requests

    def boom(*_a, **_k):
        raise requests.ConnectionError(
            'failed: https://script.google.com/x?action=pull&token=SUPERSECRET')

    monkeypatch.setattr(requests, 'get', boom)
    with pytest.raises(SheetsUnavailable) as e:
        fetch_trades('https://example.test', 'SUPERSECRET')
    assert 'SUPERSECRET' not in str(e.value)
