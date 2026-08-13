import { useState, useEffect } from 'react'
import PageHeader from '../PageHeader'
import BrowseView from './BrowseView'
import StudyMode from './StudyMode'
import TagStats from './TagStats'
import TradingGym from './TradingGym'

export default function ModelBooksPage() {
  const [mode, setMode] = useState('browse') // 'browse' | 'study' | 'stats' | 'gym'
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
        <div className="text-[12.5px] text-[var(--color-text-muted)] animate-pulse">Loading model books...</div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto py-6 px-4">
      <PageHeader group="library" title="Model Books"
        blurb="Historical winners and the bases they built before they ran. Reference for what a setup looked like beforehand — not a record of anything you did."
        meta={['1,514 entries · 1962 to 2026',
               '50 carry pattern tags and lessons',
               'every entry is here because it went up — a survivor set']} />
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          Model Books
        </h2>
        <div className="flex gap-1">
          {['browse', 'study', 'stats', 'gym'].map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 text-[11px] font-medium rounded cursor-pointer transition-colors ${
                mode === m
                  ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'
              }`}
            >
              {m === 'browse' ? 'Browse' : m === 'study' ? 'Study Mode' : m === 'stats' ? 'Stats' : 'Gym'}
            </button>
          ))}
        </div>
      </div>

      {mode === 'browse' ? (
        <BrowseView cards={cards} />
      ) : mode === 'study' ? (
        <StudyMode cards={cards} />
      ) : mode === 'stats' ? (
        <TagStats cards={cards} />
      ) : (
        <TradingGym cards={cards} />
      )}
    </div>
  )
}
