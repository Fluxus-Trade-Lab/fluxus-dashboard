import { describe, it, expect } from 'vitest'
import { changeOf, changeColour, changeLookup } from './stateChange'

describe('changeOf', () => {
  it('reads first measured against last measured, not adjacent days', () => {
    expect(changeOf(['Lagging', 'Improving', 'Leading'])).toBe('up')
    expect(changeOf(['Leading', 'Weakening', 'Lagging'])).toBe('down')
  })

  it('a round trip is not a change — over the window it did not move', () => {
    expect(changeOf(['Lagging', 'Leading', 'Lagging'])).toBe(null)
  })

  it('skips the sessions a group was not measured', () => {
    // joined the pool late: the first four nights hold no reading at all
    expect(changeOf([null, null, null, null, 'Lagging', 'Leading'])).toBe('up')
  })

  it('one reading is not "no change" — there is nothing to compare', () => {
    expect(changeOf(['Leading'])).toBe(null)
    expect(changeOf([null, 'Leading', null])).toBe(null)
    expect(changeOf([])).toBe(null)
    expect(changeOf(undefined)).toBe(null)
  })

  it('ignores values that are not one of the four states', () => {
    expect(changeOf(['Lagging', 'n/a', 'Leading'])).toBe('up')
    expect(changeOf(['n/a', 'nope'])).toBe(null)
  })
})

describe('changeColour', () => {
  it('uses the pair and nothing else — unchanged has no colour of its own', () => {
    expect(changeColour('up')).toBe('var(--color-took)')
    expect(changeColour('down')).toBe('var(--color-refused)')
    expect(changeColour(null)).toBe(null)
    expect(changeColour(undefined)).toBe(null)
  })
})

describe('changeLookup', () => {
  const history = {
    groups: {
      'Memory & Storage': { state: ['Lagging', 'Improving', 'Leading'] },
      Steel: { state: ['Improving', 'Improving', 'Lagging'] },
      Coal: { state: ['Leading', 'Leading'] },
      'Cloud Software': { state: [null, null, 'Leading'] },
    },
  }

  it('grades each group off its own stored sequence', () => {
    const at = changeLookup(history)
    expect(at('Memory & Storage')).toBe('up')
    expect(at('Steel')).toBe('down')
    expect(at('Coal')).toBe(null)
    expect(at('Cloud Software')).toBe(null)  // one reading, not "no change"
  })

  it('a group the history has never heard of grades to null, not a throw', () => {
    expect(changeLookup(history)('Nonesuch')).toBe(null)
  })

  it('with no file at all every mark falls back to ink', () => {
    expect(changeLookup(null)('Memory & Storage')).toBe(null)
    expect(changeLookup({})('Memory & Storage')).toBe(null)
    expect(changeLookup({ groups: null })('Memory & Storage')).toBe(null)
  })
})
