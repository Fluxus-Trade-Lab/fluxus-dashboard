#!/usr/bin/env python3
"""X 日调研 · 抓取器(twitterapi.io)

只做机械活：拉帖、落盘、算提及。**不做判断** —— 立场标注和日报由 Claude 读 jsonl 后写。

用法:
    export TWITTERAPI_KEY=...          # 或写进仓库根的 .env(已被 gitignore)
    python3 fetch.py --probe           # 冒烟测试：只拉 1 页，验字段与花费
    python3 fetch.py --days 2          # 抓最近 2 天(默认 1)
    python3 fetch.py --since 2026-09-04 --until 2026-09-06

产出:
    data/content/x_watch/posts/YYYY-MM-DD.jsonl
    data/content/x_watch/members.json
    data/content/x_watch/mentions.csv        (累加)
    data/content/x_watch/runlog.csv          (累加)
"""
from __future__ import annotations
import argparse, csv, json, os, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API = "https://api.twitterapi.io"
QPS_SLEEP = 5.2          # 免费档硬限：每 5 秒 1 个请求（实测 429 原文如此）
_last = [0.0]
LIST_ID = "2083551367399182754"          # Copybook（Andy 09-06 指定）
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "content" / "x_watch"
ET = timezone(timedelta(hours=-4))       # 美东夏令时；口径见 pipeline.marketcal

# 不带 $ 的裸代码若命中这些词一律不算 ticker
STOPWORDS = {
    "A","I","AI","ALL","AM","PM","AN","AND","ANY","ARE","AS","AT","BE","BUT","BY","CEO","CFO",
    "CPI","DD","DO","EOD","EPS","ER","ETF","FED","FOR","FOMC","GDP","GO","HAS","HE","IF","IN",
    "IPO","IS","IT","ITM","IV","LOL","ME","MY","NO","NOT","OF","OK","ON","OR","OTM","PT","QQQ",
    "RE","RSI","SO","TA","THE","TO","TP","UP","US","USA","VS","WE","WTF","YOY","YTD",
}


def key() -> str:
    k = os.environ.get("TWITTERAPI_KEY")
    if not k:
        env = ROOT / ".env"
        if env.exists():
            m = re.search(r"TWITTERAPI_KEY=(\S+)", env.read_text())
            if m:
                k = m.group(1).strip().strip('"\'')
    if not k:
        sys.exit("缺 TWITTERAPI_KEY。去 https://twitterapi.io/dashboard 取 key，"
                 "写进仓库根 .env：export TWITTERAPI_KEY=xxx")
    return k


def get(path: str, params: dict, k: str, tries: int = 3) -> dict:
    url = f"{API}{path}?{urlencode(params)}"
    for i in range(tries):
        wait = QPS_SLEEP - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            with urlopen(Request(url, headers={"X-API-Key": k}), timeout=45) as r:
                return json.loads(r.read())
        except HTTPError as e:
            body = e.read()[:300].decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503) and i < tries - 1:
                time.sleep(QPS_SLEEP * (i + 2)); continue
            sys.exit(f"HTTP {e.code} on {path}: {body}")
        except Exception as e:
            if i < tries - 1:
                time.sleep(3); continue
            sys.exit(f"{type(e).__name__} on {path}: {e}")
    return {}


def paged(path: str, params: dict, k: str, cap: int, item_key: str):
    """按 cursor 翻页，最多 cap 页。返回 (items, pages_used)。"""
    items, cursor, pages = [], None, 0
    while pages < cap:
        p = dict(params)
        if cursor:
            p["cursor"] = cursor
        d = get(path, p, k)
        batch = d.get(item_key) or d.get("data") or []
        if isinstance(batch, dict):
            batch = batch.get(item_key, [])
        items += batch
        pages += 1
        if not d.get("has_next_page") or not d.get("next_cursor"):
            break
        cursor = d["next_cursor"]
    return items, pages


def tickers(text: str) -> set[str]:
    out = {m.upper() for m in re.findall(r"\$([A-Za-z]{1,5})\b", text)}
    for m in re.findall(r"\b([A-Z]{2,5})\b", text):
        if m not in STOPWORDS:
            out.add(m)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--since"); ap.add_argument("--until")
    ap.add_argument("--list-id", default=LIST_ID)
    ap.add_argument("--probe", action="store_true", help="只拉 1 页，打印字段与花费，不落盘")
    ap.add_argument("--max-pages", type=int, default=40)
    a = ap.parse_args()
    k = key()
    started = datetime.now(timezone.utc)

    if a.probe:
        d = get("/twitter/list/tweets", {"listId": a.list_id}, k)
        tw = (d.get("tweets") or d.get("data") or [])
        print("=== 顶层字段 ===", list(d.keys()))
        print("=== 本页帖数 ===", len(tw))
        if tw:
            t = tw[0]
            print("=== 一条帖的字段 ===", sorted(t.keys()))
            for f in ("viewCount", "bookmarkCount", "likeCount", "replyCount",
                      "retweetCount", "createdAt", "isReply"):
                print(f"  {f:14} = {t.get(f, '❌ 缺')}")
            au = t.get("author") or {}
            print(f"  author.userName = {au.get('userName')}")
        m = get("/twitter/list/members", {"listId": a.list_id}, k)
        mem = m.get("members") or m.get("data") or []
        print("=== 成员本页 ===", len(mem),
              "· has_next:", m.get("has_next_page"))
        if mem:
            print("  样本:", [x.get("userName") for x in mem[:5]])
        return

    until = datetime.strptime(a.until, "%Y-%m-%d").replace(tzinfo=ET) if a.until \
        else datetime.now(ET)
    since = datetime.strptime(a.since, "%Y-%m-%d").replace(tzinfo=ET) if a.since \
        else until - timedelta(days=a.days)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "posts").mkdir(exist_ok=True)

    # 私密 List 的成员读不到（09-06 起 HTTP 400 list_id is required；此前是 200 + 空数组）。
    # 两种失败都不该让整轮抓取死掉，更不该把 members.json 覆盖成 []：
    # 名册是 Andy 手写的，空结果是 API 的性质，不是花名册的事实。
    try:
        mem, _ = paged("/twitter/list/members", {"listId": a.list_id}, k, 10, "members")
    except SystemExit as e:
        print(f"members 读不到（{e}），跳过；members.json 保持原样", file=sys.stderr)
        mem = []
    if mem:
        (OUT / "members.json").write_text(json.dumps(
            [{"h": x.get("userName"), "name": x.get("name"),
              "followers": x.get("followers"), "bio": (x.get("description") or "")[:200]}
             for x in mem], ensure_ascii=False, indent=1))

    raw, pages = paged("/twitter/list/tweets", {"listId": a.list_id}, k,
                       a.max_pages, "tweets")

    rows, oldest = [], None
    for t in raw:
        ca = t.get("createdAt") or ""
        try:
            dt = datetime.strptime(ca, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            try:
                dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
            except ValueError:
                continue
        oldest = dt if oldest is None or dt < oldest else oldest
        if not (since <= dt.astimezone(ET) <= until):
            continue
        au = t.get("author") or {}
        txt = t.get("text") or ""
        rows.append({
            "id": t.get("id"), "h": au.get("userName"),
            "dt": dt.astimezone(timezone.utc).isoformat(),
            "et_date": dt.astimezone(ET).strftime("%Y-%m-%d"),
            "text": txt,
            "views": t.get("viewCount"), "likes": t.get("likeCount"),
            "bookmarks": t.get("bookmarkCount"), "replies": t.get("replyCount"),
            "reposts": t.get("retweetCount"),
            "is_reply": t.get("isReply"), "url": t.get("url"),
            "tickers": sorted(tickers(txt)),
        })

    by_day: dict[str, list] = {}
    for r in rows:
        by_day.setdefault(r["et_date"], []).append(r)
    for d, rs in by_day.items():
        with (OUT / "posts" / f"{d}.jsonl").open("w", encoding="utf-8") as f:
            for r in sorted(rs, key=lambda x: x["dt"]):
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # mentions.csv 是 upsert，不是 append —— 同一个 ET 日期会被抓两次（两班制：
    # 02:00 JST 的睡前速报抓前半天，13:30 JST 的主班重抓全天），append 会把同一批
    # post_id 追加两遍。key = (date, ticker, handle, post_id)。
    # ⚠️ 已存在的行**整行保留** —— stance 列是人工回填的，重抓不许把它抹掉。
    HDR = ["date", "ticker", "handle", "post_id", "views", "bookmarks", "stance"]
    mp = OUT / "mentions.csv"
    existing, seen = [], set()
    if mp.exists():
        with mp.open(newline="", encoding="utf-8") as f:
            for x in csv.DictReader(f):
                existing.append([x.get(c, "") for c in HDR])
                seen.add((x.get("date"), x.get("ticker"), x.get("handle"), x.get("post_id")))
    added = 0
    for r in rows:
        for tk in r["tickers"]:
            k = (r["et_date"], tk, r["h"], str(r["id"]))
            if k in seen:
                continue
            seen.add(k)
            existing.append([r["et_date"], tk, r["h"], r["id"], r["views"], r["bookmarks"], ""])
            added += 1
    with mp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HDR)
        w.writerows(existing)

    mins = (datetime.now(timezone.utc) - started).total_seconds() / 60
    lp = OUT / "runlog.csv"
    new = not lp.exists()
    with lp.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["run_utc", "minutes", "pages", "posts_raw", "posts_kept",
                        "authors", "members", "oldest_raw_utc", "since_et", "until_et"])
        w.writerow([started.isoformat(timespec="seconds"), f"{mins:.1f}", pages,
                    len(raw), len(rows), len({r['h'] for r in rows}), len(mem),
                    oldest.astimezone(timezone.utc).isoformat() if oldest else "",
                    since.date(), until.date()])

    print(f"成员 {len(mem)} · 拉到 {len(raw)} 条({pages} 页)· 窗口内 {len(rows)} 条 / "
          f"{len({r['h'] for r in rows})} 人 · mentions 新增 {added} 行 · {mins:.1f} 分")
    if raw and len(rows) < len(raw) * 0.1:
        print("⚠️ 窗口内留下的不到一成 —— 检查 --since/--until 是不是设窄了")
    if oldest and oldest.astimezone(ET) > since:
        print(f"⚠️ 最旧一条 {oldest.astimezone(ET):%Y-%m-%d %H:%M} ET 仍晚于 since "
              f"—— 没翻到底，加 --max-pages")


if __name__ == "__main__":
    main()
