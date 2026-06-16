import { describe, it, expect } from 'vitest'
import { rejectRevertingSpikes } from './calculations'

describe('rejectRevertingSpikes', () => {
  it('forward-fills a one-bar DOWN spike (3:1 split mis-scale)', () => {
    // ~$90 every day, but one bar comes back on the post-split (1/3) scale.
    const out = rejectRevertingSpikes([90, 90.2, 30.1, 90.6, 90.4])
    expect(out).toEqual([90, 90.2, 90.2, 90.6, 90.4]) // bad bar -> last good
  })

  it('forward-fills a one-bar UP spike (3x mis-scale)', () => {
    const out = rejectRevertingSpikes([30, 30.1, 90.2, 30.3, 30.2])
    expect(out).toEqual([30, 30.1, 30.1, 30.3, 30.2])
  })

  it('leaves a persistent gap-down alone (real move, not a revert)', () => {
    // Drops and STAYS down — a legitimate move, must not be touched.
    const out = rejectRevertingSpikes([100, 100, 60, 58, 61])
    expect(out).toEqual([100, 100, 60, 58, 61])
  })

  it('leaves a legitimate large single-day leveraged move alone', () => {
    // 3x ETF rips +40% and holds — below the 1.6x spike factor, not flagged.
    const out = rejectRevertingSpikes([10, 10, 14, 14.2, 13.8])
    expect(out).toEqual([10, 10, 14, 14.2, 13.8])
  })

  it('never modifies first or last bar (no two-sided neighbours)', () => {
    const out = rejectRevertingSpikes([300, 100, 100])
    expect(out[0]).toBe(300)
    const out2 = rejectRevertingSpikes([100, 100, 300])
    expect(out2[2]).toBe(300)
  })

  it('tolerates nulls (missing data) without crashing', () => {
    const out = rejectRevertingSpikes([90, null, 30, null, 90])
    expect(out).toEqual([90, null, 30, null, 90]) // can't judge with null neighbours
  })

  it('is a no-op on a flat/normal series', () => {
    const s = [50, 51, 49.5, 50.2, 51.1]
    expect(rejectRevertingSpikes(s)).toEqual(s)
  })
})
