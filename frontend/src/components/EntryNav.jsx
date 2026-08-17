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
  const nowWord = cadence === 'weekly' ? 'this week' : 'today'

  return (
    <div className="flex items-center gap-1.5 text-[10px] font-mono
                    text-[var(--color-text-muted)]">
      <button type="button" disabled={!older} onClick={() => onPick(older)}
              title={older ? `Back to ${older}` : 'Nothing older'}
              aria-label="Older entry"
              className="bg-transparent border-none p-0 px-1 cursor-pointer
                         disabled:opacity-30 disabled:cursor-default
                         hover:text-[var(--color-text)]">‹</button>
      <span title={cadence === 'weekly' ? 'week beginning' : 'entry date'}>
        {isCurrent ? nowWord : date}
      </span>
      <button type="button" disabled={!newer} onClick={() => onPick(newer)}
              title={newer ? `Forward to ${newer}` : 'Nothing newer'}
              aria-label="Newer entry"
              className="bg-transparent border-none p-0 px-1 cursor-pointer
                         disabled:opacity-30 disabled:cursor-default
                         hover:text-[var(--color-text)]">›</button>
      {!isCurrent && (
        <button type="button" onClick={() => onPick(current)}
                className="bg-transparent border-none p-0 ml-1 cursor-pointer
                           underline hover:text-[var(--color-text)]">{nowWord}</button>
      )}
    </div>
  )
}
