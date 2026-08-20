import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * Two different things once wore the same name.
 *
 * `useShortlist` is the TRAY: names you picked this morning, held in
 * localStorage, with add/remove/clear. `useShortlistFile` is the nightly
 * shortlist.json: six seats an engine picked, fetched. On 2026-08-20 the
 * second was written straight over the first because it was created with the
 * same filename — the build does not type-check and nothing covered the tray,
 * so the only symptom was `add` quietly going missing from a component nobody
 * re-opened.
 *
 * This is the same failure the codebase already has a rule for: check by what
 * a thing IS, not by the name you were about to give it.
 */
const SRC = resolve(process.cwd(), 'src')
const read = (p) => readFileSync(resolve(SRC, p), 'utf8')

describe('the two shortlist stores', () => {
  it('are two files with two exports', () => {
    expect(read('hooks/useShortlist.js')).toMatch(/export function useShortlist\b/)
    expect(read('hooks/useShortlistFile.js')).toMatch(/export function useShortlistFile\b/)
  })

  it('keeps the tray a store with a way to put something in it', () => {
    const s = read('hooks/useShortlist.js')
    for (const fn of ['add', 'remove', 'clear', 'has']) expect(s).toMatch(new RegExp(`\\b${fn}\\b`))
  })

  it('keeps the file hook a fetch, with failure told apart from empty', () => {
    const s = read('hooks/useShortlistFile.js')
    expect(s).toContain('/data/output/shortlist.json')
    expect(s).toMatch(/setFailed/)
  })

  it('leaves every caller pointed at the one it means', () => {
    const walk = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
      e.isDirectory() ? walk(resolve(dir, e.name))
        : /\.jsx?$/.test(e.name) ? [resolve(dir, e.name)] : [])
    for (const f of walk(SRC)) {
      const s = readFileSync(f, 'utf8')
      // a file importing one must not call the other
      if (/from '.*hooks\/useShortlist'/.test(s)) expect(s, f).not.toMatch(/useShortlistFile\(/)
      if (/from '.*hooks\/useShortlistFile'/.test(s)) expect(s, f).not.toMatch(/\buseShortlist\(/)
    }
  })
})
