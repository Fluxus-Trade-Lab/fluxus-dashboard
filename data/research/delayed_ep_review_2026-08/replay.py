"""Delayed-EP stage review, but market-relative.

`delayed_ep_scan.py --review` prints raw forward returns per stage. Raw
returns are not a claim about the stages: each stage's cohort starts on a
different set of dates, so a difference between two stage medians can be
nothing but the two cohorts having sat in different weeks of the market.

This replay recomputes the same forward returns and subtracts SPY over the
*same* calendar window for each name, so the number being compared is excess
return. It also runs a rank test (Mann-Whitney U, normal approximation) on
the excess returns of the two biggest cohorts, so "these separate" is a
measured claim rather than an eyeballed one.

Read-only: reads data/history/delayed_ep_log.csv, writes nothing.

Run:  python3 data/research/delayed_ep_review_2026-08/replay.py [--horizon 5]
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT / "data" / "history" / "delayed_ep_log.csv"
BENCH = "SPY"


def load_log(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def first_stage_day(log: list[dict]) -> dict[tuple[str, str], dict]:
    """(ticker, stage) -> the first row where that ticker wore that stage."""
    out: dict[tuple[str, str], dict] = {}
    for r in sorted(log, key=lambda r: (r["ticker"], r["as_of"])):
        out.setdefault((r["ticker"], r["stage"]), r)
    return out


def close_series(data: pd.DataFrame, ticker: str, multi: bool) -> pd.Series | None:
    try:
        s = (data[ticker]["Close"] if multi else data["Close"]).dropna()
    except KeyError:
        return None
    return s if len(s) else None


def fwd(series: pd.Series, start: str, k: int) -> float | None:
    """Return over k sessions from the first bar on/after `start`."""
    s = series[series.index >= pd.Timestamp(start)]
    if len(s) <= k:
        return None
    return float(s.iloc[k]) / float(s.iloc[0]) - 1.0


def mannwhitney_u(a: list[float], b: list[float]) -> tuple[float, float] | None:
    """Two-sided U test, normal approximation with tie correction.

    Returns (U, p) or None when either sample is too small for the
    approximation to mean anything.
    """
    na, nb = len(a), len(b)
    if na < 5 or nb < 5:
        return None
    pooled = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks: list[float] = [0.0] * len(pooled)
    i = 0
    ties = 0.0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        t = j - i + 1
        if t > 1:
            ties += t ** 3 - t
        i = j + 1
    ra = sum(r for r, (_, g) in zip(ranks, pooled) if g == 0)
    u_a = ra - na * (na + 1) / 2.0
    n = na + nb
    mu = na * nb / 2.0
    var = na * nb / 12.0 * ((n + 1) - ties / (n * (n - 1)))
    if var <= 0:
        return None
    z = (u_a - mu) / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return u_a, p


def pct(xs: list[float]) -> str:
    xs = sorted(xs)
    med = xs[len(xs) // 2]
    win = sum(1 for x in xs if x > 0) / len(xs) * 100
    return f"median {med * 100:+5.1f}%  n={len(xs):<3} >0: {win:3.0f}%"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--log", type=Path, default=LOG)
    args = ap.parse_args()

    log = load_log(args.log)
    dates = sorted({r["as_of"] for r in log})
    tickers = sorted({r["ticker"] for r in log})
    print(f"log: {len(log)} rows, {len(dates)} sessions "
          f"({dates[0]} .. {dates[-1]}), {len(tickers)} tickers")
    print(f"horizon: {args.horizon} sessions | benchmark: {BENCH}\n")

    syms = tickers + [BENCH]
    data = yf.download(syms, period="90d", interval="1d", group_by="ticker",
                       auto_adjust=False, progress=False, threads=True)
    bench = close_series(data, BENCH, multi=True)
    if bench is None:
        raise SystemExit(f"no {BENCH} bars -- cannot compute excess returns")

    firsts = first_stage_day(log)
    rows: dict[str, list[tuple[str, str, float, float]]] = {}
    missing: list[str] = []
    for (t, stage), r in firsts.items():
        s = close_series(data, t, multi=True)
        if s is None:
            missing.append(t)
            continue
        raw = fwd(s, r["as_of"], args.horizon)
        mkt = fwd(bench, r["as_of"], args.horizon)
        if raw is None or mkt is None:
            continue
        rows.setdefault(stage, []).append((t, r["as_of"], raw, raw - mkt))

    print("forward return from the FIRST day a name wore a stage:")
    print(f"  {'stage':>9}  {'RAW':<34}  EXCESS vs " + BENCH)
    for stage in ("breaking", "basing", "drifting", "failed"):
        rs = rows.get(stage)
        if not rs:
            print(f"  {stage:>9}  (no cohort with {args.horizon} later sessions)")
            continue
        print(f"  {stage:>9}  {pct([x[2] for x in rs]):<34}  {pct([x[3] for x in rs])}")

    # market drift over the same windows, so the raw/excess gap is legible
    drifts = []
    for rs in rows.values():
        for _, d, raw, exc in rs:
            drifts.append(raw - exc)
    if drifts:
        drifts.sort()
        print(f"\n  {BENCH} over those same windows: "
              f"median {drifts[len(drifts) // 2] * 100:+.1f}% "
              f"(min {drifts[0] * 100:+.1f}%, max {drifts[-1] * 100:+.1f}%)")

    # the one comparison the method actually rests on, tested
    print("\nrank test on EXCESS returns (two-sided Mann-Whitney U):")
    pairs = [("basing", "failed"), ("basing", "drifting"), ("breaking", "basing")]
    for a, b in pairs:
        ra, rb = rows.get(a), rows.get(b)
        if not ra or not rb:
            print(f"  {a} vs {b}: one cohort empty")
            continue
        res = mannwhitney_u([x[3] for x in ra], [x[3] for x in rb])
        if res is None:
            print(f"  {a} vs {b}: n={len(ra)}/{len(rb)} -- too small to test, "
                  "no p reported")
            continue
        _, p = res
        print(f"  {a} (n={len(ra)}) vs {b} (n={len(rb)}): p={p:.4f}"
              f"{'  <- separates at 0.05' if p < 0.05 else ''}")

    # how independent are these observations, really
    starts: dict[str, set[str]] = {}
    for stage, rs in rows.items():
        starts[stage] = {d for _, d, _, _ in rs}
    all_starts = sorted(set().union(*starts.values())) if starts else []
    if all_starts:
        span = (pd.Timestamp(all_starts[-1]) - pd.Timestamp(all_starts[0])).days
        print("\nindependence check -- the cohorts are NOT n independent draws:")
        print(f"  distinct start dates: {len(all_starts)} "
              f"({all_starts[0]} .. {all_starts[-1]}, {span} calendar days)")
        print(f"  every {args.horizon}-session forward window therefore overlaps "
              "every other by at least "
              f"{max(0, args.horizon - len(all_starts) + 1)}/{args.horizon} sessions.")
        print("  effective sample size is closer to the number of distinct "
              "windows than to n. Read the p-values above as an upper bound on "
              "significance, not as the significance.")

    if missing:
        print(f"\nno bars for {len(missing)} tickers: {', '.join(sorted(set(missing)))}")


if __name__ == "__main__":
    main()
