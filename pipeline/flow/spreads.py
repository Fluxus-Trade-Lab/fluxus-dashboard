"""Detect vertical-spread legs in classified option flow.

A vertical spread shows up as two prints arriving at the same millisecond
(or within a short lag), with the same size, on different strikes of the
same option type (calls or puts), with opposite aggressor labels (one BOT,
one SOLD). Netting the hedging leg reduces noise in flow analytics.

Usage:
    pairs, singles = detect_spreads(prints, max_lag_ms=500)
"""
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class ClassifiedPrint:
    timestamp: pd.Timestamp
    strike: float
    right: str       # "C" or "P"
    size: int
    premium: float
    aggressor: str   # "BOT", "SOLD", "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SpreadPair:
    buy_leg: ClassifiedPrint
    sell_leg: ClassifiedPrint
    net_premium: float
    strike_gap: float


def detect_spreads(
    prints: list[ClassifiedPrint],
    max_lag_ms: int = 500,
    max_strike_gap: int = 3,
    strike_spacing: float = 5.0,
) -> tuple[list[SpreadPair], list[ClassifiedPrint]]:
    """Match vertical-spread legs from a list of classified prints.

    Returns (pairs, singles) where pairs are matched spread legs and
    singles are unmatched prints (directional flow).
    """
    if len(prints) < 2:
        return [], list(prints)

    max_delta = pd.Timedelta(milliseconds=max_lag_ms)
    max_gap = max_strike_gap * strike_spacing
    used = set()
    pairs = []

    by_time = sorted(range(len(prints)), key=lambda i: prints[i].timestamp)

    for idx_i, i in enumerate(by_time):
        if i in used:
            continue
        p1 = prints[i]
        if p1.aggressor == "UNKNOWN":
            continue

        for j in by_time[idx_i + 1:]:
            if j in used:
                continue
            p2 = prints[j]
            if p2.timestamp - p1.timestamp > max_delta:
                break
            if p2.aggressor == "UNKNOWN":
                continue
            if p2.right != p1.right:
                continue
            if p2.size != p1.size:
                continue
            if p2.aggressor == p1.aggressor:
                continue
            gap = abs(p2.strike - p1.strike)
            if gap == 0 or gap > max_gap:
                continue

            if p1.aggressor == "BOT":
                buy, sell = p1, p2
            else:
                buy, sell = p2, p1

            pairs.append(SpreadPair(
                buy_leg=buy,
                sell_leg=sell,
                net_premium=buy.premium - sell.premium,
                strike_gap=gap,
            ))
            used.add(i)
            used.add(j)
            break

    singles = [prints[i] for i in range(len(prints)) if i not in used]
    return pairs, singles


def net_spread_premium(
    pairs: list[SpreadPair],
    singles: list[ClassifiedPrint],
) -> dict:
    """Compute netted premium totals after spread detection."""
    bot_premium = 0.0
    sold_premium = 0.0
    spread_premium = 0.0

    for sp in pairs:
        spread_premium += abs(sp.net_premium)

    for p in singles:
        if p.aggressor == "BOT":
            bot_premium += p.premium
        elif p.aggressor == "SOLD":
            sold_premium += p.premium

    return {
        "bot_premium": bot_premium,
        "sold_premium": sold_premium,
        "spread_premium": spread_premium,
        "n_spreads": len(pairs),
        "n_singles": len(singles),
    }
