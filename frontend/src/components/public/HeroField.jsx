import { useEffect, useRef, useState } from 'react'
import {
  STAGES, BLUE_N, RED_N, PARK, TRIANGLE, FUNNEL_LINKS, GRID_LINES,
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

      // Material and light, off the reference Andy pointed at. What is copied
      // is exactly that pair — a studio: bright neutral room reflections
      // (RoomEnvironment through PMREM, no HDR file to fetch), glossy
      // clearcoated spheres, one key light that lets the spheres shadow each
      // other so a cluster reads as touching bodies rather than pasted discs.
      // What is NOT copied is the identity: the palette stays poster red and
      // blue, and the five stages stay the five stages.
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFSoftShadowMap
      // Neutral, not ACESFilmic: ACES desaturates saturated primaries by
      // design, and it was bleaching poster red to coral. Neutral (Khronos
      // PBR) holds the hue and still rolls off the highlights.
      renderer.toneMapping = THREE.NeutralToneMapping

      const scene = new THREE.Scene()
      // Still orthographic — the reference's own lens (fov 17.5 at z=30) is a
      // telephoto pretending to be one. Depth is now real for LIGHT: spheres
      // occlude and shadow one another. It is still not a dimension to read.
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 4000)
      camera.position.z = 1200

      const pmrem = new THREE.PMREMGenerator(renderer)
      let env = null
      try {
        const { RoomEnvironment } = await import('three/examples/jsm/environments/RoomEnvironment.js')
        env = pmrem.fromScene(new RoomEnvironment(), 0.04)
        scene.environment = env.texture
      } catch { /* no env — the key light still shades the spheres */ }

      const key = new THREE.DirectionalLight(0xffffff, 2.0)
      key.castShadow = true
      key.shadow.mapSize.set(2048, 2048)
      key.shadow.bias = -0.0005
      scene.add(key, new THREE.AmbientLight(0xffffff, 0.25))

      const BLUE = new THREE.Color(cssVar('--color-poster-blue', '#3b82c4'))
      const RED = new THREE.Color(cssVar('--color-poster-red', '#d94032'))
      const GREEN = new THREE.Color(cssVar('--color-poster-green', '#22c55e'))

      const ball = new THREE.SphereGeometry(1, 48, 32)
      const cone = new THREE.ConeGeometry(1, 1.5, 32)

      const owned = []
      const mat = (colour, extra = {}) => {
        const m = new THREE.MeshPhysicalMaterial({
          color: colour, roughness: 0.16, clearcoat: 1, clearcoatRoughness: 0.12,
          // the room at full strength washed poster red out to coral — the
          // reflections stay, the bleaching goes
          envMapIntensity: 0.55,
          ...extra,
        })
        owned.push(m)
        return m
      }
      const mesh = (geo, material) => {
        const o = new THREE.Mesh(geo, material)
        o.castShadow = true
        o.receiveShadow = true
        scene.add(o)
        return o
      }

      // the reference's red carries a faint inner glow; ours does the same
      const blues = Array.from({ length: BLUE_N }, () => mesh(ball, mat(BLUE)))
      const reds = Array.from({ length: RED_N }, () =>
        mesh(ball, mat(RED, { emissive: RED, emissiveIntensity: 0.14 })))

      // stage 1's marker for the turn — the only green in the field, now a
      // small glossy cone pointing the way up
      const triMat = mat(GREEN, { transparent: true })
      const triangle = mesh(cone, triMat)

      // The connective tissue — stage 1's links and stage 3's rules. Both are
      // built once in the unit square (x right, y down, origin at the centre)
      // and carried by a group that is scaled and placed with the box, so a
      // resize never touches a vertex.
      const lineMat = () => {
        // graphite on paper now, not chalk on black
        const m = new THREE.LineBasicMaterial({
          color: 0x9a958c, transparent: true, opacity: 0,
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
        alpha = 1

        // the key light rides the box so its shadow camera always covers the
        // field exactly — a fixed frustum would clip shadows on a big screen
        // or waste its whole map on a small one
        key.position.set(box.s * 0.5, box.s * 0.7, box.s * 0.9)
        const sc = key.shadow.camera
        sc.left = -box.s; sc.right = box.s; sc.top = box.s; sc.bottom = -box.s
        sc.near = 0.1; sc.far = box.s * 3
        sc.updateProjectionMatrix()
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

      // `a` fades a shape that only one stage owns; spheres never fade, they
      // shrink into PARK. A fading shape scales down with its weight instead of
      // going translucent — physical materials pay for transparency, and a
      // shrinking cone reads better than a ghost of one anyway.
      const place = (o, x, y, r, a) => {
        o.visible = a > 0.004 && r > 0.0002
        if (!o.visible) return
        const rr = R(r) * a
        o.position.x = X(x) + pointer.x * box.s * 0.012
        o.position.y = Y(y) - pointer.y * box.s * 0.012
        o.position.z = rr                     // resting on the z = 0 glass, toward the light
        o.scale.set(rr, rr, rr)
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
        ball.dispose(); cone.dispose()
        if (env) env.dispose()
        pmrem.dispose()
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
