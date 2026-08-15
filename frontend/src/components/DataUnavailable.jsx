import PageHeader from './PageHeader'

/**
 * The page a route becomes when its data did not arrive.
 *
 * Before this existed, three routes answered a failed fetch with a bare
 * sentence on the ground — no breadcrumb, no title, no card. The page stopped
 * being a page, so you lost your place in the site at the exact moment
 * something had gone wrong, which is the worst moment to lose it.
 *
 * Same rule the Placeholder follows: the frame is real whether or not the
 * body is. What changes is only the reading inside it.
 *
 * The pipeline command stays, because the person reading this is the person
 * who runs it — but as a footnote, not as the whole page. A user of the
 * hosted site sees the sentence above it and needs nothing more.
 */
export default function DataUnavailable({ group, title, what, why, command }) {
  return (
    <div>
      <PageHeader group={group} title={title}
                  meta={['no data', 'the page is here, the reading is not']} />

      <div className="bg-[var(--color-surface)] rounded-3xl p-6 max-w-[70ch]">
        <div className="text-[10px] font-mono uppercase tracking-[.24em]
                        text-[var(--color-text-muted)] mb-3">
          Not loaded
        </div>
        <p className="m-0 text-[14px] leading-relaxed text-[var(--color-text)]">
          {what}
        </p>
        {why && (
          <p className="mt-2 mb-0 text-[12.5px] leading-relaxed text-[var(--color-text-secondary)]">
            {why}
          </p>
        )}
        {command && (
          <p className="text-[11px] text-[var(--color-text-muted)] mt-5 mb-0">
            Rebuild it with <span className="font-mono">{command}</span>
          </p>
        )}
      </div>
    </div>
  )
}
