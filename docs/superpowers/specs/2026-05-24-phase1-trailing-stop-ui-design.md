# Phase 1 — Live Trailing-Stop / Leg-State UI Design

**Date:** 2026-05-24
**Status:** Draft (author wrote autonomously while user was out — needs user review/approval before plan)
**Depends on:** Phase 3 optimizer findings (already shipped in `pipeline/portfolio/`)
**Sequence:** Phase 1 (this) → Phase 2 (Capital-at-Risk widget in Exposure slot)

## Problem

The Portfolio Tracker today has a single editable `Stop` column per trade. It doesn't:

- Know what leg state a position is in (PRE_TRIM / POST_T1 / POST_T2 / POST_T3 / CLOSED) — and therefore can't apply leg-appropriate trailing logic
- Show the per-ticker EMA reference levels (10EMA, 20EMA, weekly EMAs) that the Phase 3 findings say drive optimal exits
- Suggest trim targets (the +4R and +8R rungs the optimizer validated)
- Group multi-entry same-ticker trades as a single campaign (the pyramid problem)
- Surface "stop health" — is the current stop tight enough? too tight? close to a key EMA?

User has explicitly asked for a place to record trailing stops AND get suggestions. Phase 3 results dictate the suggested defaults.

## Scope

This phase ships UI/UX changes plus the pipeline data needed to feed them. It does NOT ship the Capital-at-Risk widget (that's Phase 2, which reads the live stop set by Phase 1).

In scope:
1. Per-position **leg state** (auto-derived from `trims[]`), shown as a badge in the Tracker row
2. **Initial stop** vs **current trail stop** as separate concepts (UI distinguishes them)
3. **Per-ticker EMA reference data** plumbed from the pipeline into `universe.json`: `ema10`, `ema20`, `wk_ema10`, `wk_ema20`, plus `bo_count_*` (already exist)
4. **Stop suggestion engine** — given leg state + EMA levels + entry/stop, computes a recommended trail stop and shows it next to the editable Stop field
5. **Trim target hints** inline per row — `+4R = $X · +8R = $Y` strike-through once hit
6. **EMA proximity alerts** — chip when price is within X% of 10EMA or 20EMA
7. **Campaign grouping** in the Exposure tab Detail table — same-ticker open trades grouped under a "campaign" parent row with aggregate cost basis, total R deployed, total open risk
8. **"Add to campaign" action** — creates a new trade record tagged as a pyramid layer (existing `+ Trade` button gets a pre-fill mode when invoked from inside a campaign row)

Out of scope:
- Auto-trailing (the system never moves your stop without your click — it only suggests)
- Capital-at-Risk widget (Phase 2)
- Backtest-driven per-ticker stop suggestions (future phase; would need real-time ATR/EMA per ticker beyond the snapshot already in `universe.json`)

## Leg state derivation

State is derived from a trade's `trims[]` array on every render (no new persisted field needed):

| State | Condition |
|---|---|
| `PRE_TRIM` | No trims yet |
| `POST_T1` | Exactly 1 trim (any type), not `sell_rest` |
| `POST_T2` | Exactly 2 trims, neither `sell_rest` |
| `POST_T3` | ≥3 trims, none being final `sell_rest` |
| `CLOSED` | Any trim of type `sell_rest`, OR `currentQty == 0` |

Badge colors:
- `PRE_TRIM` → amber (at-risk, watch carefully)
- `POST_T1` → blue (working, banked some)
- `POST_T2` → teal (working well, riding residual)
- `POST_T3` → green (mostly out, runner only)
- `CLOSED` → gray (no badge in primary row; appears in expanded view)

## Stop suggestion engine

Per row, the engine returns one of:

```
{
  suggested_stop: number,         // the price level
  basis: 'csv-initial' | 'breakeven' | 'wk20ema' | 'd20ema',
  rationale: string,              // short, e.g. "wk20EMA - 0.25 ATR buffer"
  distance_atr: number,           // |current_price - suggested_stop| / ATR
}
```

Rules per leg state (using Phase 3 v3 defaults):

| State | Suggested stop |
|---|---|
| `PRE_TRIM` | Trade's current CSV stop (don't override the user's risk decision pre-T1) |
| `POST_T1`, `POST_T2`, `POST_T3` | `max(entry_price, wk_ema20_for_ticker - 0.25 × ATR)` — keeps stop at-or-above breakeven, hugs wk-20EMA with a small buffer to avoid wicking out |

The stop is displayed alongside the user-editable Stop column as a small ghost-value with a "→ Accept" link. Click to populate the Stop field; the dispatch sends `UPDATE_TRADE` with the suggested value. No auto-apply.

If a ticker has no EMA data in `universe.json` (delisted, missing), the suggestion shows `—` and the rationale becomes "no EMA data — set manually."

## Trim target hints

For each open row, computed inline:

- `+4R = entry + 4 × (entry - csv_initial_stop) × direction_sign`
- `+8R = entry + 8 × (entry - csv_initial_stop) × direction_sign`

Display as a compact "Targets: +4R $42.10 · +8R $56.40" line under the ticker name. Once the trade's `trims[]` contains a trim at or beyond a level, that target gets a strike-through and a green check.

Computed from CSV initial stop (not current trail stop) so R is always anchored to the original risk decision.

## EMA proximity alerts

Per row, a small chip appears if any of:

- `|price - 10EMA| / price < 1.5%` → chip "**10EMA**" (amber)
- `|price - 20EMA| / price < 2%` → chip "**20EMA**" (red)
- `wk_close < wk_10EMA` (Trim 2 signal) → chip "**T2**" (orange)
- `wk_close < wk_20EMA` (Full stop signal) → chip "**STOP**" (red)

Chips are read-only signals — they don't act, just notify. User decides what to do.

## Pipeline plumbing

Today's `universe.json` already has `ema21`, `sma50_dist`, `bo_count_*`, etc. Phase 1 needs four more per-ticker fields:

```python
'ema10': close.ewm(span=10, adjust=False).mean().iloc[-1],
'ema20': close.ewm(span=20, adjust=False).mean().iloc[-1],
'wk_ema10': weekly_close.ewm(span=10, adjust=False).mean().iloc[-1],
'wk_ema20': weekly_close.ewm(span=20, adjust=False).mean().iloc[-1],
```

Computed in `pipeline/adapters/yfinance_adapter.py::enrich_universe`, same place as the existing EMA21. Added to the `universe_cols` whitelist in `run_all.py`.

Frontend reads these via the existing `useUniverse` hook (no new fetch). The Portfolio Tracker joins by ticker on render.

## Campaign grouping (Exposure tab)

The Detail table in Exposure already supports expand/collapse for grouped tickers (Ticker column has the chevron). Extend the grouping criterion:

**Today:** trades grouped by `ticker` (any two trades with the same ticker collapse together).
**Phase 1:** trades grouped by `(ticker, direction)` with a `campaign_id` derived as the first-layer's trade ID. New trades that share `(ticker, direction)` and are entered within 60 business days of an open prior layer become part of that campaign.

Group row aggregates:
- **Blended entry** = `Σ (entry × qty) / Σ qty`
- **Total R deployed** = `Σ (entry - stop) × qty` (in $R)
- **Total open risk** = same, summed across only currently open layers
- **Total realized R** = sum across closed layers
- **Aggregate position %**, **aggregate market value** as usual

Group row also gets an "Add layer" mini-button that opens the trade form pre-filled with ticker + direction + an auto-tagged "Pyramid #N of campaign" note in the trade comment.

## Suggested-stop "Accept" UI affordance

In the Tracker table's Stop column, the cell renders:

```
[ user-editable stop input: $42.10 ]
  suggested $43.85 → Accept
```

Where the suggested value comes from the engine above, and "Accept" is a tiny link that overrides the input on click. If the user has already accepted (suggested matches current stop within $0.01), the suggestion is hidden — no nagging.

## Privacy mode + read-only mode behavior

- Privacy mode (already exists): suggestions remain visible (no dollar amounts in the rationale; the suggested value itself is fine — it's a price level, not a portfolio value)
- Read-only mode (Public BriefPreview): no Accept link, suggestions still display as informational

## File-level changes

```
pipeline/adapters/yfinance_adapter.py        add ema10/ema20/wk_ema10/wk_ema20 to enrich
pipeline/screeners/run_all.py                add to universe_cols whitelist

frontend/src/components/portfolio/lib/legState.js              NEW — derives PRE_TRIM/POST_T1/etc.
frontend/src/components/portfolio/lib/stopSuggestion.js        NEW — engine returning {suggested_stop, basis, rationale}
frontend/src/components/portfolio/lib/trimTargets.js           NEW — computes +4R/+8R targets
frontend/src/components/portfolio/lib/emaProximity.js          NEW — proximity chips
frontend/src/components/portfolio/lib/campaign.js              NEW — group trades into campaigns
frontend/src/components/portfolio/ui/LegStateBadge.jsx         NEW
frontend/src/components/portfolio/ui/StopCell.jsx              NEW — editable + suggestion + accept link
frontend/src/components/portfolio/ui/TrimTargetsLine.jsx       NEW — inline +4R/+8R chips
frontend/src/components/portfolio/ui/ProximityChips.jsx        NEW

frontend/src/components/portfolio/tabs/OverviewTab.jsx         modify — wire badge, stop cell, targets line
frontend/src/components/portfolio/tabs/ExposureTab.jsx         modify — campaign grouping in Detail
frontend/src/hooks/useUniverse.js                              modify (if needed) — expose EMA fields
```

## Testing strategy

- Unit: `legState`, `stopSuggestion`, `trimTargets`, `campaign` — pure functions, easy to test with fixture trades
- Visual: dev preview with sample trades (already loadable via "Try Sample" on the empty portfolio page)
- End-to-end: pick a real trade (e.g., BE 04-08), verify badge shifts as trims are recorded, verify stop suggestion updates, verify Accept works

## Risks / open questions

1. **EMA freshness**: `universe.json` is regenerated daily by the cron. The EMAs are end-of-day. Intraday, the suggestion is based on yesterday's close. Acceptable for swing trading (decisions are usually overnight) — but worth surfacing as a "data freshness" tooltip.
2. **Stop-suggestion conservatism**: the formula `max(entry, wk_ema20 - 0.25 ATR)` always keeps the stop at-or-above breakeven post-T1. This is by design — the Phase 3 finding was that close-based stops outperform, and breakeven is the natural floor. But the user may want to set a tighter stop on a particular trade for context-specific reasons; the editable Stop field always wins.
3. **Campaign detection**: the 60-day window matches the optimizer's pyramid detector. Edge case: if a user re-enters the same ticker after a long gap (>60d), the new entry is a fresh campaign, not an extension. This seems correct — but document it.
4. **"Add layer" pre-fill**: needs the trade form (`TradeForm.jsx`) to accept an optional `prefilled` prop. Minor refactor.

## Phase 3 v3 defaults baked into the UI

These are the recommended values the UI ships with — user can override per-position via the editable Stop field or by setting a different rule globally in Settings:

- **Trim 1 target**: +4R (size suggestion: 30% of original)
- **Trim 2 trigger**: weekly close < 10EMA (suggested size: 30% of remaining)
- **Trim 3 target**: +8R (suggested size: 100% of remaining)
- **Full stop**: weekly close < 20EMA, executed at next-day open
- **Stop basis**: close-confirmed by default (intraday on user discretion via the editable field)

These come straight from the v3 optimizer's `best_overall` output. If a future v4 finds different defaults, they update here.

## Acceptance criteria (Phase 1 done when)

1. ✅ Open Portfolio Tracker → every row shows a leg-state badge
2. ✅ Each row's Stop column shows the editable input + a ghost-text suggestion + Accept link
3. ✅ Each row shows "Targets: +4R $X · +8R $Y" under the ticker (strike-through if hit)
4. ✅ Each row shows EMA proximity chips when applicable
5. ✅ Exposure tab Detail table groups multi-entry same-ticker trades into a campaign parent row with aggregate stats
6. ✅ Campaign parent row has an "Add layer" button that opens the trade form pre-filled
7. ✅ `universe.json` includes the new EMA fields
8. ✅ All existing tests pass (sortable headers, filters, etc.)
9. ✅ Verified live on dev preview with sample trades — no console errors, all interactions work
