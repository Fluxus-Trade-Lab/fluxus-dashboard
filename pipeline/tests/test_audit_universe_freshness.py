"""时点闸：先证明它对每一种「能坏的方式」都报得出，再信它的绿。

真实历史那一跑（156 个快照，逐个 `git show`）要几分钟，不放 CI；这里钉性质。
阳性对照**按失败方式分类造**，不是造一个了事——这把尺子有两个方向会坏：
货是半天的（分子塌）、尺子没了（分母塌），只造一个方向只能证明它认得出
「什么都没做」。再加一条会话级的：一场里每一份快照都坏，和一场里有一份坏，
是两件事。

真实读数（工具 docstring 里有全文）：5 条 F1、8 条 F2、9 场 F4。
"""
from __future__ import annotations

from pipeline.tools.audit_universe_freshness import (
    aggregate_rvol, check, classify, et_session,
)


def _rows(n, volume, avg_volume):
    return [{'volume': volume, 'avg_volume': avg_volume} for _ in range(n)]


def _rec(session, snapshot, rvol, names=5000):
    return {'session': session, 'snapshot': snapshot, 'rvol': rvol, 'names': names}


def _steady(days, rvol=0.98):
    return [_rec(f'2026-08-{d:02d}', f'sha{d:02d}', rvol) for d in days]


# ---------------------------------------------------------------- the quantity

def test_aggregate_rvol_is_a_ratio_of_sums_not_a_mean_of_ratios():
    """99 只小票放量 50 倍、一只巨头照常——市场并没有停摆，闸不许响。

    逐只求比值再取平均会读出 49.5（F2 红）；加总求比再相除读出 1.05（绿）。
    这两个数在同一份数据上差 47 倍，所以口径不是风格问题。
    """
    rows = _rows(99, 50_000, 1_000) + [{'volume': 100_000_000,
                                        'avg_volume': 100_000_000}]
    assert round(aggregate_rvol(rows), 4) == 1.0485       # 104_950_000 / 100_099_000
    assert classify(aggregate_rvol(rows), 5_000)[0] is None
    mean_of_ratios = (99 * 50 + 1) / 100
    assert classify(mean_of_ratios, 5_000)[0] == 'F2'     # 同一份数据，另一种口径


def test_missing_values_count_as_zero_on_both_sides():
    """这是 F2 能成立的原因：分母死了，比值必须离开区间，不能悄悄停在 1.0。"""
    assert aggregate_rvol(_rows(10, 5_000, None)) is None
    rows = _rows(9, 5_000, None) + [{'volume': 5_000, 'avg_volume': 500}]
    assert aggregate_rvol(rows) == 100.0                  # 50_000 / 500


def test_non_numeric_and_bool_contribute_nothing():
    rows = [{'volume': True, 'avg_volume': 'n/a'}, {'volume': 300, 'avg_volume': 100}]
    assert aggregate_rvol(rows) == 3.0


def test_zero_denominator_is_undecidable_not_zero():
    """判不了必须是 None——返回 0.0 会被当成 F1，把「不知道」印成「有罪」。"""
    assert aggregate_rvol(_rows(10, 5_000, 0)) is None
    assert aggregate_rvol([]) is None


# ------------------------------------------------- 阳性对照 · 按失败方式分类造

def test_positive_control_premarket_payload_is_F1():
    """失败方式一：分子塌。2026-08-10 05:31 的形状，实测 rvol 0.0241。"""
    kind, why = classify(aggregate_rvol(_rows(5_618, 241, 10_000)), 5_618)
    assert kind == 'F1'
    assert 'not a completed session' in why


def test_positive_control_avg_volume_outage_is_F2():
    """失败方式二：分母塌。2026-07-15..24 的形状，实测 rvol 95–347。"""
    rows = _rows(2_999, 500_000, None) + [{'volume': 500_000, 'avg_volume': 5_000}]
    kind, why = classify(aggregate_rvol(rows), 3_000)
    assert kind == 'F2'
    assert 'avg_volume died' in why


def test_positive_control_a_session_with_only_bad_snapshots_is_F4():
    """失败方式三：会话级。08-10 那场两份快照都是盘前，它没有可用的货。"""
    result = check([_rec('2026-08-10', '0b7dfe1c', 0.0241),
                    _rec('2026-08-10', '8fb939f4', 0.0241)])
    assert not result['ok']
    assert any(v.startswith('F4 2026-08-10') for v in result['violations'])
    assert 'no usable payload' in ' '.join(result['violations'])


def test_a_bad_snapshot_beside_a_clean_one_is_F1_but_not_F4():
    """08-17/08-19 的形状：坏的那份仍要点名，但这一场是有货的。"""
    result = check([_rec('2026-08-19', 'a9e3d319', 0.0083),
                    _rec('2026-08-19', 'd2337e85', 0.9969)])
    kinds = [v.split()[0] for v in result['violations']]
    assert kinds == ['F1']


# ------------------------------------------------------------- 阴性对照与边界

def test_a_month_of_normal_sessions_is_silent():
    result = check(_steady(range(1, 21)))
    assert result['ok'], result['violations']
    assert result['warnings'] == []


def test_the_whole_measured_good_band_stays_silent():
    """实测 143 份好快照落在 0.611–1.969；两端都必须绿，否则阈值定错了。"""
    for rvol in (0.611, 0.98, 1.969):
        assert classify(rvol, 5_000)[0] is None, rvol


def test_the_empty_bands_are_wide_enough_that_the_thresholds_are_arbitrary():
    """阈值落在空档里：实测最近的坏值是 0.024 和 95.4，挪一倍也不改判。"""
    assert classify(0.0241, 5_000)[0] == 'F1'
    assert classify(95.4, 5_000)[0] == 'F2'
    assert classify(0.0241, 5_000, low=0.25)[0] == 'F1'
    assert classify(95.4, 5_000, high=6.0)[0] == 'F2'


def test_a_fragment_is_not_judged_and_never_fatal():
    """2026-06-08 写过一份 200 行的桩：判不了要说判不了，不能算违规。"""
    result = check([_rec('2026-06-08', '56ad6340', 0.94, names=120)])
    assert result['ok']
    assert result['warnings'] and result['warnings'][0].startswith('F3')


def test_an_unjudgeable_session_does_not_trigger_F4():
    """F3 不是罪名。一场只有判不了的快照，不该被记成「这场没有货」。"""
    result = check([_rec('2026-06-08', '56ad6340', None, names=120)])
    assert result['ok'], result['violations']


def test_an_empty_input_is_not_a_pass_at_the_cli_level():
    """check() 对空输入返回 ok，所以「没东西可查」必须在 main() 拦（返回 2）。"""
    assert check([])['ok'] is True
    assert check([])['snapshots'] == 0


# ------------------------------------------------------------------ 时区陷阱

def test_session_comes_from_the_payload_timestamp_in_ET():
    """22:5x UTC 在 JST 是次日；标签只认 payload 自己的时刻，不认 commit 日期。"""
    assert et_session('2026-08-10T09:31:43.747903+00:00') == '2026-08-10'   # 05:31 ET
    assert et_session('2026-09-18T23:13:52+00:00') == '2026-09-18'          # 19:13 ET
    assert et_session('2026-08-11T01:30:00+00:00') == '2026-08-10'          # 21:30 ET 前一天


def test_a_bad_timestamp_is_not_a_session():
    assert et_session(None) is None
    assert et_session('not a time') is None
