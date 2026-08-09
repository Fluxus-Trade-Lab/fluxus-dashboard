"""Aggregate per-print classified options TRADES into 2-min bars per side.

Input: enriched trades DataFrame (from pipeline.flow.enrich.enrich_trades). This module
computes premium = price*size*100 per print, classifies each print with the
Lee-Ready rule, and rolls up to 2-min bars.

For Phase 0a the "over-threshold" prints use a session-wide p95 of per-print
premium — deterministic, simple, matches the reference's threshold-square markers.
Phase 1 will replace this with a rolling EWMA quantile.
"""
import numpy as np
import pandas as pd

from pipeline.flow.quote_rule import classify

CONTRACT_MULTIPLIER = 100


def aggregate_2min(enriched: pd.DataFrame) -> pd.DataFrame:
    if enriched.empty:
        return pd.DataFrame(columns=[
            "time_bin", "premium_total", "bot_premium", "sold_premium",
            "net_premium", "n_prints", "n_prints_over_threshold", "top_prints",
        ])

    df = enriched.copy()
    df["premium"] = df["price"] * df["size"] * CONTRACT_MULTIPLIER
    df["aggressor"] = [
        classify(p, b, a, pp) for p, b, a, pp
        in zip(df["price"], df["bid"], df["ask"], df["prev_price"])
    ]
    threshold = float(np.percentile(df["premium"], 95)) if len(df) >= 10 else float("inf")
    # strict >: if all prints are the same magnitude, none of them is "extreme"
    df["is_top"] = df["premium"] > threshold
    df["time_bin"] = df["time"].dt.floor("2min")

    rows = []
    for bin_start, g in df.groupby("time_bin", sort=True):
        premium_total = float(g["premium"].sum())
        bot_premium = float(g.loc[g["aggressor"] == "BOT", "premium"].sum())
        sold_premium = float(g.loc[g["aggressor"] == "SOLD", "premium"].sum())
        tops = g.loc[g["is_top"], ["time", "premium"]].nlargest(10, "premium")
        rows.append({
            "time_bin": bin_start,
            "premium_total": premium_total,
            "bot_premium": bot_premium,
            "sold_premium": sold_premium,
            "net_premium": bot_premium - sold_premium,
            "n_prints": int(len(g)),
            "n_prints_over_threshold": int(g["is_top"].sum()),
            "top_prints": [
                {"time": t.isoformat(), "premium": float(p)}
                for t, p in zip(tops["time"], tops["premium"])
            ],
        })
    return pd.DataFrame(rows)
