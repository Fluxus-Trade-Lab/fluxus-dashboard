import { useLanguage } from '../../i18n/LanguageContext'

/**
 * The three bands a stage page is made of.
 *
 * Not tabs. A stage's parts are not alternatives you choose between — the test
 * is the reading, the ledger is where the money went, and the tools are things
 * you open when you want them. Stacking them says that; a tab strip says they
 * are three views of one thing, which they are not.
 *
 * `kind` drives the colour of the rule only. The real differentiation is what
 * goes inside: the test gets the width, the ledger gets a bar that adds up,
 * and the tools get dashed boxes with no numbers in them at all.
 */
export default function Zone({ kind, children }) {
  const { t } = useLanguage()
  const ink = { test: 'text-[var(--color-accent)]',
                ledger: 'text-[var(--color-signal-caution)]',
                tool: 'text-[var(--color-text-muted)]' }[kind]
  return (
    <section className="mt-8 first:mt-5">
      <div className="flex items-center gap-3 mb-3.5">
        <b className={`text-[10px] font-mono uppercase tracking-[.2em] ${ink}`}>
          {t(`zone.${kind}`)}
        </b>
        <i className="flex-1 h-px bg-[var(--color-border)]" />
      </div>
      {children}
    </section>
  )
}

/** A tool: dashed, no number, no verdict. It waits to be used. */
export function Tool({ title, blurb, children }) {
  const { t } = useLanguage()
  return (
    <details className="rounded-3xl border border-dashed border-[var(--color-border)]
                        px-4 py-3 group">
      <summary className="list-none cursor-pointer">
        <b className="text-[13.5px] block">{title}</b>
        <span className="text-[11.5px] text-[var(--color-text-muted)] block mt-0.5">{blurb}</span>
        <span className="text-[10px] font-mono tracking-[.1em] text-[var(--color-text-secondary)]
                         block mt-2 group-open:hidden">{t('zone.open')} →</span>
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  )
}
