import { useState } from 'react'
import StatCard from '../../portfolio/ui/StatCard'
import { fmtCur, fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'

export default function TrimStopsSection({ trimAnalysis, stopAnalysis }) {
  const [expandedTrim, setExpandedTrim] = useState(null)

  // Trim summary stats
  const trimStats = {
    total: trimAnalysis.length,
    tooEarlyPct: trimAnalysis.length > 0
      ? (trimAnalysis.filter(t => t.tooEarly).length / trimAnalysis.length) * 100
      : 0,
    avgLeftOnTable: trimAnalysis.length > 0
      ? trimAnalysis.reduce((s, t) => s + t.leftOnTable, 0) / trimAnalysis.length
      : 0,
    avgCaptured: trimAnalysis.length > 0
      ? trimAnalysis.reduce((s, t) => s + t.captured, 0) / trimAnalysis.length
      : 0,
  }

  // Stop summary stats
  const stopStats = {
    total: stopAnalysis.length,
    tooTightPct: stopAnalysis.length > 0
      ? (stopAnalysis.filter(t => t.stopTooTight).length / stopAnalysis.length) * 100
      : 0,
    avgStopDist: stopAnalysis.length > 0
      ? stopAnalysis.reduce((s, t) => s + t.stopDistPct, 0) / stopAnalysis.length
      : 0,
  }

  // Actionable callouts
  const callouts = []
  if (trimStats.tooEarlyPct > 30 && trimAnalysis.length >= 3) {
    const avgCaptured = trimStats.avgCaptured
    callouts.push({
      type: 'warning',
      text: `You trimmed too early ${fmt(trimStats.tooEarlyPct, 0)}% of the time, capturing only ${fmt(avgCaptured, 0)}% of the move on average. Consider delaying first trim or using trailing stops.`,
    })
  }
  if (stopStats.tooTightPct > 25 && stopAnalysis.length >= 3) {
    callouts.push({
      type: 'warning',
      text: `${fmt(stopStats.tooTightPct, 0)}% of stopped-out trades recovered 5%+ — stops may be too tight (avg distance: ${fmt(stopStats.avgStopDist, 1)}%).`,
    })
  }

  // Find high-beta stop-outs
  const highBetaStops = stopAnalysis.filter(s => s.recoveryPct > 10)
  if (highBetaStops.length >= 2) {
    callouts.push({
      type: 'neutral',
      text: `${highBetaStops.length} trades had 10%+ recovery after stop-out — likely high-beta names needing wider stops.`,
    })
  }

  return (
    <div className="space-y-5">
      {/* Trim Analysis */}
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Trim Analysis
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <StatCard label="Trims Analyzed" value={trimStats.total} />
          <StatCard
            label="Too Early %"
            value={fmtPct(trimStats.tooEarlyPct)}
            colorClass={trimStats.tooEarlyPct > 40 ? 'text-red-500' : trimStats.tooEarlyPct > 25 ? 'text-amber-500' : 'text-green-600'}
          />
          <StatCard
            label="Avg Left on Table"
            value={fmtPct(trimStats.avgLeftOnTable)}
            colorClass={trimStats.avgLeftOnTable > 5 ? 'text-amber-500' : ''}
          />
          <StatCard
            label="Avg Captured"
            value={fmtPct(trimStats.avgCaptured)}
            colorClass={trimStats.avgCaptured > 70 ? 'text-green-600' : 'text-amber-500'}
          />
        </div>

        {trimAnalysis.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Ticker', 'Dir', 'Entry', 'Trim#', 'Trim Price', 'Trim Date', 'Peak After', 'Peak Date', 'Left%', 'Captured%'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {trimAnalysis.map((t, i) => (
                  <tr
                    key={`${t.ticker}-${t.trimDate}-${i}`}
                    className={`${i % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-bg)]'} ${t.tooEarly ? 'border-l-2 border-l-amber-500' : ''}`}
                  >
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] font-medium">{t.ticker}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">
                      <span className={t.direction === 'long' ? 'text-green-600' : 'text-red-500'}>{t.direction?.toUpperCase()}</span>
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.entryPrice)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{t.trimIndex}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtCur(t.trimPrice)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">{t.trimDate}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-amber-500">{fmtCur(t.peakAfterTrim)}</td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">{t.peakDate}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${t.leftOnTable > 5 ? 'text-amber-500' : 'text-green-600'}`}>
                      {fmtPct(t.leftOnTable)}
                    </td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${t.captured > 70 ? 'text-green-600' : 'text-amber-500'}`}>
                      {fmtPct(t.captured)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
          <StatCard
            label="Stop Too Tight %"
            value={stopStats.total > 0 ? fmtPct(stopStats.tooTightPct) : '—'}
            colorClass={stopStats.tooTightPct > 30 ? 'text-red-500' : stopStats.tooTightPct > 15 ? 'text-amber-500' : 'text-green-600'}
          />
          <StatCard
            label="Avg Stop Distance"
            value={stopStats.total > 0 ? fmtPct(stopStats.avgStopDist) : '—'}
          />
        </div>

        {stopAnalysis.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  {['Ticker', 'Dir', 'Entry', 'Stop', 'Exit Date', 'Recovery Peak', 'Recovery Date', 'Recovery%', 'Stop Dist%'].map(h => (
                    <th key={h} className="text-left px-2 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stopAnalysis.map((s, i) => (
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
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)]">{s.recoveryDate}</td>
                    <td className={`px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums font-semibold ${s.stopTooTight ? 'text-red-500' : 'text-green-600'}`}>
                      {fmtPct(s.recoveryPct)}
                    </td>
                    <td className="px-2 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{fmtPct(s.stopDistPct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {stopAnalysis.length === 0 && (
          <div className="text-center py-8 text-[var(--color-text-muted)] text-sm">No stop-out trades detected (exit within 1% of stop price).</div>
        )}
      </div>

      {/* Actionable callouts */}
      {callouts.length > 0 && (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            Actionable Insights
          </h3>
          <div className="space-y-2">
            {callouts.map((c, i) => (
              <div key={i} className="flex gap-2 text-sm">
                <span className={`flex-shrink-0 ${c.type === 'warning' ? 'text-amber-500' : c.type === 'positive' ? 'text-green-600' : 'text-[var(--color-text-muted)]'}`}>
                  {c.type === 'warning' ? '!' : c.type === 'positive' ? '+' : '-'}
                </span>
                <span className="text-[var(--color-text-secondary)]">{c.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
