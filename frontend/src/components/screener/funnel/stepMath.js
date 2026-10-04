/**
 * The Screener step bar — pure reads over focus.json and watchlist.json.
 *
 * Andy 2026-10-04 approved the merge (「选A」, then 「可以」 on the preview): the
 * funnel's six cards and the morning brief's five steps become one bar,
 * 可交易 → 形态 → 资格 → 过闸 → 水域, each a name and a number, and one scan
 * list that holds both the funnel's setups and the Today's List panels.
 *
 * Every count on the bar is the file's own: `counts.gate` for 可交易, and for
 * the chosen setup its rows, its rows with all four §11.1 checks (`qn === 4`),
 * and its `focus` rows. 水域 is the share of the current step whose theme is
 * Leading or Improving.
 *
 * The one list the file does not ship is the 781 tradeable names themselves.
 * `rowsPassingGate` lists them from universe.json with the thresholds the file
 * states in `rule.gate` (same rule as build_cards.py `passes_gate`); a test
 * holds its length equal to `counts.gate`, so the two cannot drift silently.
 */

export const STEP_KEYS = ['gate', 'setup', 'qual', 'focus']
export const DEFAULT_STEP = 'focus'

/** The setups focus.json carries, in the order the scan list shows them. */
export const FOCUS_SETUPS = ['pullback', 'ep', 'vcp']

/**
 * The Today's List panels that join the scan list (watchlist.json keys).
 * EP lives in the funnel's own `ep` setup; the exit panels (stop_hit, ll_break,
 * extended) stay off this page (Andy: 「离场信号暂时不放这里」).
 */
export const PANEL_SCANS = [
  'true_market_leaders', 'liquid_leaders',
  'ma_reclaim', 'll_hl_1st', 'll_hl_2nd', 'll_hl_trend_break', 'liquid_leader_pullback',
  'vcs', 'anticipation',
  'pp_today', 'pp_2plus_10d', 'morales_pp_10d',
  'weekly_momentum_97', 'bullish_4pct', 'weekly_20_gainers',
]

export const isWater = (state) => state === 'Leading' || state === 'Improving'

/** The gate focus.json states; used only when that file is absent (same as build_cards.py GATE). */
export const FALLBACK_GATE = { cap: 1e9, dollar_vol: 20e6, adr: 3.5 }

/** one universe row against the stated gate */
export const passesGate = (u, gate) => (u.market_cap ?? 0) >= gate.cap
  && dollarVol(u) >= gate.dollar_vol && (u.adr_pct ?? 0) >= gate.adr

const dollarVol = (u) => u.sb_avg_dollar_vol_20 ?? (u.avg_volume ?? 0) * (u.close ?? 0)

/** universe rows that pass the file's stated gate (cap, $ volume, ADR) */
export function rowsPassingGate(universeRows, gate) {
  if (!universeRows || !gate) return []
  return universeRows.filter((u) => passesGate(u, gate))
}

/** the cards of one focus.json setup at one step */
export function setupCards(doc, setup, step) {
  const rows = doc?.setups?.[setup]?.rows ?? []
  if (step === 'qual') return rows.filter((r) => r.qn === 4)
  if (step === 'focus') return rows.filter((r) => r.focus)
  return rows
}

/** the numbers on the bar for a focus.json setup */
export function stepCounts(doc, setup) {
  const rows = doc?.setups?.[setup]?.rows ?? []
  const focus = rows.filter((r) => r.focus)
  return {
    gate: doc?.counts?.gate ?? null,
    setup: rows.length,
    qual: rows.filter((r) => r.qn === 4).length,
    focus: focus.length,
    water: focus.filter((r) => isWater(r.theme?.state)).length,
  }
}

/** the watchlist panels this page lists, in PANEL_SCANS order; absent panels are left out */
export function panelScans(watchlist) {
  const byKey = new Map()
  for (const z of watchlist?.zones ?? []) for (const p of z.panels ?? []) byKey.set(p.key, p)
  return PANEL_SCANS.filter((k) => byKey.has(k)).map((k) => {
    const p = byKey.get(k)
    return { key: k, label: p.label, measured: Boolean(p.measured),
             tickers: (p.tickers ?? []).map((r) => r.ticker) }
  })
}

export const byRs = (a, b) => (b.rs ?? -1) - (a.rs ?? -1) || a.t.localeCompare(b.t)
