import { lookupPrice } from './calculations'

/**
 * Auto-detecting split adjustment.
 *
 * The price feed (Yahoo via GAS) is split-adjusted RETROACTIVELY across its
 * whole history: once a ticker splits N:1, every historical close — including
 * dates long before the split — is divided by N. The trade log, however, keeps
 * shares and prices exactly AS TRADED. So a position held (or even just closed)
 * before a later split gets valued as `qty(as-traded) × close(adjusted)`, which
 * is wrong by the split factor.
 *
 * Real case: SNXX (2x SNDK) did an 8:1 forward split on 2026-06-03. April fills
 * at ~$72 now read ~$9 in the feed (72 / 8), so the April equity curve cratered
 * for a position that was already closed.
 *
 * We don't need the ex-date. Because the feed is fully adjusted as of "now", the
 * per-trade scale mismatch is measured directly: `entryPrice / feedClose(entryDay)`.
 * For a normal trade that's ~1 (your fill is within a few percent of the day's
 * close). For a split-affected trade it snaps to a clean ratio (8, 1/10, …). We
 * then rescale the trade onto the feed's scale: qty ×factor, prices ÷factor.
 * Every dollar amount and every ratio (R-multiple, %·return, realized P&L) is
 * invariant under this — only the qty×feedPrice MTM scale is corrected.
 */

// Forward ratios we recognise; reciprocals cover reverse splits.
const CLEAN_RATIOS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 50]

/** Snap x to the nearest clean split ratio within relative tolerance, else null. */
export function snapToCleanRatio(x, tol = 0.15) {
  let best = null
  let bestErr = tol
  for (const r of CLEAN_RATIOS) {
    for (const c of [r, 1 / r]) {
      const err = Math.abs(x - c) / c
      if (err < bestErr) { bestErr = err; best = c }
    }
  }
  return best
}

const ratioLabel = f => (f >= 1 ? `${Math.round(f)}:1` : `1:${Math.round(1 / f)}`)

/**
 * Detect the split factor for one trade against the (adjusted) price feed.
 * @returns {{factor:number, ratioLabel?:string, straddle?:boolean, suspect?:number}}
 *          factor === 1 means "no adjustment".
 */
export function detectSplitFactor(trade, dailyPrices) {
  const feedAt = d => lookupPrice(trade.ticker, (d || '').slice(0, 10), dailyPrices, null)

  const entryFeed = feedAt(trade.entryDate)
  if (!entryFeed || !(trade.entryPrice > 0)) return { factor: 1 }

  const entryRatio = trade.entryPrice / entryFeed
  if (entryRatio > 0.67 && entryRatio < 1.5) return { factor: 1 } // your fill ≈ that day's close → no split

  const snapped = snapToCleanRatio(entryRatio)
  if (!snapped) return { factor: 1, suspect: entryRatio } // off-scale but not a clean split — leave alone

  // Consistency guard: every fill must sit on the SAME (pre-split) scale. A trade
  // that straddles the ex-date has some fills already on the adjusted (≈1) scale;
  // one factor can't fix both, so flag it for a manual split record instead of
  // corrupting the already-correct fills.
  const fills = [[trade.entryPrice, trade.entryDate], ...(trade.trims || []).map(tr => [tr.price, tr.date])]
  let onAdjustedScale = 0
  for (const [px, d] of fills) {
    const f = feedAt(d)
    if (!f || !(px > 0)) continue
    if (Math.abs(px / f - 1) < 0.25) onAdjustedScale++
  }
  if (onAdjustedScale > 0) return { factor: 1, straddle: true }

  return { factor: snapped, ratioLabel: ratioLabel(snapped) }
}

/** Rescale a trade onto the feed's split-adjusted scale. Dollar amounts/ratios unchanged. */
export function applySplitFactor(trade, factor) {
  if (!factor || factor === 1) return trade
  const adj = { ...trade, entryPrice: trade.entryPrice / factor, _splitFactor: factor }
  if (trade.originalQty != null) adj.originalQty = trade.originalQty * factor
  if (trade.currentQty != null) adj.currentQty = trade.currentQty * factor
  if (trade.stopPrice != null) adj.stopPrice = trade.stopPrice / factor
  if (trade.initialStop != null) adj.initialStop = trade.initialStop / factor
  adj.trims = (trade.trims || []).map(tr => ({ ...tr, qty: tr.qty * factor, price: tr.price / factor }))
  return adj
}

/**
 * Adjust a whole trade list for retroactive splits, auto-detected from the feed.
 * @returns {{trades: object[], detected: object[]}} detected lists applied factors
 *          and straddle warnings (ticker + entryDate) for the UI.
 */
export function adjustTradesForSplits(trades, dailyPrices) {
  if (!trades?.length || !dailyPrices) return { trades: trades || [], detected: [] }
  const detected = []
  const out = trades.map(t => {
    const res = detectSplitFactor(t, dailyPrices)
    if (res.straddle) {
      detected.push({ ticker: t.ticker, entryDate: t.entryDate, straddle: true })
      return t
    }
    if (res.factor && res.factor !== 1) {
      detected.push({ ticker: t.ticker, entryDate: t.entryDate, factor: res.factor, ratioLabel: res.ratioLabel })
      return applySplitFactor(t, res.factor)
    }
    return t
  })
  return { trades: out, detected }
}
