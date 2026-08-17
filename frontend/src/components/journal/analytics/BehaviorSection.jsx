import { useMemo } from 'react'
import Empty from '../Empty'
import StatCard from '../../portfolio/ui/StatCard'
import { fmtCur, fmtPct, fmt, clr } from '../../portfolio/lib/portfolioFormat'
import {
  computeRMultipleStats,
  computeExitStyleStats,
  computeRevengeTradeClusters,
  computePanicTrimSummary,
} from '../../portfolio/lib/diagnosticsR'

const STYLE_LABEL = {
  strength: 'Strength',
  weakness: 'Weakness',
  mixed: 'Mixed',
  stop_only: 'Stop only',
}

const STYLE_HINT = {
  strength: 'Sold into rising strength — clean trim ladder',
  weakness: 'Trimmed into pullbacks — caps your winners',
  mixed: '"Let it breathe" — usually your biggest winners',
  stop_only: 'Stop hit before any profit-taking trims',
}

export default function BehaviorSection({ enriched }) {
  const rStats = useMemo(() => computeRMultipleStats(enriched), [enriched])
  const exitStyles = useMemo(() => computeExitStyleStats(enriched), [enriched])
  const revengeClusters = useMemo(
    () => computeRevengeTradeClusters(enriched, 30, 2),
    [enriched],
  )
  const panic = useMemo(() => computePanicTrimSummary(enriched), [enriched])

  if (!rStats && Object.values(exitStyles).every(s => s.count === 0)) {
    return <Empty k="empty.noClosed" />
  }

  return (
    <div className="space-y-5">
      {/* R-multiple summary */}
      {rStats && (
        <div>
          <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
            R-Multiple Distribution
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatCard label="Trades w/ Stop" value={rStats.n} />
            <StatCard label="Avg R" value={`${fmt(rStats.avgR, 2)}R`} colorClass={rStats.avgR >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'} />
            <StatCard label="Median R" value={`${fmt(rStats.medianR, 2)}R`} colorClass={rStats.medianR >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'} />
            <StatCard label="Avg Winning R" value={`${fmt(rStats.avgWinR, 2)}R`} colorClass="text-[var(--color-profit)]" />
            <StatCard label="Avg Losing R" value={`${fmt(rStats.avgLossR, 2)}R`} colorClass="text-[var(--color-loss)]" />
          </div>
          {rStats.medianR < 0 && rStats.avgR > 0 && (
            <p className="text-[11px] text-[var(--color-text-muted)] mt-2">
              Median R is negative but average R is positive — more than half your trades stop out;
              your edge lives in the right tail (avg winner = {fmt(rStats.avgWinR, 2)}R).
            </p>
          )}
        </div>
      )}

      {/* Exit-style breakdown */}
      <div>
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-3">
          Exit-Style Breakdown
        </h3>
        <div className="overflow-x-auto bg-[var(--color-surface)] rounded-3xl">
          <table className="w-full text-[12.5px]">
            <thead>
              <tr>
                <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Style</th>
                <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">N</th>
                <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Total P/L</th>
                <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Avg P/L</th>
                <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Wins</th>
                <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Losses</th>
                <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">What it means</th>
              </tr>
            </thead>
            <tbody>
              {['mixed', 'strength', 'weakness', 'stop_only'].map(style => {
                const s = exitStyles[style] || { count: 0, totalPL: 0, avgPL: 0, wins: 0, losses: 0 }
                return (
                  <tr key={style}>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] font-semibold">{STYLE_LABEL[style]}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right">{s.count}</td>
                    <td className={`px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right ${clr(s.totalPL)}`}>{fmtCur(s.totalPL)}</td>
                    <td className={`px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right ${clr(s.avgPL)}`}>{fmtCur(s.avgPL)}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right text-[var(--color-profit)]">{s.wins}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right text-[var(--color-loss)]">{s.losses}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] text-[var(--color-text-muted)]">{STYLE_HINT[style]}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Revenge-trade clusters */}
      <div>
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
          Revenge-Trade Clusters
        </h3>
        <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
          Same ticker, ≥2 losing trades within 30 days — re-attacks on a thesis that already failed.
        </p>
        {revengeClusters.length === 0 ? (
          <Empty k="empty.noClusters" />
        ) : (
          <div className="overflow-x-auto bg-[var(--color-surface)] rounded-3xl">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr>
                  <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Ticker</th>
                  <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Stops</th>
                  <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Total Loss</th>
                  <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Window</th>
                </tr>
              </thead>
              <tbody>
                {revengeClusters.map((c, i) => {
                  const first = c.trades[0]?.entryDate?.slice(0, 10) || ''
                  const last = c.trades[c.trades.length - 1]?.entryDate?.slice(0, 10) || ''
                  return (
                    <tr key={`${c.ticker}-${i}`}>
                      <td className="px-3 py-2 border-b border-[var(--color-border-light)] font-semibold">{c.ticker}</td>
                      <td className="px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right">{c.trades.length}</td>
                      <td className={`px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right ${clr(c.totalPL)}`}>{fmtCur(c.totalPL)}</td>
                      <td className="px-3 py-2 border-b border-[var(--color-border-light)] text-[var(--color-text-muted)] tabular-nums">{first} → {last}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Panic-trim leak */}
      <div>
        <h3 className="text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-secondary)] mb-1">
          Panic-Trim Leak
        </h3>
        <p className="text-[11px] text-[var(--color-text-muted)] mb-3">
          Winners whose trim prices deteriorated (sold into weakness). The leak is what you'd have made by
          executing every trim at the best price you got — your "panic-trim tax."
        </p>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <StatCard label="Trades affected" value={panic.count} />
          <StatCard label="Total leak" value={fmtCur(panic.totalLeak)} colorClass="text-[var(--color-loss)]" />
        </div>
        {panic.perTrade.length > 0 && (
          <div className="overflow-x-auto bg-[var(--color-surface)] rounded-3xl">
            <table className="w-full text-[12.5px]">
              <thead>
                <tr>
                  <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Ticker</th>
                  <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Dir</th>
                  <th className="text-left px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Entry</th>
                  <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Realized</th>
                  <th className="text-right px-3 py-2 border-b border-[var(--color-border)] text-[var(--color-text-secondary)] font-semibold text-[10px] uppercase tracking-wide">Left on Table</th>
                </tr>
              </thead>
              <tbody>
                {panic.perTrade.slice(0, 15).map((x, i) => (
                  <tr key={`${x.ticker}-${x.entryDate}-${i}`}>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] font-semibold">{x.ticker}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)]">{x.direction}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] text-[var(--color-text-muted)] tabular-nums">{x.entryDate?.slice(0, 10)}</td>
                    <td className={`px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right ${clr(x.realizedPL)}`}>{fmtCur(x.realizedPL)}</td>
                    <td className="px-3 py-2 border-b border-[var(--color-border-light)] tabular-nums text-right text-[var(--color-loss)]">{fmtCur(x.leak)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
