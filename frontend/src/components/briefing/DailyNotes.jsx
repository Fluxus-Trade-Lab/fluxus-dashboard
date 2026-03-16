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
    <div className="bg-white border border-stone-200 rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-stone-500">
          My Notes
        </h3>
        <span className="text-[10px] text-stone-400">
          {saved ? 'Saved' : 'Saving...'}
        </span>
      </div>
      <textarea
        value={text}
        onChange={handleChange}
        placeholder="Write your observations, key levels, trade ideas..."
        className="w-full min-h-[160px] p-3 border border-stone-200 rounded text-sm text-stone-700
          bg-stone-50 resize-y outline-none focus:border-stone-400 font-sans leading-relaxed
          placeholder:text-stone-300"
      />
    </div>
  )
}
