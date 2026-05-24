import { describe, it, expect } from 'vitest'
import { derive } from './legState'

describe('legState.derive', () => {
  it('returns CLOSED if currentQty is 0', () => {
    expect(derive({ currentQty: 0, originalQty: 100, trims: [] })).toBe('CLOSED')
  })

  it('returns CLOSED if any trim is sell_rest', () => {
    expect(derive({ currentQty: 50, originalQty: 100, trims: [{ type: 'sell_rest' }] })).toBe('CLOSED')
  })

  it('returns PRE_TRIM when no trims and qty > 0', () => {
    expect(derive({ currentQty: 100, originalQty: 100, trims: [] })).toBe('PRE_TRIM')
  })

  it('returns POST_T1 with exactly 1 partial trim', () => {
    expect(derive({ currentQty: 70, originalQty: 100, trims: [{ type: 'trim_1_3' }] })).toBe('POST_T1')
  })

  it('returns POST_T2 with exactly 2 partial trims', () => {
    expect(derive({
      currentQty: 40, originalQty: 100,
      trims: [{ type: 'trim_1_3' }, { type: 'trim_1_3' }],
    })).toBe('POST_T2')
  })

  it('returns POST_T3 with 3+ partial trims', () => {
    expect(derive({
      currentQty: 10, originalQty: 100,
      trims: [{ type: 'trim_1_3' }, { type: 'trim_1_5' }, { type: 'trim_1_5' }],
    })).toBe('POST_T3')
  })
})
