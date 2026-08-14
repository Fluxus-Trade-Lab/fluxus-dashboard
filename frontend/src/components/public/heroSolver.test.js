import { describe, it, expect } from 'vitest'
import { createBodies, snap, step } from './heroSolver'
import { STAGES, BLUE_N, RED_N } from './heroStages'

const run = (bodies, targets, seconds, blend, pointer = null, dt = 1 / 60) => {
  for (let t = 0; t < seconds; t += dt) step(bodies, targets, dt, blend, pointer)
}

describe('hero solver', () => {
  it('arrives exactly at rest — the panel has to be the poster panel', () => {
    const targets = [[0.2, 0.3, 0.05], [0.8, 0.7, 0.04]]
    const b = createBodies(2)
    snap(b, [[0.5, 0.5, 0], [0.5, 0.5, 0]])
    run(b, targets, 2, 0)
    for (let i = 0; i < 2; i++) {
      expect(b[i].x).toBeCloseTo(targets[i][0], 4)
      expect(b[i].y).toBeCloseTo(targets[i][1], 4)
      expect(b[i].r).toBeCloseTo(targets[i][2], 4)
    }
  })

  it('does not pry apart circles the poster draws touching', () => {
    // stage 0 has the two heavy circles at the turn overlapping, as on the
    // poster. Settled, that must survive.
    const targets = [[0.30, 0.57, 0.086], [0.34, 0.60, 0.066]]
    const b = createBodies(2)
    snap(b, targets)
    run(b, targets, 2, 0)
    const d = Math.hypot(b[0].x - b[1].x, b[0].y - b[1].y)
    expect(d).toBeLessThan(targets[0][2] + targets[1][2])   // still overlapping
  })

  it('separates overlapping circles while in flight', () => {
    const targets = [[0.5, 0.5, 0.1], [0.5, 0.5, 0.1]]
    const b = createBodies(2)
    snap(b, [[0.49, 0.5, 0.1], [0.51, 0.5, 0.1]])
    run(b, targets, 0.5, 1)
    const d = Math.hypot(b[0].x - b[1].x, b[0].y - b[1].y)
    expect(d).toBeGreaterThan(0.02)     // pushed apart, not left stacked
  })

  it('stays finite through every stage transition at a punishing step', () => {
    // 100 ms is the clamp HeroField applies after a sleeping tab; the solver
    // sub-steps internally, and must not go unstable at that size.
    const n = BLUE_N + RED_N
    const b = createBodies(n)
    const targetsFor = (s) => [...STAGES[s].blue, ...STAGES[s].red]
    snap(b, targetsFor(0))
    for (let s = 0; s < STAGES.length; s++) {
      const t = targetsFor((s + 1) % STAGES.length)
      for (let i = 0; i < 40; i++) step(b, t, 0.1, 1, { x: 0.5, y: 0.5, r: 0.3, force: 4 })
      for (let i = 0; i < 40; i++) step(b, t, 0.1, 0, null)
    }
    for (const x of b) {
      expect(Number.isFinite(x.x)).toBe(true)
      expect(Number.isFinite(x.y)).toBe(true)
      expect(Math.abs(x.x)).toBeLessThan(10)
      expect(Math.abs(x.y)).toBeLessThan(10)
    }
  })

  it('is frame-rate independent to within a pixel', () => {
    // 60 Hz and 144 Hz must not give two different animations. What this
    // actually guards is the integration being per-SECOND: drop the `* h` from
    // the velocity update and the two rates diverge by whole tenths of the
    // square. It cannot demand bit-identity, because the sub-step size differs
    // between the two and explicit integration carries that through — so the
    // bar is where it shows: the field is at most ~900 px across, and 0.002 of
    // the unit square is under two pixels there.
    const targets = [[0.9, 0.1, 0.05]]
    const a = createBodies(1), c = createBodies(1)
    snap(a, [[0.1, 0.9, 0.008]]); snap(c, [[0.1, 0.9, 0.008]])
    run(a, targets, 1, 0.5, null, 1 / 60)
    run(c, targets, 1, 0.5, null, 1 / 144)
    expect(Math.abs(a[0].x - c[0].x)).toBeLessThan(0.002)
    expect(Math.abs(a[0].y - c[0].y)).toBeLessThan(0.002)
    expect(Math.abs(a[0].r - c[0].r)).toBeLessThan(0.002)
  })

  it('leaves parked circles alone — radius zero is not a body', () => {
    const targets = [[0.5, 0.5, 0], [0.5, 0.5, 0.1]]
    const b = createBodies(2)
    snap(b, targets)
    run(b, targets, 0.5, 1, { x: 0.5, y: 0.5, r: 0.3, force: 8 })
    expect(b[0].x).toBeCloseTo(0.5, 6)   // untouched by pointer or collision
    expect(b[0].y).toBeCloseTo(0.5, 6)
  })
})
