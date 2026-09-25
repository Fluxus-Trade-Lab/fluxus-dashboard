import { describe, it, expect } from 'vitest'
import {
  judge, verdict, findPivot, extremes, preAdvanceDollarVolume, flatShare,
  PRICE_MAX, DOLLAR_VOL_MIN, VOL_MULT,
} from '../../../scripts/flag-modelbook-outliers.mjs'

/* A boring, believable series: a flat base, then a breakout on volume, then a
   run. Every test below starts from this and breaks exactly one thing, so a
   red test names the rule that caught it. */
function series({ n = 260, base = 10, volume = 500_000 } = {}) {
  const bars = []
  for (let i = 0; i < n; i++) {
    // 120 bars of base around `base`, then a steady advance
    const p = i < 120 ? base * (1 + Math.sin(i / 7) * 0.02) : base * (1 + (i - 119) * 0.01)
    bars.push({
      time: `2020-${String(1 + (i % 12)).padStart(2, '0')}-${String(1 + (i % 28)).padStart(2, '0')}`,
      open: +(p * 0.995).toFixed(4),
      high: +(p * 1.01).toFixed(4),
      low: +(p * 0.99).toFixed(4),
      close: +p.toFixed(4),
      volume,
    })
  }
  return bars
}

/** Make bar `i` a real breakout: above the prior 20 highs, on heavy volume. */
function breakoutAt(bars, i, volMult = 2) {
  const priorHigh = Math.max(...bars.slice(i - 20, i).map(b => b.high))
  const p = priorHigh * 1.05
  bars[i] = { ...bars[i], open: p * 0.99, high: p * 1.01, low: p * 0.98, close: p,
              volume: Math.round(bars[i].volume * volMult) }
  for (let k = i + 1; k < bars.length; k++) {
    const q = p * (1 + (k - i) * 0.01)
    bars[k] = { ...bars[k], open: q * 0.995, high: q * 1.01, low: q * 0.99, close: q }
  }
  return bars
}

describe('judge — the shape gate, unchanged behaviour', () => {
  it('passes a believable series', () => {
    expect(judge(series(), 150)).toBeNull()
  })

  it('catches a reverse split as a one-day jump', () => {
    const bars = series()
    // 1-for-15: every bar from here on is 15x the last
    for (let i = 200; i < bars.length; i++) {
      bars[i] = { ...bars[i], open: bars[i].open * 15, high: bars[i].high * 15,
                  low: bars[i].low * 15, close: bars[i].close * 15 }
    }
    expect(judge(bars, null)).toMatch(/one-day jump/)
  })

  it('catches a stated gain its own bars cannot contain', () => {
    // bars span about 2.4x; the entry claims 85x
    expect(judge(series(), 8400)).toMatch(/exceeds its bars/)
  })
})

describe('impossible price', () => {
  it('excludes a bar priced above the ceiling', () => {
    const bars = series()
    bars[3] = { ...bars[3], high: PRICE_MAX * 2 }
    expect(verdict({ id: 'x', ticker: 'X', year: 2020 }, bars, 'h1', new Map()))
      .toMatchObject({ rule: 'impossible_price' })
  })

  it('leaves an expensive but real stock alone (BRK.A territory)', () => {
    // BRK.A trades near $700k today; the ceiling is about adjusted history
    // running to the billions, so a merely expensive listing must pass.
    const bars = series({ base: 20_000, volume: 2_000 })
    expect(Math.max(...bars.map(b => b.high))).toBeLessThan(PRICE_MAX)
    expect(verdict({ id: 'x', ticker: 'BRKA', year: 2020 }, bars, 'h1', new Map())).toBeNull()
  })
})

describe('untradable at the buy point', () => {
  it('excludes a name whose pre-advance dollar volume is below the floor', () => {
    // $0.20 x 200,000 shares = $40,000 a day
    const bars = series({ base: 0.2, volume: 200_000 })
    expect(preAdvanceDollarVolume(bars)).toBeLessThan(DOLLAR_VOL_MIN)
    expect(verdict({ id: 'x', ticker: 'GNUS', year: 2020 }, bars, 'h1', new Map()))
      .toMatchObject({ rule: 'untradable' })
  })

  it('keeps a split-adjusted classic priced in pennies but traded in size', () => {
    // HD 1982's shape: $0.04 a share adjusted, but 12M shares = $480k a day
    const bars = series({ base: 0.04, volume: 12_000_000 })
    expect(preAdvanceDollarVolume(bars)).toBeGreaterThan(DOLLAR_VOL_MIN)
    expect(verdict({ id: 'x', ticker: 'HD', year: 1982 }, bars, 'h1', new Map())).toBeNull()
  })

  it('measures dollar volume, so a split cannot change the verdict', () => {
    const bars = series({ base: 10, volume: 100_000 })
    const split = bars.map(b => ({ ...b, open: b.open / 10, high: b.high / 10,
      low: b.low / 10, close: b.close / 10, volume: b.volume * 10 }))
    expect(preAdvanceDollarVolume(split)).toBeCloseTo(preAdvanceDollarVolume(bars), 0)
  })
})

describe('duplicate', () => {
  it('keeps the first id and excludes the second with the same bars', () => {
    const seen = new Map()
    const bars = series()
    expect(verdict({ id: 'a', ticker: 'SSC', year: 2000 }, bars, 'same', seen)).toBeNull()
    expect(verdict({ id: 'b', ticker: 'WCST', year: 2000 }, bars, 'same', seen))
      .toMatchObject({ rule: 'duplicate', why: 'same bars as SSC 2000' })
  })

  it('does not fold two different entries that merely look alike', () => {
    const seen = new Map()
    expect(verdict({ id: 'a', ticker: 'A', year: 2020 }, series(), 'h1', seen)).toBeNull()
    expect(verdict({ id: 'b', ticker: 'B', year: 2021 }, series(), 'h2', seen)).toBeNull()
  })

  it('never claims a hash for an entry that was excluded first', () => {
    // an excluded entry must not block a later, valid one carrying the same bars
    const seen = new Map()
    const bars = series({ base: 0.2, volume: 200_000 })   // untradable
    expect(verdict({ id: 'a', ticker: 'A', year: 2020 }, bars, 'same', seen))
      .toMatchObject({ rule: 'untradable' })
    expect(seen.has('same')).toBe(false)
  })
})

describe('low resolution — flags, never excludes', () => {
  it('counts bars whose four prices are one number', () => {
    const bars = series()
    for (let i = 0; i < 200; i++) {
      bars[i] = { ...bars[i], open: 0.03, high: 0.03, low: 0.03, close: 0.03 }
    }
    expect(flatShare(bars)).toBeGreaterThan(0.5)
  })

  it('does not exclude the entry it flags', () => {
    const bars = series({ base: 0.04, volume: 12_000_000 })
      .map(b => ({ ...b, open: 0.04, high: 0.04, low: 0.04, close: 0.04 }))
    expect(flatShare(bars)).toBe(1)
    const v = verdict({ id: 'x', ticker: 'HD', year: 1982 }, bars, 'h1', new Map())
    expect(v?.rule).not.toBe('low_resolution')
  })
})

describe('pivot', () => {
  it('finds the breakout bar', () => {
    const bars = breakoutAt(series(), 140)
    expect(findPivot(bars)).toBe(140)
  })

  it('refuses a breakout that lacks the volume', () => {
    // price clears the base but volume is flat — O'Neil's +40% is the gate
    const bars = breakoutAt(series(), 140, 1.0)
    expect(findPivot(bars)).not.toBe(140)
  })

  it('takes the volume threshold from VOL_MULT, not a hardcoded number', () => {
    const just_under = breakoutAt(series(), 140, VOL_MULT * 0.95)
    const just_over = breakoutAt(series(), 140, VOL_MULT * 1.05)
    expect(findPivot(just_under)).not.toBe(140)
    expect(findPivot(just_over)).toBe(140)
  })

  it('returns null rather than inventing a breakout that is not there', () => {
    // a series that only ever drifts: no bar clears 20 sessions on volume
    const bars = series().map((b, i) => ({ ...b, open: 10, high: 10.01, low: 9.99, close: 10 }))
    expect(findPivot(bars)).toBeNull()
  })

  it('locates the low before the peak, not the low of the whole file', () => {
    const bars = breakoutAt(series(), 140)
    // crash after the peak, below anything seen before it
    for (let k = 250; k < bars.length; k++) {
      bars[k] = { ...bars[k], open: 1, high: 1, low: 1, close: 1 }
    }
    const { low, peak } = extremes(bars)
    expect(peak).toBeLessThan(250)
    expect(low).toBeLessThan(peak)
  })
})
