import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { parse, inline } from './markdown'

/**
 * Parsed against the real article, not a fixture I wrote to match my parser.
 *
 * `offense_ep_mrna.md` is the first thing the Library has ever held. If a
 * construct in it is one this reader does not know, the page shows a stray
 * pipe or a lone asterisk rather than falling over — but it should be caught
 * here first, and it should be caught again the day the data side writes a
 * second article in a shape the first one did not use.
 */
const FILE = resolve(process.cwd(), '..', 'data/output/library/offense_ep_mrna.md')
let src = null
try { src = readFileSync(FILE, 'utf8') } catch { /* not shipped yet */ }

describe('inline spans', () => {
  it('reads bold, italic and code without swallowing the text between', () => {
    expect(inline('a **b** c `d` e *f*')).toEqual([
      { t: 'text', s: 'a ' }, { t: 'b', s: 'b' }, { t: 'text', s: ' c ' },
      { t: 'code', s: 'd' }, { t: 'text', s: ' e ' }, { t: 'i', s: 'f' },
    ])
  })

  it('never reads **bold** as an italic wrapping an italic', () => {
    expect(inline('**重定价**')).toEqual([{ t: 'b', s: '重定价' }])
  })

  it('leaves a bare asterisk alone rather than eating the rest of the line', () => {
    expect(inline('2 * 3 = 6')).toEqual([{ t: 'text', s: '2 * 3 = 6' }])
  })
})

describe('blocks', () => {
  it('keeps a table together and drops its divider row', () => {
    const [t] = parse('| a | b |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n')
    expect(t.type).toBe('table')
    expect(t.head).toHaveLength(2)
    expect(t.rows).toHaveLength(2)
  })

  it('does not mistake a leading-pipe line for a table without a divider', () => {
    expect(parse('| not a table\n').map((b) => b.type)).toEqual(['p'])
  })

  it('runs consecutive list items into one list, and splits on kind', () => {
    const b = parse('1. a\n2. b\n\n- c\n- d\n')
    expect(b.map((x) => [x.type, x.ordered, x.items.length]))
      .toEqual([['list', true, 2], ['list', false, 2]])
  })

  it('joins a wrapped paragraph and breaks on the blank line', () => {
    expect(parse('one\ntwo\n\nthree').map((b) => b.type)).toEqual(['p', 'p'])
  })

  it('is empty, not broken, on nothing at all', () => {
    expect(parse('')).toEqual([])
    expect(parse(null)).toEqual([])
  })
})

describe.skipIf(!src)('the real article', () => {
  const blocks = parse(src)

  it('finds its title and its sections', () => {
    expect(blocks[0]).toMatchObject({ type: 'h', level: 1 })
    expect(blocks.filter((b) => b.type === 'h' && b.level === 2).length).toBeGreaterThanOrEqual(3)
  })

  it('reads the month-of-footprints table as one table', () => {
    const tables = blocks.filter((b) => b.type === 'table')
    expect(tables).toHaveLength(1)
    expect(tables[0].head.length).toBe(2)
    expect(tables[0].rows.length).toBeGreaterThanOrEqual(8)
  })

  it('reads the four disciplines as one ordered list', () => {
    const lists = blocks.filter((b) => b.type === 'list' && b.ordered)
    expect(lists).toHaveLength(1)
    expect(lists[0].items).toHaveLength(4)
  })

  it('leaves no stray marker anywhere in the rendered text', () => {
    const flat = (spans) => spans.map((s) => s.s).join('')
    const text = blocks.flatMap((b) =>
      b.spans ? [flat(b.spans)]
      : b.items ? b.items.map(flat)
      : b.rows ? [...b.head.map(flat), ...b.rows.flatMap((r) => r.map(flat))]
      : []).join('\n')
    expect(text).not.toMatch(/\*\*/)
    expect(text).not.toMatch(/^\s*#/m)
    expect(text).not.toMatch(/\|/)
  })
})
