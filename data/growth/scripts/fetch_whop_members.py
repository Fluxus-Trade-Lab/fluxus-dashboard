#!/usr/bin/env python3
"""Whop 只读取数 → data/growth/metrics.csv 当周行的 notes（Growth Gary · T-0922-110）。

口径（2026-09-22 核 Whop 官方文档 https://docs.whop.com/api-reference/memberships/list-memberships）：
- 分页是**游标**：`first`/`after` + `page_info.has_next_page`/`end_cursor`；不认 offset/limit。
  不传 `first` 时默认每页 20 条。v1 脚本（cab3a7d8）用 offset/limit 且拿「本页 < 100 条」当末页，
  于是只读了第一页 20 条，得出 active=6——那是第一页的数，不是全量。
- status 取值（文档枚举）：trialing active past_due completed canceled expired unresolved drafted canceling。
  一次性课程买断后是 completed；订阅「到期不续」仍是 active + cancel_at_period_end=true。
- 默认不按产品过滤；实际返回是扁平的 product_id / plan_id / user_id（与文档的嵌套写法不同）。

⚠️ `whop_members` 列的 README 口径是「身份合并后的真实人头」（含 PayPal/支付宝渠道），API 只看得到
Whop 渠道，不能直接替代。所以本脚本**只写 notes，不填 whop_members**，直到 Andy 定口径
（候选见 notes）。定了之后把 COLUMN_CANDIDATE 设成对应键即可。

key 只从钥匙串读进内存：不打印、不落盘；所有异常信息先打码。仓库公开：只输出计数，不输出姓名/邮箱/id。
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API = "https://api.whop.com/api/v1"
PAGE_SIZE = 50
MAX_PAGES = 200
KEY_UNAVAILABLE = "Whop key 不可用，本周空"

# 订阅类产品（出处：data/growth/weekly/2026-08-25-paypal-reconcile.md 与 09-12 metrics 行）
SUBSCRIPTION_PRODUCTS = {
    "prod_JP6vlypnDQTNk",  # Premium Membership
    "prod_lqtg4j5LTtBVh",  # Premium++ Members Access（新档）
    "prod_0WddY2iwoTitp",  # Premium++ Members Access（旧档，已归档）
}
MASTERCLASS_PRODUCT = "prod_dTRZGYQvAc0pe"  # Swing Trade Masterclass（一次性）
PAID_STATUSES = {"active", "past_due"}

# Andy 未定口径前为 None → whop_members 列留空
COLUMN_CANDIDATE: str | None = None

REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "data" / "growth" / "metrics.csv"


class WhopError(RuntimeError):
    pass


def mask(text: object, key: str | None) -> str:
    s = str(text)
    if key:
        s = s.replace(key, "***")
    return s


def get_api_key(runner=subprocess.run) -> str | None:
    """钥匙串取 key；取不到返回 None（不抛含 key 的异常）。"""
    try:
        r = runner(
            ["security", "find-generic-password", "-a", "fluxus", "-s", "whop-readonly-key", "-w"],
            capture_output=True, text=True, check=False,
        )
    except Exception:
        return None
    key = (r.stdout or "").strip()
    return key if r.returncode == 0 and key else None


def fetch_all(session, path: str, key: str, page_size: int = PAGE_SIZE) -> tuple[list[dict], int]:
    """按游标读完所有页。返回 (rows, pages)。"""
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    rows: list[dict] = []
    after = None
    for pages in range(1, MAX_PAGES + 1):
        params = {"first": page_size}
        if after:
            params["after"] = after
        try:
            resp = session.get(f"{API}/{path}", headers=headers, params=params, timeout=30)
        except Exception as e:  # 网络错误信息也打码
            raise WhopError(mask(f"{path} 请求失败: {type(e).__name__}: {e}", key)) from None
        if resp.status_code != 200:
            raise WhopError(mask(f"{path} HTTP {resp.status_code}", key))
        body = resp.json()
        rows.extend(body.get("data") or [])
        info = body.get("page_info") or {}
        if not info.get("has_next_page"):
            return rows, pages
        after = info.get("end_cursor")
        if not after:
            raise WhopError(f"{path} has_next_page=true 但无 end_cursor（第 {pages} 页）")
    raise WhopError(f"{path} 超过 {MAX_PAGES} 页仍未读完")


def _users(rows, pred) -> int:
    return len({m.get("user_id") for m in rows if pred(m) and m.get("user_id")})


def summarize(memberships: list[dict], members: list[dict] | None = None) -> dict:
    status = Counter(m.get("status") for m in memberships)
    by_product: dict[str, Counter] = {}
    for m in memberships:
        by_product.setdefault(m.get("product_id") or "?", Counter())[m.get("status")] += 1
    paid_sub = lambda m: m.get("status") in PAID_STATUSES and m.get("product_id") in SUBSCRIPTION_PRODUCTS
    out = {
        "rows": len(memberships),
        "status": dict(status),
        "by_product": {p: dict(c) for p, c in by_product.items()},
        "users_all": _users(memberships, lambda m: True),
        # 候选 A：订阅在档付费人（按 user 去重）
        "cand_A_paid_sub_users": _users(memberships, paid_sub),
        "cand_A_of_which_cancel_at_period_end": _users(
            memberships, lambda m: paid_sub(m) and m.get("cancel_at_period_end")),
        "trialing_users": _users(memberships, lambda m: m.get("status") == "trialing"),
        "masterclass_completed_users": _users(
            memberships, lambda m: m.get("product_id") == MASTERCLASS_PRODUCT and m.get("status") == "completed"),
        "rows_missing_user_id": sum(1 for m in memberships if not m.get("user_id")),
    }
    if members is not None:
        # 候选 B：members 接口里有访问权的客户（customer 且 joined）
        out["members_rows"] = len(members)
        out["cand_B_customer_joined"] = sum(
            1 for m in members if m.get("access_level") == "customer" and m.get("status") == "joined")
    return out


def format_note(s: dict, fetched: str, pages: int) -> str:
    """notes 列：禁半角逗号（README 规则）。"""
    st = " ".join(f"{k}={v}" for k, v in sorted(s["status"].items(), key=lambda kv: str(kv[0])))
    parts = [
        f"Whop API /v1/memberships 游标分页{pages}页共{s['rows']}条(按user去重{s['users_all']}人)",
        f"取数 {fetched}",
        f"status: {st}",
        f"候选A 订阅在档付费人(status∈active|past_due·Premium与Premium++新旧三产品·按user去重)={s['cand_A_paid_sub_users']}"
        f"(其中到期不续{s['cand_A_of_which_cancel_at_period_end']})",
        f"试用trialing={s['trialing_users']}人(单列不计付费)",
        f"一次性课程completed={s['masterclass_completed_users']}人",
    ]
    if "cand_B_customer_joined" in s:
        parts.append(f"候选B /v1/members customer且joined={s['cand_B_customer_joined']}")
    parts.append("whop_members列留空:README列口径=身份合并真实人头(含PayPal/支付宝)·API只见Whop渠道·口径待Andy定")
    note = "；".join(parts)
    return note.replace(",", "，")


def update_row(csv_path: Path, date: str, note: str, value: str = "") -> None:
    """同日行存在则只改该行的 whop_members 与 notes；否则追加新行。其余行逐字节不动。"""
    import io
    lines = csv_path.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next(csv.reader([lines[0]]))
    i_w, i_n = header.index("whop_members"), header.index("notes")

    def dump(row):
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerow(row)
        return buf.getvalue()

    for i, line in enumerate(lines[1:], start=1):
        if line.startswith(date + ","):
            row = next(csv.reader([line]))
            row += [""] * (len(header) - len(row))
            row[i_w], row[i_n] = value, note
            lines[i] = dump(row)
            break
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        new = [""] * len(header)
        new[0], new[i_w], new[i_n] = date, value, note
        lines.append(dump(new))
    csv_path.write_text("".join(lines), encoding="utf-8")


def market_date() -> str:
    sys.path.insert(0, str(REPO))
    from pipeline.marketcal import market_today  # noqa: E402
    return market_today().isoformat()


def main(argv=None, session=None, key_getter=get_api_key) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="写进 metrics.csv（默认只打印聚合数）")
    ap.add_argument("--date", help="metrics.csv 行日期（默认 marketcal 今天）")
    ap.add_argument("--csv", type=Path, default=CSV_PATH)
    a = ap.parse_args(argv)

    key = key_getter()
    if not key:
        print(KEY_UNAVAILABLE)
        return 0
    if session is None:
        import requests
        session = requests.Session()
    try:
        ms, pages = fetch_all(session, "memberships", key)
        try:
            mem, _ = fetch_all(session, "members", key)
        except WhopError as e:
            print(f"members 接口不可用（候选B 跳过）: {e}", file=sys.stderr)
            mem = None
    except WhopError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        key = None  # noqa: F841

    s = summarize(ms, mem)
    fetched = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%dT%H:%M%z")
    note = format_note(s, fetched, pages)
    for k, v in s.items():
        print(f"{k}: {v}")
    if a.write:
        value = str(s[COLUMN_CANDIDATE]) if COLUMN_CANDIDATE else ""
        date = a.date or market_date()
        update_row(a.csv, date, note, value)
        print(f"已写 {a.csv.name} {date} 行（whop_members={value or '留空'}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
