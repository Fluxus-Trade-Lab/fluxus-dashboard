import { useState, useCallback, useMemo, useEffect } from 'react'
import OhlcvChart from './OhlcvChart'

const PATTERN_COLORS = {
  cup_with_handle: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300',
  flat_base: 'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300',
  vcp: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300',
  high_tight_flag: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
  pocket_pivot: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300',
  episodic_pivot: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
  range_breakout: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300',
  base_on_base: 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300',
  double_bottom: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300',
  ipo_base: 'bg-lime-50 text-lime-700 dark:bg-lime-950 dark:text-lime-300',
  faulty_base: 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400',
  cup_without_handle: 'bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300',
}

function formatPattern(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function PatternBadge({ pattern }) {
  const colors = PATTERN_COLORS[pattern] || 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]'
  return (
    <span className={`inline-block px-2 py-0.5 text-[10px] font-medium rounded-full ${colors}`}>
      {formatPattern(pattern)}
    </span>
  )
}

function shuffleArray(arr) {
  const shuffled = [...arr]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

export default function StudyMode({ cards }) {
  const [deck, setDeck] = useState(() => shuffleArray(cards))
  const [currentIndex, setCurrentIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [markedForReview, setMarkedForReview] = useState(new Set())
  const [ohlcv, setOhlcv] = useState(null)

  const card = deck[currentIndex]

  // Fetch OHLCV data when card changes
  useEffect(() => {
    if (!card?.ohlcv_file) {
      setOhlcv(null)
      return
    }

    let cancelled = false
    setOhlcv(null)

    fetch(`/data/modelbooks/${card.ohlcv_file}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        if (!cancelled) setOhlcv(data)
      })
      .catch(() => {
        if (!cancelled) setOhlcv(null)
      })

    return () => { cancelled = true }
  }, [card?.id, card?.ohlcv_file])

  const reviewCount = markedForReview.size

  const handleNext = useCallback(() => {
    setRevealed(false)
    setCurrentIndex(prev => {
      if (prev + 1 >= deck.length) {
        // Reshuffle and restart
        setDeck(shuffleArray(cards))
        return 0
      }
      return prev + 1
    })
  }, [deck.length, cards])

  const handleReveal = useCallback(() => {
    setRevealed(true)
  }, [])

  const handleMarkForReview = useCallback(() => {
    setMarkedForReview(prev => {
      const next = new Set(prev)
      if (next.has(card.id)) {
        next.delete(card.id)
      } else {
        next.add(card.id)
      }
      return next
    })
  }, [card?.id])

  const isMarked = card ? markedForReview.has(card.id) : false

  // Keyboard shortcuts: Space=reveal, N=next, M=mark
  useEffect(() => {
    const handleKey = (e) => {
      if (e.target.tagName === 'INPUT') return
      if (e.key === ' ' && !revealed) { e.preventDefault(); handleReveal() }
      else if ((e.key === 'n' || e.key === 'ArrowRight') && revealed) { e.preventDefault(); handleNext() }
      else if (e.key === 'm' && revealed) { e.preventDefault(); handleMarkForReview() }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [revealed, handleReveal, handleNext, handleMarkForReview])

  if (!card) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-xs text-[var(--color-text-muted)]">No cards available</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center">
      {/* Progress bar */}
      <div className="w-full max-w-xl flex items-center justify-between mb-4">
        <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)]">
          Card {currentIndex + 1} of {deck.length}
        </span>
        {reviewCount > 0 && (
          <span className="text-[10px] text-[var(--color-text-muted)]">
            {reviewCount} marked for review
          </span>
        )}
      </div>

      {/* Flashcard */}
      <div className="w-full max-w-xl bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden shadow-sm">
        {/* Chart area */}
        <div className="relative">
          {card.ohlcv_file && ohlcv ? (
            <OhlcvChart data={ohlcv} height={260} showMAs={revealed} showVolume={revealed} />
          ) : (
            <div className="bg-[var(--color-surface-raised)] h-[220px] flex items-center justify-center">
              {!revealed ? (
                <div className="text-center">
                  <div className="text-4xl font-bold text-[var(--color-border)] tracking-wide mb-2">?</div>
                  <div className="text-xs text-[var(--color-text-muted)]">Can you identify the pattern?</div>
                </div>
              ) : (
                <span className="text-3xl font-bold text-[var(--color-text-muted)] tracking-wide">
                  {card.ticker}
                </span>
              )}
            </div>
          )}
          {isMarked && (
            <span className="absolute top-3 right-3 text-[10px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
              Flagged
            </span>
          )}
        </div>

        {/* Content area */}
        <div className="p-5">
          {!revealed ? (
            <div className="flex justify-center">
              <button
                onClick={handleReveal}
                className="px-5 py-2 text-[11px] font-medium rounded bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] hover:bg-[var(--color-hover-bg)] transition-colors cursor-pointer"
              >
                Reveal
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Metadata row */}
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Ticker
                  </span>
                  <span className="text-sm font-semibold text-[var(--color-text-bold)]">{card.ticker}</span>
                </div>
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Year
                  </span>
                  <span className="text-sm text-[var(--color-text)]">{card.year}</span>
                </div>
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Source
                  </span>
                  <span className="text-sm text-[var(--color-text)]">{card.source}</span>
                </div>
                <div className="ml-auto">
                  <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block">
                    Outcome
                  </span>
                  <span className="text-xs font-medium text-[var(--color-text)]">{card.outcome}</span>
                </div>
              </div>

              {/* Patterns */}
              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1.5">
                  Patterns
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {card.patterns.map(p => (
                    <PatternBadge key={p} pattern={p} />
                  ))}
                </div>
              </div>

              {/* Key Lessons */}
              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-muted)] block mb-1.5">
                  Key Lessons
                </span>
                <ul className="space-y-1">
                  {card.key_lessons.map((lesson, i) => (
                    <li key={i} className="text-xs text-[var(--color-text-secondary)] flex gap-2">
                      <span className="text-[var(--color-text-muted)] select-none shrink-0">&bull;</span>
                      {lesson}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={handleNext}
                  className="px-4 py-2 text-[11px] font-medium rounded bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)] hover:bg-[var(--color-hover-bg)] transition-colors cursor-pointer"
                >
                  Next
                </button>
                <button
                  onClick={handleMarkForReview}
                  className={`px-4 py-2 text-[11px] font-medium rounded transition-colors cursor-pointer ${
                    isMarked
                      ? 'bg-amber-50 text-amber-700 hover:bg-amber-100'
                      : 'bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-hover-bg)]'
                  }`}
                >
                  {isMarked ? 'Unmark' : 'Mark for Review'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
