#!/usr/bin/env python3
"""X 名单 ticker 台账 —— 把 posts/*.jsonl + mentions.csv + subs/ 编成一页可检索的看板。

只读,不改任何源文件。产出:
  data/content/x_watch/board.html        给 Andy 看的页(自带数据,可直接双击打开)
  data/content/x_watch/board_data.json   页里嵌的那份数据,单独留一份便于别的工具读
  data/content/x_watch/ticker_daily.csv  宽表:ticker × 日期 = 当日提及人数(Excel 直接开)

⚠️ 裸代码 vs cashtag:fetch.py 把 `$AAPL` 和不带 $ 的裸代码合并进同一个 tickers 字段,
   噪声几乎全在裸代码那半边(RS/EMA/SMA/WHAT/ENJOY…)。这里按帖子原文重新判一次
   `'$'+SYM in text`,给每条提及打 cash 标记,页面默认只显示 cashtag,裸代码要手动打开。
   **不删任何数据,只是默认不显示。**
"""
from __future__ import annotations
import bisect, csv, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "data/content/x_watch"
TPL = Path(__file__).with_name("board_template.html")

# 行情：本地已有的两份，不新抓（memory feedback_reuse_local_ohlc）。
#   tickers/<SYM>.json  → ohlc_2y[{date,open,high,low,close,volume}]  个股
#   baskets/<SYM>.json  → bars[{date,close}]                          宽基/ETF，SPY 在这里
TICKERS_DIR = ROOT / "data/output/tickers"
BASKETS_DIR = ROOT / "data/output/baskets"
BENCH = "SPY"          # 基准单独取、单独验，缺了抛错（method_denominator_is_not_optional）
HORIZONS = (1, 5)      # T+k，交易日

# 结构三列（T-0923-88）：**全部读 data/output 现成字段，一个都不新算**。
#   universe.json rows[]  → rs_rating（IBD 式 1–99 相对强弱评级）· sma50_dist（距 50 日线，小数）
#   asset_signals.json rows[] → sma50_dist（指数/宽基 ETF 那 26 行，universe 里没有它们）
#   groups.json themes[]  → method=="etf" 的篮子，group 是篮子名、tickers 是成分
# 取不到就是「无」，不猜不补不折算。
UNIVERSE_PATH = ROOT / "data/output/universe.json"
SIGNALS_PATH = ROOT / "data/output/asset_signals.json"
GROUPS_PATH = ROOT / "data/output/groups.json"

# X 热度（给 dashboard 的数据文件，前端归 UI Claire）
X_HEAT_PATH = ROOT / "data/output/x_heat.json"
HEAT_WINDOW = 7        # 近 N 个有数据的 ET 日

STANCES = ["long", "watching", "short", "exited", "recap", "mention"]

# 指数与宽基 ETF：它们属于日报第 3 节「走势」，不是第 1 节的候选票。
# 分开标，不从表里删。
INDEX = {"SPY", "QQQ", "VIX", "SPX", "NDX", "IWM", "DIA", "SMH", "IWF", "IWD",
         "QQQE", "RSP", "TLT", "GLD", "SLV", "USO", "XLK", "XLF", "XLE", "XLV",
         "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "ETH", "BTC"}


def load_posts() -> list[dict]:
    rows = []
    for f in sorted((BASE / "posts").glob("*.jsonl")):
        for line in f.open():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_stance() -> dict[tuple[str, str], str]:
    """(post_id, ticker) -> stance。mentions.csv 是 CRLF,用 newline='' 交给 csv 处理。"""
    out = {}
    p = BASE / "mentions.csv"
    if not p.exists():
        return out
    with p.open(newline="") as fh:
        for r in csv.DictReader(fh):
            s = (r.get("stance") or "").strip()
            if s:
                out[(r["post_id"], r["ticker"])] = s
    return out


def load_wall() -> list[dict]:
    out = []
    for f in sorted((BASE / "subs/jfsrev").glob("*.jsonl")):
        for line in f.open():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            et = (d.get("et") or "")[:10]
            out.append({
                "id": d.get("id"), "d": et, "kind": d.get("kind") or "",
                "tickers": d.get("tickers") or [], "proxy": d.get("proxy"),
                "text": d.get("text") or "", "url": d.get("url"),
                "views": (d.get("stats") or {}).get("views"),
            })
    # 同一条帖同时躺在跨日基线文件和单日文件里。⚠️ 按 url/正文去重会漏 ——
    # 两份文件的正文换行不同(`\n$AMC\n` vs `$AMC`),必须按 post id 去重。
    seen, uniq = set(), []
    for r in out:
        k = r["id"] or (r["d"], r["kind"], tuple(r["tickers"]))
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return sorted(uniq, key=lambda r: (r["d"], r["kind"]))


# ─────────────────────────────────────────────────────────────────────────────
# 提及峰值日之后的相对 SPY 表现（事件研究 · market-adjusted model）
#
# 口径登记在 data/reference/METRIC_SOURCES.md「x_watch 提及后 T+k 相对 SPY」那行。
# 照抄的部分：abnormal return 的 market-adjusted model —— AR_it = R_it − R_mt，
#   即 β=1 / α=0、不估计参数、直接减基准（EventStudyTools, Expected Return Models）。
#   事件日落在非交易日/盘后时，以「下一个能交易的 session」为反应起点，是事件研究
#   的通行处理（announcement after close → day 0 是次日）。
# 自造并写明的部分：
#   ① 锚点 A = 峰值日当天或之前最后一个 **已收盘** 交易日的收盘价。提及帖散落在
#      ET 日历日的各个时刻，我们没有逐帖时间戳对齐盘中，取当日收盘 = 把整个提及日
#      当信息日，避免把提及之前就已经走完的当日行情算进「提及之后」。周末提及
#      因此锚在上周五收盘，T+1 是下周一。
#   ② 用持有期差（BHAR 形状：R_i − R_m 各自按 A→A+k 的简单收益）而不是逐日 AR
#      累加（CAR）。k=1/5 这两个窗口本身也不是标准，是这条台账要回答的问题决定的。
#   ③ 不做显著性检验、不设估计窗 —— 样本量和用途都不支持，读数只当描述统计。
# ─────────────────────────────────────────────────────────────────────────────

def load_closes(sym: str, tickers_dir: Path = None, baskets_dir: Path = None
                ) -> dict[str, float] | None:
    """本地收盘价序列 {ET日期: close}。两个目录都没有这只票就返回 None（＝无价格）。"""
    tickers_dir = TICKERS_DIR if tickers_dir is None else tickers_dir
    baskets_dir = BASKETS_DIR if baskets_dir is None else baskets_dir
    for d, key in ((tickers_dir, "ohlc_2y"), (baskets_dir, "bars")):
        f = d / f"{sym}.json"
        if not f.exists():
            continue
        bars = json.loads(f.read_text()).get(key) or []
        out = {b["date"][:10]: float(b["close"]) for b in bars
               if b.get("date") and b.get("close") is not None}
        if out:
            return out
    return None


def peak_day(days: dict[str, dict]) -> str | None:
    """提及人数最高的 ET 日；**并列取最早**（窗口左端优先，不许随字典序漂）。"""
    best, best_n = None, 0
    for d in sorted(days):
        n = len(days[d].get("p") or [])
        if n > best_n:                       # 严格大于 → 并列时保留先到的那天
            best, best_n = d, n
    return best


def rel_vs_bench(closes: dict[str, float], bench: dict[str, float],
                 cal: list[str], peak: str, k: int) -> tuple[float | None, str]:
    """峰值日后 T+k 的相对 SPY 表现。返回 (值, 原因码)；值为 None 时原因码说明为什么。

    cal 是基准的交易日历（SPY 有 bar 的日子），T+k 数的是交易日不是日历日。
    """
    i = bisect.bisect_right(cal, peak) - 1
    if i < 0:
        return None, "无基准日"
    j = i + k
    if j >= len(cal):
        return None, "未到期"
    a, b = cal[i], cal[j]
    if a not in closes or b not in closes:
        return None, "缺K线"
    r = closes[b] / closes[a] - 1.0
    m = bench[b] / bench[a] - 1.0
    return (r - m) * 100.0, "ok"


def price_cell(v: float | None, why: str) -> str:
    return f"{v:+.2f}%" if v is not None else why


def attach_prices(tickers: list[dict], tickers_dir: Path = None,
                  baskets_dir: Path = None) -> None:
    """就地给每只票挂 peak / relk。**基准缺失直接抛错，绝不静默当 0。**"""
    bench = load_closes(BENCH, tickers_dir, baskets_dir)
    if not bench:
        raise RuntimeError(
            f"基准 {BENCH} 的本地行情取不到（找过 {tickers_dir or TICKERS_DIR} 与 "
            f"{baskets_dir or BASKETS_DIR}）。相对表现没有分母就不是相对表现——"
            "宁可不出这两列，也不拿 0 顶替。")
    cal = sorted(bench)
    for t in tickers:
        t["peak"] = peak_day(t.get("days") or {})
        closes = load_closes(t["sym"], tickers_dir, baskets_dir)
        t["rel"] = {}
        for k in HORIZONS:
            if t["peak"] is None:
                t["rel"][k] = (None, "无提及日")
            elif closes is None:
                t["rel"][k] = (None, "无价格")
            else:
                t["rel"][k] = rel_vs_bench(closes, bench, cal, t["peak"], k)


# ─────────────────────────────────────────────────────────────────────────────
# 结构三列：RS 评级 · 距 50 日线% · 所属 ETF 篮子（T-0923-88）
#
# 三列全部是 **dashboard 管线已经算好、落在 data/output 里的字段**，这里只做一次
# join 和一次反向索引，**不新算任何指标**：
#   RS 评级      = universe.json rows[].rs_rating   （缺 → 无）
#   距 50 日线%  = universe.json rows[].sma50_dist  （小数，×100 才是 %；缺 → 无）
#                  指数/宽基 ETF 不在 universe 里，回落到 asset_signals.json 同名字段
#   所属 ETF 篮子 = groups.json themes[] 里 method=="etf" 那批的 tickers 反查
#
# ⚠️ 一只票可以同时属于多个篮子（09-23 实测最多 4 个：$TSLA —— method=="etf" 口径下的实测上限，
#    全 data/output 与本台账内都是 4。把 industry / rule 那两类组也算进来时 $BAND 有 8 个，
#    但那些不是 ETF 篮子，不进这一列）。**全留，不取第一个** ——
#    「它在几个篮子里」本身就是读数；取第一个会让同一只票在不同跑次里换篮子。
# ⚠️ 取不到一律写「无」，不写 0、不写空字符串：0 分的 RS 和「没查到这只票」是两件事。
# ─────────────────────────────────────────────────────────────────────────────

def _json_rows(path: Path, key: str = "rows") -> list[dict]:
    """读 data/output 的某个 JSON 的行数组。文件不在/坏了就当没有，不让看板挂掉。"""
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if isinstance(d, dict):
        rows = d.get(key)
        return rows if isinstance(rows, list) else []
    return d if isinstance(d, list) else []


def load_structure(universe_path: Path = None, signals_path: Path = None,
                   groups_path: Path = None) -> dict[str, dict]:
    """{SYM: {"rs": int|None, "d50": float|None, "bask": [篮子名…]}}。"""
    universe_path = UNIVERSE_PATH if universe_path is None else universe_path
    signals_path = SIGNALS_PATH if signals_path is None else signals_path
    groups_path = GROUPS_PATH if groups_path is None else groups_path

    out: dict[str, dict] = {}

    def slot(sym: str) -> dict:
        return out.setdefault(sym, {"rs": None, "d50": None, "bask": []})

    for r in _json_rows(universe_path):
        sym = (r.get("ticker") or "").upper()
        if not sym:
            continue
        s = slot(sym)
        s["rs"] = r.get("rs_rating")
        s["d50"] = r.get("sma50_dist")

    # 指数/宽基 ETF 走这份；只回填 universe 里没给到的格，不覆盖个股读数
    for r in _json_rows(signals_path):
        sym = (r.get("ticker") or "").upper()
        if not sym:
            continue
        s = slot(sym)
        if s["d50"] is None:
            s["d50"] = r.get("sma50_dist")
        if s["rs"] is None:
            s["rs"] = r.get("rs_rating")          # 这份目前没有这个字段 → 仍是 None＝无

    for th in _json_rows(groups_path, "themes"):
        if th.get("method") != "etf":
            continue
        name = th.get("group")
        if not name:
            continue
        for sym in th.get("tickers") or []:
            b = slot(str(sym).upper())["bask"]
            if name not in b:
                b.append(name)
    for s in out.values():
        s["bask"].sort()
    return out


def attach_structure(tickers: list[dict], universe_path: Path = None,
                     signals_path: Path = None, groups_path: Path = None) -> None:
    """就地给每只票挂 rs / d50 / bask。查不到的票三个键都在，值是 None / []。"""
    idx = load_structure(universe_path, signals_path, groups_path)
    for t in tickers:
        s = idx.get(t["sym"].upper(), {})
        t["rs"] = s.get("rs")
        t["d50"] = s.get("d50")
        t["bask"] = list(s.get("bask") or [])


def rs_cell(v) -> str:
    return "无" if v is None else str(int(v))


def d50_cell(v) -> str:
    """小数 → 百分比字符串。0.1406 → +14.06%。"""
    return "无" if v is None else f"{v * 100:+.2f}%"


def bask_cell(v) -> str:
    return " / ".join(v) if v else "无"


# ─────────────────────────────────────────────────────────────────────────────
# X 热度（给 dashboard 个股页的数据文件；前端归 UI Claire）
#
# 与 ticker_daily.csv 同源同口径：**人数不是帖数**，一条清单帖提十个代码只算一个人。
#   people_7d  = 窗口内提到这只票的**不重复 handle 数**（跨日去重，不是日人数相加）
#   peak_day   = 窗口内单日提及人数最高的 ET 日，**并列取最早**（与峰值日列同一函数）
# ⚠️ **人数的写实口径**：进表的票必须在窗口内至少出现过一次带 $ 的写法（裸代码那半边全是
#    RS/EMA/WHAT 这类假代码，README 口径一），但一只票进表之后，它的 people_7d **把带 $ 和
#    不带 $ 的写法合并去重**——因为 days[] 就是这么聚合的，与 ticker_daily.csv 的日人数
#    完全同口径（一个量一个家，不另立第二本账）。09-23 实测 414 只票里有 89 只两种口径不同，
#    最大一只差 1 人（$MU 合并 22 / 纯 cashtag 21）。给 Claire 的契约行照此写实。
# ─────────────────────────────────────────────────────────────────────────────

def x_heat(data: dict, window: int = HEAT_WINDOW) -> dict:
    dates = data["dates"][-window:] if data["dates"] else []
    rows = []
    for t in data["tickers"]:
        if not t.get("cash"):
            continue
        days = {d: v for d, v in (t.get("days") or {}).items() if d in dates}
        people = {h for v in days.values() for h in (v.get("p") or [])}
        if not people:
            continue
        rows.append({
            "ticker": t["sym"],
            "people_7d": len(people),
            "posts_7d": sum(v.get("n") or 0 for v in days.values()),
            "days_7d": sum(1 for v in days.values() if v.get("p")),
            "peak_day": peak_day(days),
            "peak_people": max((len(v.get("p") or []) for v in days.values()), default=0),
            "is_index": bool(t.get("idx")),
        })
    rows.sort(key=lambda r: (-r["people_7d"], -r["posts_7d"], r["ticker"]))
    return {
        "window_days": window,
        "window": {"start": dates[0] if dates else None,
                   "end": dates[-1] if dates else None},
        "count": len(rows),
        "source": "data/content/x_watch/posts/*.jsonl（同 ticker_daily.csv），"
                  "由 data/content/x_watch/tools/build_board.py 生成",
        "note": "people_7d = 窗口内不重复提及人数（跨日去重，非日人数相加）；"
                "peak_day = 单日人数最高的 ET 日，并列取最早。"
                "进表的票必须在窗口内至少出现过一次带 $ 的写法，但人数把带 $ 与不带 $ 的"
                "写法合并去重（与 ticker_daily.csv 日人数同口径）。"
                "这是「有多少人在说」，不是情绪、不是看多看空。",
        "rows": rows,
    }


def build() -> dict:
    posts, stance, wall = load_posts(), load_stance(), load_wall()
    dates = sorted({p["et_date"] for p in posts})

    tick: dict[str, dict] = {}
    for p in posts:
        text = p.get("text") or ""
        for sym in sorted(set(p.get("tickers") or [])):
            t = tick.setdefault(sym, {"sym": sym, "cash": False, "m": []})
            is_cash = f"${sym}" in text
            t["cash"] = t["cash"] or is_cash
            t["m"].append({
                "d": p["et_date"], "h": p["h"], "st": stance.get((p["id"], sym), ""),
                "v": p.get("views") or 0, "bk": p.get("bookmarks") or 0,
                "rep": bool(p.get("is_reply")), "cash": is_cash,
                "txt": re.sub(r"\s+", " ", text).strip()[:400], "url": p.get("url"),
            })

    # 墙后:哪只票在哪天被 @jfsrev 点过,以及用的是哪个词(Stalk/Focus/Update)
    wall_by_sym: dict[str, list[dict]] = defaultdict(list)
    for w in wall:
        for sym in w["tickers"]:
            wall_by_sym[sym].append({"d": w["d"], "kind": w["kind"],
                                     "proxy": w.get("proxy"), "url": w["url"]})

    # ⭐ 墙后点过、公开区一次没出现的票也要进表 —— 否则它们在页面上根本搜不到,
    #    而那正好是墙的代价所在(基线:墙后 11 只有 7 只公开区零提及)。
    for sym in wall_by_sym:
        if sym not in tick:
            tick[sym] = {"sym": sym, "cash": True, "m": []}

    out_t = []
    for sym, t in tick.items():
        by_day = defaultdict(lambda: {"people": set(), "posts": 0, "views": 0})
        for m in t["m"]:
            b = by_day[m["d"]]
            b["people"].add(m["h"])
            b["posts"] += 1
            b["views"] += m["v"]
        days = {d: {"p": sorted(v["people"]), "n": v["posts"], "v": v["views"]}
                for d, v in by_day.items()}
        st = defaultdict(int)
        for m in t["m"]:
            if m["st"]:
                st[m["st"]] += 1
        out_t.append({
            "sym": sym, "cash": t["cash"], "idx": sym in INDEX, "days": days,
            "st": dict(st), "wall": wall_by_sym.get(sym, []),
            "m": sorted(t["m"], key=lambda m: (m["d"], -m["v"])),
            "tv": sum(m["v"] for m in t["m"]), "tn": len(t["m"]),
            # 窗口内单日最高提及人数。看板默认折叠 mx<2 的票：一个人说过一次的
            # 代码占了大半张表，而「有第二个人也在说」才是这张台账的最低信号。
            "mx": max([len(v["p"]) for v in days.values()] or [0]),
        })
    out_t.sort(key=lambda t: (-len(t["days"].get(dates[-1], {}).get("p", [])), -t["tv"]))
    attach_prices(out_t)
    attach_structure(out_t)

    # 按人
    ppl = defaultdict(lambda: {"posts": 0, "syms": set(), "views": [], "bk": 0, "days": set()})
    for p in posts:
        a = ppl[p["h"]]
        a["posts"] += 1
        a["views"].append(p.get("views") or 0)
        a["bk"] += p.get("bookmarks") or 0
        a["days"].add(p["et_date"])
        for sym in set(p.get("tickers") or []):
            if f"${sym}" in (p.get("text") or ""):
                a["syms"].add(sym)
    out_p = sorted(
        ({"h": h, "posts": a["posts"], "syms": sorted(a["syms"]), "days": len(a["days"]),
          "med": sorted(a["views"])[len(a["views"]) // 2] if a["views"] else 0, "bk": a["bk"]}
         for h, a in ppl.items()),
        key=lambda a: -a["posts"])

    return {"dates": dates, "tickers": out_t, "people": out_p, "wall": wall,
            "stances": STANCES, "horizons": list(HORIZONS), "bench": BENCH,
            "counts": {"posts": len(posts), "people": len(ppl), "syms": len(out_t),
                       "cash": sum(1 for t in out_t if t["cash"])}}


def highlights(data: dict) -> list[dict]:
    """自动挑重点。判据全部写在 why 里,不给形容词。"""
    ds = data["dates"]
    if not ds:
        return []
    today, prev = ds[-1], (ds[-2] if len(ds) > 1 else None)
    out = []

    def np(t, d):
        return len(t["days"].get(d, {}).get("p", [])) if d else 0

    for t in data["tickers"]:
        if not t["cash"]:
            continue
        n, o = np(t, today), np(t, prev)
        wall_today = [w for w in t["wall"] if w["d"] <= today]
        st = t["st"]
        recap = st.get("recap", 0) + st.get("exited", 0)
        fwd = st.get("long", 0) + st.get("watching", 0)
        if n >= 2 and o == 0:
            k = "指数进场" if t["sym"] in INDEX else "新进"
            out.append({"k": k, "sym": t["sym"], "why": f"今天 {n} 人,昨天 0 人", "n": n})
        elif n == 1 and wall_today:
            kinds = "/".join(sorted({w["kind"] for w in wall_today if w["kind"]}))
            out.append({"k": "墙后补票", "sym": t["sym"],
                        "why": f"公开区 1 人,@jfsrev 墙后 {kinds or '点过'} —— 合起来 2 票", "n": n})
        elif n == 0 and o >= 3:
            out.append({"k": "掉榜", "sym": t["sym"], "why": f"昨天 {o} 人,今天 0 人", "n": 0})
        elif n >= 2 and recap > fwd and recap > 0:
            out.append({"k": "已跑完", "sym": t["sym"],
                        "why": f"{n} 人在说,立场里复盘/离场 {recap} 条 > 前瞻 {fwd} 条", "n": n})
        elif n >= 3 and o and n > o:
            out.append({"k": "加人", "sym": t["sym"], "why": f"{o} 人 → {n} 人", "n": n})

    for w in data["wall"]:
        if w["d"] != today:
            continue
        for sym in w["tickers"]:
            pub = next((t for t in data["tickers"] if t["sym"] == sym), None)
            if not pub or not pub["days"].get(today, {}).get("p"):
                out.append({"k": "墙后独有", "sym": sym,
                            "why": f"@jfsrev {w['kind']},公开区当天 0 人提及", "n": 0})
    order = {"墙后补票": 0, "新进": 1, "墙后独有": 2, "加人": 3,
             "已跑完": 4, "掉榜": 5, "指数进场": 6}
    out.sort(key=lambda h: (order.get(h["k"], 9), -h["n"]))
    return out[:8]


def main() -> None:
    data = build()
    data["highlights"] = highlights(data)

    (BASE / "board_data.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # 宽表给 Excel:只出 cashtag 的,行 = ticker,列 = 日期,值 = 当日提及人数
    with (BASE / "ticker_daily.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", *data["dates"], "总提及", "总曝光", "墙后", "立场",
                    "峰值日", f"T+1 vs {BENCH}", f"T+5 vs {BENCH}",
                    "RS 评级", "距 50 日线%", "ETF 篮子"])
        for t in data["tickers"]:
            if not t["cash"]:
                continue
            w.writerow([
                t["sym"],
                *[len(t["days"].get(d, {}).get("p", [])) for d in data["dates"]],
                t["tn"], t["tv"],
                "/".join(sorted({x["kind"] for x in t["wall"] if x["kind"]})),
                " ".join(f"{k}:{v}" for k, v in sorted(t["st"].items())),
                t.get("peak") or "",
                *[price_cell(*t["rel"][k]) for k in HORIZONS],
                rs_cell(t.get("rs")), d50_cell(t.get("d50")), bask_cell(t.get("bask")),
            ])

    # 给 dashboard 个股页的「X 热度」列(前端归 UI Claire)。这是本工具唯一写进
    # data/output/ 的文件,只新增,不碰任何既有 output。
    heat = x_heat(data)
    X_HEAT_PATH.write_text(
        json.dumps(heat, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"x_heat.json ← {heat['count']} 只票 / 窗口 "
          f"{heat['window']['start']}→{heat['window']['end']}")

    if TPL.exists():
        html = TPL.read_text(encoding="utf-8").replace(
            "/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        (BASE / "board.html").write_text(html, encoding="utf-8")
        print(f"board.html ← {len(data['tickers'])} 个代码 / {data['counts']['cash']} 个带 $ / "
              f"{len(data['dates'])} 天 / {len(data['highlights'])} 条重点")
    else:
        print(f"⚠️ 模板缺失 {TPL},只写了 json 和 csv", file=sys.stderr)


if __name__ == "__main__":
    main()
