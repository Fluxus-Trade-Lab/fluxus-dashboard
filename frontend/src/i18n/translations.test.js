import { describe, it, expect } from 'vitest'
import { translations } from './translations'

describe('translations', () => {
  it('has both en and zh dictionaries', () => {
    expect(translations.en).toBeTruthy()
    expect(translations.zh).toBeTruthy()
  })

  it('en and zh have identical key sets (no missing translations)', () => {
    const enKeys = Object.keys(translations.en).sort()
    const zhKeys = Object.keys(translations.zh).sort()
    const missingInZh = enKeys.filter((k) => !(k in translations.zh))
    const missingInEn = zhKeys.filter((k) => !(k in translations.en))
    expect(missingInZh, `keys missing in zh: ${missingInZh.join(', ')}`).toEqual([])
    expect(missingInEn, `keys missing in en: ${missingInEn.join(', ')}`).toEqual([])
  })


  /**
   * A zh value that is pure ASCII is almost always English pasted into the
   * Chinese column — the failure that makes a dictionary look complete while
   * half of it never got written. Latin is legitimate for the trade's proper
   * nouns (RS 1M, T2108, VCP…), so a value is allowed through when it still
   * carries Han characters, or when it is listed here on purpose.
   */
  it('zh values are actually Chinese, or deliberately Latin', () => {
    const DELIBERATE = new Set([
      'brand.name', 'nav.briefing',
      // A shell command. Translating it would stop it running.
      'rev.report.cmd',
    ])
    const han = /[\u4e00-\u9fff]/
    const suspects = Object.entries(translations.zh)
      .filter(([k, v]) => !DELIBERATE.has(k) && !han.test(v) && /[A-Za-z]{3}/.test(v))
      .map(([k, v]) => `${k} = "${v}"`)
    expect(suspects, `zh looks like untranslated English:\n${suspects.join('\n')}`).toEqual([])
  })

  it('has no empty string values', () => {
    for (const lang of ['en', 'zh']) {
      for (const [key, val] of Object.entries(translations[lang])) {
        expect(val, `${lang}.${key} is empty`).toBeTruthy()
      }
    }
  })
})
