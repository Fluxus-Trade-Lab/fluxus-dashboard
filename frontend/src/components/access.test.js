import { describe, it, expect } from 'vitest'
import { isLocked, FREE_PAGES, LOCKED_BLURB } from './access'
import { translations } from '../i18n/translations'

describe('isLocked', () => {
  it('leaves Model Books open — the one page Andy made free', () => {
    expect(isLocked('modelbooks')).toBe(false)
  })

  it('locks the market pages', () => {
    for (const p of ['dashboard', 'rotation', 'screener', 'watchlist', 'rs-live', 'breadth']) {
      expect(isLocked(p), p).toBe(true)
    }
  })

  it('locks the book pages', () => {
    for (const p of ['portfolio', 'journal', 'review']) expect(isLocked(p), p).toBe(true)
  })

  it('locks the library shelves but not Model Books beside them', () => {
    for (const p of ['defense', 'offense', 'psychology', 'portfolio-management', 'news']) {
      expect(isLocked(p), p).toBe(true)
    }
    expect(isLocked('modelbooks')).toBe(false)
  })

  it('does not lock the public marketing pages', () => {
    // These never reach the rail layout at all, but a stray true here would
    // blur the landing page itself — the one screen that must be readable.
    for (const p of ['', 'method', 'results', 'pricing', 'brief']) {
      expect(isLocked(p), p).toBe(false)
    }
  })

  it('leaves an unknown route alone rather than guessing', () => {
    // A page this table has never heard of is far more likely to be new work
    // than a secret, and hiding a colleague's page on the day they ship it is
    // the worse failure.
    expect(isLocked('some-page-added-next-week')).toBe(false)
    expect(isLocked(undefined)).toBe(false)
    expect(isLocked(null)).toBe(false)
  })

  it('never has a page in both tables', () => {
    for (const free of FREE_PAGES) {
      expect(Object.prototype.hasOwnProperty.call(LOCKED_BLURB, free), free).toBe(false)
    }
  })
})

describe('every locked page says what it is', () => {
  it('has a blurb key for each locked page', () => {
    for (const page of Object.keys(LOCKED_BLURB)) {
      expect(LOCKED_BLURB[page], page).toMatch(/^locked\.blurb\./)
    }
  })

  it('has real English and Chinese for every key the card can show', () => {
    const keys = [
      'locked.title', 'locked.freeHint', 'locked.ctaFree', 'locked.ctaJoin', 'locked.beta',
      ...Object.values(LOCKED_BLURB),
    ]
    const missing = []
    for (const k of new Set(keys)) {
      if (!translations.en[k]) missing.push(`en:${k}`)
      if (!translations.zh[k]) missing.push(`zh:${k}`)
    }
    expect(missing, `a card with a missing key renders the raw id:\n${missing.join('\n')}`)
      .toEqual([])
  })

  it('does not leave the Chinese as a copy of the English', () => {
    // The blur card is the first thing a Chinese-reading visitor meets on a
    // locked page. Untranslated English there reads as an unfinished site.
    const same = Object.values(LOCKED_BLURB)
      .filter(k => translations.en[k] && translations.en[k] === translations.zh[k])
    expect(same).toEqual([])
  })
})
