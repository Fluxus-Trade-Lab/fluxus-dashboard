"""宇宙人口闸：先证明它报得出 06-26 那个形状，再信它的绿。

真实历史那一跑（139 个 session，逐个 `git show`）要几分钟，不适合放进 CI，
所以这里钉的是**性质**：同样的形状用合成数据喂进去必须红，平稳的日子必须绿，
以及那条把断点定错一天的时区陷阱。真实历史的跑法写在工具 docstring 里。
"""
from __future__ import annotations

import pytest

from pipeline.tools.audit_universe_population import (
    check, et_session, share_small,
)

BIG = [5e9] * 1000          # 老宇宙：一只 $1B 以下的都没有
MIXED = [5e9] * 470 + [1.4e8] * 530   # 06-26 之后：53% 在 $1B 以下


def _steady(days, caps):
    return {f'2026-06-{d:02d}': list(caps) for d in days}


def test_share_small_ignores_missing_caps():
    assert share_small([5e9, 0, None, 1e8]) == 0.5      # 0 与 None 不算分母
    assert share_small([0, 0]) is None                  # 全不可判＝判不了，不是 0


def test_steady_universe_is_silent():
    result = check(_steady(range(1, 21), BIG))
    assert result['ok'], result['violations']


def test_the_2026_06_26_shape_is_reported():
    """一晚之间 53% 的名字换成小票、市值中位掉到七分之一——两条规则都该响。"""
    by = _steady(range(1, 21), BIG)
    by['2026-06-26'] = list(MIXED)
    result = check(by)
    assert not result['ok']
    kinds = {r['session']: r['kind'] for r in result['rows']}
    assert kinds['2026-06-26'] == 'P1+P2'
    assert all(kinds[d] in (None, 'P3') for d in kinds if d != '2026-06-26')
    assert any('P1 2026-06-26' in v for v in result['violations'])
    assert any('P2 2026-06-26' in v for v in result['violations'])


def test_recovery_also_reports_and_that_is_on_purpose():
    """筛选条件若回来，那一场同样会响——藏住「它回来了」的规则也会藏住「它又坏了」。"""
    by = _steady(range(1, 21), MIXED)
    by['2026-06-26'] = list(BIG)
    result = check(by)
    assert not result['ok']
    assert any(v.startswith('P1 2026-06-26') for v in result['violations'])


def test_a_fragment_is_not_judged():
    by = _steady(range(1, 21), BIG)
    by['2026-06-26'] = [1.4e8] * 10        # 抓挂了只剩十只，不该当成人口变了
    result = check(by)
    assert result['ok']
    assert any('P3 2026-06-26' in w for w in result['warnings'])


def test_a_drift_inside_the_band_stays_green():
    by = _steady(range(1, 21), BIG)
    by['2026-06-26'] = [5e9] * 940 + [1.4e8] * 60      # 6pp，容差 10pp
    assert check(by)['ok']


@pytest.mark.parametrize('ts, day', [
    ('2026-06-25T22:57:38', '2026-06-25'),   # UTC 晚上＝同日 ET 傍晚
    ('2026-06-25T22:57:38Z', '2026-06-25'),
    ('2026-06-26T02:30:00+00:00', '2026-06-25'),   # UTC 次日凌晨仍属前一场
])
def test_session_comes_from_the_snapshot_not_the_clock(ts, day):
    """按本机时区（JST）读这些时刻会整体偏一天——那正是把断点定错一天的走法。"""
    assert et_session(ts) == day


def test_unparseable_timestamp_is_none_not_today():
    assert et_session(None) is None
    assert et_session('not a time') is None


# ---------------------------------------------------------------------------
# 2026-09-23：变异普查读数 14/67（21%），全库最低——这道闸有 53 处可以坏掉而
# 没有任何测试会响。下面这一批是照着存活清单逐条补的，钉的是三样东西：
#   ① 每条阈值的边界（正好卡在线上 vs 越过一点）
#   ② `main()` 的三个退出码与 -q 的取舍（此前 main 一行没测过）
#   ③ `snapshots()` 的读取契约（此前完全没测过：空文件、缺时间戳、同场次后者胜、null 市值）
# 哪些存活点是等价变异、为什么不追，写在
# data/research/audit_mutation_2026-09-22/README.md。
# ---------------------------------------------------------------------------

from pipeline.tools import audit_universe_population as pop
from pipeline.tools.audit_universe_population import snapshots


def _caps(n, small_frac, big=5e9, small=1.4e8):
    """n 只票，其中 small_frac 那一份在 $1B 以下；small_frac < 0.5 时中位数仍是大票。"""
    k = round(n * small_frac)
    return [small] * k + [big] * (n - k)


def _twenty_quiet_sessions(caps=None):
    return {f'2026-06-{d:02d}': list(caps if caps is not None else BIG) for d in range(1, 21)}


# ---- ① 边界 ---------------------------------------------------------------

def test_exactly_min_names_is_judged_and_one_name_fewer_is_not():
    """200 只是「还算一个宇宙」的下界，不是上界——正好 200 要判，199 才放过。"""
    at = _twenty_quiet_sessions()
    at['2026-06-26'] = _caps(200, 0.6)
    assert not check(at)['ok'], '正好 200 只就该判'

    below = _twenty_quiet_sessions()
    below['2026-06-26'] = _caps(199, 0.6)
    r = check(below)
    assert r['ok'], r['violations']
    assert any('P3 2026-06-26: only 199 names' in w for w in r['warnings'])


def test_three_trailing_sessions_are_enough_and_two_are_not():
    three = {f'2026-06-{d:02d}': list(BIG) for d in (1, 2, 3)}
    three['2026-06-04'] = _caps(1000, 0.6)
    assert not check(three)['ok'], '三场打底就够判了'

    two = {f'2026-06-{d:02d}': list(BIG) for d in (1, 2)}
    two['2026-06-03'] = _caps(1000, 0.6)
    r = check(two)
    assert r['ok'], r['violations']
    assert any('only 2 trailing sessions' in w for w in r['warnings'])


def test_a_move_exactly_at_the_tolerance_stays_green():
    by = _twenty_quiet_sessions()
    by['2026-06-26'] = _caps(1000, 0.10)        # 正好 10pp，容差 10pp
    assert check(by)['ok'], check(by)['violations']


def test_a_move_one_name_past_the_tolerance_reports():
    """上一条的阳性对照：同样的构造往前挪一只票就必须红，否则那条绿什么都不证明。"""
    by = _twenty_quiet_sessions()
    by['2026-06-26'] = _caps(1000, 0.101)
    r = check(by)
    assert not r['ok']
    assert any(v.startswith('P1 2026-06-26') for v in r['violations'])


def test_the_median_cap_band_is_closed_at_both_edges():
    up = {f'2026-06-{d:02d}': [1e9] * 1000 for d in range(1, 21)}
    up['2026-06-26'] = [1.5e9] * 1000           # 正好 x1.50
    assert check(up)['ok'], check(up)['violations']

    down = {f'2026-06-{d:02d}': [3e9] * 1000 for d in range(1, 21)}
    down['2026-06-26'] = [2e9] * 1000           # 正好 x1/1.5
    assert check(down)['ok'], check(down)['violations']


def test_a_median_that_moves_inside_the_alphabet_but_past_the_factor_reports():
    """市值中位 x1.8、名字构成一动不动——P2 单独成立，不靠 P1 捎带。"""
    by = {f'2026-06-{d:02d}': [1e9] * 1000 for d in range(1, 21)}
    by['2026-06-26'] = [1.8e9] * 1000
    r = check(by)
    assert not r['ok']
    assert any(v.startswith('P2 2026-06-26') for v in r['violations'])
    assert not any(v.startswith('P1') for v in r['violations'])


def test_the_trailing_window_is_twenty_sessions_not_twenty_one():
    """第 21 场必须落在窗外：把它算进来，基线从 0.20 变 0.40，这一天就不响了。"""
    by = {'2026-06-01': _caps(1000, 0.4)}                       # 窗外的那一场
    for d in range(2, 12):
        by[f'2026-06-{d:02d}'] = _caps(1000, 0.0)
    for d in range(12, 22):
        by[f'2026-06-{d:02d}'] = _caps(1000, 0.4)
    by['2026-06-22'] = _caps(1000, 0.35)
    kinds = {r['session']: r['kind'] for r in check(by)['rows']}
    assert kinds['2026-06-22'] == 'P1'


def test_a_name_exactly_on_the_line_is_not_small():
    assert share_small([1e9] * 500 + [5e9] * 500) == 0.0


def test_the_cap_filter_asks_for_positive_not_for_more_than_one():
    """一分钱市值也是一只票——过滤的是「没有市值」，不是「市值太小」。"""
    assert share_small([1.0, 5e9]) == 0.5


def test_blank_caps_are_dropped_before_anything_is_counted():
    by = _twenty_quiet_sessions()
    by['2026-06-05'] = list(BIG) + [None] * 50          # 打底那一场也得干净
    by['2026-06-19'] = list(BIG) + [None] * 50 + [0] * 50
    r = check(by)
    rec = {x['session']: x for x in r['rows']}['2026-06-19']
    assert rec['names'] == len(BIG)
    assert r['ok'], r['violations']


def test_the_payload_rounds_both_shares_to_four_places():
    """当天的份额和基线份额是同一个读数的两半，精度得是同一档。"""
    third = [1.4e8] * 1000 + [5e9] * 2000              # 恰好三分之一
    by = {f'2026-06-{d:02d}': list(third) for d in range(1, 21)}
    by['2026-06-26'] = list(third)
    rec = {x['session']: x for x in check(by)['rows']}['2026-06-26']
    assert rec['share_small'] == 0.3333
    assert rec['baseline_share'] == 0.3333


def test_the_violation_says_how_far_it_moved_and_where_the_band_is():
    """这两句话是早上八点被人读的东西，不是内部字段。"""
    by = _twenty_quiet_sessions()
    by['2026-06-26'] = list(MIXED)
    v = check(by)['violations']
    p1 = next(x for x in v if x.startswith('P1 '))
    p2 = next(x for x in v if x.startswith('P2 '))
    assert 'moved 53pp' in p1
    assert 'tolerance 10pp' in p1
    assert 'band x0.67-x1.50' in p2


# ---- ② main() 的三个退出码 -------------------------------------------------

def test_main_returns_two_when_there_is_nothing_to_check(monkeypatch, capsys):
    """查不到快照不是通过——0 个违规和 0 次检查长得一样，这里必须分开。"""
    monkeypatch.setattr(pop, 'snapshots', lambda *a, **k: {})
    assert pop.main([]) == 2
    assert 'nothing checked' in capsys.readouterr().out


def test_main_is_green_on_a_steady_universe_and_prints_the_unjudgeable_row(monkeypatch, capsys):
    by = _twenty_quiet_sessions()
    by['2026-06-19'] = [0] * 1000                        # 一场全无可用市值：印成 '-'，不是 0
    monkeypatch.setattr(pop, 'snapshots', lambda *a, **k: by)
    assert pop.main([]) == 0
    out = capsys.readouterr().out
    assert 'OK: 0 violation(s)' in out
    assert 'P3    2026-06-19  names     0  <line    -    median         -' in out


def test_main_returns_one_and_names_the_session(monkeypatch, capsys):
    by = _twenty_quiet_sessions()
    by['2026-06-26'] = list(MIXED)
    monkeypatch.setattr(pop, 'snapshots', lambda *a, **k: by)
    assert pop.main([]) == 1
    assert 'P1+P2 2026-06-26' in capsys.readouterr().out


def test_quiet_drops_the_clean_rows_and_the_warnings_but_never_the_hit(monkeypatch, capsys):
    by = _twenty_quiet_sessions()
    by['2026-06-26'] = list(MIXED)
    monkeypatch.setattr(pop, 'snapshots', lambda *a, **k: by)
    assert pop.main(['-q']) == 1
    out = capsys.readouterr().out
    assert 'P1+P2 2026-06-26' in out          # 出事那一行照印
    assert '2026-06-05' not in out            # 干净的行不印
    assert 'not judged' not in out            # P3 警告安静时不印


def test_the_json_report_is_written_and_carries_the_violations(monkeypatch, tmp_path):
    import json as _json
    by = _twenty_quiet_sessions()
    by['2026-06-26'] = list(MIXED)
    monkeypatch.setattr(pop, 'snapshots', lambda *a, **k: by)
    out = tmp_path / 'report.json'
    assert pop.main(['--json', str(out)]) == 1
    payload = _json.loads(out.read_text())
    assert payload['ok'] is False
    assert any(v.startswith('P1 2026-06-26') for v in payload['violations'])
    assert payload['sessions'] == 21


# ---- ③ snapshots() 的读取契约 ---------------------------------------------

def test_snapshots_reads_the_committed_history_and_skips_what_it_cannot_date(tmp_path, monkeypatch):
    """此前这个函数一行没测过——四条存活变异点都住在这里（含 `capture_output=True`）。"""
    import json as _json
    import subprocess

    repo = tmp_path / 'r'
    repo.mkdir()

    def git(*args):
        subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)

    git('init', '-q')
    git('config', 'user.email', 't@example.com')
    git('config', 'user.name', 't')

    def commit(payload, msg):
        (repo / 'universe.json').write_text(
            payload if isinstance(payload, str) else _json.dumps(payload))
        git('add', 'universe.json')
        git('commit', '-q', '-m', msg)

    commit({'timestamp': '2026-06-25T22:57:38Z',
            'rows': [{'market_cap': 5e9}, {'market_cap': None}]}, 'first')
    commit('', 'empty file is not an empty universe')
    commit({'rows': [{'market_cap': 1e9}]}, 'no timestamp')
    commit({'timestamp': '2026-06-26T22:00:00Z', 'rows': [{'market_cap': 7e9}]}, 'second')
    commit({'timestamp': '2026-06-26T23:30:00Z', 'rows': [{'market_cap': 9e9}]}, 'rerun')

    monkeypatch.chdir(repo)
    out = snapshots(since='2026-01-01', path='universe.json')

    assert sorted(out) == ['2026-06-25', '2026-06-26']
    assert out['2026-06-25'] == [5e9, 0.0]      # null 市值记 0，行不丢
    assert out['2026-06-26'] == [9e9]           # 同一场次重跑，后写的那次算数


def test_an_offset_bearing_timestamp_is_honoured_not_overwritten():
    """带时区的时刻要按它自己的时区换算；当成 UTC 会把这一场记到第二天。"""
    assert et_session('2026-06-26T12:00:00+09:00') == '2026-06-25'
