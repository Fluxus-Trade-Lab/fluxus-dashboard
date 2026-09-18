import { describe, it, expect } from 'vitest'
/* global __dirname */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { ENGINE_LINES, t2108Level } from './BreadthTable.jsx'

// The table's tints copy the engine's lines. Read the engine, so the copy
// cannot drift the way the old 60/40 ruler did.
const py = readFileSync(resolve(__dirname, '../../../../pipeline/screeners/breadth_signals.py'), 'utf8')
const line = (key) => {
  const m = py.match(new RegExp(`'${key}':\\s*\\{([^}]*)\\}`))
  return Object.fromEntries([...m[1].matchAll(/'(\w+)':\s*([\d.]+)/g)].map(([, k, v]) => [k, Number(v)]))
}

describe('BreadthTable tints follow breadth_signals.THRESHOLDS', () => {
  it('ratio lines', () => {
    expect(line('ratio_5d')).toEqual(ENGINE_LINES.ratio5)
    const { strict, ...r10 } = ENGINE_LINES.ratio10
    expect(line('ratio_10d')).toEqual(r10)
    expect(strict).toBe(/'ratio_10d':[^}]*'strict':\s*True/.test(py))
  })
  it('%>200 lines are 50/30', () => {
    expect(line('pct200')).toEqual(ENGINE_LINES.pct200)
  })
  it('T2108 zone lines', () => {
    const z = line('t2108_zone')
    expect(z).toEqual({ strong_lo: ENGINE_LINES.t2108.strongLo, weak_hi: ENGINE_LINES.t2108.weakHi,
      oversold: ENGINE_LINES.t2108.oversold, overbought: ENGINE_LINES.t2108.overbought })
  })
  it('T2108 levels mirror the engine vote', () => {
    expect(t2108Level(65)).toBe('high')
    expect(t2108Level(30)).toBe('low')
    expect(t2108Level(50)).toBe('mid')
    expect(t2108Level(15)).toBe('mid')
    expect(t2108Level(85)).toBe('mid')
  })
})
