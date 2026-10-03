import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import ReplayChart, { MaLegend } from './ReplayChart'
import ReplayTransport from './ReplayTransport'
import NotesRail from './NotesRail'
import { patternTag, formatPattern } from './patternTag'
import { useLanguage } from '../../i18n/LanguageContext'
import { dataName } from '../../i18n/names'
import {
  WINDOWS, DEFAULT_WINDOW, acts as computeActs, readout, openingCursor, compareEntries,
} from './replayMath'

/* Layout A, which Andy picked on 2026-09-25 ("3 A"): the chart is the table
   top, the list is one strip above it, the notes are a rail on the right.

   What this replaces: a three-column browser where the chart was the middle
   48% at 350px and the 1,514-row table was the loudest thing on the page. The
   only valuable object here is the chart, so it gets the room. */

const SORTS = [
  { key: 'advance_pct', label: 'mb.sort.advance', hint: 'mb.sort.advanceHint' },
  { key: 'gain_pct', label: 'mb.sort.range', hint: 'mb.sort.rangeHint' },
  { key: 'year', label: 'mb.sort.year', hint: '' },
  { key: 'ticker', label: 'ms.th.ticker', hint: '' },
]

export default function LibraryView({ cards, noteCount }) {
  const { t, lang } = useLanguage()
  const [search, setSearch] = useState('')
  const [patternFilter, setPatternFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [notesOnly, setNotesOnly] = useState(false)
  const [sortKey, setSortKey] = useState('advance_pct')
  const [sortDir, setSortDir] = useState('desc')
  const [selectedId, setSelectedId] = useState(null)
  const [listOpen, setListOpen] = useState(false)
  const [railOpen, setRailOpen] = useState(true)

  const [bars, setBars] = useState(null)
  const [loading, setLoading] = useState(false)
  const [cursor, setCursor] = useState(0)
  const [windowIdx, setWindowIdx] = useState(DEFAULT_WINDOW)
  const [logScale, setLogScale] = useState(true)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const timer = useRef(null)

  const allPatterns = useMemo(() => {
    const s = new Set()
    cards.forEach(c => c.patterns?.forEach(p => s.add(p)))
    return [...s].sort()
  }, [cards])

  const allSources = useMemo(
    () => [...new Set(cards.map(c => c.source))].sort(), [cards])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return cards.filter(c => {
      if (notesOnly && !c.hasNotes) return false
      if (patternFilter !== 'all' && !c.patterns?.includes(patternFilter)) return false
      if (sourceFilter !== 'all' && c.source !== sourceFilter) return false
      if (!q) return true
      return c.ticker.toLowerCase().includes(q)
        || String(c.year).includes(q)
        || c.key_lessons?.some(l => l.toLowerCase().includes(q))
        || c.note?.sources?.some(s => s.labels?.some(x => x.toLowerCase().includes(q)))
    }).sort((a, b) => compareEntries(a, b, sortKey, sortDir))
  }, [cards, search, patternFilter, sourceFilter, notesOnly, sortKey, sortDir])

  const entry = useMemo(() => {
    if (!filtered.length) return null
    return filtered.find(c => c.id === selectedId) || filtered[0]
  }, [filtered, selectedId])

  useEffect(() => {
    if (entry && entry.id !== selectedId) setSelectedId(entry.id)
  }, [entry]) // eslint-disable-line react-hooks/exhaustive-deps

  const index = filtered.findIndex(c => c.id === entry?.id)

  // bars
  useEffect(() => {
    if (!entry?.ohlcv_file) { setBars(null); return }
    let cancelled = false
    setLoading(true)
    setBars(null)
    fetch(`/data/modelbooks/${entry.ohlcv_file}`)
      .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json() })
      .then(d => { if (!cancelled) { setBars(d); setLoading(false) } })
      .catch(() => { if (!cancelled) { setBars(null); setLoading(false) } })
    return () => { cancelled = true }
  }, [entry?.id, entry?.ohlcv_file])

  const stopPlay = useCallback(() => {
    setPlaying(false)
    if (timer.current) { clearInterval(timer.current); timer.current = null }
  }, [])

  // opening position — on the base, not mid-flight
  useEffect(() => {
    stopPlay()
    if (bars?.length) setCursor(openingCursor({ bars, pivot: entry?.pivot ?? null }))
  }, [bars, entry?.pivot, stopPlay])

  const actList = useMemo(() => bars?.length
    ? computeActs({ bars, low: entry?.low, peak: entry?.peak,
                    computed: entry?.computed_pivot ?? entry?.pivot,
                    stated: entry?.note?.breakout })
    : [], [bars, entry])

  // the breakout the readout measures from: the author's when there is one
  const pivotIndex = useMemo(() => {
    const stated = actList.find(a => a.kind === 'stated' && a.key === 'pivot')
    if (stated) return stated.index
    return entry?.pivot ?? null
  }, [actList, entry?.pivot])

  const read = useMemo(
    () => (bars?.length ? readout({ bars, cursor, pivotIndex }) : null),
    [bars, cursor, pivotIndex])

  useEffect(() => () => { if (timer.current) clearInterval(timer.current) }, [])

  const step = useCallback(d => {
    setCursor(c => {
      const next = Math.max(0, Math.min((bars?.length ?? 1) - 1, c + d))
      if (next >= (bars?.length ?? 1) - 1) stopPlay()
      return next
    })
  }, [bars, stopPlay])

  const togglePlay = useCallback(() => {
    if (playing) { stopPlay(); return }
    if (!bars?.length) return
    if (cursor >= bars.length - 1) {
      setCursor(openingCursor({ bars, pivot: entry?.pivot ?? null }))
    }
    setPlaying(true)
    timer.current = setInterval(() => step(1), 130 / speed)
  }, [playing, bars, cursor, entry?.pivot, speed, step, stopPlay])

  useEffect(() => {
    if (!playing) return
    if (timer.current) clearInterval(timer.current)
    timer.current = setInterval(() => step(1), 130 / speed)
    return () => { if (timer.current) clearInterval(timer.current) }
  }, [playing, speed, step])

  const move = useCallback(d => {
    if (!filtered.length) return
    const next = Math.max(0, Math.min(filtered.length - 1, index + d))
    setSelectedId(filtered[next].id)
  }, [filtered, index])

  useEffect(() => {
    const onKey = e => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return
      if (e.key === ' ') { e.preventDefault(); togglePlay() }
      else if (e.key === 'ArrowRight') { e.preventDefault(); stopPlay(); step(1) }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); stopPlay(); step(-1) }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setWindowIdx(i => Math.max(0, i - 1)) }
      else if (e.key === 'ArrowDown') { e.preventDefault(); setWindowIdx(i => Math.min(WINDOWS.length - 1, i + 1)) }
      else if (e.key === 'j') move(1)
      else if (e.key === 'k') move(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [togglePlay, step, move, stopPlay])

  const sortHintKey = SORTS.find(s => s.key === sortKey)?.hint
  const sortHint = sortHintKey ? t(sortHintKey) : ''

  return (
    <div className="flex flex-col gap-2">
      {/* the strip the 1,514-row table became */}
      <div className="flex items-center gap-2 flex-wrap">
        <button onClick={() => setListOpen(o => !o)}
                className="text-[11px] font-medium px-2.5 py-1.5 rounded cursor-pointer
                           bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]">
          {listOpen ? t('mb.list.hide') : t('mb.list.show', { n: filtered.length })}
        </button>
        <button onClick={() => move(-1)} disabled={index <= 0}
                className="text-[11px] px-2 py-1.5 rounded cursor-pointer disabled:opacity-40
                           bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]">↑</button>
        <button onClick={() => move(1)} disabled={index >= filtered.length - 1}
                className="text-[11px] px-2 py-1.5 rounded cursor-pointer disabled:opacity-40
                           bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]">↓</button>
        <input value={search} onChange={e => setSearch(e.target.value)}
               placeholder={t('mb.search')}
               className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)]
                          rounded-3xl px-3 py-1.5 w-44 focus:outline-none
                          focus:ring-1 focus:ring-[var(--color-input-border)]" />
        <select value={patternFilter} onChange={e => setPatternFilter(e.target.value)}
                className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)]
                           rounded-3xl px-2 py-1.5 cursor-pointer focus:outline-none">
          <option value="all">{t('mb.allPatterns')}</option>
          {allPatterns.map(p => <option key={p} value={p}>{dataName(formatPattern(p), lang)}</option>)}
        </select>
        <select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}
                className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)]
                           rounded-3xl px-2 py-1.5 cursor-pointer focus:outline-none">
          <option value="all">{t('mb.allSources')}</option>
          {allSources.map(s => <option key={s} value={s}>{dataName(s, lang)}</option>)}
        </select>
        <label className="flex items-center gap-1.5 text-[11px] text-[var(--color-text-muted)] cursor-pointer select-none"
               title={t('mb.notesOnlyTitle')}>
          <input type="checkbox" checked={notesOnly} className="cursor-pointer"
                 onChange={e => setNotesOnly(e.target.checked)} />
          {t('mb.notesOnly', { n: noteCount })}
        </label>
        <select value={sortKey} onChange={e => setSortKey(e.target.value)} title={sortHint}
                className="text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface)]
                           rounded-3xl px-2 py-1.5 cursor-pointer focus:outline-none ml-auto">
          {SORTS.map(s => <option key={s.key} value={s.key}>{t('mb.sortBy', { label: t(s.label) })}</option>)}
        </select>
        <button onClick={() => setSortDir(d => (d === 'desc' ? 'asc' : 'desc'))}
                className="text-[11px] px-2 py-1.5 rounded cursor-pointer
                           bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]">
          {sortDir === 'desc' ? '↓' : '↑'}
        </button>
      </div>

      {listOpen && (
        <div className="max-h-[38vh] overflow-y-auto rounded-2xl bg-[var(--color-surface)]">
          <table className="w-full text-[13px]">
            <tbody>
              {filtered.slice(0, 400).map(c => (
                <tr key={c.id} onClick={() => { setSelectedId(c.id); setListOpen(false) }}
                    className={`border-b border-[var(--color-border-light)] cursor-pointer ${
                      c.id === entry?.id ? 'ring-1 ring-inset ring-[var(--color-accent)]'
                                         : 'even:bg-[var(--color-surface-alt)] hover:bg-[var(--color-hover-bg)]'}`}>
                  <td className="px-2 py-1.5 text-[11px] font-semibold text-[var(--color-accent)]">{c.ticker}</td>
                  <td className="px-2 py-1.5 text-[11px] font-mono text-[var(--color-text-secondary)]">{c.year}</td>
                  <td className="px-2 py-1.5 text-[11px] font-mono text-[var(--color-text)]">
                    {c.advance_pct != null ? `+${c.advance_pct.toFixed(0)}%` : '—'}
                  </td>
                  <td className="px-2 py-1.5 text-[11px] text-[var(--color-text-muted)]">
                    {c.hasNotes ? t('mb.list.noteMark') : ''}
                  </td>
                  <td className="px-2 py-1.5 text-[11px] text-[var(--color-text-muted)] truncate max-w-[90px]">
                    {dataName(c.source, lang)}
                  </td>
                </tr>
              ))}
              {filtered.length > 400 && (
                <tr><td colSpan={5} className="px-2 py-2 text-[11px] text-[var(--color-text-muted)]">
                  {t('mb.list.more', { n: filtered.length - 400 })}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* the chart, and the rail beside it */}
      <div className="flex gap-2 items-start">
        <div className="flex-1 min-w-0 rounded-2xl overflow-hidden bg-[var(--color-surface)]">
          <div className="flex items-baseline gap-2 px-3 pt-2.5 pb-1 flex-wrap">
            <h3 className="text-[17px] font-semibold text-[var(--color-text-bold)] m-0">
              {entry?.ticker ?? '—'}
            </h3>
            <span className="text-[13px] text-[var(--color-text-muted)]">{entry?.year}</span>
            <span className="text-[11px] text-[var(--color-text-muted)]">{dataName(entry?.source, lang)}</span>
            {read && (
              <span className="text-[13px] font-mono ml-2">
                <span className="text-[var(--color-text-muted)]">{read.date}</span>{' '}
                <span className="text-[var(--color-text-bold)]">{read.close}</span>{' '}
                {read.changePct != null && (
                  <span style={{ color: read.changePct >= 0 ? 'var(--color-took)' : 'var(--color-refused)' }}>
                    {read.changePct >= 0 ? '+' : ''}{read.changePct.toFixed(1)}%
                  </span>
                )}
              </span>
            )}
            {bars?.length > 0 && <span className="ml-auto"><MaLegend /></span>}
            <button onClick={() => setLogScale(s => !s)}
                    className="text-[11px] font-mono px-2 py-1 rounded cursor-pointer
                               bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]">
              {logScale ? 'LOG' : 'LIN'}
            </button>
            <button onClick={() => setRailOpen(o => !o)}
                    className="text-[11px] px-2 py-1 rounded cursor-pointer
                               bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]">
              {railOpen ? t('mb.notes.hide') : t(entry?.hasNotes ? 'mb.notes.show' : 'mb.notes.showNone')}
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-[420px] text-[13px] text-[var(--color-text-muted)]">
              {t('mb.bars.loading')}
            </div>
          ) : !bars?.length ? (
            <div className="flex flex-col items-center justify-center h-[420px] gap-1 px-6 text-center">
              <span className="text-[13px] text-[var(--color-text-muted)]">{t('mb.bars.none')}</span>
              <span className="text-[11px] text-[var(--color-text-muted)]">
                {t('mb.bars.noneSub')}
              </span>
            </div>
          ) : (
            <>
              <ReplayChart bars={bars} cursor={cursor} windowSize={WINDOWS[windowIdx]}
                           logScale={logScale} acts={actList} height={420}
                           lowres={!!entry?.lowres} onScrub={i => { stopPlay(); setCursor(
                             Math.max(0, Math.min(bars.length - 1, i))) }} />
              <ReplayTransport
                barCount={bars.length} cursor={cursor} acts={actList}
                playing={playing} speed={speed} windowSize={WINDOWS[windowIdx]}
                onSeek={i => { stopPlay(); setCursor(i) }}
                onStep={d => { stopPlay(); step(d) }}
                onPlayToggle={togglePlay}
                onSpeed={() => setSpeed(s => (s === 1 ? 2 : s === 2 ? 4 : 1))}
                onWindow={d => setWindowIdx(i => (d === 0 ? DEFAULT_WINDOW
                  : Math.max(0, Math.min(WINDOWS.length - 1, i + d))))}
                onJump={i => { stopPlay(); setCursor(i) }} />
              {read && (
                <div className="grid gap-px bg-[var(--color-border-light)] border-t border-[var(--color-border-light)]"
                     style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(118px, 1fr))' }}>
                  <Cell label={t('mb.cell.vs50')} value={read.vs50dPct} suffix="%" signed />
                  <Cell label={t('mb.cell.relVol')} value={read.relVolume} suffix="×" digits={2} />
                  <Cell label={t('mb.cell.sincePivot')} value={read.sincePivotPct} suffix="%" signed digits={0} />
                  <Cell label={t('mb.cell.fromHigh')} value={read.fromHighPct} suffix="%" digits={1} />
                </div>
              )}
            </>
          )}
        </div>

        {railOpen && (
          <aside className="w-[320px] shrink-0 max-h-[calc(100vh-150px)] overflow-y-auto
                            rounded-2xl bg-[var(--color-surface)] hidden lg:block">
            <NotesRail entry={entry ? { ...entry, libraryNoteCount: noteCount } : null} />
          </aside>
        )}
      </div>

      {railOpen && (
        <div className="lg:hidden rounded-2xl bg-[var(--color-surface)]">
          <NotesRail entry={entry ? { ...entry, libraryNoteCount: noteCount } : null} />
        </div>
      )}
    </div>
  )
}

function Cell({ label, value, suffix = '', signed = false, digits = 1 }) {
  const shown = value == null ? '—'
    : `${signed && value >= 0 ? '+' : ''}${value.toFixed(digits)}${suffix}`
  const colour = value == null ? 'var(--color-text-muted)'
    : signed ? (value >= 0 ? 'var(--color-took)' : 'var(--color-refused)')
    : 'var(--color-text-bold)'
  return (
    <div className="bg-[var(--color-surface)] px-3 py-2">
      <span className="block text-[11px] uppercase tracking-wide text-[var(--color-text-muted)] mb-0.5">
        {label}
      </span>
      <b className="font-mono tabular-nums text-[17px] font-semibold" style={{ color: colour }}>
        {shown}
      </b>
    </div>
  )
}
