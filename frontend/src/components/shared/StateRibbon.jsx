/**
 * Ten weeks of four-state, drawn as one row.
 *
 * Shared from the first use on purpose. Rotation draws it today from ETF bars;
 * the Themes table will draw the same object once `groups_archive.csv` has ten
 * weeks in it. Writing it into the rotation panel would guarantee either a
 * rewrite or a copy later, and a copy is how two ribbons start meaning slightly
 * different things.
 *
 * **The grid is not the window.** Each segment is a fortnight of *drawing*, but
 * the state inside it was computed on month-scale windows — every scheme with a
 * near bucket of two weeks or less flipped sign between half samples
 * (`pipeline/themes/FOUR_STATE_DESIGN.md`). A reader looking at fortnight-wide
 * blocks will assume a fortnight reading, so the caller is required to pass
 * `windowNote` and it is surfaced on hover of every segment.
 *
 * Colour matches `groups/StateBadge` because the same four words must not be
 * two different palettes in one product. An unmeasured segment is drawn as an
 * outline rather than a colour — the board's rule that unmeasurable is never
 * zero, carried into a shape.
 */

const FILL = {
  Leading: 'bg-emerald-500/70',
  Weakening: 'bg-amber-500/70',
  Improving: 'bg-sky-500/70',
  Lagging: 'bg-rose-500/70',
}

const pct = (v) => (v == null ? '—' : `${(v * 100).toFixed(1)}%`)

export default function StateRibbon({ steps, labels, windowNote }) {
  if (!steps?.length) {
    return <span className="text-[var(--color-text-muted)] text-[11px]">—</span>
  }

  return (
    <span className="flex gap-[2px] items-stretch h-[14px] w-full">
      {steps.map((s, i) => {
        const label = labels?.[i] ?? `step ${i + 1}`
        const title = s?.state
          ? `${label}: ${s.state} — level ${pct(s.level)}, accel ${pct(s.accel)}` +
            (windowNote ? `\n${windowNote}` : '')
          : `${label}: not measurable`
        return (
          <span
            key={i}
            title={title}
            aria-label={title}
            className={`flex-1 rounded-[2px] ${
              s?.state
                ? FILL[s.state] ?? 'bg-[var(--color-text-muted)]/40'
                : 'border border-dashed border-[var(--color-border)]'
            }`}
          />
        )
      })}
    </span>
  )
}

export { FILL as STATE_FILL }
