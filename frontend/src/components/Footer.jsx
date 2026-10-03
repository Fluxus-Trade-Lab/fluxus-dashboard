import { formatTimestamp } from '../lib/format'
import { useLanguage } from '../i18n/LanguageContext'

export default function Footer({ lastUpdated, isOffline }) {
  const { lang, t } = useLanguage()
  return (
    <footer className="flex items-center justify-center gap-2 py-4 text-[11px] text-[var(--color-text-muted)] font-mono">
      <span>{t('sh.footer.updated', { ts: formatTimestamp(lastUpdated, lang) })}</span>
      {isOffline && (
        <span className="px-1.5 py-0.5 bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] rounded uppercase tracking-wider text-[11px] font-medium">
          {t('sh.footer.cached')}
        </span>
      )}
    </footer>
  )
}
