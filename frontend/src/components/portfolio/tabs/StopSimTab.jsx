import { useState } from 'react'
import StatCard from '../ui/StatCard'
import { fmtCur, fmtPct, fmt, clr } from '../lib/portfolioFormat'

export default function StopSimTab({ simData2, simData3 }) {
  const [mode, setMode] = useState(3)
  const simData = mode === 2 ? simData2 : simData3

  if (!simData || simData.rows.length === 0) {
    return (
      <div className="text-center py-16 text-[var(--color-text-muted)]">
        No closed trades with stop prices to simulate. Close some trades first.
      </div>
    )
  }

  const { rows, summary } = simData
  const hasHistoryGap = rows.some(r => !r.hasHistory)

  const cards = [
    { label: 'Actual Total P&L', value: fmtCur(summary.totalActualPL), color: clr(summary.totalActualPL) },
    { label: `${mode}-Stop Total P&L`, value: fmtCur(summary.totalSimPL), color: clr(summary.totalSimPL) },
    { label: 'P&L Difference', value: fmtCur(summary.totalDiff), color: clr(summary.totalDiff), sub: summary.totalDiff > 0 ? `${mode}-stop would save` : summary.totalDiff < 0 ? `${mode}-stop would cost` : 'No change' },
    { label: 'Actual Avg Loss', value: fmtPct(summary.avgActualLoss), color: 'text-red-500' },
    { label: `${mode}-Stop Avg Loss`, value: fmtPct(summary.avgSimLoss), color: 'text-red-500' },
    { label: 'Trades Affected', value: `${summary.tradesAffected} / ${summary.totalTrades}`, color: '', sub: 'Had stops triggered' },
  ]

  // Determine number of stop columns from first row's stops array
  const numStops = rows[0]?.stops?.length || mode

  return (
    <div>
      {/* Segmented toggle */}
      <div className="flex mb-4">
        <button
          onClick={() => setMode(2)}
          className={`px-4 py-1.5 text-xs font-semibold rounded-l-md border cursor-pointer ${
            mode === 2
              ? 'bg-[var(--color-accent)] text-white border-[var(--color-accent)]'
              : 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)]'
          }`}
        >
          2-Stop
        </button>
        <button
          onClick={() => setMode(3)}
          className={`px-4 py-1.5 text-xs font-semibold rounded-r-md border border-l-0 cursor-pointer ${
            mode === 3
              ? 'bg-[var(--color-accent)] text-white border-[var(--color-accent)]'
              : 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)]'
          }`}
        >
          3-Stop
        </button>
      </div>

      {hasHistoryGap && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-md mb-4 text-xs text-amber-700">
          Some trades lack daily price history — using worst-case (all stops triggered) for those.
          Load full history on the Performance tab for accurate simulation.
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {cards.map((c, i) => (
          <StatCard key={i} label={c.label} value={c.value} colorClass={c.color} sub={c.sub} />
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-[var(--color-border)] text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
              <th className="text-left py-2 px-2">Ticker</th>
              <th className="text-left py-2 px-1">Dir</th>
              <th className="text-right py-2 px-2">Qty</th>
              <th className="text-right py-2 px-2">Entry</th>
              <th className="text-right py-2 px-2">Stop</th>
              <th className="text-right py-2 px-2">R</th>
              {Array.from({ length: numStops }, (_, i) => (
                <th key={i} className="text-right py-2 px-2">Stop{i + 1}</th>
              ))}
              <th className="text-right py-2 px-2">Avg Exit</th>
              <th className="text-right py-2 px-2">Actual P&L</th>
              <th className="text-right py-2 px-2">{mode}-Stop P&L</th>
              <th className="text-right py-2 px-2">Diff</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id} className="border-b border-[var(--color-border-light)] hover:bg-[var(--color-hover-bg)]">
                <td className="py-2 px-2 font-semibold text-[var(--color-accent)]">{r.ticker}</td>
                <td className={`py-2 px-1 font-semibold ${r.direction === 'long' ? 'text-green-600' : 'text-red-500'}`}>
                  {r.direction.toUpperCase()}
                </td>
                <td className="text-right py-2 px-2">{r.qty}</td>
                <td className="text-right py-2 px-2">{fmtCur(r.entryPrice)}</td>
                <td className="text-right py-2 px-2">{fmtCur(r.stopPrice)}</td>
                <td className="text-right py-2 px-2">{fmt(r.R, 2)}</td>
                {r.stops.map((stop, i) => (
                  <td key={i} className={`text-right py-2 px-2 ${stop.triggered ? 'text-red-500 font-semibold' : 'text-[var(--color-text-muted)]'}`}>
                    {fmtCur(stop.level)}
                  </td>
                ))}
                <td className="text-right py-2 px-2">{fmtCur(r.actualAvgExit)}</td>
                <td className={`text-right py-2 px-2 ${clr(r.actualPL)}`}>{fmtCur(r.actualPL)}</td>
                <td className={`text-right py-2 px-2 ${clr(r.simPL)}`}>{fmtCur(r.simPL)}</td>
                <td className={`text-right py-2 px-2 font-semibold ${clr(r.diff)}`}>{fmtCur(r.diff)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
