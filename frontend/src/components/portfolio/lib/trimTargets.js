/**
 * Compute price levels for +4R and +8R targets anchored to the trade's
 * locked-at-entry stop. Direction-aware. Trailing the live `stopPrice` would
 * shrink R-per-share and quietly move these target prices closer to entry —
 * we anchor to `initialStop` so the +4R / +8R levels stay constant.
 *
 * @returns {{targetR4: number, targetR8: number}|null} null when R is undefined.
 */
export function compute(trade) {
  const { entryPrice, direction } = trade
  // Trim targets are R multiples off the entry stop. With no entry stop
  // there are no targets -- better blank than measured from a moved line.
  const initialStop = trade.initialStop ?? null
  // Explicit, not arithmetic: `entryPrice - null` is `entryPrice - 0`, so a
  // null anchor would silently produce targets measured from zero.
  if (initialStop == null) return null
  const rPerShare = Math.abs(entryPrice - initialStop)
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
