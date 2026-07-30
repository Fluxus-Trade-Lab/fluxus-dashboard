# Breadth Data v2 — Trustworthy Metrics + 3-Year Backfill (Spec 1 of 3)

**Date:** 2026-07-30
**Status:** Approved for planning
**Scope:** Pipeline only. No frontend changes. `breadth.json` schema is extended, never broken.

## Context

The breadth monitor (Stockbee-inspired) ships data but has correctness bugs, thin history,
and no interpretation layer. The full vision is split into three specs:

1. **This spec** — trustworthy data + backfilled history (phases A+B)
2. Signal engine + decision-first UI (phases C+D) — verdict banner, threshold labels,
   SPY/QQQ danger checklists, full exposure guidance (user explicitly chose full mirror
   of the reference screenshot, rule-derived and inspectable)
3. Time Machine point-in-time replay (phase E)

**Forward constraint honored now:** all derived series must be computable as a pure
function of `history[:date]` — no reads of "today" outside the frame — so the Spec 3
replay can reuse the same code path unchanged.

### Bugs this spec fixes

| Bug | Location | Symptom |
|---|---|---|
| A/D line not cumulative | `compute_ad_line` sums a 100-day rolling window | Becomes a rolling sum once history hits the cap (~19 trading days from now) |
| McClellan uses raw net advances | `compute_mcclellan` | Universe grew 2483→3000 over the sample; oscillator drifts with universe size, not breadth |
| Poisoned rows written silently | `run()` has no plausibility check | `2026-07-26` duplicated in CSV, one row with `pct_above_200sma=0.47` (enrichment failure) |
| NH/NL mislabeled | `_NEW_HIGH_THRESHOLD = -0.02` | "New highs" are actually "within 2% of 52w high" |
| Silent history reset | `_load_history` returns `[]` on parse error | Corruption self-heals into data loss |

### Missing Stockbee vocabulary added here

- **13% in 34 days** up/down counts (his key secondary scan)
- (Ratio charting, thresholds, and labels are Spec 2)

## Decisions log (user-approved)

- Backfill: **yes**, one-time, **marked** with a per-row `source` flag
- Depth: **3y download → ~2.2yr usable history** (needs 200 prior sessions per scored day)
- Storage: **CSV canonical, JSON derived** (Option 1 of 3 presented)
- Data source: **raw OHLC, fully independent**. TradingView used only as an optional
  ad-hoc cross-check via the local TV MCP — never in the critical path (cron runs
  headless in GitHub Actions; TV MCP needs the local desktop app; TV universes don't
  match ours; the MM scans have no TV symbol anyway)
- Interpretation depth (Spec 2, recorded now): **full mirror including exposure
  guidance**, every verdict traceable to a named threshold table

## 1 · Data model — one canonical store

`data/history/breadth_archive.csv` becomes the single source of truth:

- Full depth, one row per trading date, sorted ascending, dates unique
- **New columns:** `source` (`backfill` | `live`), `up_13pct_34d`, `down_13pct_34d`,
  `rana` (ratio-adjusted net advances, stored so McClellan is recomputable without
  re-deriving)
- Existing columns unchanged

`data/history/breadth_metrics_history.json` is **deprecated and deleted**. Its only
reader is `run_all.py:302`, which is rewired by this spec. (`breadth_history.json` at
`run_all.py:294` belongs to a different module and is untouched.)

`data/output/breadth.json` becomes a pure derived view of the CSV tail:

- `history.rows` / chart arrays: last 100 rows, now including `source`
- Top-level `mm` block gains `up_13pct_34d` / `down_13pct_34d`
- New top-level `data_quality` block (see §4)
- All existing keys keep their names and shapes — current UI renders unchanged

## 2 · Metric corrections

- **A/D line:** true cumulative sum of `net_advances` over the entire CSV from its
  first row. Base = 0 at the first (backfilled) row.
- **McClellan:** input switches from raw `A−D` to RANA `(A−D)/(A+D) × 1000`;
  oscillator = EMA19 − EMA39 over the full series. Values change scale (standard
  McClellan range, roughly ±100) — that is the fix, not a regression.
- **NH/NL:** true 52-week extremes. Live path: `high_52w >= -0.001` /
  `low_52w <= 0.001` (0.1% tolerance for float/quote noise; Finviz's 52w range
  includes today, so equality marks a new extreme). Backfill path: close vs. rolling
  252-session max/min of close, same tolerance. Counts will drop sharply
  (today's "251 new highs" becomes an honest few dozen) — expected.
- **13%/34d:** new `perf_34d` column in yfinance enrichment
  (`close / close[-35] − 1`, same pattern as `perf_1m` at
  `yfinance_adapter.py:443`), added to `universe_cols` in `run_all.py`. Snapshot
  counts at `>= 0.13` / `<= -0.13`.

## 3 · Daily flow (rewritten `run()`)

```
snapshot(universe)
  → load full CSV (fail LOUDLY if unreadable — no silent [])
  → quality guard (§4)
  → upsert today's row (idempotent; same-date replace; live wins over backfill)
  → recompute derived series over the full frame: ratio_5d/10d, ad_line, rana, mcclellan
  → write CSV atomically (temp file + rename)
  → emit breadth.json from the tail
```

Derived-series recomputation is a pure function `derive(frame) -> frame` — the
Spec 3 replay calls the same function on a truncated frame.

## 4 · Quality guard + error handling

Reject today's row if **any** of:

- `universe_size < 1500`
- `> 20%` nulls in `sma200_dist`
- `|Δ pct_above_200sma| > 25` points day-over-day

On rejection: CSV untouched; `breadth.json` rebuilt from yesterday's tail with
`data_quality: { stale: true, reason, as_of }`; pipeline logs an error but does not
crash the other screeners. On acceptance: `data_quality: { stale: false }`.

Corrupt/unreadable CSV **raises** — the current silent-reset behavior is how the
archive rotted unnoticed.

## 5 · Backfill script (one-time)

`pipeline/tools/backfill_breadth.py`:

1. Batch-download **3y** daily OHLC for the current universe tickers; cache to
   parquet in the scratch dir so re-runs are free
2. For every date with ≥ 200 prior sessions (~2.2yr usable): compute the full
   snapshot (4% movers, 25% qtr, 25%/50% month, 13%/34d, %>20/40/50/200 SMA,
   A/D, NH/NL) from that date's trailing window only
3. SPX close from `^GSPC` (3y)
4. Write rows with `source=backfill`; **merge under existing live rows** (live wins
   on date collision); dedupe the current CSV keep-last in the same pass (drops the
   poisoned 2026-07-26 row, keeps the good one; resolves the 2026-05-24 dup the same
   way, matching the JSON dedup the dashboard already showed)
5. `--dry-run` prints summary stats (row counts, date range, per-column null rates,
   min/max of each metric) without writing

**Known bias, accepted and marked:** the backfill applies today's ~3000-name universe
to historical prices — survivorship-biased, point-in-time-wrong. Reconstructed days
read slightly stronger than reality. The `source` flag exists so Spec 2 charts can
shade them and percentile logic can note the lean.

## 6 · TradingView cross-check (optional, ad-hoc)

`pipeline/tools/validate_breadth_tv.py` (or equivalent ad-hoc flow): read S5TH /
MMTH-class symbols via the **local** TV MCP, print ours-vs-theirs for %>200/50/20.
Levels will differ (different universes); **direction and turning points should
agree**. Run once after backfill, and any morning a number looks wrong. Never part
of the cron.

## 7 · Testing

- RANA McClellan vs. hand-computed values
- Cumulative A/D over a synthetic frame
- Upsert idempotency (re-run same date → one row)
- Each guard trigger independently + the stale `data_quality` output
- NH/NL threshold semantics (old 2% rows vs. new)
- Merge policy: live wins; keep-last dedupe
- `perf_34d` enrichment column
- Backfill golden test on synthetic OHLC (known counts in, known rows out)
- Existing `test_breadth_metrics.py` suite kept green (updated where semantics
  intentionally changed)

## Out of scope (later specs)

- Threshold table, labels, verdict banner, exposure guidance, prose (Spec 2)
- SPY/QQQ danger-signal checklists and health charts (Spec 2)
- 5D/10D ratio chart, quarterly 25% spread chart, UI rebuild (Spec 2)
- Time Machine replay (Spec 3)
- Any change to the four existing React components
