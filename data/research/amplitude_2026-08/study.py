"""Is the SIZE of the next move predictable, when the direction is not?

Pre-registration: data/research/amplitude_2026-08/prereg_amplitude.md
(written and committed as 563c05b1 BEFORE this file computed anything).

Andy's own framing (2026-08-24): the third and hardest question is
"will the next move be big or small?", because that is what sets size.
Two X posts he saved on 08-24 land on the same spot from other directions --
@Hrundel75 on vol clustering, @Muninn on ADR across 900 Qullamaggie entries.

Every earlier study here asked whether a gate lifts the MEDIAN excess and got
the same answer every time: it lifts win rate to a coin flip and no further.
So this one changes the outcome variable instead of hunting for another gate.
Primary metric is the RIGHT TAIL, P(excess_5 >= +10%), because Andy's account
is a 3.40x-payoff / 39.9%-win-rate book where the median was never the
decision quantity.

Lives under data/research/ rather than pipeline/tools/ on purpose: this
session can merge data/research/** on its own, and a study stranded on a
branch is a study that did not happen.

Run:  python3 data/research/amplitude_2026-08/study.py            # discovery
      python3 data/research/amplitude_2026-08/study.py --holdout  # burns it
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[3]
# The price panel is a machine-written cache and lives only in the main tree,
# not in this session's worktree. Prefer the local one when it exists.
PANEL = next(c for c in (ROOT / ".cache/price_panel.pkl",
                         Path.home() / "Documents/AI-Trading-System/.cache/price_panel.pkl")
             if c.exists())
EVENTS = ROOT / "data/history/ticker_events.csv"
SCREENER = "gainers_4pct"
MIN_GAP_SESSIONS = 10
NEAR_HIGH = 0.70          # B1, copied from the 08-24 prereg, not re-chosen
NARROW_LOOKBACK = 9       # B2, ditto
VOL_LOOKBACK = 20         # ADR20 and pre_vol, both EXCLUDING the event day
RIGHT_TAIL = 0.10         # P(excess_5 >= +10%)
SALT = "amp2026"          # new split: the md5(ticker)%10 one was burned 08-24

# Muninn's own boundaries, not ones this study picked.
ADR_BINS = [-np.inf, 0.25, 0.5, 1.0, 2.0, np.inf]
ADR_LABELS = ["<0.25", "0.25-0.5", "0.5-1.0", "1.0-2.0", ">=2.0"]


def arm(ticker: str) -> str:
    h = int(hashlib.md5((ticker + SALT).encode()).hexdigest()[:2], 16)
    return "discovery" if h % 10 < 7 else "holdout"


def gates(df: pd.DataFrame, i: int) -> dict:
    """B1/B2/B3 exactly as pre-registered on 08-24. Not redefined here."""
    c, h, l = df["Close"], df["High"], df["Low"]
    b3 = not (c.iloc[i - 1] > c.iloc[i - 2] > c.iloc[i - 3] > c.iloc[i - 4])
    prior_rng = (h.iloc[i - 1] - l.iloc[i - 1]) / c.iloc[i - 1]
    hist = ((h - l) / c).iloc[i - 10:i - 1]
    b2 = bool(prior_rng < hist.median()) or bool(c.iloc[i - 1] < c.iloc[i - 2])
    rng = h.iloc[i] - l.iloc[i]
    b1 = True if rng <= 0 else bool((c.iloc[i] - l.iloc[i]) / rng >= NEAR_HIGH)
    return {"B3": b3, "B2": b2, "B1": b1, "Ball": b3 and b2 and b1}


def build(panel: dict) -> pd.DataFrame:
    spy = panel["SPY"]["Close"]
    by_ticker: dict[str, list[str]] = {}
    with EVENTS.open() as fh:
        for r in csv.DictReader(fh):
            if r["screener"] == SCREENER:
                by_ticker.setdefault(r["ticker"], []).append(r["date"])

    rows = []
    for t, dates in by_ticker.items():
        df = panel.get(t)
        if df is None or len(df) < 30:
            continue
        idx = df.index
        c, h, l = df["Close"], df["High"], df["Low"]
        last_i = -10 ** 9
        for d in sorted(set(dates)):
            ts = pd.Timestamp(d)
            pos = idx.searchsorted(ts)
            if pos >= len(idx) or idx[pos] != ts:
                continue
            if pos < VOL_LOOKBACK + 1 or pos - last_i < MIN_GAP_SESSIONS:
                continue

            # Both vol measures look BACKWARD only: window ends at pos-1.
            win = slice(pos - VOL_LOOKBACK, pos)
            adr20 = float((h.iloc[win] / l.iloc[win] - 1).mean())
            pre_vol = float(((h.iloc[win] - l.iloc[win]) / c.iloc[win]).median())
            if not np.isfinite(adr20) or adr20 <= 0 or not np.isfinite(pre_vol):
                continue

            move = float(c.iloc[pos] / c.iloc[pos - 1] - 1)   # event-day close-to-close
            row = {
                "ticker": t, "date": d, "arm": arm(t),
                "adr20": adr20, "pre_vol": pre_vol,
                "move": move, "move_adr": move / adr20,
                **gates(df, pos),
            }
            ok = False
            for hz in (3, 5):
                if pos + hz >= len(idx):
                    row[f"excess_{hz}"] = None
                    continue
                sp0, sp1 = spy.reindex([idx[pos]]).iloc[0], spy.reindex([idx[pos + hz]]).iloc[0]
                if pd.isna(sp0) or pd.isna(sp1):
                    row[f"excess_{hz}"] = None
                    continue
                stock = c.iloc[pos + hz] / c.iloc[pos] - 1
                row[f"excess_{hz}"] = float(stock - (sp1 / sp0 - 1))
                ok = True
            if ok:
                last_i = pos
                rows.append(row)
    return pd.DataFrame(rows)


def two_prop_p(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sided z test on two proportions. 1.0 when a cell is empty."""
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = k1 / n1, k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = (p * (1 - p) * (1 / n1 + 1 / n2)) ** 0.5
    if se == 0:
        return 1.0
    from math import erfc
    return float(erfc(abs(p1 - p2) / se / 2 ** 0.5))


def amp(s: pd.Series) -> dict:
    """The three amplitude numbers, the direction control, and the money question.

    payoff/expectancy are NOT in the original prereg metric list. They are added
    because prereg section 7.1 committed to answering "does predictable amplitude
    turn into money", and it cannot be answered from medians. Counted as added
    specs in the writeup rather than slipped in.

    Winsorised at the 1st/99th percentile before any mean: the panel carries
    split and bad-bar rows (a +4598% row exists) and one of them owns any raw mean.
    """
    w = s.clip(s.quantile(0.01), s.quantile(0.99)) if len(s) >= 100 else s
    wins, losses = s[s > 0], s[s <= 0]
    aw = float(w[w > 0].mean()) if (w > 0).any() else 0.0
    al = float(w[w <= 0].mean()) if (w <= 0).any() else 0.0
    win = float((s > 0).mean())
    return {
        "n": len(s),
        "p_right": float((s >= RIGHT_TAIL).mean()),
        "med_abs": float(s.abs().median()),
        "iqr": float(s.quantile(0.75) - s.quantile(0.25)),
        "median": float(s.median()),          # the control: direction
        "win": win,
        "mean_w": float(w.mean()),            # winsorised mean excess
        "avg_win": aw, "avg_loss": al,
        "payoff": float(aw / abs(al)) if al else float("nan"),
        "expectancy": float(win * aw + (1 - win) * al),
        "n_wild": int((s.abs() > 1.0).sum()),  # |excess| > 100%: split or bad bar
    }


def h1_gate(d: pd.DataFrame, col: str, out: dict) -> None:
    """H1: does B-all move the right tail, or only trim the losing half?"""
    sub = d[d[col].notna()]
    a, b = sub.loc[sub["Ball"], col], sub.loc[~sub["Ball"], col]
    ra, rb = amp(a), amp(b)
    p_tail = two_prop_p(int((a >= RIGHT_TAIL).sum()), len(a),
                        int((b >= RIGHT_TAIL).sum()), len(b))
    p_absl = mannwhitneyu(a.abs(), b.abs(), alternative="two-sided").pvalue
    print(f"\n  H1  B-all vs cut, on {col}")
    print(f"      {'':<8}{'n':>7}{'P_right':>9}{'med|x|':>9}{'IQR':>8}{'median':>9}{'win%':>7}"
          f"{'payoff':>8}{'expect':>8}")
    for lab, r in (("pass", ra), ("cut", rb)):
        print(f"      {lab:<8}{r['n']:>7}{r['p_right']*100:>8.2f}%{r['med_abs']*100:>8.2f}%"
              f"{r['iqr']*100:>7.1f}%{r['median']*100:>8.2f}%{r['win']*100:>6.1f}%"
              f"{r['payoff']:>8.2f}{r['expectancy']*100:>7.2f}%")
    print(f"      diff    {'':>7}{(ra['p_right']-rb['p_right'])*100:>+8.2f}pp"
          f"{(ra['med_abs']-rb['med_abs'])*100:>+8.2f}pp  "
          f"p_tail={p_tail:.4f}  p_|x|={p_absl:.4f}")
    out["h1"] = {"pass": ra, "cut": rb, "p_tail": p_tail, "p_abs": float(p_absl)}


def bucket_table(d: pd.DataFrame, col: str, key: str, labels, name: str, out: dict) -> None:
    sub = d[d[col].notna() & d[key].notna()]
    print(f"\n  {name}  ({key} buckets, on {col})")
    print(f"      {'bucket':<10}{'n':>7}{'P_right':>9}{'med|x|':>9}{'IQR':>8}{'median':>9}{'win%':>7}"
          f"{'payoff':>8}{'expect':>8}{'wild':>6}")
    rec = {}
    for lab in labels:
        s = sub.loc[sub[key + "_bin"] == lab, col]
        if len(s) < 30:
            print(f"      {lab:<10}{len(s):>7}   (too few)")
            rec[lab] = {"n": len(s)}
            continue
        r = amp(s)
        rec[lab] = r
        print(f"      {lab:<10}{r['n']:>7}{r['p_right']*100:>8.2f}%{r['med_abs']*100:>8.2f}%"
              f"{r['iqr']*100:>7.1f}%{r['median']*100:>8.2f}%{r['win']*100:>6.1f}%"
              f"{r['payoff']:>8.2f}{r['expectancy']*100:>7.2f}%{r['n_wild']:>6}")
    out[name] = rec


def placebo(d: pd.DataFrame, col: str = "excess_5", n: int = 20) -> float:
    """08-24 measured this design's p at ~3x optimistic. Re-measured, not assumed."""
    sub = d[d[col].notna()]
    sig = 0
    for k in range(n):
        flag = sub["ticker"].map(
            lambda t: int(hashlib.md5((t + f"psalt{k}").encode()).hexdigest()[:8], 16) % 100 < 67)
        a, b = sub.loc[flag, col].abs(), sub.loc[~flag, col].abs()
        if mannwhitneyu(a, b, alternative="two-sided").pvalue < 0.05:
            sig += 1
    print(f"\n  placebo on |{col}|: {sig}/{n} meaningless splits reach p<0.05 "
          f"(1/{n} expected) -- read p here as roughly {max(sig,1)}x optimistic")
    return sig / n


def run(d: pd.DataFrame, label: str, out: dict) -> None:
    print(f"\n===== {label}  (n={len(d)}, {d['ticker'].nunique()} tickers, "
          f"{d['date'].min()} .. {d['date'].max()}) =====")
    col = "excess_5"
    base = amp(d[d[col].notna()][col])
    print(f"  baseline all rows: n={base['n']} P_right={base['p_right']*100:.2f}% "
          f"med|x|={base['med_abs']*100:.2f}% median={base['median']*100:+.2f}% "
          f"win={base['win']*100:.1f}%")
    out["baseline"] = base
    h1_gate(d, col, out)
    bucket_table(d, col, "move_adr", ADR_LABELS, "H2_move_adr", out)
    bucket_table(d, col, "pre_vol", [f"Q{i}" for i in range(1, 6)], "H3_pre_vol", out)
    sub = d[d[col].notna()]
    from scipy.stats import spearmanr
    rho_amp = spearmanr(sub["pre_vol"], sub[col].abs())
    rho_dir = spearmanr(sub["pre_vol"], sub[col])
    q5, q1 = sub.loc[sub["pre_vol_bin"] == "Q5", col], sub.loc[sub["pre_vol_bin"] == "Q1", col]
    p_q = mannwhitneyu(q5.abs(), q1.abs(), alternative="two-sided").pvalue
    p_tail_q = two_prop_p(int((q5 >= RIGHT_TAIL).sum()), len(q5),
                          int((q1 >= RIGHT_TAIL).sum()), len(q1))
    print(f"\n  H3 strength: spearman(pre_vol, |excess_5|) = {rho_amp.statistic:+.3f} "
          f"(p={rho_amp.pvalue:.2e})   vs direction spearman(pre_vol, excess_5) = "
          f"{rho_dir.statistic:+.3f} (p={rho_dir.pvalue:.3f})")
    print(f"  H3 Q5 vs Q1: |excess| p={p_q:.2e}   P_right p={p_tail_q:.2e}")
    out["H3_spearman_amp"] = [float(rho_amp.statistic), float(rho_amp.pvalue)]
    out["H3_spearman_dir"] = [float(rho_dir.statistic), float(rho_dir.pvalue)]
    out["H3_q5q1_p"] = [float(p_q), float(p_tail_q)]
    out["placebo"] = placebo(d, col)
    # H3's whole claim is that direction should NOT trend across pre_vol quintiles.
    meds = [out["H3_pre_vol"].get(f"Q{i}", {}).get("median") for i in range(1, 6)]
    if all(m is not None for m in meds):
        mono = all(meds[i] <= meds[i + 1] for i in range(4)) or \
               all(meds[i] >= meds[i + 1] for i in range(4))
        print(f"  H3 direction control: median excess across Q1..Q5 = "
              f"{', '.join(f'{m*100:+.2f}%' for m in meds)}  -> monotone: {mono}")
        out["H3_direction_monotone"] = mono


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--holdout", action="store_true")
    a = ap.parse_args()
    panel = pickle.load(open(PANEL, "rb"))
    df = build(panel)

    # Pre-registered: report the correlation, both vol measures may be one thing.
    r = df[["move_adr", "pre_vol", "adr20"]].corr(method="spearman")
    print(f"events after de-overlap: {len(df)}  "
          f"(discovery {(df['arm']=='discovery').sum()} / holdout {(df['arm']=='holdout').sum()})")
    print(f"spearman  adr20~pre_vol {r.loc['adr20','pre_vol']:+.3f}   "
          f"move_adr~pre_vol {r.loc['move_adr','pre_vol']:+.3f}")

    df["move_adr_bin"] = pd.cut(df["move_adr"], ADR_BINS, labels=ADR_LABELS)
    # Quintiles are cut on the FULL sample so discovery and holdout share edges.
    df["pre_vol_bin"] = pd.qcut(df["pre_vol"], 5, labels=[f"Q{i}" for i in range(1, 6)])
    edges = df["pre_vol"].quantile([0, .2, .4, .6, .8, 1]).round(5).tolist()
    print(f"pre_vol quintile edges: {edges}")

    out = {"n_events": len(df), "spearman_adr_prevol": float(r.loc['adr20', 'pre_vol']),
           "pre_vol_edges": edges, "salt": SALT}
    run(df[df["arm"] == "discovery"], "DISCOVERY", out.setdefault("discovery", {}))
    if a.holdout:
        run(df[df["arm"] == "holdout"], "HOLDOUT  (burned)", out.setdefault("holdout", {}))
    else:
        print("\nholdout NOT run.")
    Path(__file__).with_name("results.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
