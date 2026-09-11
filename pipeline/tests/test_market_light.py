"""market_light.json -- replicated against the course, then unit-tested.

The first three tests are the reason to trust anything below them: each one
replays a number the course PRINTS against a frozen copy of the prices it was
computed on. If a refactor moves one of them, the file is no longer computing
the course's quantity, whatever the unit tests say.

Fixtures (pipeline/tests/fixtures/market_light/) were downloaded once on
2026-09-11 with auto_adjust=True -- the basis the course's own `ohlc()` uses and
the basis our nightly `fetch_ma_data` receives (yfinance's default; checked on
2020-01-02: 296.13 adjusted vs 324.87 raw, the call returned 296.13).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline.screeners import market_light as ml

FIX = Path(__file__).parent / 'fixtures' / 'market_light'


@pytest.fixture(scope='module')
def spy_close() -> pd.Series:
    return pd.read_csv(FIX / 'SPY_adj_close_2009_2026.csv', index_col=0, parse_dates=True)['Close']


@pytest.fixture(scope='module')
def ma_ohlc() -> pd.DataFrame:
    return pd.read_csv(FIX / 'MA_adj_ohlc_2024_11_2025_05.csv', index_col=0, parse_dates=True)


# ─────────────────────────────────────────────── replication against the course

def _cycle_stats(px: pd.Series) -> dict:
    """cycle_bench.json's definition, with ml's own line and noise constants."""
    line = ml._ma(px, ml.PLUS_N_LEN, ml.PLUS_N_MA)
    sign = (px > line).map({True: 1, False: -1}).where(line.notna())
    sign = sign.loc['2010-01-01':'2026-08-31'].dropna()
    grp = (sign != sign.shift()).cumsum()
    segs = [(g.iloc[0], len(g), str(g.index[0].date()))
            for _, g in sign.groupby(grp) if len(g) > ml.NOISE_MAX]
    up = [s for s in segs if s[0] == 1]
    dn = [s for s in segs if s[0] == -1]
    return {
        'up_mean': round(sum(s[1] for s in up) / len(up), 1),
        'dn_mean': round(sum(s[1] for s in dn) / len(dn), 1),
        'n_up': len(up), 'n_dn': len(dn),
        'longest_up': list(max(up, key=lambda s: s[1])[1:]),
        'longest_down': list(max(dn, key=lambda s: s[1])[1:]),
    }


def test_plus_n_reproduces_cycle_bench_exactly(spy_close):
    """All seven SPY numbers in SwingMasterclass/_pdf/cycle_bench.json.

    Dropping (not merging) the <=4-day runs is load-bearing: merge them into
    their neighbours and the longest up-run becomes 141, not 68.
    """
    assert _cycle_stats(spy_close) == {
        'up_mean': 21.4, 'dn_mean': 12.7, 'n_up': 125, 'n_dn': 82,
        'longest_up': [68, '2025-04-24'], 'longest_down': [32, '2022-04-11'],
    }


def test_live_plus_n_lands_on_the_book_extremes(spy_close):
    """The live counter, stopped on the last day of each record run, reads the
    run's length -- the same 68 and 32 the book prints."""
    assert ml.plus_n(spy_close.loc[:'2025-07-31']) == 68
    assert ml.plus_n(spy_close.loc[:'2022-05-25']) == -32


def test_gears_reproduce_the_ma_2025_chart(ma_ohlc):
    """Lesson 6B.2 says three things about this chart; all three must hold."""
    g = ml.gear_series(ma_ohlc.loc['2025-01-02':'2025-05-02'])
    assert '2025-02-21' in g[g == 6].index.strftime('%Y-%m-%d'), "slam fires on 21 February"
    after = g.loc['2025-02-22':]
    assert after[after == 7].index[0].strftime('%Y-%m-%d') == '2025-03-05', \
        "by 5 March the whole session's high is under the line"
    assert not (g == 1).any(), "gear 1 never fires here -- the low swallows it"


def test_light_share_is_pinned_and_the_book_number_is_not_ours(spy_close):
    """Regression pin for the definition the PAGE uses (EMA, 1-day rising).

    The book's printed 54.5 / 20.7 belong to the other definition in the same
    lesson -- see test_book_numbers_are_sma_three_day. This test pins ours so a
    silent change of basis or rising-rule shows up.
    """
    n = ml.light_frame(spy_close).loc['2015-01-01':'2026-08-31', 'checks_passed'].dropna()
    assert len(n) == 2932
    assert round((n == 3).mean() * 100, 2) == 56.55
    assert round((n == 0).mean() * 100, 2) == 19.30


def test_book_numbers_are_sma_three_day(spy_close):
    """The book's own light statistics, reproduced -- on the OTHER definition.

    Lesson 6: 54.5% green, and the longest all-yes / all-no runs 2024-01-18 ->
    04-04 and 2022-08-30 -> 10-14. SMA 10/20 with "rising" = above 3 sessions
    ago gives 54.5 and both dates to the day (Studio Q, 2026-09-11). Kept here so
    that if Andy rules this definition for the page, the switch is already
    verified against the book.

    The first version of this file claimed these dates reproduce under no
    definition; the grid it searched never contained this cell.
    """
    f, s = spy_close.rolling(10).mean(), spy_close.rolling(20).mean()
    n = ((f > s).astype(int) + (f > f.shift(3)).astype(int) + (s > s.shift(3)).astype(int))
    w = n.loc['2015-01-01':'2026-08-31'].dropna()

    def longest(mask):
        best, cur, st, span = 0, 0, None, None
        for d, v in mask.items():
            if v:
                st = d if cur == 0 else st
                cur += 1
                if cur > best:
                    best, span = cur, (st.strftime('%Y-%m-%d'), d.strftime('%Y-%m-%d'))
            else:
                cur = 0
        return span

    assert round((w == 3).mean() * 100, 1) == 54.5
    assert longest(w == 3) == ('2024-01-18', '2024-04-04')
    assert longest(w == 0) == ('2022-08-30', '2022-10-14')


# ───────────────────────────────────────────────────────────── the light itself

def _df(close, **cols):
    idx = pd.bdate_range('2026-01-01', periods=len(close))
    d = pd.DataFrame({'Close': close}, index=idx)
    for k, v in cols.items():
        d[k] = v
    return d


def test_green_only_at_three_of_three():
    """A steady climb answers yes three times -> green."""
    b = ml.instrument_block(_df(np.linspace(100, 160, 80)))
    assert b['checks_passed'] == 3 and b['light'] == 'green'


def test_two_of_three_is_red_not_a_third_state():
    """'Anything else = RED, sit still' (L6:183). A 2/3 day must read red while
    still exposing the 2 -- the page shows the intermediate state."""
    up = list(np.linspace(100, 160, 70))
    b = ml.instrument_block(_df(up + [158.5, 157.0, 156.0]))   # 10 rolls over first
    assert b['checks_passed'] in (1, 2)
    assert b['light'] == 'red'


def test_rising_means_today_above_yesterday_only(spy_close):
    """The self-invented rule, and proof it is the 1-day one and not an
    'N days ago' variant the plan forbids (L106).

    ⚠️ The first version fed a close ticking 104 -> 103.9 and expected the 10
    EMA to tick down. It does not: an EMA only falls when the new close is BELOW
    the average, and a lagging EMA sits far under 104. A falling close is not a
    falling average. So this is checked on real SPY instead, where the two rules
    must disagree on some days -- if they never did, the test could not tell
    which one the code implements.
    """
    lf = ml.light_frame(spy_close).loc['2015-01-01':]
    f = lf['fast']
    assert lf['fast_rising'].equals(f > f.shift(1)), "rising is today vs yesterday"
    five = f > f.shift(5)
    disagree = (lf['fast_rising'] != five).sum()
    assert disagree > 100, f"a 5-day rule must read differently on many days (got {disagree})"


def test_warmup_is_nan_not_zero():
    """Before the averages exist the day is unmeasurable, which is not the same
    as 'all three said no' -- 0 would be a red light the market never showed."""
    lf = ml.light_frame(pd.Series(np.linspace(100, 110, 30)), ma_type='SMA')
    assert pd.isna(lf['checks_passed'].iloc[5])


def test_ma_type_is_a_parameter():
    """NEEDS_ANDY gap 1: if Andy rules SMA the file changes a constant, not code."""
    px = pd.Series(np.r_[np.linspace(100, 130, 40), np.linspace(130, 120, 10)])
    e = ml.light_frame(px, 'EMA')['fast'].iloc[-1]
    s = ml.light_frame(px, 'SMA')['fast'].iloc[-1]
    assert e != s
    with pytest.raises(ValueError):
        ml.light_frame(px, 'WMA')


def test_history_is_sixty_days_and_ends_today():
    b = ml.instrument_block(_df(np.linspace(100, 160, 120)))
    assert len(b['history']) == ml.HISTORY_DAYS
    assert b['history'][-1]['checks_passed'] == b['checks_passed']


# ──────────────────────────────────────────────────────────────────── +N / gear

def test_plus_n_sign_and_noise_flag():
    px = pd.Series([100.0] * 30 + [110.0] * 3)          # three closes above the line
    assert ml.plus_n(px) == 3
    b = ml.instrument_block(_df(list(np.linspace(90, 100, 40)) + [80.0, 79.0]))
    assert b['plus_n'] < 0 and b['plus_n_noise'] is True


def test_gear_precedence_highest_wins():
    """A day whose HIGH is under the line is maximum defense even though it also
    closes under the line (brake). Reversing the overwrite order would read 5."""
    close = list(np.linspace(100, 130, 40)) + [100.0]
    df = _df(close, Open=[c - 0.5 for c in close], High=[c + 0.2 for c in close],
             Low=[c - 1 for c in close])
    assert ml.gear_series(df).iloc[-1] == 7


# ─────────────────────────────────────────────────────────────── Q1 / Q2 / verdict

def _panel(key, tickers, count=None, truncated=False):
    return {'key': key, 'tickers': [{'ticker': t} for t in tickers],
            'count': len(tickers) if count is None else count, 'truncated': truncated}


def test_setups_read_the_tickers_key_and_dedupe():
    """Regression for the first version, which read `rows`, found nothing, and
    reported 0 on a day ma_reclaim alone had 25 names."""
    wl = {'zones': [{'key': 'entries', 'panels': [
        _panel('ll_hl_1st', ['AAA', 'BBB']),
        _panel('ll_hl_2nd', ['BBB', 'CCC']),
        _panel('vcs', ['ZZZ'] * 1),               # not an entries panel -> ignored
    ]}]}
    s = ml.setups_block(wl)
    assert s['count'] == 3, "AAA, BBB, CCC -- a name in two panels is one name"
    assert s['provisional'] is True


def test_truncated_panel_makes_the_count_a_floor():
    """Read the panel's own `truncated` flag and pre-cut `count`, never guess
    the cap from the list happening to be 25 long."""
    wl = {'zones': [{'panels': [_panel('ll_hl_1st', [f'T{i}' for i in range(25)],
                                        count=26, truncated=True)]}]}
    s = ml.setups_block(wl)
    assert s['count_is_floor'] is True
    assert s['by_panel']['ll_hl_1st'] == 26
    assert s['capped_panels'] == ['ll_hl_1st']


def test_ma_reclaim_is_not_a_pullback_setup():
    """A reclaim from below is not the course's PB (a pullback TO the MA in an
    uptrend). Adding it back roughly doubled the count on 2026-09-10 (21 -> 43)."""
    wl = {'zones': [{'panels': [_panel('ma_reclaim', ['R1', 'R2', 'R3']),
                                _panel('liquid_leader_pullback', ['P1'])]}]}
    s = ml.setups_block(wl)
    assert s['count'] == 1 and 'ma_reclaim' not in s['by_panel']


@pytest.mark.parametrize('n,band', [(0, 'none'), (1, 'dim'), (3, 'dim'),
                                    (4, 'unspecified'), (9, 'unspecified'), (10, 'bright')])
def test_setup_bands_leave_the_courses_gap_open(n, band):
    """L7:49-50 names 10+ and 1-3. It says nothing about 4-9; that gap is
    reported as 'unspecified' for Studio Q, not filled in here."""
    wl = {'zones': [{'panels': [_panel('ll_hl_1st', [f'T{i}' for i in range(n)])]}]}
    assert ml.setups_block(wl)['band'] == band


def _uni(**rows):
    return [dict(ticker=t, **v) for t, v in rows.items()]


def test_leaders_only_themes_that_lead_on_the_two_week_rung():
    groups = {'themes': [
        {'group': 'Semis', 'kind': 'theme', 'tickers': ['AAA', 'BBB']},
        {'group': 'Small Caps', 'kind': 'factor', 'tickers': ['CCC']},   # not a thematic wave
        {'group': 'Banks', 'kind': 'theme', 'tickers': ['DDD']},         # not leading
    ]}
    ladder = {'themes': {'Semis': {'2w': 'Leading'}, 'Small Caps': {'2w': 'Leading'},
                         'Banks': {'2w': 'Lagging'}}}
    uni = _uni(AAA=dict(rs_rating=99, sma50_dist=5, close=10, ema21=9),
               BBB=dict(rs_rating=98, sma50_dist=-2, close=10, ema21=11),
               CCC=dict(rs_rating=99, sma50_dist=5, close=10, ema21=9),
               DDD=dict(rs_rating=99, sma50_dist=5, close=10, ema21=9))
    got = ml.leaders_block(groups, ladder, uni)
    assert [x['ticker'] for x in got['leaders']] == ['AAA', 'BBB']
    assert {x['ticker']: x['status'] for x in got['leaders']} == {'AAA': 'holding', 'BBB': 'broken'}


def test_between_the_lines_is_holding_not_unknown():
    """Above the 50 SMA but under the 21 EMA is a pullback in a healthy trend.
    The first version returned None there -- 'not measured' for a name measured
    fine. Status is binary on the 50; the 21 is reported beside it."""
    groups = {'themes': [{'group': 'S', 'kind': 'theme', 'tickers': ['X']}]}
    ladder = {'themes': {'S': {'2w': 'Leading'}}}
    got = ml.leaders_block(groups, ladder, _uni(X=dict(rs_rating=90, sma50_dist=3, close=9, ema21=10)))
    x = got['leaders'][0]
    assert x['status'] == 'holding' and x['above_ema21'] is False


def test_rs_ties_break_stably():
    """rs_rating is an integer with walls of ties at the top; without a
    tiebreak the ten names reshuffle nightly -- a fake change on the page."""
    groups = {'themes': [{'group': 'S', 'kind': 'theme', 'tickers': ['ZZ', 'AA', 'MM']}]}
    ladder = {'themes': {'S': {'2w': 'Leading'}}}
    uni = _uni(ZZ=dict(rs_rating=99, perf_3m=10, sma50_dist=1),
               AA=dict(rs_rating=99, perf_3m=30, sma50_dist=1),
               MM=dict(rs_rating=99, perf_3m=20, sma50_dist=1))
    order = [x['ticker'] for x in ml.leaders_block(groups, ladder, uni)['leaders']]
    assert order == ['AA', 'MM', 'ZZ'], "same rs -> stronger 3M performance first"


def test_red_decides_the_verdict_alone_green_waits_for_studio_q():
    assert ml.verdict({'light': 'red'}) == 'avoid'
    assert ml.verdict({'light': 'green'}) is None
    assert ml.verdict(None) is None


# ─────────────────────────────────────────────────────────────── contract shape

def test_payload_matches_the_consumer_contract():
    """frontend/src/hooks/useMarketLight.js reads exactly these keys."""
    hist = {'SPY': _df(np.linspace(100, 140, 90), Open=np.linspace(99, 139, 90),
                       High=np.linspace(101, 141, 90), Low=np.linspace(98, 138, 90))}
    p = ml.build(hist)
    for k in ('date', 'ma_type', 'spy', 'qqq', 'brightness', 'verdict'):
        assert k in p
    spy = p['spy']
    assert {c['key'] for c in spy['checks']} == {'fast_above_slow', 'fast_rising', 'slow_rising'}
    assert set(spy['gear']) >= {'n', 'label'}
    assert set(spy['history'][0]) == {'date', 'close', 'fast', 'slow', 'checks_passed'}
    assert p['qqq'] is None, "an absent ticker is None -- rendered 'not measured', never zeros"


def test_brightness_leaders_is_the_array_the_page_maps_over():
    """The hook does `brightness.leaders.map(...)`. The first version put an
    OBJECT there ({leaders, themes, provisional}); the top-level shape test
    stayed green because it never looked one level down."""
    groups = {'themes': [{'group': 'S', 'kind': 'theme', 'tickers': ['X', 'Y']}]}
    ladder = {'themes': {'S': {'2w': 'Leading'}}}
    uni = _uni(X=dict(rs_rating=99, sma50_dist=1), Y=dict(rs_rating=98, sma50_dist=-1))
    b = ml.build({}, groups=groups, ladder=ladder, universe_rows=uni)['brightness']
    assert isinstance(b['leaders'], list)
    assert set(b['leaders'][0]) >= {'ticker', 'theme', 'status'}
    assert b['leaders_meta']['provisional'] is True
    assert isinstance(b['setups'] if b['setups'] is not None else {}, dict)


def test_missing_inputs_are_none_not_zero():
    p = ml.build({})
    assert p['spy'] is None and p['verdict'] is None
    assert p['brightness'] == {'setups': None, 'leaders': None, 'leaders_meta': None}


def test_run_all_actually_calls_it():
    """A module with green tests and no caller is not delivered
    (pitfall_tested_the_module_not_the_wiring: a hand-resolved merge conflict
    once deleted a wiring line and nothing noticed for three days).

    Deliberately NOT guarded through schema_snapshot yet: registering the file
    there would turn a failure inside market_light's own domain into a missing
    file, which the snapshot gate treats as fatal for the WHOLE nightly run.
    Add it to the snapshot once the producer has run clean for a while.
    """
    src = (Path(ml.__file__).parent / 'run_all.py').read_text()
    assert 'ML.build(ma_histories' in src, "run_all must call market_light.build"
    assert "OUTPUT_DIR / 'market_light.json'" in src, "and emit the file"
    assert "ledger.error('market_light'" in src, "inside its own failure domain"
