/**
 * Compute price levels for +4R and +8R targets anchored to the trade's
 * CSV initial stop. Direction-aware.
 *
 * @returns {{targetR4: number, targetR8: number}|null} null when R is undefined.
 */
export function compute(trade) {
  const { entryPrice, stopPrice, direction } = trade
  const rPerShare = Math.abs(entryPrice - stopPrice)
  if (rPerShare <= 0) return null
  const sign = direction === 'long' ? 1 : -1
  return {
    targetR4: entryPrice + sign * 4 * rPerShare,
    targetR8: entryPrice + sign * 8 * rPerShare,
  }
}

/**
 * Returns true if any trim in the array has crossed (at-or-beyond) the level
 * in the direction of the trade.
 */
export function isHit(trims, level, direction) {
  if (!trims || trims.length === 0) return false
  return trims.some(t => {
    if (direction === 'long') return t.price >= level
    return t.price <= level
  })
}
