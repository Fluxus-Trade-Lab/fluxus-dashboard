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

  /**
   * The first version of this said no file may import both, and the Short List
   * page broke it the moment the two halves became one page — it needs the
   * tray for Andy's names and the file for the six seats. Forbidding that was
   * never the invariant; it was a proxy for one. The rule that would actually
   * have caught the overwrite is this: nothing calls a hook it did not import.
   * A file that lost an import and kept the call is the shape of the bug.
   */
  it('never calls a shortlist hook it did not import', () => {
    const walk = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
      e.isDirectory() ? walk(resolve(dir, e.name))
        : /\.jsx?$/.test(e.name) ? [resolve(dir, e.name)] : [])
    let sawBoth = 0
    for (const f of walk(SRC)) {
      // skip the hooks themselves and this file — a test that greps for a call
      // pattern will always find its own regex source
      if (/hooks\/useShortlist(File)?\.js$/.test(f) || /\.test\.jsx?$/.test(f)) continue
      const s = readFileSync(f, 'utf8')
      const impTray = /import \{[^}]*\buseShortlist\b[^}]*\} from '.*hooks\/useShortlist'/.test(s)
      const impFile = /\buseShortlistFile\b[^\n]*from '.*hooks\/useShortlistFile'/.test(s)
      if (/\buseShortlist\(/.test(s)) expect(impTray, `${f} calls useShortlist()`).toBe(true)
      if (/\buseShortlistFile\(/.test(s)) expect(impFile, `${f} calls useShortlistFile()`).toBe(true)
      if (impTray && impFile) sawBoth += 1
    }
    // and the page that joins the two halves is expected to hold both
    expect(sawBoth).toBeGreaterThan(0)
  })
})
