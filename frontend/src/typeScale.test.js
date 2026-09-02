import { describe, it, expect } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * The type scale, enforced.
 *
 * Andy, 2026-09-02: 「我们每个页面的字体大小不统一，没有一个规则」. Measured, he was
 * right — nine tiers app-wide, five of them inside a 2px band (10 / 11 / 11.5 /
 * 12 / 12.5), which is not a hierarchy, it is noise. Two sizes 1px apart are not
 * two tiers; they are one tier written two ways.
 *
 * He set the floor himself (「我不要有 10」) and picked the scale:
 *
 *     11  labels, table cells, captions        — the dense mass
 *     13  body                                  — default reading size
 *     17  the one number or sentence per card
 *     26  the two headline numbers
 *     38 / 46  page title
 *
 * WHY A TEST AND NOT A COMMENT. The nine tiers did not arrive by decision;
 * nobody ever chose 11.5. They arrived because the next person to need
 * "slightly smaller" typed a number, and the number after that copied it. A
 * comment cannot stop that. This can: add an off-scale size and the suite goes
 * red with the file and the value.
 *
 * NOT COVERED, on purpose:
 *   - SVG text (`fontSize: n` inside a chart) — those live in drawing units
 *     under a viewBox, sized by what fits the figure, not by the page's scale.
 *   - `.orig` backups — not imported by anything (Andy: 先不碰).
 */
const ALLOWED = new Set([11, 13, 17, 26, 38, 46])
const SRC = dirname(fileURLToPath(import.meta.url))

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) { walk(p, out); continue }
    if (!/\.(jsx|js)$/.test(name) || name.includes('.orig')) continue
    out.push(p)
  }
  return out
}

describe('type scale', () => {
  it('every Tailwind text-[Npx] in the app is on the scale', () => {
    const offenders = []
    for (const file of walk(SRC)) {
      const src = readFileSync(file, 'utf8')
      for (const m of src.matchAll(/text-\[(\d+(?:\.\d+)?)px\]/g)) {
        const px = Number(m[1])
        if (!ALLOWED.has(px)) offenders.push(`${file.slice(SRC.length + 1)}: ${px}px`)
      }
    }
    expect(offenders, `off-scale sizes — the scale is ${[...ALLOWED].join(' / ')}px`).toEqual([])
  })

  it('the floor is 11 — nothing smaller ships as page text', () => {
    expect(Math.min(...ALLOWED)).toBe(11)
  })
})
