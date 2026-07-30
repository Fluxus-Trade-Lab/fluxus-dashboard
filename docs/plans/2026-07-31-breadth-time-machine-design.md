# Breadth Time Machine — Point-in-Time Replay (Spec 3 of 3)

**Date:** 2026-07-31
**Status:** Approved for planning
**Depends on:** Spec 1 (canonical archive) + Spec 2 (signal engine, shipped `daa88e7`).

## Goal

Replay the entire breadth page at any historical trading date using only
information available through that date. Approach A (user-approved):
**precomputed replay file + client-side slicing** — the Python engine remains
the single source of truth; the browser recomputes nothing.

## Decisions log (user-approved)

- Whole page replays (verdict, tiles, all six charts, danger panels, table) —
  no future data visible anywhere while pinned
- Controls: slider + ◀/▶ day-step + Play (~2 days/sec, pausable) + YTD /
  Latest presets + amber "HISTORICAL SNAPSHOT · <date> · future observations
  excluded" banner
- Rejected: JS engine port (dual-engine drift), per-date server endpoints
  (no server; static Vercel)

## 1 · Pipeline — the replay file

New pure function in `pipeline/screeners/breadth_signals.py`:

```python
build_replay(frame: pd.DataFrame,
             spy_hist: pd.DataFrame | None,
             qqq_hist: pd.DataFrame | None) -> dict
```

emitted daily by the signals step in `run_all.py` as
`data/output/breadth_replay.json` (~400 KB, lazy-loaded by the frontend only
when the Time Machine is first engaged):

```
{ timestamp, dates: [all archive dates, ascending],
  rows:    { date -> full archive metric row },
  verdicts:{ date -> full verdict block incl. context } ,
  health:  { spy: { candles/sma20/sma50/sma200 over the FULL archive span,
                    signals_history: [{date, signals{5 bools}, count}] },
             qqq: {...} } }
```

- `verdicts[d]` is computed by evaluating each prefix `frame[:date d]` with
  health truncated to `d` — identical code path to the live verdict. Dates
  where health coverage hasn't started degrade to the engine's existing
  breadth-only verdict (states None, "price signals unavailable" note).
- **`signals_history`** (new, also added to `market_health.json`): per-date
  five-signal booleans + count per ticker. Closes the Spec-2 parked item
  ("truncated health has `danger.signals == {}`") — scrubbed dates get real
  per-signal dots.
- **Atomic verdict assignment** (Spec-2 parked hardening): `run_signals`
  builds verdict + row annotations fully before mutating `breadth_result`;
  a mid-computation exception leaves the payload untouched.
- Health depth: SPY/QQQ downloads move from `period='1y'` to `'3y'` in the
  `fetch_ma_data(return_history=True)` path so health/danger replay covers
  the whole archive (live `market_health.json` stays at 130 display days).

## 2 · Frontend — the scrubber

- `useTimeMachine()` hook: owns `{active, date, playing}`; lazy-fetches
  `breadth_replay.json` on first engagement; exposes `sliceToDate(date)`.
- `sliceToDate(replay, date)` — pure JS, returns **exactly the prop shapes
  the existing components consume**: `{breadth-like, market_health-like}`
  truncated to `date` (history rows/dates/charts arrays cut; verdict =
  `replay.verdicts[date]`; danger = `signals_history` entry at `date`).
  Component internals unchanged; `BreadthPage` swaps its data source when
  pinned.
- `TimeMachineBar.jsx`: date slider over `replay.dates`, ◀/▶ step, Play
  (advance 1 session per 500 ms, pause on toggle or slider grab, stop at
  Latest), YTD preset (first session of the current year), Latest preset
  (exits replay), amber pinned banner. Sits directly under the page title,
  above VerdictBanner.
- Latest/live mode is byte-identical to today's page — the feature is inert
  until touched; replay file never fetched otherwise.
- Anti-dopamine styling: existing CSS vars; amber = `--color-signal-caution`.

## 3 · Testing

- **No-peek goldens (Python):** for sampled dates (incl. first date, a
  pre-health date, the Jul-15-24 backfill window, latest), assert
  `build_replay(...)['verdicts'][d] == evaluate(frame_prefix_d, health_d)`
  computed independently; same for `signals_history` vs `danger_signals` on
  sliced hists.
- Atomic-assignment regression test: `annotate_rows` forced to raise →
  `breadth_result` has no `verdict` key.
- `sliceToDate` shape contract verified in-browser (no JS harness, per repo
  convention): scrub to 2026-07-15 (poison-window backfill day) and confirm
  banner date, that day's verdict, truncated charts, that day's danger dots;
  confirm Latest mode renders identically to the live page; console clean.

## Out of scope

- i18n of Time Machine labels (EN, keyed like Spec 2)
- Replay of non-breadth pages (dashboard chip stays live-only)
- Alerting/holiday-guard items still parked from Specs 1-2
