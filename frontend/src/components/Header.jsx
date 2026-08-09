import { formatTimestamp } from '../lib/format'
import { useTheme } from '../hooks/useTheme'
import { useLanguage } from '../i18n/LanguageContext'

/**
 * Status bar, not navigation. The sections moved to Rail.jsx when the nav split
 * into MARKET and MY BOOK — nine flat buttons could not carry that split, and
 * two labelled groups do not fit across the top.
 *
 * What stays here is everything that is true of the whole app rather than of a
 * page: when the data was last written, whether we are offline, language, theme.
 *
 * Briefing is gone from both. briefs.json holds five entries dated 2026-03-17
 * to 03-21, so the page served five-month-old writing as today's brief. The
 * route still resolves, so sent links keep working; put it back when something
 * writes daily, or delete the page.
 */
export default function Header({ lastUpdated, isOffline }) {
  const { theme, toggle } = useTheme()
  const { lang, toggle: toggleLang, t } = useLanguage()

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <div className="flex items-center gap-3">
        {/* the mark lives in the rail on wide screens; repeated here only where
            there is no rail to carry it */}
        <h1 className="lg:hidden text-sm font-semibold tracking-tight text-[var(--color-text)]">
          Fluxus Capital
        </h1>
        {isOffline && (
          <span className="px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] rounded">
            {t('header.offline')}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="text-[10px] text-[var(--color-text-muted)] font-mono hidden sm:block">
          {formatTimestamp(lastUpdated)}
        </div>
        <button
          onClick={toggleLang}
          className="h-7 px-2 flex items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors cursor-pointer border-none text-[11px] font-semibold tracking-wide focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]"
          title={t('header.language')}
          aria-label={t('header.language')}
        >
          <span className={lang === 'en' ? 'text-[var(--color-text)]' : ''}>EN</span>
          <span className="mx-0.5 opacity-40">/</span>
          <span className={lang === 'zh' ? 'text-[var(--color-text)]' : ''}>中文</span>
        </button>
        <button
          onClick={toggle}
          className="w-7 h-7 flex items-center justify-center rounded-full bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors cursor-pointer border-none text-sm"
          title={theme === 'dark' ? t('header.lightMode') : t('header.darkMode')}
        >
          {theme === 'dark' ? '\u2600' : '\u263E'}
        </button>
      </div>
    </header>
  )
}
