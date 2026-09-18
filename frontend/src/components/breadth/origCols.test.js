/* global __dirname */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { ORIG_COLS, orig } from './origCols'

const py = readFileSync(resolve(__dirname, '../../../../pipeline/screeners/breadth_signals.py'), 'utf8')

describe('origCols mirrors the engine column map', () => {
  it('thrust numerator', () => {
    const m = py.match(/THRUST_UP, THRUST_DOWN = '(\w+)', '(\w+)'/)
    expect([ORIG_COLS.up_4pct, ORIG_COLS.down_4pct]).toEqual([m[1], m[2]])
  })
  it('ratio columns', () => {
    expect(py).toContain(`'ratio_5d': '${ORIG_COLS.ratio_5d}'`)
    expect(py).toContain(`'ratio_10d': '${ORIG_COLS.ratio_10d}'`)
  })
  it('spread columns', () => {
    expect(py).toContain(`'qtr_spread': ('${ORIG_COLS.up_25pct_qtr}', '${ORIG_COLS.down_25pct_qtr}')`)
    expect(py).toContain(`'spread_13_34': ('${ORIG_COLS.up_13pct_34d}', '${ORIG_COLS.down_13pct_34d}')`)
    expect(py).toContain(`'nh_nl': ('${ORIG_COLS.new_highs}', '${ORIG_COLS.new_lows}')`)
  })
  it('falls back to the old column, flagged', () => {
    expect(orig({ ratio_5d: 0.8 }, 'ratio_5d')).toEqual({ v: 0.8, old: true })
    expect(orig({ ratio_5d: 0.8, ratio_5d_stockbee: 1.4 }, 'ratio_5d')).toEqual({ v: 1.4, old: false })
    expect(orig({}, 'ratio_5d')).toEqual({ v: null, old: false })
  })
})
