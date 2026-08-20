/**
 * The names Andy added by hand, turned into cards.
 *
 * Two lists were living apart and are one list: the TRAY holds what he picked
 * off the morning pages (localStorage, `page3-shortlist`), and the Short List
 * tab renders the six seats the engine picked overnight. He said it plainly —
 * this page is the six pushed cards plus his own — so the tray is where the
 * manual half comes from.
 *
 * A hand-added name has a problem the engine's six do not: nobody built it a
 * card. `series`, `marks` and `verdict` are made by the nightly engine off a
 * name it already knows about, and a ticker added in this browser has not
 * reached the pipeline at all (the GAS `shortlist_upsert` half of the loop is
 * still unbuilt — DATA_CONTRACTS §七).
 *
 * What it CAN have is readings, and good ones: `universe.json` is rebuilt every
 * night over every name and carries `close`, `change_pct`, `rs_1m`, `rs_3m`,
 * `rs_line_pctl_21/63`, `atr_from_sma50`, `vcs`, `sp_signal`, `trend_base`,
 * `sector` — the same field NAMES the engine's cards use, so they drop straight
 * into a card shape without a translation layer inventing anything.
 *
 * So a manual name renders as a real card with real readings and an empty
 * chart that says why it is empty. It is not a lesser card pretending to be a
 * full one, and it is not hidden until the engine catches up.
 */

/** Readings a universe row can supply, by the card's own names. */
const CARRIED = [
  'close', 'change_pct', 'rel_volume', 'rs_1m', 'rs_3m', 'h_score',
  'rs_line_pctl_21', 'rs_line_pctl_63', 'atr_from_sma50', 'ema21_atr_dist',
  'high_52w_dist', 'vcs', 'trend_base', 'sector', 'sp_signal',
]

/**
 * @param entry  a tray entry: { ticker, from, group, group_state, rs_1m }
 * @param u      that ticker's universe row, or null
 */
export function cardFromTray(entry, u) {
  const readings = {}
  // absent stays absent: a field universe does not carry must not arrive as
  // null, because null claims it was measured and came out empty
  if (u) for (const k of CARRIED) if (u[k] != null) readings[k] = u[k]
  return {
    ticker: entry.ticker,
    source: 'manual',
    // the tray froze these at the moment of adding, which is the point of the
    // tray — what the name looked like on the day it was taken
    group: entry.group ?? null,
    state: entry.group_state ?? null,
    is_asset: false,
    readings,
    heat: null,
    verdict: null,          // the engine has not judged this name; do not invent one
    series: null,
    marks: [],
    panels: [],
    events: [],
    flags: {},
    takenFrom: entry.from ?? null,
    inUniverse: !!u,
  }
}

/**
 * The manual half of the page: tray names first, then any manual card the
 * engine already built that the tray does not hold.
 *
 * The engine's version wins on a ticker they share — it has the chart and the
 * verdict, and the tray's frozen readings are a subset of what it carries.
 * The tray's `from` survives either way: where a name came from is the thing
 * you cannot reconstruct a week later.
 */
export function manualCards(trayNames = [], doc, universeByTicker = {}) {
  const engine = new Map()
  for (const c of doc?.cards ?? []) if (c.source === 'manual') engine.set(c.ticker, c)

  const seen = new Set()
  const out = []
  for (const e of trayNames) {
    if (!e?.ticker || seen.has(e.ticker)) continue
    seen.add(e.ticker)
    const built = engine.get(e.ticker)
    out.push(built
      ? { ...built, takenFrom: e.from ?? null, inUniverse: true }
      : cardFromTray(e, universeByTicker[e.ticker] ?? null))
  }
  for (const [ticker, c] of engine) {
    if (seen.has(ticker)) continue
    out.push({ ...c, takenFrom: null, inUniverse: true })
  }
  return out
}
