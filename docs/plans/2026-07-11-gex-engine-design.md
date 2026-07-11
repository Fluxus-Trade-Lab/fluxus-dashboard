# Fluxus GEX Engine — Design Spec

*2026-07-11 · Status: approved for Phase 1 implementation planning*

## Goal

A daily automated pipeline that pulls IBKR option chains, computes dealer gamma-exposure structure, and emits (a) a versioned `gex.json` data layer and (b) a rendered HTML daily brief. The JSON is the product; the brief is its first renderer. Downstream consumers (Fluxus dashboard page, TradingView levels, alerts, regime backtests) read the same JSON in later phases.

Solves three things at once: **decision support** (the morning map), **persistent state** (dated archive = trading journal + resumable context across chat sessions), and **shareable output** (the brief).

## Decisions (settled)

| Question | Decision |
|---|---|
| Instruments | **SPX + QQQ** native; converted levels published for ES/SPY (from SPX) and NQ/NDX (from QQQ) |
| Cadence (MVP) | **Once daily, 8:00am ET premarket** (OI settles overnight — same reason SpotGamma's morning calc is the day's map). Optional post-close archive run later |
| Run model | **Fully unattended local**: IB Gateway + IBC (headless auto-login) + launchd cron on the Mac |
| Publication | Commit `data/gex/*` to the repo → rides the existing Vercel auto-deploy |
| MVP boundary | Phase 1 only: engine + JSON + brief. Dashboard page = Phase 2. Intraday/TV/alerts = Phase 3 |
| Calendar strategies in brief | User is not trading calendars; strategy-fit table reflects preferences at render time |

## Architecture

```
IB Gateway + IBC (headless, auto-login)          [one-time infra]
  └─ launchd @ 8:00am ET, Mon–Fri
       └─ pipeline/gex/engine.py
            ├─ pull SPX + QQQ chains (front 0–2DTE + swing ~5–10DTE tenors)
            ├─ pull sync quotes: SPX index, ES fut, QQQ, NQ fut → live bases/ratios
            ├─ compute per instrument+tenor:
            │    spot · net GEX ($mm/1%) · zero-gamma flip · volatility trigger
            │    call wall · put wall · abs-gamma pin · ATM straddle/expected move · ATM IV
            ├─ derive: regime (pos/neg γ) · wall-migration Δ vs prior day · OPEX flag
            │          · converted levels (ES/SPY, NQ/NDX) · strategy-fit ratings · plan bullets
            ├─ write data/gex/gex_YYYYMMDD.json  +  data/gex/latest.json
            ├─ render data/gex/brief_YYYYMMDD.html (+ latest.html) from template
            └─ git add/commit/push (only data/gex/*)
```

## Components

1. **`pipeline/gex/engine.py`** — orchestrator. Reuses proven code: chain pull from `scripts/ibkr_daily_option_plan.py` (SPX path incl. SPY×10 spot fallback; QQQ path with **integer-strike filtering**), GEX/flip/pin/walls math from this week's inline calcs. **Low clientIds (1–30) only** (high IDs hang TWS).
2. **`pipeline/gex/schema.py` + `gex.json` v1** — the data contract:
   ```json
   { "version": 1, "asof": "...", "opex_flag": {...},
     "instruments": { "SPX": { "spot":..., "basis_es":...,
        "tenors": { "front": {...}, "swing": {
           "expiry":"20260717", "net_gex_mm":..., "flip":..., "vol_trigger":...,
           "call_wall":..., "put_wall":..., "pin":..., "straddle":..., "atm_iv":...,
           "walls_top": [...], "delta_vs_prior": {"call_wall": +25, ...},
           "converted": {"ES": {...}, "SPY": {...}} } } }, "QQQ": {...} },
     "read": { "regime":"positive", "bull": [...], "bear": [...], "plan": [...] },
     "strategy_fit": [ {"name":..., "rating":"go|favored|caution|avoid", "why":...} ],
     "assumptions": { "dealer_side": "long calls / short puts (v1 baseline)" } }
   ```
3. **`pipeline/gex/render.py` + `templates/brief.html`** — the artifact brief converted into a template (Jinja2), populated purely from the JSON. No hand-written numbers.
4. **Infra (one-time):** IB Gateway + IBC install/config (auto-login, dialog dismissal, daily restart schedule) + `launchd` plist. Documented in `docs/gex-engine-setup.md`.
5. **Derivation rules (deterministic, documented):**
   - *Regime*: sign of net GEX (swing tenor primary).
   - *Vol Trigger*: last significant positive-GEX support strike above the Put Wall (v1 heuristic; distinct from flip).
   - *Wall migration*: Δ call/put wall & flip vs prior day's JSON; call wall rolling up = bullish note (SpotGamma's key signal).
   - *OPEX flag*: monthly OPEX date proximity (e.g., Jul 17) — gamma roll-off warning.
   - *Strategy fit*: rule table keyed off regime + IV + distance-to-walls (encodes this week's learned rules: no condors/naked in neg γ; far-OTM bull put spreads in pos γ + held floor; dip-fade at put wall; breakout triggers at call-wall clears).

## Error handling

- Gateway unreachable / pull fails → retry ×2 with backoff; on failure, **keep last good `latest.json`, mark `"stale": true` with reason**, render brief with a visible STALE banner, still commit (the journal records the gap). Never publish half-computed data.
- Sparse greeks (e.g., QQQ after-hours) → per-field null + `"quality"` flags rather than zeros (this week's +5 $mm artifact must be impossible).
- Git push failure → local files remain; next run recommits.

## Testing

- Unit: GEX/flip/wall math against fixture chains (including a known-answer case reproducing the Jul-10 ES +2,940 read); QQQ integer-strike filter; basis conversion.
- Integration: one live pull against Gateway in paper mode; snapshot the JSON.
- Renderer: golden-file test — fixture JSON → expected HTML.

## Out of scope (later phases)

- Phase 2: Fluxus dashboard "Positioning" page reading `latest.json`.
- Phase 3: on-demand intraday refresh; TradingView level push (ties into existing GEX-levels side project); alerts; regime backtest over the archive; SPX+SPY+ES aggregated complex; tape-based intraday flow (HIRO-style) — explicitly the hardest, furthest item.

## References

- SpotGamma methodology: GEX, Call/Put Wall, Volatility Trigger, morning-OI recompute (support.spotgamma.com articles, checked 2026-07-11).
- Internal: `docs/spx-0dte-july-dip-buy-playbook.md`, memory `project_spx_0dte_july_playbook.md`, `trading_state_jul2026.md`.
