import { useState, useEffect, useCallback, useRef } from 'react'
import EntryNav from '../EntryNav'
import SaveState from '../SaveState'
import { datesWithEntries, loadRecord, saveRecord, todayKey } from '../../lib/writingStore'

const QUESTIONS = [
  { id: 'rules', text: 'Am I following my rules?', options: ['Yes', 'No'] },
  { id: 'environment', text: 'Market environment favorable?', options: ['Yes', 'Somewhat', 'No'] },
  { id: 'sizing', text: 'Am I sized correctly?', options: ['Yes', 'No'] },
  { id: 'setup', text: 'Do I have a clear setup today?', options: ['Clear setup', 'Forcing', 'No setup'] },
  { id: 'emotional', text: 'Emotional state?', options: ['Focused', 'Tilted', 'FOMO', 'Fearful'] },
  { id: 'breakouts', text: 'Breakouts working this week?', options: ['Yes', 'Mixed', 'No'] },
]

const KIND = 'premarket-checklist'
const LEGACY_KEY = 'fluxus-checklist'

const EMPTY = { answers: {}, note: '' }
const isEmpty = (r) => !r || (!Object.keys(r.answers || {}).length && !(r.note || '').trim())

/**
 * The old store kept ONE slot and threw it away every morning:
 *
 *     if (parsed.date !== todayKey()) return { answers: {}, note: '' }
 *
 * Which is right about today — a new morning is a blank sheet — and wrong
 * about yesterday, which it deleted rather than filed. This is the journal
 * Andy calls 对内求, and a journal you cannot re-read is a habit.
 *
 * Entries are now keyed by date and nothing overwrites an older one. Today
 * still opens blank; the difference is that the rest of them still exist.
 */
function migrateLegacy() {
  try {
    const raw = localStorage.getItem(LEGACY_KEY)
    if (!raw) return
    const old = JSON.parse(raw)
    // Only the one day it held, and only if it is not already filed — this
    // runs on every mount and must not overwrite a newer edit.
    if (old?.date && !isEmpty(old) && !loadRecord(KIND, old.date)) {
      saveRecord(KIND, old.date, { answers: old.answers || {}, note: old.note || '' }, isEmpty)
    }
    localStorage.removeItem(LEGACY_KEY)
  } catch { /* a corrupt legacy blob is not worth failing a page load over */ }
}

export default function PreMarketChecklist() {
  const today = todayKey()
  const [date, setDate] = useState(today)
  const [state, setState] = useState(() => {
    migrateLegacy()
    return loadRecord(KIND, today, EMPTY)
  })
  const [history, setHistory] = useState(() => datesWithEntries(KIND))
  const noteTimerRef = useRef(null)
  const [dirty, setDirty] = useState(false)
  const latest = useRef(state)
  latest.current = state

  // Stepping through history loads that day.
  useEffect(() => { setState(loadRecord(KIND, date, EMPTY)) }, [date])

  const persist = useCallback((next) => {
    saveRecord(KIND, date, next, isEmpty)
    setHistory(datesWithEntries(KIND))
  }, [date])

  // Buttons persist immediately; there is nothing to debounce about a click.
  const setAnswer = useCallback((id, value) => {
    setState(prev => {
      // Clicking the chosen option again clears it — six questions with no way
      // back to "unanswered" made the 0/6 counter unreachable once touched.
      const answers = { ...prev.answers }
      if (answers[id] === value) delete answers[id]
      else answers[id] = value
      const next = { ...prev, answers }
      persist(next)
      return next
    })
  }, [persist])

  const setNote = useCallback((value) => {
    setState(prev => ({ ...prev, note: value }))
    setDirty(true)
    clearTimeout(noteTimerRef.current)
    noteTimerRef.current = setTimeout(() => {
      persist({ ...latest.current, note: value })
      setDirty(false)
    }, 500)
  }, [persist])

  // Flush a pending keystroke on unmount or on stepping away. Deps exclude the
  // note itself — depending on it would re-run this every keystroke and its
  // cleanup would cancel the debounce it exists to back up.
  useEffect(() => () => {
    if (noteTimerRef.current) {
      clearTimeout(noteTimerRef.current)
      saveRecord(KIND, date, latest.current, isEmpty)
    }
  }, [date])

  const saveNow = useCallback(() => {
    clearTimeout(noteTimerRef.current)
    noteTimerRef.current = null
    persist(latest.current)
    setDirty(false)
  }, [persist])

  const answeredCount = Object.keys(state.answers).length
  const totalCount = QUESTIONS.length
  const readOnlyDay = date !== today

  return (
    <div className="bg-[var(--color-surface)] rounded-3xl px-5 py-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Pre-Market Checklist
        </h3>
        <div className="flex items-center gap-3">
          <SaveState onSave={saveNow} dirty={dirty} />
          <EntryNav dates={history} date={date} current={today} onPick={setDate} />
          <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
            {answeredCount}/{totalCount}
          </span>
        </div>
      </div>

      <div className="space-y-2.5">
        {QUESTIONS.map(({ id, text, options }) => (
          <div key={id}>
            <div className="text-[13px] text-[var(--color-text)] mb-1">{text}</div>
            <div className="flex gap-1 flex-wrap">
              {options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => setAnswer(id, opt)}
                  aria-pressed={state.answers[id] === opt}
                  className={`px-2.5 py-1 text-[11px] font-medium rounded cursor-pointer transition-colors border ${
                    state.answers[id] === opt
                      ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] border-transparent'
                      : 'text-[var(--color-text-secondary)] bg-[var(--color-surface)] border-[var(--color-border)] hover:bg-[var(--color-hover-bg)]'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Manual note */}
      <div className="mt-3 pt-3 border-t border-[var(--color-border-light)]">
        <textarea
          value={state.note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Situational notes — what's on your mind today?"
          aria-label="Situational notes"
          rows={2}
          className="w-full px-3 py-2 text-[13px] bg-[var(--color-bg)] rounded-3xl resize-none outline-none focus:border-[var(--color-text-muted)] font-sans text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]"
        />
      </div>
    </div>
  )
}
