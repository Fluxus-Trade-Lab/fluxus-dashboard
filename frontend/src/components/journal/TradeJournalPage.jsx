import { useMemo, useState } from 'react'
import { useTradeJournal } from '../../hooks/useTradeJournal'
import { useLanguage } from '../../i18n/LanguageContext'
import TickerLink from '../ticker/TickerLink'

const LESSON_COLORS = {
  'Good execution':    'text-[var(--color-profit)]',
  'Premature trim':    'text-[var(--color-signal-caution)]',
  'Stopped too tight': 'text-orange-500',
  'Failed setup':      'text-[var(--color-loss)]',
  'Choppy / no edge':  'text-[var(--color-text-muted)]',
  'In progress':       'text-[var(--color-accent)]',
}

export default function TradeJournalPage() {
  const { trades, loading } = useTradeJournal()
  const { t: tr } = useLanguage()
  const [filter, setFilter] = useState('all')
  const [sortKey, setSortKey] = useState('entry_date')
  const [sortDir, setSortDir] = useState('desc')

  const filtered = useMemo(() => {
    let arr = trades
    if (filter === 'open') arr = arr.filter(t => !t.closed)
    else if (filter === 'closed') arr = arr.filter(t => t.closed)
    else if (filter && filter.startsWith('lesson:')) {
      const lesson = filter.slice(7)
      arr = arr.filter(t => t.lesson === lesson)
    }
    arr = [...arr]
    arr.sort((a, b) => {
      const av = a[sortKey]; const bv = b[sortKey]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
      return sortDir === 'asc' ? av - bv : bv - av
    })
    return arr
  }, [trades, filter, sortKey, sortDir])

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const stats = useMemo(() => {
    const closed = trades.filter(t => t.closed)
    const total = closed.length
    const totalR = closed.reduce((s, t) => s + (t.realized_R || 0), 0)
    const totalOpt = closed.reduce((s, t) => s + (t.optimal_R || 0), 0)
    const lessonCounts = {}
    for (const t of trades) {
      lessonCounts[t.lesson] = (lessonCounts[t.lesson] || 0) + 1
    }
    return { total, totalR, totalOpt, captureOverall: totalOpt > 0 ? (totalR / totalOpt * 100) : null, lessonCounts }
  }, [trades])

  if (loading) {
    return <div className="text-[var(--color-text-muted)] text-sm py-10 text-center">Loading trade journal…</div>
  }
  if (!trades.length) {
    return <div className="text-[var(--color-text-muted)] text-sm py-10 text-center">
      No trade post-mortems found. Run <code>python -m pipeline.portfolio.trade_postmortem</code>.
    </div>
  }

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-xl font-bold mb-2">{tr('page.trades.title')}</h1>
        <div className="text-[11px] text-[var(--color-text-muted)]">
          {trades.length} trades · {stats.total} closed · realized {stats.totalR.toFixed(1)}R of {stats.totalOpt.toFixed(1)}R available
          {stats.captureOverall != null && ` (${stats.captureOverall.toFixed(0)}% capture)`}
        </div>
      </div>

      {/* Lesson filter chips */}
      <div className="flex flex-wrap gap-1.5 mb-4 text-[11px]">
        <FilterChip current={filter} value="all" onChange={setFilter}>All ({trades.length})</FilterChip>
        <FilterChip current={filter} value="open" onChange={setFilter}>
          Open ({trades.filter(t => !t.closed).length})
        </FilterChip>
        <FilterChip current={filter} value="closed" onChange={setFilter}>
          Closed ({trades.filter(t => t.closed).length})
        </FilterChip>
        {Object.entries(stats.lessonCounts).map(([lesson, count]) => (
          <FilterChip key={lesson} current={filter} value={`lesson:${lesson}`} onChange={setFilter}>
            <span className={LESSON_COLORS[lesson] || ''}>{lesson}</span> ({count})
          </FilterChip>
        ))}
      </div>

      <div className="overflow-x-auto border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)]">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-[var(--color-border)] bg-[var(--color-bg)]">
              <Th onClick={() => handleSort('entry_date')} active={sortKey === 'entry_date'} dir={sortDir}>Entry</Th>
              <Th onClick={() => handleSort('ticker')} active={sortKey === 'ticker'} dir={sortDir}>Ticker</Th>
              <Th onClick={() => handleSort('direction')} active={sortKey === 'direction'} dir={sortDir}>Dir</Th>
              <Th onClick={() => handleSort('hold_days')} active={sortKey === 'hold_days'} dir={sortDir}>Days</Th>
              <Th onClick={() => handleSort('realized_R')} active={sortKey === 'realized_R'} dir={sortDir}>Realized R</Th>
              <Th onClick={() => handleSort('optimal_R')} active={sortKey === 'optimal_R'} dir={sortDir}>Optimal R</Th>
              <Th onClick={() => handleSort('capture_pct')} active={sortKey === 'capture_pct'} dir={sortDir}>Capture</Th>
              <Th onClick={() => handleSort('setup_type')} active={sortKey === 'setup_type'} dir={sortDir}>Setup</Th>
              <Th onClick={() => handleSort('lesson')} active={sortKey === 'lesson'} dir={sortDir}>Lesson</Th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(t => (
              <tr key={t.trade_id} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
                <td className="px-2 py-1.5 whitespace-nowrap">
                  <a href={`#/trade/${t.trade_id}`} className="text-[var(--color-accent)] hover:underline">
                    {String(t.entry_date).slice(0, 10)}
                  </a>
                </td>
                <td className="px-2 py-1.5 font-semibold">
                  <TickerLink symbol={t.ticker} />
                </td>
                <td className={`px-2 py-1.5 ${t.direction === 'long' ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                  {t.direction.toUpperCase()}
                </td>
                <td className="px-2 py-1.5 tabular-nums">{t.hold_days ?? '—'}</td>
                <td className={`px-2 py-1.5 tabular-nums font-semibold ${rColor(t.realized_R)}`}>
                  {fmtR(t.realized_R)}
                </td>
                <td className={`px-2 py-1.5 tabular-nums ${rColor(t.optimal_R)}`}>
                  {fmtR(t.optimal_R)}
                </td>
                <td className="px-2 py-1.5 tabular-nums">
                  {t.capture_pct != null ? `${t.capture_pct.toFixed(0)}%` : '—'}
                </td>
                <td className="px-2 py-1.5 text-[var(--color-text-muted)]">{t.setup_type}</td>
                <td className={`px-2 py-1.5 font-semibold ${LESSON_COLORS[t.lesson] || ''}`}>{t.lesson}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function Th({ children, onClick, active, dir }) {
  return (
    <th
      onClick={onClick}
      className="px-2 py-1.5 text-left cursor-pointer hover:bg-[var(--color-hover-bg)] font-medium text-[var(--color-text-secondary)] uppercase tracking-wide text-[10px] whitespace-nowrap"
    >
      {children}{active && (dir === 'asc' ? ' ↑' : ' ↓')}
    </th>
  )
}

function FilterChip({ current, value, onChange, children }) {
  const isActive = current === value
  return (
    <button
      onClick={() => onChange(value)}
      className={`px-2 py-1 rounded text-[11px] border cursor-pointer ${
        isActive
          ? 'bg-[var(--color-accent)] text-white border-[var(--color-accent)]'
          : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:bg-[var(--color-hover-bg)]'
      }`}
    >
      {children}
    </button>
  )
}

function rColor(r) {
  if (r == null) return 'text-[var(--color-text-muted)]'
  if (r > 0) return 'text-[var(--color-profit)]'
  if (r < 0) return 'text-[var(--color-loss)]'
  return 'text-[var(--color-text-muted)]'
}

function fmtR(r) {
  if (r == null) return '—'
  return `${r >= 0 ? '+' : ''}${r.toFixed(2)}R`
}
