# Portfolio Tuning Optimizer — Design

**Date:** 2026-05-24
**Status:** Draft for review
**Phase:** 3 of 3 (standalone analyzer; Phases 1–2 will wire findings into UI later)

## Problem

The user runs a two-leg swing system on high-beta momentum stocks (ATR mostly 5–10%). The default playbook — Trim 1 at +2R/+3R, BE stop, 10EMA-trim-trigger, 20EMA full stop — was calibrated by intuition, not by data. The user has 248 closed trades from 2026-01 to 2026-05 sitting in a CSV. We can re-simulate every trade under thousands of parameter variations and report which combination would have actually maximized realized R. Optimal parameters likely differ by ATR bucket and by hold-duration archetype (tactical 1–3 day vs core 4+ day), so the report bucketizes by both.

The output of this phase is a one-shot analysis: a Python script + JSON + markdown report. No UI changes yet. Phases 1 and 2 (live trailing-stop UI, Capital-at-Risk widget) will consume the parameter recommendations later.

## Inputs

1. **Trade history CSV** — the user's portfolio export. Designated folder: `data/portfolio/`. The CLI auto-detects the most recent `portfolio_*.csv` in that folder unless `--input <path>` is passed explicitly. CSV schema (header on row 3, meta rows above):
   - `Ticker, Direction, Sector, Entry Date, Entry Price, Original Qty, Current Qty, Stop Price, Closed, Trim1 Date, Trim1 Price, Trim1 Qty, Trim1 Type, Trim2 Date, Trim2 Price, Trim2 Qty, Trim2 Type, Trim3 Date, Trim3 Price, Trim3 Qty, Trim3 Type`
   - Trim Type vocabulary: `trim_1_2` = ½ of original, `trim_1_3` = ⅓, `trim_1_5` = ⅕, `sell_rest` = exit residual.
2. **Daily OHLC per ticker** — fetched from yfinance, range `entry_date − 60d` → `exit_date + 30d`. Cached to disk so re-runs are fast.

## Outputs

1. `data/output/portfolio_backtest.json` — machine-readable ranked parameter sets, per-bucket recommendations, per-trade simulation results. Schema versioned with `_schema: "v1"`.
2. `docs/portfolio-tuning-YYYY-MM-DD.md` — human-readable markdown report. Sections:
   - **Headline** — actual total R vs simulated optimal total R, lift %
   - **Recommended params overall** — best-by-total-R combo with deltas vs user's stated defaults
   - **By ATR bucket** — table with `<3% · 3-5% · 5-7% · 7-10% · 10%+` rows; user's primary bucket (5-7%, 7-10%) is highlighted
   - **By hold-duration archetype** — tactical (1-3 day actual hold) vs core (4+ day) with separate recommended params
   - **By market regime** — separate recommended params for `bull-regime entries` vs `pullback-regime entries`. This is where the sell-into-strength dimension shines: optimizer should reveal whether aggressive single-day-strength trims help in bull regimes and EMA-break weakness trims help in pullback regimes.
   - **Biggest missed-gain trades** — top-N trades by `(optimal_R − actual_R)` with a one-line explanation of what the optimizer would have done differently
   - **Sensitivity / top-5 param sets** — tight cluster vs scattered tells us whether the result is robust or fragile
3. No frontend changes.

## Trade classification

Each trade is tagged with three attributes used by the report:

- **ATR bucket** — `<3%`, `3-5%`, `5-7%`, `7-10%`, `10%+`, computed from the 14-day ATR / entry price on entry day.
- **Hold archetype** — `tactical` if `(actual_exit_date − entry_date).business_days <= 3`, `core` if `4-8 days`, `swing` if `>8 days`. The 3-day boundary is the user's stated working assumption ("usually 3-5 days"); the analyzer reports sensitivity to this boundary by also computing the segmentation at the 4-day and 5-day cutoffs and showing how recommended params shift. Final report uses the 3-day cutoff as primary view with a footnote on alternatives.
- **Entry market regime** — `bull` if SPY closes above its 21EMA on the entry day, `pullback` otherwise. Lets the report recommend different rules for bull vs pullback entries.

Trades are also classified by exit pattern (used internally, surfaced only in the JSON):

- **scale-out stop** — all trims fall on a single date. These were tight-stop exits executed in tranches; the trim/trail rules being optimized don't really apply, so they're excluded from the headline lift computation but kept in the per-trade table.
- **two-leg progression** — trims span ≥2 distinct dates. These are the trades where the optimization actually matters; they drive the headline number.

## Parameter sweep (v2 — R-target ladder)

User feedback after v1 run: switching to weekly-EMA-based exits is psychologically hard
because it requires sitting through deep mid-trend pullbacks on large positions.
User's preferred operating mode is an **R-target ladder** — predefined +R-level
trim targets layered on top of (or as alternative to) the signal-based exit. v2
sweeps this directly.

Sell-into-strength was dropped — v1 results showed `none` was selected as optimal
in every bucket. Keeping the dimension only adds noise.

| Parameter | Values |
|---|---|
| Trim 1 trigger | `+2R, +2.5R, +3R, +3.5R, +4R` |
| Trim 1 size | `30%, 40%, 50%, 60%, 70%` of original position |
| Trim 2 trigger | **`daily_close < 10EMA` · `weekly_close < 10EMA` · `daily_close < 5-day low` · `+5R reached` · `+6R reached` · `+8R reached`** |
| Trim 2 size | `30%, 50%, 70%` of remaining (after Trim 1) |
| Trim 3 trigger | **`none` · `+8R reached` · `+10R reached` · `+12R reached`** (R-target only) |
| Trim 3 size | **`50%, 100%`** of remaining (after Trim 2) |
| Full stop | `daily_close < 20EMA` · `weekly_close < 20EMA` · `daily_close < 30EMA` · `trailing 2×ATR` |
| Gain ratchet | `none` · `≥+5R close → floor at +3R` · `≥+8R close → floor at +5R` |

Total grid: 5 × 5 × 6 × 3 × 4 × 2 × 4 × 3 = **86,400 combinations**. Per-trade
vectorized loop; ~3 min full run on 46 multi-day trades.

*R-target trigger semantics (Trim 2 / Trim 3): fires the first day price closes
at or above `entry + R_multiple × R/qty` for longs (inverted for shorts).
Execution at the close of that day. If both an R-target and a signal trigger
fire on the same bar, the R-target wins (acts first).*

*Ratchet semantics: trigger fires the first day the position closes at or above
the upper level (+5R or +8R); from then on, if any subsequent daily close falls
below the floor (+3R or +5R), the residual exits at the next-day open. Triggers
on close, not intraday high — avoids whipsawing on a single spike.*

Pre-trim phase always uses the user's existing stop from the CSV. The grid only optimizes post-T1 behavior — that's where the actual decisions are.

## Simulation engine

Per (trade × params) pair, the engine:

1. Loads daily OHLC for the ticker, entry-day → exit-day + 30d buffer (so we can let the simulation run past the user's actual exit if optimal rules would have held longer).
2. Computes 5/10/13/20/30 EMA on daily bars, 10/20 EMA on weekly bars, 14-day ATR, 5-day rolling low.
3. Walks bars chronologically from entry+1. State machine: `PRE_TRIM → POST_T1 → POST_T2 → CLOSED`.
   - **PRE_TRIM**: if `high ≥ entry + (trim1_trigger × R/qty)`, execute Trim 1 at that level, transition to `POST_T1`, move stop to breakeven. If `low ≤ stop` (user's original CSV stop), exit full position at stop and finish.
   - **POST_T1**: if Trim-2 signal fires (e.g., daily close < 10EMA), execute Trim 2 at next-day open and transition to `POST_T2`. If full-stop signal fires, exit residual at next-day open. If gain-ratchet ceiling is hit and then crossed back down, exit at that crossing.
   - **POST_T2**: same exits as POST_T1 (no further trims; just trail until stopped).
4. Returns total realized R for the (trade × params) combination. Direction is honored — shorts use inverted price logic.

Edge cases:

- Trade with no stop in CSV → skip; logged in the report's appendix.
- Short trade → flip every directional comparison.
- Simulated exit would run past available OHLC → close at last available close.
- Trade still open in CSV → skip from the optimization population; included in "open positions" summary.
- Same-day scale-out trade → simulator still runs, but the trade is flagged as `scale-out-stop` and excluded from headline lift.

## Objective functions

Reported in this priority order, but the user can pick:

1. **Total realized R** — primary headline. Sum across all qualifying trades.
2. **Sharpe-adjusted R** — `mean_R / std_R × sqrt(N)`. Penalizes parameter sets that get high total R only by carrying a few huge winners.
3. **Max-drawdown-constrained R** — total R subject to simulated equity-curve max drawdown ≤ 25% (user's stated DD ceiling).

Top-5 ranked tables shown for each. The recommended set is the one that is in the top-10 for all three.

## Module layout

```
data/portfolio/
└── portfolio_YYYY-MM-DD.csv    # designated location for all CSV exports

pipeline/portfolio/
├── __init__.py
├── backtest_optimizer.py        # CLI entry point
├── trade_parser.py              # CSV → typed Trade dataclasses
├── ohlc_cache.py                # cached yfinance fetcher (parquet on disk)
├── market_regime.py             # SPY 21EMA bull/pullback classifier
├── simulator.py                 # single-trade simulation engine
├── parameter_grid.py            # parameter sweep definition + iteration
├── reporter.py                  # JSON + markdown emitters
└── tests/
    ├── test_trade_parser.py     # CSV parsing
    ├── test_simulator.py        # known-trade × known-params → expected R
    └── fixtures/
        └── sample_trades.csv    # small CSV fixture for tests
```

CLI:

```bash
python -m pipeline.portfolio.backtest_optimizer
```

Default behavior: auto-detects the most recent `data/portfolio/portfolio_*.csv`, generates a date-stamped report at `docs/portfolio-tuning-YYYY-MM-DD.md`, writes JSON to `data/output/portfolio_backtest.json`. Override with `--input`, `--output`, `--json` flags.

## Performance

- 248 trades × 3,600 param combos = ~893k simulations.
- Each simulation walks ~30-60 daily bars with O(1) checks per bar.
- Target: full run under 5 minutes on user's local machine.
- Strategy: vectorize the parameter grid per trade (numpy broadcasting — compute all 3,600 param outcomes for a single trade in one vectorized pass). If still slow, parallelize across trades with `multiprocessing.Pool`.
- yfinance fetches are cached as parquet at `.cache/ohlc/{ticker}.parquet`. First run downloads; subsequent runs are local-only.

## Error handling

- Bad CSV row → log warning with row number, skip that trade.
- yfinance fetch fails for a ticker → log warning, skip those trades, report skipped count in headline.
- Cache parquet corrupt → delete and re-fetch.
- Empty trade population after filtering → exit with clear error message.

## Testing

- **Unit:** trade parser handles all observed `trim_*` types, multiple trims same date, missing trims (only Trim 1), open trades, shorts.
- **Unit:** simulator on a hand-constructed trade with synthetic OHLC produces the expected R for each state-machine transition.
- **Integration:** end-to-end run on a 6-trade fixture CSV produces a deterministic report (snapshot test).

## Pyramid campaign analysis (v2 addition)

The user pyramids — adds to existing winners with a new trade record at a higher
price (example: DOCN entered $82.70 in April, added $155.89 in May). In the CSV
these are independent trade records. The optimizer simulates each independently.

Treating them as separate trades is technically correct but misses the campaign
view. A separate `pyramid_analyzer.py` module:

1. **Detects pyramid campaigns** — same ticker, same direction, entries within 60
   business days of each other, at least one prior entry still open when the new
   one is added.
2. **Computes campaign-level R** — total realized P/L across all layers divided
   by the *first layer's* R amount (so we measure "how much R did the campaign
   capture relative to the original risk decision").
3. **Counterfactual: "what if no pyramid?"** — for each campaign, compute the R
   that would have been captured if only the first layer had been held under the
   optimal Phase-3 rules. Pyramid adds value if `campaign_R > counterfactual_R`.
4. **Reports per-campaign delta** — surfaces which pyramid decisions actually
   added R vs which were noise / drag.

The optimizer itself does NOT include a "pyramid rule" parameter — that would
double-count user behavior already present as separate trade records. Pyramid
rules become a Phase 1 UI concern (campaign grouping, aggregate stop suggestion,
add-back signal alerts).

## What this does NOT include (deferred to Phases 1 & 2)

- Live trailing-stop UI in the Portfolio Tracker
- Per-position EMA reference data display
- Capital-at-Risk widget on Exposure tab
- Stop-suggestion engine
- Persistence of the recommended params anywhere in the app

These are sequenced after Phase 3 because Phase 3's output dictates what defaults Phases 1–2 should hard-code.

## Open questions to confirm with user

None blocking. Defaults chosen above are sensible; the user can flag changes in spec review.
