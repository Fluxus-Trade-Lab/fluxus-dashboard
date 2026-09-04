"""分诊器必须一直答对 2026-09-03 那张考卷。

考卷不是编的：`fixtures/run_ledger_2026-09-03.jsonl` 是当晚 run_ledger 的
九条真实记录，逐字取自 origin/main。那一晚的账是这样的——

    23:29  quality ok      tradeable 2553   失败（shortlist_log 一行重复）
    02:09  quality severe  tradeable   16   失败
    02:31  quality ok      tradeable 2554   失败（audit_ledger no_downgrade bug）
    02:58  quality severe  tradeable   42   失败
    03:16  quality severe  tradeable   42   失败
    03:48  quality severe  tradeable   46   失败
    04:17  quality severe  tradeable    0   失败
    05:19  quality severe  tradeable    7   失败
    06:12  quality ok      tradeable 2553   成功

两班好数据被自己的闸扔掉，然后五次全量重拉把机房 IP 从 429 打到 401，
dashboard 停更两天——而那两天的数据我们抓到过两次。

分诊器存在的唯一理由，是在按下重跑之前说出「这一班的数据是好的」。
所以这份测试盯的就是那两格：**23:29 和 02:31 必须是 C_gate**。
它们要是哪天变成 B_vendor，事故就能原样再来一次。
"""
import json
from pathlib import Path

import pytest

from pipeline.tools.failure_class import (
    NEXT_ACTION, TRADEABLE_FLOOR, classify, find_run, load_ledger,
)

LEDGER = Path(__file__).parent / "fixtures" / "run_ledger_2026-09-03.jsonl"

#: 当晚真实的分诊答案。key 是 run_id，value 是这一班该被判成什么。
#: 06:12 是那晚唯一成功的一班，所以它进 OK_RUNS 而不是这张表。
EXPECTED = {
    "33817766335": "C_gate",    # 23:29 数据好，死在 shortlist_log 重复行
    "33828373698": "B_vendor",  # 02:09 tradeable 16
    "33829804995": "C_gate",    # 02:31 数据好，死在 no_downgrade 分类 bug
    "33831418753": "B_vendor",  # 02:58 tradeable 42
    "33832579731": "B_vendor",  # 03:16 tradeable 42
    "33834496056": "B_vendor",  # 03:48 tradeable 46
    "33836209238": "B_vendor",  # 04:17 tradeable 0
    "33840040911": "B_vendor",  # 05:19 tradeable 7
}
OK_RUNS = {"33843343359"}       # 06:12，成功的那一班


@pytest.fixture(scope="module")
def records():
    recs = load_ledger(LEDGER)
    assert len(recs) == 9, "考卷少了几班，先看 fixture 是不是被动过"
    return recs


@pytest.mark.parametrize("run_id,expected", sorted(EXPECTED.items()))
def test_the_real_night_is_classified_correctly(records, run_id, expected):
    rec = find_run(records, run_id)
    assert rec is not None
    assert classify(rec)["klass"] == expected


def test_the_two_discarded_good_nights_say_do_not_refetch(records):
    """这条是整个模块的存在理由。

    23:29 和 02:31 手里都攥着完整的一晚数据。那晚给出的下一步是「再抓一遍」，
    代价是两天。分诊器给的下一步必须是相反的那句。
    """
    for run_id in ("33817766335", "33829804995"):
        v = classify(find_run(records, run_id))
        assert v["klass"] == "C_gate"
        assert "不要重抓" in NEXT_ACTION[v["klass"]]
        assert v["evidence"]["tradeable"] > 2000


def test_the_throttled_nights_say_do_not_retry_now(records):
    """B 类的下一步同样是「别立刻重跑」，但理由不同：抓不回来，不是不该抓。"""
    v = classify(find_run(records, "33836209238"))   # 04:17，tradeable 0
    assert v["klass"] == "B_vendor"
    assert "不要立刻重跑" in NEXT_ACTION[v["klass"]]


def test_a_successful_run_is_not_diagnosed(records):
    """06:12 成功了，读数当然正常——不加这个前提它会被判成 C_gate。

    这个陷阱是回放真账本时撞出来的，不是想出来的：分诊读的是抓取质量，
    而成功的夜跑抓取质量最好。
    """
    rec = find_run(records, "33843343359")
    assert classify(rec, failed=False)["klass"] == "OK"
    assert classify(rec, failed=True)["klass"] == "C_gate"   # 少了前提就误判


def test_a_run_with_no_ledger_entry_is_infra(records):
    assert classify(None)["klass"] == "A_infra"


def test_a_traceback_outranks_everything(records):
    """代码异常会把别的读数弄脏，所以它排在最前。"""
    rec = json.loads(json.dumps(find_run(records, "33829804995")))
    rec["errors"] = [{"where": "run_all", "msg": "Traceback (most recent call last): ..."}]
    assert classify(rec)["klass"] == "D_code"


def test_the_floor_separates_the_two_populations(records):
    """健康夜 45%、被限流夜 0.8% 以下——阈值放在两群之间，不是拍在某一群边上。"""
    healthy, throttled = [], []
    for r in records:
        v = classify(r)
        share = v["evidence"].get("tradeable_share")
        if share is None:
            continue
        (healthy if v["klass"] == "C_gate" else throttled).append(share)
    assert min(healthy) > TRADEABLE_FLOOR * 5
    assert max(throttled) < TRADEABLE_FLOOR / 5
