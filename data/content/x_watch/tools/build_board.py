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
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "data/content/x_watch"
TPL = Path(__file__).with_name("board_template.html")

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
        })
    out_t.sort(key=lambda t: (-len(t["days"].get(dates[-1], {}).get("p", [])), -t["tv"]))

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
            "stances": STANCES,
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
        w.writerow(["ticker", *data["dates"], "总提及", "总曝光", "墙后", "立场"])
        for t in data["tickers"]:
            if not t["cash"]:
                continue
            w.writerow([
                t["sym"],
                *[len(t["days"].get(d, {}).get("p", [])) for d in data["dates"]],
                t["tn"], t["tv"],
                "/".join(sorted({x["kind"] for x in t["wall"] if x["kind"]})),
                " ".join(f"{k}:{v}" for k, v in sorted(t["st"].items())),
            ])

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
