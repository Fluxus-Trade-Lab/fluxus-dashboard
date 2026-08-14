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
      const mesh = (geo, colour, z) => {
        const m = mat(colour)
        owned.push(m)
        const o = new THREE.Mesh(geo, m)
        o.position.z = z
        o.renderOrder = z
        scene.add(o)
        return o
      }

      const blues = Array.from({ length: BLUE_N }, () => mesh(disc, BLUE, 1))
      const reds = Array.from({ length: RED_N }, () => mesh(disc, RED, 1))

      // stage 1's marker for the turn — the only green on the page
      const triangle = mesh(tri, GREEN, 3)

      // stage 5, painted back to front: the two halves, the two lobes that bend
      // the seam into an S, then each side's seed of the other
      const taiji = {
        left: mesh(half, BLUE, 4),
        right: mesh(half, RED, 5),
        lobeA: mesh(disc, RED, 6),
        lobeB: mesh(disc, BLUE, 7),
        seedA: mesh(disc, BLUE, 8),
        seedB: mesh(disc, RED, 9),
      }
      taiji.right.rotation.z = Math.PI     // mirror the half onto the other side

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
        return new THREE.Line(geo, linkMat)
      }))
      const ruleMat = lineMat()
      const rules = group(GRID_LINES.map(([x0, y0, x1, y1]) => {
        const geo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(ux(x0), uy(y0), 0), new THREE.Vector3(ux(x1), uy(y1), 0),
        ])
        owned.push(geo)
        return new THREE.Line(geo, ruleMat)
      }))

      // ── the field's box inside the hero ───────────────────────────────────
      // Wide: a square in the right-hand third, clear of the copy, at strength.
      // Narrow: the copy spans everything, so the field goes back to being the
      // wash it is today rather than fighting the headline for the same pixels.
      let box = { cx: 0, cy: 0, s: 1 }, alpha = 1
      const measure = () => {
        const w = host.clientWidth, h = host.clientHeight
        if (!w || !h) return false
        renderer.setSize(w, h, false)
        camera.left = -w / 2; camera.right = w / 2
        camera.top = h / 2; camera.bottom = -h / 2
        camera.updateProjectionMatrix()

        const wide = w >= 900
        const s = wide ? Math.min(h * 0.86, w * 0.42) : Math.min(w * 0.92, h * 0.62)
        box = { s, cx: wide ? w * 0.29 : 0, cy: wide ? 0 : -h * 0.08 }
        alpha = wide ? 0.82 : 0.15
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

      const draw = (t) => {
        pointer.x += (pointer.tx - pointer.x) * 0.03
        pointer.y += (pointer.ty - pointer.y) * 0.03

        // A clock that runs backwards or arrives NaN would index STAGES out of
        // range and throw inside the animation loop, which leaves the canvas
        // frozen ON TOP of the CSS floor — the one failure the fallback cannot
        // cover. Cheaper to make the clock impossible to misuse.
        const span = SEG * STAGES.length
        const clock = Number.isFinite(t) ? ((t % span) + span) % span : 0
        const u = clock / SEG
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
        if (wTaiji > 0.004) {
          const { cx, cy, r: rr } = TAIJI
          place(taiji.left, cx, cy, rr, wTaiji)
          place(taiji.right, cx, cy, rr, wTaiji)
          place(taiji.lobeA, cx, cy - rr / 2, rr / 2, wTaiji)
          place(taiji.lobeB, cx, cy + rr / 2, rr / 2, wTaiji)
          place(taiji.seedA, cx, cy - rr / 2, rr / 6, wTaiji)
          place(taiji.seedB, cx, cy + rr / 2, rr / 6, wTaiji)
        } else {
          Object.values(taiji).forEach((o) => { o.visible = false })
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
        const go = visible && !document.hidden && !still
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
    </div>
  )
}
