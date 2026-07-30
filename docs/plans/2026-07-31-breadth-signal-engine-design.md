# Breadth Signal Engine + Decision-First UI (Spec 2 of 3)

**Date:** 2026-07-31
**Status:** Approved for planning
**Depends on:** Spec 1 (`docs/plans/2026-07-30-breadth-data-v2-design.md`), shipped to main 2026-07-30.

## Goal

Turn the breadth page from evidence-only into decision-first: a rule-derived market
verdict (full mirror — including exposure guidance, per user's explicit choice) at
the top, the two missing Stockbee working charts, SPY/QQQ health charts with
danger-signal checklists, and the existing tables/charts below as the evidence
layer. Every verdict traces to a named row in one declarative threshold table.

## Decisions log (user-approved)

- Thresholds: **Stockbee absolutes decide, our-history percentiles annotate**
- Placement: **Breadth page banner + one-line Dashboard chip**
- Charts: **full mirror** — SPY/QQQ health, 5D/10D ratio, quarterly 25% spread,
  2×5 danger checklists; existing %>MA + McClellan charts stay
- Engine: **Approach A** — Python (`pipeline/screeners/breadth_signals.py`),
  frontend renders precomputed JSON only
- Prose: EN-only templates for now (structured for later i18n)
- Purity constraint carried from Spec 1: `evaluate()` is a pure function of an
  archive prefix + market-health series — Spec 3's Time Machine replays it

## 1 · Signal engine

New module `pipeline/screeners/breadth_signals.py`.

```python
evaluate(frame: pd.DataFrame, health: dict | None) -> dict   # pure, total, no clock
market_health(spy_hist: pd.DataFrame, qqq_hist: pd.DataFrame) -> dict  # pure
percentile_context(frame: pd.DataFrame) -> dict              # pure
```

`frame` = archive prefix (last row = "today"). `health` = output of
`market_health()` truncated to the same date (None → breadth-only degraded
verdict). NaN inputs vote neutral; the engine never raises.

### THRESHOLDS table (single source of truth)

One module-level declarative dict; every UI label and vote cites a key.

| Key | Metric | Bull | Bear | Neutral / notes |
|---|---|---|---|---|
| `ratio_5d` | 5-day 4% ratio | ≥ 1.0 | < 0.5 | 0.5–1.0 mixed |
| `ratio_10d` | 10-day 4% ratio | ≥ 1.0 | < 0.5 | 0.5–1.0 mixed |
| `thrust` | 4% day counts | up ≥ 300 and up > down | down ≥ 300 and down > up | both ≥ 300 → label "churn/volatile" (votes neutral) |
| `qtr_spread` | up_25pct_qtr − down_25pct_qtr | > 0 | < 0 | 0 neutral |
| `spread_13_34` | up_13pct_34d − down_13pct_34d | > 0 | < 0 | 0 neutral |
| `mcclellan` | RANA McClellan | > 0 | < 0 | beyond ±70 adds label "extreme" |
| `nh_nl` | new_highs − new_lows | > 0 | < 0 | magnitude not used (true-extreme counts are small) |
| `pct200` | %>200SMA | ≥ 50 | < 30 | 30–50 neutral |
| `t2108_zone` | T2108 | 60–80 "strong" | 20–40 "weak" | 40–60 neutral; <20 / >80 handled by overrides |
| `spy_danger` | SPY warning count | ≤ 1 | ≥ 4 | 2–3 neutral |
| `qqq_danger` | QQQ warning count | ≤ 1 | ≥ 4 | 2–3 neutral |
| `bench_trend` | SPY & QQQ vs SMA50 | both close > sma50 | both close < sma50 | split → neutral |

### Verdict composition (ordered, deterministic)

1. Each of the 12 rules votes bull / bear / neutral (weight 1).
2. `score = bulls − bears`. Environment: `score ≥ +4` → **BULLISH**;
   `score ≤ −4` → **BEARISH**; else **MIXED**.
3. Overrides (outrank score): `t2108 < 20` → **OVERSOLD** ("reversal watch —
   look for a bullish thrust day"); `t2108 > 80` → **OVERBOUGHT** ("chase risk").
4. Derived columns:
   - `risk`: total warnings = spy_danger + qqq_danger (0–10): 0–2 **Low**,
     3–6 **Elevated**, 7–10 **High**
   - `spy_state` / `qqq_state`: danger ≤ 1 and close > sma20 → **Uptrend**;
     danger ≥ 4 or close < sma200 → **Downtrend**; else **Mixed**
   - `alignment`: states equal → **Aligned**, else **Divergent**
   - `confirmation`: both ratios ≥ 1 and both spreads > 0 → **Confirmed bull**;
     both ratios < 1 and both spreads < 0 → **Confirmed bear**; else
     **Inconclusive** (with the specific disagreement named, e.g. "5D vs 10D
     ratios disagree")
   - `exposure` (env × risk): BULLISH+Low → "Full / normal size";
     BULLISH+Elevated → "Normal, tighter stops"; MIXED → "Reduced / selective";
     BEARISH → "Defensive / capital preservation"; OVERSOLD → "Defensive but
     alert — thrust watch"; OVERBOUGHT → "No chasing; harvest into strength"
   - `playbook`: short label per env (e.g. MIXED → "Smaller size, cleaner
     setups, demand confirmation")
   - `guidance`: one templated sentence per (env, risk) pair — EN template
     table in the module, keyed for future i18n
5. `notes[]`: mechanical annotations that fired (churn day, McClellan extreme,
   ratios-disagree, stale-data).

### Percentile context

For `up_4pct`, `down_4pct`, `ratio_5d`, `t2108`, `mcclellan_osc`, `nh_nl` net,
`qtr_spread`: today's percentile rank against the **entire archive** (~552 rows,
2.2y), rounded to integer. Shipped as `verdict.context`, rendered beside labels
("637 down-4% — 96th pctile"). Backfill-vs-live bias note: percentiles lean on
reconstructed rows; acceptable, marked in Spec 1.

## 2 · Market health (SPY/QQQ danger signals)

`fetch_ma_data` (pipeline/adapters/yfinance_adapter.py) already downloads 1y
daily OHLC per ticker and discards it; it gains an option to also return the
trailing history frames for SPY and QQQ (no new network calls).

Five signals per ticker, formulas pinned:

| # | Signal | Definition (daily bars) |
|---|---|---|
| 1 | Below 20 SMA | `close < SMA20(close)` |
| 2 | Fast stoch below slow | raw %K = (C − L14)/(H14 − L14) × 100; fast = SMA3(raw %K); slow = SMA3(fast). Signal: fast < slow |
| 3 | Stochs curved down | fast_t < fast_{t−1} AND slow_t < slow_{t−1} |
| 4 | 3 consecutive lower lows | low_t < low_{t−1} < low_{t−2} < low_{t−3} |
| 5 | Close below 3 prior lows | close_t < min(low_{t−1}, low_{t−2}, low_{t−3}) |

H14/L14 use intraday High/Low. Division-by-zero (H14 == L14) → raw %K carried
forward from previous value (flat market), never NaN-propagated.

**Output: new `data/output/market_health.json`** (keeps breadth.json lean):

```
{ timestamp, stale: bool,
  spy: { candles: [{date, o, h, l, c} × 130], sma20: [130], sma50: [130],
         danger: { signals: {below_20sma, stoch_cross, stoch_down,
                             lower_lows, close_below_lows}, count },
         warn_history: [{date, count} × 130] },
  qqq: { ... } }
```

If the OHLC fetch fails: previous `market_health.json` left in place with
`stale: true`; `evaluate(frame, None)` produces a breadth-only verdict with
note "price signals unavailable".

## 3 · Pipeline wiring + breadth.json additions

In `run_all.py`, after the breadth step (inside its existing try/except):
`breadth_signals` computes `market_health` → `verdict` → `percentile_context`,
attaches to the breadth output, writes `market_health.json`.

`breadth.json` additions (additive-only, existing keys untouched):

- `verdict`: full block for the latest day — `{env, risk, exposure, spy_state,
  qqq_state, alignment, confirmation, playbook, guidance, notes[], context{}}`
- per history row: compact `v: {env, risk, warn}` (codes, no prose) — computed
  by evaluating each prefix of the shipped 100-row window (O(100 × evaluate),
  milliseconds; full-depth verdict history is Spec 3's concern)
- `data_quality` passes through unchanged; the banner renders its stale badge

## 4 · Frontend

New components in `frontend/src/components/breadth/`, existing four components
remain as the evidence layer below:

1. **VerdictBanner.jsx** — environment headline + columns (risk, exposure, SPY,
   QQQ, alignment, confirmation, playbook) + guidance sentence + stale badge.
   Colors from the anti-dopamine palette (muted, no alarm-red walls).
2. **MarketStateSummary.jsx** — four stat tiles (4% counts + thrust label,
   ratios + agreement, qtr spread + structural label, T2108 + zone), each with
   its percentile annotation; below, the prose paragraphs from
   `verdict.guidance`/`notes`.
3. **HealthChart.jsx** (×2: SPY, QQQ) — lightweight-charts candlesticks +
   SMA20/50 lines + T2108 overlay on a 0–100 right scale with dashed 20/80
   zone lines; header shows close/day%/20DMA/50DMA + state label.
4. **RatioChart.jsx** — 5D (solid) + 10D (dashed) with dashed reference at 1.0.
5. **SpreadChart.jsx** — quarterly 25% up vs down as two lines with filled
   spread (muted green/red fill by sign).
6. **DangerPanel.jsx** (×2) — five named rows, lit/unlit dots, active count
   in the header.
7. **Dashboard chip** — one line in the Dashboard's posture row:
   `BREADTH: MIXED · Reduced · ratios disagree`, links to #/breadth. Reads the
   same breadth.json already fetched by useMarketData (zero new requests).

`useMarketData.js`: add `market_health` to the fetch list (tolerant: page
renders without it).

Page order: Banner → StateSummary → SPY/QQQ health (2-up) → Ratio + Spread
(2-up) → Danger panels (2-up) → MarketMonitor → ClassicBreadth →
BreadthCharts (existing) → BreadthTable.

## 5 · Testing

- Table-driven pytest over every THRESHOLDS row (bull/bear/neutral boundary
  values, NaN → neutral)
- Stochastics vs hand-computed values on synthetic OHLC (incl. H14==L14 branch)
- Each danger signal on constructed 4-bar/20-bar fixtures
- Verdict composition goldens: clean bull day, clean bear day, oversold
  override, overbought override, churn day, ratios-disagree, health=None
  degradation
- Percentile ranks on a known small frame
- Prefix purity: `evaluate(frame[:k])` independent of later rows (replay guard)
- Frontend: no JS harness in repo — verified in-browser (dev server, console
  clean, DOM checks), per project convention

## Out of scope (Spec 3 / later)

- Time Machine date scrubber + full-depth verdict history file
- i18n of verdict prose (structure ready: keyed templates)
- Alerting/workflow failure on stale data (parked from Spec 1)
- Any change to screener/portfolio pages
