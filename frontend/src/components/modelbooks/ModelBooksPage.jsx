import { useState, useEffect, useMemo } from 'react'
import PageHeader from '../PageHeader'
import LibraryView from './LibraryView'
import TagStats from './TagStats'
import TradingGym from './TradingGym'
import { useLanguage } from '../../i18n/LanguageContext'
import { rich } from '../screener/richText'

/* Four sidecars are merged here, once, so every mode below reads the same
   library:

   index.json      the entries, owned by `pipeline/tools/import_big_movers.py`
   excluded.json   what the quality gate threw out and why — 105 of 1,504 on
                   2026-09-25. Excluded entries are filtered out here rather
                   than hidden behind a switch: Andy, "1 y" to deleting them.
                   Nothing is removed from disk, so the reasons stay auditable.
   analysis.json   the breakout our own rule found, the advance from it, and
                   the low-resolution flag. This is what the list ranks by.
   notes.json      the model-book annotations out of the Obsidian vault, keyed
                   ticker-year. Where a note exists for a ticker-year that is
                   not in the library, it is added as a notes-only card.

   A missing sidecar is not an error. The page renders on index.json alone,
   which is what it did before any of this existed. */

export default function ModelBooksPage() {
  const { t } = useLanguage()
  const [mode, setMode] = useState('library')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const get = (name, fallback) =>
      fetch(`/data/modelbooks/${name}`).then(r => r.json()).catch(() => fallback)
    Promise.all([
      get('index.json', []),
      get('excluded.json', null),
      get('analysis.json', null),
      get('notes.json', null),
    ]).then(([index, excluded, analysis, notes]) => {
      setData({ index, excluded, analysis, notes })
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const { cards, noteCount, excludedCount } = useMemo(() => {
    if (!data) return { cards: [], noteCount: 0, excludedCount: 0 }
    const gate = data.excluded?.entries ?? {}
    const stats = data.analysis?.entries ?? {}
    const notes = data.notes?.entries ?? {}
    const used = new Set()

    const kept = data.index
      .filter(c => !gate[c.id])
      .map(c => {
        const a = stats[c.id] ?? {}
        const key = `${c.ticker}-${c.year}`
        const note = notes[key]
        if (note) used.add(key)
        return {
          ...c,
          pivot: a.pivot ?? null,
          computed_pivot: a.computed_pivot ?? null,
          peak: a.peak ?? null,
          low: a.low ?? 0,
          advance_pct: a.advance_pct ?? null,
          lowres: !!a.lowres,
          note: note ?? null,
          hasNotes: !!note || !!c.key_lessons?.length,
        }
      })

    // notes with no entry behind them: real model-book cards whose history we
    // have not fetched. Shown, and honest about having no bars.
    const orphans = Object.entries(notes)
      .filter(([k]) => !used.has(k))
      .map(([k, n]) => ({
        id: `note-${k.toLowerCase()}`,
        ticker: n.ticker,
        year: n.year,
        source: n.has_traderlion ? 'TraderLion' : 'Market Leaders',
        patterns: [],
        key_lessons: [],
        ohlcv_file: null,
        gain_pct: n.gain_pct ?? null,
        advance_pct: null,
        pivot: null, peak: null, low: 0, lowres: false,
        note: n,
        hasNotes: true,
      }))

    const all = [...kept, ...orphans]
    return {
      cards: all,
      noteCount: all.filter(c => c.hasNotes).length,
      excludedCount: Object.keys(gate).length,
    }
  }, [data])

  if (loading) {
    return (
      <div className="max-w-[1400px] mx-auto py-6 px-4">
        <div className="text-[13px] text-[var(--color-text-muted)] animate-pulse">{t('mb.loading')}</div>
      </div>
    )
  }

  const withBars = cards.filter(c => c.ohlcv_file).length

  return (
    <div className="max-w-[1400px] mx-auto py-6 px-4">
      <PageHeader group="library" title={t('nav.modelbooks')}
        meta={[t('mb.meta.count', { n: cards.length, bars: withBars }),
               t('mb.meta.notes', { n: noteCount }),
               t('mb.meta.excluded', { n: excludedCount })]} />

      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[11px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)]">
          {t('nav.modelbooks')}
        </h2>
        <div className="flex gap-1">
          {[['library', t('mb.mode.library')], ['stats', t('mb.mode.stats')], ['gym', t('mb.mode.gym')]].map(([m, label]) => (
            <button key={m} onClick={() => setMode(m)}
                    className={`px-3 py-1.5 text-[11px] font-medium rounded cursor-pointer transition-colors ${
                      mode === m
                        ? 'bg-[var(--color-active-tab-bg)] text-[var(--color-active-tab-text)]'
                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] bg-[var(--color-surface-raised)]'}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {mode === 'library' ? <LibraryView cards={cards} noteCount={noteCount} />
        : mode === 'stats' ? <TagStats cards={cards} />
        : <TradingGym cards={cards.filter(c => c.ohlcv_file)} />}

      <p className="mt-4 text-[11px] text-[var(--color-text-muted)] leading-relaxed">
        {rich(t('mb.footer'))}
      </p>
    </div>
  )
}
