import { describe, it, expect } from 'vitest'
import {
  questionOf, questionLists, wkAccel, stateCounts, summaryParts, defaultPicks,
  momentumKind, spreadLabels, swarmLevels, measurable, DEFAULT_THRESHOLDS,
} from './rotationLogic'

const base = { group: 'X', state: 'Improving', excess_3m: -0.1, rs_3m_6m: -0.2, rs_1m_3m: -0.05, rs_1w_1m: 0.0, rs_0_1w: 0.03, rs_accel: 0.1, rs_accel_rate: 0.05, persistence: 1 }

describe('questionOf — the three shapes', () => {
  it('② igniting: weak for months, quiet 3w, this week up and faster', () => {
    expect(questionOf(base)).toBe('q2')
  })
  it('① building: prior 3w up, this week up and not slower, not strong 1–3m ago', () => {
    const r = { ...base, rs_1w_1m: 0.03, rs_0_1w: 0.02, rs_1m_3m: 0.01 }
    expect(questionOf(r)).toBe('q1')
  })
  it('① is refused when the theme was already strong 1–3m ago (the cap)', () => {
    const r = { ...base, rs_1w_1m: 0.03, rs_0_1w: 0.02, rs_1m_3m: 0.2 }
    expect(questionOf(r)).not.toBe('q1')
    expect(questionOf(r, { ...DEFAULT_THRESHOLDS, q1PriorCap: 0.3 })).toBe('q1')
  })
  it('③ fading: ahead for months, slope negative, still slowing', () => {
    const r = { ...base, excess_3m: 0.2, rs_1m_3m: 0.1, rs_accel_rate: -0.04, rs_0_1w: -0.01, rs_1w_1m: 0.02 }
    expect(questionOf(r)).toBe('q3')
  })
  it('a steady traveller is in no list', () => {
    const r = { ...base, excess_3m: 0.2, rs_1m_3m: 0.1, rs_accel_rate: 0.02, rs_0_1w: 0.01, rs_1w_1m: 0.03 }
    expect(questionOf(r)).toBeNull()
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
  it('the headline carries counts and names only', () => {
    const parts = summaryParts(rows, questionLists(rows), stateCounts(rows, () => null))
    expect(parts[0].text).toBe('1 leading, 0 lagging of 4.')
    expect(parts.find((p) => p.text.startsWith('Igniting')).strong).toBe('Ign A, Ign B.')
    expect(parts.some((p) => p.text.startsWith('Building'))).toBe(false)
  })
  it('wkAccel is this week minus the prior three weeks per week', () => {
    expect(wkAccel({ rs_0_1w: 0.05, rs_1w_1m: 0.032 })).toBeCloseTo(0.04, 6)
  })
  it('momentum kinds follow Andy\'s two kinds plus the edges', () => {
    expect(momentumKind({ ...base, persistence: 4 }, 'q1')).toBe('persistent')
    expect(momentumKind({ ...base, rs_0_1w: 0.05 }, 'q2')).toBe('burst')
    expect(momentumKind(base, 'q3')).toBe('fading')
    expect(momentumKind({ ...base, rs_0_1w: 0.01 }, 'q2')).toBe('starting')
  })
})

describe('history counts', () => {
  it('counts states at a session from the history, skipping groups with no row that day', () => {
    const hist = { A: { state: ['Leading', 'Leading'] }, B: { state: ['Lagging', null] } }
    const rows = [{ group: 'A' }, { group: 'B' }, { group: 'C' }]
    expect(stateCounts(rows, (n) => hist[n] ?? null, 0)).toEqual({ Leading: 1, Improving: 0, Weakening: 0, Lagging: 1 })
    expect(stateCounts(rows, (n) => hist[n] ?? null, 1)).toEqual({ Leading: 1, Improving: 0, Weakening: 0, Lagging: 0 })
  })
})

describe('layout helpers', () => {
  it('spreadLabels keeps a gap and preserves order', () => {
    const out = spreadLabels([10, 12, 40], (v) => v, 14)
    expect(out.map((e) => e.y)).toEqual([10, 24, 40])
  })
  it('swarmLevels steps neighbours outward deterministically', () => {
    expect(swarmLevels([0, 3, 6, 50], 10)).toEqual([0, 1, 2, 0])
  })
})
