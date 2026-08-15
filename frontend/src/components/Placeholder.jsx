import PageHeader from './PageHeader'

/**
 * A page that exists in the rail before it exists as a page.
 *
 * The rule this follows is the one the design system already holds for an
 * unmeasured condition: a slot that disappears when unfilled was never
 * reserved. So the nav entry, the title and the frame are real from day one,
 * and the body says what will be here and what it will be made of — rather
 * than a spinner, a 404, or a page quietly missing from the menu.
 */
export default function Placeholder({ group, title, blurb, willHold = [], source }) {
  return (
    <div>
      <PageHeader group={group} title={title} blurb={blurb}
                  meta={['not built yet', 'the slot is reserved, not missing']} />

      {/* The gold hatch that used to fill this went out with the v3 charter,
          along with every other colour nobody had declared. A dashed edge on
          the untested grey says "reserved" without inventing a hue. */}
      <div className="border border-dashed border-[var(--color-untested)] rounded-3xl p-6
                      max-w-[70ch]">
        <div className="text-[10px] font-mono uppercase tracking-[.24em]
                        text-[var(--color-text-muted)] mb-3">
          Reserved
        </div>
        {willHold.length > 0 && (
          <ul className="m-0 pl-4 space-y-1.5 text-[12.5px] leading-relaxed
                         text-[var(--color-text-secondary)]">
            {willHold.map((w) => <li key={w}>{w}</li>)}
          </ul>
        )}
        {source && (
          <p className="text-[11px] text-[var(--color-text-muted)] mt-4 mb-0">
            Data it will read: <span className="font-mono">{source}</span>
          </p>
        )}
      </div>
    </div>
  )
}
