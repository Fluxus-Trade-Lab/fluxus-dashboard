import { useState } from 'react'
import { fmtCur } from '../lib/portfolioFormat'

export default function EditablePrice({ value, onChange }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  if (editing) {
    return (
      <input
        autoFocus
        type="number"
        step="0.01"
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onBlur={() => {
          const v = parseFloat(draft)
          if (v > 0) onChange(v)
          setEditing(false)
        }}
        onKeyDown={e => {
          if (e.key === 'Enter') {
            const v = parseFloat(draft)
            if (v > 0) onChange(v)
            setEditing(false)
          }
          if (e.key === 'Escape') setEditing(false)
        }}
        className="w-[70px] px-1 py-0.5 border border-blue-300 rounded text-xs font-sans outline-none"
      />
    )
  }

  return (
    <span
      onClick={() => { setDraft(String(value || '')); setEditing(true) }}
      className="cursor-pointer border-b border-dashed border-[var(--color-input-border)] hover:border-[var(--color-text-secondary)]"
      title="Click to edit"
    >
      {fmtCur(value)}
    </span>
  )
}
