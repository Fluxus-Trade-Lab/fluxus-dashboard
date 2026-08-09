import { useLanguage } from '../i18n/LanguageContext'

/**
 * The one frame every page wears.
 *
 * Design: Fluxus_Brand/visual/explorations/2026-08-08/market_*.html
 *
 * Until now no page had a subject. Objects on them were fine — the ledger, the
 * state board — but a reader arriving at #/breadth met a verdict with nothing
 * saying what the page is for. This supplies exactly three things and stops:
 *
 *   crumb   which half of the product you are standing in
 *   title   the question the page answers, not the data it holds
 *   blurb   one sentence of what it is
 *   meta    the terms it is measured on, right-aligned, small
 *
 * One level. It does not nest, it does not collapse, and nothing below it
 * repeats it. A frame that has its own sub-frames is not a frame.
 */
export default function PageHeader({ group, title, blurb, meta = [] }) {
  const { t } = useLanguage()

  return (
    <header className="pb-3 mb-4 border-b border-[var(--color-v2-ink)]">
      {group && (
        <div className="text-[10px] font-mono uppercase tracking-[.2em] text-[var(--color-text-muted)] pb-3">
          {t(`rail.${group}`)}
          <span className="mx-2 opacity-50">›</span>
          {title}
        </div>
      )}
      <div className="flex flex-col lg:flex-row lg:items-end gap-2 lg:gap-12">
        <div className="min-w-0">
          <h1 className="text-[38px] lg:text-[46px] leading-[.92] font-bold m-0 tracking-[-.01em]"
              style={{ fontFamily: 'var(--font-cond)' }}>
            {title}
          </h1>
          {blurb && (
            <p className="text-[13.5px] leading-relaxed text-[var(--color-text-secondary)] mt-2 mb-0
                          max-w-[62ch]">
              {blurb}
            </p>
          )}
        </div>
        {meta.length > 0 && (
          <div className="lg:ml-auto lg:text-right shrink-0 text-[11px] leading-relaxed
                          text-[var(--color-text-muted)]">
            {meta.map((line, i) => <div key={i}>{line}</div>)}
          </div>
        )}
      </div>
    </header>
  )
}
