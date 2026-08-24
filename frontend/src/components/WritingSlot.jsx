import { useCallback, useEffect, useRef, useState } from 'react'
import { datesWithEntries, loadEntry, saveEntry, todayKey, weekKey } from '../lib/writingStore'
import EntryNav from './EntryNav'
import SaveState from './SaveState'

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
 * STAY EMPTY HONESTLY. A day with nothing written is a placeholder and a dashed
 * frame, never a filled-in one. The paragraph that used to say so out loud came
 * off on 2026-08-24 — it was addressed to the only person who writes here, who
 * knows.
 */
export default function WritingSlot({
  label,
  kind,
  cadence = 'daily',      // 'daily' | 'weekly'
  placeholder,
  rows = 8,
  className = '',
}) {
  const keyFor = cadence === 'weekly' ? weekKey : todayKey
  const current = keyFor()

  const [date, setDate] = useState(current)
  const [text, setText] = useState(() => loadEntry(kind, current))
  const [history, setHistory] = useState(() => datesWithEntries(kind))
  const timer = useRef(null)
  const [dirty, setDirty] = useState(false)
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
    setDirty(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      saveEntry(kind, date, v)
      setHistory(datesWithEntries(kind))
      setDirty(false)
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

  // Explicit save: the autosave is invisible and these words cannot be
  // regenerated, so there is a way to make it happen and see that it did.
  const saveNow = useCallback(() => {
    clearTimeout(timer.current)
    timer.current = null
    saveEntry(kind, date, latest.current)
    setHistory(datesWithEntries(kind))
    setDirty(false)
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
        <div className="flex items-center gap-3">
          <SaveState onSave={saveNow} dirty={dirty} />
          <EntryNav dates={history} date={date} current={current}
                    cadence={cadence} onPick={setDate} />
        </div>
      </div>

      <textarea
        value={text}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        placeholder={placeholder}
        /* 15px, not the 12.5px the rest of this page reads at (Andy,
           2026-08-24: at least close to the NEUTRAL badge). Those two were
           already the SAME size — the badge only looked bigger because it is
           600-weight, uppercase and reversed out of an ink block. Matching it
           by number would have changed nothing, so this goes past it: 15px is
           the largest step that still lets the weekly note's six lines sit in
           the box without scrolling. It is also the only text on this page a
           person wrote, which is reason enough for it to be the largest. */
        className="mt-2 w-full resize-y bg-transparent border-none outline-none
                   text-[15px] leading-[1.55] text-[var(--color-text)]
                   placeholder:text-[var(--color-text-muted)]
                   placeholder:text-[13px]
                   focus-visible:ring-0"
      />

      {/* The reserved copy — "written by hand on the days there is something
          to say, an empty slot on the other days is the honest state" — stood
          under the box until 2026-08-24. Andy: it explained the box to the one
          person who wrote it. The box got the space instead. The empty state
          is still honest; it is just silent about it now. */}
      {written > 1 && (
        <p className="text-[10px] font-mono text-[var(--color-text-muted)] m-0 mt-1.5">
          {written} written
        </p>
      )}
    </section>
  )
}
