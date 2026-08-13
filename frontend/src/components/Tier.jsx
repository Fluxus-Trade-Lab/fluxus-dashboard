/**
 * The three tiers a page is made of.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md §4
 *   «一页 = 一个主体 + 它的证据 + 折叠起来的参考»
 *
 * The first attempt at this only built two tiers — visible and folded — and
 * that is not the same structure. Two tiers still leaves everything visible at
 * equal weight, which was the original complaint; the page reads as a wall
 * again, just a shorter one. The middle tier is the one that does the work:
 * evidence is open, but it is open *underneath* something, and it has to look
 * subordinate or it competes to be the subject.
 *
 * SUBJECT   exactly one per page. No marker — it is first and it is largest,
 *           and a label would only be telling you what the layout already says.
 * EVIDENCE  open, smaller, introduced by a rule that names what it supports.
 * REFERENCE folded. Lives in <Reference>, not here.
 */
export default function Tier({ label, supports, children }) {
  return (
    <section className="pt-5">
      <div className="flex items-baseline gap-3 pb-2">
        <span className="text-[10px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">
          {label}
        </span>
        {supports && (
          <span className="text-[11px] text-[var(--color-text-muted)]">{supports}</span>
        )}
        <i className="flex-1 h-px bg-[var(--color-border)]" />
      </div>
      {children}
    </section>
  )
}
