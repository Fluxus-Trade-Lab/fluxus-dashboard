#!/usr/bin/env python3
"""X 日调研 · 抓取器(twitterapi.io)

只做机械活：拉帖、落盘、算提及。**不做判断** —— 立场标注和日报由 Claude 读 jsonl 后写。

用法:
    export TWITTERAPI_KEY=...          # 或写进仓库根的 .env(已被 gitignore)
    python3 fetch.py --probe           # 冒烟测试：只拉 1 页，验字段与花费
    python3 fetch.py --days 2          # 抓最近 2 天(默认 1)
    python3 fetch.py --since 2026-09-04 --until 2026-09-06

产出:
    data/content/x_watch/posts/YYYY-MM-DD.jsonl  (按 id 并集，不覆盖)
    data/content/x_watch/members.json
    data/content/x_watch/own_account.csv     (@Fluxus_Z 自己的读数,按 date_et upsert)
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
    # 大写强调词，非整行喊话（shouting() 抓不到——行里混着小写词，不满足
    # 「整行无小写」）：09-23 RealJGBanks「SPY broke the DAILY LOW.」「$SPY 230%
    # PUT TRADE」「BANKS Break. Retest. Enter」三行都把强调词当成了裸代码。
    # 这不是 shouting() 的行长阈值问题——这些行本身就不是全大写行，调阈值挡不住。
    # 取件账 09-24（T-0924-104）。LOW 虽是 Lowe's 真代码，但归在 INDICATOR_BARE
    # 更符合本文件自己立的分类口径（真代码同名缩写才进那边），见下方。
    "DAILY","PUT","TRADE","BANKS","MTF",
}

# 指标名 / 经济数据名 / 真代码同名缩写：只在「裸大写词」分支拦，带 $ 的照认。
# RS（Reliance Steel）、SMA（Summit Materials）、MA（Mastercard）是真代码，所以不能进
# STOPWORDS。09-11 主班实测：人数榜上 $RS 4 人、$SMA 3 人，全部来自「50 SMA」
# 「RS line」这类正文，没有一条带 $。DT（Dynatrace）、LOW（Lowe's）09-24 加入
# 同理——库里现存的 $DT 全部带 $（PrimeTrading_/cfromhertz 的清单帖），但「DT」
# 「LOW」也是常见大写强调词（如「DT Break」「DAILY LOW」句式），裸词先拦，
# 真要认某票就带 $（T-0924-104）。两个集合在 tickers() 里判法完全等价，放哪边
# 不影响结果，只影响这份注释自证的分类是否一致。
INDICATOR_BARE = {"SMA","EMA","RS","PPI","MA","VWAP","ATR","MACD","PCE","DT","LOW"}


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


def shouting(line: str) -> bool:
    """整行全大写（>25 字且一个小写都没有）＝喊话或板块小标题，不是代码清单。

    09-19 主班：RealJGBanks 一条全大写周末帖，光板块小标题就贡献了
    EXACT / TECH / POWER / NEXT / REAL / RISK 六个假代码，把「这条挂了几个代码」
    从 31 算成 37。取件账 09-06·3 第 3 次，三次律升机制。
    """
    return len(line) > 25 and not any(c.islower() for c in line)


def tickers(text: str) -> set[str]:
    # 带 $ 的这一遍扫全文：喊话行里真出现 $NVDA 也照认，拦的只是裸大写词。
    out = {m.upper() for m in re.findall(r"\$([A-Za-z]{1,5})\b", text)}
    for line in text.splitlines():
        if shouting(line):
            continue
        for m in re.findall(r"\b([A-Z]{2,5})\b", line):
            if m not in STOPWORDS and m not in INDICATOR_BARE:
                out.add(m)
    return out


def _post_key(r: dict) -> str:
    return str(r["id"]) if r.get("id") is not None else f'{r.get("h")}|{r.get("dt")}'


OWN_COLS = ["date_et", "followers", "following", "tweets", "fetched_utc", "source"]
OWN_SRC = "twitterapi.io /twitter/user/info"


def own_account_row(resp: dict, date_et: str, fetched_utc: str) -> dict:
    """@Fluxus_Z 自己的账号读数。取不到就写空、source 写原因,**不估**。

    Growth Gary 09-13 挂单(Andy 原话「X增长让Steve 日常顺手带上,然后都可以被阅读到」):
    metrics.csv 的 x_followers 自建表以来全空,因为 WebFetch x.com 回 402。
    """
    u = resp.get("data") if isinstance(resp, dict) else None
    row = {"date_et": date_et, "fetched_utc": fetched_utc,
           "followers": "", "following": "", "tweets": ""}
    if not isinstance(u, dict) or u.get("followers") is None:
        why = (resp.get("msg") if isinstance(resp, dict) else None) or "空响应"
        row["source"] = f"取不到: {why}"
        return row
    row.update(followers=u.get("followers"), following=u.get("following", ""),
               tweets=u.get("statusesCount", ""), source=OWN_SRC)
    return row


def upsert_own_account(path: Path, row: dict) -> None:
    """按 date_et upsert:同一个 ET 日两班都抓,后抓的那行留下;按日期排序,末行 = 最新。"""
    rows = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["date_et"]] = r
    rows[row["date_et"]] = row
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OWN_COLS)
        w.writeheader()
        for d in sorted(rows):
            w.writerow({c: rows[d].get(c, "") for c in OWN_COLS})


def merge_day_posts(existing: list[dict], fresh: list[dict]) -> list[dict]:
    """同一个 ET 日的并集。键 = id；本轮抓到的那条整行覆盖旧的（曝光/收藏只会涨）。

    09-10 事故：API 翻 7 页就报 has_next_page=false，旧写法用 "w" 把当日写成
    116 条残片，盖掉了睡前速报那份 205 条 —— 「没翻到底」的警告在写盘之后才打印。
    09-06 另有一例：thesetupfactory 06:48 ET 那条，第二轮 API 不再返回，照写就从
    归档里消失，而它在 mentions.csv 里的行还在。
    并集之后，一轮短抓只能往文件里加东西，不能再让它变短。
    """
    merged = {_post_key(r): r for r in existing}
    for r in fresh:
        merged[_post_key(r)] = r
    return sorted(merged.values(), key=lambda x: x.get("dt") or "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--since"); ap.add_argument("--until")
    ap.add_argument("--list-id", default=LIST_ID)
    ap.add_argument("--probe", action="store_true", help="只拉 1 页，打印字段与花费，不落盘")
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--own-handle", default="Fluxus_Z")
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
        m = get("/twitter/list/members", {"list_id": a.list_id}, k)
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

    # 私密 List 的成员读不到。09-06 起报 HTTP 400 `list_id is required` —— 09-10 探针定案：
    # 这个端点收 snake 的 list_id，帖子端点收 camel 的 listId，我们两处都发了 listId。
    # 改对之后回 200 但成员数仍是 0（私密 List 的天花板），所以下面的兜底照旧要留。
    # 两种失败都不该让整轮抓取死掉，更不该把 members.json 覆盖成 []：
    # 名册是 Andy 手写的，空结果是 API 的性质，不是花名册的事实。
    try:
        mem, _ = paged("/twitter/list/members", {"list_id": a.list_id}, k, 10, "members")
    except SystemExit as e:
        print(f"members 读不到（{e}），跳过；members.json 保持原样", file=sys.stderr)
        mem = []
    if mem:
        (OUT / "members.json").write_text(json.dumps(
            [{"h": x.get("userName"), "name": x.get("name"),
              "followers": x.get("followers"), "bio": (x.get("description") or "")[:200]}
             for x in mem], ensure_ascii=False, indent=1))

    # 自己的账号读数:一次请求,失败不致命(get 出错走 sys.exit,这里接住)
    try:
        own_resp = get("/twitter/user/info", {"userName": a.own_handle}, k)
    except SystemExit as e:
        own_resp = {"msg": str(e)}
    own = own_account_row(own_resp, datetime.now(ET).strftime("%Y-%m-%d"),
                          datetime.now(timezone.utc).isoformat(timespec="seconds"))
    upsert_own_account(OUT / "own_account.csv", own)
    print(f"own_account.csv ← @{a.own_handle} {own['date_et']} 粉丝 {own['followers'] or '空'} · {own['source']}")

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
        fp = OUT / "posts" / f"{d}.jsonl"
        old = []
        if fp.exists():
            with fp.open(encoding="utf-8") as f:
                old = [json.loads(l) for l in f if l.strip()]
        merged = merge_day_posts(old, rs)
        with fp.open("w", encoding="utf-8") as f:
            for r in merged:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        if old:
            fresh_keys = {_post_key(r) for r in rs}
            kept = sum(1 for r in merged if _post_key(r) not in fresh_keys)
            print(f"posts/{d}.jsonl: 旧 {len(old)} · 本轮 {len(fresh_keys)} → 并集 {len(merged)}"
                  + (f"（本轮没返回、从旧文件保留 {kept} 条）" if kept else ""))

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
