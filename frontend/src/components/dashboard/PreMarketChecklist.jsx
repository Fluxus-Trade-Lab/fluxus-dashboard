import { useState, useEffect, useCallback, useRef } from 'react'

const QUESTIONS = [
  { id: 'rules', text: 'Am I following my rules?', options: ['Yes', 'No'] },
  { id: 'environment', text: 'Market environment favorable?', options: ['Yes', 'Somewhat', 'No'] },
  { id: 'sizing', text: 'Am I sized correctly?', options: ['Yes', 'No'] },
  { id: 'setup', text: 'Do I have a clear setup today?', options: ['Clear setup', 'Forcing', 'No setup'] },
  { id: 'emotional', text: 'Emotional state?', options: ['Focused', 'Tilted', 'FOMO', 'Fearful'] },
  { id: 'breakouts', text: 'Breakouts working this week?', options: ['Yes', 'Mixed', 'No'] },
]

const STORAGE_KEY = 'fluxus-checklist'

function todayKey() {
  return new Date().toLocaleDateString('en-CA') // YYYY-MM-DD in local timezone
}

function loadChecklist() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { date: todayKey(), answers: {}, note: '' }
    const parsed = JSON.parse(raw)
    if (parsed.date !== todayKey()) return { date: todayKey(), answers: {}, note: '' }
    return parsed
  } catch {
    return { date: todayKey(), answers: {}, note: '' }
  }
}

function persistChecklist(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export default function PreMarketChecklist() {
  const [state, setState] = useState(loadChecklist)
  const noteTimerRef = useRef(null)

  // Persist immediately for button clicks
  const setAnswer = useCallback((id, value) => {
    setState(prev => {
      const next = { ...prev, answers: { ...prev.answers, [id]: value } }
      persistChecklist(next)
      return next
    })
  }, [])

  // Debounced persist for note typing
  const setNote = useCallback((value) => {
    setState(prev => ({ ...prev, note: value }))
    clearTimeout(noteTimerRef.current)
    noteTimerRef.current = setTimeout(() => {
      setState(prev => { persistChecklist(prev); return prev })
    }, 500)
  }, [])

  useEffect(() => () => clearTimeout(noteTimerRef.current), [])

  const answeredCount = Object.keys(state.answers).length
  const totalCount = QUESTIONS.length

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-5 py-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Pre-Market Checklist
        </h3>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          {answeredCount}/{totalCount}
        </span>
      </div>

      <div className="space-y-2.5">
        {QUESTIONS.map(({ id, text, options }) => (
          <div key={id}>
            <div className="text-xs text-[var(--color-text)] mb-1">{text}</div>
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
          className="w-full px-3 py-2 text-xs bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none outline-none focus:border-[var(--color-text-muted)] font-sans text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]"
        />
      </div>
    </div>
  )
}
