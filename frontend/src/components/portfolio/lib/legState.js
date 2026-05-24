/**
 * Derive a position's leg state from its current quantity and trim history.
 * @param {{currentQty: number, originalQty: number, trims: Array<{type: string}>}} trade
 * @returns {'PRE_TRIM'|'POST_T1'|'POST_T2'|'POST_T3'|'CLOSED'}
 */
export function derive(trade) {
  if (trade.currentQty <= 0) return 'CLOSED'
  const trims = trade.trims || []
  if (trims.some(t => t.type === 'sell_rest')) return 'CLOSED'
  const n = trims.length
  if (n === 0) return 'PRE_TRIM'
  if (n === 1) return 'POST_T1'
  if (n === 2) return 'POST_T2'
  return 'POST_T3'
}

/** Color hint for a leg-state badge, used by LegStateBadge. */
export const STATE_COLORS = {
  PRE_TRIM: 'amber',
  POST_T1: 'blue',
  POST_T2: 'teal',
  POST_T3: 'green',
  CLOSED: 'gray',
}
