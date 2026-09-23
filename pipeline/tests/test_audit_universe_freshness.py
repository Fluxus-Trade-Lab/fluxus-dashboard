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


# ============================================================================
# 2026-09-24（T-0924-11）· 变异测出 56 个点里 35 个活着（21/56 = 38%，全库最低）。
# 形状和昨夜的 `audit_universe_population` 一模一样：性质测过了，
# **边界、`main()`、读取端**三处没人看。下面按这三处补，等价变异不硬凑。
#   ① 阈值正好卡在线上时的取舍 + 三个默认常量本身
#   ② `main()` 的三个退出码、`-q` 丢什么、那几列人读的字（此前一行没测过）
#   ③ `snapshots()` 的读取契约（此前完全没测过：空文件、坏 JSON、缺时间戳、缺 rows）
# ============================================================================

import json as _json
import subprocess as _subprocess

from pipeline.tools import audit_universe_freshness as fresh
from pipeline.tools.audit_universe_freshness import _num, snapshots


# ---- ① 边界：正好卡在线上的那一格 -------------------------------------------

def test_exactly_at_the_low_threshold_is_still_a_whole_session():
    """`<` 不是 `<=`：0.5 本身在好的那一侧，判罪要严格越线。"""
    assert classify(0.5, 5_000)[0] is None
    assert classify(0.4999, 5_000)[0] == 'F1'


def test_exactly_at_the_high_threshold_is_still_a_whole_session():
    assert classify(3.0, 5_000)[0] is None
    assert classify(3.0001, 5_000)[0] == 'F2'


def test_exactly_min_names_is_a_universe_one_name_short_is_a_fragment():
    """200 只是「够」的那一侧。`<` 翻成 `<=` 会把正好 200 只的快照判成碎片。"""
    assert classify(0.98, 200)[0] is None
    assert classify(0.98, 199)[0] == 'F3'


def test_the_defaults_are_pinned_by_a_number_that_only_flips_at_the_right_one():
    """钉默认阈值不能靠 `assert HIGH == 3.0`——那是读自己那个常量，
    对真代码和变异体一样绿的那种测试（09-23 那班在 pp 换算上栽过一次）。
    要拿一个**只在正确阈值下才改判**的数去问它：
    「0.024 是 F1、95.4 是 F2」钉不住 HIGH，3.0 挪到 4.0 时 95.4 照样 F2；3.5 不是。
    """
    assert classify(3.5, 5_000)[0] == 'F2'      # HIGH=4.0 时这里会读成干净
    assert classify(0.45, 5_000)[0] == 'F1'     # LOW=0.25 时这里会读成干净


def test_a_non_finite_number_contributes_zero_not_itself():
    """nan/inf 泄进分子，整条比值变 nan，`classify` 的每个比较都读 False——
    **闸会对一份坏货一声不吭**。这是 `_num` 那一行存在的全部理由。"""
    assert _num(float('nan')) == 0.0
    assert _num(float('inf')) == 0.0
    assert _num(float('-inf')) == 0.0
    for poison in (float('nan'), float('inf'), float('-inf')):
        rows = [{'volume': poison, 'avg_volume': 100}, {'volume': 300, 'avg_volume': 100}]
        assert aggregate_rvol(rows) == 1.5, poison


def test_the_smallest_positive_denominator_is_still_a_denominator():
    """判不了的判据是「分母 <= 0」，不是「分母小」。"""
    assert aggregate_rvol([{'volume': 2, 'avg_volume': 1}]) == 2.0


def test_a_timestamp_with_no_zone_is_read_as_utc_not_as_the_machines_clock():
    """没有时区的时刻按 UTC 读——这正是宪法那条「不用本机 JST 钟」的代码版。

    两个时刻各贴着 ET 那一天的两端（00:30 与 23:30）：本机时区一旦被当成
    解释依据，无论它偏东偏西，这两个里至少有一个会掉到隔壁那天去。
    """
    assert et_session('2026-08-11T04:30:00') == '2026-08-11'   # 00:30 ET
    assert et_session('2026-08-12T03:30:00') == '2026-08-11'   # 23:30 ET


# ---- ① 之二：人读的那几句话 -------------------------------------------------

def test_a_lone_bad_snapshot_is_its_own_F4_session():
    """一场只有一份快照、而它是坏的——**这一场同样没有可用的货**。

    `seen > 0` 写成 `seen > 1` 时，单快照的场次会从 F4 里整个漏掉，
    而 08-10 那种「一天只提交过一份」正是最容易只有一份的日子。
    """
    result = check([_rec('2026-08-10', '8fb939f4', 0.0241)])
    assert [v.split()[0] for v in result['violations']] == ['F1', 'F4']


def test_the_violation_line_names_which_snapshot():
    """早上八点读这一行的人要能直接 `git show` 那个 sha。"""
    result = check([_rec('2026-08-19', 'a9e3d319', 0.0083),
                    _rec('2026-08-19', 'd2337e85', 0.9969)])
    assert '(a9e3d319)' in result['violations'][0]


def test_the_F4_line_counts_the_snapshots_it_actually_saw():
    result = check([_rec('2026-08-10', '0b7dfe1c', 0.0241),
                    _rec('2026-08-10', '8fb939f4', 0.0241)])
    f4 = [v for v in result['violations'] if v.startswith('F4')][0]
    assert 'its 2 snapshot(s)' in f4


def test_violations_come_out_in_snapshot_order_within_a_session():
    """同一场里的多份快照按 sha 排，不按调用者递进来的顺序——
    否则同一份历史换个读取顺序就给出另一张报告。"""
    result = check([_rec('2026-08-10', 'ffff0000', 0.0241),
                    _rec('2026-08-10', '0000aaaa', 0.0241)])
    f1s = [v for v in result['violations'] if v.startswith('F1')]
    assert ['(0000aaaa)' in f1s[0], '(ffff0000)' in f1s[1]] == [True, True]


def test_a_record_with_no_names_field_counts_as_zero_names():
    """缺字段记 0 不记 1——F3 那行印的是给人看的数。"""
    result = check([{'session': '2026-06-08', 'snapshot': '56ad6340', 'rvol': 0.94}])
    assert 'only 0 names' in result['warnings'][0]


# ---- ② main() 的三个退出码与 -q 的取舍 --------------------------------------

def _two_rows():
    return [{'session': '2026-08-19', 'snapshot': 'a9e3d319', 'rvol': 0.0083,
             'names': 5618},
            {'session': '2026-08-19', 'snapshot': 'd2337e85', 'rvol': 0.9969,
             'names': 5601},
            {'session': '2026-06-08', 'snapshot': '56ad6340', 'rvol': 0.94,
             'names': 120}]


def test_main_returns_two_when_there_is_nothing_to_check(monkeypatch, capsys):
    """0 个违规和 0 次检查长得一样——这里必须分开，且不能是 0 或 1。"""
    monkeypatch.setattr(fresh, 'snapshots', lambda *a, **k: [])
    assert fresh.main([]) == 2
    assert 'nothing checked' in capsys.readouterr().out


def test_main_is_green_and_prints_the_ok_column_on_a_steady_month(monkeypatch, capsys):
    rows = [{'session': f'2026-08-{d:02d}', 'snapshot': f'sha{d:02d}',
             'rvol': 0.98, 'names': 5_000} for d in range(1, 6)]
    monkeypatch.setattr(fresh, 'snapshots', lambda *a, **k: rows)
    assert fresh.main([]) == 0
    out = capsys.readouterr().out
    assert 'OK  2026-08-01' in out
    assert '0.9800' in out                      # rvol 那一列印的是数，不是「-」
    assert out.strip().endswith('/ 5 session(s)')


def test_main_returns_one_and_names_the_bad_snapshot(monkeypatch, capsys):
    monkeypatch.setattr(fresh, 'snapshots', lambda *a, **k: _two_rows())
    assert fresh.main([]) == 1
    out = capsys.readouterr().out
    assert 'F1  2026-08-19  a9e3d319' in out
    assert 'F1 2026-08-19 (a9e3d319)' in out
    assert 'F3 2026-06-08' in out               # 不静音时警告要印出来


def test_an_undecidable_rvol_prints_a_dash_not_a_crash(monkeypatch, capsys):
    monkeypatch.setattr(fresh, 'snapshots', lambda *a, **k: [
        {'session': '2026-07-15', 'snapshot': 'deadbeef', 'rvol': None,
         'names': 5_000}])
    assert fresh.main([]) == 0
    out = capsys.readouterr().out
    assert 'rvol      -' in out
    assert 'F3 2026-07-15' in out


def test_quiet_drops_the_clean_rows_and_the_warnings_but_never_the_hit(
        monkeypatch, capsys):
    monkeypatch.setattr(fresh, 'snapshots', lambda *a, **k: _two_rows())
    assert fresh.main(['-q']) == 1
    out = capsys.readouterr().out
    assert 'a9e3d319' in out                    # 出事那一行永不丢
    assert 'd2337e85' not in out                # 干净行丢掉
    assert 'F3 2026-06-08' not in out           # P3 警告丢掉


def test_the_json_report_is_written_and_carries_the_violations(monkeypatch, tmp_path):
    monkeypatch.setattr(fresh, 'snapshots', lambda *a, **k: _two_rows())
    out = tmp_path / 'report.json'
    assert fresh.main(['--json', str(out)]) == 1
    payload = _json.loads(out.read_text())
    assert payload['snapshots'] == 3 and payload['sessions'] == 2
    assert payload['ok'] is False
    assert any(v.startswith('F1 2026-08-19') for v in payload['violations'])
    assert (payload['low'], payload['high']) == (0.5, 3.0)


# ---- ③ snapshots() 的读取契约（此前一行没测过）------------------------------

def test_snapshots_reads_committed_history_and_skips_what_it_cannot_judge(
        tmp_path, monkeypatch):
    """六个存活变异点住在这个函数里，包括两处 `text=True`——
    它一旦拿回 bytes，`git show` 会拿着 `b'...'` 去查、一份货都读不到，
    而这道闸的结论会变成「没有违规」。
    """
    repo = tmp_path / 'r'
    repo.mkdir()

    def git(*args):
        _subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True)

    git('init', '-q')
    git('config', 'user.email', 't@example.com')
    git('config', 'user.name', 't')

    def commit(payload, msg):
        (repo / 'universe.json').write_text(
            payload if isinstance(payload, str) else _json.dumps(payload))
        git('add', 'universe.json')
        git('commit', '-q', '-m', msg)

    commit({'timestamp': '2026-08-10T09:31:43.747903+00:00',      # 05:31 ET 盘前
            'rows': [{'volume': 241, 'avg_volume': 10_000}] * 3}, 'premarket')
    commit('', 'empty file is not an empty universe')
    commit('{not json', 'a half-written payload is not a universe')
    commit({'rows': [{'volume': 1, 'avg_volume': 1}]}, 'no timestamp, no session')
    commit({'timestamp': '2026-08-11T01:30:00+00:00'}, 'no rows at all')  # 21:30 ET 前一天

    monkeypatch.chdir(repo)
    out = snapshots(since='2026-01-01', path='universe.json')

    assert [r['session'] for r in out] == ['2026-08-10', '2026-08-10']   # 旧的在前
    assert len(out[0]['snapshot']) == 8                                  # 短 sha 八位
    assert out[0]['names'] == 3
    assert round(out[0]['rvol'], 4) == 0.0241
    assert out[1]['names'] == 0 and out[1]['rvol'] is None               # 缺 rows 不是崩
    assert out[1]['timestamp'] == '2026-08-11T01:30:00+00:00'


def test_snapshots_returns_nothing_when_the_path_was_never_committed(
        tmp_path, monkeypatch):
    """「一份都没查到」要能一路传到 main() 的退出码 2，不能读成「干净」。"""
    repo = tmp_path / 'r'
    repo.mkdir()
    _subprocess.run(['git', 'init', '-q'], cwd=repo, check=True, capture_output=True)
    monkeypatch.chdir(repo)
    assert snapshots(since='2026-01-01', path='universe.json') == []
