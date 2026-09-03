import { describe, it, expect } from 'vitest'
import {
  questionOf, questionLists, wkAccel, stateCounts, summaryParts, defaultPicks, sideChanges, fastest,
  positionAt, spreadLabels, swarmLevels, measurable, DEFAULT_THRESHOLDS,
} from './rotationLogic'
import { changeOf } from '../groups/stateChange'

const base = { group: 'X', state: 'Improving', excess_3m: -0.1, rs_3m_6m: -0.2, rs_1m_3m: -0.05, rs_1w_1m: 0.0, rs_0_1w: 0.03, rs_accel: 0.1, rs_accel_rate: 0.05, persistence: 1 }

describe('questionOf — the three shapes', () => {
  it('② igniting: weak for months, quiet 3w, this week up and faster', () => {
    expect(questionOf(base)).toBe('q2')
  })
  it('① building: prior 3w up, this week up and not slower, not strong 1–3m ago', () => {
    expect(questionOf({ ...base, rs_1w_1m: 0.03, rs_0_1w: 0.02, rs_1m_3m: 0.01 })).toBe('q1')
  })
  it('① is refused when the theme was already strong 1–3m ago (the cap)', () => {
    const r = { ...base, rs_1w_1m: 0.03, rs_0_1w: 0.02, rs_1m_3m: 0.2 }
    expect(questionOf(r)).not.toBe('q1')
    expect(questionOf(r, { ...DEFAULT_THRESHOLDS, q1PriorCap: 0.3 })).toBe('q1')
  })
  it('③ fading: ahead for months, slope negative, still slowing', () => {
    expect(questionOf({ ...base, excess_3m: 0.2, rs_1m_3m: 0.1, rs_accel_rate: -0.04, rs_0_1w: -0.01, rs_1w_1m: 0.02 })).toBe('q3')
  })
  it('a steady traveller is in no list', () => {
    expect(questionOf({ ...base, excess_3m: 0.2, rs_1m_3m: 0.1, rs_accel_rate: 0.02, rs_0_1w: 0.01, rs_1w_1m: 0.03 })).toBeNull()
  })
  it('an unmeasured group is never classified — absence is not a shape', () => {
    expect(questionOf({ ...base, rs_3m_6m: null })).toBeNull()
    expect(measurable({ ...base, excess_3m: undefined })).toBe(false)
  })
})

describe('lists, defaults and the headline', () => {
  const rows = [
    { ...base, group: 'Ign A', rs_0_1w: 0.04 },
    { ...base, group: 'Ign B', rs_0_1w: 0.01 },
    { ...base, group: 'Fade', state: 'Weakening', excess_3m: 0.2, rs_1m_3m: 0.1, rs_accel_rate: -0.04, rs_0_1w: -0.01, rs_1w_1m: 0.02 },
    { ...base, group: 'Still', state: 'Leading', excess_3m: 0.2, rs_1m_3m: 0.1, rs_accel_rate: 0.02, rs_0_1w: 0.01, rs_1w_1m: 0.03 },
  ]
  it('orders each list by the strength of its own turn', () => {
    const l = questionLists(rows)
    expect(l.q2.map((r) => r.group)).toEqual(['Ign A', 'Ign B'])
    expect(l.q3.map((r) => r.group)).toEqual(['Fade'])
    expect(l.q1).toEqual([])
  })
  it('defaults are the top of each question, in question order', () => {
    expect(defaultPicks(questionLists(rows)).map((r) => r.group)).toEqual(['Ign A', 'Fade'])
  })
  it('the headline is names, never counts', () => {
    const parts = summaryParts(questionLists(rows))
    expect(parts[0]).toEqual({ text: 'Igniting: ', strong: 'Ign A, Ign B.' })
    expect(parts.some((p) => /\d/.test(p.text))).toBe(false)
    expect(summaryParts({ q1: [], q2: [], q3: [] })[0].text).toBe('Nothing is turning today.')
  })
  it('wkAccel is this week minus the prior three weeks per week', () => {
    expect(wkAccel({ rs_0_1w: 0.05, rs_1w_1m: 0.032 })).toBeCloseTo(0.04, 6)
  })
  it('fastest names the movers on both ends and never a zero mover', () => {
    const f = fastest(rows, 2, 1)
    expect(f.up.map((r) => r.group)).toEqual(['Ign A', 'Ign B'])
    expect(f.down.map((r) => r.group)).toEqual(['Fade'])
  })
})

describe('history', () => {
  const hist = { A: { state: ['Lagging', 'Improving', 'Leading'], excess: [-0.1, 0, 0.1], rs_accel: [0, 0.1, 0.2] }, B: { state: ['Leading', 'Leading', 'Weakening'], excess: [0.2, 0.2, 0.2], rs_accel: [0.1, 0.1, -0.1] } }
  const historyOf = (n) => hist[n] ?? null
  const rows = [{ group: 'A' }, { group: 'B' }, { group: 'C' }]
  it('counts states at a session, skipping groups with no row that day', () => {
    expect(stateCounts(rows, historyOf, 0)).toEqual({ Leading: 1, Improving: 0, Weakening: 0, Lagging: 1 })
  })
  it('names who changed sides over the window ending at a session', () => {
    expect(sideChanges(rows, historyOf, 2, changeOf, 5)).toEqual({ up: ['A'], down: ['B'] })
    expect(sideChanges(rows, historyOf, 0, changeOf, 5)).toEqual({ up: [], down: [] })
  })
  it('positionAt interpolates between sessions and holds at the ends', () => {
    expect(positionAt(hist.A, 0.5)).toEqual({ x: -0.05, y: 0.05, state: 'Lagging' })
    expect(positionAt(hist.A, 2)).toEqual({ x: 0.1, y: 0.2, state: 'Leading' })
    expect(positionAt(hist.A, 9)).toEqual({ x: 0.1, y: 0.2, state: 'Leading' })
    expect(positionAt(null, 1)).toBeNull()
  })
})

describe('layout helpers', () => {
  it('spreadLabels keeps a gap and preserves order', () => {
    expect(spreadLabels([10, 12, 40], (v) => v, 14).map((e) => e.y)).toEqual([10, 24, 40])
  })
  it('swarmLevels steps neighbours outward deterministically', () => {
    expect(swarmLevels([0, 3, 6, 50], 10)).toEqual([0, 1, 2, 0])
  })
})
