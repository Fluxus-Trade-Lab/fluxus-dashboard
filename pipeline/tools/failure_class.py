"""上游拒绝了我们，还是我们拒绝了自己？——夜间失败班的分诊器。

写于 2026-09-03/04 事故之后。那晚的账本长这样：

    23:29 schedule  quality ok      tradeable 2553  errors 0   ← 失败
    02:09 dispatch  quality severe  tradeable   16  errors 1
    02:31 dispatch  quality ok      tradeable 2554  errors 0   ← 失败
    02:58 dispatch  quality severe  tradeable   42  errors 1
    03:16 dispatch  quality severe  tradeable   42  errors 1
    03:48 dispatch  quality severe  tradeable   46  errors 1
    04:17 dispatch  quality severe  tradeable    0  errors 1
    05:19 dispatch  quality severe  tradeable    7  errors 1
    06:12 schedule  quality ok      tradeable 2553  errors 0   ← 成功

两班好数据（23:29 死在 shortlist_log 一行重复，02:31 死在 audit_ledger 的
no_downgrade 分类 bug）被整包丢弃，然后我们用「重抓」去修闸的问题。五次
全量重拉把 runner 的机房 IP 从 429 打到 401 Invalid Crumb，可交易数归零。
dashboard 停更两天，而那两天的数据我们其实抓到过两次。

**这两种失败的正确下一步是相反的**，而在日志里它们长得一样（都是红的
`Process completed with exit code 1`）：

    上游拒绝我们  →  等，然后再抓。抓得越快越糟。
    我们拒绝自己  →  **不要再抓**。数据是好的，去修闸、重审、提交。

所以这个模块只做一件事：**读账本，说出这是哪一种**。它不修任何东西，
也不该修——它存在的意义是让下一个人（或下一个会话）在按下重跑之前，
先被告知按下去有没有意义。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

LEDGER = Path("data/history/run_ledger.jsonl")

#: 可交易占全宇宙的比例低于此值，视为上游没给回价格。健康夜间是 45% 上下
#: （2026-09-03 的两班好数据：2553/5630 与 2554/5630）；被限流的班次是
#: 0.3% 以下（16、42、46、0、7）。两群之间差两个数量级，阈值放哪都行，
#: 放在 5% 是为了让「市场真的烂到没票可交易」也不会误触。
TRADEABLE_FLOOR = 0.05

#: 分诊结论。字符串是给人读的，键是给脚本判的。
CLASSES = {
    "OK": "这一班没有失败",
    "A_infra": "基建：这一班没在账本里留下任何记录，说明它死在跑起管线之前",
    "B_vendor": "上游拒绝：拿回来的价格不成样子（quality severe / 可交易崩塌）",
    "C_gate": "我们拒绝了自己：抓取正常，是下游的闸不让发",
    "D_code": "代码：管线自己抛了异常",
}

#: 每一类唯一正确的下一步。措辞是命令式的，因为这张表存在的全部理由，
#: 就是 2026-09-04 那晚没人对着它做决定。
NEXT_ACTION = {
    "OK": "无。",
    "A_infra": "可以直接重跑（幂等）。先确认不是排程被 GitHub 丢弃——那需要 backstop 而不是重试。",
    "B_vendor": "**不要立刻重跑。** 全量重拉正是把 429 变成 401 的那个动作。等一个退避窗口，"
                "或者干脆等下一个原生排程窗口（历史上 21:30Z 那一班一直通）。",
    "C_gate": "**绝对不要重抓。** 这一班的数据是好的。去 GitHub 把这次 run 的 "
              "`data-output-<run_id>` artifact 下载下来，修掉闸报的那一条，重审，提交。"
              "重抓只会用一份更差的数据覆盖一份更好的。",
    "D_code": "修代码，加一条能红的测试，再重跑。重跑不会让 traceback 消失。",
}


def _tradeable_share(guards: Dict) -> Optional[float]:
    uq = guards.get("universe_quality") or {}
    rows = uq.get("rows")
    tr = (uq.get("tradeable") or {}).get("tradeable")
    if not rows or tr is None:
        return None
    return tr / rows


def _looks_like_traceback(errors: List[Dict]) -> bool:
    for e in errors:
        msg = str(e.get("msg", ""))
        if "Traceback" in msg or "Error:" in msg or "Exception" in msg:
            return True
    return False


def classify(record: Optional[Dict], failed: bool = True) -> Dict:
    """给一条**失败**班次的账本记录分诊。record 为 None＝这一班没留下记录。

    `failed=False` 时直接返回 `OK`。这个参数不是装饰：分诊读的是抓取的
    读数，而一班成功的夜跑读数当然正常，所以它会被判成「闸拒了好数据」
    ——一个只在失败前提下才成立的结论。回放 2026-09-03 时 06:12 那班
    （成功、并且就是它把数据补回来的）正是这样被误判的，所以前提被提到
    了签名里，而不是留在文档里等人记得。

    顺序是有意的：代码异常在最前（它会把别的读数弄脏），上游次之
    （severe 时下游的闸怎么判都不作数），我们自己的闸最后——只有在
    抓取确实正常时，「闸拒了好数据」这个判断才成立。
    """
    if not failed:
        return {"klass": "OK", "why": "这一班没有失败，无需分诊", "evidence": {}}

    if record is None:
        return {"klass": "A_infra", "why": "账本里没有这一班的记录",
                "evidence": {}}

    guards = record.get("guards") or {}
    errors = record.get("errors") or []
    uq = guards.get("universe_quality") or {}
    share = _tradeable_share(guards)
    evidence = {
        "run_id": record.get("run_id"),
        "started_utc": record.get("started_utc"),
        "universe_quality": uq.get("status"),
        "tradeable": (uq.get("tradeable") or {}).get("tradeable"),
        "rows": uq.get("rows"),
        "tradeable_share": None if share is None else round(share, 4),
        "errors": len(errors),
    }

    if _looks_like_traceback(errors):
        return {"klass": "D_code", "why": "errors 里有 traceback", "evidence": evidence}

    if uq.get("status") == "severe" or (share is not None and share < TRADEABLE_FLOOR):
        why = []
        if uq.get("status") == "severe":
            why.append("universe_quality=severe")
        if share is not None and share < TRADEABLE_FLOOR:
            why.append(f"可交易占比 {share:.2%} < {TRADEABLE_FLOOR:.0%}")
        return {"klass": "B_vendor", "why": "；".join(why), "evidence": evidence}

    return {"klass": "C_gate",
            "why": "抓取的读数正常（quality 非 severe、可交易占比正常、无异常），"
                   "这一班是被下游的闸挡住的",
            "evidence": evidence}


def load_ledger(path: Path = LEDGER) -> List[Dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def find_run(records: List[Dict], run_id: str) -> Optional[Dict]:
    for r in records:
        if str(r.get("run_id")) == str(run_id):
            return r
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="夜间失败班分诊：上游拒绝了我们，还是我们拒绝了自己")
    ap.add_argument("--run-id", help="GitHub run id；不给则分诊账本最后一班")
    ap.add_argument("--ledger", default=str(LEDGER))
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    ap.add_argument("--session", help="按 session 列出该日全部班次的分诊")
    ap.add_argument("--succeeded", action="store_true",
                    help="这一班其实成功了——分诊只对失败班有意义")
    ap.add_argument("--ok-runs", default="",
                    help="--session 用：逗号分隔的成功 run id，它们会标成 OK 而不是被分诊")
    args = ap.parse_args(argv)

    records = load_ledger(Path(args.ledger))
    if not records:
        print("账本为空或不存在，无法分诊", file=sys.stderr)
        return 2

    if args.session:
        ok_runs = {s.strip() for s in args.ok_runs.split(",") if s.strip()}
        rows = [r for r in records if r.get("session") == args.session]
        for r in rows:
            rid = str(r.get("run_id"))
            v = classify(r, failed=rid not in ok_runs)
            e = v["evidence"] or {"run_id": rid,
                                  "started_utc": r.get("started_utc")}
            print(f"{e['run_id']:<13}{str(e['started_utc'])[11:16]:<7}"
                  f"{v['klass']:<10}{v['why']}")
        return 0

    rec = find_run(records, args.run_id) if args.run_id else records[-1]
    verdict = classify(rec, failed=not args.succeeded)

    if args.json:
        print(json.dumps(verdict, ensure_ascii=False))
        return 0

    k = verdict["klass"]
    print(f"分诊：{k} — {CLASSES[k]}")
    print(f"依据：{verdict['why']}")
    print(f"读数：{json.dumps(verdict['evidence'], ensure_ascii=False)}")
    print()
    print(f"下一步：{NEXT_ACTION[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
