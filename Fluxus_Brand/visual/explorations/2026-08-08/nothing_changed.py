"""Does the state board actually stand still? — the licence for NOTHING TO REPORT.

`Fluxus_Refusals.md` rule 1 says the card may only be issued when **not one of the
nine conditions changed state**. That is a claim about the data, so it has to be
computable, and it has to be rare — a refusal that fires most days is not a
refusal, it is the weather.

Scope, stated honestly: the full ten-dimension board needs per-name ladder
positions, which only exist for one day. The nine dimensions below are the ones
derivable from `breadth_archive.csv` for **every** archived session, so this is a
lower bound on movement — the real board, having more inputs, can only change
more often, never less. If even this says "changed", the card must not go out.

    python3 nothing_changed.py            # frequency over the whole archive
    python3 nothing_changed.py 2026-07-31 # explain one date
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path("/Users/taolezhu/Documents/AI-Trading-System")
ARCHIVE = ROOT / "data/history/breadth_archive.csv"

# Thresholds mirror pipeline/screeners/breadth_signals.py where they exist there,
# so the card and the dashboard cannot tell different stories.
T2108_EDGES = [20, 40, 60, 80]
PCT200_EDGES = [30, 50]
PCT20_EDGES = [35, 50, 65]
RATIO_EDGES = [0.5, 1.0, 1.2]
THRUST_N = 300
MCCLELLAN_EXTREME = 70


def _bucket(v, edges) -> int | None:
    if v is None or pd.isna(v):
        return None
    return sum(1 for e in edges if v >= e)


def state_vector(row: pd.Series, prev5: pd.DataFrame) -> dict[str, int | None]:
    """Nine conditions, each reduced to an ordinal level. None = not measurable."""
    up4, dn4 = row.get("up_4pct"), row.get("down_4pct")
    qtr_up, qtr_dn = row.get("up_25pct_qtr"), row.get("down_25pct_qtr")
    peak_dn4 = prev5["down_4pct"].max() if len(prev5) else None

    damage = None
    if not pd.isna(qtr_up) and not pd.isna(qtr_dn) and (qtr_up + qtr_dn) > 0:
        share = qtr_dn / (qtr_up + qtr_dn)
        damage = _bucket(share, [0.35, 0.45, 0.55])

    pressure = None
    if peak_dn4 and peak_dn4 > 0 and not pd.isna(dn4):
        pressure = _bucket(dn4 / peak_dn4, [0.5, 0.8])

    thrust = None
    if not pd.isna(up4) and not pd.isna(dn4):
        thrust = 2 if (up4 >= THRUST_N and up4 > dn4) else \
                 0 if (dn4 >= THRUST_N and dn4 > up4) else 1

    nh, nl = row.get("new_highs"), row.get("new_lows")
    extremes = None if pd.isna(nh) or pd.isna(nl) else (2 if nh > nl else 0 if nl > nh else 1)

    mc = row.get("mcclellan_osc")
    mcclellan = None if pd.isna(mc) else (
        2 if mc >= MCCLELLAN_EXTREME else 0 if mc <= -MCCLELLAN_EXTREME else 1)

    return {
        "damage":       damage,
        "pressure":     pressure,
        "breadth_20":   _bucket(row.get("pct_above_20sma"), PCT20_EDGES),
        "trend_200":    _bucket(row.get("pct_above_200sma"), PCT200_EDGES),
        "t2108":        _bucket(row.get("t2108"), T2108_EDGES),
        "confirm_5d":   _bucket(row.get("ratio_5d"), RATIO_EDGES),
        "momentum_10d": _bucket(row.get("ratio_10d"), RATIO_EDGES),
        "thrust":       thrust,
        "extremes":     extremes,
        "mcclellan":    mcclellan,
    }


# A day can stay inside every bucket and still be violent: 2026-07-29 had 637
# names down 4% and came back "still" because none of the levels crossed an edge.
# Bucketing eats magnitude, so a raw-move guard has to sit beside it.
MAGNITUDE_GUARD = {
    "up_4pct":          ("rel", 0.60),   # ±60% day over day
    "down_4pct":        ("rel", 0.60),
    "pct_above_20sma":  ("abs", 5.0),    # ±5 percentage points
    "t2108":            ("abs", 5.0),
    "ratio_5d":         ("abs", 0.15),
}


def changed(a: dict, b: dict, prev_row=None, row=None) -> list[str]:
    """Dimensions whose level moved, plus any raw input that moved violently.

    A dimension that is unmeasurable on either day is not counted — absence of
    data is not an event.
    """
    out = []
    for k in a:
        if a[k] is None or b[k] is None:
            continue
        if a[k] != b[k]:
            out.append(k)
    if prev_row is None or row is None:
        return out
    for col, (kind, lim) in MAGNITUDE_GUARD.items():
        p, c = prev_row.get(col), row.get(col)
        if p is None or c is None or pd.isna(p) or pd.isna(c):
            continue
        moved = abs(c - p) / abs(p) > lim if (kind == "rel" and p) else \
                abs(c - p) > lim if kind == "abs" else False
        if moved:
            out.append(f"!{col}")
    return out


def main() -> None:
    df = pd.read_csv(ARCHIVE).sort_values("date").reset_index(drop=True)
    vecs, dates = [], []
    for i, row in df.iterrows():
        vecs.append(state_vector(row, df.iloc[max(0, i - 5):i]))
        dates.append(row["date"])

    still, moved = [], []
    for i in range(1, len(vecs)):
        d = changed(vecs[i - 1], vecs[i], df.iloc[i - 1], df.iloc[i])
        (still if not d else moved).append((dates[i], d))

    if len(sys.argv) > 1:
        want = sys.argv[1]
        j = dates.index(want)
        d = changed(vecs[j - 1], vecs[j], df.iloc[j - 1], df.iloc[j])
        print(f"{want}  vs  {dates[j-1]}")
        for k in vecs[j]:
            a, b = vecs[j - 1][k], vecs[j][k]
            flag = "  CHANGED" if (a is not None and b is not None and a != b) else ""
            print(f"  {k:14s} {str(a):>5} → {str(b):>5}{flag}")
        raw = [x[1:] for x in d if x.startswith("!")]
        if raw: print(f"  magnitude guard tripped: {', '.join(raw)}")
        print(f"\n  → {'NOTHING TO REPORT' if not d else 'card must NOT be issued'}")
        return

    n = len(still) + len(moved)
    print(f"archive        {dates[0]} → {dates[-1]}   {n} comparable sessions")
    print(f"still          {len(still):4d}   {len(still)/n*100:5.1f}%   ← NOTHING TO REPORT fires")
    print(f"moved          {len(moved):4d}   {len(moved)/n*100:5.1f}%")
    print()
    freq = pd.Series([k for _, ks in moved for k in ks]).value_counts()
    print("which dimension moves most often")
    for k, c in freq.items():
        print(f"  {k:14s} {c:4d}   {c/n*100:5.1f}% of sessions")
    print()
    print("most recent still days:", ", ".join(d for d, _ in still[-8:]) or "none")


if __name__ == "__main__":
    main()
