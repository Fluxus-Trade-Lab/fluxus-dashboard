/**
 * A fraction drawn as countable marks.
 *
 * Design: Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md §5 «偷 1»
 *
 * `4/5` is read; four filled squares beside one empty are counted. Same
 * information, one less step. TSF draws the last five sessions this way and it
 * is the one thing on their site that is unambiguously better than ours — we
 * already use this grammar for votes and appearances, just not here.
 *
 * Isotype rule (Neurath): one mark is one countable thing, and above eight the
 * count is printed rather than drawn, because past that nobody counts — they
 * estimate area, which is the encoding we were avoiding. `of` varies by row
 * here (a group scores over 5 horizons, a proxy over 3), so the empties carry
 * the denominator and two different scales cannot be confused for one.
 */
export default function Squares({ n, of, title }) {
  if (n == null || !of) return <span className="text-[var(--color-text-muted)]">—</span>
  if (of > 8) {
    return <span className="tabular-nums" title={title}>{n}/{of}</span>
  }
  return (
    <span className="inline-flex gap-[2px] align-[-1px]"
          title={title ?? `${n} of ${of}`}
          aria-label={`${n} of ${of}`}>
      {Array.from({ length: of }, (_, i) => (
        <i key={i} className="block w-[7px] h-[11px]"
           style={i < n
             ? { background: 'var(--color-took)' }
             : { border: '1px solid var(--color-untested)' }} />
      ))}
    </span>
  )
}
