/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { translations } from './translations'

const LanguageContext = createContext(null)

const STORAGE_KEY = 'fluxus-lang'

// one warning per key per session, not one per render
const warned = new Set()

function getInitialLang() {
  if (typeof window === 'undefined') return 'en'
  const saved = localStorage.getItem(STORAGE_KEY)
  return saved === 'zh' || saved === 'en' ? saved : 'en'
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(getInitialLang)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, lang)
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', lang === 'zh' ? 'zh-CN' : 'en')
    }
  }, [lang])

  const toggle = useCallback(() => setLang((l) => (l === 'zh' ? 'en' : 'zh')), [])

  /**
   * t('namespace.key') → the string in the current language.
   *
   * Falls back to English, then to the key itself. In development a Chinese
   * miss is logged once per key: silent fallback makes an untranslated screen
   * look finished, which is the same lie as an unmeasured value rendering as
   * zero. Production stays quiet — a reader should get English, not a console.
   */
  const t = useCallback(
    (key) => {
      const dict = translations[lang] || translations.en
      if (dict[key] != null) return dict[key]
      if (import.meta.env?.DEV && lang !== 'en' && !warned.has(key)) {
        warned.add(key)
        console.warn(`[i18n] no ${lang} for "${key}" — falling back to English`)
      }
      if (translations.en[key] != null) return translations.en[key]
      return key
    },
    [lang],
  )

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggle, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) {
    // Safe fallback if a component renders outside the provider (e.g. isolated tests).
    return { lang: 'en', setLang: () => {}, toggle: () => {}, t: (k) => translations.en[k] ?? k }
  }
  return ctx
}
