#!/usr/bin/env python3
"""圈子情绪/注意力指标 —— 每日班收尾跑一次。

**全部纯计数或纯比例，不读立场、不判方向**（Andy 2026-09-07:「我只需要有人
提醒到这个 ticker 就可以了，不需要方向」）。

用法（每日班抓完公开区之后跑）:
    python3 data/content/x_watch/scoring/mood_index.py --date 2026-09-08

它做三件事:
  1. 读 posts/<date>.jsonl，算七个比例型指标
  2. 幂等地写进 scoring/mood_daily.csv（同日期重跑=覆盖那一行，不重复追加）
  3. 判「圈外主题起量」并在过闸时追一行 scoring/theme_events.csv

⚠️ coverage 从 runlog.csv 判：oldest_raw_utc 必须早于 since_et 的 00:00 ET，
   否则这一天是 partial —— **partial 的行照写，但打标，画基线时必须排除**。
   （09-07 实测:两周回抓都撞页数上限没翻到底，把 4.5 天和 3 天放一起比，
     "帖数 1081 vs 1512" 是覆盖差异不是活跃度差异。）
"""
from __future__ import annotations
import argparse, csv, json, re, sys, collections, statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "content" / "x_watch"
ET = timezone(timedelta(hours=-4))

# ── 圈外主题（非美股个股）· 代理标的用于当日 α 闸 ──────────────────
OUT_THEME = {
    "gold":   ({"GLD","GDX","GDXJ","NUGT","JNUG","PALL","SIL","SLV","XAUUSD",
                "AEM","NEM","WPM","FNV","KGC","AGI","AU"}, "GLD"),
    "crypto": ({"IBIT","ETHA","MSTR","COIN","BTC","BTCUSD","ETH","ETHUSD","BITO",
                "BMNR","MARA","RIOT","CLSK","GLXY","SOL","XRP","XXRP","ETHU","FBTC"}, "IBIT"),
    "energy": ({"USO","UCO","XLE","XOP","OIH","WTI","UNG","NGAS","BOIL"}, "XLE"),
    "fx_rates":({"TLT","IEF","DXY","UUP","US10Y","TNX","JPY","EUR","FXY"}, "TLT"),
}
INDEX = {"SPY","QQQ","IWM","DIA","SPX","NDX","RSP","QQQE","VIX","UVIX","VXX"}

# 只数词，不判谁对谁错
DEF = re.compile(r"(?i)\b(cash|sidelines?|risk[ -]?off|stopped out|stop(?:ped)? me out|"
                 r"cut (?:my|the)|trim(?:med|ming)?|de-?risk|defensive|hedg(?:e|ed|ing)|"
                 r"drawdown|chop(?:py)?|sit (?:this )?out|patien(?:ce|t)|caution|careful)\b")
OFF = re.compile(r"(?i)\b(breakout|break(?:ing)? out|added|adding|starter|full size|"
                 r"press(?:ing)?|leader(?:ship)?|thrust|follow[- ]through|new high|"
                 r"all[- ]time high|ripping|squeeze|momo|risk[ -]?on)\b")

# ⚠️ 改动 DEF/OFF 词表或 OUT_THEME 就把 CALC 加一版，并把全部历史行重算。
#    09-07 实测:我删了一个 `wait` 就让同一天的 defensive_share 从 0.037 变 0.030，
#    而旧行没重算 —— 一张静默混龄的表，每一行看着都对。
CALC = "v1"

COLS = ["date","posts","people","reply_share","top3_conc","defensive_share",
        "offensive_share","def_off","out_gold","out_crypto","out_energy","out_fx",
        "index_people","coverage","calc"]


def tickers(text: str) -> set[str]:
    return {m.upper() for m in re.findall(r"\$([A-Za-z][A-Za-z.\-]{0,5})\b", text)
            if len(m) <= 5}


def metrics(rows: list[dict]) -> tuple[dict, dict]:
    n = len(rows) or 1
    ppl = collections.defaultdict(set)
    for r in rows:
        for t in tickers(r.get("text") or ""):
            ppl[t].add(r["h"])
    tot = sum(len(v) for v in ppl.values()) or 1
    top3 = sorted(ppl.items(), key=lambda x: -len(x[1]))[:3]
    d = sum(1 for r in rows if DEF.search(r.get("text") or ""))
    o = sum(1 for r in rows if OFF.search(r.get("text") or ""))
    theme_people = {}
    for g, (syms, _) in OUT_THEME.items():
        theme_people[g] = {h for t in syms & set(ppl) for h in ppl[t]}
    m = {
        "posts": len(rows),
        "people": len({r["h"] for r in rows}),
        "reply_share": round(sum(1 for r in rows if r.get("is_reply")) / n, 3),
        "top3_conc": round(sum(len(v) for _, v in top3) / tot, 3),
        "defensive_share": round(d / n, 3),
        "offensive_share": round(o / n, 3),
        "def_off": round(d / max(o, 1), 2),
        "out_gold": len(theme_people["gold"]),
        "out_crypto": len(theme_people["crypto"]),
        "out_energy": len(theme_people["energy"]),
        "out_fx": len(theme_people["fx_rates"]),
        "index_people": len({h for t in INDEX & set(ppl) for h in ppl[t]}),
    }
    return m, theme_people


def coverage(date: str) -> str:
    """runlog 最后一行的 oldest_raw_utc 早于 since_et 00:00 ET 才算 full。"""
    p = OUT / "runlog.csv"
    if not p.exists():
        return "unknown"
    rows = list(csv.DictReader(p.open()))
    if not rows:
        return "unknown"
    last = rows[-1]
    old, since = last.get("oldest_raw_utc"), last.get("since_et")
    if not old or not since:
        return "partial"          # 空跑（402/超时）也算不完整
    try:
        o = datetime.fromisoformat(old.replace("Z", "+00:00")).astimezone(ET)
        s = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=ET)
    except ValueError:
        return "unknown"
    return "full" if o < s else "partial"


def day_alpha(proxy: str, date: str):
    """代理标的当日相对 SPY 的涨跌。取不到返回 None —— 取不到就不判庆功。"""
    try:
        import warnings; warnings.filterwarnings("ignore")
        import yfinance as yf, pandas as pd
        d0 = datetime.strptime(date, "%Y-%m-%d")
        px = yf.download([proxy, "SPY"], start=(d0 - timedelta(days=12)).strftime("%Y-%m-%d"),
                         end=(d0 + timedelta(days=2)).strftime("%Y-%m-%d"),
                         progress=False, auto_adjust=True)["Close"]
        px.index = pd.to_datetime(px.index).tz_localize(None)
        out = []
        for t in (proxy, "SPY"):
            s = px[t].dropna()
            i = s.index[s.index <= pd.Timestamp(date)]
            if len(i) < 2:
                return None
            # ⚠️ 该日必须真的有价格。没有就返回 None，**不静默用前一天** ——
            #    09-07 实测:yfinance 只到 09-04，09-05/09-06 会拿到 09-04 的涨跌，
            #    两天读出同一个 α，看着像数据其实是同一格。
            if i[-1].date().isoformat() != date:
                print(f"  ⚠️ {t} 在 {date} 没有价格（最后一根是 {i[-1].date()}）"
                      f" —— 当日 α 不算，该主题不判庆功")
                return None
            k = s.index.get_loc(i[-1])
            out.append(s.iloc[k] / s.iloc[k - 1] - 1)
        return out[0] - out[1]
    except Exception as e:
        print(f"  ⚠️ {proxy} 当日 α 取不到（{type(e).__name__}）—— 该主题不判庆功，人工看一眼")
        return None


def upsert(path: Path, cols: list[str], key: str, row: dict) -> None:
    rows = list(csv.DictReader(path.open())) if path.exists() else []
    rows = [r for r in rows if r.get(key) != row[key]]
    rows.append({c: row.get(c, "") for c in cols})
    rows.sort(key=lambda r: r[key])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="ET 日期 YYYY-MM-DD")
    ap.add_argument("--min-people", type=int, default=3, help="圈外主题起量的人数闸")
    ap.add_argument("--alpha-gate", type=float, default=0.02,
                    help="代理标的当日 |α| 超过它就是庆功不是起量")
    ap.add_argument("--from", dest="src", help="回算历史用:指定 jsonl 路径，"
                    "不读 posts/<date>.jsonl（每日班不要用这个）")
    a = ap.parse_args()

    src = Path(a.src) if a.src else OUT / "posts" / f"{a.date}.jsonl"
    if not src.exists():
        sys.exit(f"没有 {src} —— 先跑 fetch.py，或者今天是空跑（那就别写这一行）")
    rows = [json.loads(l) for l in src.open(encoding="utf-8") if l.strip()]
    if not rows:
        sys.exit(f"{src} 是空的 —— 不写 mood_daily.csv")

    m, theme_people = metrics(rows)
    cov = coverage(a.date)
    upsert(OUT / "scoring" / "mood_daily.csv", COLS, "date",
           {"date": a.date, **m, "coverage": cov, "calc": CALC})

    print(f"mood_daily.csv ← {a.date}  帖{m['posts']} 人{m['people']}  "
          f"回复{m['reply_share']} 集中{m['top3_conc']}  "
          f"防守{m['defensive_share']} 进攻{m['offensive_share']} 防守/进攻{m['def_off']}  "
          f"[{cov}]")
    if cov != "full":
        print("  ⚠️ coverage 不是 full —— 这一行画基线时要排除。先确认 fetch 翻到底了。")

    # ── 圈外主题起量 ────────────────────────────────────────────
    fired = []
    for g, who in theme_people.items():
        if len(who) < a.min_people:
            continue
        proxy = OUT_THEME[g][1]
        da = day_alpha(proxy, a.date)
        if da is not None and abs(da) > a.alpha_gate:
            print(f"  ⚠️ {g}: {len(who)} 人，但 {proxy} 当日 α {da:+.1%} 超闸 "
                  f"→ **庆功不是起量**，写进第 2 节「已经跑完的」，不记事件")
            continue
        fired.append((g, who, proxy, da))
        upsert(OUT / "scoring" / "theme_events.csv",
               ["date","theme","n_people","handles","proxy","day_alpha",
                "fwd5_alpha","fwd21_alpha","note"], "date",
               {"date": a.date, "theme": g, "n_people": len(who),
                "handles": "|".join(sorted(who)), "proxy": proxy,
                "day_alpha": "" if da is None else f"{da:.4f}",
                "note": "day_alpha 取不到，未过庆功闸" if da is None else ""})
    if fired:
        for g, who, proxy, da in fired:
            d = "—" if da is None else f"{da:+.1%}"
            print(f"  ⭐ 圈外主题起量: {g} · {len(who)} 人 · {proxy} 当日 α {d}")
            print(f"     → 置顶第 3 节；已记进 theme_events.csv（fwd5/fwd21 过 5/21 个交易日回填）")
    else:
        print("  圈外主题:无起量（这是常态 —— 基线三天里贵金属/能源/债汇的提及人数是 0）")


if __name__ == "__main__":
    main()
