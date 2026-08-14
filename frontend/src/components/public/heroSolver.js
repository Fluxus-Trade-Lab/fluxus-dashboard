/**
 * The hero field's solver — physics on the way, typography on arrival.
 *
 * The five stages are exact arrangements. Stage four's entire claim is that the
 * nodes are IDENTICAL and only the sizes differ, which a solver that merely
 * converges would quietly destroy: jittered nodes, and the two heavy circles at
 * the bottom of the V shoved apart by a collider when the poster has them
 * touching. So physics does not own the layout. It owns the transit.
 *
 *   at rest    stiffness is high and collisions are off — every circle lands on
 *              its authored coordinate, and the panel is the poster's panel
 *   in flight  stiffness drops and collisions come on — the circles fall into
 *              the next arrangement, bump each other, carry momentum
 *
 * `blend` is that dial, 0 at rest and 1 mid-flight. It rides the existing
 * hold/morph split rather than inventing a second clock.
 *
 * Why not rapier: 28 discs, two dimensions, circle-circle only, no joints, no
 * stacking, no gravity. A 130 kB wasm engine for that would also have to be
 * argued with about the arrive-exactly rule. Sixty lines is cheaper to run and
 * cheaper to reason about.
 *
 * Units are the field's unit square throughout (x right, y down, radius in
 * fractions of the side), so the solver never learns about pixels.
 */

/** Sub-steps are capped in size, not in count: a spring integrated with an
 *  explicit step goes unstable when stiffness × dt gets large, and dt is
 *  whatever the browser hands us. */
const MAX_DT = 1 / 120

const STIFF_REST = 46      // lands on the authored coordinate within a few frames
const STIFF_FLIGHT = 9     // loose enough to be pushed off course on the way

export function createBodies(n) {
  return Array.from({ length: n }, () => ({ x: 0.5, y: 0.5, vx: 0, vy: 0, r: 0 }))
}

/** Put every body exactly on its target, at rest. Used on the first frame and
 *  by the pinned review mode, where an approximation would be the wrong tool. */
export function snap(bodies, targets) {
  for (let i = 0; i < bodies.length; i++) {
    const b = bodies[i], t = targets[i]
    b.x = t[0]; b.y = t[1]; b.r = t[2]; b.vx = 0; b.vy = 0
  }
}

/**
 * @param bodies   mutated in place
 * @param targets  [[x, y, r], …] — same length and order as bodies
 * @param dt       seconds since the last step
 * @param blend    0 = at rest (exact, no collisions), 1 = mid-flight
 * @param pointer  {x, y, r, force} in unit-square coords, or null
 */
export function step(bodies, targets, dt, blend, pointer) {
  if (!(dt > 0)) return
  const steps = Math.max(1, Math.ceil(dt / MAX_DT))
  const h = dt / steps
  const k = STIFF_REST + (STIFF_FLIGHT - STIFF_REST) * blend
  const c = 2 * Math.sqrt(k)          // critically damped: settles without ringing

  for (let s = 0; s < steps; s++) {
    for (let i = 0; i < bodies.length; i++) {
      const b = bodies[i], t = targets[i]
      // Radius is not a physical quantity here — a circle does not get pushed
      // bigger — so it just tracks its target, exponentially by elapsed time.
      // Honest note: at 60 vs 144 Hz this is worth nothing, measured — the
      // sub-step is capped at 1/120 s either way, and the naive `* (h * 14)`
      // differs by well under a thousandth. It is here because that form is a
      // rate PER STEP and saturates once h passes 1/14 s, so it is only correct
      // by accident of the cap. This one is correct by construction.
      b.r += (t[2] - b.r) * (1 - Math.exp(-h * 14))
      b.vx += (-k * (b.x - t[0]) - c * b.vx) * h
      b.vy += (-k * (b.y - t[1]) - c * b.vy) * h
      b.x += b.vx * h
      b.y += b.vy * h
    }

    if (blend > 0.001) {
      // Collisions only in flight, and scaled by blend, so an arrangement the
      // poster draws touching is not pried apart once it has settled.
      for (let i = 0; i < bodies.length; i++) {
        const a = bodies[i]
        if (a.r <= 0) continue
        for (let j = i + 1; j < bodies.length; j++) {
          const b = bodies[j]
          if (b.r <= 0) continue
          const dx = b.x - a.x, dy = b.y - a.y
          const d2 = dx * dx + dy * dy
          const min = a.r + b.r
          if (d2 >= min * min || d2 === 0) continue
          const d = Math.sqrt(d2)
          const push = ((min - d) / d) * 0.5 * blend
          const px = dx * push, py = dy * push
          a.x -= px; a.y -= py
          b.x += px; b.y += py
        }
      }
    }

    if (pointer && pointer.force > 0) {
      for (let i = 0; i < bodies.length; i++) {
        const b = bodies[i]
        if (b.r <= 0) continue
        const dx = b.x - pointer.x, dy = b.y - pointer.y
        const d = Math.hypot(dx, dy)
        const reach = pointer.r + b.r
        if (d >= reach || d === 0) continue
        // falls off to nothing at the edge of reach, so nothing snaps as the
        // cursor crosses it
        const f = (1 - d / reach) * pointer.force * h
        b.vx += (dx / d) * f
        b.vy += (dy / d) * f
      }
    }
  }
}
