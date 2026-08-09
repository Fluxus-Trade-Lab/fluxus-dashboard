# Live 5-min GEX Snapshot — Producer/Consumer Design

**Status:** Design only. Not scheduled for build. Producer runs manually today.
**Date:** 2026-07-23
**Author:** Andy + Claude

## Goal

Refresh the SPX GEX snapshot (gamma rails + gamma-profile chart + expected move
+ VIX) every ~5 minutes during the RTH session, and surface it live on the
Fluxus dashboard, without burning agent tokens and without heavy compute.

## Key finding: this is I/O- and permission-bound, not compute-bound

- **Tokens:** zero, *if* a scheduled Python job does the pull. It never routes
  through Claude. (An agent-driven 5-min loop would be expensive and is the
  wrong design — explicitly excluded.)
- **GPU:** none, ever.
- **CPU:** negligible — Black-Scholes gamma over a narrow strike window + a
  profile grid is sub-millisecond. Wall-time is IBKR network round-trips
  (~10–30s), not computation. 78 pulls/session is nothing.

The real constraints are IBKR pacing, keeping TWS logged in overnight (JST),
and OPRA data cost.

## Architecture — producer / consumer split

```
  [ Mac, TWS logged in ]                     [ Vercel / Fluxus dashboard ]
  producer loop (launchd)                    consumer page (React)
   every 5 min during RTH:                    every 5 min (or on focus):
     gex_levels.py  --window tight    ─┐        fetch latest.json
     build_snapshot.py                 │  →     render gamma chart client-side
     write gex_SPX_latest.json  ───────┘        (port pipeline.reference SVG)
     publish to static store
```

Heavy work runs where the data is (TWS on the Mac). The dashboard is a thin
renderer — the browser draws the chart, so server cost is ~zero.

## Producer (Mac)

- **Scheduler:** launchd job, RTH-gated like `run_gex_daily.sh` (ET-window
  guard, weekday check). Fires every 5 min 09:30–16:00 ET.
- **Pull scope — THROTTLE HERE.** The daily `gex_levels.py` qualifies ~480
  contracts; doing that every 5 min risks IBKR's market-data line cap (~100 on
  a base sub). Mitigations, in order of preference:
  1. Add a `--window` flag narrowing strikes to ±175 (≈14 strikes = 28
     contracts) — matches what the gamma chart already displays, well under
     limits, and OI barely moves intrasession so wide wings add little.
  2. Reuse a single IB connection across the session instead of reconnecting
     each pull (the current per-run connect/disconnect adds pacing pressure).
  3. Back off on pacing errors (162/165/pacing) rather than hammering.
- **Output:** overwrite `gex_SPX_latest.json` + `snapshot_SPX_latest.json`
  each run (single rolling file, ET-stamped via `marketcal`). Keep the dated
  EOD file for the archive as today.
- **Publish:** do NOT git-commit every 5 min (78 commits/day of noise). Write
  the latest JSON to a static store the dashboard can read:
  - Option A: `frontend/public/data/gex/latest.json`, pushed once at EOD or via
    a lightweight rsync/Blob upload intraday.
  - Option B (preferred for intraday): Vercel Blob or a tiny KV, updated each
    run; dashboard reads that URL.

## Consumer (Fluxus dashboard)

- New page/panel that fetches `latest.json` on an interval (5 min) or on tab
  focus; shows staleness if the timestamp is old (producer down / TWS logged
  out).
- Render the gamma profile **client-side** — port the SVG logic from
  `pipeline/reference/render.py::_gamma_svg` to a React component, or use an
  existing chart lib. Same rails + EM + VIX card as the HTML snapshot.
- Zero server compute: the browser draws it from JSON.

## The real blocker: TWS uptime during RTH

RTH (09:30–16:00 ET) is **22:30–05:00 JST** — overnight on the Mac. TWS
auto-logs-out ~daily and needs 2FA (already noted in `run_gex_daily.sh`). A
5-min RTH loop needs TWS alive the whole window.

- Use **IB Gateway + IBC** (IBController) for headless auto-login/restart.
- Keep the Mac awake for the session (`caffeinate` / `pmset` schedule).
- Producer must detect a dead connection and mark `latest.json` stale rather
  than silently serving the last good pull (the dashboard already shows
  staleness if we stamp `generated_at`).

## Non-goals / phasing

- **Not** an agent-driven loop. No Claude in the hot path.
- **Not** tick-level streaming — 5-min OI/greeks snapshots are enough for GEX.
  (Tick-level dealer flow is the separate OptionsFlow engine.)
- Phase 1: producer loop writing rolling `latest.json` locally + verify pacing
  holds for a full session. Phase 2: publish mechanism. Phase 3: dashboard
  page with client-side chart. Phase 4: TWS-uptime hardening with IBC.

## Rough effort

| Piece | Estimate |
|---|---|
| Producer loop + `--window` throttle + single-connection reuse | ~0.5 day |
| Publish mechanism (Blob/KV or static) | ~2–3 h |
| Dashboard page + client-side gamma chart (port SVG) | ~1 day |
| TWS uptime hardening (IBC + caffeinate) | ~0.5 day, fiddly |

The code is the easy part; TWS staying logged in overnight is where the real
friction is.
