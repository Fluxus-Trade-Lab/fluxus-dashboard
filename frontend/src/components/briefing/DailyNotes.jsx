import { useState, useEffect, useCallback } from 'react'

const STORAGE_PREFIX = 'briefing-notes-'

export default function DailyNotes({ date }) {
  const [text, setText] = useState('')
  const [saved, setSaved] = useState(true)

  // Load notes for this date
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_PREFIX + date) || ''
    setText(stored)
    setSaved(true)
  }, [date])

  // Auto-save with debounce
  useEffect(() => {
    if (saved) return
    const t = setTimeout(() => {
      localStorage.setItem(STORAGE_PREFIX + date, text)
      setSaved(true)
    }, 800)
    return () => clearTimeout(t)
  }, [text, date, saved])

  const handleChange = useCallback((e) => {
    setText(e.target.value)
    setSaved(false)
  }, [])

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          My Notes
        </h3>
        <span className="text-[10px] text-[var(--color-text-muted)]">
          {saved ? 'Saved' : 'Saving...'}
        </span>
      </div>
      <textarea
        value={text}
        onChange={handleChange}
        placeholder="Write your observations, key levels, trade ideas..."
        className="w-full min-h-[160px] p-3 border border-[var(--color-border)] rounded text-sm text-[var(--color-text)]
          bg-[var(--color-bg)] resize-y outline-none focus:border-[var(--color-text-muted)] font-sans leading-relaxed
          placeholder:text-[var(--color-text-muted)]"
      />
    </div>
  )
}
