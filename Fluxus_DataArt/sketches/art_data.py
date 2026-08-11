"""共享数据层:六层语法全部物化。sketch 01+ 从这里取数,不再各自算。"""
import csv, json, datetime as dt, statistics
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
SRC = HERE.parent / "sources"
REPO = HERE.parents[2]

AI_CHAIN = {"Semiconductors Broad", "Semiconductors Large Caps", "Broad AI Theme",
            "AI - Datacenters", "AI Power & Infrastructure", "Memory & Storage",
            "Software", "Grid & Electrification", "Robotics & Automation",
            "Optics & Networking Equipment", "Electronic Components",
            "Quantum Computing", "IT Services", "Uranium & Nuclear Energy"}

KEYFRAMES = [
    ("2026-03-03", "霜冻最深处", "「多做多错。」"),
    ("2026-03-07", "连败终·十七", "「止损是营业成本。」"),
    ("2026-03-30", "所谓连胜", "「账面一回事,心态两回事。」"),
    ("2026-04-23", "剪 BABA", "「希望,穿着预判的衣服。」"),
    ("2026-04-28", "BE 第九次", "「不是胆子,是思考框架。」"),
    ("2026-05-07", "手比脑子快", "「顺风的时候可以赌。」"),
    ("2026-06-02", "两百万·同一天", "「THE MARKET GOD has decided.」"),
    ("2026-06-10", "暴雨之后", "「晒数的诅咒。」"),
    ("2026-07-05", "最长的沉默", "「It's a job.」"),
]

FROST = (dt.date(2026, 2, 26), dt.date(2026, 3, 7))
STORM = (dt.date(2026, 6, 2), dt.date(2026, 6, 10))


def _d(s):
    if not s:
        return None
    return (dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
            if "T" in s else dt.date.fromisoformat(s))


def load():
    # --- species map ---
    groups = json.load(open(SRC / "groups_snapshot.json"))
    t2th = {}
    for t in groups["themes"]:
        if t.get("method") in ("etf", "industry"):
            for tk in (t.get("tickers") or []):
                t2th.setdefault(tk, []).append(t["group"])

    # --- trades ---
    lines = list(csv.reader(open(SRC / "portfolio_2026-07-26.csv")))
    for i, l in enumerate(lines):
        if l and l[0] == "Ticker":
            header, start = l, i + 1
            break
    recs = [dict(zip(header, l)) for l in lines[start:] if l and l[0]]
    trades = []
    for x in recs:
        if x["Closed"] != "YES":
            continue
        e = float(x["Entry Price"]); q = float(x["Original Qty"])
        stop = float(x["Initial Stop"] or x["Stop Price"])
        sgn = 1 if x["Direction"] == "long" else -1
        pnl, last, trims = 0.0, None, 0
        for i in (1, 2, 3):
            if x.get(f"Trim{i} Date"):
                pnl += sgn * (float(x[f"Trim{i} Price"]) - e) * float(x[f"Trim{i} Qty"])
                last = _d(x[f"Trim{i} Date"]); trims += 1
        risk = abs(e - stop) * q
        ths = t2th.get(x["Ticker"], [])
        species = ("ai" if any(t in AI_CHAIN for t in ths)
                   else ("other" if ths else "rootless"))
        trades.append(dict(
            t=x["Ticker"], dir=x["Direction"], entry=_d(x["Entry Date"]), exit=last,
            pnl=pnl, risk=risk, r=pnl / risk if risk > 0 else 0.0, trims=trims,
            hold=(last - _d(x["Entry Date"])).days, species=species))
    trades.sort(key=lambda z: (z["exit"], z["entry"]))

    # equity at entry -> risk% (tension input)
    by_exit = sorted(trades, key=lambda z: z["exit"])
    for t in trades:
        eq = 1_000_000 + sum(x["pnl"] for x in by_exit if x["exit"] < t["entry"])
        t["risk_pct"] = t["risk"] / eq * 100

    # gold = top-31 by pnl (they carry 100% of net P&L)
    for t in sorted(trades, key=lambda z: -z["pnl"])[:31]:
        t["gold"] = True
    for t in trades:
        t.setdefault("gold", False)

    # chain index per ticker
    cnt = defaultdict(int)
    for t in sorted(trades, key=lambda z: (z["entry"], z["exit"])):
        cnt[t["t"]] += 1
        t["attempt"] = cnt[t["t"]]
    total = dict(cnt)
    for t in trades:
        t["attempts_total"] = total[t["t"]]

    # --- regime daily ---
    regime = {}
    for row in csv.DictReader(open(SRC / "regime_daily.csv")):
        regime[dt.date.fromisoformat(row["date"])] = float(row["score"])

    # --- soil: cumulative |loss| by exit date ---
    soil, cum = {}, 0.0
    for t in by_exit:
        if t["pnl"] < 0:
            cum += -t["pnl"]
        soil[t["exit"]] = cum
    soil_total = cum

    # --- rhythm ---
    entries_by_day = defaultdict(int)
    for t in trades:
        entries_by_day[t["entry"]] += 1
    bursts = sorted(d for d, n in entries_by_day.items() if n >= 5)
    edays = sorted(entries_by_day)
    silences = []
    for a, b in zip(edays, edays[1:]):
        if (b - a).days >= 4:
            silences.append((a, b))

    # --- tension per session day (proxy: streak + density + sizing CV) ---
    sessions = sorted(regime)
    streak_at = {}
    s = 0
    for t in by_exit:
        s = s + 1 if t["pnl"] < 0 else 0
        streak_at[t["exit"]] = s
    tension = {}
    last_streak = 0
    recent = []
    ent_sorted = sorted(trades, key=lambda z: z["entry"])
    ei = 0
    for d in sessions:
        while ei < len(ent_sorted) and ent_sorted[ei]["entry"] <= d:
            recent.append(ent_sorted[ei]["risk_pct"]); ei += 1
        last_streak = streak_at.get(d, last_streak)
        w = recent[-10:]
        cv = (statistics.stdev(w) / statistics.mean(w)) if len(w) > 2 and statistics.mean(w) > 0 else 0
        dens = min(entries_by_day.get(d, 0) / 9, 1)
        tension[d] = min(1.0, 0.45 * min(last_streak / 17, 1) + 0.3 * dens + 0.25 * min(cv / 2, 1))

    return dict(trades=trades, regime=regime, soil=soil, soil_total=soil_total,
                bursts=bursts, silences=silences, tension=tension,
                sessions=sessions, keyframes=KEYFRAMES, frost=FROST, storm=STORM)
