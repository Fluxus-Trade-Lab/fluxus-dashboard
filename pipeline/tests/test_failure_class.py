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


# ---------------------------------------------------------------------------
#  2026-09-30 的第二张考卷：抓取被腰斩
# ---------------------------------------------------------------------------
#
# `fixtures/run_ledger_2026-09-30.jsonl` 是三条真实记录，逐字取自
# data/history/run_ledger.jsonl：
#
#     36637199694  09-29 22:04  rows 5612 / claimed 5612   成功
#     36783219599  09-30 22:03  rows 1000 / claimed 5613   失败
#     36785607847  09-30 22:27  rows 1000 / claimed 5613   失败
#
# 那两班失败的原因是 Finviz 在第 51 页（r=1001）起返回 403，宇宙被砍到 18%。
# 而分诊器当时说 **C_gate**——「数据是好的，去下载 artifact 发布」。照它说的
# 做，会把一份 1000 行的宇宙当全市场发上 dashboard：广度、RS、新高新低全错。
#
# 它为什么答错，是这一节真正要钉住的东西：旧判据只有 `tradeable_share`，
# 而那是**已抓行内**的比例，对截断免疫。449/1000 = 44.9%，和健康夜间的
# 45% 一模一样。缺的行连分母都没进去。
FIXTURE_0930 = Path(__file__).parent / "fixtures" / "run_ledger_2026-09-30.jsonl"

TRUNCATED_RUNS = ("36783219599", "36785607847")
HEALTHY_RUN = "36637199694"


@pytest.fixture(scope="module")
def records_0930():
    recs = load_ledger(FIXTURE_0930)
    assert len(recs) == 3, "考卷少了几班，先看 fixture 是不是被动过"
    return recs


@pytest.mark.parametrize("run_id", TRUNCATED_RUNS)
def test_a_halved_universe_is_not_called_a_gate_problem(records_0930, run_id):
    """两班真实的截断必须判 E_truncated——判成 C_gate 就会有人去发布它。"""
    rec = find_run(records_0930, run_id)
    assert rec is not None
    v = classify(rec)
    assert v["klass"] == "E_truncated", v["why"]
    assert "不要发布" in NEXT_ACTION[v["klass"]]


@pytest.mark.parametrize("run_id", TRUNCATED_RUNS)
def test_the_old_ruler_cannot_see_this_shape(records_0930, run_id):
    """阳性对照①「漏改」：证明旧判据在这两班上读数是健康的。

    如果哪天有人把 E_truncated 那一支删掉，`tradeable_share` 会照样落在
    健康带里，于是又回到 C_gate——这条断言就是那个回归的检波器。它断言的
    不是「新代码对」，是「旧代码在这里必然瞎」。
    """
    v = classify(find_run(records_0930, run_id))
    share = v["evidence"]["tradeable_share"]
    assert share > TRADEABLE_FLOOR * 5, "旧判据在这一班上并不报警"
    assert 0.40 < share < 0.50, f"{share}: 和健康夜间的 45% 处在同一带"
    # 真正把它和健康夜间分开的是这一个数，不是上面那一个。
    assert v["evidence"]["universe_share"] < 0.2


def test_a_complete_universe_is_still_a_gate_problem(records_0930):
    """阳性对照②「改了但接错」：rows == claimed 的班次不许被新判据抓走。

    账本里 53 班健康夜间 rows 与 finviz_claimed 逐字相等，所以这一支只要
    阈值或分母写反（比如拿 claimed/rows），整段历史会立刻被判成截断。
    """
    rec = json.loads(json.dumps(find_run(records_0930, HEALTHY_RUN)))
    uq = rec["guards"]["universe_quality"]
    assert uq["rows"] == uq["finviz_claimed"]
    v = classify(rec)
    assert v["klass"] == "C_gate", v["why"]
    assert v["evidence"]["universe_share"] == 1.0


def test_a_traceback_still_outranks_truncation(records_0930):
    """代码异常仍在最前：它会把 rows 也弄脏，先修代码。"""
    rec = json.loads(json.dumps(find_run(records_0930, TRUNCATED_RUNS[0])))
    rec["errors"] = [{"where": "run_all", "msg": "Traceback (most recent call last): ..."}]
    assert classify(rec)["klass"] == "D_code"


def test_truncation_outranks_a_healthy_looking_quality_status(records_0930):
    """`universe_quality: ok` 不能盖过截断——那两班的 status 正是 ok。"""
    rec = find_run(records_0930, TRUNCATED_RUNS[0])
    assert rec["guards"]["universe_quality"]["status"] == "ok"
    assert classify(rec)["klass"] == "E_truncated"


def test_missing_claimed_total_falls_back_instead_of_crashing(records_0930):
    """2026-08-20 之前的账本没有 finviz_claimed；老记录不许让分诊器炸。"""
    rec = json.loads(json.dumps(find_run(records_0930, TRUNCATED_RUNS[0])))
    del rec["guards"]["universe_quality"]["finviz_claimed"]
    v = classify(rec)
    assert v["klass"] == "C_gate"
    assert v["evidence"]["universe_share"] is None


def test_the_short_scrape_threshold_has_exactly_one_home():
    """`run_all` 的 short-scrape 日志与本模块必须用同一个阈值。

    两处各写一个 0.9 时，短抓会在日志里报红、同时在分诊器里被叫成
    「数据是好的，去发布」——2026-09-30 就是这么过去的。
    """
    from pipeline.tools.failure_class import UNIVERSE_COMPLETE_FLOOR
    src = (Path(__file__).parents[1] / "screeners" / "run_all.py").read_text()
    assert "UNIVERSE_COMPLETE_FLOOR * claimed" in src
    assert "0.9 * claimed" not in src, "run_all 又自己拍了一个阈值"
    assert UNIVERSE_COMPLETE_FLOOR == 0.9
