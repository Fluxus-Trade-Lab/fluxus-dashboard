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

  /* `suspect.json` is the shape gate's verdict — see
     `scripts/flag-modelbook-outliers.mjs` for what it measures and why. It is
     merged onto the cards HERE, once, so every mode below reads the same
     judgement; only Browse acts on it today. A missing or unreadable file is
     not an error: the library renders exactly as it did before the gate. */
  useEffect(() => {
    Promise.all([
      fetch('/data/modelbooks/index.json').then(res => res.json()),
      fetch('/data/modelbooks/suspect.json').then(res => res.json()).catch(() => null),
    ])
      .then(([data, gate]) => {
        const flags = gate?.entries ?? {}
        setCards(data.map(c => (
          flags[c.id] ? { ...c, suspect: true, suspect_reason: flags[c.id] } : c
        )))
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-6 px-4">
        <div className="text-[13px] text-[var(--color-text-muted)] animate-pulse">Loading model books...</div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto py-6 px-4">
      <PageHeader group="library" title="Model Books"
        meta={['1,514 entries · 1962 to 2026',
               '50 carry pattern tags and lessons',
               'every entry is here because it went up — a survivor set']} />
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
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
