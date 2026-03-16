import { fmtPct, fmt, clr } from '../lib/portfolioFormat'

export default function MonthlyTab({ monthlyStats, ytdStats, totalReturnPct }) {
  if (monthlyStats.length === 0) {
    return <div className="text-center py-16 text-[var(--color-text-muted)]">No completed trades.</div>
  }

  const HEADERS = ['Month', 'Monthly Ret%', '# Trades', 'Avg Ret%', 'Win%', 'Avg Gain%', 'Avg Loss%', 'Max Gain%', 'Max Loss%', 'Days(W)', 'Days(L)']

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr>
            {HEADERS.map(h => (
              <th key={h} className="text-left px-2.5 py-2 border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {monthlyStats.map((m, idx) => (
            <tr key={m.month} className={idx % 2 === 0 ? 'bg-[var(--color-surface)]' : 'bg-[var(--color-surface-alt)]'}>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-semibold tabular-nums">{m.month}</td>
              <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] font-bold tabular-nums ${clr(m.monthlyRetPct)}`}>{fmtPct(m.monthlyRetPct)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades || '—'}</td>
              <td className={`px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums ${clr(m.returnPct)}`}>{m.totalTrades ? fmtPct(m.returnPct) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.totalTrades ? fmtPct(m.winPct) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.avgGain ? fmtPct(m.avgGain) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.avgLoss ? fmtPct(m.avgLoss) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-green-600">{m.largestGain ? fmtPct(m.largestGain) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums text-red-500">{m.largestLoss ? fmtPct(m.largestLoss) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldWin ? fmt(m.avgHoldWin, 2) : '—'}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border-light)] tabular-nums">{m.avgHoldLoss ? fmt(m.avgHoldLoss, 2) : '—'}</td>
            </tr>
          ))}
          {ytdStats && (
            <tr className="bg-[var(--color-surface-raised)] font-bold">
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)]">YTD</td>
              <td className={`px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums ${clr(totalReturnPct)}`}>{fmtPct(totalReturnPct)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{ytdStats.totalTrades}</td>
              <td className={`px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums ${clr(ytdStats.returnPct)}`}>{fmtPct(ytdStats.returnPct)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{fmtPct(ytdStats.winPct)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-green-600">{fmtPct(ytdStats.avgGain)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-red-500">{fmtPct(ytdStats.avgLoss)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-green-600">{fmtPct(ytdStats.largestGain)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums text-red-500">{fmtPct(ytdStats.largestLoss)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{fmt(ytdStats.avgHoldWin, 2)}</td>
              <td className="px-2.5 py-1.5 border-b border-[var(--color-border)] tabular-nums">{fmt(ytdStats.avgHoldLoss, 2)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
