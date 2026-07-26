import { describe, it, expect } from 'vitest'
import { cumFactorAfter, unadjustClose } from './splitTable'

// Synthetic table with confirmed ex-dates for deterministic tests.
const T = {
  SNXX: [{ exDate: '2026-06-03', factor: 8 }],                       // forward 8:1
  SOXS: [                                                            // TWO reverse splits
    { exDate: '2026-06-10', factor: 1 / 10 },
    { exDate: '2026-07-15', factor: 1 / 9 },
  ],
  NVDL: [{ exDate: null, factor: 3 }],                              // placeholder, ignored
}

describe('cumFactorAfter — forward split', () => {
  it('applies factor to dates BEFORE the ex-date', () => {
    expect(cumFactorAfter('SNXX', '2026-04-21', T)).toBe(8)
  })
  it('is 1 on/after the ex-date (feed already on new scale)', () => {
    expect(cumFactorAfter('SNXX', '2026-06-03', T)).toBe(1)
    expect(cumFactorAfter('SNXX', '2026-06-10', T)).toBe(1)
  })
  it('is 1 for an unknown ticker', () => {
    expect(cumFactorAfter('AAPL', '2026-04-21', T)).toBe(1)
  })
})

describe('cumFactorAfter — repeated reverse splits (the case that broke auto-detect)', () => {
  it('compounds BOTH reverse splits for a date before both', () => {
    // before 06-10 and 07-15 → 1/10 × 1/9 = 1/90
    expect(cumFactorAfter('SOXS', '2026-06-04', T)).toBeCloseTo(1 / 90, 10)
  })
  it('applies only the later split for a date between them', () => {
    expect(cumFactorAfter('SOXS', '2026-06-20', T)).toBeCloseTo(1 / 9, 10)
  })
  it('is 1 after both splits', () => {
    expect(cumFactorAfter('SOXS', '2026-07-20', T)).toBe(1)
  })
})

describe('cumFactorAfter — placeholder entries are ignored (safe to import)', () => {
  it('null exDate contributes nothing', () => {
    expect(cumFactorAfter('NVDL', '2026-01-01', T)).toBe(1)
  })
})

describe('unadjustClose', () => {
  it('forward: $9 adjusted → ~$72 as-traded before an 8:1', () => {
    expect(unadjustClose(9, 'SNXX', '2026-04-21', T)).toBeCloseTo(72, 6)
  })
  it('reverse ×2: $532 adjusted → ~$5.91 as-traded before 1:10 then 1:9', () => {
    // This is the phantom-spike fix: without it, 32031 sh × $532 ≈ $17M.
    expect(unadjustClose(532, 'SOXS', '2026-06-04', T)).toBeCloseTo(532 / 90, 6)
  })
  it('returns null for null input', () => {
    expect(unadjustClose(null, 'SNXX', '2026-04-21', T)).toBeNull()
  })
  it('leaves a non-split ticker unchanged', () => {
    expect(unadjustClose(150.5, 'AAPL', '2026-04-21', T)).toBe(150.5)
  })
})
