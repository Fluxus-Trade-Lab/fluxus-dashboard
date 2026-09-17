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
