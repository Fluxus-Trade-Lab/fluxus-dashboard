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

  it('has no empty string values', () => {
    for (const lang of ['en', 'zh']) {
      for (const [key, val] of Object.entries(translations[lang])) {
        expect(val, `${lang}.${key} is empty`).toBeTruthy()
      }
    }
  })
})
