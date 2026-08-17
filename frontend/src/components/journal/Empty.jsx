import { useLanguage } from '../../i18n/LanguageContext'

/**
 * "Nothing to show, and here is why" — in the reader's language.
 *
 * Andy's rule for this site's two languages: the sentences a reader reads get
 * translated; the measures do not. Sharpe, MFE, AVG CAPTURED are terms of art
 * and stay put — the repo's own documents mix exactly this way. What was
 * jarring on the Chinese page was not the metric names, it was the prose
 * between them.
 *
 * Empty states are the prose a reader meets most, and they survive whatever
 * these sections are redesigned into, which is why they are shared rather than
 * translated where they stand.
 */
export default function Empty({ k, children }) {
  const { t } = useLanguage()
  return (
    <div className="text-center py-16 text-[12.5px] text-[var(--color-text-muted)]">
      {k ? t(k) : children}
    </div>
  )
}
