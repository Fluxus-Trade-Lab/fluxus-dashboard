import { lookupPrice } from './calculations'
import { SPLIT_TABLE, unadjustClose } from './splitTable'

/**
 * Frozen daily-price snapshot + split suggester.
 *
 * buildFrozenSnapshot() converts the live (retroactively split-adjusted) feed
 * back onto the as-traded scale using the explicit SPLIT_TABLE and returns an
 * immutable {`TICKER:DATE`: asTradedClose} map. Once persisted, historical MTM
 * reads from this frozen truth and is immune to any FUTURE split re-adjustment.
 *
 * suggestSplits() is the *helper* that proposes new SPLIT_TABLE entries — it
 * detects single AND repeated/composite splits (the leveraged-ETF case the
 * per-trade clean-ratio detector in splits.js silently missed).
 */

const median = arr => {
  const s = [...arr].sort((a, b) => a - b)
  const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

/**
 * Freeze the feed onto the as-traded scale for every traded ticker.
 * @returns {{prices: Record<string, number>, meta: object}}
 */
export function buildFrozenSnapshot(trades, dailyPrices, table = SPLIT_TABLE) {
  const tickers = new Set((trades || []).map(t => t.ticker))
  const prices = {}
  let n = 0
  for (const [key, close] of Object.entries(dailyPrices || {})) {
    const idx = key.lastIndexOf(':')
    if (idx < 0) continue
    const tk = key.slice(0, idx)
    const date = key.slice(idx + 1)
    if (!tickers.has(tk)) continue
    const v = unadjustClose(close, tk, date, table)
    if (v != null) { prices[key] = v; n++ }
  }
  return {
    prices,
    meta: {
      frozenAt: new Date().toISOString(),
      tickers: [...tickers].sort(),
      pointCount: n,
      splitTableTickers: Object.keys(table || {}),
    },
  }
}

// Clean single ratios and their pairwise products (covers repeated splits),
// capped so we don't over-fit. Reciprocals are handled in the snap loop.
const BASE = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 50]
const COMPOSITE = (() => {
  const s = new Set()
  for (const a of BASE) {
    s.add(a)
    for (const b of BASE) if (a * b <= 200) s.add(a * b)
  }
  return [...s].sort((x, y) => x - y)
})()

/** Snap x to the nearest clean (single or composite) ratio or its reciprocal. */
export function snapComposite(x, tol = 0.12) {
  let best = null
  let bestErr = tol
  for (const r of COMPOSITE) {
    for (const c of [r, 1 / r]) {
      const err = Math.abs(x - c) / c
      if (err < bestErr) { bestErr = err; best = c }
    }
  }
  return best
}

const ratioLabel = f => (f >= 1 ? `${Math.round(f)}:1` : `1:${Math.round(1 / f)}`)

/**
 * Measure each trade's cumulative scale gap vs the feed, snap it, and decompose
 * per-ticker into individual split events with approximate ex-dates.
 *
 * The measured raw ratio r = fill / feedClose IS the cumulative un-adjust factor
 * (asTraded/adjusted) for that trade's era. As entry dates advance past each ex-
 * date, the cumulative factor steps toward 1; the ratio of adjacent levels is one
 * split's factor, and the boundary date approximates its ex-date.
 *
 * @returns {{ suggestions: object[], perTrade: object[], straddles: object[] }}
 */
export function suggestSplits(trades, dailyPrices, table = SPLIT_TABLE) {
  const feedAt = (tk, d) => lookupPrice(tk, (d || '').slice(0, 10), dailyPrices, null)

  // 1. Per-trade cumulative factor (snapped), skipping non-split (~1) trades.
  const perTrade = []
  const straddles = []
  for (const t of trades || []) {
    const fills = [[t.entryPrice, t.entryDate], ...(t.trims || []).map(tr => [tr.price, tr.date])]
    const ratios = []
    for (const [px, d] of fills) {
      const f = feedAt(t.ticker, d)
      if (f != null && f > 0 && px > 0) ratios.push(px / f)
    }
    if (!ratios.length) continue
    const med = median(ratios)
    if (med > 0.67 && med < 1.5) continue // fills ≈ closes → no split era

    // A trade with fills on BOTH scales straddles an ex-date — flag, don't snap.
    if (ratios.some(r => r > 0.67 && r < 1.5)) {
      straddles.push({ ticker: t.ticker, entryDate: t.entryDate, measured: med })
      continue
    }
    const snapped = snapComposite(med)
    perTrade.push({
      ticker: t.ticker,
      entryDate: (t.entryDate || '').slice(0, 10),
      measured: med,
      cumFactor: snapped ?? med,
      snapped: snapped != null,
    })
  }

  // 2. Decompose each ticker's cumulative levels into individual splits.
  const byTicker = {}
  for (const p of perTrade) (byTicker[p.ticker] ||= []).push(p)

  const suggestions = []
  for (const [ticker, rows] of Object.entries(byTicker)) {
    rows.sort((a, b) => a.entryDate.localeCompare(b.entryDate))
    // Distinct cumulative levels in date order (older → higher magnitude gap).
    const levels = [] // { cumFactor, firstEntry }
    for (const r of rows) {
      const last = levels[levels.length - 1]
      if (!last || Math.abs(r.cumFactor - last.cumFactor) / Math.abs(last.cumFactor) > 0.05) {
        levels.push({ cumFactor: r.cumFactor, firstEntry: r.entryDate })
      }
    }
    // Append the implicit "current scale" level (cumFactor 1) as the tail.
    const chain = [...levels, { cumFactor: 1, firstEntry: null }]
    for (let i = 0; i < chain.length - 1; i++) {
      const before = chain[i].cumFactor
      const after = chain[i + 1].cumFactor
      const splitFactor = before / after // one split's share multiplier
      const snappedFactor = snapComposite(splitFactor) ?? splitFactor
      suggestions.push({
        ticker,
        exDate: chain[i + 1].firstEntry, // first entry already on the post-split scale ≈ on/after ex-date
        factor: snappedFactor,
        ratioLabel: ratioLabel(snappedFactor),
        basis: `cum ${before.toPrecision(3)} → ${after.toPrecision(3)}`,
        confirmed: false,
      })
    }
  }

  return { suggestions, perTrade, straddles }
}
