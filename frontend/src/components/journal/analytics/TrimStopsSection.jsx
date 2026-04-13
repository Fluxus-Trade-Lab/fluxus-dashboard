import { useState, useMemo, Fragment } from 'react'
import StatCard from '../../portfolio/ui/StatCard'
import { fmtCur, fmtPct, fmt } from '../../portfolio/lib/portfolioFormat'

const INITIAL_ROWS = 8

export default function TrimStopsSection({ trimAnalysis, stopAnalysis }) {
  const [expandedTickers, setExpandedTickers] = useState({})
  const [showAllTrims, setShowAllTrims] = useState(false)
  const [showAllStops, setShowAllStops] = useState(false)

  const toggleTicker = (key) => setExpandedTickers(prev => ({ ...prev, [key]: !prev[key] }))

  // Trim summary stats
  const trimStats = {
    total: trimAnalysis.length,
    tooEarlyPct: trimAnalysis.length > 0
      ? (trimAnalysis.filter(t => t.tooEarly).length / trimAnalysis.length) * 100 : 0,
    avgLeftOnTable: trimAnalysis.length > 0
      ? trimAnalysis.reduce((s, t) => s + t.leftOnTable, 0) / trimAnalysis.length : 0,
    avgCaptured: trimAnalysis.length > 0
      ? trimAnalysis.reduce((s, t) => s + t.captured, 0) / trimAnalysis.length : 0,
  }

  // Group trims by ticker — aggregate per ticker, sorted by worst "left on table"
  const trimGroups = useMemo(() => {
    const byTicker = {}
    trimAnalysis.forEach(t => {
      const key = `${t.ticker}-${t.direction}`
      if (!byTicker[key]) byTicker[key] = { ticker: t.ticker, direction: t.direction, trims: [] }
      byTicker[key].trims.push(t)
    })
    return Object.values(byTicker).map(g => ({
      ...g,
      trimCount: g.trims.length,
      avgLeftOnTable: g.trims.reduce((s, t) => s + t.leftOnTable, 0) / g.trims.length,
      avgCaptured: g.trims.reduce((s, t) => s + t.captured, 0) / g.trims.length,
      tooEarlyCount: g.trims.filter(t => t.tooEarly).length,
      worstLeft: Math.max(...g.trims.map(t => t.leftOnTable)),
    })).sort((a, b) => b.avgLeftOnTable - a.avgLeftOnTable)
  }, [trimAnalysis])

  const visibleTrimGroups = showAllTrims ? trimGroups : trimGroups.slice(0, INITIAL_ROWS)

  // Stop summary stats
  const stopStats = {
    total: stopAnalysis.length,
    tooTightPct: stopAnalysis.length > 0
      ? (stopAnalysis.filter(t => t.stopTooTight).length / stopAnalysis.length) * 100 : 0,
    avgStopDist: stopAnalysis.length > 0
      ? stopAnalysis.reduce((s, t) => s + t.stopDistPct, 0) / stopAnalysis.length : 0,
  }

  const visibleStops = showAllStops ? stopAnalysis : stopAnalysis.slice(0, INITIAL_ROWS)

  // Actionable callouts
  const callouts = []
  if (trimStats.tooEarlyPct > 30 && trimAnalysis.length >= 3) {
    callouts.push({
      type: 'warning',
      text: `You trimmed too early ${fmt(trimStats.tooEarlyPct, 0)}% of the time, capturing only ${fmt(trimStats.avgCaptured, 0)}% of the move on average. Consider delaying first trim or using trailing stops.`,
    })
  }
  if (stopStats.tooTightPct > 25 && stopAnalysis.length >= 3) {
    callouts.push({
      type: 'warning',
      text: `${fmt(stopStats.tooTightPct, 0)}% of stopped-out trades recovered 5%+ — stops may be too tight (avg distance: ${fmt(stopStats.avgStopDist, 1)}%).`,
    })
  }
  const highBetaStops = stopAnalysis.filter(s => s.recoveryPct > 10)
  if (highBetaStops.length >= 2) {
    callouts.push({
      type: 'neutral',
      text: `${highBetaStops.length} trades had 10%+ recovery after stop-out — likely high-beta names needing wider stops.`,
    })
  }

  return (
    <div className="space-y-5">
      {/* Actionable callouts — moved to top */}
      {callouts.length > 0 && (
        <div className="space-y-2">
          {callouts.map((c, i) => (
            <div key={i} className={`flex gap-2 text-sm px-3 py-2 rounded-md border ${
              c.type === 'warning' ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              : c.type === 'positive' ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-[var(--color-surface)] border-[var(--color-border)] text-[var(--color-text-secondary)]'
            }`}>
              <span className="flex-shrink-0">{c.type === 'warning' ? '!' : c.type === 'positive' ? '+' : '-'}</span>
              <span>{c.text}</span>
            </div>
          ))}
        </div>
      )}

      {/* Trim Analysis */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Trim Analysis
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <StatCard label="Trims Analyzed" value={trimStats.total} />
          <StatCard label="Too Early %" value={fmtPct(trimStats.tooEarlyPct)}
            colorClass={trimStats.tooEarlyPct > 40 ? 'text-red-500' : trimStats.tooEarlyPct > 25 ? 'text-amber-500' : 'text-green-600'} />
          <StatCard label="Avg Left on Table" value={fmtPct(trimStats.avgLeftOnTable)}
            colorClass={trimStats.avgLeftOnTable > 5 ? 'text-amber-500' : ''} />
          <StatCard label="Avg Captured" value={fmtPct(trimStats.avgCaptured)}
            colorClass={trimStats.avgCaptured > 70 ? 'text-green-600' : 'text-amber-500'} />
        </div>

        {trimGroups.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Ticker', 'Dir', 'Trims', 'Early', 'Avg Left%', 'Worst Left%', 'Avg Captured%'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleTrimGroups.map((g, idx) => {
                  const key = `${g.ticker}-${g.direction}`
                  const expanded = expandedTickers[`trim-${key}`]
                  return (
                    <Fragment key={key}>
                      <tr
                        className={`${idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'} cursor-pointer hover:bg-[var(--color-surface-raised)]`}
                        onClick={() => toggleTicker(`trim-${key}`)}
                      >
                        <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">
                          <span className="inline-block w-3.5 text-[var(--color-text-muted)] text-[10px]">{expanded ? '▼' : '▶'}</span>
                          {g.ticker}
                        </td>
                        <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">
                          <span className={g.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{g.direction?.toUpperCase()}</span>
                        </td>
                        <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{g.trimCount}</td>
                        <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${g.tooEarlyCount > 0 ? 'text-amber-500' : 'text-green-600'}`}>
                          {g.tooEarlyCount}/{g.trimCount}
                        </td>
                        <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${g.avgLeftOnTable > 5 ? 'text-amber-500' : 'text-green-600'}`}>
                          {fmtPct(g.avgLeftOnTable)}
                        </td>
                        <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${g.worstLeft > 10 ? 'text-red-500' : g.worstLeft > 5 ? 'text-amber-500' : ''}`}>
                          {fmtPct(g.worstLeft)}
                        </td>
                        <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${g.avgCaptured > 70 ? 'text-green-600' : 'text-amber-500'}`}>
                          {fmtPct(g.avgCaptured)}
                        </td>
                      </tr>
                      {expanded && g.trims.map((t, i) => (
                        <tr key={`${t.trimDate}-${i}`} className="bg-[var(--color-surface-raised)]">
                          <td className="px-2 py-1 border-b border-[var(--color-border-light)] pl-7 text-[var(--color-text-muted)]" colSpan={2}>
                            Trim {t.trimIndex} &middot; {t.trimDate} &middot; {fmtCur(t.trimPrice)}
                          </td>
                          <td className="px-2 py-1 border-b border-[var(--color-border-light)] tabular-nums text-[var(--color-text-muted)]" colSpan={2}>
                            Peak {fmtCur(t.peakAfterTrim)} ({t.peakDate})
                          </td>
                          <td className={`px-2 py-1 border-b border-[var(--color-border-light)] tabular-nums ${t.leftOnTable > 5 ? 'text-amber-500' : 'text-green-600'}`}>
                            {fmtPct(t.leftOnTable)}
                          </td>
                          <td className="px-2 py-1 border-b border-[var(--color-border-light)]" />
                          <td className={`px-2 py-1 border-b border-[var(--color-border-light)] tabular-nums ${t.captured > 70 ? 'text-green-600' : 'text-amber-500'}`}>
                            {fmtPct(t.captured)}
                          </td>
                        </tr>
                      ))}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
            {trimGroups.length > INITIAL_ROWS && (
              <button
                onClick={() => setShowAllTrims(v => !v)}
                className="mt-2 text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
              >
                {showAllTrims ? 'Show less' : `Show all ${trimGroups.length} tickers`}
              </button>
            )}
          </div>
        )}
        {trimAnalysis.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">No trim data available for closed trades.</div>
        )}
      </div>

      {/* Stop Analysis */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Stop Analysis
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          <StatCard label="Stopped Out" value={stopStats.total} />
          <StatCard label="Stop Too Tight %" value={stopStats.total > 0 ? fmtPct(stopStats.tooTightPct) : '—'}
            colorClass={stopStats.tooTightPct > 30 ? 'text-red-500' : stopStats.tooTightPct > 15 ? 'text-amber-500' : 'text-green-600'} />
          <StatCard label="Avg Stop Distance" value={stopStats.total > 0 ? fmtPct(stopStats.avgStopDist) : '—'} />
        </div>

        {stopAnalysis.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Ticker', 'Dir', 'Entry', 'Stop', 'Exit', 'Recovery Peak', 'Recovery%', 'Stop Dist%'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleStops.map((s, i) => (
                  <tr
                    key={`${s.ticker}-${s.exitDate}-${i}`}
                    className={`${i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'} ${s.stopTooTight ? 'border-l-2 border-l-red-500' : ''}`}
                  >
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{s.ticker}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">
                      <span className={s.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{s.direction?.toUpperCase()}</span>
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(s.entryPrice)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(s.stopPrice)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">{s.exitDate}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{fmtCur(s.recoveryPeak)}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${s.stopTooTight ? 'text-red-500' : 'text-green-600'}`}>
                      {fmtPct(s.recoveryPct)}
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtPct(s.stopDistPct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {stopAnalysis.length > INITIAL_ROWS && (
              <button
                onClick={() => setShowAllStops(v => !v)}
                className="mt-2 text-[11px] text-[var(--color-accent)] hover:underline cursor-pointer"
              >
                {showAllStops ? 'Show less' : `Show all ${stopAnalysis.length} trades`}
              </button>
            )}
          </div>
        )}
        {stopAnalysis.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">No stop-out trades detected (exit within 1% of stop price).</div>
        )}
      </div>
    </div>
  )
}
