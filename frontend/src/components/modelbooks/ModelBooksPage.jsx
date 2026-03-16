import { useState, useEffect } from 'react'
import BrowseView from './BrowseView'
import StudyMode from './StudyMode'

export default function ModelBooksPage() {
  const [mode, setMode] = useState('browse') // 'browse' | 'study'
  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/modelbooks/index.json')
      .then(res => res.json())
      .then(data => { setCards(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-6 px-4">
        <div className="text-xs text-[var(--color-text-muted)] animate-pulse">Loading model books...</div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto py-6 px-4">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Model Books
        </h2>
        <div className="flex gap-1">
          {['browse', 'study'].map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 text-[11px] font-medium rounded cursor-pointer transition-colors ${
                mode === m
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
              }`}
            >
              {m === 'browse' ? 'Browse' : 'Study Mode'}
            </button>
          ))}
        </div>
      </div>

      {mode === 'browse' ? (
        <BrowseView cards={cards} />
      ) : (
        <StudyMode cards={cards} />
      )}
    </div>
  )
}
