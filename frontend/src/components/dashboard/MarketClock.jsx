import { useEffect, useState } from 'react'

/**
 * Four cities, one line.
 *
 * Andy, 2026-08-24: the page title says which SESSION you are reading — the
 * market date, ET, from the payload — and this says what time it is right now
 * in the four places the tape passes through. The two are different questions
 * and they were being answered by one line that said neither ("Today").
 *
 * NEW YORK IS THE ONE THAT MATTERS and it is last, where the eye stops. The
 * other three are there because Andy reads this at Tokyo breakfast, and a
 * London or Paris hour is how he knows how long until the open.
 *
 * The clock is the browser's, not the payload's — it is the only thing on this
 * dashboard that is allowed to be, because it is answering "now" rather than
 * reporting a measurement. Everything dated still comes from the file.
 */
const CITIES = [
  ['Tokyo', 'Asia/Tokyo'],
  ['Paris', 'Europe/Paris'],
  ['London', 'Europe/London'],
  ['New York', 'America/New_York'],
]

const hhmm = (tz, now) => new Intl.DateTimeFormat('en-GB', {
  timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false,
}).format(now)

export default function MarketClock() {
  // Ticks on the minute boundary rather than every 60s from mount, so the
  // displayed minute is never up to 59s stale against the wall clock.
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    let timer
    const schedule = () => {
      const ms = 60000 - (Date.now() % 60000)
      timer = setTimeout(() => { setNow(new Date()); schedule() }, ms + 50)
    }
    schedule()
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="flex flex-wrap gap-x-4 gap-y-0.5 font-mono text-[10px]
                    lg:justify-end tabular-nums">
      {CITIES.map(([name, tz], i) => (
        <span key={tz} className={i === CITIES.length - 1
          ? 'text-[var(--color-text-secondary)]' : ''}>
          <span className="uppercase tracking-[.14em] opacity-70">{name}</span>{' '}
          {hhmm(tz, now)}
        </span>
      ))}
    </div>
  )
}
