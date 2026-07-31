# Ticker Event Archive + Signal Timelines (Spec 1 of 2)

**Date:** 2026-07-31
**Status:** Approved for planning
**Related:** breadth v2 Specs 1-3 (`docs/plans/2026-07-3*`) established the
canonical-CSV + derived-JSON + pure-function pattern this spec reuses.

## Goal

Turn the dashboard's daily screener output into a queryable event history, so
Andy can (a) see stocks whose signals are **stacking right now**, and (b) open
any ticker and read its **signal timeline with his own fills interleaved**.

The unlock: the daily cron has committed all seven screener JSONs to git every
trading day since **2026-03-07** (88 snapshots as of 2026-07-31). Five months of
point-in-time membership already exist — mine git first, then accumulate forward.

## Decisions log (user-approved)

- Purpose: **live setup detection** + **entry audit**. Explicitly NOT
  pattern/sequence backtesting in this spec (that is the natural Spec 2).
- Scoring: **distinct screeners, quality-weighted**, over a rolling window;
  repeat hits on the same screener add little.
- Per-ticker lookup confirmed as a requirement — lands on the existing
  `#/ticker/<SYMBOL>` page, which already renders `TickerTrades`.
- Storage: canonical CSV + derived JSON, mirroring `breadth_archive.csv`.

## 1 · Data foundation

### Source shapes (verified 2026-07-31)

Seven screeners in three container styles — the extractor needs one adapter each:

| Container | Files | Path to rows |
|---|---|---|
| `tickers` (flat list) | `gainers_4pct`, `vol_up_gainers`, `episodic_pivot` | `d['tickers'][]` |
| `results` (flat list) | `vcp` | `d['results'][]` |
| nested groups | `momentum_97` (`buckets`), `healthy_charts` / `ema21_watch` (`rs_groups`) | `d[key][group][]` |

Every row carries `ticker` plus screener-specific metrics (e.g.
`change_pct, volume, sector, atr_ext` for `gainers_4pct`;
`num_contractions, max_depth, pivot, pct_to_pivot` for `vcp`).

### Canonical store

`data/history/ticker_events.csv` — one row per `(date, ticker, screener)`:

```
date, ticker, screener, group, change_pct, rel_volume, volume,
sector, atr_ext, num_contractions, pct_to_pivot
```

`group` holds the bucket/rs_group name for nested screeners, else empty.
Columns absent for a given screener are empty. Dates are US trading dates
(ET) taken from the **commit's data**, never the host clock. Sorted by
`(date, ticker, screener)`; the triple is unique.

### Backfill

`pipeline/tools/backfill_ticker_events.py` — one-time, mines git:
`git log --format='%H %ad' --date=short -- data/output/<file>.json`, then
`git show <sha>:data/output/<file>.json` per snapshot. Idempotent: re-running
over the same commits produces byte-identical rows. `--dry-run` prints row
counts per screener and per month before writing.

**Known limitation, accepted:** a screener that was empty on a given day is
indistinguishable from one that failed that day. The backfill records what the
committed file said; no interpolation.

### Daily append

`run_all` writes today's rows after the screeners finish, inside its own
try/except (a failure here must not affect any other output — the pattern the
breadth work converged on). Quality guard: reject the day's rows if **all**
seven screeners yield zero tickers (pipeline failure signature); log and skip.

## 2 · Heat scoring

`pipeline/screeners/ticker_heat.py`, pure functions:

```python
compute_heat(events: pd.DataFrame, as_of: str, window: int = 15) -> pd.DataFrame
```

- Window: trailing 15 trading sessions ending `as_of`.
- `WEIGHTS` — the single source of truth, one dict:
  - quality ×3: `episodic_pivot`, `vcp`, `momentum_97`
  - participation ×1: `gainers_4pct`, `vol_up_gainers`, `ema21_watch`, `healthy_charts`
- Score = Σ over **distinct** screeners hit of `weight`, plus
  `0.25 × weight × (hits − 1)` for repeats on the same screener — so repetition
  registers without dominating.
- Emitted per ticker: `score`, `screeners` (list, each with hit count and last
  date), `first_seen` / `last_seen` in window, `days_span` (sessions from first
  to last signal), `sector`.
- Pure and prefix-safe: `compute_heat(events, as_of)` must not read rows dated
  after `as_of` — same no-peek discipline as the breadth engine, and tested the
  same way.

## 3 · Outputs

- **`data/output/heating_up.json`** — `{timestamp, as_of, rows: [top 50 by score]}`.
  Small (~20 KB).
- **`data/output/ticker_events.json`** — `{timestamp, events: {TICKER: [{date,
  screener, group, ...metrics}]}}`, capped to the trailing 6 months to bound
  size. Lazy-loaded by the ticker page only when a ticker page is opened
  (same pattern as `breadth_replay.json`); never fetched by the dashboard.

## 4 · Frontend

- **`HeatingUp.jsx`** — new section on the Screener page: ranked table
  (ticker, score, the screeners that fired as small labelled chips, days-span,
  sector), each row linking to `#/ticker/<SYMBOL>`. A compact top-5 variant
  renders on the Dashboard beneath the existing posture row.
- **`TickerSignalHistory.jsx`** — new section on the existing ticker page,
  placed adjacent to `TickerTrades`. A reverse-chronological timeline of that
  ticker's screener appearances **interleaved with the user's fills** from
  `PortfolioContext` (already available on that page), so entries sit visually
  against the signals that preceded them. Each entry: date, screener name,
  the one or two metrics that matter for that screener; fills marked distinctly
  (BUY/SELL, size, price).
- `useTickerEvents(symbol)` hook: lazy fetch + index lookup, tolerant of a
  missing file (section simply does not render).
- Anti-dopamine palette, existing CSS vars only.

## 5 · Testing

- Extractor per container shape against fixture JSON of each style.
- Backfill reproducibility: mining a fixed set of commits twice yields
  identical rows; `--dry-run` writes nothing.
- Heat scoring: weight table boundaries, distinct-vs-repeat behavior
  (a 5×`gainers_4pct` name must rank below a `vcp` + `episodic_pivot` name),
  empty window, no-peek (rows after `as_of` ignored).
- Frontend verified in-browser (no JS harness in this repo): heating-up list
  renders and links correctly; a known ticker's timeline shows its real
  appearances interleaved with fills.

## Out of scope (Spec 2 and later)

- Sequence/pattern mining and forward-return measurement ("which signal
  sequences actually pay") — the natural follow-up once the archive exists.
- Portfolio-wide entry audit beyond the per-ticker timeline.
- Time Machine replay of the screener/portfolio pages (separate concept:
  snapshot replay vs. entity event history).
- Backfilling before 2026-03-07 (no committed data exists).
