import { describe, it, expect } from 'vitest'
import {
  viewport, priceRange, openingCursor, acts, readout, compareEntries, ema, sma,
} from './replayMath'

function bars(n = 300, f = i => 10 + i * 0.1) {
  return Array.from({ length: n }, (_, i) => {
    const p = f(i)
    return {
      time: new Date(Date.UTC(2020, 0, 1 + i)).toISOString().slice(0, 10),
      open: p * 0.995, high: p * 1.01, low: p * 0.99, close: p, volume: 1_000_000,
    }
  })
}

describe('viewport — the window follows the cursor', () => {
  it('shows the last N sessions, not the whole revealed series', () => {
    const v = viewport(400, 200, 63)
    expect(v.span).toBe(63)
    expect(v.to).toBe(200)
    expect(v.from).toBe(138)
  })

  it('keeps the span constant as the replay advances', () => {
    const a = viewport(400, 100, 63)
    const b = viewport(400, 300, 63)
    expect(a.span).toBe(b.span)
  })

  it('never reaches past the cursor', () => {
    expect(viewport(400, 50, 63).to).toBe(50)
  })

  it('falls back to what is revealed when the window is longer', () => {
    const v = viewport(400, 20, 63)
    expect(v.from).toBe(0)
    expect(v.span).toBe(21)
  })

  it('window 0 means everything revealed so far, still not the future', () => {
    const v = viewport(400, 150, 0)
    expect(v.from).toBe(0)
    expect(v.to).toBe(150)
    expect(v.span).toBe(151)
  })

  it('leaves room to the right of the newest bar', () => {
    expect(viewport(400, 200, 63).domain).toBeGreaterThan(63)
  })
})

describe('priceRange — the axis must not leak the ending', () => {
  it('ignores bars past the cursor', () => {
    const b = bars(300, i => (i < 150 ? 10 : 1000))
    const r = priceRange(b, 0, 149)
    expect(r.hi).toBeLessThan(20)
  })

  it('takes in the new high once the replay reaches it', () => {
    const b = bars(300, i => (i < 150 ? 10 : 1000))
    expect(priceRange(b, 0, 200).hi).toBeGreaterThan(900)
  })

  it('pads, so the extreme bar is not flush with the frame', () => {
    const r = priceRange(bars(50), 0, 49)
    const rawHigh = Math.max(...bars(50).map(x => x.high))
    expect(r.hi).toBeGreaterThan(rawHigh)
  })

  it('returns null on an empty slice rather than Infinity', () => {
    expect(priceRange([], 0, 0)).toBeNull()
  })
})

describe('openingCursor — open on the base, not mid-flight', () => {
  it('opens about two months before the breakout', () => {
    expect(openingCursor({ bars: bars(300), pivot: 150 })).toBe(105)
  })

  it('never opens so early that no moving average exists', () => {
    expect(openingCursor({ bars: bars(300), pivot: 60 })).toBe(55)
  })

  it('falls back to a third of the way in with no breakout', () => {
    expect(openingCursor({ bars: bars(300), pivot: null })).toBe(90)
  })

  it('stays inside a short series', () => {
    expect(openingCursor({ bars: bars(30), pivot: null })).toBe(29)
  })
})

describe('acts — the stated breakout and ours, both', () => {
  const b = bars(300)

  it('marks the author\'s breakout when the model book states one', () => {
    const a = acts({ bars: b, low: 0, peak: 299, computed: 150,
                     stated: { date: b[100].time, price: 20, book: 'TraderLion' } })
    const stated = a.find(x => x.kind === 'stated')
    expect(stated).toMatchObject({ key: 'pivot', index: 100, book: 'TraderLion' })
  })

  it('shows ours as well when the two disagree', () => {
    const a = acts({ bars: b, low: 0, peak: 299, computed: 150,
                     stated: { date: b[100].time } })
    expect(a.filter(x => x.key === 'pivot')).toHaveLength(2)
  })

  it('does not print the same breakout twice when they agree', () => {
    const a = acts({ bars: b, low: 0, peak: 299, computed: 101,
                     stated: { date: b[100].time } })
    expect(a.filter(x => x.key === 'pivot')).toHaveLength(1)
  })

  it('marks nothing for a breakout that was never found', () => {
    const a = acts({ bars: b, low: 0, peak: 299, computed: null, stated: null })
    expect(a.some(x => x.key === 'pivot')).toBe(false)
  })

  it('drops a stated date that falls outside the bars we hold', () => {
    const a = acts({ bars: b, low: 0, peak: 299, computed: null,
                     stated: { date: '2099-01-01' } })
    expect(a.some(x => x.kind === 'stated')).toBe(false)
  })
})

describe('readout — null, never a confident zero', () => {
  it('withholds the 50-day distance before there are 50 bars', () => {
    expect(readout({ bars: bars(300), cursor: 20 }).vs50dPct).toBeNull()
  })

  it('gives it once there are', () => {
    expect(readout({ bars: bars(300), cursor: 60 }).vs50dPct).toBeGreaterThan(0)
  })

  it('withholds the advance before the breakout', () => {
    expect(readout({ bars: bars(300), cursor: 100, pivotIndex: 150 }).sincePivotPct).toBeNull()
  })

  it('measures the advance from the breakout close', () => {
    const b = bars(300)
    const r = readout({ bars: b, cursor: 200, pivotIndex: 150 })
    expect(r.sincePivotPct).toBeCloseTo((b[200].close / b[150].close - 1) * 100, 6)
  })

  it('measures the drawdown against the high SO FAR, not the final high', () => {
    const b = bars(300, i => (i < 100 ? 10 + i * 0.1 : 5))
    expect(readout({ bars: b, cursor: 120 }).fromHighPct).toBeLessThan(-40)
    // and the cursor at bar 50 cannot know about the collapse at 100
    expect(readout({ bars: b, cursor: 50 }).fromHighPct).toBeCloseTo(0, 6)
  })

  it('counts what is left rather than how far it has come', () => {
    expect(readout({ bars: bars(300), cursor: 100 }).barsLeft).toBe(199)
  })
})

describe('compareEntries — ranking by what was takeable', () => {
  const rows = [
    { id: 'a', advance_pct: 120, gain_pct: 9000 },
    { id: 'b', advance_pct: 300, gain_pct: 50 },
    { id: 'c', advance_pct: null, gain_pct: 99999 },
  ]

  it('puts the largest advance first', () => {
    const s = [...rows].sort((x, y) => compareEntries(x, y, 'advance_pct', 'desc'))
    expect(s.map(r => r.id)).toEqual(['b', 'a', 'c'])
  })

  it('sinks entries with no breakout instead of borrowing the other column', () => {
    const s = [...rows].sort((x, y) => compareEntries(x, y, 'advance_pct', 'desc'))
    expect(s.at(-1).id).toBe('c')
  })

  it('still sorts by the stated gain when that column is asked for', () => {
    const s = [...rows].sort((x, y) => compareEntries(x, y, 'gain_pct', 'desc'))
    expect(s.map(r => r.id)).toEqual(['c', 'a', 'b'])
  })
})

describe('moving averages', () => {
  it('emits null until the period is filled', () => {
    expect(sma([1, 2, 3, 4], 3).slice(0, 2)).toEqual([null, null])
    expect(ema([1, 2, 3, 4], 3).slice(0, 2)).toEqual([null, null])
  })

  it('seeds the EMA with a simple average of the first window', () => {
    expect(ema([1, 2, 3, 4], 3)[2]).toBeCloseTo(2, 10)
  })
})
