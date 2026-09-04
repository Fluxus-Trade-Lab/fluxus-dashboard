#!/usr/bin/env python3
"""金9银10 / autumn effect -- every number in results.md is printed by this file.

Prose is not allowed to contain a hand-typed number (pitfall_i_misread_my_own_table).
Run:  python3 data/research/gold_autumn_2026-09/run.py
"""
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Pre-registered, from 00_prereg.md. Nothing here may change after the fact.
IN_SAMPLE = (1980, 2010)          # Baur's window
OUT_SAMPLE = (2011, 2026)         # not chosen by us: it is whatever came after

# The pre-registration says the holdout ends 2026-08. The feed carries three
# days of 2026-09, and a three-day "September" counted as a September is the
# shape of pitfall_having_a_row_is_not_having_data: the cell has a value, the
# n goes up by one, and every count-based check stays happy. Caught because
# September came back n=16 while October and November came back n=15.
LAST_COMPLETE = (2026, 8)
NAMED = [("gold", 9), ("gold", 11), ("gold", 10), ("silver", 10)]
ALPHA = 0.05 / len(NAMED)


def monthly_last(path: Path, col: int = 0) -> dict[tuple[int, int], float]:
    """(year, month) -> last quoted USD fix of that month.

    Reads either the LBMA daily JSON or the monthly CSV committed beside this
    file. Only the CSV is in the repository: the two JSON feeds are ~1.8 MB of
    daily fixes and every number here needs one price per month. Refetch with

        curl -s https://prices.lbma.org.uk/json/gold_pm.json   -o lbma_gold.json
        curl -s https://prices.lbma.org.uk/json/silver.json    -o lbma_silver.json

    and this function will read those instead if they are present.
    """
    out: dict[tuple[int, int], float] = {}
    if path.suffix == ".json":
        rows = [(r["d"], r["v"][col]) for r in json.loads(path.read_text())
                if r.get("v")]
    else:
        rows = [(ln.split(",")[0], float(ln.split(",")[1]))
                for ln in path.read_text().splitlines()[1:] if ln.strip()]
    for d, v in rows:
        if v is None:
            continue
        y, m, _ = (int(x) for x in d.split("-"))
        if (y, m) > LAST_COMPLETE:
            continue
        out[(y, m)] = float(v)        # rows are chronological; last write wins
    return out


def _source(metal: str) -> Path:
    """The daily JSON if someone refetched it, else the committed monthly CSV."""
    j = HERE / f"lbma_{metal}.json"
    return j if j.exists() else HERE / f"lbma_{metal}_monthly.csv"


def log_returns(px: dict) -> dict[tuple[int, int], float]:
    keys = sorted(px)
    out = {}
    for prev, cur in zip(keys, keys[1:]):
        # only consecutive calendar months
        if (prev[0] * 12 + prev[1]) + 1 != (cur[0] * 12 + cur[1]):
            continue
        out[cur] = math.log(px[cur] / px[prev])
    return out


def t_one_sided(xs):
    n = len(xs)
    if n < 3:
        return float("nan"), float("nan")
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    if sd == 0:
        return float("nan"), float("nan")
    t = m / (sd / math.sqrt(n))
    # survival of Student-t with n-1 df, one-sided (upper tail)
    return t, _t_sf(t, n - 1)


def _t_sf(t, df):
    """P(T > t). Uses the incomplete beta identity; no scipy in this env."""
    x = df / (df + t * t)
    p = 0.5 * _betainc(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def _betainc(a, b, x):
    """Regularised incomplete beta I_x(a,b), continued fraction (NR 6.4)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta)
    if x < (a + 1) / (a + b + 2):
        return front * _bcf(a, b, x) / a
    return 1.0 - math.exp(b * math.log(1 - x) + a * math.log(x) - lbeta) * \
        _bcf(b, a, 1 - x) / b


def _bcf(a, b, x, itmax=300, eps=3e-16):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / (c if abs(c) > 1e-300 else 1e-300)
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / (c if abs(c) > 1e-300 else 1e-300)
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def sign_test(xs):
    """(positives, n_nonzero, one-sided binomial p, minimum possible p)."""
    nz = [x for x in xs if x != 0]
    n, k = len(nz), sum(1 for x in nz if x > 0)
    if n == 0:
        return 0, 0, float("nan"), float("nan")
    p = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return k, n, p, 1.0 / (2 ** n)


def cell(rets, month, lo, hi):
    xs = [v for (y, m), v in sorted(rets.items()) if m == month and lo <= y <= hi]
    t, pt = t_one_sided(xs)
    k, n, ps, pmin = sign_test(xs)
    return {"n": len(xs), "mean_pct": 100 * (sum(xs) / len(xs)) if xs else float("nan"),
            "t": t, "p_t": pt, "pos": k, "n_sign": n, "p_sign": ps, "p_min": pmin}


def fmt(c):
    return (f"n={c['n']:>3}  mean={c['mean_pct']:+6.2f}%  t={c['t']:+5.2f}  "
            f"p_t={c['p_t']:.4f}  signs={c['pos']}/{c['n_sign']}  "
            f"p_sign={c['p_sign']:.4f}  (p_min={c['p_min']:.2e})")


def main():
    px = {"gold": monthly_last(_source("gold")),
          "silver": monthly_last(_source("silver"))}
    rets = {k: log_returns(v) for k, v in px.items()}

    # Guard, not a comment: every pre-registered cell in one window must have
    # the same n. An off-by-one there means an incomplete month slipped in.
    for lo, hi in (IN_SAMPLE, OUT_SAMPLE):
        ns = {(metal, month): cell(rets[metal], month, lo, hi)["n"]
              for metal, month in NAMED}
        assert len(set(ns.values())) == 1, (lo, hi, ns)

    print("=" * 78)
    print("DATA")
    for k, v in px.items():
        ks = sorted(v)
        print(f"  {k:6} monthly fixes: {len(ks):4}  {ks[0][0]}-{ks[0][1]:02d} "
              f"-> {ks[-1][0]}-{ks[-1][1]:02d}   returns: {len(rets[k])}")
        gaps = [(a, b) for a, b in zip(ks, ks[1:])
                if (a[0] * 12 + a[1]) + 1 != (b[0] * 12 + b[1])]
        print(f"         non-consecutive month gaps: {len(gaps)} {gaps[:5]}")

    print("=" * 78)
    print(f"PRE-REGISTERED CELLS (Bonferroni alpha = 0.05/{len(NAMED)} = {ALPHA:.4f})")
    for label, (lo, hi) in [("IN-SAMPLE  (Baur 1980-2010, replication check)", IN_SAMPLE),
                            ("OUT-OF-SAMPLE (2011-, the only verdict)", OUT_SAMPLE)]:
        print(f"\n--- {label} ---")
        for metal, month in NAMED:
            c = cell(rets[metal], month, lo, hi)
            flag = ""
            if c["p_min"] > ALPHA:
                flag = "  <<< NO RESOLUTION: this cell cannot report a positive"
            elif min(c["p_t"], c["p_sign"]) < ALPHA:
                flag = "  <<< significant after correction"
            print(f"  {metal:6} month {month:>2}: {fmt(c)}{flag}")

    print("\n" + "=" * 78)
    print("ALL 12 MONTHS -- context only, NOT tested (would be 24 comparisons)")
    for metal in ("gold", "silver"):
        for label, (lo, hi) in [("in ", IN_SAMPLE), ("out", OUT_SAMPLE)]:
            row = []
            for m in range(1, 13):
                c = cell(rets[metal], m, lo, hi)
                row.append(f"{m:>2}:{c['mean_pct']:+5.2f}")
            print(f"  {metal:6} {label} " + " ".join(row))

    print("\n" + "=" * 78)
    print("PRE-1980 (reported, in no test): regime differs, gold was pegged/just freed")
    for metal in ("gold", "silver"):
        for m in (9, 10, 11):
            c = cell(rets[metal], m, 1968, 1979)
            print(f"  {metal:6} month {m:>2}: {fmt(c)}")


if __name__ == "__main__":
    main()
