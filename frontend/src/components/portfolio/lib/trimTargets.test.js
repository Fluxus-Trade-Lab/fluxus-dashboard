import { describe, it, expect } from 'vitest'
import { compute, isHit } from './trimTargets'

describe('trimTargets.compute', () => {
  it('returns +4R and +8R for a long', () => {
    const t = { entryPrice: 100, stopPrice: 95, direction: 'long', trims: [] }
    const out = compute(t)
    expect(out.targetR4).toBe(120)
    expect(out.targetR8).toBe(140)
  })
  it('inverts price math for a short', () => {
    const t = { entryPrice: 100, stopPrice: 105, direction: 'short', trims: [] }
    const out = compute(t)
    expect(out.targetR4).toBe(80)
    expect(out.targetR8).toBe(60)
  })
  it('returns null when stopPrice equals entryPrice (no R)', () => {
    const t = { entryPrice: 100, stopPrice: 100, direction: 'long', trims: [] }
    expect(compute(t)).toBeNull()
  })
})

describe('trimTargets.isHit', () => {
  it('returns true for long when any trim is at or above the level', () => {
    const trims = [{ price: 121 }]
    expect(isHit(trims, 120, 'long')).toBe(true)
    expect(isHit(trims, 140, 'long')).toBe(false)
  })
  it('returns true for short when any trim is at or below the level', () => {
    const trims = [{ price: 79 }]
    expect(isHit(trims, 80, 'short')).toBe(true)
    expect(isHit(trims, 60, 'short')).toBe(false)
  })
})
