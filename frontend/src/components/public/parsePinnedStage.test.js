import { describe, it, expect } from 'vitest'
import { parsePinnedStage } from './parsePinnedStage'

/**
 * This test exists because its subject shipped broken: Number(null) is 0, so
 * the absent-parameter case pinned every visitor to stage 0 and the hero
 * froze in production. The first case below is the whole point.
 */
describe('parsePinnedStage', () => {
  it('returns null when there is no stage parameter — the case that froze production', () => {
    expect(parsePinnedStage('', 5)).toBeNull()
    expect(parsePinnedStage('?utm_source=x', 5)).toBeNull()
  })

  it('pins a valid stage', () => {
    expect(parsePinnedStage('?stage=0', 5)).toBe(0)
    expect(parsePinnedStage('?stage=4', 5)).toBe(4)
  })

  it('rejects everything else', () => {
    expect(parsePinnedStage('?stage=5', 5)).toBeNull()      // out of range
    expect(parsePinnedStage('?stage=-1', 5)).toBeNull()
    expect(parsePinnedStage('?stage=2.5', 5)).toBeNull()
    expect(parsePinnedStage('?stage=abc', 5)).toBeNull()
    expect(parsePinnedStage('?stage=', 5)).toBeNull()       // empty string is Number('') === 0
  })
})
