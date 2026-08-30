import { freshness } from './dataFreshness'

/**
 * The page saying how old it is, when it is old.
 *
 * Silent by default, and that silence is the reading: nothing here means the
 * file carries a session recent enough that there is nothing to say. It only
 * appears once the data is two weekdays back — see `dataFreshness.js` for why
 * a gap of one is normal and why the unit is weekdays rather than sessions.
 *
 * COLOUR: ink while it is merely behind, the pair's red once it is four
 * weekdays back. Red alone, with no blue anywhere near it, is this site's mark
 * for a binding constraint — and a dashboard four sessions stale is exactly
 * that: nothing on the page can be acted on until it is fixed.
 */
export default function DataFreshnessBadge({ sessionDate }) {
  const f = freshness(sessionDate)
  if (!f) return null

  const alarm = f.level === 'alarm'
  const nice = new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', timeZone: 'UTC',
  }).format(new Date(`${f.date}T00:00:00Z`))

  return (
    <span
      className="inline-flex items-baseline gap-1.5 font-mono text-[10px]
                 px-2 py-[3px] rounded-full"
      style={{
        color: alarm ? 'var(--color-refused)' : 'var(--color-text-secondary)',
        border: `1px ${alarm ? 'solid' : 'dashed'} ${
          alarm ? 'var(--color-refused)' : 'var(--color-border)'}`,
      }}
      title={`Newest session on file is ${f.date}. The nightly job publishes one `
             + `session a weekday; this page shows what the file holds, never more.`}>
      <b className="font-semibold tabular-nums">{f.behind}</b>
      <span>weekdays behind</span>
      <span style={{ opacity: 0.6 }}>· newest {nice}</span>
    </span>
  )
}
