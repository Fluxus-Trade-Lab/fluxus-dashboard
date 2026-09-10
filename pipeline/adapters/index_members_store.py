"""S&P 500 成员台账 —— 存名单、记变动、挡抓漏。

**为什么要存名单**(2026-09-10 Andy 问「成员是会变动的,有这样的机制吗」):
在此之前我们每晚现抓 Finviz 的 idx_sp500,所以变动**跟得上**;但名单算完就扔,
归档里只留一个计数 `sp500_members`。后果有三:
  1. 答不出「谁进谁出、哪天」;
  2. 任何历史回填只能用**今天**的成分股 —— 幸存者偏差;
  3. 抓回 480 只也照算,没有任何东西喊一声。

**变动有多频繁**(2026-09-10 查证,不是凭印象):历史换手率约 **4.4%/年 ≈ 22 次**,
且**不是**集中在季度调仓 —— 1995 年以来落在 3/6/9/12 月第三个周五的反而是少数,
多数由并购、退市、不再合规触发,任何一天都可能发生。所以**不能**改成「一年查一两次」,
夜间现抓保留;这个模块加的是**记账**,不是降频。

两个文件:
  `data/reference/sp500_members.json`   当前名单(每晚重写)+ 每只的 first_seen
  `data/reference/sp500_members_log.csv` 追加式变动流水(date, action, ticker)

**抓漏保护是这个模块的主张。** Finviz 的成员页要翻 ~26 页;翻到一半失败会返回一个
**结构完好但内容残缺**的集合。没有保护时,那一晚会被记成「80 只同时被剔除」——
一条永久的假历史,而且下一晚它们又「加回来」。所以:单晚变动超过阈值时**拒绝写入**,
保留上一版名单并报警。宁可停在昨天的名单,也不要在台账里刻一条假的大换血。
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

ROSTER = Path("data/reference/sp500_members.json")
CHANGELOG = Path("data/reference/sp500_members_log.csv")

# 单晚允许的净变动上限。真实换手 ~22 次/年,一晚超过 15 只几乎一定是抓漏
# 而不是市场事件 —— 即使是标普历史上最剧烈的 1976 年(全年换 60 只),
# 单日也远不到这个数。
MAX_DAILY_CHANGE = 15

# 名单小于这个数一定是残缺:标普 500 的成分股数常年在 500-505 之间
# (少数公司有多个股份类别,如 GOOG/GOOGL)。
MIN_PLAUSIBLE_MEMBERS = 480


class MembershipRejected(Exception):
    """抓来的名单不可信,调用方应保留上一版。"""


def load_roster(path: Optional[Path] = None) -> Dict[str, str]:
    """读当前名单 -> {ticker: first_seen}。文件不存在返回空 dict。

    ⚠️ 路径**在调用时**解析,不写成 `path: Path = ROSTER`。默认参数在函数定义时
    就求值绑死,monkeypatch 模块属性对它无效 —— 2026-09-10 就因为这个,一批测试
    静默把假名单(PAD0001…)写进了真仓库的 data/reference/。
    """
    path = path or ROSTER
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text()))
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning("sp500 roster unreadable at %s - treating as empty", path)
        return {}


def diff(previous: Iterable[str], current: Iterable[str]) -> Tuple[List[str], List[str]]:
    """返回 (新进, 剔除),都按字母序。"""
    prev, cur = set(previous), set(current)
    return sorted(cur - prev), sorted(prev - cur)


def vet(current: Set[str], previous: Dict[str, str]) -> None:
    """抓来的名单可信吗?不可信就抛 MembershipRejected。

    ⚠️ 首次建账(previous 为空)只查绝对规模,不查变动量 —— 否则第一晚
    503 只全是「新进」,必然超阈值,台账永远建不起来。
    """
    if len(current) < MIN_PLAUSIBLE_MEMBERS:
        raise MembershipRejected(
            f"只抓到 {len(current)} 只,低于 {MIN_PLAUSIBLE_MEMBERS} —— 判为抓漏,不是市场事件")
    if not previous:
        return
    added, dropped = diff(previous, current)
    churn = len(added) + len(dropped)
    if churn > MAX_DAILY_CHANGE:
        raise MembershipRejected(
            f"单晚变动 {churn} 只(进 {len(added)} / 出 {len(dropped)}),"
            f"超过上限 {MAX_DAILY_CHANGE} —— 判为抓漏,保留上一版名单")


def update(
    current: Set[str],
    as_of: str,
    roster_path: Optional[Path] = None,
    log_path: Optional[Path] = None,
) -> Dict[str, object]:
    """核验 -> 写名单 -> 追加变动流水。返回本次的摘要。

    抛 MembershipRejected 时**什么都不写**,上一版名单原封不动。
    """
    roster_path = roster_path or ROSTER
    log_path = log_path or CHANGELOG
    previous = load_roster(roster_path)
    vet(current, previous)                      # 不可信直接抛,先于任何写入

    added, dropped = diff(previous, current)
    roster = {t: (previous.get(t) or as_of) for t in sorted(current)}

    roster_path.parent.mkdir(parents=True, exist_ok=True)
    roster_path.write_text(json.dumps(roster, indent=0, sort_keys=True))

    # ⚠️ 首建不写流水:那 503 只不是「今晚新进」,它们本来就在指数里。
    # 把快照记成 503 条 add,会让流水从第一行起就是假的 —— 流水记的是**变动**,
    # 而首建没有「之前」可以变。回放的起点由名单里最早的 first_seen 界定。
    if (added or dropped) and previous:
        new_file = not log_path.exists()
        with log_path.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new_file:
                w.writerow(["date", "action", "ticker"])
            for t in added:
                w.writerow([as_of, "add", t])
            for t in dropped:
                w.writerow([as_of, "drop", t])
        logger.info("sp500 membership %s: +%d -%d", as_of, len(added), len(dropped))

    return {
        "as_of": as_of,
        "members": len(roster),
        "added": added,
        "dropped": dropped,
        "first_build": not previous,
    }


def members_on(as_of: str, log_path: Optional[Path] = None,
               roster_path: Optional[Path] = None) -> Optional[Set[str]]:
    """把名单回放到某一天 —— 让历史回填不必用今天的成分股。

    从当前名单往回放流水:比 as_of **晚**的每一条,进的减掉、出的加回。
    早于流水第一条日期时返回 None(那段历史我们没有记录,不许瞎猜)。
    """
    log_path = log_path or CHANGELOG
    full = load_roster(roster_path)
    roster = set(full)
    if not roster:
        return None
    # 台账建立之前的日期我们没有记录 —— 返回 None,不许拿今天的名单冒充。
    # 界碑是名单里最早的 first_seen(首建那晚),不是流水第一行:名单可能
    # 好几个月没变过,那几个月流水里一行都没有,却是有记录的。
    if as_of < min(full.values()):
        return None
    if not log_path.exists():
        return roster
    with log_path.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in sorted(rows, key=lambda r: r["date"], reverse=True):
        if r["date"] <= as_of:
            break
        if r["action"] == "add":
            roster.discard(r["ticker"])
        elif r["action"] == "drop":
            roster.add(r["ticker"])
    return roster


def today() -> str:
    """交易日期一律走 marketcal(ET),不用本机 JST 时钟。

    用 `market_today` 而不是 `last_trading_day`:台账记的是「我们这一晚看到的名单」,
    周末跑一次也该按当天记,不该记到上周五头上。
    """
    from pipeline import marketcal  # noqa: PLC0415
    return marketcal.market_today().isoformat()
