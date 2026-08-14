import { useEffect, useRef, useState } from 'react'
import {
  STAGES, BLUE_N, RED_N, PARK, TRIANGLE, TAIJI, FUNNEL_LINKS, GRID_LINES,
} from './heroStages'
import { createBodies, snap, step as solve } from './heroSolver'
import { parsePinnedStage } from './parsePinnedStage'

/**
 * The hero's field — the Masterclass poster's five panels, as one motion.
 *
 * The blue and red circles on this page were copied off the poster, but only
 * the *look* of them: six divs at fixed offsets, a still photograph of a
 * diagram. The poster's circles are not decoration. They are five diagrams,
 * one per day of the course, each a metaphor for a stage of the method:
 *
 *   1  reversal        a descent, a floor, a climb — and the green triangle
 *                      marking the turn
 *   2  the funnel      many names at the top, curved down through the screens,
 *                      one leader at the bottom
 *   3  the scatter     setups strewn across the market; different strategies
 *                      find different ones
 *   4  the grid        the same nodes, wildly different circle sizes — size is
 *                      risk, and that is the whole lesson of the day
 *   5  taiji           long against short, each carrying a seed of the other
 *
 * So the field does not drift at random. It holds each stage, then morphs into
 * the next, and the same circles carry through all five — which is the honest
 * claim: it is one body of capital passing through five stages, not five
 * unrelated pictures.
 *
 * ── Why this is allowed here and nowhere else ────────────────────────────────
 * This is the marketing half, which runs on its own track: its own palette
 * (--color-poster-*), exempt from the encoding discipline, because nothing on
 * it is a measurement. That exemption is the entire licence. The same thing
 * inside the dashboard would break the one property every chart there depends
 * on — that equal lengths look equal. Here a circle's size is a metaphor. There
 * it would be a number, and a number read through perspective is a lie.
 *
 * ── What it must not do ─────────────────────────────────────────────────────
 * Anti-dopamine: one full cycle takes 29 seconds, nothing pulses, and the only
 * response to the reader is a heavily damped parallax. A visitor sees two
 * stages and has to stay to see the rest — which is the point of a curriculum.
 *
 * ── Degrading ───────────────────────────────────────────────────────────────
 * The CSS dots are the floor, not the thing being replaced. They paint at once
 * and stay painted until a context is proven running, so no WebGL, a refused
 * context, a failed chunk, or a lost context all leave the hero looking the way
 * it looks today rather than an empty black band. `prefers-reduced-motion`
 * draws stage one and stops.
 *
 * three arrives by dynamic import, so it lands in its own chunk and the
 * dashboard half of the bundle never pays for it.
 */

/** The six clusters this hero has had until now — the floor. */
const DOTS = [
  { cls: 'hero-dot-blue', size: 280, top: -60, right: -40 },
  { cls: 'hero-dot-red', size: 180, top: 80, right: 120 },
  { cls: 'hero-dot-blue', size: 100, bottom: 20, left: '15%' },
  { cls: 'hero-dot-red', size: 60, top: 40, left: '10%' },
  { cls: 'hero-dot-blue', size: 40, bottom: 60, right: '30%' },
  { cls: 'hero-dot-red', size: 140, bottom: -40, left: '40%' },
]

const HOLD = 3.4      // seconds a stage is held
const MORPH = 2.4     // seconds spent becoming the next one
const SEG = HOLD + MORPH
const HOLD_F = HOLD / SEG

// A turn and a half, unwound as the taiji lands — and it LANDS, at exactly
// zero, eyes vertical, the poster's own orientation. The first version kept
// turning forever (one lap per hundred seconds, "a contest does not finish"),
// which meant the resting form was a random angle: Andy caught it at 90° and
// the figure read as two eyes side by side instead of the poster's panel. The
// poster is the spec; the story loses.
const SPIN_IN = Math.PI * 3
const POINTER_TAU = 0.42         // seconds for the pointer lag to decay by 1/e

/** Smootherstep — zero velocity AND zero acceleration at both ends, so a stage
 *  settles instead of arriving. */
const ease = (x) => x * x * x * (x * (x * 6 - 15) + 10)

function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}

export default function HeroField() {
  const hostRef = useRef(null)
  const [live, setLive] = useState(false)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return

    let disposed = false
    let teardown = null

    const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // ?stage=0..4 holds one stage and never starts the loop. It exists because
    // the five panels have to be reviewable one at a time — a 29-second cycle
    // is no way to judge a layout — and because requestAnimationFrame does not
    // fire in every embedded browser, which makes the running version
    // unobservable in exactly the places you would want to check it.
    const pinned = parsePinnedStage(window.location.search, STAGES.length)

    ;(async () => {
      let THREE
      try { THREE = await import('three') } catch { return }
      if (disposed) return

      let renderer
      try {
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' })
      } catch { return }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))

      const canvas = renderer.domElement
      canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block'
      const onLost = (e) => { e.preventDefault(); setLive(false) }
      canvas.addEventListener('webglcontextlost', onLost)

      const scene = new THREE.Scene()
      // Orthographic: the poster's circles are flat and hard-edged, and a
      // perspective camera would make the same radius render at two sizes.
      // Depth here orders the painting; it is not a third dimension to read.
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 10)
      camera.position.z = 5

      const BLUE = new THREE.Color(cssVar('--color-poster-blue', '#3b82c4'))
      const RED = new THREE.Color(cssVar('--color-poster-red', '#d94032'))
      const GREEN = new THREE.Color(cssVar('--color-poster-green', '#22c55e'))

      const disc = new THREE.CircleGeometry(1, 64)
      const half = new THREE.CircleGeometry(1, 64, Math.PI / 2, Math.PI)   // left half
      const tri = new THREE.CircleGeometry(1, 3)

      const mat = (colour) => new THREE.MeshBasicMaterial({
        color: colour, transparent: true, opacity: 1, depthWrite: false, depthTest: false,
      })
      const owned = []
      // Everything is drawn on ONE plane at z = 0 and ordered by renderOrder,
      // never by depth. Stacking meshes along z would have put the taiji's last
      // three pieces past the near plane and clipped them out of the scene —
      // and with depthTest off, z was never buying the ordering anyway.
      const mesh = (geo, colour, order, parent = scene) => {
        const m = mat(colour)
        owned.push(m)
        const o = new THREE.Mesh(geo, m)
        o.renderOrder = order
        o.frustumCulled = false
        parent.add(o)
        return o
      }

      const blues = Array.from({ length: BLUE_N }, () => mesh(disc, BLUE, 1))
      const reds = Array.from({ length: RED_N }, () => mesh(disc, RED, 1))

      // stage 1's marker for the turn — the only green on the page
      const triangle = mesh(tri, GREEN, 3)

      // Stage 5, built as one rigid assembly so it can TURN. Two colours that
      // rotate and settle into the figure say the thing a cross-fade cannot:
      // long and short are not two states, they are one contest in motion, and
      // the shape only resolves when it stops. It keeps turning after it lands,
      // one revolution every hundred seconds — a contest does not finish.
      //
      // Painted back to front: the two halves, the two lobes that bend the seam
      // into an S, then each side's seed of the other. Children are positioned
      // in unit-square units about the centre, and the group carries the scale,
      // so the rotation is a single number rather than six.
      const taiji = new THREE.Group()
      scene.add(taiji)
      const taijiParts = {
        left: mesh(half, BLUE, 4, taiji),
        right: mesh(half, RED, 5, taiji),
        lobeA: mesh(disc, RED, 6, taiji),
        lobeB: mesh(disc, BLUE, 7, taiji),
        seedA: mesh(disc, BLUE, 8, taiji),
        seedB: mesh(disc, RED, 9, taiji),
      }
      taijiParts.right.rotation.z = Math.PI   // mirror the half onto the other side
      {
        const r = TAIJI.r
        const at = (o, y, s) => { o.position.set(0, y, 0); o.scale.set(s, s, 1) }
        at(taijiParts.left, 0, r)
        at(taijiParts.right, 0, r)
        at(taijiParts.lobeA, r / 2, r / 2)
        at(taijiParts.lobeB, -r / 2, r / 2)
        at(taijiParts.seedA, r / 2, r / 6)
        at(taijiParts.seedB, -r / 2, r / 6)
      }

      // The connective tissue — stage 1's links and stage 3's rules. Both are
      // built once in the unit square (x right, y down, origin at the centre)
      // and carried by a group that is scaled and placed with the box, so a
      // resize never touches a vertex.
      const lineMat = () => {
        const m = new THREE.LineBasicMaterial({
          color: 0x8c847a, transparent: true, opacity: 0, depthWrite: false, depthTest: false,
        })
        owned.push(m)
        return m
      }
      const ux = (v) => v - 0.5          // unit-square coord → group-local, x
      const uy = (v) => -(v - 0.5)       // …and y, which the tables measure down

      const group = (objs) => {
        const g = new THREE.Group()
        g.position.z = 0
        objs.forEach((o) => g.add(o))
        scene.add(g)
        return g
      }
      const linkMat = lineMat()
      const links = group(FUNNEL_LINKS.map(([x0, y0, x1, y1]) => {
        const curve = new THREE.QuadraticBezierCurve(
          new THREE.Vector2(ux(x0), uy(y0)),
          new THREE.Vector2(ux(x0), uy(y1)),    // straight down out of the parent…
          new THREE.Vector2(ux(x1), uy(y1)),    // …then a swing into the child
        )
        const geo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(24))
        owned.push(geo)
        const l = new THREE.Line(geo, linkMat)
        l.frustumCulled = false
        return l
      }))
      const ruleMat = lineMat()
      const rules = group(GRID_LINES.map(([x0, y0, x1, y1]) => {
        const geo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(ux(x0), uy(y0), 0), new THREE.Vector3(ux(x1), uy(y1), 0),
        ])
        owned.push(geo)
        const l = new THREE.Line(geo, ruleMat)
        l.frustumCulled = false
        return l
      }))

      // ── the field's box inside the hero ───────────────────────────────────
      // The viewport is the field's alone now — the copy lives below the fold —
      // so the box is simply the largest centred square that fits, with a small
      // margin. Square, because the stage layouts are authored in one, and
      // stretching to the viewport's aspect would turn every circle into an
      // ellipse and the taiji into an egg. The scrim, the copy measurement and
      // the layout compression that existed to share this screen with a
      // headline are all gone with the sharing.
      let box = { cx: 0, cy: 0, s: 1 }, alpha = 1
      const measure = () => {
        const w = host.clientWidth, h = host.clientHeight
        if (!w || !h) return false
        renderer.setSize(w, h, false)
        camera.left = -w / 2; camera.right = w / 2
        camera.top = h / 2; camera.bottom = -h / 2
        camera.updateProjectionMatrix()

        box = { s: Math.min(h * 0.9, w * 0.9), cx: 0, cy: 0 }
        // Poster ink is opaque. An earlier 0.92 was meant as restraint but it
        // made every overlap translucent — six taiji parts stacked into a
        // muddle, and circles showing through each other where the poster has
        // them occluding cleanly.
        alpha = 1
        return true
      }

      // px within the box → world, y measured down like the layout tables
      const X = (u) => box.cx + (u - 0.5) * box.s
      const Y = (v) => box.cy - (v - 0.5) * box.s
      const R = (r) => Math.max(r * box.s, 0.0001)

      // Two readings of the same cursor, because they answer different
      // questions. `x`/`y` are -1..1 across the hero and drive the parallax.
      // `u`/`v` are the cursor IN THE FIELD'S OWN unit square — the inverse of
      // X() and Y() — which is the only frame the solver speaks.
      const pointer = { x: 0, y: 0, tx: 0, ty: 0, u: -9, v: -9, over: false }
      const onPointer = (e) => {
        const b = host.getBoundingClientRect()
        pointer.tx = ((e.clientX - b.left) / b.width - 0.5) * 2
        pointer.ty = ((e.clientY - b.top) / b.height - 0.5) * 2
        const wx = e.clientX - b.left - b.width / 2      // world, y up, origin centre
        const wy = b.height / 2 - (e.clientY - b.top)
        pointer.u = (wx - box.cx) / box.s + 0.5
        pointer.v = 0.5 - (wy - box.cy) / box.s
        pointer.over = true
      }
      const onLeave = () => { pointer.over = false }

      const place = (o, x, y, r, a) => {
        o.visible = a > 0.004 && r > 0.0002
        if (!o.visible) return
        o.position.x = X(x) + pointer.x * box.s * 0.012
        o.position.y = Y(y) - pointer.y * box.s * 0.012
        o.scale.set(R(r), R(r), 1)
        o.material.opacity = a * alpha
      }

      // One body and one target per circle, blue first then red, allocated once
      // — the loop must not make garbage sixty times a second.
      const bodies = createBodies(BLUE_N + RED_N)
      const targets = Array.from({ length: BLUE_N + RED_N }, () => [0.47, 0.47, 0])
      let seeded = false

      let last = 0
      const draw = (t) => {
        const dt = Math.min(Math.max(t - last, 0), 0.1)   // a tab that slept must not jump
        last = t
        // Damped by ELAPSED TIME, not per frame. `x += (target - x) * 0.03`
        // reads like a constant but is a rate per frame, so the pointer caught
        // up twice as fast on a 120 Hz display as on a 60 Hz one — the same
        // gesture, two different feels, decided by the monitor. The exponential
        // form has a half-life in seconds and behaves the same everywhere.
        // (Read off maath's `easing.damp`, which the r3f demos use for this.)
        const lag = 1 - Math.exp(-dt / POINTER_TAU)
        pointer.x += (pointer.tx - pointer.x) * lag
        pointer.y += (pointer.ty - pointer.y) * lag

        // A clock that runs backwards or arrives NaN would index STAGES out of
        // range and throw inside the animation loop, which leaves the canvas
        // frozen ON TOP of the CSS floor — the one failure the fallback cannot
        // cover. Cheaper to make the clock impossible to misuse.
        const span = SEG * STAGES.length
        const clock = Number.isFinite(t) ? ((t % span) + span) % span : 0
        const u = pinned != null ? pinned : clock / SEG
        const i = Math.floor(u)
        const f = u - i
        const k = f <= HOLD_F ? 0 : ease((f - HOLD_F) / (1 - HOLD_F))
        const A = STAGES[i], B = STAGES[(i + 1) % STAGES.length]
        const mix = (p, q) => p + (q - p) * k
        /** how present stage `j` is right now — drives the parts only one
         *  stage owns, so they fade with their own diagram, not on a timer */
        const weight = (j) => (i === j ? 1 - k : 0) + ((i + 1) % STAGES.length === j ? k : 0)

        // Where the arrangement WANTS each circle. The solver decides where it
        // actually is — loosely on the way, exactly once the stage has landed.
        for (let n = 0; n < BLUE_N; n++) {
          const a = A.blue[n] ?? PARK, b = B.blue[n] ?? PARK
          const t2 = targets[n]
          t2[0] = mix(a[0], b[0]); t2[1] = mix(a[1], b[1]); t2[2] = mix(a[2], b[2])
        }
        for (let n = 0; n < RED_N; n++) {
          const a = A.red[n] ?? PARK, b = B.red[n] ?? PARK
          const t2 = targets[BLUE_N + n]
          t2[0] = mix(a[0], b[0]); t2[1] = mix(a[1], b[1]); t2[2] = mix(a[2], b[2])
        }

        if (pinned != null || !seeded) {
          // The first frame and the review mode both have to BE the authored
          // panel, not an approach to it — otherwise the hero opens on a blur
          // of circles springing in from the centre.
          snap(bodies, targets)
          seeded = true
        } else {
          // A bell on the morph, not a ramp: physics is loudest mid-flight and
          // gone at both ends, so a stage is entered and left as the poster
          // draws it and only the crossing is alive.
          const blend = Math.sin(Math.PI * k)
          solve(bodies, targets, dt, blend,
            pointer.over ? { x: pointer.u, y: pointer.v, r: 0.15, force: 1.8 } : null)
        }

        for (let n = 0; n < BLUE_N; n++) {
          const b = bodies[n]
          place(blues[n], b.x, b.y, b.r, 1)
        }
        for (let n = 0; n < RED_N; n++) {
          const b = bodies[BLUE_N + n]
          place(reds[n], b.x, b.y, b.r, 1)
        }

        place(triangle, TRIANGLE.x, TRIANGLE.y, TRIANGLE.r, weight(0))

        // the two line groups ride the box; only their scale and origin move
        for (const [g, m, wt] of [[links, linkMat, weight(1)], [rules, ruleMat, weight(3)]]) {
          g.visible = wt > 0.004
          if (!g.visible) continue
          g.position.set(box.cx + pointer.x * box.s * 0.012, box.cy - pointer.y * box.s * 0.012, 0)
          g.scale.set(box.s, box.s, 1)
          m.opacity = wt * alpha * 0.55   // the poster draws these faint on purpose
        }

        const wTaiji = weight(4)
        taiji.visible = wTaiji > 0.004
        if (taiji.visible) {
          taiji.position.set(
            X(TAIJI.cx) + pointer.x * box.s * 0.012,
            Y(TAIJI.cy) - pointer.y * box.s * 0.012, 0,
          )
          taiji.scale.set(box.s, box.s, 1)
          // it arrives spinning — a turn and a half unwinding as it appears —
          // and then never quite stops
          taiji.rotation.z = -SPIN_IN * (1 - wTaiji)
          Object.values(taijiParts).forEach((o) => { o.material.opacity = wTaiji * alpha })
        }

        renderer.render(scene, camera)
      }

      if (!measure()) return
      host.appendChild(canvas)
      draw(0)
      setLive(true)

      // The loop runs whenever the component is mounted, and each frame decides
      // for itself whether there is anything to draw.
      //
      // The first version gated the loop on three LATCHED booleans — an
      // IntersectionObserver's saved answer, a saved visibilitychange, a saved
      // media query — and started or cancelled the rAF chain when they changed.
      // That design froze the hero on Andy's own machine with zero errors: the
      // page loaded in an occluded window, the observer's initial callback
      // reported not-intersecting, and since the element's layout never changed
      // afterwards the observer never spoke again — a stale `false` no event
      // would ever correct, holding the gate shut while the window sat in
      // plain view. Diagnosed live over CDP: injected rAF counter advancing,
      // app canvas frozen, every other gate condition measured true.
      //
      // So: no latches. A hidden or occluded window costs nothing anyway — the
      // browser stops firing rAF there, which is the battery saving the
      // observer was supposed to provide, provided for free and never stale.
      // The one case that keeps a per-frame check is the hero scrolled out of
      // view in a visible tab, and that is a one-line read of scrollY — the
      // hero starts at the top of the page, so it is off screen exactly when a
      // full viewport has been scrolled past. A parked frame skips drawing but
      // keeps the chain alive; a no-op rAF is nanoseconds.
      let raf = 0
      const t0 = performance.now()
      const loop = () => {
        raf = requestAnimationFrame(loop)
        if (window.scrollY > window.innerHeight) return   // parked below the fold
        draw((performance.now() - t0) / 1000)
      }
      if (!still && pinned == null) loop()
      const ro = new ResizeObserver(() => { if (measure()) draw((performance.now() - t0) / 1000) })
      ro.observe(host)
      // On the SECTION, not on the field. The field carries pointer-events:none
      // so it can never eat a click meant for the CTA — which also meant it
      // never received a pointermove, so the parallax had been dead since the
      // day it was written. Nothing showed it: the only browser it was checked
      // in does not fire requestAnimationFrame, so there was no motion to miss.
      const surface = host.parentElement ?? host
      surface.addEventListener('pointermove', onPointer)
      surface.addEventListener('pointerleave', onLeave)

      teardown = () => {
        if (raf) cancelAnimationFrame(raf)
        ro.disconnect()
        surface.removeEventListener('pointermove', onPointer)
        surface.removeEventListener('pointerleave', onLeave)
        canvas.removeEventListener('webglcontextlost', onLost)
        owned.forEach((m) => m.dispose())
        disc.dispose(); half.dispose(); tri.dispose()
        renderer.dispose()
        canvas.remove()
      }
    })()

    return () => { disposed = true; if (teardown) teardown() }
  }, [])

  return (
    <div ref={hostRef} aria-hidden="true"
         className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className={`absolute inset-0 transition-opacity duration-700 ${live ? 'opacity-0' : 'opacity-100'}`}>
        {DOTS.map((d, i) => (
          <div key={i} className={`hero-dot ${d.cls}`}
               style={{ width: d.size, height: d.size, top: d.top, bottom: d.bottom,
                        left: d.left, right: d.right }} />
        ))}
      </div>
    </div>
  )
}
