import { useMemo } from 'react'

/**
 * Step through the days an entry actually exists on.
 *
 * Shared because the recap, the founder's notes and the pre-market checklist
 * all need the same walk and two implementations of one control is how they
 * start disagreeing about what "today" means.
 *
 * The walk skips empty stretches — the timeline is the written days plus the
 * current one, so a fortnight of silence is one click rather than fourteen,
 * and today is always reachable whether or not it has been written.
 */
export default function EntryNav({ dates, date, current, onPick, cadence = 'daily' }) {
  const timeline = useMemo(() => {
    const s = new Set(dates)
    s.add(current)
    return [...s].sort().reverse()          // newest first
  }, [dates, current])

  const ix = timeline.indexOf(date)
  const older = ix >= 0 && ix < timeline.length - 1 ? timeline[ix + 1] : null
  const newer = ix > 0 ? timeline[ix - 1] : null
  const isCurrent = date === current
  /* Andy, 2026-08-24: print the date, always. "today" and "this week" are the
     two labels that stop meaning anything the moment you step back one entry
     and then look away — and on a page whose title is now the session date,
     a slot reading "today" was the only thing on screen not saying WHICH. */

  return (
    <div className="flex items-center gap-1.5 text-[11px] font-mono
                    text-[var(--color-text-muted)]">
      <button type="button" disabled={!older} onClick={() => onPick(older)}
              title={older ? `Back to ${older}` : 'Nothing older'}
              aria-label="Older entry"
              className="bg-transparent border-none p-0 px-1 cursor-pointer
                         disabled:opacity-30 disabled:cursor-default
                         hover:text-[var(--color-text)]">‹</button>
      <span title={cadence === 'weekly' ? 'week beginning' : 'entry date'}
            className={isCurrent ? 'text-[var(--color-text-secondary)]' : ''}>
        {date}
      </span>
      <button type="button" disabled={!newer} onClick={() => onPick(newer)}
              title={newer ? `Forward to ${newer}` : 'Nothing newer'}
              aria-label="Newer entry"
              className="bg-transparent border-none p-0 px-1 cursor-pointer
                         disabled:opacity-30 disabled:cursor-default
                         hover:text-[var(--color-text)]">›</button>
      {!isCurrent && (
        <button type="button" onClick={() => onPick(current)}
                title={cadence === 'weekly' ? 'Back to this week' : 'Back to today'}
                className="bg-transparent border-none p-0 ml-1 cursor-pointer
                           underline hover:text-[var(--color-text)]">{current}</button>
      )}
    </div>
  )
}
