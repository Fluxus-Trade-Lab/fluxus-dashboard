import { describe, it, expect } from 'vitest'
import {
  wkAccel, r2wSeries, lastOf, boardsOf, defaultPicks, radius, pack, spreadLabels, smoothPath, windowBounds, visibleFrom, countsAt, namesByState,
  R2W_LAG, PRIOR_WEEKS, Y_MAX,
} from './rotationLogic'

const row = (group, o = {}) => ({ group, kind: 'theme', rs_0_1w: 0.02, rs_1w_1m: 0.03, excess_3m: 0.1, ...o })

describe('two-week strength from the relative index', () => {
  it('is rel[t] / rel[t − 10] − 1 and null inside the lag', () => {
    const rel = Array.from({ length: 15 }, (_, i) => 1 + i * 0.01)
    const s = r2wSeries(rel)
    expect(s.slice(0, R2W_LAG).every((v) => v === null)).toBe(true)
    expect(s[14]).toBeCloseTo(1.14 / 1.04 - 1, 10)
  })
  it('a hole in the index is a hole in the strength, not a zero', () => {
    const rel = Array.from({ length: 12 }, (_, i) => (i === 1 ? null : 1))
    expect(r2wSeries(rel)[11]).toBeNull()
    expect(r2wSeries(rel)[10]).toBe(0)
  })
  it('lastOf skips trailing nulls', () => {
    expect(lastOf([1, 2, null])).toBe(2)
    expect(lastOf([null])).toBeNull()
  })
})

describe('the three boards', () => {
  const rel = Array.from({ length: 12 }, (_, i) => 1 + i * 0.005)
  const seriesOf = (n) => (n === 'A' ? { rel } : null)
  it('rs2w reads the ladder when the group has a series, falls back and flags otherwise', () => {
    const b = boardsOf([row('A'), row('B', { rs_0_1w: 0.01, rs_1w_1m: 0.032 })], seriesOf)
    const a = b.rs2w.find((it) => it.r.group === 'A'), bb = b.rs2w.find((it) => it.r.group === 'B')
    expect(a.approx).toBe(false)
    expect(a.rs2w).toBeCloseTo(rel[11] / rel[1] - 1, 10)
    expect(bb.approx).toBe(true)
    expect(bb.rs2w).toBeCloseTo(0.01 + 0.032 / PRIOR_WEEKS, 10)
    expect(b.approx).toBe(true)
  })
  it('sorts each board descending and drops the unmeasurable', () => {
    const b = boardsOf([row('A', { excess_3m: 0.1 }), row('B', { excess_3m: 0.3 }), row('C', { excess_3m: null })], () => null)
    expect(b.long.map((it) => it.r.group)).toEqual(['B', 'A'])
  })
  it('acceleration is this week minus the prior three weeks per week', () => {
    expect(wkAccel({ rs_0_1w: 0.02, rs_1w_1m: 0.032 })).toBeCloseTo(0.01, 10)
  })
  it('default picks take the top of each board without repeating a name', () => {
    const b = boardsOf([row('A', { rs_0_1w: 0.05, excess_3m: 0.5 }), row('B', { rs_0_1w: 0.04, excess_3m: 0.4 }), row('C', { rs_0_1w: 0.001, rs_1w_1m: -0.05, excess_3m: 0.3 })], () => null)
    const picks = defaultPicks(b)
    expect(new Set(picks).size).toBe(picks.length)
    expect(picks.length).toBe(3)
  })
})

describe('dots on a strip', () => {
  it('radius runs 3.5 → 10 across the range', () => {
    expect(radius(-1, -1, 1)).toBe(3.5)
    expect(radius(1, -1, 1)).toBe(10)
    expect(radius(0, 0, 0)).toBe(3.5)
  })
  it('packing leaves no two circles overlapping, even in a dense cluster', () => {
    const items = Array.from({ length: 30 }, (_, i) => ({ y: 200 + (i % 7) * 2, r: 3.5 + (i % 5) }))
    const pos = pack(items, 70)
    for (let i = 0; i < pos.length; i += 1) {
      for (let j = i + 1; j < pos.length; j += 1) {
        expect(Math.hypot(pos[i].x - pos[j].x, pos[i].y - pos[j].y)).toBeGreaterThanOrEqual(items[i].r + items[j].r + 1.5 - 1e-9)
      }
    }
  })
  it('the biggest dot keeps the axis', () => {
    const pos = pack([{ y: 100, r: 4 }, { y: 100, r: 10 }], 70)
    expect(pos[1]).toEqual({ x: 70, y: 100 })
  })
  it('labels are pushed apart by the gap', () => {
    const out = spreadLabels([{ y: 10 }, { y: 12 }, { y: 40 }], (it) => it.y, 14)
    expect(out.map((e) => e.y)).toEqual([10, 24, 40])
  })
})

describe('the Flux line and its windows', () => {
  it('a smooth path starts at the first point and has one cubic per interval', () => {
    const d = smoothPath([[0, 0], [10, 5], [20, 0], [30, 5]])
    expect(d.startsWith('M0.0 0.0')).toBe(true)
    expect((d.match(/ C/g) || []).length).toBe(3)
  })
  it('calendar windows count back fourteen days from the latest session', () => {
    const dates = ['2026-08-03', '2026-08-10', '2026-08-17', '2026-08-24', '2026-08-31', '2026-09-02']
    expect(windowBounds(dates, 0)).toEqual({ start: 3, end: 5 })     // (08-19, 09-02]
    expect(windowBounds(dates, 1)).toEqual({ start: 1, end: 2 })     // (08-05, 08-19]
    expect(windowBounds(dates, 3)).toBeNull()
  })
  it('the y-axis is fixed at ±20% — a line added never rescales the others', () => {
    expect(Y_MAX).toBe(0.20)
  })
  it('Terrain draws only back to the oldest window the select can reach', () => {
    // a session a day for 100 days: the oldest window (8–10w ago) opens 70 days back
    const dates = Array.from({ length: 100 }, (_, i) => new Date(Date.UTC(2026, 5, 1) + i * 86400e3).toISOString().slice(0, 10))
    const from = visibleFrom(dates)
    const daysApart = (a, b) => (Date.parse(b) - Date.parse(a)) / 86400e3
    // the window is (D − 70d, D − 56d], so the session exactly 70 days out is outside it
    expect(daysApart(dates[from], dates[dates.length - 1])).toBe(69)
    expect(from).toBe(windowBounds(dates, 4).start)
  })
  it('a short archive stays whole rather than starting past its end', () => {
    expect(visibleFrom(['2026-09-01', '2026-09-02'])).toBe(0)
  })
  it('counts and names on a session', () => {
    const h = { Leading: [1, 2], Weakening: [0, 0], Improving: [3, 1], Lagging: [0, 1] }
    expect(countsAt(h, 1)).toEqual({ Leading: 2, Weakening: 0, Improving: 1, Lagging: 1 })
    const seriesOf = (n) => (n === 'A' ? { states_2w: ['Lagging', 'Leading'] } : null)
    const todayOf = (n) => (n === 'B' ? 'Improving' : null)
    expect(namesByState(['A', 'B'], seriesOf, todayOf, 1, 1)).toEqual({ byState: { Leading: ['A'], Weakening: [], Improving: ['B'], Lagging: [] }, known: true })
    expect(namesByState(['B'], seriesOf, todayOf, 0, 1).known).toBe(false)
  })
})
