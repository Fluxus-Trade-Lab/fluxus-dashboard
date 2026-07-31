# Sequence Mining — Which Signal Sequences Actually Pay (Spec 2 of 2)

**Date:** 2026-08-01
**Status:** Approved for planning
**Depends on:** the ticker event archive (`docs/plans/2026-07-31-ticker-events-design.md`), shipped `800d5f4`.

## Goal

Measure whether ordered screener sequences ("Episodic Pivot, then a 4% day
within 10 sessions") lead anywhere, using the point-in-time event archive plus
forward price data. The deliverable is a ranked report of numbers with their
uncertainty attached — not a recommendation and not a dashboard page.

## Decisions log (user-approved)

- Outcome measure: **MFE/MAE in ATR-multiples (R) at 5/10/21 sessions, plus
  forward return vs SPY**
- Candidate selection: **enumerate all ordered pairs and triples**, rank by
  measured edge, with n and a baseline on every row
- Deliverable: **CLI report**, no UI in this spec

## Context and honest limits

Stated up front because they bound every number this produces:

- **Sample depth:** the archive covers 2026-03-09 → 2026-07-30, 89 sessions,
  3,872 tickers, 57,553 events — 347 Episodic Pivot and 420 VCP first-
  occurrences. A given pair may yield 50–150 instances. Suggestive, not proof.
- **One regime.** Five months of a single market environment. A sequence that
  works here may simply be describing that regime.
- **Multiple comparisons.** ~49 pairs and several hundred triples means some
  will look excellent by chance. The three guards in §3 exist for this.
- **Survivorship.** Price data is fetched today, so delisted/renamed tickers
  fail to download — and failures skew toward losers. Coverage loss is
  reported per sequence, never silently dropped.
- **17 archive dates are missing by design** (non-session + poisoned days, see
  the ticker-events spec). Sequence windows are measured in *archive sessions*,
  so a gap shortens elapsed calendar time; the report states the calendar span
  of each window alongside the session count.

## 1 · Price panel

New `pipeline/tools/build_price_panel.py` (one-time, re-runnable):

- Tickers = the distinct set in `data/history/ticker_events.csv`, plus `SPY`.
- Download daily OHLC covering the archive range with **60 sessions of lead-in**
  (ATR(14) warm-up plus slack) and **25 sessions of tail** beyond the last
  archive date (the 21-session horizon needs forward bars).
- Cache to `data/history/price_panel.pkl` (pickle, not parquet — no parquet
  engine on this host); `--refresh` forces re-download. Add to `.gitignore`.
- Emits a coverage summary: tickers requested / returned / missing, and the
  missing list written to `data/research/price_coverage.json`.

## 2 · Outcome measurement

New `pipeline/research/outcomes.py`, pure functions:

```python
atr(high, low, close, period=14) -> pd.Series          # Wilder ATR
measure_outcome(bars: pd.DataFrame, spy: pd.DataFrame, signal_date: str,
                horizons=(5, 10, 21)) -> dict | None
```

`bars` = one ticker's OHLC (DatetimeIndex ascending). Returns `None` when the
signal date is absent, ATR is undefined, or fewer than `max(horizons)` forward
bars exist (these become reported coverage loss, not silent drops).

Per horizon `h`, measured from the **next session's open** after `signal_date`
(the earliest realistically actionable price):

- `ret_h` — close at +h vs entry open
- `excess_h` — `ret_h` minus SPY's same-window return
- `mfe_r_h` — `(max high over the h bars − entry_open) / atr_at_signal`
- `mae_r_h` — `(min low over the h bars − entry_open) / atr_at_signal` (≤ 0)

R is ATR(14) as of `signal_date`, so every excursion reads directly in the
units the user's stop/target framework consumes.

## 3 · Sequence enumeration and statistics

New `pipeline/research/sequences.py`, pure functions:

```python
find_pair_instances(events, a, b, window=10) -> list[dict]
find_triple_instances(events, a, b, c, window=10) -> list[dict]
summarize(instances_with_outcomes, min_n=20) -> dict
random_baseline(events, panel, n_draws, seed) -> dict
```

An instance of `A → B`: a ticker with screener `A` on archive session `d1` and
`B` on `d2`, where `0 < index(d2) − index(d1) ≤ window` in **archive-session
index** (not calendar days). Outcomes are measured from **`d2`** — the
confirmation is when a trade would be taken. Per ticker, the *first* qualifying
`d2` after each `d1` counts once; overlapping restatements of the same setup
are not double-counted.

Triples extend the same rule: `A → B → C`, each leg within `window`.

`summarize` reports per sequence: `n`, median and mean of `excess_h`,
`mfe_r_h`, `mae_r_h` for each horizon, win rate (`excess_h > 0`), and the
count of instances lost to missing price data.

**Three guards against manufactured winners:**

1. **Random-entry baseline** — for each sequence, draw `n` random
   `(ticker, date)` pairs from the same ticker pool and archive date range,
   measure identically, and report every statistic as *sequence minus
   baseline*. A sequence must beat random entry into the same universe, not
   beat zero.
2. **Split-sample** — the archive window is split at its midpoint; every
   sequence is scored independently in each half and both are shown. A
   sequence strong in one half and absent in the other is flagged
   `unstable`.
3. **`min_n` floor (default 20)** — sequences below it appear in the report
   marked `under-powered` and are excluded from the ranking.

Ranking key: median `excess_10` minus baseline, restricted to sequences that
are neither under-powered nor unstable.

## 4 · CLI and output

```
python3 -m pipeline.research.mine_sequences [--window 10] [--min-n 20]
                                            [--horizons 5,10,21] [--seed 42]
```

Writes `data/research/sequences_<as_of>.md` (ranked human-readable report) and
`data/research/sequences_<as_of>.csv` (same data, machine-readable). The
markdown report leads with the limits from "Context and honest limits" above,
then the ranked table, then the under-powered and unstable sections.

No dashboard page, no `data/output/` JSON — the deliverable is a report the
user reads and judges. Wiring a proven sequence into the Heating Up list is a
separate, small follow-up.

## 5 · Testing

- `atr` against hand-computed Wilder values on a fixed 20-bar fixture.
- `measure_outcome` on a constructed bar set with known highs/lows: verify
  `mfe_r`/`mae_r`/`excess` exactly; verify `None` on missing date, insufficient
  forward bars, and undefined ATR.
- `find_pair_instances` on a synthetic event frame with planted sequences:
  correct instances found; window boundary (exactly `window` = included,
  `window+1` = excluded); same-day `A` and `B` excluded (requires `d2 > d1`);
  first-qualifying-`d2`-only (no double counting).
- `find_triple_instances` ordering and per-leg window.
- `summarize` arithmetic on known inputs; `min_n` flagging.
- `random_baseline` null property: baseline measured against itself yields
  ≈ zero edge (fixed seed, tolerance stated in the test).
- Reproducibility: the same `--seed` yields an identical report.

## Out of scope

- Any dashboard/UI surface for sequences.
- Trade simulation with stops and targets (this measures the signal, not a
  strategy).
- Sequences longer than three legs.
- Re-running or altering the ticker event archive.
