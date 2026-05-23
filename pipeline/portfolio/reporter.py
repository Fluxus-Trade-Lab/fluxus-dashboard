"""Generate the JSON + markdown report from raw simulation results."""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np

from pipeline.portfolio.parameter_grid import params_to_label
from pipeline.portfolio.simulator import SimParams
from pipeline.portfolio.trade_parser import Trade

logger = logging.getLogger(__name__)


# ── trade tagging ──────────────────────────────────────────────────────────

def atr_bucket(atr_pct: Optional[float]) -> str:
    if atr_pct is None:
        return 'unknown'
    if atr_pct < 3:
        return '<3%'
    if atr_pct < 5:
        return '3-5%'
    if atr_pct < 7:
        return '5-7%'
    if atr_pct < 10:
        return '7-10%'
    return '10%+'


ATR_BUCKET_ORDER = ('<3%', '3-5%', '5-7%', '7-10%', '10%+', 'unknown')
HOLD_ORDER = ('tactical (1-3d)', 'core (4-8d)', 'swing (>8d)', 'unknown')
REGIME_ORDER = ('bull', 'pullback', 'unknown')


def hold_archetype(hold_business_days: Optional[int]) -> str:
    if hold_business_days is None:
        return 'unknown'
    if hold_business_days <= 3:
        return 'tactical (1-3d)'
    if hold_business_days <= 8:
        return 'core (4-8d)'
    return 'swing (>8d)'


# ── ranking ────────────────────────────────────────────────────────────────

def find_best_param(
    R_matrix: np.ndarray,
    params: list[SimParams],
    row_mask: np.ndarray,
) -> Optional[dict]:
    """Given trade × param R matrix and a row mask, return the best param dict."""
    if not row_mask.any():
        return None
    subset = R_matrix[row_mask]
    # ignore NaN rows (skipped trades) in this slice
    valid = ~np.isnan(subset).all(axis=1)
    if not valid.any():
        return None
    subset = subset[valid]
    totals = np.nansum(subset, axis=0)
    best_idx = int(np.argmax(totals))
    best_total = float(totals[best_idx])

    # Sharpe-adjusted: mean / std × sqrt(N)
    means = np.nanmean(subset, axis=0)
    stds = np.nanstd(subset, axis=0)
    n = subset.shape[0]
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(stds > 0, means / np.where(stds > 0, stds, 1), 0)
    sharpe = ratio * np.sqrt(n)

    return {
        'best_idx': best_idx,
        'best_label': params_to_label(params[best_idx]),
        'best_params': {
            'trim1_trigger_R': params[best_idx].trim1_trigger_R,
            'trim1_size_pct': params[best_idx].trim1_size_pct,
            'trim2_signal': params[best_idx].trim2_signal,
            'trim2_size_pct': params[best_idx].trim2_size_pct,
            'full_stop_signal': params[best_idx].full_stop_signal,
            'gain_ratchet': params[best_idx].gain_ratchet,
            'sell_strength': params[best_idx].sell_strength,
        },
        'total_R': best_total,
        'mean_R': float(means[best_idx]),
        'sharpe_adj_R': float(sharpe[best_idx]),
        'trade_count': int(n),
    }


def top_n_params(R_matrix: np.ndarray, params: list[SimParams], n: int = 5) -> list[dict]:
    """Top-N parameter sets by total R across ALL valid trades."""
    valid_rows = ~np.isnan(R_matrix).all(axis=1)
    if not valid_rows.any():
        return []
    subset = R_matrix[valid_rows]
    totals = np.nansum(subset, axis=0)
    top_idxs = np.argsort(-totals)[:n]
    return [
        {
            'rank': i + 1,
            'label': params_to_label(params[idx]),
            'total_R': float(totals[idx]),
            'params': {
                'trim1_trigger_R': params[idx].trim1_trigger_R,
                'trim1_size_pct': params[idx].trim1_size_pct,
                'trim2_signal': params[idx].trim2_signal,
                'trim2_size_pct': params[idx].trim2_size_pct,
                'full_stop_signal': params[idx].full_stop_signal,
                'gain_ratchet': params[idx].gain_ratchet,
                'sell_strength': params[idx].sell_strength,
            },
        }
        for i, idx in enumerate(top_idxs)
    ]


# ── markdown writer ────────────────────────────────────────────────────────

def _fmt_R(v: Optional[float]) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return '—'
    return f"{v:+.2f}R"


def write_markdown(report: dict, path: Path) -> None:
    """Render the report dict to a markdown file."""
    lines: list[str] = []
    push = lines.append

    push(f"# Portfolio Tuning Report — {report['generated_at']}\n")
    push(f"_{report['summary']['trades_total']} closed trades · "
         f"{report['summary']['multiday_count']} multi-day-trim · "
         f"{report['summary']['param_combos']:,} param sets · "
         f"{report['summary']['simulations']:,} simulations_\n")

    # ── TL;DR / Key takeaways ───────────────────────────────────────────────
    push("## TL;DR — Key takeaways\n")
    for bullet in _build_takeaways(report):
        push(f"- {bullet}")
    push("")

    # Headline
    push("## Headline\n")
    h = report['headline']
    push(f"- **Actual total R** (across {report['summary']['multiday_count']} multi-day trades): **{_fmt_R(h['actual_total_R'])}**")
    push(f"- **Best simulated total R**: **{_fmt_R(h['optimal_total_R'])}** "
         f"(lift: {h['lift_pct']:+.1f}%)")
    push(f"- Largest gap came from {h['largest_gap_reason']}\n")

    # Recommended params (overall)
    push("## Recommended parameter set — Overall\n")
    rec = report['best_overall']
    push(_param_table(rec))

    # By ATR bucket
    push("\n## By ATR bucket\n")
    push("| ATR% | # trades | Actual R | Optimal R | Best params |")
    push("|---|---:|---:|---:|---|")
    for bucket in ATR_BUCKET_ORDER:
        row = report['by_atr_bucket'].get(bucket)
        if row is None or row.get('trade_count', 0) < 1:
            continue
        push(f"| **{bucket}** | {row['trade_count']} | "
             f"{_fmt_R(row.get('actual_total_R'))} | "
             f"{_fmt_R(row.get('total_R'))} | "
             f"{row.get('best_label', '—')} |")

    # By hold archetype
    push("\n## By hold archetype\n")
    push("Tactical (1-3d) trades = positions stopped or scaled out within 3 business days. "
         "Core (4-8d) = the main two-leg system trades. Swing (>8d) = extended trend-followers.\n")
    push("| Archetype | # trades | Actual R | Optimal R | Best params |")
    push("|---|---:|---:|---:|---|")
    for arch in HOLD_ORDER:
        row = report['by_hold'].get(arch)
        if row is None or row.get('trade_count', 0) < 1:
            continue
        push(f"| **{arch}** | {row['trade_count']} | "
             f"{_fmt_R(row.get('actual_total_R'))} | "
             f"{_fmt_R(row.get('total_R'))} | "
             f"{row.get('best_label', '—')} |")

    # By market regime
    push("\n## By entry market regime\n")
    push("Bull regime = SPY closed above its 21EMA on the trade entry day. "
         "Pullback = SPY below 21EMA. Use this to gauge whether aggressive "
         "sell-into-strength rules help in strong tape vs defensive EMA-break "
         "rules help when the market is correcting.\n")
    push("| Regime | # trades | Actual R | Optimal R | Best params |")
    push("|---|---:|---:|---:|---|")
    for reg in REGIME_ORDER:
        row = report['by_regime'].get(reg)
        if row is None or row.get('trade_count', 0) < 1:
            continue
        push(f"| **{reg}** | {row['trade_count']} | "
             f"{_fmt_R(row.get('actual_total_R'))} | "
             f"{_fmt_R(row.get('total_R'))} | "
             f"{row.get('best_label', '—')} |")

    # Biggest missed-gain trades
    push("\n## Biggest missed-gain trades\n")
    push("Trades where the optimizer's exit chain produced significantly more R than the actual exit.\n")
    push("| Ticker · Entry | Actual R | Optimal R | Δ R |")
    push("|---|---:|---:|---:|")
    for t in report['missed_gains'][:15]:
        push(f"| {t['ticker']} · {t['entry_date']} | "
             f"{_fmt_R(t['actual_R'])} | {_fmt_R(t['optimal_R'])} | "
             f"**{_fmt_R(t['optimal_R'] - t['actual_R'])}** |")

    # Sensitivity
    push("\n## Sensitivity — top-5 parameter sets (by total R)\n")
    push("Tight cluster around similar rules = robust recommendation. Scattered = fragile.\n")
    for row in report['top_n']:
        push(f"{row['rank']}. {row['label']} → **{_fmt_R(row['total_R'])}**")

    push("\n---\n")
    push("_Report generated by `pipeline.portfolio.backtest_optimizer`. "
         "Re-run any time after exporting a fresh CSV into `data/portfolio/`._\n")

    path.write_text('\n'.join(lines))
    logger.info(f"Wrote markdown report to {path}")


def _build_takeaways(report: dict) -> list[str]:
    """Generate plain-English actionable bullets from the report data."""
    bullets: list[str] = []
    h = report['headline']
    best = report['best_overall']
    lift_R = h['optimal_total_R'] - h['actual_total_R']

    bullets.append(
        f"**Total opportunity**: {_fmt_R(lift_R)} of additional R was left on the table "
        f"across {best['trade_count']} multi-day-trim trades "
        f"({h['lift_pct']:+.1f}% lift over actual)."
    )

    # Rule change recommendation
    p = best['best_params']
    daily_to_weekly = 'wk_close' in p['trim2_signal'] or 'wk_close' in p['full_stop_signal']
    if daily_to_weekly:
        bullets.append(
            f"**Move from daily to weekly EMAs**: optimal trim-2 signal is "
            f"`{_pretty_sig(p['trim2_signal'])}` and full stop is "
            f"`{_pretty_stop(p['full_stop_signal'])}`. Weekly closes filter out "
            f"daily whipsaw on high-ATR momentum names."
        )

    # Trim 1 sizing change
    if p['trim1_size_pct'] <= 0.40:
        bullets.append(
            f"**Trim smaller on Trim 1**: optimal is "
            f"**{int(p['trim1_size_pct']*100)}%** at **+{p['trim1_trigger_R']}R** "
            f"(your stated default is 50%/+2-3R). Leaving more on the table for "
            f"the runner is worth more than the early lock-in."
        )

    # Per-bucket call-outs
    bull_pull = report.get('by_regime', {})
    bull = bull_pull.get('bull')
    pull = bull_pull.get('pullback')
    if pull and bull:
        bull_gap = (bull.get('total_R', 0) or 0) - (bull.get('actual_total_R', 0) or 0)
        pull_gap = (pull.get('total_R', 0) or 0) - (pull.get('actual_total_R', 0) or 0)
        if pull_gap > bull_gap * 1.5:
            bullets.append(
                f"**Pullback-regime entries are the leaky bucket**: optimizer found "
                f"{_fmt_R(pull_gap)} of lift on {pull.get('trade_count', 0)} "
                f"pullback-regime entries vs {_fmt_R(bull_gap)} on "
                f"{bull.get('trade_count', 0)} bull-regime entries. Bull entries are "
                f"already near-optimal; pullback entries need tighter stop / wider "
                f"EMA discipline."
            )

    # Tactical archetype: discretion vs rules
    by_hold = report.get('by_hold', {})
    tac = by_hold.get('tactical (1-3d)')
    if tac and tac.get('actual_total_R', 0) > (tac.get('total_R', 0) or 0):
        bullets.append(
            f"**Don't replace your tactical discretion with rules**: for "
            f"{tac.get('trade_count', 0)} tactical (1-3 day) trades you achieved "
            f"{_fmt_R(tac.get('actual_total_R'))} vs the rule-based optimizer's "
            f"{_fmt_R(tac.get('total_R'))}. Your fast-exit intuition is "
            f"outperforming any mechanical rule. Keep discretion on these."
        )

    # Swing archetype: biggest lift
    swing = by_hold.get('swing (>8d)')
    if swing:
        swing_lift = (swing.get('total_R', 0) or 0) - (swing.get('actual_total_R', 0) or 0)
        bullets.append(
            f"**Swing (>8d) trades have the biggest lift potential**: "
            f"{_fmt_R(swing_lift)} of additional R available on "
            f"{swing.get('trade_count', 0)} swing trades — the optimizer wants "
            f"weekly-EMA-based exits and a smaller Trim 1 to let trends mature."
        )

    # Single-trade callout: biggest miss
    misses = report.get('missed_gains', [])
    if misses and misses[0]['delta_R'] > 5:
        m = misses[0]
        bullets.append(
            f"**Single biggest gap: {m['ticker']} entered {m['entry_date']}** — "
            f"actual {_fmt_R(m['actual_R'])} vs optimal {_fmt_R(m['optimal_R'])} "
            f"({_fmt_R(m['delta_R'])} miss). Review the chart: this is the canonical "
            f"example of premature trim on a runner."
        )

    # Sensitivity / robustness
    top_n = report.get('top_n', [])
    if len(top_n) >= 5:
        # are top 5 sharing the same trim1 trigger / trim1 size?
        triggers = {row['params']['trim1_trigger_R'] for row in top_n[:5]}
        sizes = {row['params']['trim1_size_pct'] for row in top_n[:5]}
        if len(triggers) == 1 and len(sizes) == 1:
            bullets.append(
                f"**Result is robust**: all top-5 parameter sets agree on Trim 1 "
                f"= **+{list(triggers)[0]}R / {int(list(sizes)[0]*100)}%**. The "
                f"recommendation is not a fragile peak."
            )

    return bullets


def _param_table(rec: Optional[dict]) -> str:
    if rec is None:
        return "_No recommendation — insufficient data._\n"
    p = rec['best_params']
    lines = [
        "| Parameter | Value |",
        "|---|---|",
        f"| Trim 1 trigger | **+{p['trim1_trigger_R']}R** |",
        f"| Trim 1 size | **{int(p['trim1_size_pct']*100)}%** of original position |",
        f"| Trim 2 signal | **{_pretty_sig(p['trim2_signal'])}** |",
        f"| Trim 2 size | **{int(p['trim2_size_pct']*100)}%** of remaining |",
        f"| Full stop | **{_pretty_stop(p['full_stop_signal'])}** |",
        f"| Gain ratchet | **{_pretty_ratchet(p['gain_ratchet'])}** |",
        f"| Sell-into-strength | **{_pretty_strength(p['sell_strength'])}** |",
        f"|  |  |",
        f"| Simulated total R | **{_fmt_R(rec['total_R'])}** |",
        f"| Mean R per trade | {_fmt_R(rec['mean_R'])} |",
        f"| Sharpe-adj R | {rec['sharpe_adj_R']:.2f} |",
        f"| Trade count | {rec['trade_count']} |",
    ]
    return '\n'.join(lines) + '\n'


def _pretty_sig(s: str) -> str:
    return {
        'd_close_lt_10ema': 'daily close < 10EMA',
        'wk_close_lt_10ema': 'weekly close < 10EMA',
        'd_close_lt_13ema': 'daily close < 13EMA',
        'd_close_lt_5d_low': 'daily close < 5-day low',
    }.get(s, s)


def _pretty_stop(s: str) -> str:
    return {
        'd_close_lt_20ema': 'daily close < 20EMA',
        'wk_close_lt_20ema': 'weekly close < 20EMA',
        'd_close_lt_30ema': 'daily close < 30EMA',
        'trailing_2atr': 'trailing 2×ATR (intraday)',
    }.get(s, s)


def _pretty_ratchet(s: str) -> str:
    return {
        'none': 'none',
        '5R_to_3R': 'once close ≥ +5R, floor exit at +3R',
        '8R_to_5R': 'once close ≥ +8R, floor exit at +5R',
    }.get(s, s)


def _pretty_strength(s: str) -> str:
    return {
        'none': 'none',
        'trim_30_on_15pct': 'trim 30% on single-day close +15% from entry',
        'trim_50_on_20pct': 'trim 50% on single-day close +20% from entry',
    }.get(s, s)


def write_json(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2, default=_json_default)
    logger.info(f"Wrote JSON report to {path}")


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, np.floating):
        if np.isnan(obj):
            return None
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Not serializable: {type(obj)}")
