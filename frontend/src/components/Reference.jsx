import { useState } from 'react'

/**
 * Demoted, not deleted.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md §4
 *
 * Market State rendered 4,747 numbers across thirteen objects, all at the same
 * weight, so none of them was the subject. The fix is not to print fewer
 * numbers — the denominators and the falsification lines are what separates us
 * from a site that says «Gold Miners +14.86%» and stops. The fix is rank: one
 * subject, its evidence, and everything that answers «where» rather than «so
 * what» folded behind a line that says what it holds.
 *
 * So the label must be specific. «Show more» hides the fact that something was
 * hidden; «Historical breadth series — 6 charts» is a reader deciding, and a
 * reader who never opens it has still been told it exists.
 */
export default function Reference({ label, note, count, children }) {
  const [open, setOpen] = useState(false)

  return (
    <section className="border-t border-[var(--color-border)] pt-2">
      <button type="button" onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
              className="w-full flex items-baseline gap-3 text-left bg-transparent
                         border-0 p-0 cursor-pointer group">
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]
                         group-hover:text-[var(--color-text)] w-3">
          {open ? '−' : '+'}
        </span>
        <span className="text-[11px] font-mono uppercase tracking-[.2em]
                         text-[var(--color-text-muted)] group-hover:text-[var(--color-text)]">
          {label}
        </span>
        {count != null && (
          <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
            {count} {count === 1 ? 'object' : 'objects'}
          </span>
        )}
        {note && (
          /* the note earns its ink on approach: label and count are the
             always-on promise, the description appears when the reader is
             already looking at the line */
          <span className="text-[11px] text-[var(--color-text-muted)] truncate
                           opacity-0 group-hover:opacity-100 transition-opacity">
            {note}
          </span>
        )}
      </button>

      {open && <div className="mt-3 space-y-3">{children}</div>}
    </section>
  )
}
