import { useEffect, useRef, useState } from 'react'
import {
  STAGES, BLUE_N, RED_N, PARK, TRIANGLE, TAIJI, FUNNEL_LINKS, GRID_LINES,
} from './heroStages'

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

const SPIN_IN = Math.PI * 3      // a turn and a half, unwound as the taiji lands
const SPIN_HELD = 0.063          // ~100 s a revolution once it has
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
  /** how far up the scrim has to reach — the copy's own height plus a tenth of
   *  the hero, so the words never start inside the gradient's fading half */
  const [scrim, setScrim] = useState(0)

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
    const asked = Number(new URLSearchParams(window.location.search).get('stage'))
    const pinned = Number.isInteger(asked) && asked >= 0 && asked < STAGES.length ? asked : null

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
      // z-1: above the CSS floor it supersedes, below the scrim that gives the
      // copy its ground. The canvas is appended last, so without this it would
      // paint over the scrim and the headline would sit under the circles.
      canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;z-index:1'
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
      // The field owns the page, so it takes the largest square that fits —
      // square, because the stage layouts are authored in one, and stretching
      // to the viewport's aspect would turn every circle into an ellipse and
      // the taiji into an egg.
      //
      // The square takes the whole band above the copy, then DIP past its floor
      // so the diagram sinks into the scrim instead of stopping politely on a
      // line. Two versions were wrong before this one: a square in the right
      // third read as an ornament balancing a headline, and a square the full
      // height of the page buried every stage's punchline — the bottom of the
      // V, the leader at the end of the funnel, the green triangle at the turn
      // — under the solid part of the scrim. The bottom of each stage is where
      // its point is; it has to stay above the black.
      //
      // The band is measured off the copy, never guessed. It is what changes
      // when the headline wraps to a fourth line, when the viewport turns, when
      // someone adds a stat — and a fixed fraction would be wrong the first
      // time any of those happened.
      // 1.28 put the funnel's leader — the circle the whole stage is about —
      // half behind the headline. 1.12 keeps every stage's lowest mark clear of
      // the copy while the square still runs past the band into the scrim.
      const DIP = 1.12
      let box = { cx: 0, cy: 0, s: 1 }, alpha = 1
      const measure = () => {
        const w = host.clientWidth, h = host.clientHeight
        if (!w || !h) return false
        renderer.setSize(w, h, false)
        camera.left = -w / 2; camera.right = w / 2
        camera.top = h / 2; camera.bottom = -h / 2
        camera.updateProjectionMatrix()

        const wide = w >= 900
        const copy = host.parentElement?.querySelector('[data-hero-copy]')
        const reserved = copy?.getBoundingClientRect().height || h * 0.5
        const band = Math.max(h - reserved, h * 0.3)

        const s = Math.min(band * DIP, w * (wide ? 0.58 : 0.96))
        box = { s, cx: 0, cy: h / 2 - s / 2 - h * 0.02 }   // hung from the top
        alpha = wide ? 0.92 : 0.7
        setScrim(Math.min(Math.round(reserved + h * 0.08), h))
        return true
      }

      // px within the box → world, y measured down like the layout tables
      const X = (u) => box.cx + (u - 0.5) * box.s
      const Y = (v) => box.cy - (v - 0.5) * box.s
      const R = (r) => Math.max(r * box.s, 0.0001)

      const pointer = { x: 0, y: 0, tx: 0, ty: 0 }
      const onPointer = (e) => {
        const b = host.getBoundingClientRect()
        pointer.tx = ((e.clientX - b.left) / b.width - 0.5) * 2
        pointer.ty = ((e.clientY - b.top) / b.height - 0.5) * 2
      }

      const place = (o, x, y, r, a) => {
        o.visible = a > 0.004 && r > 0.0002
        if (!o.visible) return
        o.position.x = X(x) + pointer.x * box.s * 0.012
        o.position.y = Y(y) - pointer.y * box.s * 0.012
        o.scale.set(R(r), R(r), 1)
        o.material.opacity = a * alpha
      }

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

        const run = (pool, key) => pool.forEach((o, n) => {
          const a = A[key][n] ?? PARK, b = B[key][n] ?? PARK
          place(o, mix(a[0], b[0]), mix(a[1], b[1]), mix(a[2], b[2]), 1)
        })
        run(blues, 'blue')
        run(reds, 'red')

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
          taiji.rotation.z = -SPIN_IN * (1 - wTaiji) - clock * SPIN_HELD
          Object.values(taijiParts).forEach((o) => { o.material.opacity = wTaiji * alpha })
        }

        renderer.render(scene, camera)
      }

      if (!measure()) return
      host.appendChild(canvas)
      draw(0)
      setLive(true)

      // Off screen or in a background tab it stops dead. An ambient field is
      // not worth one frame of anybody's battery once nobody is looking.
      let raf = 0, visible = true
      const t0 = performance.now()
      const loop = () => { raf = requestAnimationFrame(loop); draw((performance.now() - t0) / 1000) }
      const pump = () => {
        const go = visible && !document.hidden && !still && pinned == null
        if (go && !raf) loop()
        else if (!go && raf) { cancelAnimationFrame(raf); raf = 0 }
      }
      const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; pump() }, { threshold: 0 })
      io.observe(host)
      document.addEventListener('visibilitychange', pump)
      const ro = new ResizeObserver(() => { if (measure() && !raf) draw(0) })
      ro.observe(host)
      host.addEventListener('pointermove', onPointer)
      pump()

      teardown = () => {
        if (raf) cancelAnimationFrame(raf)
        io.disconnect(); ro.disconnect()
        document.removeEventListener('visibilitychange', pump)
        host.removeEventListener('pointermove', onPointer)
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
      {/* The copy sits ON the field now, not beside it, so the field has to
          give it ground. The scrim is the poster's own black fading up out of
          the floor: the circles do not stop at a line, they sink. Its height
          is the copy's, measured, so the words always begin above the point
          where the gradient has gone solid. */}
      <div className="absolute inset-x-0 bottom-0 z-[2]"
           style={{
             height: scrim || '58%',
             background: 'linear-gradient(to top, var(--color-poster-bg) 0%, var(--color-poster-bg) 42%, color-mix(in srgb, var(--color-poster-bg) 76%, transparent) 70%, transparent 100%)',
           }} />
    </div>
  )
}
