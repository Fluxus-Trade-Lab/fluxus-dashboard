// Contact sheet for the hero field's five stages.
//
// requestAnimationFrame never fires inside the headless Browser pane, so the
// running animation cannot be observed there. This renders the same STAGES
// module to a flat SVG so every layout can actually be looked at — and side by
// side is a better way to review five panels than watching a 29-second loop.
//
// It imports the real module. There is no second copy of the numbers.

import { writeFileSync } from 'node:fs'
import {
  STAGES, STAGE_NAMES, TRIANGLE, FUNNEL_LINKS, GRID_LINES,
} from '../src/components/public/heroStages.js'

const BLUE = '#3b82c4'
const RED = '#d94032'
const GREEN = '#22c55e'
// the studio's paper, since the hero went material — panels preview layout,
// not light, but they should at least sit on the right ground
const BG = '#ececec'

const S = 300          // panel side
const GAP = 22
const PAD = 26
const LABEL = 30

const W = PAD * 2 + S * 5 + GAP * 4
const H = PAD * 2 + S + LABEL

const circle = (ox, [x, y, r], fill) =>
  r <= 0 ? '' : `<circle cx="${(ox + x * S).toFixed(1)}" cy="${(y * S + PAD).toFixed(1)}" r="${(r * S).toFixed(1)}" fill="${fill}"/>`

const panels = STAGES.map((st, i) => {
  const ox = PAD + i * (S + GAP)
  const P = (x, y) => `${(ox + x * S).toFixed(1)} ${(y * S + PAD).toFixed(1)}`
  const parts = [`<rect x="${ox}" y="${PAD}" width="${S}" height="${S}" fill="#e2e2e2"/>`]
  // connective tissue goes under the circles, faint, as on the poster
  if (i === 1) {
    parts.push(...FUNNEL_LINKS.map(([x0, y0, x1, y1]) =>
      `<path d="M ${P(x0, y0)} Q ${P(x0, y1)} ${P(x1, y1)}" fill="none" stroke="#9a958c" stroke-opacity="0.7" stroke-width="1"/>`))
  }
  if (i === 3) {
    parts.push(...GRID_LINES.map(([x0, y0, x1, y1]) =>
      `<line x1="${(ox + x0 * S).toFixed(1)}" y1="${(y0 * S + PAD).toFixed(1)}" x2="${(ox + x1 * S).toFixed(1)}" y2="${(y1 * S + PAD).toFixed(1)}" stroke="#9a958c" stroke-opacity="0.7" stroke-width="1"/>`))
  }
  parts.push(
    ...st.blue.map((c) => circle(ox, c, BLUE)),
    ...st.red.map((c) => circle(ox, c, RED)),
  )
  if (i === 0) {
    const x = ox + TRIANGLE.x * S, y = TRIANGLE.y * S + PAD, r = TRIANGLE.r * S
    parts.push(`<polygon points="${x},${y - r} ${x + r * 0.87},${y + r * 0.5} ${x - r * 0.87},${y + r * 0.5}" fill="${GREEN}"/>`)
  }
  parts.push(
    `<text x="${ox}" y="${PAD + S + 20}" fill="#57534e" font-family="ui-monospace,Menlo,monospace" font-size="11" letter-spacing="2">${i + 1}. ${STAGE_NAMES[i].toUpperCase()}</text>`,
  )
  return parts.join('\n')
})

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="${W}" height="${H}" fill="${BG}"/>
${panels.join('\n')}
</svg>`

const out = process.argv[2] ?? 'hero-stages.svg'
writeFileSync(out, svg)

// a shape check the eye should not have to do
const bad = []
STAGES.forEach((st, i) => {
  for (const key of ['blue', 'red']) {
    st[key].forEach((c, n) => {
      if (!Array.isArray(c) || c.length !== 3 || c.some((v) => !Number.isFinite(v))) bad.push(`stage ${i} ${key}[${n}] malformed`)
      else if (c[2] < 0) bad.push(`stage ${i} ${key}[${n}] negative radius`)
    })
    if (st[key].length !== STAGES[0][key].length) bad.push(`stage ${i} ${key} has a different cast size`)
  }
})
console.log(bad.length ? bad.join('\n') : `ok — 5 stages, ${STAGES[0].blue.length} blue + ${STAGES[0].red.length} red, all finite`)
console.log('wrote', out)
