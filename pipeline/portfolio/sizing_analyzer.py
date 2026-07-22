"""Volatility-adjusted sizing analysis.

Looks at every CLOSED multi-day trade in the user's CSV and asks:
  - What size (% of equity) was actually put on?
  - Given the entry-day ATR%, what was the implied initial risk in R-multiples?
  - Does the user's actual sizing curve match the optimal "constant initial R"
    sizing curve (size inversely proportional to ATR)?
  - Did oversized trades earn more or less R per trade than rightsized ones?

The user's stated sizing convention:
  - ATR 5-7%: larger size (~12-15%)
  - ATR 9-10%: smaller (~8%)

The user's stated fixed R = $2,500 (0.25% of $1M equity). With a tight ≤1 ATR
stop, the implied position % to deliver exactly 1R risk would be:
    position_% = R% / ATR%
  → ATR 5%:  5% position for 1R, 15% for 3R
  → ATR 7%:  3.6% position for 1R, 10.7% for 3R
  → ATR 10%: 2.5% position for 1R, 7.5% for 3R

User's tactical leg explicitly accepts 2-3R initial risk for the burst capture.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from pipeline.marketcal import market_today

import numpy as np
import pandas as pd

from pipeline.portfolio.ohlc_cache import fetch_ohlc
from pipeline.portfolio.trade_parser import Trade

logger = logging.getLogger(__name__)

# Starting capital — used to compute position_pct
STARTING_CAPITAL = 1_000_000.0
FIXED_R_DOLLARS = 2_500.0  # 0.25% of equity per the user's profile
FIXED_R_PCT = FIXED_R_DOLLARS / STARTING_CAPITAL * 100  # 0.25


@dataclass
class TradeSizing:
    ticker: str
    entry_date: date
    direction: str
    entry_price: float
    original_qty: int
    stop_price: float
    realized_R: Optional[float]
    position_dollars: float
    position_pct: float                 # of starting capital
    entry_atr_pct: Optional[float]      # 14-day ATR / entry price
    initial_risk_R: float               # (entry - stop) × qty / FIXED_R
    # Implied "ideal" position size to deliver exactly the realized initial_risk_R
    # IF the stop had been exactly 1 ATR (lets us see if the user's stop is
    # tighter or wider than the ATR-implied stop):
    stop_distance_atr_mults: Optional[float] = None


def compute_entry_atr_pct(trade: Trade, ohlc: pd.DataFrame) -> Optional[float]:
    """14-day ATR / entry price as a percentage, on the entry day."""
    if ohlc is None or len(ohlc) < 14:
        return None
    prior = ohlc[ohlc.index <= str(trade.entry_date)]
    if len(prior) < 14:
        return None
    highs = prior['High']
    lows = prior['Low']
    closes = prior['Close']
    tr = np.maximum(
        highs - lows,
        np.maximum(
            (highs - closes.shift(1)).abs(),
            (lows - closes.shift(1)).abs(),
        ),
    )
    atr = tr.rolling(14, min_periods=1).mean().iloc[-1]
    close_at_entry = closes.iloc[-1]
    if close_at_entry <= 0:
        return None
    return float(atr / close_at_entry * 100)


def build_trade_sizings(trades: list[Trade], ohlc_by_ticker: dict) -> list[TradeSizing]:
    """For each closed trade with valid R, compute its sizing profile."""
    out: list[TradeSizing] = []
    for t in trades:
        if not t.closed:
            continue
        if t.R_dollars <= 0:
            continue
        ohlc = ohlc_by_ticker.get(t.ticker)
        atr_pct = compute_entry_atr_pct(t, ohlc)
        pos_dollars = t.entry_price * t.original_qty
        pos_pct = pos_dollars / STARTING_CAPITAL * 100
        initial_R = t.R_dollars / FIXED_R_DOLLARS
        stop_mults_atr = None
        if atr_pct and atr_pct > 0:
            # Sizing analysis uses the locked-at-entry stop — trailed stops would
            # bias the ATR-multiple distribution after the fact.
            stop_distance_pct = abs(t.entry_price - t.initial_stop) / t.entry_price * 100
            stop_mults_atr = stop_distance_pct / atr_pct
        out.append(TradeSizing(
            ticker=t.ticker,
            entry_date=t.entry_date,
            direction=t.direction,
            entry_price=t.entry_price,
            original_qty=t.original_qty,
            stop_price=t.initial_stop,
            realized_R=t.realized_R,
            position_dollars=pos_dollars,
            position_pct=pos_pct,
            entry_atr_pct=atr_pct,
            initial_risk_R=initial_R,
            stop_distance_atr_mults=stop_mults_atr,
        ))
    return out


ATR_BUCKETS = (
    ('<3%', 0, 3),
    ('3-5%', 3, 5),
    ('5-7%', 5, 7),
    ('7-10%', 7, 10),
    ('10%+', 10, 999),
)


def summarize_by_atr(sizings: list[TradeSizing]) -> list[dict]:
    """Bucket trades by ATR and compute median position %, R, etc."""
    rows = []
    for label, lo, hi in ATR_BUCKETS:
        bucket = [s for s in sizings
                  if s.entry_atr_pct is not None and lo <= s.entry_atr_pct < hi]
        if not bucket:
            continue
        pos_pcts = [s.position_pct for s in bucket]
        risk_Rs = [s.initial_risk_R for s in bucket]
        realized = [s.realized_R for s in bucket if s.realized_R is not None]
        stop_mults = [s.stop_distance_atr_mults for s in bucket if s.stop_distance_atr_mults is not None]
        # ideal position % for 1R risk (assuming 1ATR stop).
        # position_pct (percent) = R$/(stop_distance × equity) × 100
        # With stop = 1 ATR = ATR% × price / 100, and qty = R$/stop_distance:
        #   position_$ = qty × price = R$ × price / stop_distance = R$ × 100 / ATR%
        #   position_pct = position_$ / equity × 100 = R% × 100 / ATR%
        # where R% = FIXED_R_PCT (= 0.25 for $2.5k on $1M).
        mid_atr = (lo + min(hi, 12)) / 2
        ideal_pos_1R = (FIXED_R_PCT * 100 / mid_atr) if mid_atr > 0 else None
        rows.append({
            'bucket': label,
            'n_trades': len(bucket),
            'median_position_pct': float(np.median(pos_pcts)),
            'mean_position_pct': float(np.mean(pos_pcts)),
            'median_risk_R': float(np.median(risk_Rs)),
            'mean_risk_R': float(np.mean(risk_Rs)),
            'median_stop_dist_atr': float(np.median(stop_mults)) if stop_mults else None,
            'mean_realized_R': float(np.mean(realized)) if realized else 0.0,
            'median_realized_R': float(np.median(realized)) if realized else 0.0,
            'ideal_pos_pct_for_1R': float(ideal_pos_1R) if ideal_pos_1R else None,
        })
    return rows


def summarize_by_risk_R(sizings: list[TradeSizing]) -> list[dict]:
    """Bucket by initial-risk-R to see if oversized trades earn more / less."""
    R_buckets = (
        ('< 1R', 0, 1),
        ('1-2R', 1, 2),
        ('2-3R', 2, 3),
        ('3-5R', 3, 5),
        ('5R+', 5, 999),
    )
    rows = []
    for label, lo, hi in R_buckets:
        bucket = [s for s in sizings if lo <= s.initial_risk_R < hi]
        if not bucket:
            continue
        realized = [s.realized_R for s in bucket if s.realized_R is not None]
        rows.append({
            'risk_bucket': label,
            'n_trades': len(bucket),
            'mean_realized_R': float(np.mean(realized)) if realized else 0.0,
            'median_realized_R': float(np.median(realized)) if realized else 0.0,
            'win_rate_pct': float(
                100 * sum(1 for r in realized if r > 0) / len(realized)
            ) if realized else 0.0,
        })
    return rows


def find_outliers(sizings: list[TradeSizing], top_n: int = 10) -> dict:
    """Top trades by oversize (initial_risk_R) and biggest losses by oversize."""
    by_risk = sorted(sizings, key=lambda s: -s.initial_risk_R)
    top_oversized = [
        {
            'ticker': s.ticker, 'entry_date': s.entry_date.isoformat(),
            'position_pct': s.position_pct, 'atr_pct': s.entry_atr_pct,
            'initial_risk_R': s.initial_risk_R, 'realized_R': s.realized_R,
            'stop_dist_atr': s.stop_distance_atr_mults,
        }
        for s in by_risk[:top_n]
    ]
    # which oversized trades LOST money
    oversized_losses = sorted(
        [s for s in sizings if s.initial_risk_R >= 1.5 and (s.realized_R or 0) < 0],
        key=lambda s: s.realized_R or 0,
    )
    return {
        'top_oversized': top_oversized,
        'oversized_losses_count': len(oversized_losses),
        'oversized_losses_total_R': float(sum(s.realized_R for s in oversized_losses)),
        'oversized_losses_top': [
            {
                'ticker': s.ticker, 'entry_date': s.entry_date.isoformat(),
                'position_pct': s.position_pct, 'atr_pct': s.entry_atr_pct,
                'initial_risk_R': s.initial_risk_R, 'realized_R': s.realized_R,
            }
            for s in oversized_losses[:top_n]
        ],
    }


def write_sizing_report(
    sizings: list[TradeSizing], by_atr: list[dict], by_risk: list[dict],
    outliers: dict, path,
) -> None:
    """Write a standalone markdown sizing report."""
    lines: list[str] = []
    push = lines.append

    push(f"# Position-Sizing Analysis — {market_today().isoformat()}\n")
    push(f"_{len(sizings)} closed trades · ${STARTING_CAPITAL:,.0f} starting capital · "
         f"fixed R = ${FIXED_R_DOLLARS:,.0f} ({FIXED_R_PCT:.2f}% of equity)_\n")

    # ── TL;DR ──────────────────────────────────────────────────────────────
    push("## TL;DR\n")

    # Are you oversizing in aggregate?
    median_R_risk = float(np.median([s.initial_risk_R for s in sizings]))
    mean_R_risk = float(np.mean([s.initial_risk_R for s in sizings]))
    pct_above_1R = 100 * sum(1 for s in sizings if s.initial_risk_R > 1) / len(sizings)
    pct_above_2R = 100 * sum(1 for s in sizings if s.initial_risk_R > 2) / len(sizings)

    push(f"- **Median trade is sized to risk {median_R_risk:.2f}R** (mean {mean_R_risk:.2f}R) "
         f"on the initial stop. {pct_above_1R:.0f}% of trades risked >1R; "
         f"{pct_above_2R:.0f}% risked >2R. Your tactical-leg design intentionally "
         f"accepts 2-3R initial risk on burst entries.")

    # Does sizing inversely correlate with ATR?
    valid = [s for s in sizings if s.entry_atr_pct is not None]
    if valid:
        atrs = np.array([s.entry_atr_pct for s in valid])
        positions = np.array([s.position_pct for s in valid])
        corr = float(np.corrcoef(atrs, positions)[0, 1])
        if corr < -0.2:
            push(f"- **Sizing correlates inversely with ATR** (r = {corr:.2f}) — "
                 f"you do size smaller on higher-ATR names, matching your stated rule.")
        elif corr > 0.2:
            push(f"- **Sizing correlates POSITIVELY with ATR** (r = {corr:.2f}) — "
                 f"unexpected. You're trading bigger on more volatile names. Worth a look.")
        else:
            push(f"- **Sizing has weak relationship with ATR** (r = {corr:.2f}) — "
                 f"position size doesn't track volatility much. Your stated rule "
                 f"(larger size for lower-ATR) is not strongly reflected in the data.")

    # Risk-bucket performance
    if by_risk:
        best_risk_bucket = max(by_risk, key=lambda r: r['mean_realized_R'])
        worst_risk_bucket = min(by_risk, key=lambda r: r['mean_realized_R'])
        push(f"- **Best-performing risk bucket**: **{best_risk_bucket['risk_bucket']}** "
             f"(mean realized R = {best_risk_bucket['mean_realized_R']:+.2f}, "
             f"win rate {best_risk_bucket['win_rate_pct']:.0f}% on "
             f"{best_risk_bucket['n_trades']} trades).")
        if best_risk_bucket['risk_bucket'] != worst_risk_bucket['risk_bucket']:
            push(f"- **Worst-performing risk bucket**: **{worst_risk_bucket['risk_bucket']}** "
                 f"(mean realized R = {worst_risk_bucket['mean_realized_R']:+.2f} on "
                 f"{worst_risk_bucket['n_trades']} trades).")

    # Oversized losses
    if outliers.get('oversized_losses_total_R', 0) < 0:
        push(f"- **Cost of oversized losses**: "
             f"{outliers['oversized_losses_count']} trades risked >1.5R and lost — "
             f"total realized {outliers['oversized_losses_total_R']:+.2f}R. "
             f"This is the dollar cost of stretching past your R limit on losers.")

    # ── By ATR bucket ──────────────────────────────────────────────────────
    push("\n## By ATR bucket — actual sizing vs ideal for 1R risk\n")
    push("`Median position %` = the size you actually trade. ")
    push("`Ideal pos % for 1R` = the size that would deliver exactly 1R risk if your stop is 1 ATR away. ")
    push("Anything well above ideal means you're running tactical-leg oversized; below means under-leveraged.\n")
    push("| ATR bucket | # trades | Median pos % | Ideal pos % (1R) | Median stop dist (ATR) | Median initial risk (R) | Median realized R |")
    push("|---|---:|---:|---:|---:|---:|---:|")
    for row in by_atr:
        ideal = f"{row['ideal_pos_pct_for_1R']:.2f}%" if row['ideal_pos_pct_for_1R'] else '—'
        stop_mult = f"{row['median_stop_dist_atr']:.2f}×" if row['median_stop_dist_atr'] else '—'
        push(f"| **{row['bucket']}** | {row['n_trades']} | "
             f"{row['median_position_pct']:.2f}% | {ideal} | {stop_mult} | "
             f"{row['median_risk_R']:.2f}R | "
             f"{row['median_realized_R']:+.2f}R |")

    # ── By initial-risk bucket ─────────────────────────────────────────────
    push("\n## By initial-risk bucket — do oversized trades earn more?\n")
    push("Sort trades by how much R was at risk on the initial stop. ")
    push("If mean realized R rises with risk, oversizing is paying off. If it plateaus or falls, "
         "extra risk is unrewarded.\n")
    push("| Initial risk | # trades | Win rate | Mean realized R | Median realized R |")
    push("|---|---:|---:|---:|---:|")
    for row in by_risk:
        push(f"| **{row['risk_bucket']}** | {row['n_trades']} | "
             f"{row['win_rate_pct']:.0f}% | "
             f"{row['mean_realized_R']:+.2f}R | "
             f"{row['median_realized_R']:+.2f}R |")

    # ── Top oversized trades ───────────────────────────────────────────────
    push("\n## Top 10 oversized trades (by initial-risk R)\n")
    push("Trades that risked the most R on the initial stop. Check whether the size was justified.\n")
    push("| Ticker · Entry | Position % | ATR% | Stop dist (ATR) | Initial risk R | Realized R |")
    push("|---|---:|---:|---:|---:|---:|")
    for t in outliers['top_oversized']:
        atr_str = f"{t['atr_pct']:.1f}%" if t['atr_pct'] is not None else '—'
        stop_str = f"{t['stop_dist_atr']:.2f}×" if t['stop_dist_atr'] is not None else '—'
        rr_str = f"{t['realized_R']:+.2f}R" if t['realized_R'] is not None else '—'
        push(f"| {t['ticker']} · {t['entry_date']} | "
             f"{t['position_pct']:.2f}% | {atr_str} | {stop_str} | "
             f"{t['initial_risk_R']:.2f}R | {rr_str} |")

    if outliers.get('oversized_losses_top'):
        push("\n## Biggest losses on oversized trades\n")
        push("Trades that risked >1.5R AND lost money. The closest data we have to "
             "'what did oversizing cost me?'\n")
        push("| Ticker · Entry | Position % | ATR% | Initial risk R | Realized R |")
        push("|---|---:|---:|---:|---:|")
        for t in outliers['oversized_losses_top']:
            atr_str = f"{t['atr_pct']:.1f}%" if t['atr_pct'] is not None else '—'
            push(f"| {t['ticker']} · {t['entry_date']} | "
                 f"{t['position_pct']:.2f}% | {atr_str} | "
                 f"{t['initial_risk_R']:.2f}R | "
                 f"{t['realized_R']:+.2f}R |")

    # ── Recommended sizing curve ───────────────────────────────────────────
    push("\n## Recommended sizing curve\n")
    push("Given your fixed R = $2,500 (0.25% of $1M), a tight ≤1 ATR stop, and the "
         "tactical-leg goal of 2-3R initial risk on burst entries, here's the size "
         "to put on for each ATR bucket. Adjust ±1% for context.\n")
    push("| ATR% | For 1R risk | For 2R (tactical low) | For 3R (tactical high) |")
    push("|---|---:|---:|---:|")
    for atr_mid, label in [(4, '3-5%'), (6, '5-7%'), (8.5, '7-10%'), (11, '10%+')]:
        s1 = FIXED_R_PCT * 100 / atr_mid
        s2 = 2 * FIXED_R_PCT * 100 / atr_mid
        s3 = 3 * FIXED_R_PCT * 100 / atr_mid
        push(f"| **{label}** | {s1:.1f}% | {s2:.1f}% | {s3:.1f}% |")

    push("\n_Rule of thumb_: **position % ≈ (target_R × 0.25%) × 100 / ATR%**. "
         "E.g., ATR 7% × 3R target → position ≈ 10.7%. ATR 10% × 2R target → position ≈ 5%.\n")

    path.write_text('\n'.join(lines))
    logger.info(f"Wrote sizing report to {path}")
