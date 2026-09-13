"""Writers that feed data/output must emit R and % only.

Andy 2026-09-13, verbatim: 「管线只做R 和%, 不写股数和美元」

test_public_output_privacy.py scans what is on disk; these tests pin the three
writers that leaked (trade_postmortem, h1_report, pyramid_analyzer), so a
regression fails here on a synthetic book instead of after a nightly run has
already published it. Banned names are literals, not imported.
"""
import json
import re
from datetime import date, timedelta

import pandas as pd

from pipeline.portfolio import trade_postmortem as tp
from pipeline.portfolio.h1_report import public_h1_stats
from pipeline.portfolio.pyramid_analyzer import Campaign, build_pyramid_section
from pipeline.portfolio.trade_parser import Trade, TrimEvent

BANNED = {
    'qty', 'shares', 'original_qty', 'current_qty', 'r_dollars', 'R_dollars',
    'realized_pl', 'pnl', 'pl', 'pl_dollars', 'dollars', 'position',
    'total_pnl', 'open_pnl', 'best_pnl', 'avg_pnl', 'unrealized', 'amount',
    'mtm_equity', 'peak_equity', 'profit_total', 'realized_pnl',
    'unrealized_pnl', 'starting_capital', 'avg_winner', 'avg_loser', 'expectancy',
}
DOLLAR_TOTAL = re.compile(r'\$\s?\d{1,3}(,\d{3})+')


def _keys(node, path=''):
    if isinstance(node, dict):
        for k, v in node.items():
            yield f'{path}.{k}', k
            yield from _keys(v, f'{path}.{k}')
    elif isinstance(node, list):
        for x in node:
            yield from _keys(x, f'{path}[]')


def _banned_in(doc):
    return [p for p, k in _keys(doc) if k in BANNED]


def _trade(closed=True, current_qty=0):
    return Trade(
        ticker='AAOI', direction='long', sector='Tech',
        entry_date=date(2026, 2, 18), entry_price=44.41,
        original_qty=2262, current_qty=current_qty,
        stop_price=41.0, initial_stop=41.0, closed=closed,
        trims=(TrimEvent(date(2026, 2, 20), 50.35, 754, 'trim_1_3'),
               TrimEvent(date(2026, 2, 26), 54.87, 1508, 'sell_rest')),
    )


def test_trade_to_dict_has_r_and_pct_not_qty_or_dollars():
    d = tp._trade_to_dict(_trade())
    assert _banned_in(d) == []
    assert d['trims'][0]['pct_of_position'] == 754 / 2262 * 100
    assert d['remaining_pct'] == 0
    assert d['r_pct_of_entry'] == abs(44.41 - 41.0) / 44.41 * 100
    assert d['realized_R'] is not None


def test_open_position_reports_remaining_pct():
    d = tp._trade_to_dict(_trade(closed=False, current_qty=1508))
    assert d['remaining_pct'] == 1508 / 2262 * 100
    assert _banned_in(d) == []


def test_generate_postmortems_writes_no_private_fields(tmp_path, monkeypatch):
    days = [date(2026, 1, 5) + timedelta(days=i) for i in range(80)]
    df = pd.DataFrame({
        'open': [44.0] * 80, 'high': [46.0] * 80, 'low': [42.0] * 80,
        'close': [45.0] * 80, 'volume': [1e6] * 80,
    }, index=days)
    monkeypatch.setattr(tp, '_load_ohlc_df', lambda t: df)
    s = tp.generate_postmortems([_trade()], tmp_path)
    assert s['succeeded'] == 1
    rec = json.loads(next(tmp_path.glob('AAOI_*.json')).read_text())
    assert _banned_in(rec) == []
    assert 'qty' not in rec['narrative']
    assert not DOLLAR_TOTAL.search(rec['narrative']), rec['narrative']
    assert '% of entry' in rec['narrative']


def test_writer_goes_red_on_a_reintroduced_field(monkeypatch):
    """Positive control: the assertion above must be able to fail."""
    real = tp._trade_to_dict
    monkeypatch.setattr(tp, '_trade_to_dict',
                        lambda t: {**real(t), 'r_dollars': 7713.42})
    assert _banned_in(tp._trade_to_dict(_trade())) == ['.r_dollars']


def _h1_fixture():
    return {
        'meta': {'csv': 'x.csv', 'start': '2026-01-01', 'starting_capital': 1000.0},
        'headline': {'h1_return_pct': 30.0, 'mtm_equity': 1300.0, 'profit_total': 300.0,
                     'realized_pnl': 200.0, 'unrealized_pnl': 100.0, 'spy_h1_pct': 9.31},
        'trade_stats': {'win_rate': 40.0, 'avg_winner': 50.0, 'avg_loser': -10.0,
                        'expectancy': 5.0, 'avg_r': 0.9,
                        'max_dd': {'pct': -10.0, 'amount': -130.0, 'peak_equity': 1300,
                                   'deepest_pct': {'pct': -12.0, 'amount': -100}}},
        'open_positions': [{'ticker': 'A', 'entry': 10.0, 'mark': 11.0, 'qty': 50,
                            'unrealized': 50.0, 'pct': 10.0}],
        'winners': [{'ticker': 'B', 'pnl': 80.0, 'r': 3.0}],
        'losers': [{'ticker': 'C', 'pnl': -20.0, 'r': -1.0}],
        'top_trades': [{'ticker': 'B', 'entry': 10.0, 'qty': 100, 'position': 1000,
                        'exits': [{'date': '2026-02-01', 'price': 11.0, 'qty': 25},
                                  {'date': '2026-02-02', 'price': 12.0, 'qty': 75}],
                        'pnl': 80, 'r': 3.0}],
        'worst_trades': [],
        'campaigns': [{'ticker': 'B', 'total_pnl': 100, 'open_pnl': 0, 'best_pnl': 80}],
        'sectors': [{'sector': 'Tech', 'pnl': 60.0, 'trades': 2}],
        'exit_styles': {'strength': {'count': 2, 'total_pnl': 90.0, 'avg_pnl': 45.0}},
    }


def test_public_h1_stats_is_r_and_pct_only():
    out = public_h1_stats(_h1_fixture())
    assert _banned_in(out) == []
    h = out['headline']
    assert (h['realized_pct'], h['unrealized_pct']) == (20.0, 10.0)
    assert h['realized_pct'] + h['unrealized_pct'] == h['h1_return_pct']
    assert out['top_trades'][0]['exits'][0]['pct_of_position'] == 25.0
    assert out['top_trades'][0]['contrib_pct'] == 8.0
    assert out['campaigns'][0]['total_contrib_pct'] == 10.0
    assert out['exit_styles']['strength']['avg_contrib_pct'] == 4.5
    assert out['trade_stats']['avg_r'] == 0.9


def test_public_h1_stats_does_not_mutate_its_input():
    src = _h1_fixture()
    public_h1_stats(src)
    assert src['meta']['starting_capital'] == 1000.0


def test_pyramid_layers_are_sized_relative_to_the_first_layer():
    a = _trade()
    b = Trade(ticker='AAOI', direction='long', sector='Tech', entry_date=date(2026, 3, 2),
              entry_price=50.0, original_qty=1131, current_qty=0, stop_price=47.0,
              initial_stop=47.0, closed=True,
              trims=(TrimEvent(date(2026, 3, 9), 55.0, 1131, 'sell_rest'),))
    c = Campaign(ticker='AAOI', direction='long', layers=[a, b], actual_realized_R=2.0)
    out = build_pyramid_section([c])
    assert _banned_in(out) == []
    assert [l['size_pct_of_first'] for l in out[0]['layer_entries']] == [100.0, 50.0]
