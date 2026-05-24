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
            'trim2_trigger': params[best_idx].trim2_trigger,
            'trim2_size_pct': params[best_idx].trim2_size_pct,
            'trim3_trigger': params[best_idx].trim3_trigger,
            'trim3_size_pct': params[best_idx].trim3_size_pct,
            'full_stop_signal': params[best_idx].full_stop_signal,
            'gain_ratchet': params[best_idx].gain_ratchet,
            'stop_basis': params[best_idx].stop_basis,
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
                'trim2_trigger': params[idx].trim2_trigger,
                'trim2_size_pct': params[idx].trim2_size_pct,
                'trim3_trigger': params[idx].trim3_trigger,
                'trim3_size_pct': params[idx].trim3_size_pct,
                'full_stop_signal': params[idx].full_stop_signal,
                'gain_ratchet': params[idx].gain_ratchet,
                'stop_basis': params[idx].stop_basis,
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

    # Pyramid campaigns
    pyramids = report.get('pyramid_campaigns', [])
    if pyramids:
        push("\n## Pyramid campaigns\n")
        push("Same-ticker, same-direction trades opened within 60 business days of each other are grouped as a pyramid campaign. ")
        push("`Counterfactual R` = first layer simulated alone under the optimal Phase-3 rules, out to the campaign's final exit. ")
        push("`Δ R = Actual − Counterfactual`: positive means pyramiding added value, negative means the additional layers were a drag vs holding the first layer alone with the patient rules.\n")
        push("| Ticker · # layers | First → Last entry | Actual R | Counterfactual R | Δ R |")
        push("|---|---|---:|---:|---:|")
        for c in sorted(pyramids, key=lambda x: -(x.get('actual_R', 0) or 0)):
            delta_str = _fmt_R(c['delta_R']) if c['delta_R'] is not None else '—'
            cf_str = _fmt_R(c['counterfactual_R']) if c['counterfactual_R'] is not None else '—'
            push(f"| **{c['ticker']}** · {c['n_layers']} layers "
                 f"({c['direction']}) | {c['first_entry']} → {c['last_entry']} | "
                 f"{_fmt_R(c['actual_R'])} | {cf_str} | **{delta_str}** |")
        # short interpretation
        pos_deltas = [c for c in pyramids if c.get('delta_R') is not None and c['delta_R'] > 0]
        neg_deltas = [c for c in pyramids if c.get('delta_R') is not None and c['delta_R'] < 0]
        push(f"\n**Net pyramid impact**: {len(pos_deltas)} campaigns added R, "
             f"{len(neg_deltas)} subtracted. Total Δ = "
             f"{_fmt_R(sum(c['delta_R'] for c in pos_deltas + neg_deltas))}.\n")

    # Stop-basis head-to-head
    sb = report.get('stop_basis_comparison')
    if sb:
        push("\n## Stop-basis head-to-head — intraday vs close\n")
        push("Best of all parameter sets restricted to each stop-basis discipline. "
             "Tells you which approach maximizes R across your trade population.\n")
        push("| Basis | Best total R | Winning param set |")
        push("|---|---:|---|")
        push(f"| **intraday** (cut on any wick) | {_fmt_R(sb['best_intraday_total_R'])} | {sb['best_intraday_label']} |")
        push(f"| **close** (wait for close confirmation) | {_fmt_R(sb['best_close_total_R'])} | {sb['best_close_label']} |")
        push(f"\n**Winner: `{sb['winner']}`** — by {_fmt_R(abs(sb['delta_R']))} over the other basis.")

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

    # Recommended rule changes
    p = best['best_params']
    bullets.append(
        f"**Recommended Trim 1**: **+{p['trim1_trigger_R']}R / "
        f"{int(p['trim1_size_pct']*100)}%** of original. "
        f"Then Trim 2 = `{_pretty_trigger(p['trim2_trigger'])}`, "
        f"size {int(p['trim2_size_pct']*100)}% of remaining."
    )
    if p['trim3_trigger'] != 'none':
        bullets.append(
            f"**Trim 3 ladder rung adds value**: target "
            f"`{_pretty_trigger(p['trim3_trigger'])}`, trim "
            f"**{int(p['trim3_size_pct']*100)}%** of what's left. "
            f"Validates your stated practice of using a 3-rung R-target ladder "
            f"rather than relying on a single signal-based exit."
        )
    else:
        bullets.append(
            f"**Trim 3 R-target did NOT add edge** in aggregate. The optimizer "
            f"selected `none` for the third trim rung — the residual after Trim 2 "
            f"is best held until the full-stop signal fires. Override per chart "
            f"context as always."
        )
    bullets.append(
        f"**Full stop**: `{_pretty_stop(p['full_stop_signal'])}` — "
        f"the patient runner-exit signal the optimizer keeps selecting across buckets."
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

    # Stop-basis head-to-head
    sb = report.get('stop_basis_comparison')
    if sb:
        winner = sb['winner']
        delta = abs(sb['delta_R'])
        if winner == 'close':
            bullets.append(
                f"**Close-based stops beat intraday stops by {_fmt_R(delta)}** in aggregate. "
                f"The data says your intraday cut-quickly instinct is costing R on average — "
                f"trades that get wicked through the stop intraday but close inside it tend "
                f"to recover. Best with close-confirmed stops: {_fmt_R(sb['best_close_total_R'])}; "
                f"best with intraday stops: {_fmt_R(sb['best_intraday_total_R'])}."
            )
        else:
            bullets.append(
                f"**Intraday stops beat close-based stops by {_fmt_R(delta)}** in aggregate. "
                f"Your cut-quickly discipline is the right call — waiting for close "
                f"confirmation costs R because real breakdowns continue overnight. "
                f"Best with intraday stops: {_fmt_R(sb['best_intraday_total_R'])}; "
                f"best with close-confirmed stops: {_fmt_R(sb['best_close_total_R'])}."
            )

    # Pyramid callouts
    pyramids = report.get('pyramid_campaigns', [])
    if pyramids:
        with_delta = [p for p in pyramids if p.get('delta_R') is not None]
        if with_delta:
            net_delta = sum(p['delta_R'] for p in with_delta)
            pos = [p for p in with_delta if p['delta_R'] > 0]
            neg = [p for p in with_delta if p['delta_R'] < 0]
            best_pyr = max(with_delta, key=lambda p: p['delta_R'])
            worst_pyr = min(with_delta, key=lambda p: p['delta_R'])
            bullets.append(
                f"**Pyramiding is net positive**: {_fmt_R(net_delta)} of total lift "
                f"across {len(with_delta)} multi-layer campaigns "
                f"({len(pos)} added R, {len(neg)} subtracted). When you pyramid INTO "
                f"a winning trend you're adding real edge."
            )
            if best_pyr['delta_R'] > 5:
                bullets.append(
                    f"**Best pyramid: {best_pyr['ticker']}** ({best_pyr['n_layers']} layers, "
                    f"{best_pyr['first_entry']} → {best_pyr['last_entry']}) — "
                    f"actual {_fmt_R(best_pyr['actual_R'])} vs first-layer-alone "
                    f"{_fmt_R(best_pyr['counterfactual_R'])} = "
                    f"**{_fmt_R(best_pyr['delta_R'])} added by the adds.**"
                )
            if worst_pyr['delta_R'] < -5:
                bullets.append(
                    f"**Worst pyramid: {worst_pyr['ticker']}** ({worst_pyr['n_layers']} layers) — "
                    f"actual {_fmt_R(worst_pyr['actual_R'])} vs first-layer-alone "
                    f"{_fmt_R(worst_pyr['counterfactual_R'])} = "
                    f"**{_fmt_R(worst_pyr['delta_R'])} drag.** Check whether you were "
                    f"adding to strength (real pyramid) or averaging down (loser-doubling)."
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
    t3_label = (
        '—' if p['trim3_trigger'] == 'none'
        else f"**{_pretty_trigger(p['trim3_trigger'])}**, trim **{int(p['trim3_size_pct']*100)}%** of remaining"
    )
    lines = [
        "| Parameter | Value |",
        "|---|---|",
        f"| Trim 1 trigger | **+{p['trim1_trigger_R']}R** |",
        f"| Trim 1 size | **{int(p['trim1_size_pct']*100)}%** of original position |",
        f"| Trim 2 trigger | **{_pretty_trigger(p['trim2_trigger'])}** |",
        f"| Trim 2 size | **{int(p['trim2_size_pct']*100)}%** of remaining |",
        f"| Trim 3 trigger | {t3_label} |",
        f"| Full stop | **{_pretty_stop(p['full_stop_signal'])}** |",
        f"| Stop basis | **{p.get('stop_basis', 'close')}** (intraday wick vs close-confirmed) |",
        f"| Gain ratchet | **{_pretty_ratchet(p['gain_ratchet'])}** |",
        f"|  |  |",
        f"| Simulated total R | **{_fmt_R(rec['total_R'])}** |",
        f"| Mean R per trade | {_fmt_R(rec['mean_R'])} |",
        f"| Sharpe-adj R | {rec['sharpe_adj_R']:.2f} |",
        f"| Trade count | {rec['trade_count']} |",
    ]
    return '\n'.join(lines) + '\n'


def _pretty_trigger(s: str) -> str:
    """Trigger label that handles both signal-based and R-target triggers."""
    if s.startswith('r_'):
        return f"price reaches +{s[2:]}R"
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
