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
 *
 * Redesigned 2026-09-11 (Andy: "折叠区也需要改设计"). The row itself did not
 * change what it promises — still label + count + what it holds, closed by
 * default — only how it looks: a dot instead of a bare +/−, and the note is
 * always on rather than appearing on hover. Hover-only was a scan-ability
 * problem the moment there were eight of these stacked: reading what a row
 * holds meant sweeping the mouse down eight times. The one thing a demoted
 * section cannot also demote is its own label.
 */
export default function Reference({ label, note, count, children }) {
  const [open, setOpen] = useState(false)

  return (
    <section className="border-t border-[var(--color-border-light)] first:border-t-0 py-1">
      <button type="button" onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
              className="w-full flex items-center gap-3 text-left bg-transparent
                         border-0 py-2 px-1 -mx-1 cursor-pointer group rounded-lg
                         hover:bg-[var(--color-hover-bg)]">
        <i aria-hidden="true" className="block w-[7px] h-[7px] rounded-full shrink-0"
           style={{ background: open ? 'var(--color-accent)' : 'var(--color-untested)' }} />
        <span className="text-[13px] font-medium text-[var(--color-text)] shrink-0">
          {label}
        </span>
        {count != null && (
          <span className="text-[11px] font-mono text-[var(--color-text-muted)] shrink-0">
            {count}
          </span>
        )}
        {note && (
          <span className="text-[11px] text-[var(--color-text-muted)] truncate flex-1 min-w-0">
            {note}
          </span>
        )}
        <span className="text-[13px] font-mono text-[var(--color-text-muted)]
                         group-hover:text-[var(--color-text)] shrink-0">
          {open ? '−' : '+'}
        </span>
      </button>

      {open && (
        <div className="mt-2 mb-2 pl-[19px] space-y-3">{children}</div>
      )}
    </section>
  )
}
