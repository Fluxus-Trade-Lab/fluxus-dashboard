import { useCallback, useEffect, useRef, useState } from 'react'
import { datesWithEntries, loadEntry, saveEntry, todayKey, weekKey } from '../lib/writingStore'
import EntryNav from './EntryNav'

/**
 * A dated slot for words Andy writes himself, with its own back-catalogue.
 *
 * These slots used to be dashed empty frames with a paragraph explaining that
 * they were reserved. Reserving space is the right instinct — a card that
 * appears only once it is full was never reserved — but the frame never became
 * writable, so the reservation never came due.
 *
 * Two things it must do that a textarea does not:
 *
 * READ BACK. The point of a journal is the second reading. Arrows step through
 * the days that actually carry text, so an empty stretch is skipped rather than
 * walked. Today is always reachable, whether or not it has been written.
 *
 * STAY EMPTY HONESTLY. A day with nothing written shows the reserved copy, not
 * a blank box pretending to be an entry. Same rule the rest of the site keeps:
 * absent is a reading, zero is a claim.
 */
export default function WritingSlot({
  label,
  kind,
  cadence = 'daily',      // 'daily' | 'weekly'
  reserved,               // the copy shown on a day with nothing written
  placeholder,
  rows = 3,
  className = '',
}) {
  const keyFor = cadence === 'weekly' ? weekKey : todayKey
  const current = keyFor()

  const [date, setDate] = useState(current)
  const [text, setText] = useState(() => loadEntry(kind, current))
  const [history, setHistory] = useState(() => datesWithEntries(kind))
  const timer = useRef(null)
  // The flush-on-leave effect must see the newest text without depending on
  // it. Depending on `text` re-ran that effect every keystroke, and its
  // cleanup cancelled the debounce it was meant to back up — every character
  // typed killed its own save. A ref changes without re-running effects.
  const latest = useRef(text)
  latest.current = text

  // Reload when stepping through history.
  useEffect(() => { setText(loadEntry(kind, date)) }, [kind, date])

  // Debounced, because this fires per keystroke. The in-memory value is the
  // source of truth while typing, so a failed write never eats a character.
  const onChange = useCallback((v) => {
    setText(v)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      saveEntry(kind, date, v)
      setHistory(datesWithEntries(kind))
    }, 600)
  }, [kind, date])

  // A pending keystroke must not be lost to a step backwards or an unmount.
  // Deps are the entry's identity only — see the ref above.
  useEffect(() => () => {
    if (timer.current) {
      clearTimeout(timer.current)
      timer.current = null
      saveEntry(kind, date, latest.current)
    }
  }, [kind, date])

  const isCurrent = date === current

  const written = new Set([...history, ...(text.trim() ? [date] : [])]).size

  return (
    <section className={`rounded-3xl border px-4 py-3 ${
      text.trim() ? 'border-[var(--color-border)]' : 'border-dashed border-[var(--color-border)]'
    } ${className}`}>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[10px] font-mono uppercase tracking-[.24em]
                         text-[var(--color-text-muted)]">{label}</span>
        <EntryNav dates={history} date={date} current={current}
                  cadence={cadence} onPick={setDate} />
      </div>

      <textarea
        value={text}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        placeholder={placeholder}
        className="mt-2 w-full resize-y bg-transparent border-none outline-none
                   text-[12.5px] leading-relaxed text-[var(--color-text)]
                   placeholder:text-[var(--color-text-muted)]
                   focus-visible:ring-0"
      />

      {!text.trim() && reserved && (
        <p className="text-[11px] leading-relaxed text-[var(--color-text-muted)] m-0">
          {reserved}
        </p>
      )}
      {written > 1 && (
        <p className="text-[10px] font-mono text-[var(--color-text-muted)] m-0 mt-1.5">
          {written} written
        </p>
      )}
    </section>
  )
}
